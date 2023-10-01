#!/usr/bin/env python3

"""
autostart.py: TODO: Headline...

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
import logging
import os
import platform
import shutil

# Constants.
CURRENT_PLATFORM = platform.uname()[0].upper()
USER_HOME = os.path.expanduser("~")
APP_PATH = os.path.dirname(os.path.realpath(__file__))[:-6]
CONFIG_FILE = f"{USER_HOME}/Library/Preferences/swiftguard/swiftguard.ini"
LOG_FILE = f"{USER_HOME}/Library/Logs/swiftguard/swiftguard.log"

# Child logger.
LOGGER = logging.getLogger(__name__)


def add_autostart():
    # TODO: docstring.
    # macOS: Create launch agent.
    if CURRENT_PLATFORM.startswith("DARWIN"):
        launch_agent_dest = (
            f"{USER_HOME}/Library/LaunchAgents/dev.lennolium.swiftguard.plist"
        )
        try:
            # Create LaunchAgents directory if it does not exist.
            if not os.path.isdir(os.path.dirname(launch_agent_dest)):
                os.mkdir(os.path.dirname(launch_agent_dest))

                LOGGER.info(
                    f"Created directory "
                    f"{os.path.dirname(launch_agent_dest)}."
                )

            # Copy the plist to the LaunchAgents directory.
            shutil.copy(
                os.path.join(
                    APP_PATH, "install", "dev.lennolium.swiftguard.plist"
                ),
                launch_agent_dest,
            )

        except Exception as e:
            LOGGER.error(
                f"Autostart could not be configured. Could not copy "
                f"launch agent plist to {launch_agent_dest}. \n"
                f"Error: {e}"
            )

    # Linux: Create systemd service (WiP).
    else:
        raise NotImplementedError("Linux is not supported yet.")
        # # Debian based, e.g. Ubuntu: Create systemd service.
        # # See https://linuxhandbook.com/create-systemd-services/
        # user_systemd_dest =
        # f"{USER_HOME}/.config/systemd/user/"
        # systemd_service_dest =
        # "/etc/systemd/system/swiftguard.service"
        # systemd_service_dest_alt = "
        # /usr/systemd/system/swiftguard.service"
        #
        # # Non-Debian based, e.g. Arch Linux: Create systemd service.
        # systemd_service_dest_alt2 =
        # "/usr/lib/systemd/system/swiftguard.service"
        #
        # # Copy the service to the systemd directory.
        # shutil.copy(
        #     os.path.join(APP_PATH, "install", "swiftguard.service"),
        #     systemd_service_dest,
        # )
        #
        # # User: Reload the systemd daemon, enable and start the
        # # service.
        # os.system("systemctl --user daemon-reload")
        # os.system("systemctl --user enable swiftguard.service")
        # os.system("systemctl --user start swiftguard.service")
        #
        # # System.
        # os.system("systemctl daemon-reload")
        # os.system("systemctl enable swiftguard.service")
        # os.system("systemctl start swiftguard.service")
