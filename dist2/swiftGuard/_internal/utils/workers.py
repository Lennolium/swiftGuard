#!/usr/bin/env python3

"""
workers.py: This module implements the main worker object/loop, which is
a subclass of QObject. It guards the usb ports and detects manipulation.
It also executes the user defined action, if a manipulation is detected.
The worker is started by the main application, runs in a separate thread
and is stopped if the user defuses the countdown.

NOTE: You can use this module standalone without the GUI. Just run this
script in terminal. For changing settings and allowing devices, have a
look in ~/Library/Preferences/swiftguard/swiftguard.ini.

WHITELIST: Insert your USB device, open a terminal and run the command:
'system_profiler SPUSBDataType -xml -detailLevel mini'.

Search your device and copy 'vendor_id', 'product_id' (both without 0x),
serial_num and _name. Insert them in the whitelist section of the config
file using the following format:
('vendor_id', 'product_id', 'serial_num', '_name')

Separate multiple devices with a comma and a space. Example:
devices = ('apple_vendor_id', '12a8', '000012345ABCD123456789',
'iPhone 13 Pro'), ('0123', '6110', '00001234ABCDE123', 'UsbStick')

For Apple devices, use the full name. Example: iPhone -> iPhone 13 Pro.
A list of all full names can be found in the helpers.py file.

ALTERNATIVE: Insert USB device, start the application (GUI) and add the
device to the whitelist in the settings menu. Close the application and
start this script. The device should be allowed now.
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.2"
__build__ = "2023.2"
__date__ = "2023-10-09"
__status__ = "Prototype"

# Imports.
import logging
from ast import literal_eval
from collections import Counter
from time import sleep

from PySide6.QtCore import QObject, Signal

from swiftguard.const import CONFIG_FILE
from swiftguard.utils.helpers import (
    bt_devices,
    devices_state,
    hibernate,
    shutdown,
    usb_devices,
    )

# Child logger.
LOGGER = logging.getLogger(__name__)


class Workers(QObject):
    # Class variables (shared between all instances of the class, e.g.
    # to pass an updated config to running workers or to defuse all
    # running workers instances).
    tampered_sig = Signal()
    tampered = False
    config = None
    defused = False


class Worker(Workers):
    def __init__(self, interface):
        super().__init__()

        # The interface attribute defines if the worker is checking for
        # USB, Bluetooth or any other device interface.
        self.interface = interface
        self.running = False
        self.tampered_var = False
        self._isRunning = True
        self.start_devices_count = None
        self.allowed_devices = None

        # Updated/load the whitelist.
        self.updated_whitelist()

    def stop(self):
        """
        The stop function sets the _isRunning variable to False, which
        will cause the worker stop running.

        :param self: Represent the instance of the class
        :return: None
        """
        self._isRunning = False
        self.running = False

    def whitelist(self):
        # Parse allowed devices from config file.
        try:
            allowed_devices = literal_eval(
                f"[{self.config['Whitelist'][self.interface.lower()]}]"
            )
            return allowed_devices

        except Exception as e:
            raise e from RuntimeError(
                f"Could not parse allowed devices from config "
                f"file. Please check your config file at {CONFIG_FILE} "
                f"for right formatting.\nExiting ... \nError: {str(e)}"
            )

    def updated_whitelist(self):
        # Get the allowed devices from config file.
        self.allowed_devices = self.whitelist()

        # Get all connected devices at startup.
        if self.interface == "USB":
            start_devices = usb_devices()
        elif self.interface == "Bluetooth":
            start_devices = bt_devices()
        else:
            raise RuntimeError(f"Unknown interface: {self.interface}.")

        # Remove allowed devices from start devices. They are
        # allowed to disconnect and connect freely.
        if self.allowed_devices:
            # Remove allowed devices from start devices.
            for device in self.allowed_devices:
                if device in start_devices:
                    start_devices.remove(device)

        # Count of each device at startup (minus allowed devices).
        self.start_devices_count = Counter(start_devices)

    def loop(self):
        """
        The loop function is the main function of the worker. It checks
        the interface for changes (new devices, removed devices).

        :param self: Refer to the instance of the class
        :return: None
        """

        # Get all connected devices at startup.
        if self.interface == "USB":
            start_devices = usb_devices()
        elif self.interface == "Bluetooth":
            start_devices = bt_devices()
        else:
            raise RuntimeError(f"Unknown interface: {self.interface}.")

        # Remove allowed devices from start devices. They are
        # allowed to disconnect and connect freely.
        if self.allowed_devices:
            # Remove allowed devices from start devices.
            for device in self.allowed_devices:
                if device in start_devices:
                    start_devices.remove(device)

        # Count of each device at startup (minus allowed devices).
        self.start_devices_count = Counter(start_devices)

        # Start the main working loop.
        LOGGER.info(
            f"Start guarding the {self.interface} interface ..."
            f"{devices_state(self.interface)}"
        )
        self.running = True

        # Main loop.
        while self.running:
            # Sleep for the user defined interval.
            sleep(float(self.config["User"]["check_interval"]))

            # List of currently connected devices.
            if self.interface == "USB":
                current_devices = usb_devices()
            elif self.interface == "Bluetooth":
                current_devices = bt_devices()
            else:
                raise RuntimeError(f"Unknown interface: {self.interface}.")

            # Remove allowed devices from current devices. They are
            # allowed to disconnect and connect freely. We do not need
            # to check them.
            if self.allowed_devices:
                # Remove allowed devices from current devices.
                for device in self.allowed_devices:
                    if device in current_devices:
                        current_devices.remove(device)

            # Counting the number current connected devices.
            current_devices_count = Counter(current_devices)

            # Check if current devices and their occurrences are equal
            # to start devices. No change -> start next loop iteration
            # and skip the rest of the loop.
            if self.start_devices_count == current_devices_count:
                continue

            # Not whitelisted device was added.
            elif current_devices_count > self.start_devices_count:
                dev = current_devices_count - self.start_devices_count
                LOGGER.warning(
                    f"Non-whitelisted {self.interface}-device added:"
                    f" {str(dev)[9:-5]}."
                )

            # Not whitelisted device was removed.
            else:
                dev = self.start_devices_count - current_devices_count
                LOGGER.warning(
                    f"Non-whitelisted {self.interface}-device removed:"
                    f" {str(dev)[9:-5]}."
                )

            # Log current state.
            LOGGER.warning(
                f"Manipulation detected!{devices_state(self.interface)}"
            )

            # Emit tampered_sig signal to main app: Worker detected a
            # manipulation.
            self.tampered_sig.emit()
            self.tampered = True

            # Stop the next run of the worker main loop.
            self.running = False

            # If delay time specified, wait for defuse by user.
            action = self.config["User"]["action"]
            delay = int(self.config["User"]["delay"])
            if delay != 0:
                # Log that countdown started.
                LOGGER.warning(
                    f"Countdown till {action} started: {delay} s.",
                )

                for i in range(delay):
                    sleep(1)

                    # Check if worker was defused by main app.
                    if self.defused:
                        # Reset defused variable.
                        self.defused = False
                        LOGGER.warning(
                            "The Countdown was defused by user! Remaining "
                            f"time: {delay - i} s.",
                        )

                        return

                # Log that countdown ended.
                LOGGER.warning("The Countdown ended. No defuse in time!")

            # Execute action.
            LOGGER.warning(
                f"Now executing action: {action}."
                f"{devices_state(self.interface)}"
            )

            if action == "hibernate":
                hibernate()
            else:
                shutdown()

        # Exit the function and return.
        return
