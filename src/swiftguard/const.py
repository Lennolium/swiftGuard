#!/usr/bin/env python3

"""
const.py: TODO: Headline...

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
import os
import platform
import re
import sys

# Constants.
CURRENT_PLATFORM = platform.uname()[0].upper()
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
