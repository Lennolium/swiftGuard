import pytest
from PySide6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QLabel,
    QScrollArea,
    QWidget,
    )

from swiftguard.app import CustomDialog


############################################
#            CustomDialog class            #
############################################


# Fixture to initialize the QApplication before running tests
@pytest.fixture(scope="module")
def app():
    app = QApplication([])
    yield app
    app.quit()


def test_custom_dialog_creation(app):
    # Test if the CustomDialog can be created without errors
    dialog = CustomDialog("test_file.txt", "Test Dialog")
    assert dialog is not None


def test_custom_dialog_title(app):
    # Test if the CustomDialog's title matches the expected title
    dialog = CustomDialog("test_file.txt", "Test Dialog")
    assert dialog.windowTitle() == "Test Dialog"


def test_custom_dialog_header(app):
    # Test if the CustomDialog's header label text matches the expected header
    dialog = CustomDialog(
        "test_file.txt", "Test Dialog", "This is a test header."
    )
    header_label = dialog.findChild(QLabel)
    assert header_label.text() == "This is a test header.\n\n"


def test_custom_dialog_close_button(app, monkeypatch):
    # Test if the CustomDialog's close button triggers the 'rejected' signal
    dialog = CustomDialog("test_file.txt", "Test Dialog")
    btn_box = dialog.findChild(QDialogButtonBox)
    monkeypatch.setattr(btn_box, "rejected", lambda x: None)
    btn_box.button(QDialogButtonBox.Close).click()


def test_custom_dialog_contents(app):
    # Test if the CustomDialog displays the contents from the test file
    dialog = CustomDialog("test_file.txt", "Test Dialog")
    scroll_area = dialog.findChild(QScrollArea)
    scroll_widget = scroll_area.findChild(QWidget)
    labels = scroll_widget.findChildren(QLabel)

    # Load the expected content from the test file
    expected_content = []
    with open("test_file.txt", "r") as file:
        for line in file:
            expected_content.append(line.strip())

    # Extract the text from the QLabel widgets in the scroll area
    displayed_content = [label.text() for label in labels]

    assert displayed_content == expected_content


############################################
#            create_tray_icon()            #
############################################
