#!/usr/bin/env python3

"""
listeners.py: TODO: Headline...

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
from ast import literal_eval
from collections import Counter

from PySide6.QtCore import QCoreApplication, QObject, QThread, QTimer, Signal

from swiftguard.utils import helpers

# Child logger.
LOGGER = logging.getLogger(__name__)


class Listeners(QObject):
    # Signal for sending signals and data to the main thread.
    triggered = Signal()
    triggered_data = Signal(object)

    # Instance-wide config.
    config = None

    def __init__(self, intervall=1000):
        super().__init__()
        self.intervall = intervall
        self.timer = None

    def start(self):
        self.timer = QTimer(interval=self.intervall)
        self.timer.timeout.connect(self.listen)
        self.timer.start()

        # Check if the listener is executed in a separate thread.
        if QThread.currentThread() is QCoreApplication.instance().thread():
            raise RuntimeError("Listener is running in the main thread!")

        LOGGER.debug("Listener is running in a separate thread.")

    def stop(self):
        self.timer.stop()
        self.timer.deleteLater()

    def listen(self):
        raise NotImplementedError


class ListenerUSB(Listeners):
    def __init__(self):
        super().__init__()

        self.start_connect_count = None
        self.start_allow_count = None

    def listen(self):
        # Get the current devices and their exact count.
        current_connect = helpers.usb_devices()
        current_connect_count = Counter(current_connect)

        # Get the allowed devices and their exact count.
        current_allow = literal_eval(
            "[" + self.config["Whitelist"]["usb"] + "]"
        )
        current_allow_count = Counter(current_allow)

        # If the count of currently connected devices is the same as
        # before, and the count of allowed devices is the same as
        # before, there is no need to update the device menu.
        if (
            self.start_connect_count == current_connect_count
            and self.start_allow_count == current_allow_count
        ):
            print("KEIN menu update nötig")
            return

        print("menu update NÖTIG")

        # Update the start connected and allowed devices count, for next
        # function call/iteration.
        self.start_connect_count = current_connect_count
        self.start_allow_count = current_allow_count

        # Emit signal to main thread to update the device menu with
        # passed device and whitelist data.
        self.triggered.emit()


# TODO: auch für update checking implementieren? intervall von 24h oder
#  anhand von datetime oder runtime der app? QDate.currentDate()?
