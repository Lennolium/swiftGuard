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
import sys

# Constants.
CURRENT_PLATFORM = platform.uname()[0].upper()  # 'DARWIN' / 'LINUX' ...
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
]

# Resource paths.
LIGHT = {
    "checkmark": ":/resources/light/checkmark.svg",
    "usb-connection": ":/resources/light/usb-connection.svg",
    "shield-check": ":/resources/light/shield-check.svg",
    "shield-slash": ":/resources/light/shield-slash.svg",
    "shield-tamper": ":/resources/light/shield-tamper.svg",
    "app-icon": ":/resources/light/statusbar-macos@2x.png",
    "app-logo": ":/resources/logo-macos@2x.png",
}

DARK = {
    "checkmark": ":/resources/dark/checkmark.svg",
    "usb-connection": ":/resources/dark/usb-connection.svg",
    "shield-check": ":/resources/dark/shield-check.svg",
    "shield-slash": ":/resources/dark/shield-slash.svg",
    "shield-tamper": ":/resources/dark/shield-tamper.svg",
    "app-icon": ":/resources/dark/statusbar-macos@2x.png",
    "app-logo": ":/resources/logo-macos@2x.png",
}
