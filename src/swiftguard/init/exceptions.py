#!/usr/bin/env python3

"""
init/exceptions.py: Custom exceptions for swiftGuard.

**Hierarchy:**

* SwiftGuardException(Exception)

    x ApplicationError
        + OperatingSystemNotSupported
        + NotMainThreadError
        + BlockingMainThreadError
        + UninstallError
        + SudoExecuteScriptError

    x UpdateCheckError
        + GitHubUpdateError
        + ConnectionUpdateError

    x ConstantsError
        + ConstantsReadOnlyError
        + ConstantsLowerCaseError
        + ConstantsPrivateError

    x ConfigurationError
        + ConfigurationIntegrityError

    x LaunchAgentError
        + LaunchAgentInitError
        + LaunchAgentActivateError
        + LaunchAgentDeactivateError

    x NotificationError
        + NotificationSetupError
        + NotificationSendError
        + NotificationTakePhotoError

    x IntegrityError
        + RuntimeIntegrityError
        + BinaryIntegrityError
        + ConfigurationIntegrityError

    x MonitoringError
        + BusNotSupportedError
        + SystemProfilerError
        + SystemProfilerTerminated
        + WhiteListError
        + BluetoothControllerError
        + BluetoothDisabledError
        + NetworkControllerError
        + NetworkDisabledError

    x TamperingEvent
        + USBTamperingEvent
        + BluetoothTamperingEvent
        + NetworkTamperingEvent

    x AuthenticationError
        + NotReadyError
        + DefusingFailedError

    x HelperError
        + HelperInstallError
        + HelperSudoScriptError
        + HelperUninstallError
        + HelperNotStartedError
        + LoginFailedError
        + HMACFailedError
        + NonceReusedError
        + TTLExpiredError
        + CommandFailedError
        + ActionFailedError


**Functions:**

* exit_handler
* exception_handler

"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "swiftguard@lennolium.dev"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-02-16"
__status__ = "Prototype/Development/Production"

# Imports.
import sys
import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from swiftguard.core import devices

# Child logger.
LOGGER = logging.getLogger(__name__)


class SwiftGuardException(Exception):
    """
    Base class for exceptions in swiftGuard.
    """
    code: int = 1


class ApplicationError(SwiftGuardException):
    """
    Exception raised for application errors.
    """
    code: int = 2


class OperatingSystemNotSupported(ApplicationError):
    """
    Exception raised for Windows OS.
    """
    code: int = 20


class NotMainThreadError(ApplicationError):
    """
    Exception raised for not running in the main thread.
    """
    code: int = 21


class BlockingMainThreadError(ApplicationError):
    """
    Exception raised for blocking the main thread.
    """
    code: int = 22


class UninstallError(ApplicationError):
    """
    Exception raised for unhandled errors during uninstallation.
    """
    code: int = 23


class SudoExecuteScriptError(ApplicationError):
    """
    Exception raised for errors during execution of a script as root.
    """
    code: int = 24


class UpdateCheckError(SwiftGuardException):
    """
    Exception raised for update check errors.
    """
    code: int = 3


class GitHubUpdateError(UpdateCheckError):
    """
    Exception raised for GitHub API errors.
    """
    code: int = 30


class ConnectionUpdateError(UpdateCheckError):
    """
    Exception raised for connection errors.
    """
    code: int = 31


class ConstantsError(SwiftGuardException):
    """
    Exception raised for constants errors.
    """
    code: int = 4


class ConstantsReadOnlyError(ConstantsError):
    """
    Exception raised for trying to change a constant.
    """
    code: int = 40


class ConstantsLowerCaseError(ConstantsError):
    """
    Exception raised for trying to set a constant in lowercase.
    """
    code: int = 41


class ConstantsPrivateError(ConstantsError):
    """
    Exception raised for trying to set a private constant (_.../__...).
    """
    code: int = 42


class ConfigurationError(SwiftGuardException):
    """
    Exception raised for configuration errors.
    """
    code: int = 5


class LaunchAgentError(SwiftGuardException):
    """
    Exception raised for launch agent errors.
    """
    code: int = 6


class LaunchAgentInitError(LaunchAgentError):
    """
    Exception raised for launch agent initialization errors.
    """
    code: int = 60


class LaunchAgentActivateError(LaunchAgentError):
    """
    Exception raised for launch agent creation errors.
    """
    code: int = 61


class LaunchAgentDeactivateError(LaunchAgentError):
    """
    Exception raised for launch agent removal errors.
    """
    code: int = 62


class NotificationError(SwiftGuardException):
    """
    Exception raised for notification errors.
    """
    code: int = 7


class NotificationSetupError(NotificationError):
    """
    Exception raised for when notification setup fails.
    """
    code: int = 70


class NotificationSendError(NotificationError):
    """
    Exception raised when notification sending fails.
    """
    code: int = 71


class NotificationSetupCameraError(NotificationError):
    """
    Exception raised when setting up the camera for notification fails.
    """
    code: int = 72


class NotificationTakePhotoError(NotificationError):
    """
    Exception raised when taking a photo for the notification fails.
    """
    code: int = 73


class IntegrityError(SwiftGuardException):
    """
    Exception raised for integrity errors.
    """
    code: int = 8


class HashFileError(IntegrityError):
    """
    Exception raised for hash file not found errors.
    """
    code: int = 80


class RuntimeIntegrityError(IntegrityError):
    """
    Exception raised for integrity errors during runtime of the app.
    """
    code: int = 81


class BinaryIntegrityError(IntegrityError):
    """
    Exception raised for integrity errors in binary files.
    """
    code: int = 82


class ConfigurationIntegrityError(IntegrityError, ConfigurationError):
    """
    Exception raised for integrity errors in the configuration file.
    """
    code: int = 83


class MonitoringError(SwiftGuardException):
    """
    Exception raised for monitoring errors.
    """
    code: int = 9


class BusNotSupportedError(MonitoringError):
    """
    Exception raised for bus not supported.
    """
    code: int = 90


class SystemProfilerError(MonitoringError):
    """
    Exception raised for system profiler errors.
    """
    code: int = 91


class SystemProfilerTerminated(MonitoringError):
    """
    Exception raised to signal that the system profiler was terminated.
    """
    code: int = 92


class WhiteListError(MonitoringError):
    """
    Exception raised for whitelist errors.
    """
    code: int = 93


class BluetoothControllerError(MonitoringError):
    """
    Exception raised for Bluetooth monitoring errors.
    """
    code: int = 94


class BluetoothDisabledError(MonitoringError):
    """
    Exception raised for if Bluetooth is disabled.
    """
    code: int = 95


class NetworkControllerError(MonitoringError):
    """
    Exception raised for network monitoring errors.
    """
    code: int = 96


class NetworkDisabledError(MonitoringError):
    """
    Exception raised for if network is disabled.
    """
    code: int = 97


class TamperingEvent(SwiftGuardException):
    """
    Exception raised for tampering detected.
    """
    code: int = 255
    action: str | None = None
    device: devices.Devices | None = None


class USBTamperingEvent(TamperingEvent):
    """
    Exception raised for USB tampering detected.
    """
    code: int = 255


class BluetoothTamperingEvent(TamperingEvent):
    """
    Exception raised for Bluetooth tampering detected.
    """
    code: int = 255


class NetworkTamperingEvent(TamperingEvent):
    """
    Exception raised for network tampering detected.
    """
    code: int = 255


class AuthenticationError(SwiftGuardException):
    """
    Exceptions regarding authentication.
    """
    code: int = 90


class NotReadyError(AuthenticationError):
    """
    Exception raised if the AuthManager is not fully setup.
    """
    code: int = 91


class ChallengeFailedError(AuthenticationError):
    """
    Exception raised if defusing the alarm failed due to an unsuccessful
    authentication by the user.
    """
    code: int = 92


class HelperError(SwiftGuardException):
    """
    Exceptions regarding the privileged helper binary.
    """
    code: int = 10


class HelperInstallError(HelperError):
    """
    The helper binary could not be installed.
    """
    code: int = 100


class HelperSudoScriptError(HelperError):
    """
    The helper binary could not be installed.
    """
    code: int = 101


class HelperUninstallError(HelperError):
    """
    The helper binary could not be uninstalled.
    """
    code: int = 102


class HelperNotStartedError(HelperError):
    """
    The helper binary was not started.
    """
    code: int = 103


class LoginFailedError(HelperError):
    """
    Login to the helper binary failed.
    """
    code: int = 104


class HMACFailedError(HelperError):
    """
    HMAC verification of received message failed due to integrity error.
    """
    code: int = 105


class NonceReusedError(HelperError):
    """
    Nonce was already received. Possibly a replay attack.
    """
    code: int = 106


class TTLExpiredError(HelperError):
    """
    Timestamp of received message is too old. Possibly a replay attack.
    """
    code: int = 107


class CommandFailedError(HelperError):
    """
    Command execution failed. Only raised for normal commands (VERSION,
    HEALTH, etc.), not for actions.
    """
    code: int = 108


class ActionFailedError(HelperError):
    """
    Action execution failed. Raised for any action that was requested
    by the user with high privileges (e.g. HIBERNATE, SHUTDOWN, etc.).
    """
    code: int = 109


def _fast_cleanup() -> None:
    """
    Fast cleanup of the application. This function is called when the
    application is exited. It hides the tray icon, stops all threads
    and workers.

    :return: None
    """

    from swiftguard.init import models
    from swiftguard.app.app import SwiftGuardApp
    app: SwiftGuardApp | QApplication | None = QApplication.instance()

    if app is not None:

        if hasattr(app, "window"):
            app.window.tray.hide()
            app.window.hide()
            app.window.tray.deleteLater()
            app.window.deleteLater()

        if hasattr(app, "worker_usb"):
            app.workers_toggle(force_stop=True)

        singletons = models.Singleton.all_instances()

        if mani_mgr := singletons.get("ManipulationManager", None):
            mani_mgr.stop()

        if moni_mgr := singletons.get("MonitorManager", None):
            moni_mgr.stop()

        if help_mgr := singletons.get("HelperManager", None):
            help_mgr.stop()

        if inte_mgr := singletons.get("IntegrityManager", None):
            inte_mgr.stop()


def exit_handler(
        signum: int = 0,
        frame: object = None,
        ) -> None:
    """
    The exit_handler function is a signal handler that catches the
    SIGINT and SIGTERM signals. It then prints out a message to the
    log file, and exits with status 0.

    :param signum: Identify the signal that caused the exit_handle
        to be called (default: 0).
    :type signum: int
    :param frame: Reference the frame object that called function.
    :type frame: object
    :return: None
    """

    # Hide tray icon and stop all threads/workers.
    _fast_cleanup()

    # Stop the Qt event loop if the QApplication instance exists.
    from swiftguard.app.app import SwiftGuardApp
    app: SwiftGuardApp | QApplication | None = QApplication.instance()

    if app is not None:
        try:
            app.closeAllWindows()
            app.exit(signum)
        except Exception as _:
            pass

    if QApplication is not None:
        QApplication.closeAllWindows()
        QApplication.exit(signum)

    # Last text to display/log: Sweet bye message.
    if signum != 0:
        LOGGER.info(
                "A critical error caused the application to exit "
                "unexpectedly ... Bye!"
                )
    else:
        LOGGER.info("Exited the application gracefully ... Bye!")

    # Soft exit (after 1 second).
    QTimer.singleShot(1000, lambda: sys.exit(signum))

    # Hard exit (after 2 seconds).
    import os
    QTimer.singleShot(2000, lambda: os._exit(signum))


def exception_handler(
        exc_type,
        exc_value,
        exc_traceback,
        ) -> None:
    """
    The exception_handler function is a custom exception handler that
    logs uncaught exceptions to the log file with the level CRITICAL.
    Finally, it calls the exit_handler function to exit the program.

    :param exc_type: Store the exception type.
    :param exc_value: Get the exception value.
    :param exc_traceback: Get the traceback object.
    :return: None
    """

    # Do not log KeyboardInterrupt (Ctrl+C).
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    LOGGER.critical(msg="Uncaught Exception:",
                    exc_info=(exc_type, exc_value, exc_traceback),
                    )

    # Display debug/error prompt to the user (not for tampering events).
    if not issubclass(exc_type, TamperingEvent):
        _fast_cleanup()  # We can already clean up here.
        # Just import when needed to avoid circular imports.
        from swiftguard.constants import C
        from swiftguard.ui import dialogs

        LOGGER.info("----------------- Summary: -----------------")
        LOGGER.info(f"Warnings: {C.log.LOGGER.counter.warnings}, "
                    f"Errors: {C.log.LOGGER.counter.errors}, "
                    f"Criticals: {C.log.LOGGER.counter.criticals}"
                    )
        LOGGER.info("--------------------------------------------")
        dialogs.show_error_dialog(thrown_exc=exc_type)

    # Call the exit handler to exit the program.
    if hasattr(exc_type, "code"):
        exit_handler(signum=exc_type.code)
    else:
        exit_handler(signum=1)
