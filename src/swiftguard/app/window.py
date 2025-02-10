#!/usr/bin/env python3

"""
window.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__build__ = "2024.5"
__date__ = "2024-05-08"
__status__ = "Prototype/Development/Production"

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import (QEasingCurve, QEvent, QFile, QPropertyAnimation,
                            QTextStream, QTimer,
                            Slot)
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (QDialog, QDialogButtonBox,
                               QGraphicsColorizeEffect, QInputDialog,
                               QMenu, QMessageBox)

from swiftguard.core import devices
# Imports.
from swiftguard.ui.window_ui import *
from swiftguard.ui import dialogs
from swiftguard.init import exceptions as exc
from swiftguard.constants import C
from swiftguard.app import interfaces


class MainWindow(QMainWindow):
    """
    The MainWindow class represents the main window of the application.
    It contains all the widgets and functions for the main window. It
    also contains the functions for the animations of the main window
    and its widgets.

    :param QMainWindow: It provides a main application window.
    :type QMainWindow: class
    :return: None
    """

    def __init__(self):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the window and all of its widgets, connects buttons
        to their respective functions, and removes the title bar from
        the window.

        :param self: Refer to the current instance of a class
        :return: None
        """

        super(MainWindow, self).__init__()

        self.app = QtWidgets.QApplication.instance()

        # Create the system tray icon.
        self.tray = QtWidgets.QSystemTrayIcon()
        self.tray.setToolTip(f"swiftGuard v{__version__} ({__build__})")

        # Set the app icon.
        icon = QtGui.QIcon(QtGui.QIcon(C.res.RES["tray"]))
        icon.setIsMask(True)  # Dark mode fix for macOS.
        self.tray.setIcon(icon)

        # The window visibility is toggled when the icon gets clicked
        # and hidden when the window loses focus.
        self.tray.activated.connect(self.toggle_visibility)
        self.app.focusChanged.connect(self.focus_lost)

        self.tray.show()

        # Load the UI Window from the ui_interface.py file.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Remove window title bar and the background.
        self.setWindowFlags(
                self.windowFlags()
                | Qt.FramelessWindowHint
                # | Qt.WindowStaysOnTopHint
                )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Real-time theme changes (not needed anymore).
        self.style_hints = self.app.styleHints()
        self.style_hints.colorSchemeChanged.connect(
                lambda _: self.theme_changed()
                )
        self.theme = None
        self.theme_changed()

        self.dialog_open = False

        # Animation for the interfaces dropdowns (Allowed).
        self.inter_usb = interfaces.Interface(self.ui, "usb", self.theme)
        self.ui.usb_allowed.clicked.connect(self.inter_usb.toggle_dropdown)

        # Interfaces state buttons (Guarding/Inactive).
        self.ui.usb_state.clicked.connect(self.inter_usb.toggle_state)
        self.ui.usb_state.enterEvent = lambda _: self.inter_usb.hover_on()
        self.ui.usb_state.leaveEvent = lambda _: self.inter_usb.hover_off()

        # Hover effects for specific buttons.
        for btn_hover in (
                self.ui.exit_button,
                self.ui.help_button,
                self.ui.settings_button,):
            btn_hover.enterEvent = lambda _, button=btn_hover: self.hover_on(
                    button
                    )
            btn_hover.leaveEvent = lambda _, button=btn_hover: self.hover_off(
                    button
                    )

        # Control buttons (Exit, Help, Settings).
        self.ui.exit_button.clicked.connect(dialogs.show_exit_dialog)
        self.ui.help_button.clicked.connect(dialogs.show_about_dialog)
        # self.ui.settings_button.clicked.connect(dialogs.show_settings)
        self.ui.settings_button.clicked.connect(self.lol)

        self.devices = None
        self.devices_btns = {"USB": [], "Bluetooth": [], "Network": []}

        # TODO: remove!
        # print("WHITELIST:", C.cfg.CFG["usb"])

        self.setMaximumHeight(226)

        # Hide the dropdown menu.
        QTimer.singleShot(250, self.ui.usb_allowed.click)

        # Update quick view settings.
        self.update_quick_settings()

        # Open dialog and ask for custom countdown.
        # self.dialog_open = True
        # text, ok = QInputDialog.getText(self, "Custom",
        #                                 "Countdown in seconds:"
        #                                 )
        # self.dialog_open = False
        # if ok and text:
        #     print(ok, text)

    def lol(self):
        print("lol")

        self.app.workers_toggle()

        return

        lol = devices.USB(vendor_id="lol0", product_id="lol1",
                          serial_num="lol2",
                          name="lolomatico", manufacturer="lol4"
                          )
        self.inter_usb.add_device(lol)

    def update_quick_settings(self):
        """
        Update quick settings view with current settings from config.

        :return: None
        """

        self.ui.countdown_text.setText(f"{C.cfg.CFG['delay']} s")
        self.ui.counter_icon.setIcon(
                QtGui.QIcon(C.res.RES[self.theme][C.cfg.CFG["action"]])
                )

        # Set tooltips.
        self.ui.countdown_left_button.setToolTip("Countdown before action")
        self.ui.counter_left_button.setToolTip(
                "Action executed after a non-defused manipulation"
                )
        self.ui.counter_icon.setToolTip(C.cfg.CFG["action"])

    def hover_on(
            self,
            button: QtWidgets.QPushButton
            ) -> None:
        """
        Change the icon of the button to the hover icon. Dynamically
        changes the icon depending on the theme and the button name.

        :param button: The button that should change its icon.
        :type button: QtWidgets.QPushButton
        :return: None
        """

        # 'settings_button' -> 'settings'.
        button_name = button.objectName().split("_")[0]

        # Change icon to hover icon.
        button.setIcon(
                QtGui.QIcon(C.res.RES[self.theme][f"{button_name}-hover"])
                )

    def hover_off(
            self,
            button: QtWidgets.QPushButton
            ) -> None:
        """
        Change the icon of the button back to the default icon.

        :param button: The button that should change its icon.
        :type button: QtWidgets.QPushButton
        :return: None
        """

        button_name = button.objectName().split("_")[0]
        button.setIcon(QtGui.QIcon(C.res.RES[self.theme][button_name]))

    def theme_changed(self) -> None:
        """
        Gets called when the system theme changes. It changes the
        stylesheet of the window and updates the theme variable, which
        is used for selecting the correct icons.

        :return: None
        """

        if self.app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            theme = "dark"
        else:
            theme = "light"

        # TODO: remove
        theme = "light"

        # Early return if theme mode did not change.
        if theme == self.theme:
            return

        # Set the qss stylesheet.
        file = QFile(C.res.RES[theme]["style"])
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        self.setStyleSheet(stream.readAll())

        # Update icons and logos.
        self.ui.logo.setPixmap(QtGui.QPixmap(C.res.RES[theme]["logo-text"]))
        self.ui.exit_button.setIcon(QtGui.QIcon(C.res.RES[theme]["exit"]))
        self.ui.help_button.setIcon(QtGui.QIcon(C.res.RES[theme]["help"]))
        self.ui.settings_button.setIcon(
                QtGui.QIcon(C.res.RES[theme]["settings"])
                )

        self.theme = theme

    @property
    def devicePixelRatio(self):
        return self.devicePixelRatioF()

    @Slot("QWidget*", "QWidget*")
    def focus_lost(
            self,
            old: QtWidgets.QWidget,
            now: QtWidgets.QWidget
            ) -> None:
        """
        The focus_lost function is called when the window loses focus.
        It hides the window and removes the active window state.

        :param old: The old widget that had the focus.
        :type old: QtWidgets.QWidget
        :param now: The new widget that has the focus.
        :type now: QtWidgets.QWidget
        :return: None
        """

        if now is None and not self.dialog_open:
            self.hide()
            self.setWindowState(self.windowState() & ~Qt.WindowActive)

    def center_window(self) -> None:
        """
        Centers the window under the tray icon.

        :return: None
        """

        # Get the geometry of the tray icon and the window
        tray_geometry = self.tray.geometry()

        # Calculate the new position of the window
        x = tray_geometry.center().x() - self.size().width() / 2
        y = tray_geometry.bottom()

        self.move(x, y)

    def toggle_visibility(
            self,
            reason: QtWidgets.QSystemTrayIcon.ActivationReason
            ) -> None:
        """
        Show or hide the window when the tray icon gets clicked.

        :param reason: The trigger for icon activation.
        :type reason: QtWidgets.QSystemTrayIcon.ActivationReason
        :return: None
        """

        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                # Get the screen at the current cursor position
                screen = QApplication.screenAt(QCursor.pos())
                if screen is not None:
                    self.center_window()

                    self.show()
                    self.activateWindow()
                    self.raise_()
                    self.setFocus()
