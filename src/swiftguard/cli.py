#!/usr/bin/env python3

"""
cli.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.2"
__build__ = "2023.2"
__date__ = "2023-09-28"
__status__ = "Prototype"

# Imports.
import signal
import sys

from swiftguard.utils.helpers import startup
from swiftguard.utils.log import LogCount, add_handler, create_logger
from swiftguard.utils.workers import WorkerUsb

# Root logger and log counter.
LOG_COUNT = LogCount()
LOGGER = create_logger(LOG_COUNT)


# Handle uncaught exceptions and log them to CRITICAL.
def handle_exception(exc_type, exc_value, exc_traceback):
    # Do not log KeyboardInterrupt (Ctrl+C).
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    LOGGER.critical(
        "Uncaught Exception:",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


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

    LOGGER.info("Exiting the application properly ...")
    sys.exit(0)


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

    log_dest = config["Application"]["log"].split(", ")
    for dest in log_dest:
        # Logging to file is default (can not be disabled).
        if dest == "file":
            continue
        elif dest == "syslog":
            add_handler(LOGGER, "syslog")

        elif dest == "stdout":
            add_handler(LOGGER, "stdout")

    # Get log level from config file and apply it to the root logger.
    # 1 = DEBUG, 2 = INFO, 3 = WARNING, 4 = ERROR, 5 = CRITICAL.
    log_level = int(config["Application"]["log_level"]) * 10
    LOGGER.setLevel(log_level)

    # Create worker and start main worker loop.
    print("Start guarding the USB ports ...", file=sys.stdout)
    worker = WorkerUsb(config)
    worker.loop()

    # Exit program.
    sys.exit(0)


# You can also just start the script with python3 -m swiftguard.cli
# instead of python3 -m swiftguard.
if __name__ == "__main__":
    main()
