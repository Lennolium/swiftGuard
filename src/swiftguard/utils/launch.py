#!/usr/bin/env python3

"""
launch.py: TODO: Headline...

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-02-28"
__status__ = "Prototype/Development/Production"

# Imports.
import logging
import traceback

from swiftguard.constants import C
from swiftguard.init import exceptions as exc
from swiftguard.init import models
from swiftguard.utils import process

# Child logger.
LOGGER = logging.getLogger(__name__)


class LaunchAgentManager(metaclass=models.Singleton):
    """
    LaunchAgent for macOS and Linux.
    """

    def __init__(self) -> None:
        """
        Initialize the LaunchAgent class.

        :raise exc.LaunchAgentInitError: If the LaunchAgent could not be
            initialized.
        :return: None
        """

        # If the LaunchAgent is already initialized, return.
        if hasattr(self, "agent"):
            return

        try:
            # Initialize the LaunchAgent depending on the OS.
            if C.app.OS == "macOS":
                self.agent = _MacOSAgent.init()
            else:
                self.agent = _LinuxAgent.init()

            # Get the user's preference and set LaunchAgent accordingly.
            if C.cfg.CFG["autostart"]:
                self.activate()
            else:
                self.deactivate()

        except Exception as e:
            raise exc.LaunchAgentInitError(
                    f"Could not initialize LaunchAgent. "
                    f"Error: {e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )

    @property
    def is_active(self) -> bool:
        """
        Get the current state of the LaunchAgent, if the auto start at
        login is enabled or disabled.

        :return: True if the LaunchAgent is active, False otherwise.
        :rtype: bool
        """
        return self.agent.is_active()

    def activate(self) -> None:
        """
        Activate the LaunchAgent for autostart at login.

        :raise exc.LaunchAgentActivateError: If the LaunchAgent could not
            be activated.
        :return: None
        """

        try:
            self.agent.activate()
            C.cfg.CFG["autostart"] = True
            LOGGER.info("Autostart is enabled (recommended).")

        except Exception as e:
            C.cfg.CFG["autostart"] = False
            raise exc.LaunchAgentActivateError(
                    f"Could not initialize autostart at login. "
                    f"Error: {e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )

    def deactivate(self) -> None:
        """
        Deactivate the LaunchAgent for autostart at login.

        :raise exc.LaunchAgentDeactivateError: If the LaunchAgent could
            not be deactivated.
        :return: None
        """

        try:
            self.agent.deactivate()
            C.cfg.CFG["autostart"] = False
            LOGGER.info("Autostart is disabled (not recommended).")

        except Exception as e:
            C.cfg.CFG["autostart"] = True
            raise exc.LaunchAgentDeactivateError(
                    f"Could not disable autostart at login. "
                    f"Error: {e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )


class _Agent:
    """
    Abstract class for LaunchAgents.
    """

    def __init__(self) -> None:
        """
        Does not allow direct instantiation of the class.
        """

        raise NotImplementedError(
                f"The class '{type(self).__name__}' cannot be instantiated "
                f"directly. Use LaunchAgentManager instead."
                )

    @classmethod
    def init(cls) -> _Agent:
        """
        Create a new instance of the class.

        :return: A new instance of the class.
        :rtype: _Agent
        """

        return cls.__new__(cls)


class _MacOSAgent(_Agent):
    """
    LaunchAgent for macOS. Not to be instantiated directly.
    """

    @staticmethod
    def is_active() -> bool:
        """
        Get the current state of the LaunchAgent.

        :return: True if the LaunchAgent is active, False otherwise.
        """

        # Check if the LaunchAgent exists.
        return C.app.LAUNCH_AGENT_MACOS.exists()

    def activate(self) -> None:
        """
        Activate the LaunchAgent for autostart at login.

        :raise exc.LaunchAgentCreateError: If the LaunchAgent could not
            be created.
        :return: None
        """

        if self.is_active():
            return

        # Create LaunchAgents directory if it does not exist.
        C.app.LAUNCH_AGENT_MACOS.parent.mkdir(
                parents=True,
                exist_ok=True,
                )

        # Maybe the user renames the app or puts it in a different
        # directory, so we get the path to binary dynamically.
        binary_path = None
        for par in C.app.PATH.parents:
            if par.name == "Contents":
                binary_path = par
                break

        with open(file=(C.app.LAUNCH_AGENT_SOURCE /
                        "dev.lennolium.swiftguard.plist"),
                  mode="r",
                  ) as fh:
            # Substitute path placeholder with actual path to the
            # executable.
            launch_plist = fh.read().replace(
                    "$PATH_PLACEHOLDER",
                    str(binary_path),
                    )

        # Write the plist to the LaunchAgents directory.
        with open(file=C.app.LAUNCH_AGENT_MACOS, mode="w") as fh:
            fh.write(launch_plist)

        # Load the LaunchAgent.
        process.Process(
                binary_path="/bin/launchctl",
                args=("load",
                      C.app.LAUNCH_AGENT_MACOS),
                timeout=5,
                blocking=True,
                ).run()

    def deactivate(self) -> None:

        # Unload the LaunchAgent.
        process.Process(
                binary_path="/bin/launchctl",
                args=("unload",
                      C.app.LAUNCH_AGENT_MACOS),
                timeout=5,
                blocking=True,
                ).run()

        # If the launch agent exists, delete it.
        if self.is_active():
            C.app.LAUNCH_AGENT_MACOS.unlink(missing_ok=True)


class _LinuxAgent(_Agent):
    """
    LaunchAgent for Linux. Not to be instantiated directly.
    """

    @staticmethod
    def is_active() -> bool:
        """
        Get the current state of the LaunchAgent.

        :raise NotImplementedError: If the method is not implemented.
        :return: True if the LaunchAgent is active, False otherwise.
        """
        raise NotImplementedError(
                "Linux-support is still work in progress."
                )

    def activate(self) -> None:
        """
        Activate the LaunchAgent for autostart at login.

        :raise NotImplementedError: If the method is not implemented.
        :return: None
        """

        raise NotImplementedError(
                "Linux-support is still work in progress."
                )
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

    def deactivate(self) -> None:
        """
        Deactivate the LaunchAgent for autostart at login.

        :raise NotImplementedError: If the method is not implemented.
        :return: None
        """
        raise NotImplementedError(
                "Linux-support is still work in progress."
                )


# Main.
if __name__ == "__main__":
    obj = LaunchAgentManager()

    print(obj.is_active)

    obj.deactivate()

    # obj.activate()

    print(obj.is_active)
