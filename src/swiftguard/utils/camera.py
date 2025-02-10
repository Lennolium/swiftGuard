#!/usr/bin/env python3

"""
utils/camera.py: Initialize the system camera and take photos.

The CameraManager class initializes the system camera and provides
methods for taking photos and showing a camera preview dialog. The
camera preview dialog shows the camera output in a viewfinder with a
close button. The camera access permissions are requested during object
initialization. If the user denies access, the camera permissions will
be reset once and the user will be prompted again. If the user denies
access again, an exception will be raised and the CameraManager object
will not be initialized.
"""

from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2025-01-06"
__status__ = "Prototype/Development/Production"

# Imports.
import sys
import os
import logging
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout,
                               QPushButton, QDialog)
from PySide6.QtMultimedia import (QCamera, QMediaDevices,
                                  QMediaCaptureSession,
                                  QImageCapture, QCameraDevice, QCameraFormat)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QEventLoop, QObject, QTimer

from swiftguard.constants import C
from swiftguard.init import exceptions as exc, models
from swiftguard.utils import helpers

# Child logger.
LOGGER = logging.getLogger(__name__)


class CameraPreview(QDialog):
    """
    Dialog for previewing the camera output in a viewfinder.
    """

    def __init__(
            self,
            parent: CameraManager,
            window_size: tuple[int, int] = (740, 480)
            ) -> None:
        """
        Dialog for previewing the camera output in a viewfinder with a
        close button.

        :param parent: Parent camera manager.
        :type parent: CameraManager
        :param window_size: Size of the dialog window (default: (740, 480)).
        :type window_size: tuple[int, int]
        :return: None
        """

        super().__init__()
        self.parent = parent
        self.setWindowTitle("Camera Preview")
        self.setGeometry(100, 100, *window_size)
        self.setModal(True)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.viewfinder = QVideoWidget(self)
        self.layout.addWidget(self.viewfinder)

        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        self.layout.addLayout(button_layout)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Close the camera preview dialog and stop the camera.

        :param event: Close event.
        :type event: QCloseEvent
        :return: None
        """

        self.parent.camera.stop()
        self.parent.capture_session.setVideoOutput(QVideoWidget())
        self.parent.is_camera_active = False
        event.accept()


@contextmanager
def suppress_deprecated_warnings() -> None:
    """
    Suppress deprecation warnings for the camera setup given by PySide
    using macOS-deprecated camera APIs.

    :return: None
    """

    original_stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stderr.close()
        sys.stderr = original_stderr


class CameraManager(metaclass=models.Singleton):
    """
    Camera manager for taking photos and showing camera previews.
    """

    def __init__(self) -> None:
        """
        Camera manager for taking photos and showing a dialog with a
        camera viewfinder for previewing the camera output.
        After initialization, use the 'show_preview' method to show the
        camera output in a dialog window, and the 'take_photo' method to
        take a photo with the camera. If you want to get the latest
        photo file location, use the 'photo_file' attribute. If camera
        access permissions are not set yet, the user will be prompted to
        grant camera access permissions, during object initialization.
        If the user denies access, the camera permissions will be reset
        once and the user will be prompted again. If the user denies
        access again, an exception will be raised.

        :raise NotificationSetupCameraError: If camera access permissions
            are denied or the camera could not be initialized.
        :return: None
        """

        # Access permissions denied -> Reset -> Request.
        # Access permissions not determined yet -> Request.
        if not self.permissions_status:
            if not self.request_permissions():
                raise exc.NotificationSetupCameraError(
                        "Camera access permissions denied. Could not "
                        "initialize CameraManager!"
                        )

        # Camera setup.
        try:
            with suppress_deprecated_warnings():
                self.camera = QCamera(self._default_camera)
            self.capture_session = QMediaCaptureSession()
            self.capture_session.setCamera(self.camera)
            self._image_capture = QImageCapture(self.camera)
            self.capture_session.setImageCapture(self._image_capture)
            if self._max_format:
                self.camera.setCameraFormat(self._max_format)
            self.is_camera_active = False
            self.photo_file: Path | None = None

            # Timeout for photo capture.
            self._check_timer = QTimer()
            self._check_timer.timeout.connect(self._check_photo_saved)
            self._loop = QEventLoop()

            # UI setup (dialog to preview camera output).
            self.camera_dialog: CameraPreview | None = None

        except Exception as e:
            raise exc.NotificationSetupCameraError(
                    f"An error occurred during camera setup: "
                    f"{e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )

        if not self.ready:
            raise exc.NotificationSetupCameraError(
                    "Camera is not ready. Could not initialize CameraManager!"
                    )

    @property
    def _default_camera(self) -> QCameraDevice:
        """
        Get the default camera device. We prefer the built-in camera
        ('FaceTime HD Camera' or 'iSight') and if not found, we use the
        OS-default camera.

        :return: Default camera device.
        :rtype: QCameraDevice
        """

        for camera_info in QMediaDevices.videoInputs():

            # Built-in camera.
            if "facetime" in camera_info.description().lower():
                return camera_info
            elif "isight" in camera_info.description().lower():
                return camera_info

        return QMediaDevices.defaultVideoInput()

    @property
    def _max_format(self) -> QCameraFormat | None:
        """
        Get the camera format with the highest resolution and aspect
        ratio of 16:9 for maximum image quality.

        :return: Camera format with the highest resolution and aspect
            ratio of 16:9.
        :rtype: QCameraFormat | None
        """

        max_resolution = (0, 0)
        best_format = None

        for camera_format in self.camera.cameraDevice().videoFormats():
            resolution = camera_format.resolution()
            aspect_ratio = resolution.width() / resolution.height()
            if (aspect_ratio == 16 / 9
                    and (resolution.width() * resolution.height()) >
                    (max_resolution[0] * max_resolution[1])):
                max_resolution = (resolution.width(), resolution.height())
                best_format = camera_format

        if best_format:
            return best_format

    # @property
    # def permissions_status(self) -> bool | None:
    #     """
    #     Get the current camera access permissions status.
    #
    #     :return: True if camera access is granted, False otherwise. If
    #         the permissions are not determined yet, return None.
    #     :rtype: bool | None
    #     """
    #
    #     try:
    #         status = (
    #                 AVFoundation.AVCaptureDevice.
    #                 authorizationStatusForMediaType_(
    #                         AVFoundation.AVMediaTypeVideo
    #                         ))
    #
    #     except Exception as _:
    #         return False
    #
    #     # User granted access.
    #     if status == AVFoundation.AVAuthorizationStatusAuthorized:
    #         return True
    #
    #     # User denied access.
    #     elif status == AVFoundation.AVAuthorizationStatusDenied:
    #         return False
    #
    #     # Restricted by system policy (e.g. parental controls).
    #     elif status == AVFoundation.AVAuthorizationStatusRestricted:
    #         return False
    #
    #     # Not determined or set yet -> Ask for permission.
    #     elif status == AVFoundation.AVAuthorizationStatusNotDetermined:
    #         return None
    #
    #     # Unknown status.
    #     else:
    #         return False

    @property
    def permissions_status(self) -> bool | None:
        """
        Get the current camera access permissions status.

        :return: True if camera access is granted, False otherwise. If
            the permissions are not determined yet, return None.
        :rtype: bool | None
        """

        try:
            status = QApplication.instance().checkPermission(
                    QtCore.QCameraPermission()
                    )

        except Exception as _:
            return False

        # User granted access.
        if status == QtCore.Qt.PermissionStatus.Granted:
            return True

        # Not determined or set yet -> Ask for permission.
        elif status == QtCore.Qt.PermissionStatus.Undetermined:
            return None

        # Denied or restricted by system policy (parental controls).
        else:
            return False

    @property
    def ready(self) -> bool:
        """
        Check if the camera is ready to take a photo, and we got all
        needed permissions.

        :return: If the camera is ready to take a photo.
        :rtype: bool
        """

        return (hasattr(self, "camera")
                and self.camera is not None
                and self.camera.error() == QCamera.Error.NoError
                and self.camera.isAvailable()
                and self.permissions_status)

    @staticmethod
    def _rotated_file_name(photo_file: Path) -> Path:
        """
        Create a new photo file name with a timestamp appended
        (e.g. 'attacker_photo_20220101_120000.jpg').
        We keep only the 5 most recent photos (autorotation/deletion).

        :return: New photo file name with timestamp appended.
        :rtype: Path
        """

        # Append datetime to photo file name.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_photo_file = photo_file.with_name(
                f"{photo_file.stem}_{timestamp}"
                f"{photo_file.suffix}"
                )

        photo_dir = photo_file.parent
        photo_files = sorted(
                photo_dir.glob(
                        f"{photo_file.stem}_*"
                        f"{photo_file.suffix}"
                        ),
                key=lambda p: p.stat().st_mtime,
                reverse=True
                )

        # Delete all but the 5 most recent photos.
        for old_photo in photo_files[4:]:
            old_photo.unlink()

        return new_photo_file

    # def request_permissions(self) -> bool:
    #     """
    #     Request camera access permission from the user using the system
    #     dialog. Function will block until the dialog was answered.
    #     If the user (accidentally) denies access, we reset the camera
    #     permissions once and try again.
    #
    #     :return: If camera access permission was granted.
    #     :rtype: bool
    #     """
    #
    #     import AVFoundation
    #
    #     class Callback:
    #         """
    #         Callback for the camera access request.
    #         """
    #
    #         __slots__ = ("loop", "success",)
    #
    #         def __init__(self) -> None:
    #             """
    #             Callback for the camera access request.
    #             """
    #
    #             self.loop = QEventLoop()
    #             self.success = False
    #
    #         def call(self, granted: bool) -> None:
    #             """
    #             Callback for the camera access request.
    #             Side effect: Sets the success attribute True/False.
    #
    #             :param granted: If camera access was granted.
    #             :type granted: bool
    #             :return: None
    #             """
    #
    #             if granted:
    #                 self.success = True
    #
    #             self.loop.quit()
    #
    #     # Try twice to request camera access.
    #     for i in range(2):
    #         callback = Callback()
    #
    #         # Request permissions for camera access.
    #         (AVFoundation.AVCaptureDevice
    #         .requestAccessForMediaType_completionHandler_(
    #                 AVFoundation.AVMediaTypeVideo,
    #                 callback.call,
    #                 ))
    #
    #         # Starting event loop, until callback fires, quits the loop,
    #         # so the function can return the result.
    #         callback.loop.exec()
    #
    #         # If the first request was denied, reset camera permissions
    #         # once and ask again.
    #         if i == 0 and callback.success is False:
    #             helpers.reset_camera_access()
    #             LOGGER.info("Camera permissions reset. Asking again for "
    #                         "camera access the last time now."
    #                         )
    #             continue
    #
    #         return callback.success

    def request_permissions(self) -> bool:
        """
        Request camera access permission from the user using the system
        dialog. Function will block until the dialog was answered.
        If the user (accidentally) denies access, we reset the camera
        permissions once and try again.

        :return: If camera access permission was granted.
        :rtype: bool
        """

        class Callback(QObject):
            """
            Callback for the camera access request.
            """

            __slots__ = ("permission", "loop", "success",)

            def __init__(self) -> None:
                """
                Callback for the camera access request.
                """

                super().__init__()
                self.permission = QtCore.QCameraPermission()
                self.loop = QEventLoop()
                self.success = False

            def call(self, granted: bool) -> None:
                """
                Callback for the camera access request.
                Side effect: Sets the success attribute True/False.

                :param granted: If camera access was granted.
                :type granted: bool
                :return: None
                """

                if granted:
                    self.success = True

                self.loop.quit()

        # Try twice to request camera access.
        for i in range(2):
            callback = Callback()

            # Request permissions for camera access.
            print("Requesting camera permissions...")
            QApplication.instance().requestPermission(
                    callback.permission,
                    callback,
                    callback.call,
                    )

            # Starting event loop, until callback fires, quits the loop,
            # so the function can return the result.
            callback.loop.exec()

            # If the first request was denied, reset camera permissions
            # once and ask again.
            # NOTE: This is not working as expected, as the callback
            # also returns True if Undetermined. Instead, we just check
            # permissions again.
            # if i == 0 and callback.success is False:
            if i == 0 and not self.permissions_status:
                helpers.reset_camera_access()
                LOGGER.info("Camera permissions reset. Asking again for "
                            "camera access the last time now."
                            )
                continue

            return callback.success

    def _check_photo_saved(self) -> None:
        """
        Check if the photo was saved successfully. We check this every
        250 ms and if the photo was saved, we can early return to give
        control back to the main thread, for further alarm processing.

        :return: None
        """

        # For fast returning if photo was saved.
        if self.photo_file.exists():
            LOGGER.info(f"Photo taken and saved to '{self.photo_file}'.")
            self._check_timer.stop()
            self._loop.quit()

    def _capture_photo(self) -> None:
        """
        Capture the photo and save it to the location specified in
        C.email.PHOTO_FILE.

        :return: None
        """

        self._image_capture.imageCaptured.connect(
                lambda ident, image: image.save(str(self.photo_file))
                )
        self._image_capture.captureToFile(str(self.photo_file))
        self.camera.stop()

    def take_photo(
            self,
            save_to: Path = C.email.PHOTO_FILE,
            warmup: int = C.email.PHOTO_WARMUP,
            ) -> None:
        """
        Take a photo with the camera and save it to the location
        specified in C.email.PHOTO_FILE. The photo is saved with a
        timestamp appended, and we keep only the 5 most recent photos
        (autorotation).

        :param save_to: Path to save the photo to
            (default: C.email.PHOTO_FILE).
        :type save_to: Path
        :param warmup: Warm-up time for the camera in ms, for ensuring
            good focus and exposure (default: 1000 ms).
        :raise NotificationTakePhotoError: If photo could not be taken.
        :return: None
        """

        # Check permissions (False -> Denied, None -> Not determined).
        # Not determined -> We will not display a request dialog, as
        # in case of a tampering, we want to continue fast.
        if not self.permissions_status:
            raise exc.NotificationTakePhotoError(
                    "Camera access permissions denied. Could not take "
                    "photo."
                    )

        if not self.ready:
            raise exc.NotificationTakePhotoError(
                    "Camera is not ready. Could not take photo."
                    )

        try:

            if not save_to.parent.exists():
                save_to.parent.mkdir(parents=True)

            # Get the current photo file name (with timestamp and rotation).
            self.photo_file = self._rotated_file_name(photo_file=save_to)

            self.camera.start()

            # Delay to warm up the camera.
            QTimer.singleShot(warmup, self._capture_photo)

            # Check every 250 ms if photo was saved and early return if so.
            self._check_timer.start(250)
            self._loop.exec()

        except Exception as e:
            raise exc.NotificationTakePhotoError(
                    f"{e.__class__.__name__}: {e} \n"
                    f"{traceback.format_exc()}"
                    )

    def show_preview(self) -> None:
        """
        Show a preview of the camera output in a dialog window.

        :return: None
        """

        if not (self.is_camera_active or self.camera_dialog):
            self.camera_dialog = CameraPreview(self)
            self.camera.start()
            self.capture_session.setVideoOutput(self.camera_dialog.viewfinder)
            self.is_camera_active = True
            self.camera_dialog.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    import time

    time_start = time.perf_counter()
    cam = CameraManager()

    # cam.show_preview()

    # print("READY:", cam.ready)

    # cam.take_photo(save_to=Path("/Users/Lennart/Desktop/capture_test.jpg"))

    time_end = time.perf_counter()
    print(f"TIME: {time_end - time_start:.2f} s")

    sys.exit(app.exec())
