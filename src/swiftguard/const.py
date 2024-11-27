#!/usr/bin/env python3

"""
const.py: TODO: Headline...

TODO: Description...
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
import os
import platform
import re
import subprocess
import sys

import gnupg
from PySide6.QtCore import Qt

# import gpg_lite as gpg

# Constants.
CURRENT_PLATFORM = platform.uname()[0].upper()  # 'DARWIN' / 'LINUX' ...
CURRENT_ARCH = platform.uname()[4]  # 'x86_64' / 'arm64' ...
CURRENT_MODE = sys.modules["__main__"].__file__[-6:-3]  # 'app' / 'cli'
USER_HOME = os.path.expanduser("~")
CONFIG_FILE = f"{USER_HOME}/Library/Preferences/swiftguard/swiftguard.ini"
LOG_FILE = f"{USER_HOME}/Library/Logs/swiftguard/swiftguard.log"

if getattr(sys, "frozen", False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable '_MEIPASS'.
    # See: https://pyinstaller.org/en/stable/runtime-information.html
    APP_PATH = sys._MEIPASS
else:
    APP_PATH = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

# Precompiled regex for device detection.
DEVICE_RE = [
        re.compile(".+ID\s(?P<id>\w+:\w+)"),  # noqa: W605
        re.compile("0x([0-9a-z]{4})"),
        re.compile("(^[a-zA-Z0-9'_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"),
        re.compile("(^[a-zA-Z0-9'_.+-]+\.[a-zA-Z0-9-.]+$)"),
        re.compile("- \*\*(.*?)\*\*:")
        ]

# Resource paths.
RES = {
        "check": ":/resources/icons/checkmark.svg",
        "usb": ":/resources/icons/cable.connector.svg",
        "guarding": ":/resources/icons/checkmark.shield.fill.svg",
        "inactive": ":/resources/icons/shield.slash.svg",
        "tamper": ":/resources/icons/exclamationmark.shield.fill.svg",
        "tray": ":/resources/icons/tray.png",
        "app": ":/resources/icons/app.png",
        }

LIGHT = {
        "checkmark": ":/resources/light/checkmark.svg",
        "usb-connection": ":/resources/light/usb-connection.svg",
        "shield-check": ":/resources/light/shield-check.svg",
        "shield-slash": ":/resources/light/shield-slash.svg",
        "shield-tamper": ":/resources/light/shield-tamper.svg",
        "app-icon": ":/resources/light/statusbar-macos@2x.png",
        "app-logo": ":/resources/logo-macos.png",
        }

DARK = {
        "checkmark": ":/resources/dark/checkmark.svg",
        "usb-connection": ":/resources/dark/usb-connection.svg",
        "shield-check": ":/resources/dark/shield-check.svg",
        "shield-slash": ":/resources/dark/shield-slash.svg",
        "shield-tamper": ":/resources/dark/shield-tamper.svg",
        "app-icon": ":/resources/dark/statusbar-macos@2x.png",
        "app-logo": ":/resources/logo-macos.png",
        }

URLS = {
        "project": "https://github.com/Lennolium/swiftGuard",
        "release-api": "https://api.github.com/repos/Lennolium/swiftGuard"
                       "/releases/latest",
        "latest": "https://github.com/Lennolium/swiftGuard/releases/latest",
        "sha256sums": f"https://github.com/Lennolium/swiftGuard/releases"
                      f"/download/"
                      f"v{__version__}/SHA256SUMS",
        "sha_test": "https://github.com/Lennolium/swiftGuard/releases/download"
                    "/v0.0.2/SHA256SUM",  # TODO: Remove this!
        "release-key": "https://keys.openpgp.org/vks/v1/by-fingerprint"
                       "/8D599BE9FD05CFFACA7E7039AC4CB992D8D5FF9A",
        "keyserver": "https://keys.openpgp.org/vks/v1/by-fingerprint/",
        }

LOCAL_FILES = [
        "install/dev.lennolium.swiftguard.plist",
        "install/RELEASE_KEY.asc",
        "install/swiftguard.ini",
        "install/swiftguard.service",
        "resources/ACKNOWLEDGMENTS",
        "resources/mail-template.txt",
        "resources/mail-template.html",
        "resources/resources_rc.py",
        "utils/__init__.py",
        "utils/autostart.py",
        "utils/conf.py",
        "utils/enc.py",
        "utils/hash.py",
        "utils/helpers.py",
        "utils/listeners.py",
        "utils/log.py",
        "utils/notif.py",
        "utils/upgrade.py",
        "utils/workers.py",
        "__init__.py",
        "__main__.py",
        "const.py",
        ]

# GPG and Hashes.
# TODO: change to /.gnupg
HASH_FILE = f"{APP_PATH}/install/SHA256SUMS"
GPG_DIR = f"{USER_HOME}/.gnupg"
GPG_RELEASE_FP = "8D599BE9FD05CFFACA7E7039AC4CB992D8D5FF9A"
GPG_INSTALL_KEY = f"{APP_PATH}/install/RELEASE_KEY.asc"
GPG_RELEASE_KEY = f"{USER_HOME}/Library/Integrity/swiftguard/RELEASE_KEY.asc"
os.makedirs(GPG_DIR, exist_ok=True)
GPG_STORE = gnupg.GPG(
        gnupghome=GPG_DIR,
        gpgbinary="/opt/homebrew/bin/gpg" if CURRENT_ARCH == "arm64" else "/usr/local/bin/gpg",
        )
GPG_STORE.encoding = "utf-8"


def get_size(bytes_inp, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes_inp < factor:
            return f"{bytes_inp:.0f}{unit}{suffix}"
        bytes_inp /= factor


# System information (for E-Mail, bug reports and debugging).
if CURRENT_PLATFORM == "DARWIN":
    sys_os = "macOS"
    sys_version = str(platform.mac_ver()[0])
    cpu_name = subprocess.check_output(
            ["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"],
            encoding='utf-8'
            ).strip()
else:
    sys_os = platform.linux_distribution()[0]
    sys_version = str(platform.linux_distribution()[1])
    cpu_name = str(subprocess.check_output("cat /proc/cpuinfo",
                                           shell=True
                                           ).strip()
                   )

SYSTEM_INFO = [
        sys_os,
        sys_version,
        os.getlogin(),
        platform.uname().node,
        cpu_name,
        get_size(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")),
        platform.python_version(),
        ]

# Qt keys to QuickMacHotKeys conversion tables.
KEYS_QT = [Qt.Key_0, Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5,
           Qt.Key_6, Qt.Key_7, Qt.Key_8, Qt.Key_9,
           Qt.Key_A, Qt.Key_B, Qt.Key_C, Qt.Key_D, Qt.Key_E, Qt.Key_F,
           Qt.Key_G, Qt.Key_H, Qt.Key_I, Qt.Key_J, Qt.Key_K, Qt.Key_L,
           Qt.Key_M, Qt.Key_N, Qt.Key_O, Qt.Key_P, Qt.Key_Q, Qt.Key_R,
           Qt.Key_S, Qt.Key_T, Qt.Key_U, Qt.Key_V, Qt.Key_W, Qt.Key_X,
           Qt.Key_Y, Qt.Key_Z,
           ]

KEYS_QM = [29, 18, 19, 20, 21, 23,  # 0-5
           22, 26, 28, 25,  # 6-9
           0, 11, 8, 2, 14, 3,  # A-F
           5, 4, 34, 38, 40, 37,  # G-L
           46, 45, 31, 35, 12, 15,  # M-R
           1, 17, 32, 9, 13, 7,  # S-X
           16, 6,  # Y-Z
           ]

MODS_QT = [Qt.ControlModifier,  # Cmd
           Qt.AltModifier,  # Option
           Qt.ShiftModifier,  # Shift
           Qt.MetaModifier  # Control
           ]

MODS_QM = [256, 2048, 512, 4096]  # Cmd, Option, Shift, Control
