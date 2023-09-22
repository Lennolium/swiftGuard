#!/usr/bin/env python3

"""
worker.py: This module implements the main worker object/loop, which is
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
__version__ = "0.0.1"
__date__ = "2023-09-21"
__status__ = "Prototype"

# Imports.
import os
import re
import signal
import sys
from ast import literal_eval
from collections import Counter
from time import sleep

from PySide6.QtCore import QObject, Signal

from helpers import hibernate, log, shutdown, startup, usb_devices

# Constants.
CURRENT_PLATFORM = os.uname()[0].upper()
USER_HOME = os.path.expanduser("~")
APP_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = f"{USER_HOME}/Library/Preferences/swiftguard/swiftguard.ini"
LOG_FILE = f"{USER_HOME}/Library/Logs/swiftguard/swiftguard.log"

# Precompiled regex for device detection.
DEVICE_RE = [
    re.compile(".+ID\s(?P<id>\w+:\w+)"),
    re.compile("0x([0-9a-z]{4})"),
]


class Worker(QObject):
    # Signal to emit when a manipulation/new usb device is detected.
    tampered = Signal()

    def __init__(self, config):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the initial state of the object.

        :param self: Represent the instance of the class
        :param config: Pass in the config file
        :return: The self object
        """

        super().__init__()
        self.config = config
        self.running = False
        self.tampered_var = False
        self.defused = False
        self._isRunning = True

    def stop(self):
        """
        The stop function sets the _isRunning variable to False, which
        will cause the worker stop running.

        :param self: Represent the instance of the class
        :return: The value of the _isRunning variable
        """
        self._isRunning = False

    def loop(self):
        """
        The loop function is the main function of the worker. It checks
        the USB ports for changes.

        :param self: Refer to the instance of the class
        :return: None
        """

        # Get check interval from config file (how long to wait)
        check_interval = float(self.config["User"]["check_interval"])

        # Get delay time till action execution.
        delay = int(self.config["User"]["delay"])

        action = self.config["User"]["action"]

        # Parse allowed devices from config file.
        try:
            allowed_devices = literal_eval(
                f"[{self.config['Whitelist']['devices']}]"
            )

        # If parsing fails, log to file and exit program.
        except Exception as e:
            log(
                2,
                f"Could not parse allowed devices from config "
                f"file. Please check your config file at {CONFIG_FILE} "
                f"for right formatting.\nExiting ... \nError: {e}",
            )
            sys.exit(1)

        # Get all connected usb devices at startup.
        start_devices = usb_devices()

        # Remove allowed devices from start devices. They are
        # allowed to disconnect and connect freely.
        if allowed_devices:
            # Remove allowed devices from start devices.
            for device in allowed_devices:
                if device in start_devices:
                    start_devices.remove(device)

        # Count of each device at startup (minus allowed devices).
        start_devices_count = Counter(start_devices)

        self.running = True
        self.defused = False

        # Write to logs that loop is starting.
        log(0, "Start guarding the USB ports ...")

        # Main loop.
        while self.running:
            # Sleep for the user defined interval.
            sleep(check_interval)

            # List the current usb devices.
            current_devices = usb_devices()

            # Remove allowed devices from current devices. They are
            # allowed to disconnect and connect freely. We do not need
            # to check them.
            if allowed_devices:
                # Remove allowed devices from current devices.
                for device in allowed_devices:
                    if device in current_devices:
                        current_devices.remove(device)

            # Counting the number current connected devices.
            current_devices_count = Counter(current_devices)

            # Check if current devices and their occurrences are equal
            # to start devices. No change -> start next loop iteration.
            if start_devices_count == current_devices_count:
                continue

            if current_devices_count > start_devices_count:
                usb = current_devices_count - start_devices_count
                log(1, f"Non-whitelisted USB-device added: {str(usb)[9:-5]}")

            else:
                usb = start_devices_count - current_devices_count
                log(1, f"Non-whitelisted USB-device removed: {str(usb)[9:-5]}")

            # Log current state.
            log(1, "Manipulation detected!", True)

            # Emit tampered signal the main app: worker detected a
            # manipulation.
            self.tampered.emit()
            self.tampered_var = True

            # Stop the next run of the worker main loop.
            self.running = False

            # Wait for delay time.
            if delay != 0:
                # Log that countdown started.
                log(
                    1,
                    "Countdown till action execution started: "
                    f""
                    f"{delay} s. ",
                )

                for i in range(delay):
                    sleep(1)

                    # Check if worker was defused by main app.
                    if self.defused:
                        # Log current state.
                        log(
                            1,
                            "The Countdown was defused by user! Remaining "
                            f"time: {delay - i} s.",
                        )

                        return

                # Log that countdown ended.
                log(1, "The Countdown ended. No defuse in time!")

            # Log that action is executed.
            log(1, f"Now executing action: {action}", True)

            # Execute action.
            if action == "hibernate":
                hibernate()
            else:
                shutdown()

        # Exit the function and return.
        return


def main():
    """
    The main function is the entry point of the standalone script.
    It initializes and starts the main worker loop. It is not possible
    to defuse the countdown if a delay is set and the script is running
    standalone.

    NOTE: For further instructions for using this script standalone,
    please refer to the header of this file.

    :return: None
    """

    config, exit_code = startup()

    def exit_handler(signum, frame):
        """
        The exit_handler function is a signal handler that catches the
        SIGINT and SIGTERM signals. It then prints out a message to the
        log file, and exits with status 0.

        :param signum: Identify the signal that caused the exit_handler
            to be called
        :param frame: Reference the frame object that called function
        :return: The exit_handler function
        """

        log(0, "Exiting the application properly ...")
        sys.exit(0)

    # Register handlers for clean exit of program.
    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]:
        signal.signal(sig, exit_handler)

    # Check if startup was successful (exit_code = 1 -> error).
    if exit_code == 1:
        log(
            2,
            (f"Startup failed, check logs at {LOG_FILE}" + "\nExiting " "..."),
        )
        sys.exit(1)

    # Create worker and start main worker loop.
    worker = Worker(config)
    worker.loop()

    # Exit program.
    sys.exit(0)


if __name__ == "__main__":
    main()
