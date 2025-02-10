#!/usr/bin/env python3

"""
__main__.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2025.1"
__date__ = "2025-01-08"
__status__ = "Development"

# Imports.
import contextlib
import os
import sys
import signal
import webbrowser

from PySide6.QtCore import QDateTime

from swiftguard.init import exceptions as exc


def main() -> int:
    """
    Main entry point for the application.
    For application exit codes see: init/exceptions.py

    :return: Exit code of the application.
    :rtype: int
    """

    # Exit handler for clean exit of the application.
    for sig in (
            signal.SIGINT,
            signal.SIGTERM,
            signal.SIGQUIT,
            signal.SIGABRT,
            ):
        signal.signal(sig, exc.exit_handler)

    # Exception hook for unhandled exceptions.
    sys.excepthook = exc.exception_handler

    # Startup: Load logger, config and paths.
    with handle_integrity_exc():
        from swiftguard.constants import C
    C.log.LOGGER.info("----------------- Initialization: ----------------")
    C.log.LOGGER.info(f"Path: '{C.app.PATH}'")
    C.log.LOGGER.info(f"Version: {__version__} ({__build__})")
    C.log.LOGGER.info(f"Python: {C.app.PYTHON}")
    C.log.LOGGER.info(f"Logs: '{C.log.FILE}' (Level: {C.cfg.CFG['log_level']})"
                      )
    C.log.LOGGER.info(f"Config: '{C.cfg.FILE}' (encrypted)")
    C.log.LOGGER.info(f"System: {C.app.OS} {C.app.OS_VERSION} - {C.app.CPU} - "
                      f"{C.app.ARCH} - {C.app.RAM} RAM (supported)"
                      )

    # Run pre-flight checks.
    from init import checks
    checks.already_running()
    checks.operating_system()
    checks.filevault()
    checks.automation()

    # Create QApplication instance and pass remaining arguments.
    C.log.LOGGER.info("--------------- Application Setup: ---------------")
    from app.app import SwiftGuardApp
    app = SwiftGuardApp(sys.argv)

    # General application settings and fixes.
    app.setApplicationDisplayName("swiftGuard")
    app.setApplicationName("swiftGuard")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("lennolium.dev")
    app.setOrganizationDomain("lennolium.dev")
    # Prevent app exit, if popups/messageBoxes are closed.
    app.setQuitOnLastWindowClosed(False)
    # Fix for macOS Big Sur and older.
    if C.app.OS == "macOS" and C.app.OS_VERSION <= "11.0":
        os.environ["QT_MAC_WANTS_LAYER"] = "1"
    if hasattr(app, "setDesktopFileName"):
        app.setDesktopFileName("dev.lennolium.swiftGuard")
    app.launch_time = QDateTime.currentDateTime()
    app.launch_time_unix = QDateTime.currentSecsSinceEpoch()

    # Start app and return exit code, when app is closed.
    C.log.LOGGER.info("--------------------- Runtime: --------------------")
    return app.exec()


@contextlib.contextmanager
def handle_integrity_exc() -> None:
    """
    Context manager to handle integrity compromises, that occur before
    the application is initialized. It displays a dialog, opens the
    uninstall-guide and exits the application.

    :return: None
    """

    try:
        yield
    except exc.IntegrityError as e:

        from PySide6.QtWidgets import QApplication, QMessageBox, QWidget
        _ = QApplication()

        # Play a sound to alert the user.
        from swiftguard.utils import process
        _ = process.Process(
                binary_path="/usr/bin/afplay",
                args=("/System/Library/Sounds/Submarine.aiff",),
                timeout=1,
                blocking=False,
                ).run()

        QMessageBox.critical(QWidget(),
                             "swiftGuard",
                             f"The integrity of swiftGuard is compromised! "
                             f"Please reinstall! \n\n"
                             f"{e}",
                             QMessageBox.StandardButton.Help,
                             )
        webbrowser.open(
                url="https://github.com/Lennolium/swiftGuard?tab=readme"
                    "-ov-file#uninstall",
                new=2,
                )
        sys.exit(8)


if __name__ == "__main__":
    sys.exit(main())
