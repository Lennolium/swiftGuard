#!/usr/bin/env python3

"""
utils/update.py:

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2025.1"
__date__ = "2024-12-16"
__status__ = "Prototype/Development/Production"

# Imports.
import logging
import re
import webbrowser

import requests
from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox

from swiftguard import constants
from swiftguard.constants import C
from swiftguard.init import exceptions as exc, models
from swiftguard.utils import process

# Child logger.
LOGGER = logging.getLogger(__name__)


class UpdateManager(metaclass=models.Singleton):
    """
    Update manager for the application.
    """

    def __init__(self) -> None:
        """
        Checks for updates and displays a dialog if a new version is
        available. If automatic update checks are enabled, the manager
        checks for updates once a week. To enable/disable the background
        check, use enable_background_check() and disable...() methods.
        For manual checks, call the check() method. To validate if the
        privileged helper tool is up-to-date, call check_helper().

        :return: None
        """

        self.current_version = constants.__version__
        self.newest_version = None
        self.last_checked = None
        self._background_check = None

        if C.cfg.CFG["check_updates"]:
            LOGGER.info("Automatic update check is enabled (recommended).")
            self.enable_background_check()

        else:
            LOGGER.warning(
                    "Automatic update check is disabled (NOT recommended)."
                    )

    @staticmethod
    def _query_github() -> dict:
        """
        Get the newest available release from GitHub Releases API.

        :raises exc.GitHubUpdateError: If the GitHub API returns an
            error or is limiting the access.
        :raises exc.ConnectionUpdateError: If no internet connection is
            available.
        :return: The newest release api response.
        :rtype: dict
        """

        try:
            response = requests.get(
                    url=C.app.URLS["release-api"],
                    allow_redirects=True,
                    timeout=5,
                    )

            if response.status_code != 200:
                raise exc.GitHubUpdateError(
                        f"Could not check for updates. GitHub API returned "
                        f"status code '{response.status_code}'."
                        )

            return response.json()

        except requests.exceptions.ConnectionError as e:
            raise exc.ConnectionUpdateError(
                    f"Could not check for updates. Maybe no internet "
                    f"connection? Error: {e.__class__.__name__}: {e}"
                    # f"\n{traceback.format_exc()}"
                    )

        except Exception as e:
            raise exc.GitHubUpdateError(
                    f"Could not check for updates. Probably GitHub is "
                    f"limiting API access. Just to many requests. Error: "
                    f"{e.__class__.__name__}: {e}"
                    # f"\n{traceback.format_exc()}"
                    )

    @staticmethod
    def _get_features(github_res: dict) -> list[str]:
        """
        Get new features of the newest release.

        :param github_res: The raw response from the GitHub API.
        :type github_res: str
        :return: The list of new features.
        :rtype: list[str]
        """

        # Extract the main feature bullet points from the release.
        return re.findall(r"- \*\*(.*?)\*\*:", github_res["body"])

    def _is_newer(self, github_res: dict) -> bool:
        """
        Compare the current version with the newest available version.

        :param github_res: The raw response from the GitHub API.
        :type github_res: str
        :return: True if a newer version is available, False if not.
        :rtype: bool
        """

        release_name = github_res["name"]  # v0.0.2-alpha

        if "-" in release_name:
            release_split = release_name[1:].split("-")  # ['0.0.2', 'alpha']
            release = release_split[0].split(".")  # ['0', '0', '2']
            release_str = release_split[0]  # '0.0.2'

        else:
            release = release_name[1:].split(".")  # ['0', '0', '2']
            release_str = release_name[1:]  # '0.0.2'

        rel_major = int(release[0])  # 0
        rel_minor = int(release[1])  # 0
        rel_patch = int(release[2])  # 2

        current = constants.__version__.split(".")  # ['0', '0', '1']
        cur_major = int(current[0])  # 0
        cur_minor = int(current[1])  # 0
        cur_patch = int(current[2])  # 1

        # Check if major.minor.patch are each higher than the current
        # version. If update is available, return the new version as string.
        # If not, return None. I know it's ugly, but it works.
        if rel_major > cur_major:
            self.newest_version = release_str
            return True

        elif rel_major == cur_major:
            if rel_minor > cur_minor:
                self.newest_version = release_str
                return True

            elif rel_minor == cur_minor:
                if rel_patch > cur_patch:
                    self.newest_version = release_str
                    return True

        self.newest_version = self.current_version
        return False

    def check(self) -> None:
        """
        Check if an update is available for the application. If so, an
        update dialog is displayed.

        :return: None
        """

        LOGGER.info("Checking for updates...")
        self.last_checked = QDateTime.currentDateTime()

        try:
            res = self._query_github()

            if not self._is_newer(github_res=res):
                LOGGER.info(
                        "You are running the latest version of swiftGuard."
                        )
                return

            LOGGER.warning(
                    f"You are running an outdated version of swiftGuard: "
                    f"{__version__} ({__build__}). "
                    f"Newest version: {self.newest_version}."
                    )

            # Display the new features in a dialog.
            new_features = self._get_features(github_res=res)
            self.display_prompt(feature_list=new_features)

        except Exception as e:
            LOGGER.warning(e)

    @staticmethod
    def check_helper() -> None:
        """
        Check if the privileged helper tool is installed and up-to-date.
        """

        from swiftguard.app.app import SwiftGuardApp
        app: SwiftGuardApp | QApplication | None = QApplication.instance()

        if not hasattr(app, "helper_mgr"):
            LOGGER.warning(
                    "Could not get helper version, no HelperManager was found."
                    )
            return

        try:
            helper_version = app.helper_mgr.cmd_version()

            if helper_version != constants.__version__:
                LOGGER.warning(
                        f"Privileged helper is outdated: {helper_version}. "
                        f"Current version: {constants.__version__}."
                        )

                # TODO: Implement update prompt for helper.

                return

            LOGGER.info("Privileged helper is up-to-date.")

        except exc.CommandFailedError as e:
            LOGGER.warning(f"Could not get helper version: {e}")
            return

    def background_check(self) -> None:
        """
        Check for updates automatically once a week.

        :return: None
        """

        # If the user disabled the automatic update check, stop the
        # background check.
        if C.cfg.CFG["check_updates"] is False:
            self.disable_background_check()

        if self.last_checked is None:
            LOGGER.info("Automatic startup update check triggered now.")
            self.check()

        elif self.last_checked.daysTo(QDateTime.currentDateTime()) >= 7:
            LOGGER.info("Automatic weekly update check triggered now.")
            self.check()

    def enable_background_check(self) -> None:
        """
        Enables the automatically update check. We check every hour if
        the last check was more than a week ago. If so, we query over
        internet for updates by simply looking at GitHub Releases API.

        :return: None
        """
        C.cfg.CFG["check_updates"] = True

        self._background_check = QTimer()
        self._background_check.timeout.connect(self.background_check)
        self._background_check.start(60 * 60 * 1000)  # 1 hour.

        # First check after initialization.
        self.first_check()

    def first_check(self) -> None:
        """
        We wait for the QApplication/window to be initialized before we
        start the first update check, as we need the QApplication
        instance to be ready to display the update prompt. If the
        instance is not ready, we wait 5 seconds and try again.

        :return: None
        """

        if hasattr(QApplication.instance(), "window"):
            self.background_check()

        else:
            QTimer.singleShot(5 * 1000, self.first_check)

    def disable_background_check(self) -> None:
        """
        Disable the automatic update check.

        :return: None
        """

        C.cfg.CFG["check_updates"] = False

        if self._background_check:
            self._background_check.stop()
            self._background_check = None

    def display_prompt(self, feature_list: list[str]) -> None:
        """
        The update_box function is used to display a message box
        informing the user that an update is available. The message box
        contains a download button that opens the GitHub release page
        in the default browser and a close button that closes the
        message box. A checkbox is also included to disable future
        update messages.

        :param feature_list: The list of new features.
        :type feature_list: list[str]
        :return: None
        """

        msg_box = QMessageBox()
        msg_box.setWindowTitle("swiftGuard")
        msg_box.setWindowFlags(msg_box.windowFlags() |
                               Qt.WindowType.WindowStaysOnTopHint
                               )

        new_features_formatted = ""
        for i, feature in enumerate(feature_list):
            new_features_formatted += f"- {feature}\n"

            # Show max 4 new features.
            if i == 3:
                new_features_formatted += "- And more ..."
                break

        # Bold text.
        msg_box.setText(
                f"Update Available!\n\n"
                f"Installed: {self.current_version}\nLatest Release: "
                f"{self.newest_version}\n\nNew Features:"
                )

        # Smaller, informative text.
        msg_box.setInformativeText(f"{new_features_formatted}")

        msg_box.setIconPixmap(QPixmap(C.res.RES["icon"]))
        msg_button = msg_box.addButton("Download",
                                       QMessageBox.ButtonRole.YesRole
                                       )
        msg_box.addButton("Close", QMessageBox.ButtonRole.NoRole)

        # Make text selectable and copyable.
        msg_box.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                )

        # Add checkbox to disable update message.
        cb = QCheckBox("Don't show this message again")
        msg_box.setCheckBox(cb)

        # Play a sound to alert the user.
        _ = process.Process(
                binary_path="/usr/bin/afplay",
                args=("-t", "0.9",
                      "-q", "1",
                      "-v", "0.4",
                      "/System/Library/Sounds/Blow.aiff"),
                timeout=1,
                blocking=False,
                ).run()

        msg_box.exec()
        # msg_box.open()

        if msg_box.clickedButton() == msg_button:
            webbrowser.open_new_tab(C.app.URLS["latest"])

        # Disable future update messages.
        if cb.isChecked():
            C.cfg.CFG["check_updates"] = False


if __name__ == "__main__":
    pass
