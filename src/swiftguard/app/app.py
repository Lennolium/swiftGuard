#!/usr/bin/env python3

"""
app.py: TODO: Headline...

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2025.1"
__date__ = "2024-03-04"
__status__ = "Development"

# Imports.
import logging
import random
import traceback

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

from swiftguard.app import window
from swiftguard.ui import dialogs
from swiftguard.utils import helpers, hotkey, notify, process
from swiftguard.init import exceptions as exc, models
from swiftguard.constants import C
from swiftguard.core import (helper, integrity, monitor, workers, actions,
                             devices)

# Child logger.
LOGGER = logging.getLogger(__name__)


class SwiftGuardApp(QApplication, metaclass=models.SingletonQt):
    """
    SwiftGuardApp class for the main application instance.
    TODO: Description...
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        helpers.parse_args(*args)

        self.thread_id = self._thread_id()
        LOGGER.info(f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"started initializing itself in MainThread."
                    )

        self.worker_usb = None
        self.worker_bluetooth = None
        self.worker_network = None

        # Workers states.
        self.worker_usb_running = False
        self.worker_bluetooth_running = False
        self.worker_network_running = False

        self.connected_devices = None

        # Start the application UI.
        self.window = window.MainWindow()

        # Start HelperManager and connect to privileged helper.
        self.helper_mgr = helper.HelperManager()

        # self.workers_toggle()

        # TODO: remove later.
        C.cfg.CFG["autostart"] = False
        C.cfg.CFG["email_enabled"] = True
        C.cfg.CFG["take_photo"] = True
        C.cfg.CFG["delay_sound"] = True

        # Check for auto-start and install launch agent, if necessary.
        from swiftguard.utils import launch
        self.launchagent_mgr = launch.LaunchAgentManager()

        # Check for new updates.
        from swiftguard.utils import update
        self.update_mgr = update.UpdateManager()

        # Initialize the hotkey manager.
        self.hotkey_mgr = hotkey.HotKeyManager()

        # Initialize the notification manager for sending an email, when
        # tampering is detected.
        self.notification_mgr = notify.NotificationManager()

        # Start IntegrityManager (runtime manipulation detection).
        self.integrity_mgr = integrity.IntegrityManager()
        self.integrity_mgr.error_sig.connect(self.integrity_error)

        self.monitor_mgr = monitor.MonitorManager()
        self.monitor_mgr.updated_sig.connect(self.on_updated)

        self.manipulation_mgr = workers.ManipulationManager()

        # self.countdown = workers.Countdown()
        # self.countdown.start()
        #
        # from PySide6.QtCore import QTimer
        # QTimer.singleShot(4000, self.test_countdown)
        #
        # QTimer.singleShot(10000, self.countdown.start)

        # self.integrity_mgr.stop()
        # self.threadpool.

        # TODO: change depending on state.
        # Change tooltip (hovering over the tray icon).
        # xself.tray.setToolTip(
        #         f"swiftGuard\nGuarding ..."
        #        )

        # raise exc.NotMainThreadError("Test Exception")
        # Test exception.
        # from PySide6.QtCore import QTimer
        # QTimer.singleShot(5000, self.raise_lol)

        # raise exc.NotMainThreadError("Test Exception")

        # TODO: at end send signal to main window to update its UI.

    def on_updated(self):
        print(self.monitor_mgr.devices)

    def test_countdown(self):
        print("defuse called!")
        self.countdown.defuse()

    def exit(self, retcode: int = 0) -> None:
        """
        Exit the SwiftGuardApp instance and log the exit. Gets called
        automatically from the QApplication instance.

        :param retcode: The return code of the application.
        :type retcode: int
        :return: None
        """

        super().exit()

        LOGGER.info(f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"exited with return code: {retcode}"
                    )

    def _thread_id(self) -> str:
        """
        Get the current thread ID of the SwiftGuardApp instance.

        :raises NotMainThreadError: If the SwiftGuardApp instance is not
            running in the MainThread.
        :return: The thread ID of the SwiftGuardApp instance.
        :rtype: str
        """

        thread_id = None

        try:
            thread_id = (str(self.thread()
                             ).split(sep=f"QThread(0x",
                                     maxsplit=1,
                                     )[1].split(sep=", name = ",
                                                maxsplit=1,
                                                )[0])

        except Exception as e:
            LOGGER.error(
                    f"Could not get the {self.__class__.__qualname__} thread "
                    f"ID. Generating random ID. "
                    f"{e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )
            thread_id = f"30000{random.randint(1000000, 9999999)}"

        # No exception raised -> Verify that we run in MainThread.
        else:
            if self.thread().isMainThread() is False:
                raise exc.NotMainThreadError(
                        f"{self.__class__.__qualname__} thread is not "
                        f"running in the MainThread."
                        )

        finally:
            return thread_id

    def raise_lol(self):
        raise exc.HelperError("Test Exception here we go!")

    def alert_manipulation(self):
        print("ALERT ...")
        self.window.inter_usb.toggle_manipulation()

    def integrity_error(self, cb_error):
        print("Integrity error:", cb_error)
        dialogs.show_integrity_dialog(cb_error)

        # raise cb_error

    def defuse(self):

        # Defuse all workers, but they keep running ...
        for worker in (self.worker_usb,
                       self.worker_bluetooth,
                       self.worker_network):
            if worker:
                worker.defuse()

        # ... so we stop them now.
        self.workers_toggle(force_stop=True)

    def running(self, cb_running):

        return

        print("----------------------------------")

        if cb_running[0] == "USB":
            self.worker_usb_running = cb_running[1]
            print("USB:", self.worker_usb_running)
        elif cb_running[0] == "Bluetooth":
            self.worker_bluetooth_running = cb_running[1]
            print("Bluetooth:", self.worker_bluetooth_running)
        elif cb_running[0] == "Network":
            self.worker_network_running = cb_running[1]
            print("Network:", self.worker_network_running)

        print("----------------------------------")

    def error(self, cb_error):
        for interface in cb_error:
            if cb_error[interface]:
                msg = "Error in thread: \n", "".join(
                        traceback.format_exception(
                                type(cb_error[interface]),
                                value=cb_error[interface],
                                tb=cb_error[interface].__traceback__
                                )
                        )

                LOGGER.error(msg)

    def tampering(self,
                  cb_tampering: tuple[
                      exc.TamperingEvent,
                      devices.Devices,
                      str]
                  ):
        print("Tampering signal to app.py ...")

        # Sending notification email if enabled.
        try:
            if self.notification_mgr:
                self.notification_mgr.prepare(
                        device=str(cb_tampering[1]),
                        device_action=cb_tampering[2],
                        device_interface=cb_tampering[1].__class__.__name__,
                        )
                self.notification_mgr.send()

        except exc.NotificationError as e:
            LOGGER.error(f"Failed to send notification email. Error: "
                         f"{e.__class__.__name__}: {e} \n"
                         f"{traceback.format_exc()}"
                         )

        # Initiating the counter-measure (shutdown, hibernate, ...)
        if C.cfg.CFG["action"] == "hibernate":
            actions.hibernate()
        else:
            actions.shutdown()

    def devices_state(self, cb_devices: dict):

        # self.window.update_devices(cb_devices)
        self.window.inter_usb.update_devices(cb_devices)

    def workers_toggle(self, force_stop: bool = False):

        # When quiting or after exceptions, stop all workers.
        if force_stop:
            LOGGER.debug("Stopping all workers ...")
            self._workers_stop("USB")
            self._workers_stop("Bluetooth")
            self._workers_stop("Network")

        else:
            # USB (enabled by default).
            if C.cfg.CFG["usb_enabled"]:
                self._workers_start("USB")
            else:
                self._workers_stop("USB")

            # Bluetooth (if enabled).
            if C.cfg.CFG["bluetooth_enabled"]:
                self._workers_start("Bluetooth")
            else:
                self._workers_stop("Bluetooth")

            # Network (if enabled).
            if C.cfg.CFG["network_enabled"]:
                self._workers_start("Network")
            else:
                self._workers_stop("Network")

    def _workers_stop(self, interface: str):
        if interface == "USB":
            if self.worker_usb and not self.worker_usb.stopped:
                self.worker_usb.stop()
        elif interface == "Bluetooth":
            if self.worker_bluetooth and not self.worker_bluetooth.stopped:
                self.worker_bluetooth.stop()
        elif interface == "Network":
            if self.worker_network and not self.worker_network.stopped:
                self.worker_network.stop()
        else:
            raise exc.BusNotSupportedError(
                    f"Unknown interface: {interface}."
                    )

    def _workers_start(self, interface: str):

        if interface.lower() == "usb":
            # if not hasattr(self, "worker_usb"):
            if not self.worker_usb:
                self.worker_usb = workers.WorkerUSB()
                self.worker_usb.signals.running.connect(self.running)
                self.worker_usb.signals.error.connect(self.error)
                self.worker_usb.signals.tampering.connect(self.tampering)
                self.worker_usb.signals.detected.connect(
                        self.alert_manipulation
                        )
                self.worker_usb.signals.devices.connect(self.devices_state)
                self.worker_usb.setAutoDelete(False)  # Reuse worker.

            if self.worker_usb.stopped:
                self.threadpool.start(self.worker_usb)

        elif interface.lower() == "bluetooth":
            if not self.worker_bluetooth:
                self.worker_bluetooth = workers.WorkerBluetooth()
                self.worker_bluetooth.signals.running.connect(self.running)
                self.worker_bluetooth.signals.error.connect(self.error)
                self.worker_bluetooth.signals.tampering.connect(self.tampering)
                self.worker_bluetooth.signals.devices.connect(
                        self.devices_state
                        )
                self.worker_bluetooth.setAutoDelete(False)

            if self.worker_bluetooth.stopped:
                self.threadpool.start(self.worker_bluetooth)

        elif interface.lower() == "network":
            if not self.worker_network:
                self.worker_network = workers.WorkerNetwork()
                self.worker_network.signals.running.connect(self.running)
                self.worker_network.signals.error.connect(self.error)
                self.worker_network.signals.tampering.connect(self.tampering)
                self.worker_network.signals.devices.connect(self.devices_state)
                self.worker_network.setAutoDelete(False)

            if self.worker_network.stopped:
                self.threadpool.start(self.worker_network)

        else:
            raise exc.BusNotSupportedError(f"Unknown interface: {interface}.")

        # TODO: Remove debug/testing code:
        from swiftguard.core import devices

        C.cfg.CFG["network_strict"] = True
        C.cfg.CFG["action"] = "hibernate"
        C.cfg.CFG["delay"] = 15
        C.cfg.CFG["delay_sound"] = False

        device = devices.USB(vendor_id="0951",
                             product_id="1666",
                             serial_num="408D5CE4B641E460A93A486B",
                             name="DataTraveler 3.0",
                             manufacturer="Kingston"
                             )

        # cfg.CFG.whitelist(device=device, add=True)
        # print("WHITELIST:", cfg.CFG["usb"])
