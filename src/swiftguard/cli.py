#!/usr/bin/env python3

"""
cli.py: Starting point of the command-line interface application.

You can use this module standalone without the GUI. Just run this
script in terminal or to use poetry check the README.md -> Usage -> CLI.
For changing settings and allowing devices, have a look in
~/Library/Preferences/swiftguard/swiftguard.ini.

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
A list of all full names can be found in the utils/helpers.py file.

ALTERNATIVE: Insert USB device, start the application (GUI) and add the
device to the whitelist in the settings menu. Close the application and
start this script. The device should be allowed now.
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
import signal
import sys

from swiftguard.utils.helpers import startup
from swiftguard.utils.log import LogCount, create_logger, set_level_dest
from swiftguard.utils.workers import Worker, Workers

# Root logger and log counter.
LOG_COUNT = LogCount()
LOGGER = create_logger(LOG_COUNT)


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    The handle_exception function is a custom exception handler that
    logs uncaught exceptions to the log file with the level CRITICAL.
    Finally, it calls the exit_handler function to exit the program.

    :param exc_type: Store the exception type
    :param exc_value: Get the exception value
    :param exc_traceback: Get the traceback object
    :return: None
    """

    # Do not log KeyboardInterrupt (Ctrl+C).
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    LOGGER.critical(
        "Uncaught Exception:",
        exc_info=(exc_type, exc_value, exc_traceback),
    )

    exit_handler(error=True)


def exit_handler(signum=None, frame=None, error=False):
    """
    The exit_handler function is a signal handler that catches the
    SIGINT and SIGTERM signals. It then prints out a message to the
    log file, and exits with status 0.

    :param signum: Identify the signal that caused the exit_handler
        to be called
    :param frame: Reference the frame object that called function
    :param error: If True, an error occurred which caused the exit
    :return: The exit_handler function
    """

    # If error is True, an error occurred which caused the exit.
    if error:
        code = 1
        LOGGER.critical(
            "A critical error occurred that caused the application "
            "to exit unexpectedly."
        )

    else:
        code = 0
        LOGGER.info("Exiting the application properly ...")

    sys.exit(code)


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

    # Register handlers for clean exit of program.
    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]:
        signal.signal(sig, exit_handler)

    # Set the exception hook.
    sys.excepthook = handle_exception

    # Startup.
    config = startup()

    # Set log level (1,2,3,4,5) and destination (file, syslog, stdout).
    set_level_dest(LOGGER, config)

    # Print worker start message, but only if not logging to stdout.
    if "stdout" not in config["Application"]["log"]:
        print("Start guarding the USB ports ...", file=sys.stdout)



    # Create worker and start main worker loop.
    Workers.config = config
    worker = Worker("USB")
    worker.loop()

    # Exit program.
    sys.exit(0)


# You can also just start the script with python3 -m swiftguard.cli
# instead of python3 -m swiftguard.
if __name__ == "__main__":
    main()
