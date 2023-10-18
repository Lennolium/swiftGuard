#!/usr/bin/env python3

"""
conf.py: Configuration file handling.

This module provides functions for creating, loading, and validating the
configuration file used by swiftGuard. It also defines default
configuration settings and handles writing the configuration file to
disk.
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
import configparser
import logging
import os
import shutil

from swiftguard import const

# Child logger.
LOGGER = logging.getLogger(__name__)


def create(force_restore=False):
    """
    The function is used to create a config file for the user. It will
    copy the default config file from the 'install' directory and place
    it in the user's home directory. If no config file exists, this
    function will be called by default when swiftGuard starts up.

    :param force_restore: Overwrite the config file with default values
    :return: None
    """

    # If no config file exists, copy the default config file.
    if os.path.isfile(const.CONFIG_FILE) and not force_restore:
        return
    try:
        # If no config directory exists, create it.
        if not os.path.isdir(os.path.dirname(const.CONFIG_FILE)):
            os.mkdir(os.path.dirname(const.CONFIG_FILE))

        # Copy config file to config dir or overwrite existing one.
        shutil.copy(
            os.path.join(const.APP_PATH, "install", "swiftguard.ini"),
            const.CONFIG_FILE,
        )

    except Exception as e:
        raise e from RuntimeError(
            f"Could not create config file at {const.CONFIG_FILE}!\n"
            f"Error: {str(e)}"
        )

    if force_restore:
        LOGGER.warning(
            f"Config file at {const.CONFIG_FILE} was overwritten with "
            f"default values."
        )
        return

    LOGGER.info(f"Created config file at {const.CONFIG_FILE}.")


def validate(config):
    """
    The validate function checks if the config file is valid.
    It checks if all sections and options are present and if the values
    are valid. If not, it will overwrite the config file with default
    values.

    :param config: Pass the config object to be checked
    :return: A configparser object, our validated/sanitized config file
    """

    conf_default = {
        "Application": ["version", "log", "log_level", "check_updates"],
        "User": ["autostart", "action", "delay", "check_interval"],
        "Email": ["enabled", "name", "email", "smtp"],
        "Whitelist": ["usb", "bluetooth"],
    }

    for key, value in conf_default.items():
        for item in value:
            if not config.has_option(key, item):
                create(force_restore=True)
                config.read(const.CONFIG_FILE, encoding="utf-8")

                # Further checks are not needed, because of overwrite.
                return config

    # Defaulting some values if incorrect or not set.
    default_needed = False

    log_dest = config["Application"]["log"]
    # Check length of string (4: 'file' to 20: 'file, syslog, stdout').
    if not 4 <= len(log_dest) <= 20:
        config["Application"]["log"] = "file"
        log_dest = "file"
        default_needed = True

    log_dest = log_dest.split(", ")

    # Check if 'log to' options are valid (file, syslog, stdout).
    for dest in log_dest:
        if dest not in ["file", "syslog", "stdout"]:
            config["Application"]["log"] = "file"
            default_needed = True

    # Check if log_level is in valid bounds (1,2,...,5).
    if config["Application"]["log_level"] not in ["1", "2", "3", "4", "5"]:
        config["Application"]["log_level"] = "2"
        default_needed = True

    # Check if update checking is either 1 (True) or 0 (False).
    if config["Application"]["check_updates"] not in ["0", "1"]:
        config["User"]["check_updates"] = "1"
        default_needed = True

    # Check if autostart is either 1 (True) or 0 (False).
    if config["User"]["autostart"] not in ["0", "1"]:
        config["User"]["autostart"] = "1"
        default_needed = True

    # Check if action is valid option.
    if config["User"]["action"] not in ["shutdown", "hibernate"]:
        config["User"]["action"] = "shutdown"
        default_needed = True

    # Check if delay is convertable to an integer and not negative.
    if not config["User"]["delay"].isdecimal():
        config["User"]["delay"] = "0"
        default_needed = True

    elif int(config["User"]["delay"]) < 0:
        config["User"]["delay"] = "0"
        default_needed = True

    # Check if check_interval is convertable to a float.
    try:
        float(config["User"]["check_interval"])
    except ValueError:
        config["User"]["check_interval"] = "1.0"
        default_needed = True

    # Check if check_interval is negative.
    if float(config["User"]["check_interval"]) <= 0:
        config["User"]["check_interval"] = "0.5"
        default_needed = True

    if config["Email"]["enabled"] not in ["0", "1"]:
        config["Email"]["enabled"] = "0"
        config["Email"]["name"] = ""
        config["Email"]["email"] = ""
        config["Email"]["smtp"] = ""
        default_needed = True

    if config["Email"]["name"] != "":
        if not config["Email"]["name"].replace(" ", "").isalpha():
            config["Email"]["enabled"] = "0"
            config["Email"]["name"] = ""
            config["Email"]["email"] = ""
            config["Email"]["smtp"] = ""
            default_needed = True

    if config["Email"]["email"] != "":
        if not const.DEVICE_RE[2].match(config["Email"]["email"]):
            config["Email"]["enabled"] = "0"
            config["Email"]["name"] = ""
            config["Email"]["email"] = ""
            config["Email"]["smtp"] = ""
            default_needed = True

    if config["Email"]["smtp"] != "":
        if not const.DEVICE_RE[3].match(config["Email"]["smtp"]):
            config["Email"]["enabled"] = "0"
            config["Email"]["name"] = ""
            config["Email"]["email"] = ""
            config["Email"]["smtp"] = ""
            default_needed = True

    # If default values were needed, write config file on disk.
    if default_needed:
        LOGGER.warning(
            f"One or more values in {const.CONFIG_FILE} were incorrect or not "
            f"set. Corrected them to default values and wrote config file "
            f"on disk.",
        )
        write(config)

    return config


def load(config):
    """
    The load function loads the config file and checks if its
    content is valid and complete by calling the validate
    function. If any errors occur, the config file will be overwritten
    with default config.

    :param config: Pass the config object to this function
    :return: A configparser object
    """

    # Parse config file.
    try:
        config.read(const.CONFIG_FILE, encoding="utf-8")

    except (
        configparser.MissingSectionHeaderError,
        configparser.ParsingError,
    ) as e:
        LOGGER.error(f"Error while parsing config file: {str(e)}.")
        create(force_restore=True)
        config.read(const.CONFIG_FILE, encoding="utf-8")

        # Further checks are not needed, because of overwrite.
        return config

    # Validate and sanitize loaded config.
    config = validate(config)

    return config


def write(config):
    """
    The write function writes the config file to disk.

    :param config: The config object to be written to disk
    :return: None
    """

    with open(const.CONFIG_FILE, "w", encoding="utf-8") as config_file:
        config.write(config_file)
