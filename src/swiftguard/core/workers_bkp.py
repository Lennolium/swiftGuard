#!/usr/bin/env python3

"""
workers.py: TODO: Headline...

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-03-06"
__status__ = "Prototype/Development/Production"

# Imports.
import random
import logging
import traceback

from PySide6.QtCore import (QObject, QRunnable, QThread,
                            Signal, Slot)
from PySide6.QtWidgets import QApplication

from swiftguard.constants import C
from swiftguard.init import exceptions as exc
from swiftguard.core import actions, monitor

# Child logger.
LOGGER = logging.getLogger(__name__)


class WorkerManager:
    """
    Manage the workers in threads etc. TODO: Description...
    """

    def __init__(self):
        # TODO: start workers according to config.
        # TODO: register callbacks to main.

        # Get the threadpool from main app.
        self.threadpool_gl = QApplication.instance().threadpool

        self.worker_usb = WorkerUSB()
        self.worker_bluetooth = WorkerBluetooth()
        self.worker_network = WorkerNetwork()

        # Reuse workers -> Stopping does not delete its thread.
        self.worker_usb.setAutoDelete(False)
        self.worker_bluetooth.setAutoDelete(False)
        self.worker_network.setAutoDelete(False)

        # Start workers accordingly to settings in config.
        if C.cfg.CFG["usb_enabled"]:
            self.threadpool_gl.start(self.worker_usb)

        if C.cfg.CFG["bluetooth_enabled"]:
            self.threadpool_gl.start(self.worker_bluetooth)

        if C.cfg.CFG["network_enabled"]:
            self.threadpool_gl.start(self.worker_network)

    def start(self):
        # Start all workers.
        ...

    def stop(self):
        if not self.worker_usb.stopped:
            self.worker_usb.stop()

        if not self.worker_bluetooth.stopped:
            self.worker_bluetooth.stop()

        if not self.worker_network.stopped:
            self.worker_network.stop()

    def kill(self):
        # Kill all threads for clean exit. setDelete to True...
        # When called, a new instance of WorkerManager has to be
        # initiated after wards. Merely useful when closing the main
        # app and not restarting it.
        self.worker_usb.setAutoDelete(True)
        self.worker_bluetooth.setAutoDelete(True)
        self.worker_network.setAutoDelete(True)

        self.stop()


class WorkerSignals(QObject):
    """
    Signals for the workers, as QRunnable does not support signals.
    """

    running = Signal(tuple)
    error = Signal(Exception)
    detected = Signal()
    tampering = Signal(tuple)
    devices = Signal(dict)
    devices_usb = Signal(list)
    devices_bluetooth = Signal(list)
    devices_network = Signal(list)


class Worker(QRunnable):
    """
    Base class for the workers. Do not instantiate directly, instead
    use WorkerUSB, WorkerBluetooth or WorkerNetwork.
    """

    _defused = False

    @classmethod
    def defuse(cls) -> None:
        """
        Defuse the worker. This function is called when the worker is
        defused. It sets the defused flag to True, so the worker and
        its running counter-measure can stop itself.

        :return: None
        """

        cls._defused = True

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the worker.

        :param args: Optional arguments.
        :type args: list
        :param kwargs: Optional keyword arguments.
        :type kwargs: dict
        :return: None
        """

        super().__init__()

        # For every worker an own monitor process is needed.
        self.MONITOR = monitor.Monitor()

        # Worker parameters.
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Worker callbacks.
        self.cb_error = {"USB": None,
                         "Bluetooth": None,
                         "Network": None,
                         }
        self.cb_devices = {"USB": None,
                           "Bluetooth": None,
                           "Network": None,
                           }
        self.tamper_device = None
        self.tamper_action = None

        # Worker status.
        self.interface = self.__class__.__name__.split("Worker", 1)[1]
        self.stopped = True
        self.armed = False
        type(self)._defused = False
        self.thread_id = None

        # Start devices.
        self.start_devices = None

        # Mapping of functions and exceptions for each interface.
        _map_get_func = {"USB": self.MONITOR.get_usb,
                         "Bluetooth": self.MONITOR.get_bluetooth,
                         "Network": self.MONITOR.get_network,
                         }
        _map_tamp_exc = {"USB": exc.USBTamperingEvent,
                         "Bluetooth": exc.BluetoothTamperingEvent,
                         "Network": exc.NetworkTamperingEvent,
                         }

        self.get_devs = _map_get_func[self.interface]
        self.tamper_exc = _map_tamp_exc[self.interface]

    @property
    def whitelist(self) -> list:
        """
        Get the whitelist for the current interface.

        :return: Whitelist.
        :rtype: list
        """

        return C.cfg.CFG[self.interface.lower()]

    def get_start(self) -> list[list]:
        """
        Get the start devices (with removed whitelisted devices).

        :return: Start devices.
        :rtype: list[list]
        """

        start_devs = []

        for mode in self.get_devs():
            for device in mode:
                if device in self.whitelist:
                    mode.remove(device)

            start_devs.append(mode)

        return start_devs

    def _thread_id(self) -> str:
        """
        Get the thread ID of the worker and verify we are not running in
        the main thread, as this would block the GUI.

        :return: Unique thread ID.
        :rtype: str
        """

        # Worker in main thread is a critical blocking issue.
        if QThread.currentThread() is QApplication.instance().thread():
            raise exc.BlockingMainThreadError(
                    "Worker is running in the main thread and blocking the "
                    "GUI!"
                    )

        try:
            return (str(QThread.currentThread()
                        ).split(sep="QThread(0x",
                                maxsplit=1,
                                )[1].split(sep=", name = ",
                                           maxsplit=1,
                                           )[0])

        except Exception as e:
            LOGGER.error(f"Could not get the {self.interface}-worker thread "
                         f"ID. Generating random ID. "
                         f"{e.__class__.__name__}: {e} \n"
                         f"{traceback.format_exc()}"
                         )
            return f"30000{random.randint(1000000, 9999999)}"

    def _countdown(self) -> bool:
        """
        Countdown mechanism for the worker.

        :return: True if the worker was defused, False otherwise.
        :rtype: bool
        """

        LOGGER.warning(
                f"Countdown till {C.cfg.CFG['action']} started: "
                f"{C.cfg.CFG['delay']} seconds. Awaiting defuse ..."
                )

        # Playing an alert sound during countdown.
        if C.cfg.CFG["delay_sound"]:

            class CountdownAlert(QThread):
                def run(self):
                    actions.alert(C.cfg.CFG["delay"])

            countdown_alert = CountdownAlert()
            countdown_alert.start()

        else:
            countdown_alert = None

        for j in range(1, (C.cfg.CFG["delay"] + 1)):
            QThread.sleep(1)

            # Check if worker was defused by main app.
            if type(self)._defused:
                LOGGER.warning(
                        f"The Countdown was defused with "
                        f"{C.cfg.CFG['delay'] - j} seconds remaining."
                        )

                if countdown_alert:
                    countdown_alert.terminate()
                    countdown_alert.wait()

                return True

        LOGGER.warning("The Countdown ended. No defuse in time!")

        if countdown_alert:
            countdown_alert.terminate()
            countdown_alert.wait()

        return False

    @Slot()
    def run(self) -> None:
        """
        Run the worker. This function is called when the worker is
        started. It runs the monitoring method in a loop.

        :return: None
        """

        self.stopped = False
        type(self)._defused = False
        self.signals.running.emit((self.interface, True))

        # Get the thread ID.
        self.thread_id = self._thread_id()

        LOGGER.info(f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"started monitoring the {self.interface} interface."
                    )

        for i in range(1, 4):

            try:
                # Get the start devices (with removed whitelisted devices).
                self.start_devices = self.get_start()

                # Run the monitoring.
                while not self.stopped:
                    self.monitoring(*self.args, **self.kwargs)

                    # Sleep for the interval time, except for the
                    # network interface, as fetching the network
                    # devices takes significantly longer.
                    if self.interface == "Network":
                        sleep_time = 15
                    else:
                        sleep_time = C.cfg.CFG["interval"]

                    # Break the sleep time into smaller intervals and
                    # check if thread is stopped after each interval,
                    # so we can stop the worker immediately.
                    for _ in range(sleep_time):
                        if self.stopped:
                            break
                        QThread.sleep(1)

                # Monitoring finished, get out of the loop.
                break

            except exc.TamperingEvent as e:
                # Wait 15 seconds before emitting the tampering signal.
                # Maybe it is just a temporary network issue, but if
                # connected to a network, we directly raise tampering.
                if (e.__class__ == exc.NetworkTamperingEvent
                        and i < 2
                        and self.tamper_action != "connected"):
                    LOGGER.warning("Possible network tampering detected. "
                                   "Verifying it is not a temporary network "
                                   "issue. Retrying in 15 seconds ..."
                                   )
                    QThread.sleep(15)
                    continue

                # Warn and log the user.
                LOGGER.warning("!!!!! MANIPULATION DETECTED !!!!!")
                LOGGER.warning(e)
                self.signals.detected.emit()

                # Defuse/countdown mechanism.
                if C.cfg.CFG["delay"] > 0:
                    if self._countdown():
                        break

                self.signals.tampering.emit((e,
                                             self.tamper_device,
                                             self.tamper_action)
                                            )
                break

            # Worker was stopped by the main app and the system profiler
            # was terminated, so we do not have to wait for its results.
            except exc.SystemProfilerTerminated:
                break

            except exc.MonitoringError as e:
                LOGGER.warning(f"Could not start worker: {e}")
                self.cb_error[self.interface] = e
                self.signals.error.emit(self.cb_error)

                # Stop the worker.
                self.stop()
                break

            except Exception as e:

                # After the third failed attempt, we stop the worker.
                if i >= 3:
                    LOGGER.error(f"{i}. attempt to run "
                                 f"{self.interface} monitoring failed."
                                 )

                    # Emit the last exception.
                    self.cb_error[self.interface] = e
                    self.signals.error.emit(self.cb_error)

                    # Stop the worker.
                    self.stop()
                    break

                # Wait few seconds before trying to restart monitoring.
                else:
                    LOGGER.warning(
                            f"{i}. attempt to run {self.interface} monitoring "
                            f"failed. Trying again in a few seconds ..."
                            )
                    QThread.sleep(random.randint(1, 5))
                    continue

    def stop(self) -> None:
        """
        Stop the worker. This does not delete the thread or the worker
        object, but the worker will finish the current loop and then
        stop. If we restart the worker, it will reuse the same thread.

        :return: None
        """

        LOGGER.info(f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"stopped monitoring the {self.interface} interface."
                    )

        self.stopped = True
        self.signals.running.emit((self.interface, False))
        self.MONITOR.kill_process()

    def monitoring(self, *args, **kwargs) -> None:
        """
        Monitoring method for different interfaces. This function is run
        by the worker thread in a loop. Must be implemented in the
        subclasses (WorkerUSB, WorkerBluetooth or WorkerNetwork).

        :param args: Optional arguments.
        :type args: list
        :param kwargs: Optional keyword arguments.
        :type kwargs: dict
        :raises NotImplementedError: If the method is not implemented in
            the subclasses.
        :return: None
        """

        raise NotImplementedError("Monitoring method must be implemented in "
                                  "the subclasses (WorkerUSB, WorkerBluetooth "
                                  "or WorkerNetwork)!"
                                  )


class WorkerUSBBluetooth(Worker):
    """
    Base class for USB and Bluetooth workers.
    Do not instantiate directly, instead use WorkerUSB or
    WorkerBluetooth.
    """

    def monitoring(self, *args, **kwargs) -> None:
        """
        Monitoring method for the USB or Bluetooth interface. This
        function is run by the worker thread in a loop.

        :param args: Optional arguments.
        :type args: list
        :param kwargs: optional keyword arguments.
        :type kwargs: dict
        :raises exc.USBTamperingEvent or exc.BluetoothTamperingEvent:
            If tampering is detected.
        :return: None
        """

        # Currently connected devices.
        current = self.get_devs()[0]

        # Emit current devices to app for displaying.
        self.cb_devices[self.interface] = current
        self.signals.devices.emit(self.cb_devices)

        # Start devices (with removed whitelisted devices).
        start = self.start_devices[0]

        # Remove whitelisted devices from the currently connected list.
        for device in self.whitelist:
            if device in current:
                current.remove(device)

        # No changes or worker is not armed (searching for devices).
        if start == current:
            return
        elif not self.armed:
            return

        # Tampering: Check if all start devices are still connected.
        for device in start:
            if device not in current:
                self.tamper_device = device
                self.tamper_action = "disconnected"
                raise self.tamper_exc(
                        f"Unknown {self.interface}-device disconnected: "
                        f"{device:out}"
                        )

        # All start devices still connected: Check if new devices were
        # connected.
        else:
            for device in current:
                if device not in start:
                    self.tamper_device = device
                    self.tamper_action = "connected"
                    raise self.tamper_exc(
                            f"Unknown {self.interface}-device connected: "
                            f"{device:out}"
                            )

        # If we reach this point, tampering was detected, but we
        # could not determine the exact device in question.
        self.tamper_device = "Unknown"
        self.tamper_action = "not recognized"
        raise self.tamper_exc(
                f"Unknown {self.interface}-device connected or disconnected!\n"
                f"Current state: {current}"
                )


class WorkerUSB(WorkerUSBBluetooth):
    """
    Worker for USB interface. Instantiate this class to start the USB
    monitoring.
    """

    pass


class WorkerBluetooth(WorkerUSBBluetooth):
    """
    Worker for Bluetooth interface. Instantiate this class to start the
    Bluetooth monitoring.
    """

    pass


class WorkerNetwork(Worker):
    """
    Worker for Network interface. Instantiate this class to start the
    Network monitoring.
    """

    def monitoring(self, *args, **kwargs) -> None:
        """
        Monitoring method for the Network interface. This function is
        run by the worker thread in a loop.

        :param args: Optional arguments.
        :type args: list
        :param kwargs: Optional keyword arguments.
        :type kwargs: dict
        :raises exc.NetworkTamperingEvent: If tampering is detected.
        :return: None
        """

        # Currently connected devices.
        current = self.get_devs()
        current_connect = current[0]
        current_disconnect = current[1]

        # Emit current devices to app for displaying.
        self.cb_devices[self.interface] = current
        self.signals.devices.emit(self.cb_devices)

        # Start devices (with removed whitelisted devices).
        start = self.start_devices

        # Remove whitelisted devices from the currently connected list.
        for device in self.whitelist:
            if device in current:
                current.remove(device)

        start_connect = start[0]
        # start_disconnect = start[1]  # Not needed so far.

        # Worker is not armed (searching for devices).
        if not self.armed:
            return

        # Strict mode: Wi-Fi network disconnected -> tampering.
        if C.cfg.CFG["network_strict"]:
            if start_connect == current_connect:
                return

        # Non-strict mode: Wi-Fi network disconnected, but Wi-Fi signal
        # of the same network is still available -> no tampering.
        # Wi-Fi signal of network not available -> tampering.
        else:
            try:
                start_is_near = start_connect[0] in current_disconnect

            # At start time, no Wi-Fi network was connected (empty
            # start_connect).
            except IndexError:
                start_is_near = False

            if start_connect == current_connect or start_is_near:
                return

        # At start time, no Wi-Fi network was connected. Now a Wi-Fi
        # network is connected -> tampering.
        if len(start_connect) == 0:
            self.tamper_device = current_connect[0]
            self.tamper_action = "connected"
            msg = (f"Connected to unknown Wi-Fi Network: "
                   f"{self.tamper_device:out}"
                   )

        elif C.cfg.CFG["network_strict"]:
            self.tamper_device = start_connect[0]
            self.tamper_action = "disconnected"
            msg = (f"Disconnected from Wi-Fi Network: "
                   f"{self.tamper_device:out}")

        else:
            self.tamper_device = start_connect[0]
            self.tamper_action = "lost signal"
            msg = (f"Lost signal to Wi-Fi Network: "
                   f"{self.tamper_device:out}")

        raise self.tamper_exc(msg)
