import configparser
import os

from swiftguard.const import CONFIG_FILE
from swiftguard.utils.conf import create, load, validate, write


def test_create():
    # Act
    create(force_restore=False)

    # Assert
    assert os.path.isfile(CONFIG_FILE) is True


def test_validate():
    # Arrange
    config = configparser.ConfigParser()
    config["Application"] = {
        "version": "0.1",
        "log": "file",
        "log_level": "2",
        "check_updates": "1",
    }
    config["User"] = {
        "autostart": "1",
        "action": "shutdown",
        "delay": "0",
        "check_interval": "1.0",
    }
    config["Whitelist"] = {
        "usb": "usb_device_1, usb_device_2",
        "bluetooth": "bluetooth_device_1",
    }

    # Act
    validated_config = validate(config)

    # Assert
    assert validated_config == config


def test_load(tmp_path):
    # Arrange
    config_path = os.path.join(tmp_path, "swiftguard.ini")
    config = configparser.ConfigParser()
    with open(config_path, "w") as config_file:
        config.write(config_file)

    # Act
    loaded_config = load(config)

    # Assert
    assert loaded_config == config


def test_write(tmp_path):
    # Arrange
    config_path = CONFIG_FILE
    config = configparser.ConfigParser()
    config["Application"] = {
        "version": "0.1",
        "log": "file",
        "log_level": "2",
        "check_updates": "1",
    }
    config["User"] = {
        "autostart": "1",
        "action": "shutdown",
        "delay": "0",
        "check_interval": "1.0",
    }
    config["Whitelist"] = {
        "usb": "usb_device_1, usb_device_2",
        "bluetooth": "bluetooth_device_1",
    }

    # Act
    write(config)

    # Assert
    assert os.path.isfile(config_path) is True


def test_create_overwrite(tmp_path):
    # Arrange
    config_path = CONFIG_FILE

    # Act
    create(force_restore=True)

    # Assert
    assert os.path.isfile(config_path) is True


def test_write_empty_config(tmp_path):
    # Arrange
    config_path = CONFIG_FILE
    config = configparser.ConfigParser()

    # Act
    write(config)

    # Assert
    assert os.path.isfile(config_path) is True
