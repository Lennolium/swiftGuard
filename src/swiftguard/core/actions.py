#!/usr/bin/env python3

"""
action.py: TODO: Headline...

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-03-12"
__status__ = "Prototype/Development/Production"

# Imports.
import subprocess
import logging
import traceback
from pathlib import Path

from PySide6.QtCore import QThread

from swiftguard.utils import process

# Child logger.
LOGGER = logging.getLogger(__name__)


def shutdown() -> None:
    """
    This function will shut down the computer using AppleScript.

    :return: None
    """

    LOGGER.warning("Now executing counter-measure >> Shutdown << Bye ...")

    # AppleScript: slow, but only way to shut down without sudo.
    res = subprocess.run(args=("/usr/bin/osascript",
                               "-e",
                               'tell app "System Events" to shut down'),
                         timeout=5,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.PIPE,
                         )  # nosec B603

    # Check exit code of osascript for success.
    if res.returncode != 0:
        LOGGER.error(f"Shutting down failed with following Error: "
                     f"{res.stderr.decode()} \n"
                     f"Fallback to hibernate."
                     )
        # Fallback to hibernate.
        hibernate()

    # Return to prevent multiple execution.
    return


def hibernate() -> None:
    """
    This function will put the computer to sleep by trying two methods.

    :return: None
    """

    LOGGER.warning("Now executing counter-measure >> Hibernation << Bye ...")

    # First method/try (pmset, faster).
    res = subprocess.run(args=("/usr/bin/pmset",
                               "sleepnow"),
                         timeout=3,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         )  # nosec B603

    # Second method/try (AppleScript, slower).
    if res.returncode != 0:
        LOGGER.warning(
                f"First method to hibernate failed with following Error: "
                f"{res.stderr.decode()}, {res.stdout.decode()}"
                f"\nTrying second method now ..."
                )

        res2 = subprocess.run(args=("/usr/bin/osascript",
                                    "-e",
                                    'tell app "System Events" to sleep'),
                              timeout=5,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.PIPE,
                              )  # nosec B603

        if res2.returncode != 0:
            LOGGER.error(
                    f"Second method also failed with following Error: "
                    f"{res2.stderr.decode()} \n"
                    f"We need to give up ..."
                    )

    # Return to prevent multiple execution.
    return


def shred(file: str | Path, folder: str | Path = None) -> None:
    """
    This function will shred a file using the `shred` command.

    :param file: The file to shred.
    :type file: str | Path
    :param folder: Shred the content of a directory.
    :type folder: str | Path
    :return: None
    """

    if folder:
        LOGGER.warning(f"Now shredding content of directory '{folder}' ...")
        res = subprocess.run(args=("/usr/bin/shred",
                                   "--force",
                                   "--remove",
                                   "-v",
                                   "-n",
                                   "3",
                                   "-z",
                                   "-u",
                                   folder),
                             timeout=5,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.PIPE,
                             )

        if res.returncode != 0:
            LOGGER.error(f"Shredding failed with following Error: "
                         f"{res.stderr.decode()}"
                         )

    else:
        LOGGER.warning(f"Now shredding file '{file}' ...")

        res = subprocess.run(args=("/usr/bin/shred",
                                   "--force",
                                   "--remove",
                                   file),
                             timeout=5,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.PIPE,
                             )  # nosec B603

        if res.returncode != 0:
            LOGGER.error(f"Shredding failed with following Error: "
                         f"{res.stderr.decode()}"
                         )

    # Return to prevent multiple execution.
    return


def alert(sec: int = 1) -> None:
    """
    This function will play an alert sound for a given duration. It will
    repeat the sound and increase its frequency over time.

    :param sec: The total duration of how many seconds the sound should
        be repeated (default: 5).
    :type sec: int
    :return: None
    """

    # Calculate the sleep durations for the alert sound.
    # We start with half of the total duration and then decrease it
    # by half each time. The last 5 repetitions will be 0 seconds.
    if sec >= 9:
        sleep_durs = [sec // 2]
        for i in range(sec):

            if sum(sleep_durs) >= sec - 5:
                sleep_durs.extend([0, 0, 0, 0, 0])
                break

            if 0 in sleep_durs:
                sleep_durs.extend([0, 0, 0, 0])
                break

            val = sleep_durs[-1] // 2
            if len(sleep_durs) >= 4:
                val = 0
            sleep_durs.append(val)

    elif sec <= 5:
        sleep_durs = []
        for i in range(sec):
            sleep_durs.append(0)

    else:
        sleep_durs = [sec - 5, 0, 0, 0, 0, 0]

    # Ensure the volume is high enough to hear the alarm.
    res0 = process.Process(
            binary_path="/usr/bin/osascript",
            args=("-e",
                  "set volume output volume 50"),
            timeout=1,
            blocking=True,
            ).run()

    # Timeout expired.
    if res0.return_code == 2:
        pass

    elif res0.return_code != 0:
        LOGGER.error(f"During increasing the systems audio volume "
                     f"occurred an error: "
                     f"Code={res0.return_code}, "
                     f"Stdout={res0.stdout}, "
                     f"Stderr={res0.stderr}."
                     )

    for sleep_time in sleep_durs:

        # Play the alarm sound.
        res1 = process.Process(
                binary_path="/usr/bin/afplay",
                args=("-t", "1.0",
                      "-q", "1",
                      "/System/Library/Sounds/Submarine.aiff",),
                timeout=1,
                blocking=True,
                ).run()

        # Timeout expired.
        if res1.return_code == 2:
            pass

        elif res1.return_code != 0:
            LOGGER.error(f"During playing the alarm sound occurred an error: "
                         f"Code={res1.return_code}, "
                         f"Stdout={res1.stdout}, "
                         f"Stderr={res1.stderr}."
                         )
            return

        # Sleep for the calculated amount of time.
        QThread.sleep(sleep_time)

    return
