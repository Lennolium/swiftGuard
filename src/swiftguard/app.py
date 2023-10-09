#!/usr/bin/env python3

"""
swiftguard.py: Starting point of the application.

This module is responsible for starting the application and implementing
the main tray icon. The main menu is created dynamically, depending on
the current state of the application, e.g. connected or whitelisted USB
devices, current theme, etc. The menu entries from Qt are extended with
custom attributes, e.g. a function that is called when the entry is
clicked, to show a checkmark or other icons and states.

This application is heavily inspired and based on project << usbkill >>
by Hephaestos. Project link: https://github.com/hephaest0s/usbkill
I want to thank him and all the other great contributors of usbkill for
their great work, inspiration and help. I firmly believe in the
principles of the open source community, which call for the sharing and
enhancement of one another work. The purpose of this project is to
revive an abandoned project and to support others in learning and
comprehending the fundamentals of Python, Qt and macOS, and to develop
their own projects.

<< swiftGuard >> is licensed under GNU GPLv3. Refer to the LICENSE file:
https://github.com/Lennolium/swiftGuard/blob/main/LICENSE
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.2"
__build__ = "2023.2"
__date__ = "2023-10-09"
__status__ = "Prototype"

# Imports.
import configparser
import datetime
import signal
import sys
import webbrowser
from ast import literal_eval
from collections import Counter
from copy import deepcopy
from functools import partial

import darkdetect
from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    )

from swiftguard.const import APP_PATH
# pylint: disable=unused-import
# noinspection PyUnresolvedReferences
from swiftguard.resources import resources_rc  # noqa: F401
from swiftguard.utils.autostart import add_autostart, del_autostart
from swiftguard.utils.helpers import (
    check_updates,
    config_write,
    startup,
    usb_devices,
    )
from swiftguard.utils.log import LogCount, create_logger, set_level_dest
from swiftguard.utils.workers import Worker, Workers

# Root logger and log counter.
LOG_COUNT = LogCount()
LOGGER = create_logger(LOG_COUNT)

# Resource paths.
LIGHT = {
    "checkmark": ":/resources/light/checkmark.svg",
    "usb-connection": ":/resources/light/usb-connection.svg",
    "shield-check": ":/resources/light/shield-check.svg",
    "shield-slash": ":/resources/light/shield-slash.svg",
    "shield-tamper": ":/resources/light/shield-tamper.svg",
    "app-icon": ":/resources/light/statusbar-macos@2x.png",
    "app-logo": ":/resources/logo-macos@2x.png",
}

DARK = {
    "checkmark": ":/resources/dark/checkmark.svg",
    "usb-connection": ":/resources/dark/usb-connection.svg",
    "shield-check": ":/resources/dark/shield-check.svg",
    "shield-slash": ":/resources/dark/shield-slash.svg",
    "shield-tamper": ":/resources/dark/shield-tamper.svg",
    "app-icon": ":/resources/dark/statusbar-macos@2x.png",
    "app-logo": ":/resources/logo-macos@2x.png",
}


class CustomDialog(QDialog):
    """
    A custom QDialog class for displaying text content from a file.

    This class provides a dialog window with scrollable text content
    loaded from a specified text file. It is useful for displaying
    informational messages, help texts, or license agreements.

    :param file_path: The file path of the text file to be read.
    :param title: The title of the window.
    :param header: The text to be displayed at the top of the window.
    """

    def __init__(self, file_path, title, header=None):
        """
        The __init__ function is run as soon as an object of a class is
        instantiated.

        :param self: Represent the instance of the class
        :param file_path: Set the file path of the text file to be read
        :param title: Set the title of the window
        :param header: Set the text of the QLabel at the window top
        :return: None
        """

        # Call the __init__ function of the parent class QDialog.
        super().__init__()

        if header is None:
            header = ""

        # Close button.
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        message = QLabel(f"{header}\n\n")

        # Scroll area properties (set the scroll area to be always on).
        scroll = QScrollArea()
        widget = QWidget()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(10, 0, 10, 0)

        # Read the text file and add each line to the scroll area.
        with open(file_path, "r") as file_handle:
            for line in file_handle:
                msg = QLabel(line.strip())
                msg.setWordWrap(True)
                msg.setContentsMargins(0, 0, 0, 0)
                vbox.addWidget(msg)

        widget.setLayout(vbox)

        # Scroll Area Properties
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll.setWidgetResizable(False)
        scroll.setWidget(widget)

        layout.addWidget(message)
        layout.addWidget(scroll)
        layout.addWidget(btn_box)
        self.setLayout(layout)

        self.setGeometry(300, 200, 700, 500)
        self.setWindowTitle(title)


class ToggleEntry:
    """
    Represents a menu entry with a toggle function that can switch
    between different states.

    :param function: function to be called when the entry is toggled.
    :type function: callable
    :param states: A list of two states that the entry can have.
    :type states: list
    :param icon: The icon for the entry.
    :type icon: str or QIcon or list[QIcon | QIcon]
    :param checked: The initial state of the entry.
    :type checked: bool
    :param full_name: The full name of the entry, if necessary.
    :type full_name: str, optional

    :ivar entry: The menu entry displayed in the user interface.
    :type entry: QAction

    :methods:
        - toggle: Toggles between the two states of the entry.
    """

    def __init__(self, function, states, icon, checked, full_name=None):
        """
        Initialize a ToggleEntry instance.

        :param function: The function to be called when the entry is
            toggled.
        :type function: callable
        :param states: A list of two states that the entry can have.
        :type states: list
        :param icon: The icon for the entry.
        :type icon: str or QIcon or list[QIcon | QIcon]
        :param checked: The initial state of the entry.
        :type checked: bool
        :param full_name: The full name of the entry, if necessary.
        :type full_name: str, optional

        :return: None
        """

        self.function = function
        self.states = states
        self.icon = icon
        self.checked = checked
        if full_name is not None:
            self.full_name = full_name

        # Create the entry with given name.
        self.entry = QAction(self.states[0])

        # Set the icon if the entry is checked.
        if self.checked:
            # If user provides a list of icons, use the first one.
            # This is done to support different icons for ON and OFF,
            # and not only ON -> checkmark, OFF -> no icon.
            if isinstance(self.icon, QIcon):
                self.entry.setIcon(QIcon(self.icon))
                self.entry.setText(self.states[0])
                self.entry.setToolTip(self.states[0])
            else:
                self.entry.setIcon(QIcon(self.icon[0]))
                self.entry.setText(self.states[0].lstrip())
                self.entry.setToolTip(self.states[0].lstrip())

        else:
            if isinstance(self.icon, QIcon):
                self.entry.setIcon(QIcon())
                self.entry.setText(self.states[1])
                self.entry.setToolTip(self.states[1])
            else:
                self.entry.setIcon(QIcon(self.icon[1]))
                self.entry.setText(self.states[1].lstrip())
                self.entry.setToolTip(self.states[1].lstrip())

        # Connect the entry to the function.
        self.entry.triggered.connect(partial(self.toggle))

    def toggle(self):
        """
        Toggles between the two states of the entry.

        If the entry is in the first state, it switches to the second
        state, and vice versa. When toggled, it also calls the
        associated function with the state as an argument.

        :return: None
        """

        # Toggle the entry: ON -> OFF.
        if self.checked:
            self.checked = False

            if isinstance(self.icon, QIcon):
                self.entry.setIcon(QIcon())
                self.entry.setText(self.states[1])
                self.entry.setToolTip(self.states[1])
            else:
                self.entry.setIcon(QIcon(self.icon[1]))
                self.entry.setText(self.states[1].lstrip())
                self.entry.setToolTip(self.states[1].lstrip())

            # Call the function with the state name as argument.
            # lstrip() is required to remove the leading whitespace
            # that are used for menu text alignment.

            if hasattr(self, "full_name"):
                self.function(self.full_name, True)
            else:
                self.function(self.states[1].lstrip())

        # OFF -> ON.
        else:
            self.checked = True

            if isinstance(self.icon, QIcon):
                self.entry.setIcon(QIcon(self.icon))
                self.entry.setText(self.states[0])
                self.entry.setToolTip(self.states[0])
            else:
                self.entry.setIcon(QIcon(self.icon[0]))
                self.entry.setText(self.states[0].lstrip())
                self.entry.setToolTip(self.states[0].lstrip())

            # Call the function with the state name as argument.
            if hasattr(self, "full_name"):
                self.function(self.full_name, False)
            else:
                self.function(self.states[0])


class SubMenu:
    """
    Creates a submenu and provides management functions for submenu
    entries.

    :param name: The name of the submenu.
    :type name: str
    :param exclusive: A boolean value indicating whether only one entry
        in the submenu can be selected at a time.
    :type exclusive: bool
    :param entries: A variable number of entries to be added to the
        submenu.
    :type entries: ToggleEntry or tuple[ToggleEntry, ...]

    :methods:
        - toggle_excl: Toggles between the two states of the entry and
            toggles all other entries off.
    """

    def __init__(self, name, exclusive, *entries):
        """
        Initialize a SubMenu instance.

        :param name: The name of the submenu.
        :type name: str
        :param exclusive: A boolean value indicating whether only one
            entry in the submenu can be selected at a time.
        :type exclusive: bool
        :param entries: A variable number of entries to be added to the
            submenu.
        :type entries: ToggleEntry | tuple[ToggleEntry, ...]

        :return: None
        """

        self.name = name
        self.exclusive = exclusive
        self.entries = entries
        self.submenu = QMenu(self.name)

        for entry in self.entries:
            self.submenu.addAction(entry.entry)

            # Connect the entry to the exclusive toggling function.
            if self.exclusive:
                entry.entry.triggered.connect(partial(self.toggle_excl, entry))

    def toggle_excl(self, entry_clicked):
        """
        Toggles exclusive entries within the submenu.

        This function is used to toggle between exclusive entries within
        the submenu. When one entry is clicked, it gets toggled to the
        active state, while others are toggled off.

        :param entry_clicked: The entry that was clicked and should be
            toggled.
        :type entry_clicked: ToggleEntry

        :return: None
        """

        for entry in self.entries:
            # Clicked entry gets toggled: OFF -> ON. No need to call the
            # function, because it is already called by the entry's
            # toggle() method.
            if entry_clicked == entry:
                entry.entry.checked = True
                entry.entry.setIcon(QIcon(entry.icon))
                entry.entry.setText(entry.states[0])
                entry.entry.setToolTip(entry.states[0])

            # All other entries get toggled: ON -> OFF.
            else:
                entry.entry.checked = False
                entry.entry.setIcon(QIcon())
                entry.entry.setText(entry.states[1])
                entry.entry.setToolTip(entry.states[1])


class TrayApp:
    """
    Main application class responsible for managing the system tray icon
    and its functionalities.

    This class initializes the application, manages the theme and worker
    threads, and handles user interactions through the system tray icon
    menu.

    :ivar app: The main Qt application instance.
    :type app: QApplication
    :ivar theme: The current system theme (e.g., Light or Dark).
    :type theme: str
    :ivar resources: The resource paths for icons and images based on
        the current theme.
    :type resources: dict
    :ivar config: The application configuration loaded from the
        configuration file.
    :type config: configparser.ConfigParser
    :ivar start_devices_count: A Counter object to keep track of
        initially connected USB devices.
    :type start_devices_count: collections.Counter
    :ivar allowed_devices_count: A Counter object to keep track of
        allowed USB devices.
    :type allowed_devices_count: collections.Counter
    :ivar current_devices_count: A Counter object to keep track of
        currently connected USB devices.
    :type current_devices_count: collections.Counter

    :methods:
        - usb_worker_handle: Start or stop the USB worker thread for
            monitoring connected devices.
        - menu_devices_update: Update the device menu based on connected
            and allowed devices.
        - whitelist_update: Add or remove devices from the whitelist.
        - worker_handle: Start or stop the main worker thread for
            manipulation detection.
        - defuse: Defuse the manipulation detection and reset the alarm.
        - manipulation: Handle manipulation detection and display
            the alarm.
        - config_update: Update the application configuration based on
            user settings.
        - theme_worker_handle: Start or stop the theme listener thread.
        - theme_listener: Listen for changes in the system theme and
            update application resources accordingly.
        - create_tray_icon: Create and configure the system tray icon
            and its menu.
        - help: Display a help message with instructions for using
            the application.
        - about: Display an about message with information about the
            application and its author.
        - exit_handler: Handle application exit and cleanup.

    :param None:
    :return: None
    """

    def __init__(self):
        """
        Initialize the TrayApp instance.

        This method initializes the TrayApp instance by setting up the
        main Qt application, loading configuration, initializing
        counters, connecting signals and slots, and creating the system
        tray icon.

        :return: None
        """

        # Initialize the Qt Application.
        self.app = QApplication(sys.argv)

        # Set the launch time of the application.
        self.app.launch_time = datetime.datetime.now()

        # Register handlers for clean exit of program.
        for sig in [
            signal.SIGINT,
            signal.SIGTERM,
            signal.SIGQUIT,
            signal.SIGABRT,
        ]:
            signal.signal(sig, self.exit_handler)

        # Set the exception hook.
        sys.excepthook = self.handle_exception

        # Set the current OS theme and corresponding resources.
        self.theme = darkdetect.theme()
        self.resources = LIGHT if self.theme == "Light" else DARK

        # Initialize the config and run startup checks.
        self.config = startup()

        # Set log level (1,2,3,4,5) and destination (file, syslog, stdout).
        set_level_dest(LOGGER, self.config)

        # Print worker start message, but only if not logging to stdout.
        if "stdout" not in self.config["Application"]["log"]:
            print("Start guarding the USB interface ...", file=sys.stdout)

        # OS theme listener: checks for theme changes every 2 seconds in
        # a separate thread.
        self.theme_thread = None
        self.theme_timer = None
        self.theme_worker_handle(True)

        # Start the main worker thread (for manipulation detection).
        self.worker = None
        self.worker_thread = None
        self.worker_handle("Guarding")

        self.menu_settings = None
        self.submenu = None
        self.menu_enabled = None
        self.menu_tamper = None

        # Create and display the system tray icon with its menu.
        self.app_icon = self.create_tray_icon()
        self.app_icon.show()

        # Start the USB worker thread (checks for connected devices).
        self.usb_worker_timer = None
        self.usb_worker_thread = None
        self.start_devices_count = Counter(usb_devices())
        self.allowed_devices_count = Counter(
            literal_eval("[" + self.config["Whitelist"]["usb"] + "]")
        )
        self.current_devices_count = Counter(usb_devices())
        self.usb_worker_handle(state=True)
        self.menu_devices_update(start_up=True)

        # After full initialization, check for updates and show
        # messageBox if update is available.
        if new_vers := check_updates():
            self.update_box(new_vers)

    def usb_worker_handle(self, state):
        """
        Start or stop the USB worker thread for monitoring connected
        devices.

        This function manages the USB worker thread responsible for
        monitoring USB device connections. It can be started or stopped
        based on the provided state.

        :param state: A boolean value indicating whether to start (True)
            or stop (False) the USB worker thread.
        :type state: bool

        :return: None
        """

        if state:
            # Start the usb worker thread.
            self.usb_worker_thread = QThread()
            self.usb_worker_timer = QTimer(interval=1000)
            self.usb_worker_timer.timeout.connect(self.menu_devices_update)
            self.usb_worker_timer.moveToThread(self.usb_worker_thread)
            self.usb_worker_thread.started.connect(self.usb_worker_timer.start)
            self.usb_worker_thread.finished.connect(self.usb_worker_timer.stop)
            self.usb_worker_thread.start()

        else:
            # Stop the usb worker thread.
            self.usb_worker_thread.quit()
            self.usb_worker_thread.wait()
            self.usb_worker_thread.deleteLater()

    def menu_devices_update(self, start_up=False):
        """
        Update the device menu based on connected and allowed devices.

        This function updates the device menu in the system tray based
        on the currently connected USB devices and the devices allowed
        in the whitelist. It can be called at startup and when devices
        change.

        :param start_up: A boolean indicating whether the update is
            occurring at application startup.
        :type start_up: bool

        :return: None
        """

        # Get the current devices and their exact count.
        curr = usb_devices()
        curr_copy = deepcopy(curr)
        curr_count = Counter(curr)

        # Get the allowed devices and their exact count.
        allow = literal_eval("[" + self.config["Whitelist"]["usb"] + "]")
        allow_count = Counter(allow)

        # If the count of currently connected devices is the same as
        # before, and the count of allowed devices is the same as
        # before, there is no need to update the device menu.
        if not start_up and (
            self.start_devices_count == curr_count
            and self.allowed_devices_count == allow_count
        ):
            return

        # Remove allowed devices from start devices.
        for device in allow:
            if device in curr_copy:
                curr_copy.remove(device)

        # Clear the submenu of all entries.
        self.submenu.clear()

        # Add all whitelisted devices to the submenu.
        for device in allow:
            device_name = str(device[3])
            device_action = ToggleEntry(
                self.whitelist_update,
                [device_name, f"      {device_name}"],
                QIcon(self.resources["checkmark"]),
                True,
                full_name=device,
            )

            self.submenu.addAction(device_action.entry)

        # Add the remaining currently connected devices to the submenu.
        for device in curr_copy:
            device_name = str(device[3])
            device_action = ToggleEntry(
                self.whitelist_update,
                [device_name, f"      {device_name}"],
                QIcon(self.resources["checkmark"]),
                False,
                full_name=device,
            )

            self.submenu.addAction(device_action.entry)

        # If whitelist is empty and no devices are connected, add a
        # dummy entry ("Searching").
        if not allow and not curr:
            submenu_dummy = QAction("Searching ...", self.submenu)
            submenu_dummy.setEnabled(False)
            self.submenu.addAction(submenu_dummy)

        # Update the start and allowed devices count, for next
        # function call/iteration.
        self.start_devices_count = curr_count
        self.allowed_devices_count = allow_count

    def whitelist_update(self, device_menu, checked):
        """
        Add or remove devices from the whitelist.

        This function allows users to add or remove USB devices from the
        whitelist by clicking on corresponding menu entries. It updates
        the application configuration.

        :param device_menu: The USB device entry that was clicked.
        :type device_menu: str
        :param checked: A boolean indicating whether the device should
            be added (False) or removed (True) from the whitelist.
        :type checked: bool

        :return: None
        """

        # Remove device from whitelist.
        if checked:
            allowed = literal_eval("[" + self.config["Whitelist"]["usb"] + "]")
            for allow in allowed:
                if allow == device_menu:
                    allowed.remove(device_menu)

                    # Remove device from whitelist.
                    self.config["Whitelist"]["usb"] = str(allowed)[1:-1]

                    LOGGER.info(
                        f"Remove device from whitelist: {device_menu}."
                    )

                    break

            # Write the updated config to disk.
            config_write(self.config)

            # Signal the worker, that the whitelist was updated.
            self.worker.updated_whitelist()

            return

        # Add device to whitelist.
        curr = usb_devices()
        for device in curr:
            if device == device_menu:
                if self.config["Whitelist"]["usb"] == "":
                    self.config["Whitelist"]["usb"] = str(device)

                else:
                    self.config["Whitelist"]["usb"] += f", {device}"

                LOGGER.info(f"Add device to whitelist: {device_menu}.")

                # Write the updated config to disk.
                config_write(self.config)

                # Signal the worker, that the whitelist was updated.
                self.worker.updated_whitelist()

                return

    def worker_handle(self, state):
        """
        Start or stop the main worker thread for manipulation detection.

        This function manages the main worker thread responsible for
        detecting manipulation of USB devices. It can be started or
        stopped based on the provided state.

        :param state: A string indicating the desired state for the
            worker thread ('Guarding' or 'Inactive').
        :type state: str

        :return: None
        """

        if state == "Guarding":
            # Initialize the worker object with config.
            Workers.config = self.config
            Workers.defused = False
            Workers.tampered_var = False
            self.worker = Worker("USB")

            # Connect the worker signals to the corresponding slots.
            # If the worker detects tampering, it emits the tampered
            # signal, which is connected to the manipulation function
            # that displays the alarm.
            self.worker.tampered_sig.connect(self.manipulation)

            # Move the worker object to a separate thread.
            self.worker_thread = QThread()
            self.worker.moveToThread(self.worker_thread)

            self.worker_thread.started.connect(self.worker.loop)
            self.worker_thread.finished.connect(self.worker.stop)
            self.worker_thread.start()

        else:
            # Stop the worker thread.
            self.worker.running = False
            self.worker.stop()

            try:
                self.worker_thread.quit()
                self.worker_thread.wait()
                self.worker_thread.deleteLater()

            except RuntimeError:
                # Ignore RuntimeError: wrapped C/C++ object of type
                # Worker has been deleted.
                pass

            LOGGER.info(
                "STOPPED guarding the USB interface ...",
            )

    def defuse(self):
        """
        Defuse the manipulation detection countdown and reset the alarm.

        This function is called when the user clicks on the
        "Manipulation" menu entry to reset the alarm and return to
        normal monitoring mode.

        :return: None
        """

        # If delay is set to 0, defusing is disabled.
        if self.config["User"]["delay"] == "0":
            return

        # Defuse the worker by setting the defused flag to True.
        self.worker.defused = True
        self.worker.tampered_var = False

        # Show "Guarding/Inactive" and hide "Manipulation" menu entry.
        self.menu_enabled.entry.setVisible(True)
        self.menu_tamper.setVisible(False)

        # Stop the worker.
        self.worker_handle("Inactive")

        # Recreate/Update the tray menu.
        self.app_icon.deleteLater()
        self.app_icon = self.create_tray_icon()
        self.app_icon.show()

        # Update the device menu.
        self.menu_devices_update(start_up=True)

        LOGGER.info("The worker was STOPPED after defusing!")

        self.menu_settings.setDisabled(False)
        self.submenu.setDisabled(False)

    def manipulation(self):
        """
        Handle manipulation detection and display the alarm.

        This function is triggered when manipulation of USB devices is
        detected. It displays the "Manipulation" menu entry to alert
        the user.

        :return: None
        """

        # Display "Manipulation" menu item and hide the "ON/OFF" menu.
        self.menu_enabled.entry.setVisible(False)
        self.menu_tamper.setVisible(True)

        # Prevent changing the settings or adding devices to whitelist,
        # while the alarm is active (Manipulation detected).
        self.menu_settings.setDisabled(True)
        self.submenu.setDisabled(True)

    def config_update(self, button, state=None):
        """
        Update the application configuration file based on user input.

        This function updates the application configuration when the
        user selects settings in the menu. If user edits the config file
        on disk manually, the GUI will NOT be updated automatically,
        a restart of the application is required.

        :param button: The setting or option selected by the user.
        :type button: str
        :param state: The state of the button before it was clicked.
            Only available for toggle buttons with full_name.
        :type state: bool, optional

        :return: None
        """

        # User -> Action.
        if button == "Hibernate":
            self.config["User"]["action"] = "hibernate"
        elif button == "Shutdown":
            self.config["User"]["action"] = "shutdown"

        # User -> Delay.
        elif button == "0 s":
            self.config["User"]["delay"] = "0"
        elif button == "5 s":
            self.config["User"]["delay"] = "5"
        elif button == "10 s":
            self.config["User"]["delay"] = "10"
        elif button == "30 s":
            self.config["User"]["delay"] = "30"
        elif button == "60 s":
            self.config["User"]["delay"] = "60"

        # User -> Autostart.
        elif button == "Autostart":
            # ON -> OFF.
            if state:
                del_autostart()

                # Update the config.
                self.config["User"]["autostart"] = "0"

            # OFF -> ON.
            else:
                result = add_autostart()

                if result:
                    # Update the config.
                    self.config["User"]["autostart"] = "1"

        else:
            LOGGER.info(f"Unknown menu settings button was pressed: {button}.")

        # Write the updated config to disk.
        config_write(self.config)

    def theme_worker_handle(self, state):
        """
        Start or stop the theme listener thread.

        This function manages the theme listener thread, which detects
        changes in the system theme. It can be started or stopped based
        on the provided state.

        :param state: A boolean value indicating whether to start (True)
            or stop (False) the theme listener thread.
        :type state: bool

        :return: None
        """

        if state:
            # Start the theme thread.
            self.theme_thread = QThread()
            self.theme_timer = QTimer(interval=2000)
            self.theme_timer.timeout.connect(self.theme_listener)
            self.theme_timer.moveToThread(self.theme_thread)
            self.theme_thread.started.connect(self.theme_timer.start)
            self.theme_thread.finished.connect(self.theme_timer.stop)
            self.theme_thread.start()

        else:
            # Stop the theme thread.
            self.theme_thread.quit()
            self.theme_thread.wait()
            self.theme_thread.deleteLater()

    def theme_listener(self):
        """
        Listen for changes in the system theme and update application
        resources accordingly.

        This function listens for changes in the system theme (e.g.,
        Light to Dark) and updates application resources such as icons
        and images accordingly.

        :return: None
        """

        theme_os = darkdetect.theme()

        if self.theme != theme_os:
            # Update application resources to their dark/light variants.
            self.resources = LIGHT if theme_os == "Light" else DARK
            # Set the current theme variable.
            self.theme = theme_os

            # Update all icons by deleting and recreating the tray menu.
            self.app_icon.deleteLater()
            self.app_icon = self.create_tray_icon()
            self.app_icon.show()

            # Update the device menu.
            self.menu_devices_update(start_up=True)

            # Log.
            LOGGER.info(f"Application theme changed: {self.theme}.")

    def update_box(self, new_vers):
        """
        The update_box function is used to display a message box
        informing the user that an update is available. The function
        takes one argument, new_vers, which is the latest version of
        swiftGuard as determined by check_update(). The message box
        contains a download button that opens the GitHub release page
        in the default browser and a close button that closes the
        message box. A checkbox is also included to disable future
        update messages.

        :param self: Refer to the current instance of a class
        :param new_vers: Display the latest version of swiftguard
        :return: A message box
        """

        msg_box = QMessageBox()
        msg_box.setWindowTitle("swiftGuard")

        # Bold text.
        msg_box.setText(
            f"Update available!\n\n"
            f"Installed version: {__version__}\nLatest version: "
            f"{new_vers}\n"
        )

        # Smaller, informative text.
        msg_box.setInformativeText(
            "Keeping swiftGuard up to date is advisable due to "
            "its rapid development cycle, ensuring security enhancements, "
            "bug fixes, and continuous improvements.\n"
        )

        # Add app logo.
        pixmap = QPixmap(self.resources["app-logo"])
        msg_box.setIconPixmap(pixmap)

        # Add update button.
        msg_button = msg_box.addButton("Download", QMessageBox.YesRole)

        # Add close button.
        msg_box.addButton("Close", QMessageBox.NoRole)

        # Make text selectable and copyable.
        msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Add checkbox to disable update message.
        cb = QCheckBox("Don't show this message again")
        msg_box.setCheckBox(cb)

        # Show message box.
        msg_box.exec()

        # Open website in browser in new tab.
        if msg_box.clickedButton() == msg_button:
            webbrowser.open_new_tab(
                "https://github.com/Lennolium/swiftGuard/releases/latest"
            )

        # Disable future update messages.
        if cb.isChecked():
            self.config["Application"]["check_updates"] = "0"
            config_write(self.config)

    def create_tray_icon(self):
        """
        Create and configure the system tray icon and its menu.

        This function creates and configures the system tray icon, sets
        up the menu with various options and submenus, and connects
        menu items to their respective functions.

        :return: The configured system tray icon.
        :rtype: QSystemTrayIcon
        """

        # Create and configure the system tray icon.
        tray_icon = QSystemTrayIcon()
        tray_icon.setToolTip("swiftGuard")

        tray_icon.setIcon(QIcon(self.resources["app-icon"]))

        menu_tray = QMenu()

        # Create a submenu for "Devices" initially disabled.
        self.submenu = menu_tray.addMenu("Devices")
        self.submenu.setIcon(QIcon(self.resources["usb-connection"]))
        submenu_dummy = QAction("Searching ...", self.submenu)
        submenu_dummy.setEnabled(False)
        self.submenu.addAction(submenu_dummy)

        # Add an "Enabled" menu item and connect it to submenu creation.
        self.menu_enabled = ToggleEntry(
            self.worker_handle,
            ["Guarding", "      Inactive"],
            [
                QIcon(self.resources["shield-check"]),
                QIcon(self.resources["shield-slash"]),
            ],
            bool(self.worker._isRunning),
        )

        self.menu_enabled.entry.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_E))
        if self.worker.tampered_var:
            self.menu_enabled.entry.setVisible(False)
        else:
            self.menu_enabled.entry.setVisible(True)
        menu_tray.addAction(self.menu_enabled.entry)

        # Create hidden "Manipulation" menu item.
        self.menu_tamper = QAction("Manipulation", menu_tray)
        self.menu_tamper.setIcon(QIcon(self.resources["shield-tamper"]))
        if self.worker.tampered_var:
            self.menu_tamper.setVisible(True)
        else:
            self.menu_tamper.setVisible(False)
        self.menu_tamper.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_E))
        menu_tray.addAction(self.menu_tamper)
        self.menu_tamper.triggered.connect(self.defuse)

        menu_tray.addSeparator()

        # Create a "Settings" menu.
        self.menu_settings = QMenu("      Settings", menu_tray)
        menu_tray.addMenu(self.menu_settings)

        # Create an "Action" submenu within "Settings."
        entry01 = ToggleEntry(
            self.config_update,
            ["Shutdown", "      Shutdown"],
            QIcon(self.resources["checkmark"]),
            self.config["User"]["action"] == "shutdown",
        )

        entry02 = ToggleEntry(
            self.config_update,
            ["Hibernate", "      Hibernate"],
            QIcon(self.resources["checkmark"]),
            self.config["User"]["action"] == "hibernate",
        )

        submenu2 = SubMenu("      Action", True, entry01, entry02)

        self.menu_settings.addMenu(submenu2.submenu)

        # Create a "Delay" submenu within "Settings."
        entry04 = ToggleEntry(
            self.config_update,
            ["0 s", "      0 s"],
            QIcon(self.resources["checkmark"]),
            self.config["User"]["delay"] == "0",
        )

        entry05 = ToggleEntry(
            self.config_update,
            ["5 s", "      5 s"],
            QIcon(self.resources["checkmark"]),
            self.config["User"]["delay"] == "5",
        )

        entry06 = ToggleEntry(
            self.config_update,
            ["10 s", "      10 s"],
            QIcon(self.resources["checkmark"]),
            self.config["User"]["delay"] == "10",
        )

        entry07 = ToggleEntry(
            self.config_update,
            ["30 s", "      30 s"],
            QIcon(self.resources["checkmark"]),
            self.config["User"]["delay"] == "30",
        )

        entry08 = ToggleEntry(
            self.config_update,
            ["60 s", "      60 s"],
            QIcon(self.resources["checkmark"]),
            self.config["User"]["delay"] == "60",
        )

        submenu3 = SubMenu(
            "      Delay", True, entry04, entry05, entry06, entry07, entry08
        )

        self.menu_settings.addMenu(submenu3.submenu)

        # Add an "Autostart" menu item in "Settings" submenu.
        entry09 = ToggleEntry(
            self.config_update,
            ["Autostart", "      Autostart"],
            QIcon(self.resources["checkmark"]),
            self.config["User"]["autostart"] == "1",
            full_name="Autostart",
        )

        self.menu_settings.addAction(entry09.entry)

        # Create "Help" menu item.
        menu_help = QAction("      Help", menu_tray)
        menu_tray.addAction(menu_help)
        menu_help.triggered.connect(self.help)

        # Create "About" menu item.
        menu_about = QAction("      About", menu_tray)
        menu_tray.addAction(menu_about)
        menu_about.triggered.connect(self.about)

        menu_tray.addSeparator()

        # Create an "Exit" menu item and connect it to the exit handler.
        menu_exit = QAction("      Exit", menu_tray)
        menu_exit.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_Q))
        menu_exit.triggered.connect(self.exit_handler)
        menu_tray.addAction(menu_exit)

        # Set the system tray menu.
        tray_icon.setContextMenu(menu_tray)

        return tray_icon

    def acknowledgements(self):
        """
        The acknowledgements function is called when the user clicks on
        the acknowledgements button in the help menu. It creates a
        custom dialog box with a text and a scrollbar explaining what
        third-party libraries swiftGuard uses.

        :param self: Represent the instance of the class
        :return: A message box with a list of third party libraries
            used in the project
        """

        msg_box = CustomDialog(
            f"{APP_PATH}/resources/ACKNOWLEDGMENTS",
            "Acknowledgements",
            "swiftGuard uses the following third-party libraries:",
        )

        msg_box.exec()

    def help(self):
        """
        Display a help message with instructions for using the program.

        This function displays a help message with brief instructions
        on how to use the application and its features.

        :return: None
        """

        msg_box = QMessageBox()
        msg_box.setWindowTitle("swiftGuard")

        # Bold text.
        msg_box.setText("swiftGuard\n\nBrief Instructions")

        # Smaller, informative text.
        msg_box.setInformativeText(
            "1. Click the 'Guarding/Inactive' entry to start or pause the "
            "guarding of your USB ports\n\n"
            "2. The devices menu displays all allowed and connected "
            "devices. Allowed Devices are indicated with a checkmark, "
            "even if they are not connected.\n\n"
            "3. To add or remove a Device from the whitelist, simply "
            "click on the corresponding device entry.\n\n"
            "4. If manipulation is detected by swiftGuard, an alert will "
            "appear in the main menu. Clicking on it will reset the "
            "alarm. The Exit button will not work.\n\n"
            "5. You can set a delay (0 - 60 seconds) and an action "
            "(Shutdown or Hibernate) in the settings menu. The delay "
            "determines how long swiftGuard will wait for you to reset "
            "the alarm before executing the action.\n\n"
            "Notes: swiftGuard alerts you if devices are removed "
            "that were connected before or while the application was started, "
            "except you add them to the whitelist. Connecting new devices "
            "will always trigger an alert, if these devices are not "
            "whitelisted. For running the script in standalone mode, check "
            "the project repository on GitHub for instructions.\n"
        )

        # Add app logo.
        pixmap = QPixmap(self.resources["app-logo"])
        msg_box.setIconPixmap(pixmap)

        # Add documentation button.
        doc_button = msg_box.addButton("Documentation", QMessageBox.HelpRole)

        # Add project and close button.
        email_button = msg_box.addButton("E-Mail", QMessageBox.HelpRole)
        msg_box.addButton("Close", QMessageBox.NoRole)

        # Make text selectable and copyable.
        msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Show message box.
        msg_box.exec()

        # Open website in browser in new tab.
        if msg_box.clickedButton() == doc_button:
            webbrowser.open_new_tab(
                "https://github.com/Lennolium/swiftGuard/wiki"
            )
        elif msg_box.clickedButton() == email_button:
            webbrowser.open_new_tab(
                "mailto:lennart-haack@mail.de?subject=swiftGuard%3A%20I"
                "%20need%20assistance&body=Dear%20Lennart%2C%0A%0AI'm"
                "%20using%20your%20application%20'swiftGuard'%2C%20but"
                "%20I%20did%20run%20into%20some%20problems%20and%20I"
                "%20need%20assistance%20with%20the%20following%3A"
            )

    def about(self):
        """
        Display an about message with information about the application
        and its author.

        This function displays an about message with information about
        the application, its purpose, and its author.

        :return: None
        """

        msg_box = QMessageBox()
        msg_box.setWindowTitle("swiftGuard")

        # Bold text.
        msg_box.setText(
            f"swiftGuard\n\nVersion {__version__} ({__build__})\n\n\nMade "
            f"with ❤️ by Lennolium" + "                                       "
        )

        # Smaller, informative text.
        msg_box.setInformativeText(
            "\n👋🏻 Lennart Haack \n"
            "📨 lennart-haack@mail.de \n"
            "🔑 F452 A252 1A91 043C A02D 4C06 5BE3 C31E F9DF CEA7\n\n"
            "swiftGuard is free software: you can redistribute it and/or "
            "modify it under the terms of the GNU General Public License as "
            "published by the Free Software Foundation, either version 3 of "
            "the License, or (at your option) any later version."
            "This program is distributed in the hope that it will be useful, "
            "but WITHOUT ANY WARRANTY; without even the implied warranty of "
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the "
            "GNU General Public License for more details. "
            "You should have received a copy of the GNU General Public "
            "License along with this program. If not, see \n\n"
            "< https://www.gnu.org/licenses/ >.\n"
            "< https://github.com/Lennolium/swiftGuard/blob/main/LICENSE >\n"
        )

        # Add app logo.
        pixmap = QPixmap(self.resources["app-logo"])
        msg_box.setIconPixmap(pixmap)

        # Add documentation button.
        project_button = msg_box.addButton("Project", QMessageBox.YesRole)

        # Add project and close button.
        acknow_button = msg_box.addButton(
            "Acknowledgments", QMessageBox.HelpRole
        )
        msg_box.addButton("Close", QMessageBox.NoRole)

        # Make text selectable and copyable.
        msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Show message box.
        msg_box.exec()

        # Open website in browser in new tab.
        if msg_box.clickedButton() == project_button:
            webbrowser.open_new_tab("https://github.com/Lennolium/swiftGuard")
        elif msg_box.clickedButton() == acknow_button:
            self.acknowledgements()

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        The handle_exception function is a custom exception handler that
        logs uncaught exceptions to CRITICAL.

        :param exc_type: Store the type of exception that occurred
        :param exc_value: Get the exception value
        :param exc_traceback: Get the traceback object
        :return: None
        """

        # Do not log KeyboardInterrupt (Ctrl+C).
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        LOGGER.critical(
            "Uncaught Exception:",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

        self.exit_handler(error=True)

    def exit_handler(self, signum=None, frame=None, error=False):
        """
        Handle application exit and cleanup.

        This function performs cleanup tasks and ensures that the
        application exits gracefully when the user chooses to close it.

        :param signum: Identify the signal that caused the exit_handler
            to be called
        :param frame: Reference the frame object that called function
        :param error: If True, an error occurred which caused the exit
        :return: None
        """

        try:
            # If the manipulation was detected, do not exit the application,
            # if user presses the "Exit" menu item. Defusing before exiting
            # is required.
            if self.menu_tamper.isVisible():
                return

            # Stop and delete the theme thread to prevent memory leaks.
            self.theme_worker_handle(False)

            # Stop and delete the connected devices thread.
            self.usb_worker_handle(False)

            # Stop and delete the worker thread.
            self.worker_handle("Inactive")

        except Exception:  # nosec B110
            pass

        # If error is True, an error occurred which caused the exit.
        if error:
            LOGGER.critical(
                "A critical error occurred that caused the application "
                "to exit unexpectedly."
            )
            self.app.quit()
            sys.exit(1)

        LOGGER.info("Exiting the application properly ...")
        self.app.quit()
        sys.exit(0)


def main():
    """
    Entry point for starting the USB Device Monitoring application.

    This function initializes the Qt application, creates an instance
    of the TrayApp class, and starts the application event loop. Also
    sets some general application information. Prevents the application
    from exiting when popups or message boxes are closed.

    :return: None
    """

    # Create the tray application instance.
    tray = TrayApp()

    # Set general application information.
    tray.app.setApplicationDisplayName("swiftGuard")
    tray.app.setApplicationName("swiftGuard")
    tray.app.setApplicationVersion(__version__)
    tray.app.setOrganizationName("lennolium.dev")
    tray.app.setOrganizationDomain("lennolium.dev")

    # Prevent app exit, if popups/messageBoxes are closed.
    tray.app.setQuitOnLastWindowClosed(False)

    # Exit the application when the tray_app is closed.
    sys.exit(tray.app.exec())


if __name__ == "__main__":
    main()
