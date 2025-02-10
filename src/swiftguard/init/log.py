#!/usr/bin/env python3

"""
Implements the logging manager for the application.

The logging manager creates a logger with a file, a stdout and a syslog
handler. It also provides a custom log counter to count warnings,
errors and criticals. Use like the standard logging methods:

    - from log import LoggingManager
    - LOGGER = LoggingManager()
    - LOGGER.error("Error message to log...")
    - LOGGER.counter.errors  >> 1
    - LOGGER.reset_counter()
    - LOGGER.set_level(logging.DEBUG)
    - LOGGER.logger >> <Logger swiftguard (DEBUG)>
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "swiftguard@lennolium.dev"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2023.3"
__date__ = "2023-10-09"
__status__ = "Development"

# Imports.
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

import pyoslog

from swiftguard.init import models


class _LogCount(logging.Handler):
    """
    Custom logging handler to count warnings, errors and criticals.

    :ivar warnings: Number of warnings.
    :type warnings: int
    :ivar errors: Number of errors.
    :type errors: int
    :ivar criticals: Number of criticals.
    :type criticals: int
    """

    def __init__(self) -> None:
        """
        Initialize the log counter.
        """

        super().__init__()
        self.warnings = 0
        self.errors = 0
        self.criticals = 0

    def __repr__(self):
        """
        Return a string representation of the log counter.

        :return: String representation of the log counter.
        :rtype: str
        """

        return (f"LogCount("
                f"warnings={self.warnings}, "
                f"errors={self.errors}, "
                f"criticals={self.criticals})")

    def emit(self, record) -> None:
        """
        Emit the log record and count warnings, errors and criticals.

        :param record: The log record.
        :type record: logging.LogRecord
        :return: None
        """

        if record.levelname == "WARNING":
            self.warnings += 1
        elif record.levelname == "ERROR":
            self.errors += 1
        elif record.levelname == "CRITICAL":
            self.criticals += 1


class LoggingManager(metaclass=models.Singleton):
    """
    Manager for logging in the application.
    """

    def __init__(
            self,
            log_file: Path,
            platform: str,
            default_level: int | str | "logging.Level" = logging.INFO,
            max_size: int = 2,
            max_files: int = 5,
            ) -> None:
        """
        Initialize the logging manager.

        :param default_level: Set the default log level (default:
            logging.INFO).
        :type default_level: logging.Level | int
        :param max_size: Maximum size of the log file in MB
            (default: 2).
        :type max_size: int
        :param max_files: Maximum number of log files to keep
            (default: 5).
        :type default_level: int
        """

        self._log_file = log_file
        self._platform = platform

        self._default_level = self._convert_level(default_level)
        self._max_size = max_size
        self._max_files = max_files

        self.counter = _LogCount()
        self.logger = self._create()

    def __repr__(self) -> str:
        """
        Return a string representation of the logging manager.

        :return: String representation of the logging manager.
        :rtype: str
        """

        return (f"LoggingManager("
                f"log_file={self._log_file}, "
                f"platform={self._platform}, "
                f"default_level={self._default_level}, "
                f"max_size={self._max_size}, "
                f"max_files={self._max_files})")

    @staticmethod
    def _convert_level(level: int | str | "logging.Level") -> int:
        """
        Convert the log level to an integer.

        :param level: The log level.
        :type level: int | str | "logging.Level"
        :return: The log level as integer.
        :rtype: int
        """

        if level not in (logging.DEBUG, logging.INFO, logging.WARNING,
                         logging.ERROR, logging.CRITICAL,
                         "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",
                         0, 10, 20, 30, 40, 50,):
            raise ValueError(f"Invalid log level supplied: '{level}'.")

        if isinstance(level, str):
            return getattr(logging, level.upper())
        else:
            return level

    def _create(self) -> logging.Logger:
        """
        Create the logger and add handlers for file, stdout and syslog.

        :return: The logger instance.
        :rtype: logging.Logger
        """

        # Root logger.
        logger = logging.getLogger()

        # Create parent folders if they do not exist.
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

        # Log file: Rotate log file every 2 MB and keep 5 old log files.
        file_handler = RotatingFileHandler(
                filename=self._log_file,
                backupCount=self._max_files,
                maxBytes=self._max_size * 1024 * 1024
                )

        # Stdout: Print log messages to stdout.
        stdout_handler = logging.StreamHandler(stream=sys.stdout)

        # Syslog/Console: Log to syslog on macOS and to console on Linux.
        if self._platform == "macOS":
            syslog_handler = pyoslog.Handler()
            syslog_handler.setSubsystem("dev.lennolium.swiftguard", "client")
        else:
            syslog_handler = logging.StreamHandler(stream=sys.stderr)

        # Define format (level, timestamp, filename, line number, message).
        fmt = logging.Formatter(
                fmt="%(levelname)s | %(asctime)s | %(filename)s:%(lineno)s | "
                    "%(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
                )

        file_handler.setFormatter(fmt)
        stdout_handler.setFormatter(fmt)
        syslog_handler.setFormatter(fmt)

        logger.addHandler(self.counter)
        logger.addHandler(file_handler)
        logger.addHandler(stdout_handler)
        logger.addHandler(syslog_handler)

        # Set default log level.
        logger.setLevel(self._default_level)

        return logger

    def reset_counter(self) -> None:
        """
        Reset the counter for warnings, errors and criticals.

        :return: None
        """

        self.counter.warnings = 0
        self.counter.errors = 0
        self.counter.criticals = 0

    def set_level(self, level: int | str | "logging.Level") -> None:
        """
        Set the log level.

        :param level: Set the log level.
        :type level: logging.Level | int
        :return: None
        """

        self.logger.setLevel(self._convert_level(level))

    @property
    def debug(self) -> logging.Logger.debug:
        """
        Return the debug method of the logger. Use like the standard
        logging.debug method.

        :return: The debug method of the logger.
        :rtype: logging.Logger.debug
        """

        return self.logger.debug

    @property
    def info(self) -> logging.Logger.info:
        """
        Return the info method of the logger. Use like the standard
        logging.info method.

        :return: The info method of the logger.
        :rtype: logging.Logger.info
        """

        return self.logger.info

    @property
    def warning(self) -> logging.Logger.warning:
        """
        Return the warning method of the logger. Use like the standard
        logging.warning method.

        :return: The warning method of the logger.
        :rtype: logging.Logger.warning
        """

        return self.logger.warning

    @property
    def error(self) -> logging.Logger.error:
        """
        Return the error method of the logger. Use like the standard
        logging.error method.

        :return: The error method of the logger.
        :rtype: logging.Logger.error
        """

        return self.logger.error

    @property
    def critical(self) -> logging.Logger.critical:
        """
        Return the critical method of the logger. Use like the standard
        logging.critical method.

        :return: The critical method of the logger.
        :rtype: logging.Logger.critical
        """

        return self.logger.critical
