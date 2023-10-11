#!/usr/bin/env python3

"""
workers.py: This module implements the main worker object/loop, which is
a subclass of QObject. It guards the interface and detects manipulation.
It also executes the user defined action, if a manipulation is detected.
The worker is started by the main application, runs in a separate thread
and is stopped if the user defuses the countdown. There are many other
workers possible, one for each interface (USB, Bluetooth, ...).
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2023.3"
__date__ = "2023-10-09"
__status__ = "Development"

# Imports.
import logging
import subprocess
from ast import literal_eval
from collections import Counter

from PySide6.QtCore import QObject, QThread, Signal

from swiftguard.const import CONFIG_FILE
from swiftguard.utils.helpers import (
    bt_devices,
    devices_state,
    usb_devices,
    )

# Child logger.
LOGGER = logging.getLogger(__name__)


def shutdown():
    """
    This function will shut down the computer using AppleScript.

    :return: None
    """

    # AppleScript: slower, but only way to shut down without sudo.
    osascript_path = "/usr/bin/osascript"
    sd_process = subprocess.run(  # nosec B603
        [osascript_path, "-e", 'tell app "System Events" to shut down'],
    )

    # Check exit code of osascript for success.
    if sd_process.returncode != 0:
        # Fallback to hibernate.
        hibernate()

    # Return to prevent multiple execution.
    return


def hibernate():
    """
    This function will put the computer to sleep by trying two methods.

    :return: None
    """

    # First method/try (pmset, faster).
    pmset_path = "/usr/bin/pmset"
    subprocess.run([pmset_path, "sleepnow"])  # nosec B603

    # Second method/try (AppleScript, slower).
    osascript_path = "/usr/bin/osascript"
    subprocess.run(  # nosec B603
        [osascript_path, "-e", 'tell app "System Events" to sleep'],
    )

    # Return to prevent multiple execution.
    return


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
        self.update()

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

    def update(self):
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

        # Get the whitelist and start devices.
        self.update()

        # Start the main working loop.
        LOGGER.info(
            f"Start guarding the {self.interface} interface ..."
            f"{devices_state(self.interface)}"
        )
        self.running = True

        # Main loop.
        while self.running:
            # Sleep for the user defined interval.
            # sleep(float(self.config["User"]["check_interval"]))
            QThread.sleep(1)

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
                    QThread.sleep(1)

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
