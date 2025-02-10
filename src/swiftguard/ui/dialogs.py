#!/usr/bin/env python3

"""
dialogs.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-05-14"
__build__ = "2024.5"
__status__ = "Prototype/Development/Production"

# Imports.
import webbrowser
from collections import deque

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
                               QHBoxLayout, QLabel,
                               QMessageBox,
                               QMainWindow,
                               QSizePolicy, QSpacerItem, QStyle, QTextEdit,
                               QVBoxLayout)
from PySide6.QtCore import QDateTime, QTimer, Qt

from swiftguard.utils import helpers, process
from swiftguard.constants import C
from swiftguard.init import exceptions as exc


def show_exit_dialog():
    # Get the main window to set the dialog_open attribute.
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QMainWindow):
            mainwindow = widget
            break

    mainwindow.dialog_open = True

    msg_box = QMessageBox()
    msg_box.setWindowTitle("swiftGuard")
    msg_box.setIconPixmap(QPixmap(C.res.RES["icon"]))

    msg_box.setText("Are you really sure?")
    msg_box.setInformativeText(
            "This will stop all guarding processes and close the "
            "application.\n"
            )
    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes |
                               QMessageBox.StandardButton.No
                               )
    msg_box.setDefaultButton(QMessageBox.StandardButton.No)

    reply = msg_box.exec()

    if reply == QMessageBox.StandardButton.Yes:
        exc.exit_handler(signum=0)

    mainwindow.dialog_open = False


def show_about_dialog():
    """
    Display an about message with information about the application
    and its author.

    This function displays an about message with information about
    the application, its purpose, and its author.

    :return: None
    """

    msg_box = QMessageBox()
    msg_box.setWindowTitle("swiftGuard")

    msg_box.setText(
            f"swiftGuard\n\nVersion {__version__} ({__build__})\n\n\nMade "
            f"with ❤️ by Lennolium" + "                                  "
                                      "     "
            )

    msg_box.setInformativeText(
            "\n👋🏻 Lennart Haack \n"
            "🧭 https://swiftguard.lennolium.dev \n"
            "📨 swiftguard@lennolium.dev \n"
            "🔑 F452 A252 1A91 043C A02D 4C06 5BE3 C31E F9DF CEA7\n\n"
            "swiftGuard is free software: you can redistribute it and/or "
            "modify it under the terms of the GNU General Public License "
            "as published by the Free Software Foundation, either version 3 "
            "of the License, or (at your option) any later version. See the "
            "GNU General Public License for more details:\n\n"
            "< https://www.gnu.org/licenses/ >\n"
            "< https://github.com/Lennolium/swiftGuard/blob/main/LICENSE >"
            "\n\n"
            "For all used libraries and resources, see ACKNOWLEDGMENTS.\n\n"
            )

    msg_box.setIconPixmap(QPixmap(C.res.RES["icon"]))

    help_button = msg_box.addButton("Help", QMessageBox.ButtonRole.HelpRole)
    source_button = msg_box.addButton("Source",
                                      QMessageBox.ButtonRole.HelpRole
                                      )
    acknow_button = msg_box.addButton("Acknowledgments",
                                      QMessageBox.ButtonRole.HelpRole
                                      )
    close_button = msg_box.addButton("Close",
                                     QMessageBox.ButtonRole.AcceptRole
                                     )

    # Make text selectable and copyable.
    msg_box.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            )

    msg_box.exec()

    # Open website in browser in new tab.
    if msg_box.clickedButton() == source_button:
        webbrowser.open_new_tab(C.app.URLS["github"])
    elif msg_box.clickedButton() == acknow_button:
        return
        # acknowledgements()


def show_uninstall_dialog(
        signum: int = 0
        ) -> None:
    """
    Display a prompt to the user to guide him through the uninstallation
    process.

    :param signum: If non-zero, the dialog will display and exit button,
        otherwise a cancel button will be displayed.
    :type signum: int
    :return: None
    """

    msg_box = QMessageBox()
    msg_box.setWindowTitle("swiftGuard")
    msg_box.setIconPixmap(QPixmap(C.res.RES["icon"]))

    msg_box.setText(
            "You are about to uninstall swiftGuard!"
            )

    msg_box.setInformativeText(
            "Please select an option or cancel the uninstallation.\n\n"
            "----- Full ----- \n"
            "Uninstall swiftGuard and all its components. "
            "Every trace of the app will be removed."
            "\n\n"
            "----- Keep Config ----- \n"
            "Uninstall swiftGuard, but keep the "
            "configuration. This option is useful if you want to reinstall "
            "the app later with the same settings."
            "\n\n"
            "----- Manual ----- \n"
            "Open the uninstallation guide in your browser. "
            "Use this, if you want to delete the files manually and do not "
            "want to use the uninstall script.\n"
            )

    full_btn = msg_box.addButton("Full",
                                 QMessageBox.ButtonRole.DestructiveRole
                                 )
    cfg_btn = msg_box.addButton("Keep Config",
                                QMessageBox.ButtonRole.DestructiveRole
                                )
    man_btn = msg_box.addButton("Manual", QMessageBox.ButtonRole.YesRole)
    if signum != 0:
        msg_box.addButton("Exit", QMessageBox.ButtonRole.RejectRole)
    else:
        msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

    msg_box.exec()

    if msg_box.clickedButton() == full_btn:
        helpers.uninstall_app(keep_config=False)

    elif msg_box.clickedButton() == cfg_btn:
        helpers.uninstall_app(keep_config=True)

    elif msg_box.clickedButton() == man_btn:
        webbrowser.open(
                url=C.app.URLS["uninstall"],
                new=1,
                )

        if signum != 0:
            exc.exit_handler(signum=signum)

    else:
        if signum != 0:
            exc.exit_handler(signum=signum)
        else:
            pass


def show_integrity_dialog(e: Exception) -> None:
    """
    Display a prompt to the user, if the integrity of the
    application is compromised.

    :param e: The exception that was raised used to display the
        modified file(s).
    :type e: Exception
    :return: None
    """

    msg_box = QMessageBox()
    msg_box.setWindowTitle("swiftGuard")
    msg_box.setText(
            f"The integrity of swiftGuard is compromised!"
            )

    # Extract the file from the exception.
    try:
        file = str(e).split("'")[1]
    except IndexError:
        file = "unknown"

    msg_box.setInformativeText(
            f"Someone modified the program and/or config files. "
            f"This could be the result of a security breach.\n\n"
            f"Please ensure integrity of your system and reinstall "
            f"swiftGuard!\n\n"
            f"The following file is compromised:\n"
            f"'{file}'"
            )

    # pixmap = QPixmap(C.res.RES["icon"])
    # msg_box.setIconPixmap(pixmap)

    # Gives a deprecated warning.
    # msg_box.setIconPixmap(QMessageBox.standardIcon(QMessageBox.Critical))
    # Using this instead.
    msg_box.setIconPixmap(
            QApplication.style().standardIcon(
                    QStyle.StandardPixmap.SP_MessageBoxCritical
                    ).pixmap(64, 64)
            )

    msg_box.addButton("Uninstall", QMessageBox.ButtonRole.DestructiveRole)
    exit_btn = msg_box.addButton("Exit", QMessageBox.ButtonRole.YesRole)

    # Set the volume to 50%.
    process.Process(
            binary_path="/usr/bin/osascript",
            args=("-e",
                  "set volume output volume 50"),
            timeout=1,
            blocking=True,
            ).run()

    # Play a sound to alert the user.
    _ = process.Process(
            binary_path="/usr/bin/afplay",
            args=("-t", "1.0",
                  "-q", "1",
                  "/System/Library/Sounds/Submarine.aiff",),
            timeout=1,
            blocking=False,
            ).run()

    msg_box.exec()

    if hasattr(e, "code"):
        signum = e.code
    else:
        signum = 8

    if msg_box.clickedButton() == exit_btn:
        exc.exit_handler(signum=signum)
    else:
        show_uninstall_dialog(
                signum=signum,
                )


def show_error_dialog(thrown_exc: Exception) -> None:
    """
    Display an error message to the user.

    :param thrown_exc: The exception name to display.
    :type thrown_exc: Exception
    :return: None
    """

    # Memory-efficiently load the last 150 lines of the log file.
    try:
        with open(C.log.FILE, "r") as f:
            last_150_lines = deque(f, maxlen=150)

        last_50_lines_str = "\n".join(list(last_150_lines)[-50:])

    except Exception as e:
        last_150_lines = deque(
                f"Could not read log file: {e.__class__.__name__}:"
                f" {e}"
                )
        last_50_lines_str = (
                f"Could not read log file: {e.__class__.__name__}:"
                f" {e}")

    dialog = QDialog()
    dialog.setWindowTitle("swiftGuard")
    dialog.setWindowFlags(dialog.windowFlags() |
                          Qt.WindowType.WindowStaysOnTopHint
                          )
    dialog.setMinimumSize(650, 450)

    layout = QVBoxLayout()
    top_layout = QHBoxLayout()
    label_layout = QVBoxLayout()
    button_layout = QHBoxLayout()

    # Critical icon.
    icon_label = QLabel()
    icon_label.setPixmap(QMessageBox.standardIcon(QMessageBox.Icon.Critical))
    spacer = QSpacerItem(20, 0, QSizePolicy.Policy.Fixed,
                         QSizePolicy.Policy.Minimum
                         )

    # Add the error message.
    heading_label = QLabel(
            f"<br><b>swiftGuard crashed unexpectedly!</b><br>"
            f"Exception: {thrown_exc.__name__}"
            )
    font = heading_label.font()
    font.setPointSize(15)
    heading_label.setFont(font)

    # Add the informative text.
    subheading_label = QLabel(
            f"<br>"
            f"The application crashed at "
            f"{QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")} "
            f"due to an unexpected error. "
            f"<br> Please choose an action below to help me fix the issue. "
            f"<br>"
            )

    label_layout.addWidget(heading_label, 0, Qt.AlignmentFlag.AlignLeft)
    label_layout.addWidget(subheading_label, 0, Qt.AlignmentFlag.AlignLeft)

    top_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignLeft)
    top_layout.addItem(spacer)
    top_layout.addLayout(label_layout)
    top_layout.addStretch()

    # Link to the log file folder.
    log_label = QLabel(f"<a href='#'>{C.log.FILE}</a>")
    log_label.setOpenExternalLinks(False)
    log_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
            )
    log_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    log_label.setCursor(Qt.CursorShape.PointingHandCursor)
    log_label.linkActivated.connect(helpers.open_log)

    # Log field with color formatted log lines.
    log_field = QTextEdit()
    log_field.setHtml(helpers.format_log(last_150_lines))
    log_field.setReadOnly(True)
    log_field.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    # Scroll to the bottom of the QTextEdit widget (newest log lines).
    QTimer.singleShot(0, lambda: log_field.verticalScrollBar().setValue(
            log_field.verticalScrollBar().maximum()
            )
                      )

    # Buttons and related actions.
    btn_box = QDialogButtonBox()
    send_logs_button = btn_box.addButton(
            "Send Crash Report",
            QDialogButtonBox.ButtonRole.ActionRole
            )
    open_github_button = btn_box.addButton(
            "Copy and Open GitHub",
            QDialogButtonBox.ButtonRole.ActionRole
            )
    exit_button = btn_box.addButton(
            "    Exit    ",
            QDialogButtonBox.ButtonRole.ActionRole
            )
    exit_button.setDefault(True)
    send_logs_button.clicked.connect(
            lambda _: helpers.send_log(lines=last_50_lines_str)
            )
    open_github_button.clicked.connect(
            lambda _: helpers.open_github_issue(lines=last_50_lines_str)
            )
    exit_button.clicked.connect(dialog.accept)

    button_layout.addWidget(send_logs_button)
    button_layout.addWidget(open_github_button)
    button_layout.addStretch()
    button_layout.addWidget(exit_button)

    layout.addLayout(top_layout)
    layout.addWidget(log_label)
    layout.addWidget(log_field)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)

    # Set the volume to 60%.
    process.Process(
            binary_path="/usr/bin/osascript",
            args=("-e",
                  "set volume output volume 60"),
            timeout=1,
            blocking=True,
            ).run()

    # Play a sound to alert the user.
    _ = process.Process(
            binary_path="/usr/bin/afplay",
            args=("-t", "1.0",
                  "-q", "1",
                  "/System/Library/Sounds/Bottle.aiff",),
            timeout=1,
            blocking=False,
            ).run()

    # Show the dialog.
    dialog.exec()
