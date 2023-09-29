#!/usr/bin/env python3

"""
helpers.py: Helper functions for main application and worker.

These functions are used by the main application and the worker to
perform logging, shutdown, hibernate, but also to do startup checks and
to perform fast usb device detection (macOS native).
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
import configparser
import os
import plistlib
import re
import shutil
import subprocess  # nosec
import sys
from datetime import datetime

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


def shutdown():
    """
    This function will shut down the computer using AppleScript.

    :return: None
    """

    # AppleScript: slower, but only way to shut down without sudo.
    osascript_path = "/usr/bin/osascript"
    sd_process = subprocess.run(
        [osascript_path, "-e", 'tell app "System Events" to shut down'],
    )  # nosec

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
    subprocess.run([pmset_path, "sleepnow"])  # nosec

    # Second method/try (AppleScript, slower).
    osascript_path = "/usr/bin/osascript"
    subprocess.run(
        [osascript_path, "-e", 'tell app "System Events" to sleep'],
    )  # nosec

    # Return to prevent multiple execution.
    return


def log(svt, msg, verbose=False):
    """
    The log function is used to log messages to the log file.

    :param svt: Determine the severity level of the log message
    :param msg: Specify the message to log
    :param verbose: Print the current usb state
    :return: None
    """

    # First startup: prepare directories for keeping log file.
    if not os.path.isfile(LOG_FILE):
        try:
            # Make sure there is a logging folder.
            if not os.path.isdir(os.path.dirname(LOG_FILE)):
                os.mkdir(os.path.dirname(LOG_FILE))

        except Exception as e:
            # Print error and exit.
            sys.exit(
                f"\n[ERROR] Could not create log file at "
                f"{LOG_FILE}!\nError: {e}."
            )

        else:
            # Log info.
            msg += (
                f"\n{datetime.now().strftime('[%Y/%m/%d %H:%M:%S]')}"
                f" [INFO] Created log file at {LOG_FILE}."
            )

    # Severity level (0 = info, 1 = warning, 2 = error).
    if svt == 0:
        contents = (
            f"{datetime.now().strftime('[%Y/%m/%d %H:%M:%S]')}"
            f" [INFO] {msg} \n"
        )

    elif svt == 1:
        contents = (
            f"{datetime.now().strftime('[%Y/%m/%d %H:%M:%S]')}"
            f" [WARNING] {msg} \n"
        )

    else:
        contents = (
            f"{datetime.now().strftime('[%Y/%m/%d %H:%M:%S]')}"
            f" [ERROR] {msg} \n"
        )

    # Log current USB state
    if verbose:
        system_profiler_path = "/usr/sbin/system_profiler"

        verbose_process = subprocess.run(
            [system_profiler_path, "SPUSBDataType"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )  # nosec

        # Check exit code of fdesetup for success.
        if verbose_process.returncode != 0:
            contents += (
                f"------ Current state: ------\n"
                f"Could not get current USB state! Error: "
                f"{verbose_process.stdout.strip()}"
            )

        else:
            contents += (
                f"------ Current state: ------\n"
                f"{verbose_process.stdout.strip()}"
            )

    # Write log to file.
    with open(LOG_FILE, "a+") as log:
        log.write(contents)


def config_create(force_restore=False):
    # TODO: docstring.

    # If no config file exists, copy the default config file.
    if not os.path.isfile(CONFIG_FILE) or force_restore:
        try:
            # If no config dir exists, create it.
            if not os.path.isdir(os.path.dirname(CONFIG_FILE)):
                os.mkdir(os.path.dirname(CONFIG_FILE))

            # Copy config file to config dir or overwrite existing one.
            shutil.copy(
                os.path.join(APP_PATH, "install", "swiftguard.ini"),
                CONFIG_FILE,
            )

        except Exception as e:
            # Log error.
            log(
                2,
                f"Could not create config file at {CONFIG_FILE}! "
                f"Error: {e}.",
            )

            # Return exit code 1 (Error occurred).
            return 1

        # Log success.
        log(0, f"Created config file at {CONFIG_FILE}.")

        # Return exit code 0 (Success).
        return 0


def config_load(config):
    """
    The config_load function loads the config file and checks if its
    content is valid and complete. If not, it will exit the program with
    an error message.

    :param config: Pass the config object to this function
    :return: A configparser object
    """

    try:
        config.read(CONFIG_FILE, encoding="utf-8")

    except (
        configparser.MissingSectionHeaderError,
        configparser.ParsingError,
    ) as e:
        # Log error.
        log(
            2,
            "Config file is not valid. Please check your config file "
            f"at {CONFIG_FILE} for missing sections.\nExiting..."
            f"\nError: {e}",
        )

        # Exit program. TODO: use exitcodes.
        sys.exit(1)

    # Check if config file has all needed sections and options.
    if not config.has_option("Application", "version"):
        restore_needed = True
    elif not config.has_option("User", "action"):
        restore_needed = True
    elif not config.has_option("User", "delay"):
        restore_needed = True
    elif not config.has_option("User", "check_interval"):
        restore_needed = True
    elif not config.has_option("Whitelist", "devices"):
        restore_needed = True
    else:
        restore_needed = False

    # Overwrite config file with default one.
    if restore_needed:
        config_create(force_restore=True)

    # Defaulting some values if incorrect or not set.
    default_needed = False

    # Check if action is valid option.
    if config["User"]["action"] not in ["shutdown", "hibernate"]:
        config["User"]["action"] = "shutdown"
        default_needed = True

        # Log warning.
        log(
            1,
            "Action set to default value 'shutdown', because "
            f"of invalid value in config file at {CONFIG_FILE}.",
        )

    # Check if delay is convertable to an integer and not negative.
    if config["User"]["delay"] == "":
        config["User"]["delay"] = "0"
        default_needed = True
    elif not config["User"]["delay"].isdecimal():
        config["User"]["delay"] = "0"
        default_needed = True

        # Log warning.
        log(
            1,
            "Delay set to default value '0', because of "
            f"invalid value in config file at {CONFIG_FILE}.",
        )

    elif int(config["User"]["delay"]) < 0:
        config["User"]["delay"] = "0"
        default_needed = True

        # Log warning.
        log(
            1,
            "Delay set to default value '0', because of "
            f"negative value in config file at {CONFIG_FILE}.",
        )

    # Check if check_interval is convertable to a float.
    try:
        float(config["User"]["check_interval"])
    except ValueError:
        config["User"]["check_interval"] = "1.0"
        default_needed = True

        # Log warning.
        log(
            1,
            "Check interval set to default value '1.0', because "
            f"of invalid value in config file at {CONFIG_FILE}.",
        )

    # Check if check_interval is negative.
    if float(config["User"]["check_interval"]) <= 0:
        config["User"]["check_interval"] = "0.5"
        default_needed = True

        # Log warning.
        log(
            1,
            "Check interval set to default value '0.5', because of "
            f"negative value in config file at {CONFIG_FILE}.",
        )

    # If default values were needed, write config file on disk.
    if default_needed:
        config_write(config)

    return config


def config_write(config):
    """
    The config_write function writes the config file to disk.

    :param config: Write the config file
    :return: None
    """

    with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
        config.write(config_file)


def check_encryption():
    # TODO: docstring
    # macOS: Check if FileVault (fv) is enabled.
    if CURRENT_PLATFORM == "DARWIN":
        fv_command = ["/usr/bin/fdesetup", "isactive"]

        fv_process = subprocess.run(
            fv_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )  # nosec

        # Check exit code of fdesetup for success.
        if fv_process.returncode != 0:
            log(
                1,
                f"Could not determine encryption status of host system! "
                f"Error: {fv_process.stderr.strip()}.",
            )

            return 1

        if fv_process.stdout.strip():
            # FileVault is enabled.
            log(0, "FileVault is enabled (recommended).")
            return 0

        else:
            # FileVault is disabled.
            log(
                1, "FileVault is disabled. Sensitive data SHOULD be encrypted."
            )
            return 0

    # Linux: Check if LUKS is enabled (WiP).
    else:
        raise NotImplementedError


def startup():
    """
    The startup function is responsible for checking the host system,
    it needed permissions and if FileVault is enabled. It also creates a
    config file in case it does not exist yet. It returns and exit code
    of 0 if all checks passed and an exit code of 1 if not.

    :return: config and exit code
    """

    # Start logging.
    log(0, "--------- Startup: ---------")
    log(0, "Starting swiftGuard and running startup checks ...")

    log(0, f"You are running swiftGuard version: {__version__}")

    # First check if host system is supported (macOS so far).
    if not CURRENT_PLATFORM.startswith("DARWIN"):
        # Log error.
        log(
            2,
            f"This program only supports macOS, not {CURRENT_PLATFORM}! "
            f"Exiting ...",
        )

        # Return exit code 1 to main to exit program.
        return None, 1

    else:
        log(0, "Host system is supported (macOS).")

    # Ask for macOS permission. In case of problems the user has to
    # manually add swiftGuard to the list of apps with permissions in
    # System Preferences -> Security & Privacy -> Privacy -> Automation.
    osascript_path = "/usr/bin/osascript"
    permission_automation = subprocess.call(
        [
            osascript_path,
            "-e",
            'tell application "System ' 'Events"',
            "-e",
            'keystroke ""',
            "-e",
            "end tell",
        ]
    )  # nosec

    if permission_automation == 1:
        # Log error.
        log(
            1,
            "Looks like swiftGuard has not its needed "
            "Permission granted! Go to System Preferences -> Security & "
            "Privacy -> Privacy -> Automation and add swiftGuard "
            "manually! "
            "If done and Warning persists test if swiftGuard can shutdown"
            "your system by connecting a new USB device. If so, you can "
            "ignore this warning.",
        )

    else:
        log(0, "Looks like swiftGuard has its needed permission granted.")

    # Check if user has FileVault enabled (highly recommended).
    enc_exit_code = check_encryption()

    if enc_exit_code == 1:
        # Return error exit code 1 to main program.
        return None, 1

    # Copy default config file to CONFIG_FILE location.
    config_exit_code = config_create()

    if config_exit_code == 1:
        # Return error exit code 1 to main program.
        return None, 1

    # Load settings from config file.
    config_parser = configparser.ConfigParser()
    config = config_load(config_parser)

    # TODO: Config encryption by user password.
    # import binascii
    # from crypto_config import cryptoconfigparser
    # from configparser_crypt import ConfigParserCrypt
    # import keyring
    #
    # CONFIG_FILE_ENC = USER_HOME + (
    #     "/Library/Preferences/swiftguard/swiftguard_enc"
    #     ".ini")

    # # Encrypt config file.
    # conf_file = ConfigParserCrypt()
    # conf_file.generate_key()
    # keyring.set_password(
    #         "swiftGuard",
    #         "application-encryption-key",
    #         binascii.b2a_hex(conf_file.aes_key).decode("utf-8").strip()
    #         )
    #
    # conf_file.read(CONFIG_FILE)
    # # Write encrypted config file
    # with open(CONFIG_FILE_ENC, 'wb') as file_handle:
    #     conf_file.write_encrypted(file_handle)
    #
    # conf_file.read_encrypted(CONFIG_FILE_ENC)
    #
    # # Decrypt config file.
    # conf_file = ConfigParserCrypt()
    # conf_file.aes_key = binascii.a2b_hex(
    #         keyring.get_password(
    #                 "swiftGuard",
    #                 "application-encryption-key"
    #                 )
    #         )
    # conf_file.read_encrypted(CONFIG_FILE_ENC)

    # Application version check.
    if config["Application"]["version"] != __version__:
        log(
            0,
            f"You are running an outdated version of swiftGuard"
            f"({__version__}). Updating to latest version...",
        )

        # TODO: Application updating.
        # ...

        # When done, update the version number in the config file.
        config["Application"]["version"] = __version__

        # And write the config file on disk.
        config_write(config)

    else:
        # Log info.
        log(0, "You are running the latest version of swiftGuard.")

    # All startup checks finished without critical errors.
    log(0, "Startup checks done and swiftGuard ready to run!")

    # Return created config and exit code 0 to worker (checks passed).
    return config, 0


def apple_lookup(name, bcd):  # sourcery skip: move-assign
    """
    The apple_lookup function takes two arguments:
        1. The name of the device (e.g., iPhone, iPad, iPod)
        2. The BCD code for the device (e.g., 1234,5678)

    Reference: https://gist.github.com/adamawolf/3048717

    :param name: Determine which dictionary to use
    :param bcd: Look up the device name in a dictionary
    :return: The name of the device
    """

    iphones = {
        "1.01": "iPhone",
        "1.02": "iPhone 3G",
        "2.01": "iPhone 3GS",
        "3.01": "iPhone 4",
        "3.02": "iPhone 4",
        "3.03": "iPhone 4",
        "4.01": "iPhone 4S",
        "5.01": "iPhone 5",
        "5.02": "iPhone 5",
        "5.03": "iPhone 5C",
        "5.04": "iPhone 5C",
        "6.01": "iPhone 5S",
        "6.02": "iPhone 5S",
        "7.01": "iPhone 6 Plus",
        "7.02": "iPhone 6",
        "8.01": "iPhone 6s",
        "8.02": "iPhone 6s Plus",
        "8.04": "iPhone SE",
        "9.01": "iPhone 7",
        "9.02": "iPhone 7 Plus",
        "9.03": "iPhone 7",
        "9.04": "iPhone 7 Plus",
        "10.01": "iPhone 8",
        "10.02": "iPhone 8 Plus",
        "10.03": "iPhone X",
        "10.04": "iPhone 8",
        "10.05": "iPhone 8 Plus",
        "10.06": "iPhone X",
        "11.02": "iPhone XS",
        "11.04": "iPhone XS Max",
        "11.06": "iPhone XS Max",
        "11.08": "iPhone XR",
        "12.01": "iPhone 11",
        "12.03": "iPhone 11 Pro",
        "12.05": "iPhone 11 Pro Max",
        "12.08": "iPhone SE (2. Gen)",
        "13.01": "iPhone 12 Mini",
        "13.02": "iPhone 12",
        "13.03": "iPhone 12 Pro",
        "13.04": "iPhone 12 Pro Max",
        "14.02": "iPhone 13 Pro",
        "14.03": "iPhone 13 Pro Max",
        "14.04": "iPhone 13 Mini",
        "14.05": "iPhone 13",
        "14.06": "iPhone SE (3. Gen)",
        "14.07": "iPhone 14",
        "14.08": "iPhone 14 Plus",
        "15.02": "iPhone 14 Pro",
        "15.03": "iPhone 14 Pro Max",
        "15.04": "iPhone 15",
        "15.05": "iPhone 15 Plus",
        "16.01": "iPhone 15 Pro",
        "16.02": "iPhone 15 Pro Max",
    }

    ipods = {
        "1.01": "iPod (1. Gen)",
        "2.01": "iPod (2. Gen)",
        "3.01": "iPod (3. Gen)",
        "4.01": "iPod (4. Gen)",
        "5.01": "iPod (5. Gen)",
        "7.01": "iPod (6. Gen)",
        "9.01": "iPod (7. Gen)",
    }

    ipads = {
        "1.01": "iPad",
        "1.02": "iPad 3G",
        "2.01": "iPad (2. Gen)",
        "2.02": "iPad (2. Gen, Cellular)",
        "2.03": "iPad (2. Gen, Cellular)",
        "2.04": "iPad (2. Gen)",
        "3.01": "iPad (3. Gen)",
        "3.02": "iPad (3. Gen, Cellular)",
        "3.03": "iPad (3. Gen, Cellular)",
        "2.05": "iPad mini",
        "2.06": "iPad mini (Cellular)",
        "2.07": "iPad mini (Cellular)",
        "3.04": "iPad (4. Gen)",
        "3.05": "iPad (4. Gen, Cellular)",
        "3.06": "iPad (4. Gen, Cellular)",
        "4.01": "iPad Air",
        "4.02": "iPad Air (Cellular)",
        "4.03": "iPad Air",
        "4.04": "iPad mini Retina",
        "4.05": "iPad mini Retina (Cellular)",
        "4.06": "iPad mini Retina",
        "4.07": "iPad mini 3",
        "4.08": "iPad mini 3 (Cellular)",
        "4.09": "iPad Mini 3",
        "5.01": "iPad mini 4",
        "5.02": "iPad mini 4 (Cellular)",
        "5.03": "iPad Air 2",
        "5.04": "iPad Air 2 (Cellular)",
        "6.03": "iPad Pro 9.7",
        "6.04": "iPad Pro 9.7 (Cellular)",
        "6.07": "iPad Pro 12.9",
        "6.08": "iPad Pro 12.9 (Cellular)",
        "6.11": "iPad (2017)",
        "6.12": "iPad (2017)",
        "7.01": "iPad Pro (2. Gen)",
        "7.02": "iPad Pro (2. Gen, Cellular)",
        "7.03": "iPad Pro 10.5 (2. Gen)",
        "7.04": "iPad Pro 10.5 (2. Gen)",
        "7.05": "iPad (6. Gen)",
        "7.06": "iPad (6. Gen, Cellular)",
        "7.11": "iPad 10.2 (7. Gen)",
        "7.12": "iPad 10.2 (7. Gen, Cellular)",
        "8.01": "iPad Pro 11 (3. Gen)",
        "8.02": "iPad Pro 11 (3. Gen, 1TB)",
        "8.03": "iPad Pro 11 (3. Gen, Cellular)",
        "8.04": "iPad Pro 11 (3. Gen, 1TB, Cellular)",
        "8.05": "iPad Pro 12.9 (3. Gen)",
        "8.06": "iPad Pro 12.9 (3. Gen, 1TB)",
        "8.07": "iPad Pro 12.9 (3. Gen, Cellular)",
        "8.08": "iPad Pro 12.9 (3. Gen, 1TB, Cellular)",
        "8.09": "iPad Pro 11 (4. Gen)",
        "8.10": "iPad Pro 11 (4. Gen, Cellular)",
        "8.11": "iPad Pro 12.9 (4. Gen)",
        "8.12": "iPad Pro 12.9 (4. Gen, Cellular)",
        "11.01": "iPad mini (5. Gen)",
        "11.02": "iPad mini (5. Gen)",
        "11.03": "iPad Air (3. Gen)",
        "11.04": "iPad Air (3. Gen)",
        "11.06": "iPad (8. Gen)",
        "11.07": "iPad (8. Gen, Cellular)",
        "12.01": "iPad (9. Gen)",
        "12.02": "iPad (9. Gen, Cellular)",
        "14.01": "iPad mini (6. Gen)",
        "14.02": "iPad mini (6. Gen, Cellular)",
        "13.01": "iPad Air (4. Gen)",
        "13.02": "iPad Air (4. Gen, Cellular)",
        "13.04": "iPad Pro 11 (5. Gen)",
        "13.05": "iPad Pro 11 (5. Gen)",
        "13.06": "iPad Pro 11 (5. Gen)",
        "13.07": "iPad Pro 11 (5. Gen)",
        "13.08": "iPad Pro 12.9 (5. Gen)",
        "13.09": "iPad Pro 12.9 (5. Gen)",
        "13.10": "iPad Pro 12.9 (5. Gen)",
        "13.11": "iPad Pro 12.9 (5. Gen)",
        "13.16": "iPad Air (5. Gen)",
        "13.17": "iPad Air (5. Gen, Cellular)",
        "13.18": "iPad (10. Gen)",
        "13.19": "iPad (10. Gen)",
        "14.03": "iPad Pro 11 (4. Gen)",
        "14.04": "iPad Pro 11 (4. Gen)",
        "14.05": "iPad Pro 12.9 (6. Gen)",
        "14.06": "iPad Pro 12.9 (6. Gen)",
    }

    watches = {
        "1.01": "Apple Watch 38",
        "1.02": "Apple Watch 42",
        "2.06": "Apple Watch Series 1 38",
        "2.07": "Apple Watch Series 1 42",
        "2.03": "Apple Watch Series 2 38",
        "2.04": "Apple Watch Series 2 42",
        "3.01": "Apple Watch Series 3 38 (Cellular)",
        "3.02": "Apple Watch Series 3 42 (Cellular)",
        "3.03": "Apple Watch Series 3 38",
        "3.04": "Apple Watch Series 3 42",
        "4.01": "Apple Watch Series 4 40",
        "4.02": "Apple Watch Series 4 44",
        "4.03": "Apple Watch Series 4 40 (Cellular)",
        "4.04": "Apple Watch Series 4 44 (Cellular)",
        "5.01": "Apple Watch Series 5 40",
        "5.02": "Apple Watch Series 5 44",
        "5.03": "Apple Watch Series 5 40 (Cellular)",
        "5.04": "Apple Watch Series 5 44 (Cellular)",
        "5.09": "Apple Watch SE 40",
        "5.10": "Apple Watch SE 44",
        "5.11": "Apple Watch SE 40 (Cellular)",
        "5.12": "Apple Watch SE 44 (Cellular)",
        "6.01": "Apple Watch Series 6 40",
        "6.02": "Apple Watch Series 6 44",
        "6.03": "Apple Watch Series 6 40 (Cellular)",
        "6.04": "Apple Watch Series 6 44 (Cellular)",
        "6.06": "Apple Watch Series 7 41",
        "6.07": "Apple Watch Series 7 45",
        "6.08": "Apple Watch Series 7 41 (Cellular)",
        "6.09": "Apple Watch Series 7 45 (Cellular)",
        "6.10": "Apple Watch SE 40",
        "6.11": "Apple Watch SE 44",
        "6.12": "Apple Watch SE 40 (Cellular)",
        "6.13": "Apple Watch SE 44 (Cellular)",
        "6.14": "Apple Watch Series 8 41",
        "6.15": "Apple Watch Series 8 45",
        "6.16": "Apple Watch Series 8 41 (Cellular)",
        "6.17": "Apple Watch Series 8 45 (Cellular)",
        "6.18": "Apple Watch Ultra",
        "7.01": "Apple Watch Series 9 41",
        "7.02": "Apple Watch Series 9 45",
        "7.03": "Apple Watch Series 9 41 (Cellular)",
        "7.04": "Apple Watch Series 9 45 (Cellular)",
        "7.05": "Apple Watch Ultra 2",
    }

    if name == "iPhone":
        name = iphones[bcd]

    elif name == "iPad":
        name = ipads[bcd]

    elif name == "iPod":
        name = ipods[bcd]

    elif name == "Watch":
        name = watches[bcd]

    return name


def usb_devices():
    """
    The usb_devices function returns a list of tuples containing the
    following information:
        - vendor_id (e.g. 0x05ac)
        - product_id (e.g. 0x12a8)
        - serial number (if available, otherwise &quot;None&quot;)
        - device name

    :return: A list of tuples
    """

    # Fully qualified path to system_profiler (to prevent executing a
    # bogus binary if PATH is modified).
    system_profiler_path = "/usr/sbin/system_profiler"

    # Run system_profiler and capture its output.
    result = subprocess.run(
        [
            system_profiler_path,
            "SPUSBDataType",
            "-xml",
            "-detailLevel",
            "mini",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )  # nosec

    if result.returncode != 0:
        # Handle the error case.
        res_stderr = result.stderr.decode("utf-8").strip()
        log(1, f"Error while running system_profiler: " f"{res_stderr}.")
        return []

    # Load the XML output using plistlib.
    df = plistlib.loads(result.stdout)

    def _check_inside(result, devices):
        """
        This is a recursive function that checks if the devices are
        built-in. It also checks if there are items inside
        (e.g., USB hubs). If so, it will recursively check what's inside
        those items as well.

        :param result: Pass the result of a previous call to
        :param devices: Store the devices that have been found
        :return: A list of devices
        """

        # Do not take devices with "Built-in_Device=Yes".
        try:
            result["Built-in_Device"]
        except KeyError:
            # Check if vendor_id/product_id is available for this one.
            try:
                # Ensure vendor_id and product_id are present
                assert "vendor_id" in result and "product_id" in result

                # Vendor ID.
                try:
                    vendor_id = DEVICE_RE[1].findall(result["vendor_id"])[0]
                except IndexError:
                    # Assume this is not a standard vendor_id (probably
                    # apple_vendor_id instead of 0x....).
                    vendor_id = result["vendor_id"]

                # Product ID.
                try:
                    product_id = DEVICE_RE[1].findall(result["product_id"])[0]
                except IndexError:
                    # Assume this is not a standard product_id (0x....).
                    product_id = result["product_id"]

                # Serial number.
                try:
                    serial_num = result["serial_num"]
                except Exception:
                    # No serial number found for this device.
                    serial_num = "None"

                # Device name.
                try:
                    name = result["_name"]
                except Exception:
                    # No name found for this device.
                    name = "Unknown"

                # If it is an Apple device, lookup the exact name, using
                # bcd_device (e.g. bcd: 13.04 -> iPhone 12 Pro Max)
                if vendor_id == "apple_vendor_id" and name in [
                    "iPhone",
                    "iPod",
                    "iPad",
                    "Watch",
                ]:
                    name = apple_lookup(name, result["bcd_device"])

                # Append to the list of devices (each device a tuple).
                devices.append((vendor_id, product_id, serial_num, name))

            except AssertionError:
                pass

        # Check if there are items inside.
        try:
            for result_deep in result["_items"]:
                # Check what's inside the _items array
                _check_inside(result_deep, devices)

        except KeyError:
            pass

    # Run the loop and return the list of devices.
    devices = []
    for result in df[0]["_items"]:
        _check_inside(result, devices)

    return devices


def bt_devices():
    """
    The function is used to detect connected bluetooth devices.
    It will return a list of dictionaries, each dictionary containing
    the following keys:
        - name (string) : The name of the device.
        - mac_address (string) : The MAC address of the device.

    NOTE: This function is still WiP and not used yet, but will be in
        the near future.
    NOTE 2: 'system_profiler SPBluetoothDataType -xml -detailLevel mini'
        will be used to identify connected bluetooth devices (mini ->
        basic -> full). Can also be used to list near (but not
        connected) bluetooth devices.

    :return: A list of bluetooth devices
    """

    raise NotImplementedError
