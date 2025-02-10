#!/usr/bin/env python3

"""
checks.py: TODO: Headline...

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__build__ = "2024.3"
__date__ = "2024-02-20"
__status__ = "Prototype/Development/Production"

# Imports.
import os
import platform
import logging
import sys
import stat
from pathlib import Path

from swiftguard.init import exceptions as exc
from swiftguard.utils import process

# Child logger.
LOGGER = logging.getLogger(__name__)


def check_file(file_path: str | Path, permissions: int = stat.S_ISUID) -> bool:
    # Get the current permissions
    current_mode = os.stat(file_path).st_mode

    # Check if the current permissions match the required permissions
    return True if current_mode & permissions else False


def already_running() -> None:
    """
    Check if another instance of swiftGuard is already running.
    We do not want two instances conflicting with each other.
    Automatically exits the function-calling app.

    :return: None.
    """

    res = None
    try:
        current_pid = os.getpid()
        current_process_name = os.path.basename(sys.argv[0])

        res = process.Process(
                binary_path="/usr/bin/pgrep",
                args=("-f",
                      current_process_name),
                timeout=2,
                blocking=True,
                ).run()

        for pid in res.stdout.split():
            if int(pid) != current_pid:
                LOGGER.error("Another instance of swiftGuard is already "
                             "running! Exiting..."
                             )
                sys.exit(1)

    except Exception as e:

        if res:
            res_info = (f"\nCode={res.return_code}, "
                        f"Stdout={res.stdout}, "
                        f"Stderr={res.stderr}")
        else:
            res_info = ""

        LOGGER.error(f"Could not check if another instance of "
                     f"swiftGuard is already running. Ignoring it. "
                     f"{e.__class__.__name__}: {e}"
                     f"{res_info}"
                     )


def filevault() -> bool:
    """
    Check if FileVault is enabled.

    :return: True if FileVault is enabled, False otherwise.
    :rtype: bool
    """

    res = process.Process(
            binary_path="/usr/bin/fdesetup",
            args=("isactive",),
            timeout=3,
            blocking=True,
            ).run()

    if res.return_code != 0:
        LOGGER.error(f"Could not check if FileVault is enabled."
                     f"Code={res.stderr}, "
                     f"Stdout={res.stdout}, "
                     f"Stderr={res.stderr}."
                     )
        return False

    if res.stdout.strip() == "true":
        return True
    else:
        LOGGER.warning("FileVault is not enabled. This is a security risk.")
        return False


def operating_system() -> None:
    """
    Check if the operating system is macOS or Linux.

    :raises exc.OperatingSystemNotSupported: If the operating system is
        not supported.
    :return: None
    """

    # Check if the operating system is macOS or Linux.
    if not platform.uname()[0].upper().startswith(("DARWIN", "LINUX")):
        raise exc.OperatingSystemNotSupported(
                f"The operating system '{platform.uname()[0]}' is not "
                f"supported. Only macOS and Linux are supported."
                )


def automation() -> bool:
    """
    Ask for macOS permission. In case of problems the user has to
    manually add swiftGuard to the list of apps with permissions in
    System Preferences -> Security & Privacy -> Privacy -> Automation.

    :return: True if the permission is granted, False otherwise.
    :rtype: bool
    """

    res = process.Process(
            binary_path="/usr/bin/osascript",
            args=("-e",
                  "tell application \"System Events\"",
                  "-e",
                  'keystroke ""',
                  "-e",
                  "end tell",
                  ),
            timeout=5,
            blocking=True,
            ).run()

    if res.return_code == 0:
        return True

    LOGGER.warning(
            "Looks like swiftGuard has not its needed "
            "Permission granted! Go to System Preferences -> Security & "
            "Privacy -> Privacy -> Automation and add swiftGuard "
            "manually! If done and Warning persists test if swiftGuard "
            "can shutdown your system by connecting a new USB device. "
            f"If so, you can ignore this warning."
            )
    return False
