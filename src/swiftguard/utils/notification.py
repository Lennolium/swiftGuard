#!/usr/bin/env python3

"""
mail.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2023-10-17"
__status__ = "Prototype/Development/Production"

# Imports.
import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from swiftguard import const

# Child logger.
LOGGER = logging.getLogger(__name__)


class NotificationMail:
    def __init__(self, sender_email, receiver_email, password, host, name):
        # Init E-Mail configuration.
        self.sender_email = sender_email
        self.receiver_email = receiver_email
        self.password = password
        self.host = host
        self.name = name

        # Init system information.
        self.info_date = None
        self.info_time = None
        self.info_user = None
        self.info_system = None

        # Configure message.
        self.message = MIMEMultipart("alternative")
        self.message["Subject"] = "SWIFTGUARD: Manipulation Detected"
        self.message["From"] = self.sender_email
        self.message["To"] = self.receiver_email

    def update_sys_info(self):
        # Get detailed system Information.
        self.info_date = datetime.now().strftime("%Y-%m-%d")
        self.info_time = datetime.now().strftime("%H:%M:%S")
        self.info_user = const.SYSTEM_INFO[2]
        self.info_system = (
            f"{const.SYSTEM_INFO[0]}"
            f" {const.SYSTEM_INFO[1]}"
            f" - {const.SYSTEM_INFO[4]}"
            f" - {const.SYSTEM_INFO[5]} RAM"
        )

    def create_text(self, info_device, info_action, info_counter_measure):
        # Plain-text email.
        text = f"""\
        Dear {self.name}
        I am writing to inform you that swiftGuard has detected a manipulation
        of the USB interface on your system. An unauthorized device has been 
        disconnected/newly connected. This could potentially indicate an attempt to 
        access or tamper with your system.
        
        Detailed Information:
        _______________________________________________
        Date: {self.info_date}
        Time: {self.info_time}
        Device: {info_device}
        Action: {info_action}
        Counter-Measure: {info_counter_measure}
        User: {self.info_user}
        System: {self.info_system}
        _______________________________________________
        
        If you believe this modification was legitimate, or you are aware of the 
        changes, please disregard this message. However, if you suspect any 
        unauthorized activity, I recommend taking immediate action to secure
        your system and investigate further. 
        
        Should you require any assistance or have any questions, please do not 
        hesitate reach out to me further guidance and assistance: 
        lennart-haack@mail.de
        
        Thank you for using swiftGuard to help secure your system.</p>
        
        Best Regards,
        Lennart Haack
        Developer
        """

        return text

    def create_html(self, info_device, info_action, info_counter_measure):
        # HTML email.
        html = f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    background-color: #f2f2f2;
                    color: #333333;
                    margin: 30px 0;
                }}
        
                .email-container {{
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 20px;
                    max-width: 90%;
                    text-align: left;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }}
        
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
        
                .content {{
                    margin-bottom: 20px;
                    line-height: 1.6;
                }}
        
                .debug-info {{
                    background-color: #f2f2f2;
                    padding: 20px;
                    margin-bottom: 20px;
                    border: 1px solid #e6e6e6;
                    border-radius: 5px;
                    font-family: monospace;
                }}
        
                .signature {{
                    margin-top: 20px;
                }}
        
                .github-link {{
                    text-align: center;
                    margin-top: 20px;
                }}
        
                .disclaimer {{
                    text-align: center;
                    margin-top: 50px;
                }}
        
                @media only screen and (max-width: 600px) {{
                    .email-container {{
                        border-radius: 0;
                    }}
                }}
        
                @media (prefers-color-scheme: dark) {{
                    body {{
                        background-color: #1a1a1a;
                        color: #e6e6e6;
                    }}
        
                    .email-container {{
                        background-color: #2a2a2a;
                        box-shadow: 0 4px 8px rgba(255, 255, 255, 0.1);
                    }}
        
                    .debug-info {{
                        background-color: #1a1a1a;
                        border: 1px solid #333333;
                    }}
                }}
            </style>
            <title>swiftGuard</title>
        </head>
        
        <body>
        <div class="email-container">
            <div class="header">
                <picture>
                    <source srcset="https://raw.githubusercontent.com/Lennolium/swiftGuard/main/img/banner/banner_dark.png"
                            media="(prefers-color-scheme: dark)" style="width: 100%; max-width: 500px;">
                    <img src="https://raw.githubusercontent.com/Lennolium/swiftGuard/main/img/banner/banner_light.png"
                         alt="swiftGuard banner" style="width: 100%; max-width: 500px;">
                </picture>
            </div>
            <div class="content">
                <h2>ALERT: Manipulation Detected</h2>
                <p>Dear {self.name},</p>
                <p>I am writing to inform you that swiftGuard has
                    detected a manipulation
                    of the USB interface on your
                    system.
                    An unauthorized <strong>device has been disconnected/newly connected</strong>. This could
                    potentially indicate an attempt to access or tamper with your system.
                </p>
            </div>
            <div class="debug-info">
                <p><strong>Detailed Information:</strong></p>
                <p style="font-family: monospace;">Date: {self.info_date}</p>
                <p style="font-family: monospace;">Time: {self.info_time}</p>
                <p style="font-family: monospace;">Device: {info_device}</p>
                <p style="font-family: monospace;">Action: {info_action}</p>
                <p style="font-family: monospace;">Counter-Measure: 
                {info_counter_measure}</p>
                <p style="font-family: monospace;">User: {self.info_user}</p>
                <p style="font-family: monospace;">System: 
                {self.info_system}</p>
            </div>
            <div class="content">
                <p>If you believe this modification was legitimate, or you are aware of the changes, please disregard this
                    message. However, if you suspect any unauthorized activity, 
                    I recommend taking immediate action to secure
                    your system and investigate further.</p>
                <p>Should you require any assistance or have any questions, please do not hesitate to <a
                        href="mailto:lennart-haack@mail.de?subject=swiftGuard%3A%20I%20need%20assistance&body=Dear%20Lennart%2C%0A%0AI'm%20using%20your%20application%20'swiftGuard'%2C%20but%20I%20did%20run%20into%20some%20problems%20and%20I%20need%20assistance%20with%20the%20following%3A"
                        style="text-decoration: none; color: #007bff;">reach out to me</a> for
                    further guidance and assistance.</p>
                <p>Thank you for using swiftGuard to help secure your system.</p>
                <p class="signature">Best Regards,<br>Lennart Haack<br><small>Developer</small></p>
            </div>
            <div class="github-link">
                <a href="https://github.com/Lennolium/swiftGuard"
                   style="text-decoration: none; color: #007bff;">Check out on GitHub</a>
            </div>
            <div class="disclaimer">
                <a style="text-decoration: none; color: #cccccc; font-size: 13px">This email has been sent from your account as
                    configured in the swiftGuard app on your Mac. You have enabled this notification feature within the
                    settings of swiftGuard. If you wish to stop receiving these emails, simply remove the email account from
                    the settings menu.
                </a>
            </div>
        </div>
        
        <script>
            const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");
            if (prefersDarkScheme.matches) {{
                document.body.style.backgroundColor = "#1a1a1a";
                document.body.style.color = "#e6e6e6";
                document.querySelector('.email-container').style.backgroundColor = "#2a2a2a";
                document.querySelector('.debug-info').style.backgroundColor = "#1a1a1a";
                document.querySelector('.debug-info').style.border = "1px solid #333333";
            }}
        </script>
        </body>
        </html>
        """

        return html

    def send(self, device, action, counter_measure):
        # Update system information.
        self.update_sys_info()

        text = self.create_text(device, action, counter_measure)
        html = self.create_html()

        # Turn the messages into plain/html MIMEText objects.
        text_part = MIMEText(text, "plain")
        html_part = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message.
        self.message.attach(text_part)
        self.message.attach(html_part)

        # Create secure connection with server and send email. We set a
        # very short timeout, because we don't want to wait for an SMTP
        # server timeout if the user is offline.
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                self.host, 465, context=context, timeout=1
            ) as server:
                server.login(self.sender_email, self.password)
                server.sendmail(
                    self.sender_email,
                    self.receiver_email,
                    self.message.as_string(),
                )

        # Do not raise exception, because it would stop the execution of
        # the main program.
        except Exception as e:
            LOGGER.error(f"Failed to send E-Mail. Error: {str(e)}")
            print("error", e)
