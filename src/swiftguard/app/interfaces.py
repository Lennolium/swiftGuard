#!/usr/bin/env python3

"""
interfaces.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-05-21"
__status__ = "Prototype/Development/Production"

# Imports.
from PySide6.QtCore import (QObject, QParallelAnimationGroup,
                            QPropertyAnimation, QEasingCurve, QRect, QSize,
                            QTimer, Qt, Slot)
from PySide6.QtGui import QCursor, QFont, QIcon
from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow

from swiftguard.app import supp
from swiftguard.constants import C
from swiftguard.ui.window_ui import Ui_MainWindow
from swiftguard.core.devices import USB, Bluetooth, Network


class Interface(QObject):

    def __init__(
            self,
            ui: Ui_MainWindow,
            name: str,
            theme: str | None,
            ) -> None:
        """
        Initialize the interface object.

        :param ui: The main window UI object.
        :type ui: Ui_MainWindow
        :param name: Name of interface ('usb', 'bluetooth', 'network').
        :type name: str
        :param theme: current theme of application ('dark' or 'light').
        :type theme: str
        """

        super().__init__()

        # General.
        self.ui = ui
        self.theme = theme
        self.name = name
        self.app = QApplication.instance()
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMainWindow):
                self.main_window = widget
                break

        # Worker.
        self.worker = getattr(self.app, f"worker_{self.name}")

        # Allowed dropdown menu.
        self._dd_frm = getattr(self.ui, f"{self.name}_dropdown")
        self._dd_btn = getattr(self.ui, f"{self.name}_allowed")
        self._dd_anim = QPropertyAnimation(
                self._dd_frm,
                b"maximumHeight",
                self.ui.centralwidget
                )
        self._dd_anim.setDuration(350)
        self._dd_anim.setEasingCurve(QEasingCurve.OutCirc)
        self._dd_anim.finished.connect(lambda: self._dd_btn.setEnabled(True))

        # Main window animation.
        self._main_window_anim = QPropertyAnimation(
                self.main_window,
                b"geometry"
                )
        self._main_window_anim.setEasingCurve(QEasingCurve.OutCirc)
        self._main_window_anim.setDuration(350)

        self._animation_group = QParallelAnimationGroup()
        self._animation_group.addAnimation(self._dd_anim)
        self._animation_group.addAnimation(self._main_window_anim)

        # Button state (Guarding/Inactive).
        self._st_widget = getattr(self.ui, f"{self.name}_button")
        self._st_btn = getattr(self.ui, f"{self.name}_state")
        self._st_count = getattr(self.ui, f"{self.name}_count")

        # Enable interface if it is enabled in the configuration.
        if C.cfg.CFG[f"{self.name}_enabled"]:
            self._st_btn.setChecked(True)
            self.toggle_state(now_checked=True)
        else:
            self._st_btn.setChecked(False)
            self.toggle_state(now_checked=False)

        # Current state of devices.
        self.displayed_devices: list = []

        self.show_whitelisted()

    def show_whitelisted(self) -> None:
        # Check for whitelisted devices.
        whitelist = C.cfg.CFG[self.name]
        if whitelist:
            for dev in whitelist:
                self.add_device(dev, whitelisted=True)
                self.displayed_devices.append(dev)

            # If whitelisted or connected devices -> remove placeholder.
            self.toggle_placeholder(show=False)

    def toggle_placeholder(self, show: bool) -> None:
        """
        Toggle the placeholder for the allowed devices dropdown menu.

        :param show: Show or hide the placeholder.
        :type show: bool
        :return: None
        """

        placeholder_widget = self._dd_frm.findChild(
                QPushButton,
                f"{self.name}_placeholder"
                )

        if show:
            placeholder_widget.show()
        else:
            placeholder_widget.hide()

    def update_devices(self, devices: dict) -> None:

        print("DEVICES:", devices)

        # Return early if devices did not change.
        if devices[self.name.upper()] == self.displayed_devices:
            return

        # Display new connected devices.
        for dev in devices[self.name.upper()]:
            if dev not in self.displayed_devices:
                self.displayed_devices.append(dev)
                self.add_device(dev)

        # Remove devices that are not connected anymore.
        for dev in self.displayed_devices:
            if (dev not in devices[self.name.upper()]
                    and dev not in C.cfg.CFG[self.name]):
                self.displayed_devices.remove(dev)
                self.remove_device(dev)

    def remove_device(
            self,
            dev: USB | Bluetooth | Network
            ) -> None:
        """
        Remove a single device from dropdown menu of allowed devices.

        :param dev: The device object to remove.
        :type dev: USB | Bluetooth | Network
        :return: None
        """

        no = self._dd_frm.layout().count()

        for i in range(no):
            attr = self._dd_frm.layout().itemAt(i).widget()
            if attr.text().strip() == f"{dev.name}":
                attr.hide()
                attr.deleteLater()
                break

        # If no devices are left, show the placeholder.
        if not self.displayed_devices:
            self.toggle_placeholder(show=True)

        # Update the layout to accommodate the new size needed.
        QTimer.singleShot(100, self.update_dropdown_size)

    def add_device(
            self,
            dev: USB | Bluetooth | Network,
            whitelisted: bool = False,
            ) -> None:
        """
        Add a single device to the dropdown menu of allowed devices.

        :param dev: The device object to add.
        :type dev: USB | Bluetooth | Network
        :param whitelisted: Check the button, as the device is allowed.
        :type whitelisted: bool
        :return: None
        """

        no = self._dd_frm.layout().count() + 1

        # Remove placeholder if it is still visible.
        if self.displayed_devices:
            self.toggle_placeholder(show=False)

        setattr(self.ui, f"{self.name}_dev{no}",
                QPushButton(self._dd_frm)
                )
        attr = getattr(self.ui, f"{self.name}_dev{no}")

        # General appearance.
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        icon = QIcon()
        icon.addFile(u":/icns/circle.fill.gray.svg", QSize(), QIcon.Normal,
                     QIcon.Off
                     )
        icon.addFile(u":/icns/circle.fill.svg", QSize(), QIcon.Normal,
                     QIcon.On
                     )
        attr.setObjectName(f"{self.name}_dev{no}")
        attr.setMinimumSize(QSize(0, 27))
        attr.setMaximumSize(QSize(212, 27))
        attr.setFont(font)
        attr.setCursor(QCursor(Qt.PointingHandCursor))
        attr.setIcon(icon)
        attr.setIconSize(QSize(9, 9))
        attr.setCheckable(True)
        attr.setText(f" {dev.name}")  # Extra white space for padding.
        attr.setChecked(whitelisted)
        self._dd_frm.layout().addWidget(attr)

        # Update the layout to accommodate the new size needed.
        QTimer.singleShot(100, self.update_dropdown_size)

    def hover_on(self) -> None:
        """
        Hover effect for the button, but only if the state button is
        displaying the manipulation state. Displays defuse text if
        hovering over the button.

        :return: None
        """

        if self._st_btn.text() == "  MANIPULATION":
            self._st_btn.setText("  DEFUSE ALARM")
            self._st_count.setText("?")

    def hover_off(self) -> None:
        """
        Hover effect for the button (see hover_on).

        :return: None
        """

        if self._st_btn.text() == "  DEFUSE ALARM":
            self._st_btn.setText("  MANIPULATION")
            self._st_count.setText("!")

    def update_dropdown_size(self) -> None:
        """
        Update the size of the dropdown menu of allowed devices.

        :return: None
        """

        if self._dd_frm.maximumHeight() == 0:
            print("early return")
            return

        # Get the number of items in the dropdown menu (not hidden).
        no = sum(1 for i in range(self._dd_frm.layout().count()) if
                 not self._dd_frm.layout().itemAt(i).widget().isHidden()
                 )

        # Calculate the height of the dropdown menu.
        exp_height = (no * 27) + (4 * no) + 14 + 10

        # Main window size.
        main_window_start_geometry = self.main_window.geometry()
        main_window_end_geometry = QRect(main_window_start_geometry.x(),
                                         main_window_start_geometry.y(),
                                         main_window_start_geometry.width(),
                                         main_window_start_geometry.height()
                                         + exp_height
                                         )

        self._dd_anim.setStartValue(self._dd_frm.maximumHeight())
        self._dd_anim.setEndValue(exp_height)

        self._main_window_anim.setStartValue(main_window_start_geometry)
        self._main_window_anim.setEndValue(main_window_end_geometry)

        self._animation_group.start()

        print("CALLEd")

    @Slot()
    def toggle_dropdown(self) -> None:
        """
        Toggle the dropdown menu of the allowed devices for interface.

        :return: None
        """

        # Get the number of items in the dropdown menu (not hidden).
        no = sum(1 for i in range(self._dd_frm.layout().count()) if
                 not self._dd_frm.layout().itemAt(i).widget().isHidden()
                 )

        # Calculate the height of the dropdown menu.
        exp_height = (no * 27) + (4 * no) + 14 + 10

        # Main window size.
        main_window_start_geometry = self.main_window.geometry()
        main_window_end_geometry = QRect(main_window_start_geometry.x(),
                                         main_window_start_geometry.y(),
                                         main_window_start_geometry.width(),
                                         main_window_start_geometry.height()
                                         + exp_height
                                         )

        # Disable the button to prevent multiple clicks.
        self._dd_btn.setEnabled(False)

        # Expanded -> collapsed / On -> Off.
        if self._dd_frm.maximumHeight() > 0:
            self._dd_anim.setStartValue(exp_height)
            self._dd_anim.setEndValue(0)

            self._main_window_anim.setStartValue(main_window_start_geometry)
            self._main_window_anim.setEndValue(
                    QRect(main_window_start_geometry.x(),
                          main_window_start_geometry.y(),
                          main_window_start_geometry.width(),
                          main_window_start_geometry.height() - exp_height
                          )
                    )

        # Collapsed -> expanded / Off -> On.
        else:
            self._dd_anim.setStartValue(0)
            self._dd_anim.setEndValue(exp_height)

            self._main_window_anim.setStartValue(main_window_start_geometry)
            self._main_window_anim.setEndValue(main_window_end_geometry)

        self._animation_group.start()

    @Slot()
    def toggle_state(self, now_checked: bool) -> None:
        """
        Toggle the state of the interface button (Guarding/Inactive).

        :param now_checked: The current state of the button, after it
            was clicked (automatically passed by the Qt connect signal).
        :type now_checked: bool
        :return: None
        """

        # After manipulation defusing, we show the allowed button again.
        self._dd_btn.show()

        # OFF -> ON.
        if now_checked:
            self._st_btn.setText("  Guarding")

            # Change to colorful state of whole button background.
            self._st_widget.setStyleSheet(
                    supp.state_on.replace("XXX", self.name)
                    )

            # Change the color of the allowed count label.
            self._st_count.setStyleSheet(
                    supp.count_on.replace("XXX", self.name)
                    )

            # TODO: das wurde auskommentiert beim countdown testen.
            # Arm the interface.
            # self.worker.armed = True

        # ON -> OFF.
        else:
            self._st_btn.setText("  Inactive")

            # Change to gray state of whole button background.
            if self.theme == "dark":
                self._st_widget.setStyleSheet(
                        supp.state_off_dark.replace("XXX", self.name)
                        )

                self._st_count.setStyleSheet(
                        supp.count_off_dark.replace("XXX", self.name)
                        )

            else:
                self._st_widget.setStyleSheet(
                        supp.state_off.replace("XXX", self.name)
                        )

                # Allowed count label.
                self._st_count.setStyleSheet(
                        supp.count_off.replace("XXX", self.name)
                        )

            # Disarm the interface.
            self.worker.armed = False

    @Slot()
    def toggle_manipulation(
            self,
            ) -> None:
        """
        Displays the manipulation text and style for the interface
        button, if manipulation is detected. Hides the dropdown menu,
        if it is visible, so an attacker cannot add his device to the
        white list.

        :return: None
        """

        # Manipulation detected -> Alert.
        if self._st_btn.text() != "  MANIPULATION":

            # Hide the dropdown menu, if it is open.
            if self._dd_btn.isChecked():
                self._dd_btn.click()

            self._st_btn.setText("  MANIPULATION")
            self._st_btn.setMaximumWidth(180)
            self._dd_btn.hide()

            self._st_widget.setStyleSheet(
                    supp.state_manip.replace("XXX", self.name)
                    )

            self._st_count.setText("!")
            self._st_count.setStyleSheet(
                    supp.count_manip.replace("XXX", self.name)
                    )

        # Defused.
        else:
            self._dd_btn.show()
            self._st_btn.setMaximumWidth(115)

            # We reset to inactive/off state after defusing.
            self.toggle_state(now_checked=False)
            self._st_btn.setChecked(False)
