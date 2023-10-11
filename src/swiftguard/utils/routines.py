#!/usr/bin/env python3

"""
routines.py: TODO: Headline...

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
from PySide6.QtCore import QThread, QTimer


class Listener:
    def __init__(self, name, callback, intervall=1000):
        self.name = name
        self.callback = callback
        self.intervall = intervall
        self.thread = None
        self.timer = None
        print(f"DEBUG: Listener{self.name} initialized!")

    def start(self):
        self.thread = QThread()
        self.timer = QTimer(interval=self.intervall)
        self.timer.timeout.connect(self.callback)
        self.timer.moveToThread(self.thread)
        self.thread.started.connect(self.timer.start)
        self.thread.finished.connect(self.timer.stop)
        self.thread.start()
        print(f"DEBUG: Listener{self.name} started!")

    def stop(self):
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        print(f"DEBUG: Listener{self.name} stopped!")


# TODO: auch für update checking implementieren? intervall von 24h oder
#  anhand von datetime oder runtime der app?
