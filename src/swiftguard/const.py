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

# Constants.
CURRENT_PLATFORM = platform.uname()[0].upper()
USER_HOME = os.path.expanduser("~")
APP_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = f"{USER_HOME}/Library/Preferences/swiftguard/swiftguard.ini"
LOG_FILE = f"{USER_HOME}/Library/Logs/swiftguard/swiftguard.log"

# Precompiled regex for device detection.
DEVICE_RE = [
    re.compile(".+ID\s(?P<id>\w+:\w+)"),
    re.compile("0x([0-9a-z]{4})"),
]
