#!/usr/bin/env python3

"""
constants.py: Constants and settings for the application.

This module contains all constants and settings for the application,
like paths, system information, configuration defaults, logging,
security and email settings, resources and device dictionaries.
Only one instance is enforced (singleton) and the constants are
read-only. New attributes can only be added, not overwritten.


**USAGE:**

*Import the constants from anywhere in the application.*

- from swiftguard.constants import C

*Access the constants.*

- path = C.app.PATH
- print(C.cfg.CFG["log_level"])

*Create a new attribute (has to be all uppercase and not start with an
underscore).*

- C.app.NEW_ = "new_value"

"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2025.1"
__date__ = "2025-01-08"
__status__ = "Prototype/Development/Production"

# Imports.
import os
import subprocess
import sys
import platform
import re
from pathlib import Path

import platformdirs
import distro

from swiftguard.init import cfg, models
from swiftguard.init import exceptions as exc
from swiftguard.init import log
from swiftguard.utils import process


class ReadOnly:
    """
    Add a custom __setattr__ method to only allow adding new attributes,
    while also prohibiting overwriting existing ones.
    Overwrites the __repr__ method to show also the new attributes.
    """

    def __setattr__(
            self: any,
            key: str,
            value: any,
            ) -> None:
        """
        Custom __setattr__ method to only allow adding new attributes,
        while also prohibiting overwriting existing ones.

        :param self: The instance of the class.
        :type self: any
        :param key: The attribute to set.
        :type key: str
        :param value: The value to set.
        :type value: any
        :return: None
        """

        if key in type(self).__dict__.keys():
            raise exc.ConstantsReadOnlyError(
                    f"Constants attributes are read-only. "
                    f"Tried to set '{key}' to '{value}'."
                    )

        elif key.startswith("_"):
            raise exc.ConstantsPrivateError(
                    f"New constants attributes must not start "
                    f"with underscores (protected/private). "
                    f"Tried to set '{key}'."
                    )

        elif not key.isupper():
            raise exc.ConstantsLowerCaseError(
                    f"New constants attributes must be all "
                    f"uppercase. Tried to set '{key}'."
                    )

        self.__dict__[key] = value

    def __repr__(self: any) -> str:
        """
        Custom __repr__ method to show the class name and all attributes,
        except the private ones (starting with one or two underscores).

        :param self: The instance of the class.
        :type self: any
        :return:  The class name and all attributes.
        :rtype: str
        """

        res = [f"{const}={value!r}" for const, value in
               {**type(self).__dict__, **self.__dict__}.items() if
               not const.startswith("_")]
        return f"{self.__class__.__qualname__}({', '.join(res)})"


def get_size(bytes_inp: int, suffix: str = "B") -> str:
    """
    Scale bytes to their proper format,
    e.g:
        1253656 => '1 MB'
        1253656678 => '1.17 GB' (change below to :.2f)

    :param bytes_inp: The bytes to scale.
    :type bytes_inp: int
    :param suffix: The suffix for the size.
    :type suffix: str
    :return: The scaled bytes with suffix (e.g. 1.20MB).
    :rtype: str
    """

    for unit in ("", "K", "M", "G", "T", "P"):
        if bytes_inp < 1024:
            return f"{bytes_inp:.0f} {unit}{suffix}"
        bytes_inp /= 1024


def get_cpu(platform: str) -> str:
    """
    Get the CPU information on Linux or macOS.

    :param platform: The platform to get the CPU information from
        ('macOS' or 'Linux').
    :type platform: str
    :return: The CPU model.
    :rtype: str
    """

    if platform == "macOS":

        res = process.Process(
                binary_path="/usr/sbin/sysctl",
                args=("-n",
                      "machdep.cpu.brand_string"),
                timeout=5,
                blocking=True,
                ).run()

        return res.stdout.strip()

    else:

        lscpu = subprocess.Popen(args="lscpu",
                                 stdout=subprocess.PIPE,
                                 )
        grep = subprocess.Popen(args=("grep", "Model name"),
                                stdin=lscpu.stdout,
                                stdout=subprocess.PIPE,
                                )
        cut = subprocess.Popen(args=("cut", "-f", "2", "-d", ":"),
                               stdin=grep.stdout,
                               stdout=subprocess.PIPE,
                               )
        awk = subprocess.Popen(args=("awk", "{$1=$1}1"),
                               stdin=cut.stdout,
                               stdout=subprocess.PIPE,
                               )

        lscpu.stdout.close()
        grep.stdout.close()
        cut.stdout.close()

        return awk.communicate()[0].decode().strip()


class AppConstants(ReadOnly):
    """
    Constants for the application and system information.
    """

    # General system and user paths.
    PATH: Path = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else (
            Path(os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
                 ).resolve())
    USER_HOME: Path = Path(os.path.expanduser("~")).resolve()

    # Platform and OS information.
    PLATFORM: str = ("macOS" if platform.uname()[0].upper() == "DARWIN" else
                     "Linux")
    USER: str = os.getlogin()
    ARCH: str = "arm64" if platform.machine() == "arm64" else "x86_64"
    HOSTNAME: str = platform.uname().node
    PYTHON: str = platform.python_version()
    RAM: str = get_size(os.sysconf("SC_PAGE_SIZE") *
                        os.sysconf("SC_PHYS_PAGES")
                        )
    OS: str = PLATFORM if PLATFORM == "macOS" else distro.name()
    OS_VERSION: str = (platform.mac_ver()[0] if PLATFORM == "macOS" else
                       distro.version(pretty=True))
    CPU: str = get_cpu(platform=PLATFORM)

    # Launch agents for autostart.
    LAUNCH_AGENT_SOURCE: Path = PATH / "assets" / "agnt"
    LAUNCH_AGENT_MACOS: Path = (USER_HOME / "Library" / "LaunchAgents" /
                                "dev.lennolium.swiftguard.plist")

    UNINSTALL_SCRIPT: Path = PATH / "supp" / "uninstall-app.sh"

    # Project specific information.
    URLS: dict = {
            "github": "https://github.com/Lennolium/swiftGuard",
            "issues": "https://github.com/Lennolium/swiftGuard/issues/new"
                      "/choose",
            "website": "https://swiftguard.lennolium.dev",
            "release-api": "https://api.github.com/repos/Lennolium/swiftGuard"
                           "/releases/latest",
            "latest": "https://github.com/Lennolium/swiftGuard/releases"
                      "/latest",
            "uninstall": "https://github.com/Lennolium/swiftGuard?tab=readme"
                         "-ov-file#uninstall",  # Sync with __main__.py!
            }


class LoggingConstants(ReadOnly):
    """
    Constants for the logging system and the logger instance.
    """

    FILE: Path = platformdirs.user_log_path(
            appname="dev.lennolium.swiftguard",
            appauthor=False,
            ensure_exists=True,
            ) / "swiftguard.log"
    LEVEL: str = os.environ.get("SG_LOG_LEVEL", "INFO")  # Default: INFO.
    MAX_SIZE: int = 2  # 2 MB per file.
    MAX_FILES: int = 5  # 5 files.

    # Create the logger instance.
    LOGGER: log.LoggingManager = log.LoggingManager(
            log_file=FILE,
            platform=AppConstants.PLATFORM,
            default_level=LEVEL,
            max_size=MAX_SIZE,
            max_files=MAX_FILES,
            )


class SecurityConstants(ReadOnly):
    """
    Constants for the security system, the integrity checks and
    the sanitization patterns.
    """

    # Encrypt and hashing (change in init/cfg.py and utils/process.py).
    PEPPER: bytes = b"swiftGuard-2024"

    # Integrity checks.
    INTEGRITY_INTERVAL: int = 10  # Check every 10 seconds.
    INTEGRITY_FILE: Path = AppConstants.PATH / "supp" / "hashes.json"
    INTEGRITY_FILE_HASH: str = (
            "7c4872b4a825d1400a2ef8f0a2e86c9978ec766fc6f83bb9c26b2c0175d238b6"
            "8afd75c05ed512e526331f31d20715e9993b918427b96226710a82d0951937df")
    # TODO: Add all files here!
    INTEGRITY_FILES: tuple[Path] = (
            AppConstants.PATH / "__init__.py",
            )

    # Monitoring.
    MONITOR_RE: re.Pattern = re.compile(r"0x([0-9a-z]{4})")
    MONITOR_RE2: re.Pattern = re.compile(r"0x([0-9A-Z]{4})")

    # Sanitization.
    SANITIZE_EMAIL: re.Pattern = (
            re.compile(r"(^[a-zA-Z0-9'_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"))
    SANITIZE_SMTP: re.Pattern = (
            re.compile(r"(^[a-zA-Z0-9'_.+-]+\.[a-zA-Z0-9-.]+$)"))
    SANITIZE_CLIPBOARD: re.Pattern = (
            re.compile(r"[^\w\s.,!?@|/:\-<>()_\[\]{}\"'\\]"))


class ConfigurationConstants(ReadOnly):
    """
    Constants for configuration system, the configuration manager and
    the default configuration for reset.
    """

    FILE: Path = platformdirs.user_config_path(
            appname="dev.lennolium.swiftguard",
            appauthor=False,
            ensure_exists=True,
            ) / "swiftguard.enc"
    DEFAULT: dict = {
            "General": {
                    "autostart": True,
                    "check_updates": True,
                    },
            "Monitoring": {
                    "action": "hibernate",
                    "delay": 15,
                    "delay_sound": False,
                    "interval": 1,
                    "usb_enabled": True,
                    "bluetooth_enabled": False,
                    "network_enabled": False,
                    "network_strict": False,
                    "hotkey": [2, [256, 512]],
                    "password": None,
                    "touchid": False,
                    },
            "Whitelist": {
                    "usb": [],
                    "bluetooth": [],
                    "network": [],
                    },
            "Shred": {
                    "shred_enabled": False,
                    "shred_paths": [],
                    },
            "E-Mail": {
                    "email_enabled": False,
                    "take_photo": False,
                    "receiver_name": None,
                    "receiver_email": None,
                    "smtp_email": None,
                    "smtp_password": None,
                    "smtp_server": None,
                    "smtp_port": None,
                    },
            "Other": {
                    "version": cfg.__version__,
                    "log_level": LoggingConstants.LEVEL,
                    "release_hash": SecurityConstants.INTEGRITY_FILE_HASH,
                    },
            }
    CFG: cfg.ConfigurationManager = cfg.ConfigurationManager(
            config_file=FILE,
            config_default=DEFAULT,
            )


class EmailSettings(ReadOnly):
    """
    Constants for the email system and the email templates.
    """

    TIMEOUT_INIT: int = 5
    TIMEOUT_SEND: int = 2
    TEMPLATE_TEXT: Path = (
            AppConstants.PATH / "assets" / "tmpls" / "mail-template.txt")
    TEMPLATE_HTML: Path = (
            AppConstants.PATH / "assets" / "tmpls" / "mail-template.html")
    BANNER_LIGHT: Path = (
            AppConstants.PATH / "assets" / "tmpls" / "banner-light.b64")
    BANNER_DARK: Path = (
            AppConstants.PATH / "assets" / "tmpls" / "banner-dark.b64")
    PHOTO_WARMUP: int = 1000  # Milliseconds.
    PHOTO_FILE: Path = platformdirs.user_cache_path(
            appname="dev.lennolium.swiftguard",
            appauthor=False,
            ensure_exists=True,
            ) / "attacker_photo.jpg"


class HelperSettings(ReadOnly):
    """
    Constants and settings regarding the C++ helper binary, which is
    responsible for privileged system actions like shutdown and sleep.
    Settings for secure and encrypted communication over a Unix socket.
    """

    BINARY_PATH: Path = (AppConstants.PATH / "bin" /
                         "dev.lennolium.swiftguardhelper")
    WRAPPER_PATH: Path = (AppConstants.PATH / "bin" /
                          "dev.lennolium.swiftguardhelperw")
    LAUNCH_AGENT_WRAPPER_SOURCE: Path = (
            AppConstants.PATH / "assets" / "agnt" /
            "dev.lennolium.swiftguardhelperw.plist")
    LAUNCH_AGENT_WRAPPER_DEST: Path = (
            AppConstants.USER_HOME / "Library" / "LaunchAgents" /
            "dev.lennolium.swiftguardhelperw.plist")
    SUDO_SCRIPT: Path = AppConstants.PATH / "supp" / "install-helper.sh"
    SUDOERS_PATH: Path = Path("/etc/sudoers.d/dev_lennolium_swiftguardhelper")
    KEY_SERVICE: str = "swiftGuard-helper"
    KEY_USER: str = "swiftguard@lennolium.dev"
    SOCKET_PATH: Path = Path("/var/run/dev.lennolium.swiftguard.sock")
    MAX_NONCES: int = 5000
    AES_IVLEN: int = 12
    TTL: int = 2  # 2 seconds.


class ResourcesConstants(ReadOnly):
    """
    Constants for the resources, like icons, styles and images.
    Also includes the device dictionaries for Apple devices.
    """

    RES: dict = {
            # General resources.
            "tray": ":/icns/swiftGuard-tray.png",
            "icon": ":/icns/swiftGuard-icon.png",

            # Light mode icons and styles.
            "light": {
                    "style": ":/thms/light.qss",
                    "logo-text": ":/icns/light/swiftGuard-text-light.png",
                    "bg": ":/icns/light/bg.png",

                    "hibernate": ":/icns/light/powersleep.svg",
                    "shutdown": ":/icns/light/power.svg",

                    "settings": ":/icns/light/gear.svg",
                    "settings-hover": ":/icns/light/gear-hover.svg",
                    "help": ":/icns/light/questionmark.svg",
                    "help-hover": ":/icns/light/questionmark-hover.svg",
                    "exit": ":/icns/light/xmark.svg",
                    "exit-hover": ":/icns/light/xmark-hover.svg",

                    },

            # Dark mode icons and styles.
            "dark": {
                    "style": ":/thms/dark.qss",
                    "logo-text": ":/icns/dark/swiftGuard-text-dark.png",
                    "bg": ":/icns/dark/bg.png",

                    "settings": ":/icns/dark/gear.svg",
                    "settings-hover": ":/icns/dark/gear-hover.svg",
                    "help": ":/icns/dark/questionmark.svg",
                    "help-hover": ":/icns/dark/questionmark-hover.svg",
                    "exit": ":/icns/dark/xmark.svg",
                    "exit-hover": ":/icns/dark/xmark-hover.svg",

                    }
            }

    IPHONES: dict = {
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
            "17.03": "iPhone 16",
            "17.04": "iPhone 16 Plus",
            "17.01": "iPhone 16 Pro",
            "17.02": "iPhone 16 Pro Max",
            }

    IPODS: dict = {
            "1.01": "iPod (1. Gen)",
            "2.01": "iPod (2. Gen)",
            "3.01": "iPod (3. Gen)",
            "4.01": "iPod (4. Gen)",
            "5.01": "iPod (5. Gen)",
            "7.01": "iPod (6. Gen)",
            "9.01": "iPod (7. Gen)",
            }

    IPADS: dict = {
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
            "13.01": "iPad Air (4. Gen)",
            "13.02": "iPad Air (4. Gen, Cellular)",
            "13.04": "iPad Pro 11 (5. Gen)",
            "13.05": "iPad Pro 11 (5. Gen, Cellular)",
            "13.06": "iPad Pro 11 (5. Gen, Cellular)",
            "13.07": "iPad Pro 11 (5. Gen, Cellular)",
            "13.08": "iPad Pro 12.9 (5. Gen)",
            "13.09": "iPad Pro 12.9 (5. Gen, Cellular)",
            "13.10": "iPad Pro 12.9 (5. Gen, Cellular)",
            "13.11": "iPad Pro 12.9 (5. Gen, Cellular)",
            "13.16": "iPad Air (5. Gen)",
            "13.17": "iPad Air (5. Gen, Cellular)",
            "13.18": "iPad (10. Gen)",
            "13.19": "iPad (10. Gen, Cellular)",
            "14.01": "iPad mini (6. Gen)",
            "14.02": "iPad mini (6. Gen, Cellular)",
            "14.03": "iPad Pro 11 (4. Gen)",
            "14.04": "iPad Pro 11 (4. Gen)",
            "14.05": "iPad Pro 12.9 (6. Gen)",
            "14.06": "iPad Pro 12.9 (6. Gen, Cellular)",
            "14.08": "iPad Air M2 11 (6. Gen)",
            "14.09": "iPad Air M2 11 (6. Gen, Cellular)",
            "14.10": "iPad Air M2 13 (7. Gen)",
            "14.11": "iPad Air M2 13 (7. Gen, Cellular)",
            "16.03": "iPad Pro M4 11 (5. Gen)",
            "16.04": "iPad Pro M4 11 (5. Gen, Cellular)",
            "16.05": "iPad Pro M4 12.9 (7. Gen)",
            "16.06": "iPad Pro M4 12.9 (7. Gen, Cellular)",
            }

    WATCHES: dict = {
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


class Constants(ReadOnly, metaclass=models.Singleton):
    """
        Constants for the application, only one instance is enforced and
        accessible via the C constant (e.g. from constants import C).

        :ivar app: The application constants.
        :type app: AppConstants
        :ivar log: The logging constants.
        :type log: LoggingConstants
        :ivar cfg: The configuration constants.
        :type cfg: ConfigurationConstants
        :ivar sec: The security constants.
        :type sec: SecurityConstants
        :ivar email: The email settings.
        :type email: EmailSettings
        :ivar res: The resources constants.
        :type res: ResourcesConstants
        """

    app: AppConstants = AppConstants()
    log: LoggingConstants = LoggingConstants()
    cfg: ConfigurationConstants = ConfigurationConstants()
    sec: SecurityConstants = SecurityConstants()
    email: EmailSettings = EmailSettings()
    helper: HelperSettings = HelperSettings()
    res: ResourcesConstants = ResourcesConstants()


# For direct import (e.g. from swiftguard.constants import C).
C = Constants()
