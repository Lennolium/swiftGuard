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

from PySide6.QtCore import (QMutex, QObject, QRunnable, QThread,
                            QTime, QWaitCondition, Signal, Slot)
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from swiftguard.constants import C
from swiftguard.init import exceptions as exc, models
from swiftguard.core import actions, devices, monitor
from swiftguard.utils import process

# Child logger.
LOGGER = logging.getLogger(__name__)


class Countdown(QThread):

    def __init__(self) -> None:
        super().__init__()

        self._defused: bool = False

        self.mutex: QMutex = QMutex()
        self.condition: QWaitCondition = QWaitCondition()

    @property
    def _total_duration(self) -> int:
        return C.cfg.CFG["delay"]

    @property
    def _sound_intervals(self) -> list[int]:
        """
        Calculates the intervals for playing a sound based on the total
        duration. The intervals are calculated so that the sound is
        played at decreasing intervals until the remaining time is
        5 seconds or less, then the sound is played every second.

        :return: A list of intervals in seconds between sound playing.
        :rtype: list[int]
        """

        total_duration = max(self._total_duration, 0)
        intervals = []

        if total_duration == 0:
            return [0]

        # Calculate the intervals by halving the total duration until it
        # is less than 5 seconds.
        while (total_duration // 2) >= 5:
            intervals.append(total_duration // 2)
            total_duration //= 2

        # Add the remaining interval if the sum of the intervals + 5 seconds
        # is less than the total duration.
        if (sum(intervals) + 5) < self._total_duration:
            intervals.append(self._total_duration - sum(intervals) - 5)
            total_duration = 5

        # Countdown left <= 5 seconds: Play sound every second.
        intervals.extend([1] * total_duration)

        return intervals

    @Slot()
    def run(self) -> None:

        self._defused = False

        if self._total_duration == 0:
            return

        LOGGER.warning(
                f"Countdown till {C.cfg.CFG['action']} started: "
                f"{C.cfg.CFG['delay']} seconds. Awaiting defuse ..."
                )

        start_time = QTime.currentTime()

        # No sound during countdown.
        if not C.cfg.CFG["delay_sound"]:
            self.mutex.lock()
            self.condition.wait(self.mutex, (self._total_duration * 1000))
            self.mutex.unlock()

        # Play sound during countdown.
        else:

            # Ensure the volume is high enough to hear the alarm.
            _ = process.Process(
                    binary_path="/usr/bin/osascript",
                    args=("-e",
                          "set volume output volume 50"),
                    timeout=1,
                    blocking=False,
                    ).run()

            for interval in self._sound_intervals:

                if self._defused:
                    break

                try:
                    _ = process.Process(
                            binary_path="/usr/bin/afplay",
                            args=("-t", "0.7",
                                  "-q", "0",
                                  "/System/Library/Sounds/Submarine.aiff",),
                            timeout=1,
                            blocking=False,
                            ).run()

                except Exception as _:
                    pass

                self.mutex.lock()
                self.condition.wait(self.mutex, (interval * 1000))
                self.mutex.unlock()

        if self._defused:
            remaining = max(
                    self._total_duration
                    - start_time.secsTo(QTime.currentTime()), 0
                    )
            LOGGER.info(
                    f"Countdown was defused with {remaining} seconds "
                    f"remaining."
                    )

        else:
            LOGGER.warning("The Countdown ended. No defuse in time!")

    def defuse(self) -> None:
        """
        Defuse the countdown. This function is called when the countdown
        is defused. It stops the countdown.

        :return: None
        """

        self._defused = True

        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()

        # Wait for the thread to finish.
        self.quit()
        if not self.wait(2500):
            self.terminate()
            self.wait(2500)


class ManipulationManager(QThread, metaclass=models.SingletonQt):
    """
    Manage the manipulation detection and defuse/countdown mechanism.
    """

    # Signals for communication to main app.
    running_sig: Signal = Signal(bool)
    tampering_sig: Signal = Signal(bool)

    def __init__(self) -> None:
        super().__init__()

        self.running: bool = False
        self.tampering: bool = False
        self.thread_id: str | None = None

        self._defused: bool = False
        self._armed: bool = True

        self._countdown = Countdown()

        self.mutex: QMutex = QMutex()
        self.condition: QWaitCondition = QWaitCondition()

        self.moni_mgr: monitor.MonitorManager | None = None

        self.devices: dict = {
                "USB": [[], []],
                "Bluetooth": [[], []],
                "Network": [[], []],
                }

        self.start(priority=QThread.Priority.HighPriority)

    def _thread_id(self) -> str:
        """
        Get the thread ID of the manipulation manager and verify we are
        not running in the main thread, as this would block the GUI.

        :return: Unique thread ID.
        :rtype: str
        """

        # Worker in main thread is a critical blocking issue.
        if QThread.currentThread() is QGuiApplication.instance().thread():
            raise exc.BlockingMainThreadError(
                    f"{self.__class__.__qualname__} thread is running in the "
                    f"main thread and blocking the GUI!"
                    )

        try:
            return (str(QThread.currentThread()
                        ).split(sep=f"{self.__class__.__name__}(0x",
                                maxsplit=1,
                                )[1].split(sep=") at",
                                           maxsplit=1,
                                           )[0])

        except Exception as e:
            LOGGER.error(
                    f"Could not get the {self.__class__.__qualname__} thread "
                    f"ID. Generating random ID. "
                    f"{e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )
            return f"30000{random.randint(1000000, 9999999)}"

    @Slot()
    def run(self) -> None:
        """
        Run the manipulation manager. This function is called when the
        manipulation manager is started. It runs the monitoring method
        in a loop.

        :return: None
        """

        self.running = True
        self.running_sig.emit(True)
        self.thread_id = self._thread_id()

        singletons: dict[str, models.Singleton] = (
                models.Singleton.all_instances()
        )

        # Try to connect to MonitorManager three times with sleep time.
        for i in range(1, 4):

            self.moni_mgr: monitor.MonitorManager | None = (
                    singletons.get("MonitorManager", None)
            )

            if self.moni_mgr and self.moni_mgr.running:

                # Connect to necessary signals from MonitorManager.
                # TODO: implement here!

                self.moni_mgr.updated_sig.connect(self.on_updated)

                LOGGER.info(
                        f"{self.__class__.__qualname__} "
                        f"(ID: {self.thread_id}) connected to MonitorManager "
                        f"and started guarding."
                        )

                break

            else:
                LOGGER.error(f"Could not find MonitorManager instance. "
                             f"Waiting for it to be initialized "
                             f"({i}/3)."
                             )
                QThread.sleep(i)

        else:
            raise exc.MonitoringError(
                    "Could not connect to MonitorManager. "
                    "Stopping manipulation detection."
                    )

        try:
            while self.running:
                print("while loop top in run()")
                self.mutex.lock()
                self.condition.wait(self.mutex)  # Wait for signal.
                self.mutex.unlock()

                if not self.running:
                    break

                # Check if a tampering event occurred.
                self._check()

        except exc.TamperingEvent as e:
            print("tampering in run() mani_mgr:", e)

            # Warn and do countdown and then action here or sep funcs.
            # TODO: implement!

    @Slot(bool)
    def on_updated(self, updated: bool) -> None:
        """
        Slot to receive the updated devices from the MonitorManager.

        :param updated: True if the devices were updated,
            False otherwise.
        :type updated: bool
        :return: None
        """

        print("on_updated() called")

        # Get current device states.
        self.devices = self.moni_mgr.devices

        # Unlock the condition to check for tampering events.
        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()

    def _check(self) -> None:
        """
        Check for tampering events. It is called if moni_mgr emitted
        updated signal, so our on_updated func unlocks the condition
        and this function is called.

        :raises exc.TamperingEvent: If tampering is detected.
        :return: None
        """

        print("_check() called")


# TODO:
#   - Monitor als eigener manager (Qthread) -> nur für device fetching
#   zuständig und ui updates
#   - Worker umbenennen in evtl Tamper/Guard/Watcher/ManipulationManager
#   - Countdown als eigener qthread (Teil von ManipMgr. Wenn countdown
#   sound an ist, dann entsprechend sound abspielen, ansonsten einfach
#   normal zeit sleepen)
#   - ManipMgr hat countdown klasse inne, fetcht vom monitormgr die
#   devices und entscheidet (mit whitelist) ob tamper und gibt final
#   call an helper
#   - Monitor hat ein updated signal das nur ausgelöst wird, wenn sich
#   was bei den devices geändert hat (sparen wir uns UI updates)


class WorkerManager(QThread, metaclass=models.SingletonQt):
    """
    Manage the workers in threads etc. TODO: Description...
    """

    # Signals from thread state.
    running_sig: Signal = Signal(bool)
    status_sig: Signal = Signal(bool)
    error_sig: Signal = Signal(Exception)

    defused: bool = False
    armed: bool = True

    def __init__(self):

        super().__init__()

        # Thread management and communication.
        self.thread_id: str | None = None
        self.running: bool = False
        self.status: bool | None = None
        self.error: Exception | None = None
        self.mutex: QMutex = QMutex()
        self.condition: QWaitCondition = QWaitCondition()

        self.worker_usb = WorkerUSB()
        self.worker_bluetooth = WorkerBluetooth()
        self.worker_network = WorkerNetwork()

        # All implemented interfaces to monitor.
        self.interfaces = ("USB", "Bluetooth", "Network")

        # Reuse workers -> Stopping does not delete its thread.
        # self.worker_usb.setAutoDelete(False)
        # self.worker_bluetooth.setAutoDelete(False)
        # self.worker_network.setAutoDelete(False)

        self._create_workers()

        # Start the run method/thread. Starts the ... TODO!
        self.start()

    def _create_workers(self):
        for inter in self.interfaces:
            worker_class = globals()[f"Worker{inter}"]
            worker_inst = worker_class()
            setattr(self, f"worker_{inter.lower()}", worker_inst)

    def _thread_id(self) -> str:
        """
        Get the thread ID of the worker and verify we are not running in
        the main thread, as this would block the GUI.

        :return: Unique thread ID.
        :rtype: str
        """

        # Worker in main thread is a critical blocking issue.
        if QThread.currentThread() is QGuiApplication.instance().thread():
            raise exc.BlockingMainThreadError(
                    f"{self.__class__.__qualname__} thread is running in the "
                    f"main thread and thus blocking the GUI!"
                    )

        try:
            return (str(QThread.currentThread()
                        ).split(sep=f"{self.__class__.__name__}(0x",
                                maxsplit=1,
                                )[1].split(sep=") at",
                                           maxsplit=1,
                                           )[0])

        except Exception as e:
            LOGGER.error(
                    f"Could not get the {self.__class__.__qualname__} thread "
                    f"ID. Generating random ID. "
                    f"{e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )
            return f"30000{random.randint(1000000, 9999999)}"

    @property
    def interfaces_pretty(self) -> str:
        """
        Get the enabled interfaces as a string.

        :return: Enabled interfaces as a pretty string representation.
        :rtype: str
        """

        # Old and ugly version, for reference.
        # res = ""
        # for i, inter in enumerate(self.interfaces, start=1):
        #
        #     if i == len(self.interfaces):
        #         res = res[:-2]
        #         res += f" & {inter}"
        #
        #     else:
        #         res += f"{inter}, "
        #
        # return res

        return " & ".join(
                [", ".join(self.interfaces[:-1]), self.interfaces[-1]]
                ) if len(self.interfaces) > 1 else self.interfaces[0]

    @property
    def interfaces_lookup(
            self
            ) -> dict[str, dict[str, [bool | list[devices.Devices] | int]]]:
        """
        Property to get all real-time parameters for monitoring.

        :return: Real-time parameters for monitoring.
        :rtype: dict[str, dict[str, [bool | list[devices.Devices] | int]]]
        """

        res = {}

        for inter in self.interfaces:
            res[inter] = {
                    "enabled": C.cfg.CFG[f"{inter.lower()}_enabled"],
                    "allowed": C.cfg.CFG[inter.lower()],
                    "interval": C.cfg.CFG["interval"],
                    }

        # We need to overwrite the sleep interval for network
        # monitoring, as it takes more time to fetch network devices.
        res["Network"]["interval"] = 15

        return res

    @Slot()
    def run(self):

        self.running = True
        self.running_sig.emit(True)
        self.thread_id = self._thread_id()

        LOGGER.info(f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"started monitoring the {self.interfaces_pretty} "
                    f"interface."
                    )

        network_sleep = 0

        try:
            while self.running:

                self.mutex.lock()

                # Wait for the interval time or until the thread is
                # woken up by the main app.
                self.condition.wait(self.mutex, C.cfg.CFG["interval"])
                network_sleep += C.cfg.CFG["interval"]

                self.mutex.unlock()

                if not self.running:
                    break

                # Run the monitoring (except for network).
                self.worker_usb.monitoring()
                self.worker_bluetooth.monitoring()

                # Network monitoring is done every 15 seconds, as it
                # takes more time to fetch network devices.
                if network_sleep >= 15:
                    self.worker_network.monitoring()
                    network_sleep = 0

        # Worker was stopped by the main app and the system profiler
        # was terminated, so we do not have to wait for its results.
        except exc.SystemProfilerTerminated:
            pass

        except exc.TamperingEvent as e:
            # Warn and log the user.
            LOGGER.warning("!!!!! MANIPULATION DETECTED !!!!!")
            LOGGER.warning(e)

            # Defuse/countdown mechanism.
            # TODO!!!

        except exc.MonitoringError as e:
            LOGGER.warning(f"Could not start worker: {e}")
            self.cb_error[self.interface] = e
            self.signals.error.emit(self.cb_error)

            # Stop the worker.
            self.stop()
            return

        except Exception as e:

            LOGGER.critical(
                    f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"found a critical issue. Stopping the thread."
                    )
            LOGGER.critical(f"{e.__class__.__name__}: {e} \n"
                            f"{traceback.format_exc()}"
                            )

            self.running = False
            self.running_sig.emit(False)
            self.error = e
            self.error_sig.emit(e)
            return

        LOGGER.info(f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"stopped monitoring the {self.interfaces_str} "
                    f"interface."
                    )

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

    def reset(self) -> None:
        """
        Reset defused worker and start it again. TODO!

        :return: None
        """
        ...

    def defuse(self) -> None:
        """

        :return: None
        """

        self.defused = True


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
                    actions.alert(sec=C.cfg.CFG["delay"])

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
