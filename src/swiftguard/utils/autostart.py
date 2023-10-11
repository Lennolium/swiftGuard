#!/usr/bin/env python3

"""
autostart.py: TODO: Headline...

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
import logging
import os
import shutil

from swiftguard import const

# Child logger.
LOGGER = logging.getLogger(__name__)


def add_autostart():
    # TODO: docstring.
    # macOS: Create launch agent.
    if const.CURRENT_PLATFORM.startswith("DARWIN"):
        launch_agent_dest = f"{const.USER_HOME}/Library/LaunchAgents/dev.lennolium.swiftguard.plist"
        try:
            # Create LaunchAgents directory if it does not exist.
            if not os.path.isdir(os.path.dirname(launch_agent_dest)):
                os.mkdir(os.path.dirname(launch_agent_dest))

                LOGGER.info(
                    f"Created directory {os.path.dirname(launch_agent_dest)} "
                    " for autostart."
                )

            # Copy the plist to the LaunchAgents directory.
            if not os.path.isfile(launch_agent_dest):
                shutil.copy(
                    os.path.join(
                        const.APP_PATH,
                        "install",
                        "dev.lennolium.swiftguard.plist",
                    ),
                    launch_agent_dest,
                )
            LOGGER.info("Autostart is enabled (recommended).")

            return True

        except Exception as e:
            LOGGER.error(
                f"Autostart could not be configured. Could not copy "
                f"launch agent plist from {const.APP_PATH} to "
                f"{launch_agent_dest}.\nError: {str(e)}"
            )

            return False

    # Linux: Create systemd service (WiP).
    else:
        raise NotImplementedError("Linux-support is still work in progress.")
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


def del_autostart():
    # macOS: Delete launch agent.
    if const.CURRENT_PLATFORM.startswith("DARWIN"):
        launch_agent_dest = f"{const.USER_HOME}/Library/LaunchAgents/dev.lennolium.swiftguard.plist"

        # If the launch agent exists, delete it.
        if os.path.isfile(launch_agent_dest):
            os.remove(launch_agent_dest)

        LOGGER.info("Autostart is disabled (not recommended).")

        return True

    # Linux: Delete systemd service (WiP).
    else:
        raise NotImplementedError("Linux-support is still work in progress.")
