#!/usr/bin/env python3

"""
tray.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2024.3"
__date__ = "2024-03-04"
__status__ = "Prototype/Development/Production"

from functools import partial

# Imports.
from PySide6 import QtGui
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import Signal

from swiftguard.assets import resources_rc  # noqa: F401
from swiftguard.constants import C
from swiftguard.init import exceptions as exc


class SwiftGuardTray(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.app = QApplication.instance()
        self.setToolTip(f"swiftGuard v{__version__} ({__build__})")

        # Set the app icon.
        icon = QtGui.QIcon(QtGui.QIcon(":/assets/icns/tray.png"))

        icon.setIsMask(True)  # Dark mode fix for macOS.
        self.setIcon(icon)

        return

        self.menu = QMenu(parent)

        menu_usb = QAction("USB", self.menu)
        self.menu.addAction(menu_usb)
        menu_usb.triggered.connect(partial(self.guarding, "USB"))

        menu_bt = QAction("Bluetooth", self.menu)
        self.menu.addAction(menu_bt)
        menu_bt.triggered.connect(partial(self.guarding, "Bluetooth"))

        menu_net = QAction("Network", self.menu)
        self.menu.addAction(menu_net)
        menu_net.triggered.connect(partial(self.guarding, "Network"))

        menu_test2 = QAction("Defuse", self.menu)
        self.menu.addAction(menu_test2)
        menu_test2.triggered.connect(self.test2_defuse)

        menu_exit = QAction("Exit", self.menu)
        self.menu.addAction(menu_exit)
        menu_exit.triggered.connect(exc.exit_handler)

        self.setContextMenu(self.menu)

        print("conf", C.cfg.CFG["usb_enabled"], C.cfg.CFG["bluetooth_enabled"],
              C.cfg.CFG["network_enabled"]
              )

        # Start guarding the interfaces.
        self.app.workers_toggle()

    def test_hotkey(self):
        print("test hotkey ...")

        self.app.hotkey_manager.change(1, [256, 512])  # Cmd + Shift + S

    def guarding(self, interface):
        # Toggle the setting in the configuration.
        before = C.cfg.CFG[f"{interface.lower()}_enabled"]
        C.cfg.CFG[f"{interface.lower()}_enabled"] = not before

        # Toggle the worker corresponding to the interface settings.
        self.app.workers_toggle()

    def test2_defuse(self):
        self.app.defuse()

    # def on_activated(self, reason):
    #     if reason == QSystemTrayIcon.Trigger:
    #         # Fügen Sie hier den Code ein, der ausgeführt werden soll,
    #         # wenn auf das Tray-Icon geklickt wird.
    #         print("on activated ...")
