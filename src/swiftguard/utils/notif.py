#!/usr/bin/env python3

"""
notif.py: TODO: Headline...

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
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

import keyring as kr
import keyring.errors

from swiftguard import const
from swiftguard.utils import conf

# Child logger.
LOGGER = logging.getLogger(__name__)


class NotificationMail:
    def __init__(self, config):
        self.config = config

        # Init E-Mail configuration.
        self.sender_email = None
        self.receiver_email = None
        self.password = None
        self.host = None
        self.port = None
        self.name = None

        # Init system information.
        self.info_date = None
        self.info_time = None
        self.info_user = None
        self.info_system = None

    def set_credentials(self, email, password, host, name, port):
        # If credentials already exist, delete the old object.
        try:
            if kr.get_credential("swiftGuard-mail", email):
                kr.delete_password("swiftGuard-mail", email)

        except keyring.errors.KeyringError:
            pass

        try:
            # Save password in system's keyring of the current user.
            kr.set_password(
                    "swiftGuard-mail",
                    email,
                    password,
                    )

            # Save credentials in config file.
            self.config["Email"]["enabled"] = "1"
            self.config["Email"]["name"] = name
            self.config["Email"]["email"] = email
            self.config["Email"]["smtp"] = host
            self.config["Email"]["port"] = port

            self.config = conf.validate(self.config)
            conf.write(self.config)

            return True

        except Exception as e:
            LOGGER.error(f"Failed to save E-Mail credentials. Error: {str(e)}")
            return False

    def get_credentials(self):
        # Get credentials from system's keyring of the current user.
        try:
            pw = kr.get_password(
                    "swiftGuard-mail", self.config["Email"]["email"]
                    )

        except Exception as e:
            LOGGER.error(
                    "Failed to get E-Mail credentials from keyring. "
                    f"Error: {str(e)}"
                    )
            self.config["Email"]["enabled"] = "0"
            conf.write(self.config)
            return False

        if not pw:
            LOGGER.error("No saved E-Mail credentials found.")
            self.config["Email"]["enabled"] = "0"
            conf.write(self.config)
            return False

        # We get the email account password from the keyring object.
        self.password = pw

        # And the other stuff from the config file.
        self.sender_email = self.config["Email"]["email"]
        self.receiver_email = self.config["Email"]["email"]
        self.name = self.config["Email"]["name"]
        self.host = self.config["Email"]["smtp"]
        self.port = self.config["Email"]["port"]

        return True

    def update_sys_info(self):
        # Get detailed system Information.
        self.info_date = datetime.now().strftime("%Y-%m-%d")
        self.info_time = (f"{datetime.now().strftime('%H:%M:%S')} "
                          f"{datetime.now().astimezone().tzname()}")
        self.info_user = const.SYSTEM_INFO[2]
        self.info_system = (
                f"{const.SYSTEM_INFO[0]}"
                f" {const.SYSTEM_INFO[1]}"
                f" - {const.SYSTEM_INFO[4]}"
                f" - {const.SYSTEM_INFO[5]} RAM"
        )

    def create_emails(
            self, info_device, info_action, info_counter_measure, interface
            ):
        # Plain-text and html email templates paths.
        templates = [
                f"{const.APP_PATH}/resources/mail-template.txt",
                f"{const.APP_PATH}/resources/mail-template.html",
                ]

        emails = []

        for template in templates:
            with open(template, "r") as fh:
                read = fh.read()

                temp = Template(read)

                # Fill in the template.
                email = temp.substitute(
                        info_name=self.name,
                        info_interface=interface,
                        info_action=info_action,
                        info_date=self.info_date,
                        info_time=self.info_time,
                        info_device=info_device,
                        info_counter_measure=info_counter_measure,
                        info_user=self.info_user,
                        info_system=self.info_system,
                        )

                emails.append(email)

        return emails

    def send(self, device, action, counter_measure, interface):
        # Update system information.
        self.update_sys_info()

        # Get the email credentials.
        self.get_credentials()

        # Configure message.
        message = MIMEMultipart("alternative")
        message["Subject"] = "swiftGuard: Manipulation Detected"
        message["From"] = self.sender_email
        message["To"] = self.receiver_email

        try:
            text, html = self.create_emails(
                    device, action, counter_measure, interface
                    )
        except Exception as e:
            LOGGER.error(
                    f"Failed to create E-Mail. Sending fallback E-Mail. "
                    f"Error: {str(e)}"
                    )
            text = (
                    "Manipulation Detected, but failed to create E-Mail. "
                    "Please check the log file for more information. "
                    f"Error: {str(e)}"
            )
            html = text

        # Turn the messages into plain/html MIMEText objects.
        text_part = MIMEText(text, "plain")
        html_part = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message.
        message.attach(text_part)
        message.attach(html_part)

        # Create secure connection with server and send email. We set a
        # very short timeout, because we don't want to wait for an SMTP
        # server timeout if the user is offline.
        # SSL connection.
        try:
            if self.port == "465":
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                        self.host, 465, context=context, timeout=1
                        ) as server:
                    server.login(self.sender_email, self.password)
                    server.sendmail(
                            self.sender_email,
                            self.receiver_email,
                            message.as_string(),
                            )

            # TLS connection.
            elif self.port == "587":
                context = ssl.create_default_context()
                with smtplib.SMTP(self.host, 587, timeout=1) as server:
                    server.starttls(context=context)
                    server.login(self.sender_email, self.password)
                    server.sendmail(
                            self.sender_email,
                            self.receiver_email,
                            message.as_string(),
                            )

            LOGGER.info(
                    "Successfully sent E-Mail notification to "
                    f"{self.receiver_email}."
                    )

        except Exception as e:
            LOGGER.error(
                    "Could NOT send E-Mail notification to "
                    f"{self.receiver_email}. Error: {str(e)}"
                    )
