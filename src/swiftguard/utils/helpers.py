#!/usr/bin/env python3

"""
helpers.py: TODO: Headline...

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2024.1"
__date__ = "2024-02-22"
__status__ = "Prototype/Development/Production"

# Imports.
import traceback
import logging
import shutil
import webbrowser
from collections import deque

from pathlib import Path

import keyring as kr

from PySide6.QtWidgets import QApplication

import swiftguard.init.exceptions as exc
from swiftguard.constants import C
from swiftguard.constants import __email__ as mail_addr
from swiftguard.utils import process

# Child logger.
LOGGER = logging.getLogger(__name__)


def format_log(log_lines: list[str] | deque[str]) -> str:
    """
    Format the log lines for the error prompt. This function formats
    the log lines with HTML tags to color the log levels.

    :param log_lines: The log lines to format.
    :type log_lines: list[str] | deque[str]
    :return: The formatted log lines.
    :rtype: str
    """

    lines = "".join(log_lines)

    formatted_lines = ""
    log_levels = {
            "CRITICAL": "red; font-weight: bold",
            "ERROR": "red",
            "WARNING": "#ffda3d",
            }
    current_color = None
    for line in lines.split("\n"):
        for level, color in log_levels.items():
            if line.startswith(level):
                if current_color:
                    formatted_lines += '</span>'
                current_color = color
                formatted_lines += f'<span style="color:{color};">{line}<br>'
                break
        else:
            if current_color and not any(
                    line.startswith(lvl) for lvl in ["INFO", "DEBUG"]
                    ):
                formatted_lines += f'{line}<br>'
            else:
                if current_color:
                    formatted_lines += '</span>'
                    current_color = None
                formatted_lines += f'{line}<br>'

    if current_color:
        formatted_lines += '</span>'

    return formatted_lines


def send_log(lines: str) -> None:
    """
    Send the last 50 lines of the log file to developer via the user's
    system email client.

    :param lines: The last 50 lines of the log file.
    :type lines: str
    :return: None
    """

    try:
        # Needed to remove empty lines (ugly).
        lines = "\n".join(line for line in lines.split("\n") if line)

        body = ("Dear Lennart,\n\n"
                "I'm using your application 'swiftGuard', but I experienced "
                "an issue that caused the application to crash. "
                f"Here are the last 50 lines of the log file:\n\n"
                f"{lines}")

        webbrowser.open(
                url=f"mailto:{mail_addr}?subject=swiftGuard: I experienced an "
                    f"issue&body={body}",
                new=1,
                )

    except Exception as e:
        LOGGER.error(
                f"Failed to send crash log to developer: "
                f"{e.__class__.__name__}: {e} \n"
                f"{traceback.format_exc()}"
                )


def open_log() -> None:
    """
    Open the folder containing the log file with Finder.app on macOS.

    :return: None
    """

    res = process.Process(
            binary_path="/usr/bin/open",
            args=(C.log.FILE.parent,),
            timeout=5,
            blocking=True,
            ).run()

    if res != 0:
        LOGGER.error("Failed to open log file with log viewer. "
                     f"Code={res.return_code}, "
                     f"Stdout={res.stdout}, "
                     f"Stderr={res.stderr}."
                     )


def open_github_issue(lines: str) -> None:
    """
    Copy the log to the clipboard and open the GitHub issue page in the
    user's default web browser.

    :param lines: The last 50 lines of the log file.
    :type lines: str
    :return: None
    """

    try:
        # Needed to remove empty lines (ugly).
        lines = "\n".join(line for line in lines.split("\n") if line)

        # Copy the log to the clipboard.
        clipboard(text=lines)

        # Open the GitHub issue page in the user's default web browser.
        webbrowser.open(
                url=C.app.URLS["issues"],
                new=1,
                )

    except Exception as e:
        LOGGER.error("Failed to open GitHub issue page and copy log to "
                     f"clipboard: {e.__class__.__name__}: {e} \n"
                     f"{traceback.format_exc()}"
                     )


def parse_args(*args: list) -> None:
    """
    Parse the command line arguments and execute the corresponding
    actions.

    :param args: Command line arguments.
    :type args: list
    :return: None
    """

    if len(args) == 1:
        return

    LOGGER.info(f"CLI Arguments: {args[1:]}")
    if any(arg in args for arg in ("--reset", "-r")):
        C.cfg.reset()
        LOGGER.info("Configuration was reset.")

    # Log level is changed just for this session.
    if any(arg in args for arg in ("--debug", "-d")):
        C.log.LOGGER.set_level("DEBUG")

        C.cfg.CFG["log_level"] = "DEBUG"
        LOGGER.info("Log level set to 'DEBUG' for this session.")

    elif any(arg in args for arg in ("--log", "-l")):
        log_level = None
        for i, arg in enumerate(args):
            if (arg == "--log" or arg == "-l") and i + 1 < len(args):
                log_level = args[i + 1].upper()
                break

        if log_level:
            C.log.LOGGER.set_level(log_level)
            LOGGER.info(
                    f"Log level set to '{log_level}' for this session."
                    )

    if any(arg in args for arg in ("--help", "-h")):
        LOGGER.info("Help:")
        LOGGER.info("  -h, --help: Show this help message.")
        LOGGER.info("  -r, --reset: Reset the configuration to default.")
        LOGGER.info(
                "  -d, --debug: Set log level to 'DEBUG' for this session."
                )
        LOGGER.info(
                "  -l, --log: Set log level to a specific level for this "
                "session. Usage: '-l [LEVEL]'. Example: '-l INFO'."
                )

    if any(arg in args for arg in ("--version", "-v")):
        LOGGER.info(f"swiftGuard: {__version__} ({__build__})")


def run_sudo_script(
        script_path: Path | str,
        script_args: list[str] = None,
        ) -> int:
    """
    Run a shell script with root rights using the macOS API.

    :param script_path: Path to the sudo script.
    :type script_path: Path
    :param script_args: List of arguments for the script (optional).
    :type script_args: list[str]
    :raises SudoExecuteScriptError: If the execution failed, due to
        the user not granting the necessary root rights.
    :return: The return code of the script execution
    :rtype: int
    """

    try:
        if script_args is None:
            script_args = []

        import ctypes
        import ctypes.util
        from ctypes import byref

        # Import  C libraries for interacting via ctypes with the
        # macOS API.
        sec = ctypes.cdll.LoadLibrary(ctypes.util.find_library("Security"))

        k_authorization_flag_defaults = 0
        auth = ctypes.c_void_p()
        r_auth = byref(auth)
        sec.AuthorizationCreate(
                None,
                None,
                k_authorization_flag_defaults,
                r_auth
                )

        exe = ["/bin/sh", str(script_path)]

        # Add the script arguments to the executable list.
        exe.extend(script_args)

        # exe = [sys.executable, str(PATH / "child.py")]
        args = (ctypes.c_char_p * len(exe))()
        for i, arg in enumerate(exe[1:]):
            args[i] = arg.encode("utf8")

        io = ctypes.c_void_p()

        return_code = sec.AuthorizationExecuteWithPrivileges(
                auth,
                exe[0].encode("utf8"),
                0,
                args,
                byref(io)
                )

    except Exception as e:
        raise exc.SudoExecuteScriptError(e)

    # MacOS authorization errors.
    if return_code != 0:
        raise exc.SudoExecuteScriptError(
                f"AuthorizationExecute of the"
                f"script '{script_path}' as root failed with return "
                f"code: {return_code}"
                )

    LOGGER.info("Sudo script executed successfully.")

    return return_code


def uninstall_app(keep_config: bool = False) -> None:
    """
    The uninstall_app function uninstalls the application by removing
    the application bundle from the Applications folder, configuration
    files, logs, keyring entries, attacker photos taken,
    the privileged helper, the custom sudoers file and all launch agents
    created. So no trace of swiftGuard is left and the uninstall-script
    is self-deleted after execution.

    :param keep_config: If True, the configuration file will not be
        deleted (default: False).
    :type keep_config: bool
    :raises exc.UninstallError: If error occurred during uninstallation.
    :return: None
    """

    # TODO: remove later! security measure!
    print("UNINSTALL CALLED WITH KEEP CONFIG:", keep_config)

    return

    from swiftguard.app.app import SwiftGuardApp
    app: SwiftGuardApp | QApplication | None = QApplication.instance()

    # Check if the uninstall-script exists.
    if not C.app.UNINSTALL_SCRIPT.exists(follow_symlinks=False):
        raise exc.UninstallError("The uninstall script could not be found at "
                                 f"'{C.app.UNINSTALL_SCRIPT}'."
                                 )

    # Move the uninstall-script to the /tmp folder.
    Path("/tmp/").mkdir(parents=True, exist_ok=True)
    shutil.copy(
            src=C.app.UNINSTALL_SCRIPT,
            dst=Path("/tmp/uninstall-app.sh")
            )

    # Now we are stopping each crucial app component, reducing the
    # chance of a crash during uninstallation.
    if app is not None:

        # Stop the guarding workers.
        app.workers_toggle(force_stop=True)

        # Stop runtime integrity checks.
        if hasattr(app, "integrity_mgr"):
            app.integrity_mgr.stop()
            app.integrity_mgr = None

        # Remove main application launch agent.
        if hasattr(app, "launchagent_mgr"):
            app.launchagent_mgr.deactivate()
            app.launchagent_mgr = None

        # Stop update checks, hotkey listener and notification system.
        if hasattr(app, "update_mgr"):
            app.update_mgr.disable_background_check()
            app.update_mgr = None

        if hasattr(app, "hotkey_mgr"):
            app.hotkey_mgr = None

        if hasattr(app, "notification_mgr"):
            app.notification_mgr = None

    # Privileged helper.
    if (app is not None
            and hasattr(app, "helper_mgr")):
        #  Stop/exit the helper now, if it is running.
        if app.helper_mgr.binary_running:
            for i in range(2):
                try:
                    app.helper_mgr.cmd_exit()
                    app.helper_mgr.stop()
                    break
                except exc.CommandFailedError:
                    continue

        # Remove the launch agent of the helper.
        app.helper_mgr.uninstall_launch_agent()

        # Remove helper logs and socket file.
        Path("/tmp/dev.lennolium.swiftguardhelper.err").unlink(missing_ok=True)
        Path("/tmp/dev.lennolium.swiftguardhelper.out").unlink(missing_ok=True)
        C.helper.SOCKET_PATH.unlink(missing_ok=True)

        app.helper_mgr = None

    # Remove the configuration file and all keyring entries.
    if not keep_config:
        C.cfg.FILE.unlink(missing_ok=True)

        keyring_services = ("swiftGuard-key",
                            "swiftGuard-hash",
                            "swiftGuard-helper")

    # If we keep the config, we also need to keep its hash and the key
    # to encrypt the config file.
    else:
        keyring_services = ("swiftGuard-helper",)

    for service in keyring_services:
        kr.delete_password(service_name=service,
                           username="swiftguard@lennolium.dev"
                           )

    # Remove now all caches and attacker photos.
    for file in C.email.PHOTO_FILE.parent.glob("*"):
        if file.is_file():
            file.unlink(missing_ok=True)
        else:
            shutil.rmtree(path=file, ignore_errors=True)

    C.email.PHOTO_FILE.parent.rmdir()

    # Last steps: Delete all logs and the log folder.
    for file in C.log.FILE.parent.glob("*"):
        if file.is_file():
            file.unlink(missing_ok=True)
        else:
            shutil.rmtree(path=file, ignore_errors=True)

    C.log.FILE.parent.rmdir()

    # Get the path of the application bundle (swiftGuard.app).
    app_path = None
    current_path = Path(__file__).resolve()
    while current_path != current_path.parent:
        if current_path.name.endswith(".app"):
            app_path = current_path
            break

        current_path = current_path.parent

    if app_path is None:
        raise exc.UninstallError("The application bundle could not be found.")

    # Now we launch the uninstall-script and pass the .app and the
    # custom sudoers file we need to delete.
    try:
        _ = run_sudo_script(
                script_path=C.app.UNINSTALL_SCRIPT,
                script_args=[
                        str(app_path),
                        str(C.helper.SUDOERS_PATH)]
                )

    except exc.SudoExecuteScriptError as e:
        raise exc.UninstallError(e)


def current_wifi() -> str:
    """
    The current_wifi function returns the SSID of the currently
    connected Wi-Fi network.

    :return: The SSID of the currently connected Wi-Fi network or
        an empty string if not connected.
    :rtype: str
    """

    try:
        res = process.Process(
                binary_path="/usr/sbin/networksetup",
                args=("-getairportnetwork",
                      "en0"),
                timeout=1,
                blocking=True,
                ).run()

        for line in res.stdout.split("\n"):
            if "Current Wi-Fi Network" in line:
                return line.split(":")[1].strip()

        return ""

    except Exception as _:
        return ""


def reset_camera_access() -> None:
    """
    Resets the camera access permissions for the current user. This as
    side effect will reset the camera permissions for all applications.
    So we will use this only sparingly.

    :return: None
    """

    _ = process.Process(
            binary_path="/usr/bin/tccutil",
            args=("reset",
                  "Camera"),
            timeout=3,
            blocking=False,
            ).run()


def clipboard(text: str) -> None:
    """
    Copy the given text to the clipboard.

    :param text: The text to copy to the clipboard.
    :type text: str
    """

    # Input sanitization and validation.
    if not isinstance(text, str):
        raise TypeError("Text to copy to the clipboard must be a string.")
    else:
        text = C.sec.SANITIZE_CLIPBOARD.sub(repl="", string=text)

    # Qt implementation.
    # app = QApplication(sys.argv)
    # cb = QApplication.clipboard()
    # cb.clear(mode=cb.Clipboard)
    # cb.setText(text, mode=cb.Clipboard)

    # No dependencies implementation.
    res = process.Process(
            binary_path="/usr/bin/pbcopy",
            stdin=text,
            timeout=3,
            blocking=True,
            ).run()

    if (res.return_code != 0) and (res.return_code != 2):
        LOGGER.error(
                f"Could not copy to clipboard. "
                f"Code={res.return_code}, "
                f"Stdout={res.stdout}, "
                f"Stderr={res.stderr}."
                )

    # try:
    #     subprocess.run(args="pbcopy",
    #                    text=True,
    #                    input=text,
    #                    timeout=5
    #                    )
    #
    # except Exception as e:
    #     LOGGER.error(
    #             f"Could not copy to clipboard. "
    #             f"Error: {e.__class__.__name__}: {e} \n"
    #             f"{traceback.format_exc()}"
    #             )


def apple_lookup(name: str, bcd: str) -> str:
    """
    The apple_lookup function takes two arguments:
        1. The name of the device (e.g., iPhone, iPad, iPod)
        2. The BCD code for the device (e.g., 1234,5678)

    Reference: https://gist.github.com/adamawolf/3048717

    :param name: The name of the device (e.g., iPhone, iPad, iPod).
    :type name: str
    :param bcd: The BCD code for the device (e.g., 1234,5678).
    :type bcd: str
    :return: The real world name of the device (e.g., iPhone 15 Pro).
    :rtype: str
    """

    name = name.lower()

    if name == "iphone":
        name = C.res.IPHONES.get(bcd, "Generic iPhone")

    elif name == "ipad":
        name = C.res.IPADS.get(bcd, "Generic iPad")

    elif name == "ipod":
        name = C.res.IPODS.get(bcd, "Generic iPod")

    elif name == "watch":
        name = C.res.WATCHES.get(bcd, "Generic Apple Watch")

    else:
        name = "Generic Apple Device"

    return name


if __name__ == "__main__":
    app = QApplication()

    input_text = input("Enter text: ")

    clipboard(text=input_text)

    # show_integrity_dialog(Exception("Test"))

    # from swiftguard.ui import dialogs

    # dialogs.show_uninstall_dialog()
