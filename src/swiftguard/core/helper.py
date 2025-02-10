#!/usr/bin/env python3

"""
core/helper.py: HelperManager class for managing the helper binary.

The HelperManager class is a singleton class that manages the helper
binary. It is responsible for starting the binary, logging in, sending
encrypted and signed messages, and stopping the binary.


**USAGE:**

*Create a new instance (automatically starts the binary and logs in).*

- from swiftguard.core import helper
- helper = helper.HelperManager()

*Get the current instance (useful for importing in other modules).*

- helper = helper.HelperManager.get_instance()

*Use the instance methods to interact with the helper binary (raises
exceptions on failure).*

- helper.action_shutdown()
- helper.cmd_status()
- ...

*Manually send a command to the helper binary (returns '0 (COMMAND)' on
success, NO exception raised on failure).*

- response = helper.send("SHUTDOWN")

*If you are done, logout and close the socket connection.*

- helper.cmd_logout()

*Login method is only really needed, when we first logged out, but the
HelperManager instance is still used.*

- helper.cmd_login()

*Context manager usage (automatically logs in and logs out).*

- with helper.HelperManager() as helper:
-     helper.action_shutdown()
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-11-19"
__status__ = "Prototype/Development/Production"

# Imports.
import random
import socket
import logging
import base64
import hmac
import hashlib
import os
import struct
import time
import traceback
import re
import sys
from collections import deque
from functools import wraps
from pathlib import Path

import keyring as kr
from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import HKDF
from Cryptodome.Hash import SHA256
from PySide6.QtCore import (QMutex, QObject, QRunnable, QThread, QThreadPool,
                            QWaitCondition, Qt, Signal, Slot)
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QFileDialog,
                               QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QMessageBox, QPushButton,
                               QSizePolicy,
                               QSpacerItem,
                               QDialog,
                               QVBoxLayout, QWidget)

from swiftguard.constants import C
from swiftguard.constants import get_size
from swiftguard.init import exceptions as exc, models
from swiftguard.utils import helpers, process

# Child logger.
LOGGER = logging.getLogger(__name__)


class PathSelector(QDialog):
    """
    PathSelector: Dialog for selecting files and folders to shred.
    """

    _file_size_cache = {}

    class SizeCalculator(QRunnable):
        """
        SizeCalculator: Runnable for calculating the total size of
        files and folders in a separate thread.
        """

        class Signals(QObject):
            """
            Signals for the SizeCalculator runnable.
            """
            size_calculated = Signal(float)

        def __init__(self, paths: list[Path]) -> None:
            """
            Runnable for calculating the total size of files and folders
            in a separate thread.

            :param paths: List of paths to calculate the total size of.
            :type paths: list[Path]
            :return: None
            """

            super().__init__()
            self.paths = paths
            self.signals = self.Signals()
            self._is_running = True

        def run(self) -> None:
            """
            Calculate the total size of all paths and emit the signal.

            :return: None
            """

            total_size = 0
            for path in self.paths:
                if not self._is_running:
                    return
                total_size += self._get_size(path)

            try:
                self.signals.size_calculated.emit(total_size)
            except RuntimeError:
                pass

        def stop(self):
            """
            Stop the size calculation.

            :return: None
            """

            self._is_running = False

        def _get_size(self, path: Path) -> int:
            """
            Get the total size of a given path in bytes. The size is cached
            to speed up the process. If the path is a directory, the total
            size of all files in the directory and most of its
            subdirectories is calculated (limited to 20 per default).

            :param path: Given path of file or folder to get the size of.
            :type path: Path
            :return: The total size of the given path in bytes.
            :rtype: int
            """

            if path in PathSelector._file_size_cache:
                return PathSelector._file_size_cache[path]

            if not os.path.exists(path):
                return 0

            total_size = 0

            if os.path.isfile(path):
                total_size = os.stat(path, follow_symlinks=False).st_size
            else:
                stack = [path]

                while stack:
                    if not self._is_running:
                        return 0
                    current_path = stack.pop()
                    try:

                        with os.scandir(current_path) as it:
                            for entry in it:
                                if not self._is_running:
                                    return 0
                                try:
                                    if entry.is_dir(follow_symlinks=False):
                                        stack.append(entry.path)
                                    elif entry.is_file(follow_symlinks=False):
                                        total_size += entry.stat().st_size
                                except OSError:
                                    pass
                    except OSError:
                        pass

            PathSelector._file_size_cache[path] = total_size

            return total_size

    def __init__(self) -> None:
        """
        Initialize the PathSelector dialog.

        :return: None
        """

        super().__init__()
        self.setWindowTitle("Files and Folders to Shred")

        self._shred_paths = []

        self.setFixedSize(650, 465)
        # self.setGeometry(0, 0, 600, 400)
        # self.setMinimumSize(600, 400)

        # Move to center of the screen.
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        description_label = QLabel(
                "<center>The files and folders listed below will be "
                "permanently and "
                "securely deleted in case of a detected tampering event "
                "and shredding is activated. "
                "In case of defusing the alarm, no data will be lost."
                "<br><br>"
                "<b><span style='color: red;'>Warning: </span></b>"
                "Files cannot be recovered after shredding, even "
                "with the use of forensic tools!"
                "<br></center>"
                )
        description_label.setTextFormat(Qt.TextFormat.RichText)
        description_label.setWordWrap(True)
        self.layout.addWidget(description_label)

        self.path_list = QListWidget()
        self.layout.addWidget(self.path_list)

        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.clicked.connect(self._add_folder)
        self.button_layout.addWidget(self.add_folder_button)

        self.add_file_button = QPushButton("Add Files")
        self.add_file_button.clicked.connect(self._add_file)
        self.button_layout.addWidget(self.add_file_button)

        # Spacer item to push buttons to the right.
        spacer = QSpacerItem(40, 20,
                             QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Minimum
                             )
        self.button_layout.addItem(spacer)

        self.size_label = QLabel("Total size: 0 B")
        self.button_layout.addWidget(self.size_label)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        self.button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.button_layout.addWidget(self.cancel_button)

        # Load shred paths from configuration.
        self.warning_showed = False
        if C.cfg.CFG["shred_paths"]:
            for path in C.cfg.CFG["shred_paths"]:
                self._add_path(Path(path))

    def _update_file_sizes(self) -> None:
        """
        Check the total size of all paths and display it in the window.
        Over 5 GB in total we also display a warning, that shredding
        will probably take a long time. The size is calculated in a
        separate thread to not block the GUI.
        Displayed file size is color coded:
        < 500 MB -> White/Black,
        < 5 GB -> Yellow,
        > 5 GB -> Red.

        :return: None
        """

        # Check if the size calculator is already running.
        # If so, stop it and start a new one.
        if hasattr(self, "size_calculator"):
            self.size_calculator.stop()

        self.size_calculator = PathSelector.SizeCalculator(self._shred_paths)
        self.size_calculator.signals.size_calculated.connect(
                self._on_size_calculated
                )
        QThreadPool.globalInstance().start(self.size_calculator)

    def _on_size_calculated(self, total_size) -> None:
        """
        Update the size label with the calculated total size and color
        code it based on the size.

        :param total_size: The total size of all paths in bytes.
        :type total_size: int
        :return: None
        """

        total_size_frmt, unit = get_size(total_size).split(maxsplit=1)
        approx_sign = "~" if total_size > 0 else ""
        self.size_label.setText(
                f"Total size: {approx_sign} {total_size_frmt} {unit}"
                )

        # > 5 GB -> Red font and warning displayed.
        if total_size > 5 * 1024 * 1024 * 1024:
            if self.size_label.styleSheet() != "color: red;":
                self.size_label.setStyleSheet("color: red;")

                # Display warning only if user adds a new path.
                # Not for already existing paths in the config.
                if not self.warning_showed:
                    QMessageBox.warning(
                            self,
                            "Warning",
                            f"The total size of the selected files is "
                            f"larger than {total_size_frmt} {unit}. Shredding "
                            f"will take some time."
                            )
                    self.warning_showed = True

        # > 500 MB -> Yellow font.
        elif total_size > 500 * 1024 * 1024:
            self.size_label.setStyleSheet("color: #FFC846;")
        else:
            self.size_label.setStyleSheet("")

    # def _update_file_sizes_blocking(self) -> None:
    #     """
    #     Check the total size of all paths and display it in the window.
    #     Over 5 GB in total we also display a warning, that shredding
    #     will probably take a long time. The size is calculated in the
    #     main thread and blocks the GUI.
    #     Displayed file size is color coded:
    #     < 500 MB -> White/Black,
    #     < 5 GB -> Yellow,
    #     > 5 GB -> Red.
    #
    #     :return: None
    #     """
    #
    #     total_size = sum(self.SizeCalculator()._get_size(path) for path in
    #                      self._shred_paths
    #                      )
    #     size_no, unit = re.match(
    #             r"(\d+)([A-Za-z]+)",
    #             get_size(total_size)
    #             ).groups()
    #     self.size_label.setText(f"Total size: ~ {size_no} {unit}")
    #
    #     # > 5 GB -> Red size and warning displayed.
    #     if total_size > 5 * 1024 * 1024 * 1024:
    #         if self.size_label.styleSheet() != "color: red;":
    #             QMessageBox.warning(
    #                     self,
    #                     "Warning",
    #                     f"The total size of the selected files is "
    #                     f"larger than {size_no} {unit}. Shredding might
    #                     take "
    #                     f"a long time."
    #                     )
    #
    #         self.size_label.setStyleSheet("color: red;")
    #
    #     elif total_size > 500 * 1024 * 1024:  # > 500 MB -> Yellow.
    #         self.size_label.setStyleSheet("color: #FFD700;")
    #     else:
    #         self.size_label.setStyleSheet("")  # < 500 MB: Default.

    def _add_folder(self) -> None:
        """
        Open a system file dialog to select a folder to shred.

        :return: None.
        """

        folder = QFileDialog.getExistingDirectory(self, "Select Folder",
                                                  str(Path.home())
                                                  )
        if folder:
            self._add_path(Path(folder))

    def _add_file(self) -> None:
        """
        Open a system file dialog to select files to shred.

        :return: None.
        """

        files, _ = QFileDialog.getOpenFileNames(self, "Select Files",
                                                str(Path.home()),
                                                "All Files (*)"
                                                )
        for file in files:
            self._add_path(Path(file))

    def _add_path(self, path: Path) -> None:
        """
        Add a given Path object to the displayed list of shred paths
        in the path selector dialog. Also validates that the path is
        not already in the list. Also adds the path to the internal
        list of shred paths, which is returned when the path selector
        dialog is accepted.

        :param path: The path to add to the list.
        :type path: Path
        :return: None
        """

        path_str = str(path)

        # Check if path is already in the list.
        for index in range(self.path_list.count()):
            item = self.path_list.item(index)
            widget = self.path_list.itemWidget(item)
            path_label = widget.findChild(QLabel)
            if len(path_str) > 67:
                path_str = "... " + path_str[-(67 - 3):]
            if path_label.text() == path_str:
                return

        item = QListWidgetItem()
        widget = QWidget()
        layout = QHBoxLayout()

        # Path label overflow -> Abbreviate path from left side.
        if len(path_str) > 67:
            path_str = "... " + path_str[-(67 - 3):]

        path_label = QLabel(path_str)
        path_label.setWordWrap(False)
        path_label.setSizePolicy(QSizePolicy.Policy.Ignored,
                                 QSizePolicy.Policy.Preferred
                                 )
        path_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                )

        # Check if the path exists and apply strikethrough if it doesn't.
        if not path.exists():
            path_label.setStyleSheet(
                    "text-decoration: line-through; color: #50505e;"
                    )

        layout.addWidget(path_label, 4)
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self._remove_path(item))
        layout.addWidget(remove_button, 1)
        layout.setContentsMargins(10, 0, 10, 0)
        widget.setLayout(layout)
        item.setSizeHint(widget.sizeHint())
        self.path_list.addItem(item)
        self.path_list.setItemWidget(item, widget)

        # Add path to internal list of shred paths.
        self._shred_paths.append(path)

        self._update_file_sizes()

    def _remove_path(self, item: QListWidgetItem) -> None:
        """
        Remove a given item from the displayed list of shred paths
        in the path selector dialog. Also removes the path from the
        internal list of shred paths.

        :param item: The item to remove from the list.
        :type item: QListWidgetItem
        :return: None
        """

        widget = self.path_list.itemWidget(item)
        path_label = widget.findChild(QLabel)
        path_str = path_label.text()

        # Remove path from internal list.
        # Need an approximate match, as the path might be abbreviated.
        full_path = next((p for p in self._shred_paths if
                          str(p).endswith(path_str.replace("... ", ""))), None
                         )
        if full_path:
            self._shred_paths.remove(full_path)

        # Remove path from the displayed list.
        row = self.path_list.row(item)
        self.path_list.takeItem(row)

        self._update_file_sizes()

    def exec(self) -> list[Path] | None:
        """
        Execute the path selector dialog and return the list of shred
        paths if the dialog was accepted. If the dialog was canceled,
        return None. It also clears the file size cache.

        :return: List of shred paths or None.
        :rtype: list[Path] | None
        """

        result = super().exec()
        self._file_size_cache.clear()

        if hasattr(self, "size_calculator"):
            self.size_calculator.stop()

        if result == QDialog.DialogCode.Accepted:
            return self._shred_paths

        else:
            return None


class HelperManager(QThread, metaclass=models.SingletonQt):
    """
    HelperManager: Singleton class for managing the helper binary.

    The HelperManager class is a singleton class that manages the helper
    binary. It is responsible for starting the binary, logging in,
    sending encrypted and signed messages, and stopping the binary.

    :ivar _nonce_window: A deque to store the last 5000 nonces.
    :type _nonce_window: deque
    :ivar _socket: The UNIX socket connection to the helper binary.
    :type _socket: socket.socket | None
    :ivar _key_enc: The encryption key (32 bytes, base64 encoded).
    :type _key_enc: bytes | None
    :ivar _key_sig: The signing key (32 bytes, base64 encoded).
    :type _key_sig: bytes | None
    """

    # Signals from thread state.
    running_sig: Signal = Signal(bool)
    status_sig: Signal = Signal(bool)
    error_sig: Signal = Signal(Exception)

    def __init__(self) -> None:
        """
        If the binary is not running, it will be started automatically.
        The keys for encryption and signing messages are derived from
        the master key stored in the keyring. The socket connection is
        established and the LOGIN command is sent. Now the instance is
        ready for use.

        To securely send and receive encrypted and signed messages over
        the UNIX socket, use the 'send' instance method or even better
        the convenience methods:
            - cmd_login (called in __init__)
            - cmd_logout (disconnects and logs out)
            - cmd_exit (stops the helper binary)
            - action_shutdown (shutdown the host)
            - action_hibernate (hibernate the host)
            - action_shred (shred files)
            - cmd_status (binary ready?)
            - cmd_version (cmd_version string of binary)

        :raises HelperNotStartedError: If binary could not be started.
        :raises LoginFailedError: If the login failed for any reason.
        :return: None
        """

        super().__init__()

        self._nonce_window: deque = deque(maxlen=C.helper.MAX_NONCES)

        self._socket: socket.socket | None = None
        self._key_enc: bytes | None = None
        self._key_sig: bytes | None = None

        # Thread management and communication.
        self.thread_id: str | None = None
        self.running: bool = False
        self.status: bool | None = None
        self.error: Exception | None = None
        self.mutex: QMutex = QMutex()
        self.condition: QWaitCondition = QWaitCondition()

        # Start the run method/thread. Starts the helper binary and
        # login. The login also ensures that the binary is installed and
        # running.
        self.start()

    def __enter__(self):
        """
        Enter method: Create instance, which automatically starts the
        binary and logs in. Called when entering a context manager.

        :return: The current instance of the HelperManager.
        :rtype: HelperManager
        """

        return self

    def __exit__(
            self,
            exc_type: type,
            exc_value: Exception,
            tb: traceback,
            ):
        """
        Exit method: Logout and close the socket connection. Called when
        exiting a context manager.

        :param exc_type: The exception type.
        :type exc_type: type
        :param exc_value: The exception value.
        :type exc_value: Exception
        :param tb: The traceback.
        :type tb: traceback
        :return: None
        """

        if self._socket:
            self.cmd_logout()

    def _thread_id(self) -> str:
        """
        Get the thread ID of the worker and verify we are not running in
        the main thread, as this would block the GUI.

        :return: Unique thread ID.
        :rtype: str
        """

        # Worker in main thread is a critical blocking issue.
        if QThread.currentThread() is QGuiApplication.instance().thread():
            raise exc.BlockingMainThreadError(
                    f"{self.__class__.__qualname__} thread is running in the "
                    f"main thread and thus blocking the GUI!"
                    )

        try:
            return (str(QThread.currentThread()
                        ).split(sep=f"{self.__class__.__name__}(0x",
                                maxsplit=1,
                                )[1].split(sep=") at",
                                           maxsplit=1,
                                           )[0])

        except Exception as e:
            LOGGER.error(
                    f"Could not get the {self.__class__.__qualname__} thread "
                    f"ID. Generating random ID. "
                    f"{e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )
            return f"30000{random.randint(1000000, 9999999)}"

    @Slot()
    def run(self) -> None:
        """
        The main thread method for the QThread. It is responsible for
        establishing a connection to the helper binary, logging in and
        continuously checking the status/health of the binary.

        :return: None
        """

        self.running = True
        self.running_sig.emit(True)
        self.thread_id = self._thread_id()

        LOGGER.info(f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"started and is now establishing a connection to the "
                    f"helper."
                    )

        # We try two times to establish a connection to the helper.
        for i in range(2):
            try:
                if not self._socket and self.running:
                    self.cmd_login()
                    self.status = self.cmd_status()
                    self.status_sig.emit(self.status)

                while self.running:
                    self.mutex.lock()
                    self.condition.wait(self.mutex, (10 * 1000))  # 10 secs.
                    self.mutex.unlock()

                    if not self.running:
                        break

                    self.status = self.cmd_status()
                    self.status_sig.emit(self.status)

                break

            except Exception as e:

                # First critical issue -> We try one more time.
                if i == 0:
                    LOGGER.error(
                            "Helper status check failed. Trying one more time"
                            )

                    continue

                LOGGER.critical(
                        f"{self.__class__.__qualname__} (ID: "
                        f"{self.thread_id}) found a critical issue. "
                        f"Stopping the thread."
                        )
                LOGGER.critical(f"{e.__class__.__name__}: {e} \n"
                                f"{traceback.format_exc()}"
                                )

                if self._socket:
                    try:
                        self.cmd_logout()
                    except Exception as _:
                        pass

                self.running = False
                self.running_sig.emit(False)
                self.status = False
                self.status_sig.emit(False)
                self.error = e
                self.error_sig.emit(e)

    def stop(self) -> None:
        """
        Stop the QThread and close the socket connection.

        :return: None
        """

        if not self.running:
            LOGGER.info(
                    f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"is not running, but stopping was requested."
                    )
            return

        # Stop the socket connection and wake up the thread.
        self.running = False
        self.running_sig.emit(False)
        self.status = None

        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()

        if self._socket:
            try:
                self.cmd_logout()
            except Exception as _:
                pass

        LOGGER.info(
                f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                f"was stopped and the connection was closed."
                )

        # Wait for the thread to finish.
        self.quit()
        self.wait()

    @staticmethod
    def ensure_logged_in(f: callable) -> callable:
        """
        Decorator to ensure that the HelperManager instance is logged in
        and the QThread for continuous socket connection and status
        updates is running.

        :param f: The function to ensure the login for to wrap.
        :type f: callable
        :return: The wrapped function.
        :rtype: callable
        """

        @wraps(f)
        def wrapper(self, *args, **kwargs) -> any:
            """
            Wrapper function for the decorated function.

            :param self: The HelperManager instance.
            :type self: HelperManager
            :param args: Arguments for the wrapped function.
            :type args: list
            :param kwargs: Keyword arguments for the wrapped function.
            :type kwargs: dict
            :return: The result of the wrapped function.
            :rtype: any
            """

            if not self.running:
                LOGGER.info(
                        f"{self.__class__.__qualname__} thread is not "
                        f"running! Starting now. Then executing "
                        f"{f.__name__}()."
                        )
                self.start()
                QThread.msleep(100)

            return f(self, *args, **kwargs)

        return wrapper

    @property
    def binary_installed(self):
        """
        Check if the helper, its wrapper binary and all their
        dependencies are fully installed.

        :return: True if the binary is installed, False otherwise.
        :rtype: bool
        """

        required_files = (
                C.helper.BINARY_PATH,
                C.helper.WRAPPER_PATH,
                C.helper.LAUNCH_AGENT_WRAPPER_DEST,
                C.helper.SUDOERS_PATH,
                )

        if not all(file.exists(follow_symlinks=True)
                   for file in required_files
                   ):
            return False

        res = process.Process(
                binary_path="/bin/launchctl",
                args=("list",),
                timeout=5,
                blocking=True,
                ).run()

        if res.return_code != 0:
            return False

        if not any(C.helper.WRAPPER_PATH.name in line
                   for line in res.stdout.split("\n")
                   ):
            return False

        return True

    @property
    def binary_running(self) -> bool:
        """
        Check if the helper binary is running and has root privileges.

        :return: True if the binary is running, False otherwise.
        :rtype: bool
        """

        res = process.Process(
                binary_path="/usr/bin/pgrep",
                args=("-x",
                      C.helper.BINARY_PATH.name),
                timeout=5,
                blocking=True,
                ).run()

        if res.return_code != 0:
            return False

        # Check for each PID if the process is run by root.
        for pid in res.stdout.split(maxsplit=1):
            res2 = process.Process(
                    binary_path="/bin/ps",
                    args=("-o",
                          "user=",
                          "-p",
                          pid),
                    timeout=5,
                    blocking=True,
                    ).run()

            if res2.stdout.strip() != "root":
                return False

        return True

    @property
    def max_socket_size(self) -> int:
        """
        Get the maximum socket buffer size for sending and receiving.

        :return: The maximum socket buffer size in bytes.
        :rtype: int
        """

        return self._socket.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_SNDBUF
                )

    @staticmethod
    def _derive_keys(master_key: bytes) -> tuple[bytes, bytes]:
        """
        Derives two keys from a master key using HKDF with SHA256.

        :param master_key: The master key (32 bytes, base64 encoded).
        :type master_key: bytes
        :return: The first and second derived key (32 bytes each).
        :rtype: tuple[bytes, bytes]
        """

        # Derive the first key.
        key1: bytes = HKDF(master=master_key,
                           key_len=32,
                           salt=C.sec.PEPPER,
                           hashmod=SHA256,
                           context=b'key_enc'
                           )

        # Derive the second key.
        key2: bytes = HKDF(master=master_key,
                           key_len=32,
                           salt=C.sec.PEPPER,
                           hashmod=SHA256,
                           context=b'key_sig'
                           )

        return key1, key2

    @staticmethod
    def _remove_redundancy(paths: list[str]) -> list[str]:
        """
        Removes redundant paths from the list.

        Example:
        If a directory and one or more files within that directory are
        provided, the files are removed since the directory already
        contains all the files.

        :param paths: List of paths.
        :type paths: list[str]
        :return: Cleaned list of paths without redundancies.
        :rtype: list[str]
        """

        cleaned_paths = []
        for path in paths:
            if not any(
                    other != path
                    and path.startswith(other)
                    for other in paths
                    ):
                cleaned_paths.append(path)

        return cleaned_paths

    def _start_binary(self):
        """
        Start the helper binary using launchctl.

        :raises HelperNotStartedError: If binary could not be started.
        :return: None
        """

        if self.binary_running:
            LOGGER.info("Helper binary is already running!")
            return

        # Binary not running -> Start it and wait 15 seconds for it.
        process.Process(
                binary_path="/bin/launchctl",
                args=("start",
                      C.helper.WRAPPER_PATH.name),
                timeout=5,
                blocking=True,
                ).run()

        for i in range(15):
            time.sleep(1)
            if self.binary_running:

                # Wait 60 seconds for the binary to get permissions from
                # user to create socket -> Fully initialized.
                for j in range(60):
                    time.sleep(1)
                    if C.helper.SOCKET_PATH.exists():
                        LOGGER.info("Helper binary was started "
                                    "and initialized successfully!"
                                    )
                        return

                LOGGER.error("Helper binary was started but not given "
                             "full permissions to run!"
                             )
                break

        # If after 15 seconds the binary is still not running, we
        # raise an exception.
        raise exc.HelperNotStartedError(
                "Helper binary could not be started!"
                )

    def _nonce_reused(self, nonce: bytes) -> bool:
        """
        Checks if a nonce has been used before (within last 5000 nonces).

        :param nonce: The nonce to check.
        :type nonce: bytes
        :return: True if the nonce has been used before, False otherwise.
        :rtype: bool
        """

        return nonce in self._nonce_window

    def _add_nonce(self, nonce: bytes) -> None:
        """
        Adds a nonce to the nonce window. No need to check if deque
        is full, as it is automatically handled by its 'maxlen' param.

        :param nonce: The nonce to add.
        :type nonce: bytes
        :return: None
        """

        self._nonce_window.append(nonce)

    def _generate_nonce(self) -> bytes:
        """
        Generates a new nonce (96 bit) for AES GCM mode encryption.
        It is guaranteed to be unique and not used before.

        :return: The nonce (12 bytes).
        :rtype: bytes
        """

        while True:
            nonce: bytes = os.urandom(C.helper.AES_IVLEN)

            # Generate a new nonce if it has been used before.
            if not self._nonce_reused(nonce=nonce):
                return nonce

    def _encrypt_message(
            self,
            message: str,
            key_enc: bytes = None,
            key_sig: bytes = None,
            ) -> bytes:
        """
        Encrypts a message using AES GCM mode, adds an HMAC (256 bit) for
        integrity, adds a nonce (96 bit), timestamps the message (64 bit),
        and returns the encrypted message. If no encryption and signing
        keys are provided, the instance keys are used.

        :param key_enc: The encryption key (32 bytes, base64 encoded).
        :type key_enc: bytes | None
        :param key_sig: The signing key (32 bytes, base64 encoded).
        :type key_sig: bytes | None
        :param message: The message to encrypt.
        :type message: str
        :return: The encrypted message (base64 encoded), ready to be sent.
        :rtype: bytes
        """

        # Use the instance keys if none are provided.
        if key_enc is None and key_sig is None:
            key_enc = self._key_enc
            key_sig = self._key_sig

            if key_enc is None or key_sig is None:
                raise RuntimeError("No keys provided or found in instance!")

        # Get the current timestamp
        timestamp: int = int(time.time())

        nonce: bytes = self._generate_nonce()
        self._add_nonce(nonce=nonce)

        # Initialize AES in GCM mode with the nonce.
        cipher = AES.new(
                key=key_enc,
                mode=AES.MODE_GCM,
                nonce=nonce
                )

        # Encrypt the message.
        ciphertext, tag = cipher.encrypt_and_digest(message.encode())

        hmac_input: bytes = (struct.pack(">Q", timestamp)
                             + nonce
                             + ciphertext
                             + tag)

        # Generate HMAC for integrity (using the concatenation of nonce,
        # ciphertext, and tag).
        hmac_message: bytes = hmac.new(
                key=key_sig,
                msg=hmac_input,
                digestmod=hashlib.sha256,
                ).digest()

        # Pack the data (timestamp, nonce, ciphertext, tag, HMAC)
        encrypted_message: bytes = hmac_input + hmac_message

        # Return the base64 encoded encrypted message.
        return base64.b64encode(encrypted_message)

    def _decrypt_message(
            self,
            encrypted_message: bytes,
            key_enc: bytes = None,
            key_sig: bytes = None,
            ) -> str:
        """
        Decrypts a message using AES GCM mode, verifies the HMAC
        (256 bit) for integrity, checks the nonce (96 bits) for reuse,
        and validates the timestamp (64 bits) for a maximum deviation of
        2 seconds (TTL). If no encryption and signing keys are provided,
        the instance keys are used.

        :param encrypted_message: Encrypted message (base64 encoded).
        :type encrypted_message: bytes
        :param key_enc: The encryption key (32 bytes, base64 encoded).
        :type key_enc: bytes
        :param key_sig: The signing key (32 bytes, base64 encoded).
        :type key_sig: bytes
        :raises LoginFailedError: If no keys are provided or found.
        :raises HMACFailedError: If the HMAC verification fails.
        :raises NonceReusedError: If the nonce was reused.
        :raises TTLExpiredError: If timestamp deviation was too high.
        :return: Decrypted message.
        :rtype: str
        """

        # Use the instance keys if none are provided.
        if key_enc is None and key_sig is None:
            key_enc = self._key_enc
            key_sig = self._key_sig

            if key_enc is None or key_sig is None:
                raise exc.LoginFailedError(
                        "No keys provided or found in instance!"
                        )

        # Base64 decode the encrypted message.
        try:
            encrypted_message: bytes = base64.b64decode(encrypted_message)
        except Exception as e:
            raise exc.HelperError(
                    f"Base64 decoding failed! Probably it is a unencrypted "
                    f"error message: {e.__class__.__name__}: {e}"
                    )

        # Extract the timestamp, nonce, ciphertext, tag, and HMAC.
        timestamp: int = struct.unpack(">Q", encrypted_message[:8])[0]
        nonce: bytes = encrypted_message[8:20]
        ciphertext: bytes = encrypted_message[20:-48]
        tag: bytes = encrypted_message[-48:-32]
        received_hmac: bytes = encrypted_message[-32:]

        # Verify the HMAC for integrity.
        hmac_input: bytes = encrypted_message[:-32]
        expected_hmac: bytes = hmac.new(
                key_sig,
                hmac_input,
                hashlib.sha256
                ).digest()
        if not hmac.compare_digest(received_hmac, expected_hmac):
            raise exc.HMACFailedError("HMAC verification failed! "
                                      "Message integrity compromised."
                                      )

        # Check the timestamp for a maximum deviation.
        current_timestamp: int = int(time.time())
        if abs(current_timestamp - timestamp) > C.helper.TTL:
            raise exc.TTLExpiredError(
                    f"Message expired by "
                    f"{abs(current_timestamp - timestamp)} s "
                    f"(Max: {C.helper.TTL} s)."
                    f"Message integrity compromised."
                    )

        if self._nonce_reused(nonce=nonce):
            raise exc.NonceReusedError(
                    "Nonce has been used before! "
                    "Message integrity compromised."
                    )

        self._add_nonce(nonce=nonce)

        # Initialize AES in GCM mode with the nonce.
        cipher = AES.new(key=key_enc,
                         mode=AES.MODE_GCM,
                         nonce=nonce
                         )

        # Decrypt the ciphertext.
        decrypted_message: bytes = cipher.decrypt_and_verify(
                ciphertext=ciphertext,
                received_mac_tag=tag,
                )

        return decrypted_message.decode()

    def _chunkify_paths(
            self,
            file_list: list[str],
            command_str: str,
            ) -> list[list[str]]:
        """
        Split the list of files into chunks based on the maximum socket
        buffer size, so we do not overflow the buffer.

        :param file_list: List of base64 encoded file paths.
        :type file_list: list[str]
        :param command_str: The command string to send, e.g. 'SHRED'.
            Important for calculating the total size of the message.
        :type command_str: str
        :return: List of file chunks.
        :rtype: list[list[str]]
        """

        chunks = []
        current_chunk = []

        for file in file_list:
            if current_chunk:
                new_str_len = len(
                        f"{command_str} "
                        f"{'|'.join(current_chunk + [file])}".encode(
                                "utf-8"
                                )
                        )

                if new_str_len > (self.max_socket_size - 256):
                    chunks.append(current_chunk)
                    current_chunk = [file]
                else:
                    current_chunk.append(file)
            else:
                current_chunk.append(file)

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def send(self, command: str) -> str:
        """
        Send a command to the helper binary. If the socket is not
        connected, login first. Send the encrypted message and receive
        the response. If a broken pipe or connection reset occurs,
        reconnect and try again.

        :param command: The command to send (e.g. 'SHUTDOWN', ...).
        :type command: str
        :raises ActionFailedError: If the action failed (SHUTDOWN, ...).
        :raises CommandFailedError: If the command failed (STATUS, ...).
        :return: The response from the helper binary.
        :rtype: str
        """

        # If the socket is not connected, login first.
        if not self._socket:
            LOGGER.info("Socket not connected, logging in now.")
            self.cmd_login()

        # Send the encrypted message and receive the response.
        try:
            self._socket.sendall(self._encrypt_message(message=command))
            response: bytes = self._socket.recv(1024)

        # Maybe a broken pipe or connection reset occurred -> reconnect.
        except Exception as e:
            LOGGER.error(f"Connection error occurred "
                         f"({e.__class__.__name__}: {e})! "
                         f"Reconnecting ... \n"
                         f"{traceback.format_exc()}"
                         )
            self._socket.close()
            self._socket = None
            QThread.sleep(1)

            try:
                # Login again.
                self.cmd_login()

                # Send the command again.
                self._socket.sendall(self._encrypt_message(message=command))
                response: bytes = self._socket.recv(1024)

            # We give up after the second try.
            except Exception as e:

                if (command in ("HIBERNATE", "SHUTDOWN")
                        or command.startswith("SHRED")):
                    raise exc.ActionFailedError(
                            f"Reconnecting try failed too! Giving up. "
                            f"({e.__class__.__name__}: {e}) \n"
                            f"{traceback.format_exc()}"
                            )
                else:
                    raise exc.CommandFailedError(
                            f"Reconnecting try failed too! Giving up."
                            f"({e.__class__.__name__}: {e}) \n"
                            f"{traceback.format_exc()}"
                            )

        # Try to decrypt the response.
        try:
            response_dec: str = self._decrypt_message(
                    encrypted_message=response, )

        # Failed -> we got an error code (unencrypted).
        except Exception as e:
            LOGGER.error(f"Decryption failed. Response: {response}, "
                         f"Exception: {e.__class__.__name__}: {e} \n"
                         f"{traceback.format_exc()}"
                         )
            response_dec: str = response.decode()

        LOGGER.debug(f"Sent: {command}, Response: {response}")

        return response_dec

    @ensure_logged_in
    def cmd_login(self) -> None:
        """
        Login to the helper binary by sending the LOGIN command. First,
        we start the binary if it is not running. Then, we extract the
        key from the keyring, derive the encryption and signing keys.
        After connecting to the socket and sending the LOGIN message,
        we receive the response and check if the login was successful.

        :raises LoginFailedError: If the command failed for any reason.
        :return: None
        """

        # Check if we are already logged in.
        if self._socket:
            LOGGER.info("Helper already logged in!")
            return

        # Check if the binary is installed.
        if not self.binary_installed:
            LOGGER.info("Helper binary is not installed! Installing now.")
            self.install()

        # Start the helper binary if it is not running.
        if not self.binary_running:
            LOGGER.info("Helper binary is not running! Starting now.")
            self._start_binary()

        # Check if the socket file exists.
        if not C.helper.SOCKET_PATH.exists():
            raise exc.LoginFailedError(
                    "Helper login failed! Socket not found."
                    )

        # Extract the key from the keyring and base64 decode it.
        try:
            key: bytes = base64.b64decode(
                    kr.get_password(
                            service_name=C.helper.KEY_SERVICE,
                            username=C.helper.KEY_USER,
                            )
                    )

        # Key not found in keyring.
        except Exception:
            try:
                # Maybe the key was deleted or the keyring is locked.
                # -> Restart the helper.
                LOGGER.error("Key not found in keyring! Restarting helper.")

                process.Process(
                        binary_path="/bin/launchctl",
                        args=("stop",
                              C.helper.WRAPPER_PATH.name),
                        timeout=5,
                        blocking=True,
                        ).run()

                time.sleep(3)

                process.Process(
                        binary_path="/bin/launchctl",
                        args=("start",
                              C.helper.WRAPPER_PATH.name),
                        timeout=5,
                        blocking=True,
                        ).run()

                time.sleep(3)

                key: bytes = base64.b64decode(
                        kr.get_password(
                                service_name=C.helper.KEY_SERVICE,
                                username=C.helper.KEY_USER,
                                )
                        )

            # We give up here.
            except Exception:
                raise exc.LoginFailedError(
                        "Helper login failed! Key not found in keyring."
                        )

        # print("Key:", base64.b64encode(key))
        # print("Key hex:", key.hex())

        # Derive the encryption and signing keys from the master key.
        self._key_enc, self._key_sig = self._derive_keys(key)

        # Connect to the socket and set a timeout of 5 seconds.
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(str(C.helper.SOCKET_PATH))
        self._socket.settimeout(5)

        # After connecting, we have 2 seconds to send the login message.
        try:
            self._socket.sendall(self._encrypt_message(message="LOGIN", ))
            login_res: bytes = self._socket.recv(1024)

        except Exception as e:
            self._socket.close()
            self._socket = None

            if isinstance(e, BrokenPipeError):
                raise exc.LoginFailedError(
                        f"Helper login failed (Broken pipe)! "
                        f"Connection closed."
                        )

            raise exc.LoginFailedError(
                    f"Helper login failed! ({e.__class__.__name__}: {e})"
                    )

        try:
            login_res_dec: str = self._decrypt_message(
                    encrypted_message=login_res
                    )

        # Login failed, we get the response unencrypted.
        except exc.HelperError:
            login_res_dec: str = login_res.decode()

        LOGGER.debug(f"Login response: '{login_res_dec}' (raw: '{login_res}')")

        if login_res_dec != "0 (LOGIN)":
            self._socket.close()
            self._socket = None
            raise exc.LoginFailedError(f"Helper login failed with "
                                       f"'{login_res_dec}'! "
                                       "Connection closed."
                                       )

        LOGGER.info("Helper login successful!")

    def cmd_logout(self) -> None:
        """
        Send the LOGOUT command to the helper binary -> Logout the user
        and close the socket. Suppresses any exceptions and errors that
        might occur during the logout process, but logs them.

        :return: None
        """

        if not self._socket:
            LOGGER.info("Helper already logged out!")
            return

        try:
            resp: str = self.send(command="LOGOUT")

        except exc.HelperError as e:
            LOGGER.warning(
                    f"Helper logout failed! (Exception: "
                    f"{e.__class__.__name__}: {e}) \n"
                    f"{traceback.format_exc()}"
                    )

        else:
            if resp != "0 (LOGOUT)":
                LOGGER.warning(f"Helper logout failed! (Response: {resp})")

            LOGGER.info("Helper logout successful!")

        finally:
            self._socket.close()
            self._socket = None

    @ensure_logged_in
    def cmd_exit(self) -> None:
        """
        Send the EXIT command to the helper binary -> Stop the helper
        binary and close the socket.

        :raises CommandFailedError: If the EXIT command failed.
        :return: None
        """

        resp: str = self.send(command="EXIT")

        if resp != "0 (EXIT)":
            raise exc.CommandFailedError(
                    f"EXIT command returned with: '{resp}'"
                    )

        self._socket.close()
        self._socket = None

        LOGGER.info("Stopped the helper binary.")

    @ensure_logged_in
    def action_shutdown(self) -> None:
        """
        Send the SHUTDOWN command to the helper binary -> Shutdown the
        host system.

        :raises ActionFailedError: If the SHUTDOWN action failed.
        :return: None
        """

        resp: str = self.send(command="SHUTDOWN")

        if resp != "0 (SHUTDOWN)":
            raise exc.ActionFailedError(
                    f"SHUTDOWN action returned with: '{resp}'"
                    )

        LOGGER.info("SHUTDOWN command was successfully executed")

    @ensure_logged_in
    def action_hibernate(self) -> None:
        """
        Send the HIBERNATE command to the helper binary -> Hibernate the
        host system.

        :raises ActionFailedError: If the HIBERNATE action failed.
        :return: None
        """

        resp: str = self.send(command="HIBERNATE")

        if resp != "0 (HIBERNATE)":
            raise exc.ActionFailedError(
                    f"HIBERNATE action returned with: '{resp}'"
                    )

        LOGGER.info("HIBERNATE command was successfully executed.")

    @ensure_logged_in
    def action_shred(self) -> None:
        """
        Shred the provided files and folders using the helper binary.
        It takes the paths from the config file, removes redundancies,
        encodes them to base64, and sends them in chunks to the helper
        binary. The helper binary will overwrite the files and folders
        with random data and then securely delete them.

        :raises ActionFailedError: If the SHRED action failed completely
            for one or more file chunks.
        :return: None
        """

        # Shredding disabled or no paths provided -> Early return.
        if not C.cfg.CFG["shred_enabled"] or not C.cfg.CFG["shred_paths"]:
            return

        # Remove redundant paths from the list.
        # E.g. ['/path/to/folder', '/path/to/folder/file.txt'] ->
        # Remove '/path/to/folder/file.txt', as the folder it is inside
        # and all its contents will be shredded.
        file_list_reduced = self._remove_redundancy(
                paths=C.cfg.CFG["shred_paths"]
                )

        # Encode the paths to base64 to avoid issues with special
        # characters in the path names.
        file_list_enc = [base64.b64encode(f.encode()).decode()
                         for f in file_list_reduced]

        chunks = self._chunkify_paths(
                file_list=file_list_enc,
                command_str="SHRED"
                )

        # Send all chunks (separator is null byte).
        failure_count = 0
        for i, chunk in enumerate(chunks, start=1):

            # Shred takes longer, so we disable the timeout for now.
            self._socket.settimeout(None)

            resp: str = self.send(command=f"SHRED {'|'.join(chunk)}")

            # Reset the timeout to 5 seconds.
            self._socket.settimeout(5)

            # Success for all files in the chunk.
            if resp == "0 (SHRED)":
                LOGGER.info(
                        f"SHRED action completed successfully for file "
                        f"chunk {i}/{len(chunks)}."
                        )

            # Partial failure for one or more files (overwrite
            # successful, but deletion failed).
            elif resp == "2 (SHRED)":
                LOGGER.warning(
                        f"SHRED action partially failed (overwrite "
                        f"successful, but deletion failed) for 1 or more "
                        f"files in the file chunk {i}/{len(chunks)}."
                        )

            # Complete failure for one or more files and
            # returned '1 (SHRED)'.
            else:
                failure_count += 1
                LOGGER.error(
                        f"SHRED action failed for 1 or more files in the "
                        f"file chunk {i}/{len(chunks)}."
                        )

        # Remove the paths from the config file after shredding to
        # remove all traces of the files.
        C.cfg.CFG["shred_paths"] = []

        # If we had any complete failures, we throw the exception at
        # the end, so we can shred as many files as possible.
        if failure_count:
            raise exc.ActionFailedError(
                    f"SHRED action failed for {failure_count}/{len(chunks)} "
                    f"file chunks!"
                    )

    @ensure_logged_in
    def cmd_permissions(self) -> None:
        """
        Request the necessary permissions for the helper binary to run
        the shred action. It creates temporary files in the paths
        specified in the config file to ensure that the helper binary
        has the necessary permissions to shred these paths. In case of
        a not defused alarm, the shredding can be done without any
        OS permission dialogs.

        :raises CommandFailedError: If the PERMISSIONS command failed.
        :return: None
        """

        if not C.cfg.CFG["shred_paths"]:
            return

        file_list_clean = self._remove_redundancy(
                paths=C.cfg.CFG["shred_paths"]
                )

        # Encode the paths to base64 to avoid issues with special
        # characters in the path names.
        file_list_enc = [base64.b64encode(f.encode()).decode()
                         for f in file_list_clean]

        chunks = self._chunkify_paths(
                file_list=file_list_enc,
                command_str="PERMISSIONS"
                )

        # Send all chunks (separator is null byte).
        failure_count = 0
        for i, chunk in enumerate(chunks, start=1):

            # Requesting permissions takes longer, so we disable the
            # timeout for now.
            self._socket.settimeout(None)

            resp: str = self.send(command=f"PERMISSIONS {'|'.join(chunk)}")

            # Reset the timeout to 5 seconds.
            self._socket.settimeout(5)

            # Success for all files in the chunk.
            if resp == "0 (PERMISSIONS)":
                LOGGER.info(
                        f"PERMISSIONS request completed successfully for "
                        f"file chunk {i}/{len(chunks)}."
                        )

            # Failure for one or more files or folders.
            else:
                failure_count += 1
                LOGGER.error(
                        f"PERMISSIONS request failed for 1 or more files "
                        f"in the file chunk {i}/{len(chunks)}."
                        )

        # If we had any complete failures, we throw the exception at
        # the end, so we can shred as many files as possible.
        if failure_count:
            raise exc.CommandFailedError(
                    f"PERMISSIONS request failed for {failure_count}/"
                    f"{len(chunks)} file chunks!"
                    )

    @ensure_logged_in
    def cmd_status(self) -> bool:
        """
        Get the (health-) status of the helper binary.

        :raises CommandFailedError: If the STATUS command failed.
        :return: True if the status is OK, False otherwise.
        :rtype: bool
        """

        resp: str = self.send(command="STATUS")

        if resp not in ("0 (STATUS)", "1 (STATUS)"):
            raise exc.CommandFailedError(
                    f"STATUS command returned with: '{resp}'"
                    )

        # Gives us at the end '0' or '1' as resp_status.
        resp_status: str = resp.split(sep=" ", maxsplit=1)[0]

        return not bool(int(resp_status))

    @ensure_logged_in
    def cmd_version(self) -> str:
        """
        Get the version of the helper binary (e.g. '0.2.3').

        :raises CommandFailedError: If the VERSION command failed.
        :return: The version of the helper binary (x.y.z).
        :rtype: str
        """

        resp: str = self.send(command="VERSION")

        # Response did not match the expected format -> Error occurred.
        if not re.match(r"^\d+\.\d+\.\d+ \(VERSION\)$", resp):
            raise exc.CommandFailedError(
                    f"VERSION command returned with: '{resp}'"
                    )

        return resp.split(sep=" ", maxsplit=1)[0]

    def show_shred_window(self):
        """
        Display the file and folder selection dialog for shredding.

        :return: None
        """

        window = PathSelector()
        paths = window.exec()

        # None -> Cancel button -> Do nothing.
        if paths is None:
            pass

        # Save to configuration.
        # Empty list -> OK button -> User removed all paths.
        # List with paths -> OK button -> There are paths to shred.
        else:
            C.cfg.CFG["shred_paths"] = [str(path) for path in paths]

        # Let the binary ask for permissions for these paths.
        self.cmd_permissions()

    def _install_launch_agent(self) -> None:
        """
        Install the helper binary as a launch agent.

        :raises HelperInstallError: If the installation failed.
        :return: None
        """

        try:

            # Create LaunchAgents directory if it does not exist.
            C.helper.LAUNCH_AGENT_WRAPPER_DEST.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                    )

            # Maybe the user renames the app or puts it in a different
            # directory, so we get the path to binary dynamically.
            binary_path = None
            for par in C.app.PATH.parents:
                if par.name == "Contents":
                    binary_path = par / "Frameworks"
                    break

            else:
                # TODO: REMOVE!
                binary_path = C.app.PATH / "bin"

                binary_path = Path(
                        "/Applications/swifthelper.app/Contents/Resources"
                        )

            if binary_path is None:
                raise exc.HelperInstallError(
                        "Could determine the binary path!"
                        )

            # Substitute path placeholder with actual path to the
            # executable in memory.
            with open(file=C.helper.LAUNCH_AGENT_WRAPPER_SOURCE,
                      mode="r",
                      ) as fh:
                launch_plist = fh.read().replace(
                        "$PATH_PLACEHOLDER",
                        str(binary_path),
                        2,
                        )

            # Write the plist from memory to the LaunchAgents directory.
            with open(file=C.helper.LAUNCH_AGENT_WRAPPER_DEST, mode="w") as fh:
                fh.write(launch_plist)

            QThread.sleep(1)

            # Load the launchctl service.
            process.Process(
                    binary_path="/bin/launchctl",
                    args=("load",
                          "-w",
                          str(C.helper.LAUNCH_AGENT_WRAPPER_DEST)),
                    timeout=5,
                    blocking=True,
                    ).run()

            LOGGER.info("Helper binary was installed as a launch agent.")

        except Exception as e:
            raise exc.HelperInstallError(e)

    def _check_install_script(self, path: Path = C.helper.SUDO_SCRIPT) -> None:
        """
        Validate the helper sudo installation script. Check if the file
        is not a symlink and has the right permissions. We want to be
        extra paranoid here since this script is executed with sudo
        privileges. No need to check a pre-calculated hash, as the
        IntegrityManager runs these validations continuously in
        background.
        Thanks for Michael Altfield@BusKill for his excellent code here!

        :param path: Path to the script (optional).
        :type path: Path
        :raises HelperSudoScriptError: If the script is not valid.
        :return: None
        """
        try:

            if path.is_symlink():
                raise exc.HelperSudoScriptError(
                        "Helper sudo installation script is a symlink!"
                        )

            # Check if script is not executable by others than owner.
            if path.stat().st_mode & 0o777 != 0o500:
                raise exc.HelperSudoScriptError(
                        f"Helper sudo installation script has wrong "
                        f"cmd_permissions: {oct(path.stat().st_mode & 0o777)}!"
                        )

            # Check if the owned by root or user.
            if path.stat().st_uid != 0 and path.stat().st_uid != os.getuid():
                raise exc.HelperSudoScriptError(
                        "Helper sudo installation script is not owned "
                        "by root or user!"
                        )

            # Check if the script is owned by group root or user.
            if path.stat().st_gid != 0 and path.stat().st_gid != os.getgid():
                raise exc.HelperSudoScriptError(
                        "Helper sudo installation script is not owned "
                        "by root group or user group!"
                        )

            LOGGER.info("Helper sudo installation script is valid.")

        except Exception as e:
            raise exc.HelperSudoScriptError(
                    f"Helper sudo installation script validation "
                    f"failed: {e.__class__.__name__}: {e}"
                    )

    def _run_install_script(self) -> None:
        """
        Run the helper sudo installation script as root using
        AuthorizationExecuteWithPrivileges. The script is executed with
        the necessary arguments and the helper binary hash to whitelist
        it in the sudoers file, so the helper can auto-start with the
        necessary permissions on boot. Using a custom sudoers file, we
        want to be extra paranoid here. The hash ensures only the exact
        helper binary is allowed to run with sudo privileges.

        :raises HelperSudoScriptError: If the script is not valid or the
            execution failed (script error, macOS authorization error).
        :return: None
        """

        try:
            # Hash of helper binary, for whitelisting in sudoers file.
            with open(C.helper.BINARY_PATH, "rb") as fh:
                fh_hash = hashlib.file_digest(
                        fh,
                        "sha256"
                        ).hexdigest()

            script_args = [
                    str(C.helper.BINARY_PATH),
                    fh_hash,
                    str(C.app.USER),
                    str(C.helper.SUDOERS_PATH),
                    ]

            # Run the helper sudo installation script.
            _ = helpers.run_sudo_script(
                    script_path=C.helper.SUDO_SCRIPT,
                    script_args=script_args,
                    )

            # Read output from the script and extract its result.
            time.sleep(1)
            with open(f"{C.app.PATH}/supp/install-helper.log", "r") as f:
                output = f.readlines()

            # We to get the second last line, as the last line is a
            # visual separator (-----).
            result_line = output[-2].strip()

        except exc.SudoExecuteScriptError as e:
            raise exc.HelperSudoScriptError(e)

        # Install-helper script errors.
        if result_line != "Success: Helper binary installed successfully.":
            raise exc.HelperSudoScriptError(
                    f"The helper sudo installation script "
                    f"({C.helper.SUDO_SCRIP}) was executed but returned "
                    f"with: \nExit code: 1, message: '{result_line}'"
                    )

    # Moved to utils/helpers.py.
    # def _run_sudo_script(
    #         self,
    #         script_path: Path = C.helper.SUDO_SCRIPT,
    #         script_args: list[str] = None,
    #         ) -> None:
    #     """
    #     Run the helper sudo installation script as root using
    #     AuthorizationExecuteWithPrivileges. The script is executed with
    #     the necessary arguments and the helper binary hash to whitelist
    #     it in the sudoers file, so the helper can auto-start with the
    #     necessary permissions on boot.
    #
    #     :param script_path: Path to the helper sudo installation script
    #         (optional).
    #     :type script_path: Path
    #     :param script_args: List of arguments for the script (optional).
    #     :type script_args: list[str]
    #     :raises HelperSudoScriptError: If the script is not valid or the
    #         execution failed (script error, macOS authorization error).
    #     :return: None
    #     """
    #
    #     try:
    #         # Default script arguments.
    #         if script_args is None and script_path == C.helper.SUDO_SCRIPT:
    #             # Hash of helper binary, for whitelisting in sudoers file.
    #             with open(C.helper.BINARY_PATH, "rb") as fh:
    #                 fh_hash = hashlib.file_digest(
    #                         fh,
    #                         "sha256"
    #                         ).hexdigest()
    #
    #             script_args = [
    #                     str(C.helper.BINARY_PATH),
    #                     fh_hash,
    #                     str(C.app.USER),
    #                     str(C.helper.SUDOERS_PATH),
    #                     ]
    #
    #         else:
    #             script_args = []
    #
    #         import ctypes
    #         import ctypes.util
    #         from ctypes import byref
    #
    #         # Import  C libraries for interacting via ctypes with the
    #         # macOS API.
    #         sec = ctypes.cdll.LoadLibrary(ctypes.util.find_library(
    #         "Security"))
    #
    #         k_authorization_flag_defaults = 0
    #         auth = ctypes.c_void_p()
    #         r_auth = byref(auth)
    #         sec.AuthorizationCreate(
    #                 None,
    #                 None,
    #                 k_authorization_flag_defaults,
    #                 r_auth
    #                 )
    #
    #         # main_pid = os.getpid()
    #
    #         exe = ["/bin/sh", str(script_path)]
    #
    #         # Add the script arguments to the executable list.
    #         exe.extend(script_args)
    #
    #         # exe = [sys.executable, str(PATH / "child.py")]
    #         args = (ctypes.c_char_p * len(exe))()
    #         for i, arg in enumerate(exe[1:]):
    #             args[i] = arg.encode("utf8")
    #
    #         io = ctypes.c_void_p()
    #
    #         return_code = sec.AuthorizationExecuteWithPrivileges(
    #                 auth,
    #                 exe[0].encode("utf8"),
    #                 0,
    #                 args,
    #                 byref(io)
    #                 )
    #
    #         # Read output from the script and extract its result.
    #         time.sleep(1)
    #         with open(f"{C.app.PATH}/supp/install-helper.log", "r") as f:
    #             output = f.readlines()
    #
    #         # We to get the second last line, as the last line is a
    #         # visual separator (-----).
    #         result_line = output[-2].strip()
    #
    #     except Exception as e:
    #         raise exc.HelperSudoScriptError(e)
    #
    #     # MacOS authorization errors.
    #     if return_code != 0:
    #         raise exc.HelperSudoScriptError(
    #                 f"AuthorizationExecute the helper sudo installation "
    #                 f"script ({script_path}) as root failed with return "
    #                 f"code: {return_code}."
    #                 )
    #
    #     # Install-helper script errors.
    #     if result_line != "Success: Helper binary installed successfully.":
    #         raise exc.HelperSudoScriptError(
    #                 f"The helper sudo installation script "
    #                 f"({script_path}) was executed but returned with: \n"
    #                 f"Exit code: 1, "
    #                 f"message: '{result_line}'"
    #                 )
    #
    #     LOGGER.info("Helper sudo installation script executed successfully.")

    def uninstall_launch_agent(self) -> None:
        """
        Uninstall the helper binary as a launchctl service.

        :raises HelperUninstallError: If the uninstallation failed.
        :return: None
        """

        try:

            # Unload the launchctl service.
            process.Process(
                    binary_path="/bin/launchctl",
                    args=("unload",
                          C.helper.LAUNCH_AGENT_WRAPPER_DEST),
                    timeout=5,
                    blocking=True,
                    ).run()

            time.sleep(1)

            # Remove the launch agent plist.
            C.helper.LAUNCH_AGENT_WRAPPER_DEST.unlink()

        except Exception as e:
            raise exc.HelperUninstallError(e)

    def install(self) -> None:
        """
        Install the helper binary as a launch agent.

        :return: None
        """

        if self.binary_installed or self.binary_running:
            LOGGER.info("Helper binary is already installed!")
            return

        self._check_install_script()
        self._run_install_script()
        self._install_launch_agent()

        if not self.binary_installed:
            raise exc.HelperInstallError("Helper binary installation failed!")

        else:
            LOGGER.info("Helper binary was successfully installed.")

    def todo(self):
        # Startup logic:
        # Check if binary is installed, check if its running
        # -> yes, yes -> login()
        # -> yes, no -> start_binary(),
        #   check if its running -> cmd_login()
        # -> no, no -> install(), start_binary(),
        #   check if its running -> cmd_login()
        pass


if __name__ == "__main__":

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ins = HelperManager()

    print("Installed:", ins.binary_installed)
    print("Running:", ins.binary_running)

    # ins.install()
    # ins._uninstall_launch_agent()

    # ins.start_manually()

    # print(C.cfg.CFG["shred_paths"])

    # C.cfg.CFG["shred_paths"] = [str(Path("/Users/lennart/Desktop/test/lol")),
    #                           str(Path("/Users/lennart/Desktop/test/lol2"))]

    # C.cfg.CFG["shred_enabled"] = True
    print(C.cfg.CFG["shred_paths"])

    #######################################

    running = True
    while running:
        cmd_inp = input("Enter command: ")

        # Convert input to method call.
        if cmd_inp in ("SHUTDOWN", "HIBERNATE", "SHRED"):
            func = getattr(ins, f"action_{cmd_inp.lower()}")

        elif cmd_inp in ("STATUS", "VERSION", "LOGIN", "LOGOUT",
                         "PERMISSIONS"):
            func = getattr(ins, cmd_inp.lower())

        elif cmd_inp == "EXIT":
            func = getattr(ins, cmd_inp.lower())
            running = False

        else:
            func = None

        start = time.perf_counter()

        if func:
            out = func()

        else:
            out = ins.send(cmd_inp)

        end = time.perf_counter()
        print(f"Received ({end - start:2f} s):", out)
