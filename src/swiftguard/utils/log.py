#!/usr/bin/env python3

"""
log.py: TODO: Headline...

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
import logging
import os
import platform
import sys
from logging.handlers import RotatingFileHandler

import pyoslog

# Constants.
CURRENT_PLATFORM = platform.uname()[0].upper()
USER_HOME = os.path.expanduser("~")
APP_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = f"{USER_HOME}/Library/Preferences/swiftguard/swiftguard.ini"
LOG_FILE = f"{USER_HOME}/Library/Logs/swiftguard/swiftguard.log"


# Custom logging handler to count warnings, errors and criticals.
class LogCount(logging.Handler):
    def __init__(self):
        super().__init__()
        self.warnings = 0
        self.errors = 0
        self.criticals = 0

    def emit(self, record):
        if record.levelname == "WARNING":
            self.warnings += 1
        elif record.levelname == "ERROR":
            self.errors += 1
        elif record.levelname == "CRITICAL":
            self.criticals += 1


def create_logger(counter):
    # Prepare directory for log file.
    if not os.path.isdir(os.path.dirname(LOG_FILE)):
        os.mkdir(os.path.dirname(LOG_FILE))

    # Create root logger.
    logger = logging.getLogger()

    # Stdout: Print log messages to stdout.
    # stdout_handler = logging.StreamHandler(stream=sys.stdout)

    # Log file: Rotate log file every 2 MB and keep 5 old log files.
    file_handler = RotatingFileHandler(
        LOG_FILE, backupCount=5, maxBytes=2000000
    )

    # Define format (level, timestamp, filename, line number, message).
    fmt = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s | %(filename)s:%(lineno)s | %("
        "message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    # Set the format for the handlers.
    # stdout_handler.setFormatter(fmt)
    file_handler.setFormatter(fmt)

    # Add the handlers to the logger (stdout, file and error counter).
    # logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)
    logger.addHandler(counter)

    # # Syslog/Console: Log to syslog on macOS and to console on Linux.
    # if CURRENT_PLATFORM == "DARWIN":
    #     syslog_handler = pyoslog.Handler()
    #     syslog_handler.setSubsystem("dev.lennolium.swiftguard", "client")
    #     logger.addHandler(syslog_handler)
    # elif CURRENT_PLATFORM == "LINUX":
    #     syslog_handler = logging.StreamHandler(stream=sys.stderr)
    #     logger.addHandler(syslog_handler)

    # Set the log level to default (INFO).
    logger.setLevel(logging.INFO)

    return logger


def add_handler(logger_obj, dest):
    if dest == "syslog":
        # Syslog/Console: Log to syslog on macOS and to console on Linux.
        if CURRENT_PLATFORM == "DARWIN":
            syslog_handler = pyoslog.Handler()
            syslog_handler.setSubsystem("dev.lennolium.swiftguard", "client")
        elif CURRENT_PLATFORM == "LINUX":
            syslog_handler = logging.StreamHandler(stream=sys.stderr)

        logger_obj.addHandler(syslog_handler)

    elif dest == "stdout":
        # Stdout: Print log messages to stdout.
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        # Define format (level, timestamp, filename, line number, message).
        fmt = logging.Formatter(
            fmt="%(levelname)s | %(asctime)s | %(filename)s:%(lineno)s | %("
            "message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        stdout_handler.setFormatter(fmt)

        logger_obj.addHandler(stdout_handler)

    return logger_obj
