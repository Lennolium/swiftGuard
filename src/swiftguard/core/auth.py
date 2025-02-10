#!/usr/bin/env python3

"""
core/auth.py: Used to authenticate the user with password or Touch ID.

The user can set a password for the application or use Touch ID for
authentication. If no authentication is configured, the user can defuse
the alarm without any authentication.


**USAGE:**

*Create a new instance.*

- from swiftguard.core import auth
- auth_man = auth.AuthenticationManager()

*Set up the password/Touch ID or no credential's authentication. The
password needs to be at least 4 characters long and is saved in the
encrypted config.*

- if auth_man.setup_password(): print("Password set.")
- if auth_man.setup_touchid(): ...
- if auth_man.setup_no_auth(): ...

*Challenge the user for authentication. If no authentication is
configured, no challenge dialog is shown. If the authentication fails,
a DefusingFailedError is raised. If the manager is not ready for use,
a NotReadyError is raised.*

- auth_man.challenge()

*Get different states of the authentication manager.*

- if auth_man.ready: print("Ready for use and fully configured.")
- if auth_man.no_auth_configured: ...
- if auth_man.password_configured: ...
- if auth_man.touchid_configured: ...
- if auth_man.touchid_available: print("This device has Touch ID.")

"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-06-05"
__status__ = "Prototype/Development/Production"

# Imports.
import logging
import sys
import traceback
import ctypes
from LocalAuthentication import LAContext
from LocalAuthentication import LAPolicyDeviceOwnerAuthenticationWithBiometrics

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication,
                               QDialog,
                               QHBoxLayout,
                               QVBoxLayout,
                               QLabel,
                               QLineEdit,
                               QPushButton)

from swiftguard.constants import C
from swiftguard.core import integrity
from swiftguard.init import exceptions as exc, models

# Child logger.
LOGGER = logging.getLogger(__name__)


class PasswordDialog(QDialog):
    """
    Dialog to set a password for the application.
    """

    def __init__(
            self,
            title: str,
            description: str,
            confirm: bool = True,
            parent=None,
            ) -> None:
        """
        Initialize the dialog for setting a password. User needs to
        enter a password and confirm it. Minimum length is 4 characters
        and the passwords need to match.

        :param title: Title of the dialog.
        :type title: str
        :param description: Description of the dialog.
        :type description: str
        :param confirm: If True, a confirmation password input field is
            shown. Default is True.
        :type confirm: bool
        :param parent: Parent widget of the dialog.
        :type parent: QWidget
        :return: None
        """

        super(PasswordDialog, self).__init__(parent)

        self.password_retries = 2

        self.setWindowTitle(title)
        self.setFixedSize(300, 300)
        self.layout = QVBoxLayout(self)

        # Description of the dialog.
        self.explanation_label = QLabel(f"\n{description}\n\n", self)
        self.explanation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.explanation_label.setWordWrap(True)
        self.layout.addWidget(self.explanation_label)

        # Password input field.
        self.password_layout = QHBoxLayout()
        # self.label = QLabel("Password: ", self)
        # self.password_layout.addWidget(self.label)
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setPlaceholderText(" Password/PIN")
        self.lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.lineEdit.textChanged.connect(self.check_length)
        self.password_layout.addWidget(self.lineEdit)

        # Eye icon to show/hide password.
        self.eye_button = QPushButton("show", self)
        self.eye_button.setCheckable(True)
        self.eye_button.clicked.connect(self.toggle_password_vis)
        self.password_layout.addWidget(self.eye_button)
        self.layout.addLayout(self.password_layout)

        # Confirm password input field (initially hidden).
        self.confirm = confirm
        self.confirm_lineEdit = QLineEdit(self)
        self.confirm_lineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_lineEdit.setPlaceholderText(" Confirm Password/PIN")
        self.confirm_lineEdit.setVisible(False)
        self.confirm_lineEdit.textChanged.connect(self.validate_confirm)
        self.layout.addWidget(self.confirm_lineEdit)

        # Error message label for password length.
        self.error_label = QLabel("", self)
        self.error_label.setStyleSheet("color: red; font-weight: 500;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.error_label)

        # Cancel button.
        self.button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)

        # Ok button.
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.validate)
        self.ok_button.setDefault(True)
        self.button_layout.addWidget(self.ok_button)
        self.layout.addLayout(self.button_layout)

        # Set tab order.
        self.setTabOrder(self.lineEdit, self.confirm_lineEdit)
        self.setTabOrder(self.confirm_lineEdit, self.ok_button)
        self.setTabOrder(self.ok_button, self.cancel_button)
        self.setTabOrder(self.cancel_button, self.eye_button)
        self.setTabOrder(self.eye_button, self.lineEdit)

    def validate(self) -> None:
        """
        Validate the password. Minimum length is 4 characters and the
        passwords need to match. Checked when the OK button is clicked.

        :return: None
        """

        # Set password.
        if self.confirm:
            if len(self.lineEdit.text()) < 4:
                self.error_label.setText("Minimum 4 characters required.")
            elif self.lineEdit.text() != self.confirm_lineEdit.text():
                self.error_label.setText("Passwords do not match.")
            else:
                self.error_label.setText("")
                self.accept()

        # Check password.
        else:
            if C.cfg.CFG["password"] == integrity.get_string_hash(
                    self.lineEdit.text()
                    ):
                self.error_label.setText("")
                self.accept()
            else:
                self.error_label.setText("Wrong password.")
                if self.password_retries <= 0:
                    self.accept()
                self.password_retries -= 1

    def validate_confirm(self) -> None:
        """
        Validate the password to confirm. If the passwords match, the
        error label is cleared. Called when the password to confirm
        input field is changed.

        :return: None
        """

        if self.lineEdit.text() == self.confirm_lineEdit.text():
            self.error_label.setText("")

    def check_length(self) -> None:
        """
        Check the length of the password. If the password is at least
        4 characters long, confirmation password input field is shown.
        Called when the password input field is changed.

        :return: None
        """

        if self.confirm:
            if len(self.lineEdit.text()) >= 4:
                self.error_label.setText("")
                self.confirm_lineEdit.setVisible(True)

            else:
                pass
                # self.confirm_lineEdit.setVisible(False)

        else:
            self.error_label.setText("")

    def toggle_password_vis(self) -> None:
        """
        Toggle the visibility of the password in the password input
        field. Called when the show/hide button is clicked.

        :return: None
        """

        if self.eye_button.isChecked():
            self.eye_button.setText(" hide ")
            self.lineEdit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.eye_button.setText("show")
            self.lineEdit.setEchoMode(QLineEdit.EchoMode.Password)


class AuthManager(metaclass=models.Singleton):
    """
    Authentication manager for the application. Handles Touch ID and
    password authentication. If no password is set, the user is
    prompted to set a password. If Touch ID is available, the user can
    authenticate with Touch ID.
    """

    kTouchIdPolicy = LAPolicyDeviceOwnerAuthenticationWithBiometrics

    c = ctypes.cdll.LoadLibrary(name=None)

    DISPATCH_TIME = sys.maxsize

    dispatch_semaphore_create = c.dispatch_semaphore_create
    dispatch_semaphore_create.restype = ctypes.c_void_p
    dispatch_semaphore_create.argtypes = [ctypes.c_int]

    dispatch_semaphore_wait = c.dispatch_semaphore_wait
    dispatch_semaphore_wait.restype = ctypes.c_long
    dispatch_semaphore_wait.argtypes = [ctypes.c_void_p, ctypes.c_uint64]

    dispatch_semaphore_signal = c.dispatch_semaphore_signal
    dispatch_semaphore_signal.restype = ctypes.c_long
    dispatch_semaphore_signal.argtypes = [ctypes.c_void_p]

    def __init__(self) -> None:
        """
        Initialize the authentication manager.
        """

        self.context = LAContext.new()

    @property
    def ready(self) -> bool:
        """
        Check if the authentication manager is ready for use. This
        means a password is set or Touch ID is configured or no
        authentication required for defusing is configured.

        :return: True if the authentication manager is ready, False
            otherwise.
        :rtype: bool
        """

        return (self.password_configured
                or self.touchid_configured
                or self.no_auth_configured)

    @property
    def no_auth_configured(self) -> bool:
        """
        Check if no authentication (password or Touch ID) is configured.
        So the user can defuse the alarm without any authentication.

        :return: True if no authentication is configured, False
            otherwise.
        :rtype: bool
        """

        return (not self.password_configured
                and not self.touchid_configured)

    @property
    def password_configured(self) -> bool:
        """
        Is a password configured.

        :return: True if a password is configured, False otherwise.
        :rtype: bool
        """

        return bool(C.cfg.CFG["password"])

    @property
    def touchid_configured(self) -> bool:
        """
        Is Touch ID authentication configured.

        :return: True if Touch ID authentication is configured, False
            otherwise.
        :rtype: bool
        """

        return C.cfg.CFG["touchid"]

    @property
    def touchid_available(self) -> bool:
        """
        Check if Touch ID is available on the current machine.

        :return: True if Touch ID is available, False otherwise.
        :rtype: bool
        """

        supported = self.context.canEvaluatePolicy_error_(
                self.kTouchIdPolicy,
                None,
                )[0]
        enrolled = (self.context.evaluatedPolicyDomainState() is not None)

        return supported and enrolled

    @staticmethod
    def _challenge_password(
            title: str = "swiftGuard: Password required",
            description: str = None,
            ) -> bool:
        """
        Show a password dialog to authenticate the user.

        :param title: Window title displayed in the dialog (optional).
        :type title: str
        :param description: Description showed above the password input
            field (optional). Default is a defusing message.
        :type description: str
        :return: True if the authentication was successful, False
            otherwise.
        :rtype: bool
        """

        if description is None:
            description = "🚨 Do you want to DEFUSE the alarm? 🚨"
        else:
            if not description.endswith((".", "!", "?")):
                description = f"{description}."

        dialog = PasswordDialog(
                title=title,
                description=description,
                confirm=False,
                )

        dialog.setFixedSize(300, 200)

        # Dialog was accepted -> Check the password.
        if dialog.exec():
            if C.cfg.CFG["password"] == integrity.get_string_hash(
                    dialog.lineEdit.text()
                    ):
                return True

            return False

        # Dialog was canceled.
        else:
            return False

    def _challenge_touchid(
            self,
            reason: str = None,
            ) -> bool:
        """
        Show a Touch ID dialog to authenticate the user.

        :param reason: Reason for the authentication (optional). Default
            is a defusing message.
        :type reason: str
        :return: True if the authentication was successful, False
            otherwise.
        :rtype: bool
        """

        if reason is None:
            reason = ("\n\n🚨 Do you want to DEFUSE the alarm? 🚨\n\n"
                      "‼️ Ensure it is a false alarm")

        else:
            reason = f"\n\n{reason}"

        self.context = LAContext.new()
        sema = self.dispatch_semaphore_create(0)

        # We can not reassign objects from another scope, but we can
        # modify them.
        res = {"success": False, "error": None}

        def cb(_success, _error):
            res["success"] = _success
            if _error:
                res["error"] = _error.localizedDescription()
            self.dispatch_semaphore_signal(sema)

        self.context.evaluatePolicy_localizedReason_reply_(
                self.kTouchIdPolicy,
                reason,
                cb
                )

        self.dispatch_semaphore_wait(sema, self.DISPATCH_TIME)

        return res["success"]

    @staticmethod
    def setup_no_auth() -> bool:
        """
        Configure the application to not require any authentication for
        defusing the alarm.

        :return: True if the setup was successful, False otherwise.
        :rtype: bool
        """

        try:
            C.cfg.CFG["password"] = None
            C.cfg.CFG["touchid"] = False

            LOGGER.info("Disabled required authentication for alarm defusing.")
            return True

        except Exception as e:
            LOGGER.error(f"Setup of no authentication failed: "
                         f"{e.__class__.__name__}: {e} \n"
                         f"{traceback.format_exc()}"
                         )
            return False

    @staticmethod
    def setup_password(
            title: str = "Enter a password",
            description: str = "Please choose a secure password to "
                               "enable the defusing of false alarms.",
            ) -> bool:
        """
        Setup password authentication for the application. The user is
        prompted to set a password and confirm it. Minimum length is 4
        characters. It is saved in the encrypted config.

        :param title: Title of the password dialog.
        :type title: str
        :param description: Description of the password dialog,
            displayed above the password input field.
        :type description: str
        :return: True if the setup was successful, False otherwise.
        :rtype: bool
        """

        try:
            dialog = PasswordDialog(title=title, description=description)

            # If the dialog was accepted, store the password in the config.
            if dialog.exec():
                C.cfg.CFG["password"] = integrity.get_string_hash(
                        dialog.lineEdit.text()
                        )
                C.cfg.CFG["touchid"] = False

                LOGGER.info("Enabled and set password for alarm defusing.")
                return True

            else:
                return False

        except Exception as e:
            LOGGER.error(f"Setup of password authentication failed: "
                         f"{e.__class__.__name__}: {e} \n"
                         f"{traceback.format_exc()}"
                         )
            return False

    def setup_touchid(
            self,
            reason: str = "authenticate yourself with Touch ID to enable "
                          "the defusing of false alarms",
            ) -> bool:
        """
        Setup Touch ID authentication for the application.
        The user is prompted to authenticate with Touch ID to enable
        the defusing of false alarms.

        :param reason: Reason for the authentication, displayed in the
            Touch ID dialog.
        :type reason: str
        :return: True if the setup was successful, False otherwise.
        :rtype: bool
        """

        try:
            # Let the user confirm his touchid and test the authentication.
            if self._challenge_touchid(reason=reason):
                C.cfg.CFG["touchid"] = True
                C.cfg.CFG["password"] = None

                LOGGER.info(
                        "Enabled Touch ID authentication for alarm defusing."
                        )
                return True

            return False

        except Exception as e:
            LOGGER.error(f"Setup of Touch ID authentication failed: "
                         f"{e.__class__.__name__}: {e} \n"
                         f"{traceback.format_exc()}"
                         )
            return False

    def challenge(self, reason: str = None) -> None:
        """
        Challenge the user for authentication with password or Touch ID.
        If no authentication is configured, the function early returns.
        If the authentication fails, an exception is raised.

        :param reason: Reason for the authentication, displayed in the
            challenge dialog (optional. Default displays a defusing
            message).
        :type reason: str
        :raises NotReadyError: If the authentication manager is not
            ready for use/fully setup.
        :raises DefusingFailedError: If the authentication for defusing
            the alarm fails due to wrong credentials or canceled by the
            user.
        :raises AuthenticationError: If the authentication fails for an
            unknown reason.
        :return: None
        """

        try:

            # No countdown timer set -> No need to challenge, as the
            # alarm is not possible to defuse.
            if C.cfg.CFG["delay"] <= 0:
                return

            if not self.ready:
                raise exc.NotReadyError(
                        "AuthManager encountered an setup mismatch and is "
                        "not ready for use."
                        )

            # If no authentication is configured, we do not need to display
            # a challenge dialog and return directly.
            if self.no_auth_configured:
                return

            elif self.password_configured:
                if not self._challenge_password(description=reason):
                    raise exc.ChallengeFailedError(
                            "Password authentication for challenge failed!"
                            )

            elif self.touchid_configured:
                if not self._challenge_touchid(reason=reason):
                    raise exc.ChallengeFailedError(
                            "Touch ID authentication for challenge failed!"
                            )

        except Exception as e:

            # Defusing failed -> re-raise the exception.
            if isinstance(e, exc.AuthenticationError):
                raise e

            # Any other exception -> re-raise as AuthenticationError.
            raise exc.AuthenticationError(
                    f"During authentication for challenge an unknown error "
                    f"occurred: {e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )


if __name__ == '__main__':
    # Required for displaying the dialog (just here for testing).
    app = QApplication(sys.argv)

    auth = AuthManager()

    # auth.setup_touchid()
    auth.setup_password()
    # auth.setup_no_auth()

    print("Ready:", auth.ready)
    print("Touch ID configured:", auth.touchid_configured)
    print("Password configured:", auth.password_configured)
    print("No-Auth configured:", auth.no_auth_configured)

    print("Challenge now ...")
    auth.challenge()
