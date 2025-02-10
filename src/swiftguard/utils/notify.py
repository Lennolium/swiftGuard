#!/usr/bin/env python3

"""
utils/notify.py: Sends E-Mail in case of manipulation detection.

This module provides a notification system to send E-Mails to the
receiver(s) if a manipulation is detected. It sends an HTML and a plain
text alternative E-Mail to the receiver(s) with detailed information
about the manipulation and the system. If enabled it takes a photo of
the potential attacker and adds it base64-encoded to the E-Mail
(only for HTML E-Mail supported). If the system is once fully setup (
credentials and password are securely stored in the encrypted
configuration file), you do not have to set up the system / call
the 'setup' method again.


**USAGE:**
    - mail = NotificationManager()
    - print(mail.ready)  # Check if fully setup, if not call setup().
    - mail.get_photo_permission()  # Let OS ask for camera permission.
    - mail.setup(
            receiver_email="send@to.me",
            sender_email="example@mail.org",
            password="strongPassword",
            name="John Doe",
            server="smtp.mail.org",
            port=587,
            enabled=True)
    - mail.prepare("Kingston 64GB", "inserted", "USB")
    - C.cfg.CFG["take_photo"] = True  # Enable photo taking (optional).
    - mail.send()

"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-02-25"
__status__ = "Prototype/Development/Production"

# Imports.
import logging
import smtplib
import ssl
import socket
import time

import certifi
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
import traceback
import string
from pathlib import Path

from PySide6.QtCore import QThread

from swiftguard.constants import C
from swiftguard.init import exceptions as exc, models
from swiftguard.utils import camera, helpers

# Child logger.
LOGGER = logging.getLogger(__name__)


class NotificationManager(metaclass=models.Singleton):
    """
    Manager for sending E-Mail notifications to the receiver(s) if a
    manipulation is detected. It sends an HTML and a plain text
    alternative E-Mail to the receiver(s) with detailed information
    about the manipulation and the system. If enabled it takes a photo
    of the potential attacker and attaches it to the E-Mail (only HTML
    E-Mail supported). If the system is once fully setup (credentials
    and password are securely stored in the system's keyring and the
    encrypted configuration file), you do not have to set up the
    system / call the 'setup' method again.
    """

    def __init__(self) -> None:
        """
        Initialize the notification manager. Check if the E-Mail
        notification system is fully setup and ready to use.
        If attribute 'ready' is False, the E-Mail notification system
        is not fully setup and cannot be used until the 'setup' method
        is called.

        :return: None
        """

        # Init E-Mail configuration.
        self._email_subject = None
        self._email_text = None
        self._email_html = None
        self._email_fallback = (
                "Manipulation detected, but failed to create E-Mail! "
                "Please check the log file for more information. "
                "Sorry for the inconvenience. Details about the "
                "manipulation: ")
        self._email_test = (
                "This is a test E-Mail from swiftGuard to check if the "
                "notification system is working properly. "
                "If you received this E-Mail, everything is working fine.")
        self._email_test_subject = "swiftGuard: E-Mail Connection Test"

        # Init CameraManager if taking photos is enabled.
        self._camera_manager = None
        if C.cfg.CFG["take_photo"]:
            try:
                self._camera_manager = camera.CameraManager()
            except exc.NotificationSetupCameraError as e:
                LOGGER.error(
                        "Failed to setup CameraManager for taking photos. "
                        f"Error: {e.__class__.__name__}: {e}"
                        )
                self._camera_manager = None

        if self.ready:
            LOGGER.info("E-Mail notification is fully setup.")

    @property
    def ready_camera(self) -> bool:
        """
        Check if the CameraManager is fully setup and ready to use.

        :return: True if the CameraManager is fully setup and ready,
            otherwise False.
        :rtype: bool
        """

        if self._camera_manager is None:
            LOGGER.error("CameraManager is not set up for taking photos.")
            return False
        elif not self._camera_manager.ready:
            LOGGER.error("CameraManager is not ready for taking photos.")
            return False

        return True

    @property
    def ready(self) -> bool:
        """
        Check if the E-Mail notification system is fully setup: E-Mail
        account credentials and password are set, available, and the
        connection to the SMTP server is possible. This excludes the
        CameraManager, which is checked separately with 'ready_camera'.

        :return: True if the E-Mail notification system is fully setup,
            otherwise False.
        :rtype: bool
        """

        if not self._check_conf():
            LOGGER.error("E-Mail notification is not fully setup.")
            return False

        if not self._check_conn():
            LOGGER.error("Could not connect to the mail server. "
                         "If your email configuration is correct, "
                         "maybe your internet connection is down."
                         )
            return False

        return True

    @property
    def ready_conf(self) -> bool:
        """
        Check if the E-Mail account credentials are set and available in
        the encrypted configuration file.

        :return: True if the E-Mail notification system is fully setup,
            otherwise False.
        :rtype: bool
        """

        return self._check_conf()

    @property
    def ready_conn(self) -> bool:
        """
        Check if the E-Mail notification connection to its configured
        SMTP server is healthy.

        :return: True if the connection to the SMTP server is healthy,
            otherwise False.
        :rtype: bool
        """

        return self._check_conn()

    @staticmethod
    def _check_conf() -> bool:
        """
        Check if the E-Mail account credentials are set and available in
        the encrypted configuration file.

        :return: True if the E-Mail notification system is fully setup,
            otherwise False.
        :rtype: bool
        """

        # Check if all necessary credentials are set and available.
        for key, value in C.cfg.CFG.config["E-Mail"].items():
            if value is None or value == "":
                LOGGER.error("E-Mail credentials are not set or available.")
                return False

        return True

    @staticmethod
    def _check_conn() -> bool:
        """
        Check if the E-Mail notification connection to its configured
        SMTP server is healthy.

        :return: True if the connection to the SMTP server is healthy,
            otherwise False.
        :rtype: bool
        """

        # Test connection to SMTP server.
        try:
            context = ssl.create_default_context(
                    cafile=certifi.where()
                    )
            if C.cfg.CFG["smtp_port"] == 465:
                server = smtplib.SMTP_SSL(
                        host=C.cfg.CFG["smtp_server"],
                        port=C.cfg.CFG["smtp_port"],
                        context=context,
                        timeout=C.email.TIMEOUT_INIT,
                        )
            else:
                server = smtplib.SMTP(
                        host=C.cfg.CFG["smtp_server"],
                        port=C.cfg.CFG["smtp_port"],
                        timeout=C.email.TIMEOUT_INIT,
                        )
                server.starttls(context=context)

            server.login(
                    user=C.cfg.CFG["smtp_email"],
                    password=C.cfg.CFG["smtp_password"]
                    )
            server.quit()

        except smtplib.SMTPAuthenticationError as e:
            LOGGER.error(f"Authentication with SMTP server failed. "
                         f"Error: {e.__class__.__name__}: {e}"
                         )
            return False

        except (smtplib.SMTPConnectError, socket.gaierror) as e:
            LOGGER.error(f"Connection to SMTP server failed. "
                         f"Error: {e.__class__.__name__}: {e}"
                         )
            return False

        except Exception as e:
            LOGGER.error(
                    f"Unexpected error occurred with SMTP server. "
                    f"Error: {e.__class__.__name__}: {e}"
                    )
            return False

        return True

    # def get_photo_permission(self):
    #     """
    #     Get the permission to take a photo of the potential attacker
    #     and attach it to the E-Mail. This method needs to be called once
    #     before sending an E-Mail with a photo attached.
    #
    #     :return: True if the permission is granted, otherwise False.
    #     :rtype: bool
    #     """
    #
    #     try:
    #         C.email.PHOTO_FILE.parent.mkdir(parents=True, exist_ok=True)
    #         test_file = C.email.PHOTO_FILE.parent / "test_permissions.jpg"
    #
    #         self._camera_manager.take_photo(save_to=test_file)
    #
    #         if self._camera_manager.photo_file.exists():
    #             self._camera_manager.photo_file.unlink()
    #             LOGGER.info(f"Permissions to take photo granted. Test photo "
    #                         f"was successfully captured and deleted."
    #                         )
    #         else:
    #             raise exc.NotificationTakePhotoError(
    #                     f"Could not take test photo to check permissions!"
    #                     )
    #
    #     except Exception as e:
    #         raise exc.NotificationTakePhotoError(
    #                 "Could not take test photo to check permissions! \n"
    #                 f"Exception: {e.__class__.__name__}: {e} \n"
    #                 f"{traceback.format_exc()}"
    #                 )

    def _insert_photo(self, photo: Path) -> None:
        """
        Convert the photo to base64 and insert it into the HTML
        template.

        :param photo: Path to the photo.
        :type photo: Path
        :raise NotificationTakePhotoError: If the photo was not found.
        :return: None
        """

        # Ensure the photo was saved as opening the file can hang.
        if not self._camera_manager.photo_file.exists():
            QThread.msleep(250)
            for _ in range(2):
                if not self._camera_manager.photo_file.exists():
                    QThread.msleep(250)
                else:
                    break

            if not self._camera_manager.photo_file.exists():
                raise exc.NotificationTakePhotoError(
                        "Failed to insert the photo into the E-Mail, as the "
                        "file was not found."
                        )

        # Encode the photo to base64, so every E-Mail client
        # can display it.
        with open(file=photo, mode="rb") as photo_file:
            photo_encoded = base64.b64encode(
                    photo_file.read()
                    ).decode()

        # The HTML snippet to insert into the HTML template.
        photo_html = f"""
               <div class="image-container">
                   <img src="data:image/jpeg;base64,{photo_encoded}"
                       alt="Picture of the potential attacker.
                       If you see no picture, use another E-Mail client 
                       which supports base64-encoded images (e.g 
                       Thunderbird).">
               </div>"""

        # Replace the placeholder in the HTML template with
        # the base64 encoded photo.
        self._email_html = self._email_html.replace(
                "<!-- INSERT IMAGE HERE -->",
                photo_html,
                )

    def setup(
            self,
            receiver_email: str | list[str],
            sender_email: str,
            password: str,
            name: str,
            server: str,
            port: int | str,
            enabled: bool = True,
            ) -> None:
        """
        Save the E-Mail password and the other credentials to the
        encrypted configuration file. This method has to be called
        before the E-Mail notification system can be used, except
        it was sometime called before and the credentials are still
        available.

        :param receiver_email: E-Mail address(es) of the receiver(s).
        :type receiver_email: str | list[str]
        :param sender_email: E-Mail address of the sender.
        :type sender_email: str
        :param password: Password of the sender's E-Mail account.
        :type password: str
        :param name: Name of the receiver (only one name supported).
        :type name: str
        :param server: SMTP server of the sender's E-Mail account (e.g.
            smtp.mail.de).
        :type server: str
        :param port: Port of the SMTP server (SSL=456 or TLS=587).
        :type port: int | str
        :param enabled: If True, the E-Mail notification system is
            enabled, otherwise not (default: True).
        :type enabled: bool
        :raise NotificationSetupError: If the credentials could not be
            saved, the setup failed due to no internet connection or
            CameraManager could not be setup (if set to take photos).
        :return: None
        """

        try:
            # Save all credentials to encrypted config file.
            C.cfg.CFG["email_enabled"] = bool(enabled)
            C.cfg.CFG["receiver_name"] = str(name)
            C.cfg.CFG["receiver_email"] = str(receiver_email)
            C.cfg.CFG["smtp_email"] = str(sender_email)
            C.cfg.CFG["smtp_password"] = str(password)
            C.cfg.CFG["smtp_server"] = str(server)
            C.cfg.CFG["smtp_port"] = int(port)

        except Exception as e:
            raise exc.NotificationSetupError(
                    f"Failed to save E-Mail credentials. Error: "
                    f"{e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )

        # Set up the camera manager if taking photos is enabled.
        if C.cfg.CFG["take_photo"]:
            try:
                self._camera_manager = camera.CameraManager()

            except exc.NotificationSetupCameraError as e:
                raise exc.NotificationSetupError(
                        f"Failed to setup CameraManager for taking photos. "
                        f"Error: {e.__class__.__name__}: {e} \n"
                        f"{traceback.format_exc()}"
                        )

        # Check the health of the SMTP connection and system in general.
        if not self.ready:
            raise exc.NotificationSetupError(
                    "Failed to setup NotificationManager, maybe no "
                    "internet connection? Please check the credentials and "
                    "try again."
                    )

    def prepare_test(self) -> None:
        """
        Prepare a test E-Mail to send to the receiver(s).

        :return: None
        """

        self._email_subject = self._email_test_subject
        self._email_html = self._email_test
        self._email_text = self._email_test

    def prepare(
            self,
            device: str,
            device_action: str,
            device_interface: str,
            ) -> None:
        """
        Prepare the E-Mail template with the given information.
        If the E-Mail template files are not available, a fallback
        plain text is used.

        :param device: Name of the device (e.g. 'Kingston 64GB').
        :type device: str
        :param device_action: Action performed on the device (e.g.
            'inserted' or 'removed').
        :type device_action: str
        :param device_interface: Interface of the device (e.g. 'USB').
        :type device_interface: str
        :return: None
        """

        try:
            # Get current date and time nicely formatted.
            current_dt = datetime.now()
            current_date = current_dt.strftime("%Y-%m-%d")
            current_time = (f"{current_dt.strftime('%H:%M:%S')} "
                            f"{current_dt.astimezone().tzname()}")

            # Get currently connected Wi-Fi SSID.
            wifi_ssid = helpers.current_wifi()

            # Read the E-Mail template files (text and html).
            for file in (C.email.TEMPLATE_TEXT, C.email.TEMPLATE_HTML):
                with open(file, "r") as fh:
                    template = string.Template(fh.read())

                    # Fill in the template.
                    email = template.safe_substitute(
                            info_name=C.cfg.CFG["receiver_name"][:50],
                            info_interface=device_interface,
                            info_action=device_action,
                            info_date=current_date,
                            info_time=current_time,
                            info_device=device,
                            info_counter_measure=C.cfg.CFG["action"],
                            info_user=C.app.USER,
                            info_wifi=str(wifi_ssid),
                            info_system=(f"{C.app.OS} {C.app.OS_VERSION} - "
                                         f"{C.app.CPU} - {C.app.RAM} RAM"),
                            )

                    # Remove the Wi-Fi line, if we are not connected.
                    if not wifi_ssid:
                        email = "\n".join(
                                line for line in email.split("\n")
                                if not line.lstrip().startswith("WiFi:")
                                )

                if file.suffix == ".txt":
                    self._email_text = email
                else:
                    self._email_html = email

                self._email_subject = "swiftGuard: Manipulation Detected"

        except Exception as e:
            LOGGER.error(
                    "Failed to prepare the E-Mail template. "
                    "Falling back to plain text E-Mail. "
                    f"Error: {e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )

            last_fallback = (f"{self._email_fallback}Interface:"
                             f" {device_interface}, Device: {device}, "
                             f"Action: {device_action}.")
            self._email_text = last_fallback
            self._email_html = last_fallback

    def send(self, timeout: int = C.email.TIMEOUT_SEND) -> None:
        """
        Send the prepared E-Mail to the receiver(s). If the feature is
        enabled, a photo is taken before action and attached to the
        E-Mail.

        :param timeout: Timeout for the SMTP connection (default: 2).
        :type timeout: int
        :raise NotificationSendError: If the E-Mail could not be sent.
        :return: None
        """

        if not self.ready:
            raise exc.NotificationSendError(
                    "E-Mail notification system is not fully setup!"
                    )

        # Take a photo before sending E-Mail if feature is enabled, and
        # we are not sending a test E-Mail.
        if (C.cfg.CFG["take_photo"]
                and hasattr(self, "_camera_manager")
                and self._camera_manager is not None
                and self.ready_camera
                and self._email_subject != self._email_test_subject):
            try:
                self._camera_manager.take_photo()
                self._insert_photo(photo=self._camera_manager.photo_file)

            except Exception as e:
                LOGGER.error(
                        "Falling back to sending E-Mail without photo. "
                        f"Error: {e.__class__.__name__}: {e} \n"
                        f"{traceback.format_exc()}"
                        )

        # Configure message.
        message = MIMEMultipart("mixed")
        message["Subject"] = self._email_subject
        message["From"] = C.cfg.CFG["smtp_email"]
        if isinstance(C.cfg.CFG["receiver_email"], str):
            message["To"] = C.cfg.CFG["receiver_email"]
        elif len(C.cfg.CFG["receiver_email"]) == 1:
            message["To"] = C.cfg.CFG["receiver_email"][0]
        else:
            message["To"] = ", ".join(C.cfg.CFG["receiver_email"]
                                      )

        # Turn the messages into plain/html MIMEText objects and add
        # them to the MIMEMultipart message.
        body = MIMEMultipart("alternative")
        body.attach(MIMEText(self._email_text, "plain"))
        body.attach(MIMEText(self._email_html, "html"))
        message.attach(body)

        # Secure connection to server and send email with short timeout.
        try:
            # SSL connection (port 465).
            if C.cfg.CFG["smtp_port"] == 465:
                context = ssl.create_default_context(cafile=certifi.where())
                with smtplib.SMTP_SSL(
                        host=C.cfg.CFG["smtp_server"],
                        port=465,
                        context=context,
                        timeout=timeout,
                        ) as server:
                    server.login(user=C.cfg.CFG["smtp_email"],
                                 password=C.cfg.CFG["smtp_password"],
                                 )
                    server.sendmail(
                            C.cfg.CFG["smtp_email"],
                            C.cfg.CFG["receiver_email"],
                            message.as_string(),
                            )

            # TLS connection (STARTTLS, port 587).
            else:
                context = ssl.create_default_context(cafile=certifi.where())
                with smtplib.SMTP(host=C.cfg.CFG["smtp_server"],
                                  port=587,
                                  timeout=timeout,
                                  ) as server:
                    server.starttls(context=context)
                    server.login(user=C.cfg.CFG["smtp_email"],
                                 password=C.cfg.CFG["smtp_password"],
                                 )
                    server.sendmail(
                            C.cfg.CFG["smtp_email"],
                            C.cfg.CFG["receiver_email"],
                            message.as_string(),
                            )

            LOGGER.info(
                    "Successfully sent E-Mail notification to "
                    f"'{C.cfg.CFG['receiver_email']}'."
                    )

        except Exception as e:
            raise exc.NotificationSendError(
                    "Could NOT send E-Mail notification to "
                    f"'{C.cfg.CFG['receiver_email']}'. "
                    f"Error: {e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    qapp = QApplication([])

    mail = NotificationManager()
    mail.setup(
            receiver_email="lennart-haack@mail.de",
            sender_email="lennart-haack@mail.de",
            password="3Lxm+LjDH?jzh!iLh387&?",
            name="Lennart",
            server="smtp.mail.de",
            port=587,
            enabled=True,
            )

    start_time = time.perf_counter()

    print("READY:", mail.ready)

    print("Time took for setup:", time.perf_counter() - start_time)

#  mail.prepare("USB", "inserted", "USB", )

# C.cfg.CFG["take_photo"] = True
# mail.send()
