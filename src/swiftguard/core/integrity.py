#!/usr/bin/env python3

"""
core/integrity.py: Manages the runtime integrity of the application.

This module contains the IntegrityManager class, which is a singleton
class that manages the runtime integrity of the application. It checks
the integrity of the files and the configuration file during runtime.
It features
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__date__ = "2024-02-16"
__status__ = "Prototype/Development/Production"

# Imports.
import json
import traceback
import logging
import hashlib
import random
from pathlib import Path

from PySide6.QtCore import (QObject, QRunnable, QThread,
                            Signal, Slot, QMutex, QWaitCondition)
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox, QStyle

from swiftguard.constants import C
from swiftguard.init import exceptions as exc, models

# Child logger.
LOGGER = logging.getLogger(__name__)


def get_file_hash(fp: str | Path) -> str:
    """
    Generate a hash for a file using the secure blake2b algorithm.

    :param fp: file path of the file to hash.
    :type fp: str
    :return: hash of the file.
    :rtype: str
    """

    f_hash = hashlib.blake2b(person=C.sec.PEPPER)
    with open(fp, "rb") as f:
        while chunk := f.read(8192):
            f_hash.update(chunk)
    return f_hash.hexdigest()


def get_string_hash(string: str) -> str:
    """
    Generate a hash for a string using the secure blake2b algorithm.

    :param string: The string to hash.
    :type string: str
    :return: The hash of the string.
    :rtype: str
    """

    str_hash = hashlib.blake2b(person=C.sec.PEPPER)
    str_hash.update(string.encode())
    return str_hash.hexdigest()


# Only for pre-release, not used in the final app.
def generate_hash_json(files: list[Path], hashes_file: Path):
    """
    Generate a json file containing the hashes of the files. The file
    is used to verify the integrity of the shipped files during runtime.

    :param files: list of file paths to hash.
    :type files: list[Path]
    :param hashes_file: file path of the json file to write the hashes to.
    :type hashes_file: Path
    """

    hashes = {str(file): get_file_hash(file) for file in files}
    with open(hashes_file, "w", encoding="utf-8") as f:
        json.dump(hashes, f)


class IntegrityManager(QThread, metaclass=models.SingletonQt):
    """
    Manager for securing the runtime integrity of the application.
    """

    # Signals from thread state.
    running_sig: Signal = Signal(bool)
    healthy_sig: Signal = Signal(bool)
    error_sig: Signal = Signal(Exception)

    def __init__(self) -> None:
        """
        Starts the IntegrityManager thread and initializes the signals.
        To stop the thread, call the stop method.

        :return: None
        """

        super().__init__()

        # Thread management and communication.
        self.thread_id: str | None = None
        self.running: bool = False
        self.healthy: bool | None = None
        self.error: Exception | None = None
        self.mutex: QMutex = QMutex()
        self.condition: QWaitCondition = QWaitCondition()

        # Start the run method/thread.
        self.start()

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
                    f"started running its integrity checks."
                    )

        try:
            while self.running:
                self.mutex.lock()
                self.condition.wait(self.mutex, (10 * 1000))  # 10 secs.
                self.mutex.unlock()

                if not self.running:
                    break

                self._check_hashes()
                C.cfg.CFG.integrity()

                self.healthy = True
                self.healthy_sig.emit(self.healthy)

        except Exception as e:

            LOGGER.critical(
                    f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"found a critical issue. Stopping the thread."
                    )
            LOGGER.critical(f"{e.__class__.__name__}: {e} \n"
                            f"{traceback.format_exc()}"
                            )

            self.running = False
            self.running_sig.emit(False)
            self.healthy = False
            self.healthy_sig.emit(self.healthy)
            self.error = e
            self.error_sig.emit(e)

    def stop(self) -> None:
        """
        Stop the worker. This does not delete the thread or the worker
        object, but the worker will finish the current loop and then
        stop. If we restart the worker, it will reuse the same thread.

        :return: None
        """

        if not self.running:
            LOGGER.info(
                    f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"is not running, but stopping was requested."
                    )
            return

        # Stop the integrity checks and wake the thread.
        self.running = False
        self.running_sig.emit(False)
        self.healthy = None

        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()

        LOGGER.info(
                f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                f"stopped running its checks."
                )

        # Wait for the thread to finish.
        self.quit()
        if not self.wait(2500):
            self.terminate()
            self.wait(2500)

    @staticmethod
    def _check_hashes(hashes_file: Path = C.sec.INTEGRITY_FILE) -> None:
        """
        Verify the hashes of the files in the json file.

        :param hashes_file: File path of json file containing hashes.
        :type hashes_file: str
        :raises exceptions.RuntimeIntegrityError: If the swiftguard of a
            file is compromised.
        :return: None.
        """

        # First verify hash of the json file (containing all hashes).
        if get_file_hash(hashes_file) != C.cfg.CFG["release_hash"]:
            raise exc.RuntimeIntegrityError(
                    f"Integrity of file '{hashes_file}' compromised!"
                    )

        with open(hashes_file, "r") as f:
            hashes = json.load(f)

        # For every file in the json file check if the hashes matches.
        for file, sha in hashes.items():
            if get_file_hash(Path(file)) != sha:
                raise exc.RuntimeIntegrityError(
                        f"Integrity of file '{file}' compromised!"
                        )


if __name__ == "__main__":
    ...

    s0 = ("/Users/lennart/Library/Application "
          "Support/dev.lennolium.swiftguard/swiftguard.enc")

    s = ("/Users/lennart/Documents/Programmieren/CharmProjects/Privat"
         "/Projekte/swiftguard-redesign/src/swiftguard/supp/hashes.json")

    print(get_file_hash(Path(s)))
    app = QApplication([])
    mng = IntegrityManager()
    # mng.show_integrity_dialog(exc.RuntimeIntegrityError("Test"))
    # Start of the program.

    # Create a list of files to hash and save to json file.
    # generate_hash_json(C.sec.INTEGRITY_FILES, C.sec.INTEGRITY_FILE)

    # print("C.RELEASE_HASH:", integrity.get_file_hash(C.sec.INTEGRITY_FILE))

    # manager = IntegrityManager()
    # manager.start()
