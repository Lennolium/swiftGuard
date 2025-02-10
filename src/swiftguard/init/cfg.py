#!/usr/bin/env python3

"""
init/cfg.py: Complete module to manage the file configuration of app.

This module contains the ConfigurationManager class, which is used to
load, save, and modify the application's configuration. The
configuration is stored in a file and can be encrypted with a password
to enhance security. The ConfigurationManager class implements the
Singleton pattern to ensure that only one instance of the class exists.
This prevents inconsistencies in the configuration. The configuration is
stored as a JSON file and can contain values of various data types,
including strings, numbers, boolean values, and lists. This module also
includes functions for verifying the integrity of the configuration
file. A hash of the file is created and stored, and this hash is used to
verify whether the file has been modified since the last save.


**USAGE:**

*Create a new instance (automatically creates encrypted config file and
saves the key in the OS keyring). It uses the default config dict.*


- from swiftguard.init import cfg
- cfg = cfg.ConfigurationManager(config_file=Path("./config.json"),
  config_default={"section1": {"setting1": "value1"}})

*Get the current value for a setting (only pass the setting name, not
the section). ConfigurationError is raised for non-existing settings.*

- value1 = cfg["setting1"]

*Set a new value for a setting. It saves the changes to the config file
and ensures the correct data type. ConfigurationError is raised for
invalid data types and non-existing settings. Only the same data types
as in the default config are allowed.*

- cfg["setting1"] = "new_value1"

*Reset the configuration to the default configuration and save the
changes to the config file.*

- cfg.reset()

*Check the integrity of the configuration file (hash comparison). If the
file has been tampered with, a ConfigurationIntegrityError is raised.*

- cfg.integrity()

*Add or remove devices from the whitelist. The device type is
auto-detected and added to the corresponding whitelist.*

- from swiftguard.core.devices import USB
- cfg.whitelist(device=USB("device1"), add=True)
- cfg.whitelist(device=USB("device1"), add=False)

"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__date__ = "2024-02-18"
__status__ = "Prototype/Development/Production"

# Imports.
import hashlib
import json
import logging
import traceback
from copy import deepcopy
import keyring as kr
from cryptography.fernet import Fernet
from pathlib import Path

from swiftguard.init import exceptions, models
from swiftguard.core.devices import Bluetooth, Network, USB

# Child logger.
LOGGER = logging.getLogger(__name__)

# Monkey patch the JSON encoder to use the to_json method of the class
# if it exists, otherwise use the default encoder, needed for
# serializing custom objects/classes.
json._default_encoder.default = (
        lambda obj: getattr(obj.__class__,
                            "to_json",
                            json._default_encoder.default
                            )(obj))


# Same for deserialization.
def devices_from_json(dct: dict) -> dict | USB | Bluetooth | Network:
    """
    Deserialize the JSON string to the corresponding class object.

    :param dct: The dictionary to deserialize.
    :type dct: dict
    :return: The deserialized object.
    :rtype: dict | USB | Bluetooth | Network
    """

    if not isinstance(dct, dict):
        return dct

    for cls in (USB, Bluetooth, Network):
        if set(dct.keys()) == set(cls.__slots__):
            return cls(**dct)

    return dct


def get_file_hash(fp: str | Path) -> str:
    """
    Generate a hash for a file using the secure blake2b algorithm.

    :param fp: file path of the file to hash.
    :type fp: str
    :return: hash of the file.
    :rtype: str
    """

    # Needed if swiftGuard is not yet initialized.
    try:
        from swiftguard.constants import C
        pepper = C.sec.PEPPER
    except Exception:
        pepper = b"swiftGuard-2024"

    sha = hashlib.blake2b(person=pepper)
    with open(fp, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


class ConfigurationManager(metaclass=models.Singleton):
    """
    Configuration manager to access and modify the configuration file.

    :cvar _config_hash: The hash of the configuration file.
    :type _config_hash: str
    :ivar config: The configuration as a dictionary.
    :type config: dict
    """

    _config_hash = None

    def __init__(self, config_file: Path, config_default: dict) -> None:
        """
        Initialize the configuration manager.

        :param config_file: The path to the configuration file, defaults
            to the default configuration file.
        :type config_file: Path
        :param config_default: Default configuration as a dictionary.
        :type config_default: dict
        :raises ConfigurationError: If the configuration file could
            not be loaded.
        :raises ConfigurationIntegrityError: If the configuration file
            has been tampered with.
        """

        # Check if configuration has already been loaded (singleton).
        if hasattr(self, "config"):
            return

        self.config_file = config_file
        self.config_default = config_default

        # Retrieve the key from the keyring.
        key = kr.get_password(service_name="swiftGuard-key",
                              username="swiftguard@lennolium.dev"
                              )

        # The app is started for first time, the key/config hash or the
        # config file were deleted, so we create a new key and
        # corresponding file.
        try:
            if (not key or
                    not self.config_file.exists(follow_symlinks=False) or
                    not kr.get_password(
                            service_name="swiftGuard-hash",
                            username="swiftguard@lennolium.dev"
                            )):
                self.config = self._create()

            # Not the first start.
            else:
                # Load the configuration from the file on disk.
                self.config = self._load()

                # User updated swiftGuard, so we migrate old settings to
                # the new version, where it is possible.
                if self.config.get("Other", {}).get("version", ""
                                                    ) != __version__:
                    self._migrate()

        except OSError as e:
            raise exceptions.ConfigurationError(e)
        except Exception as e:
            raise exceptions.ConfigurationIntegrityError(e)

        LOGGER.debug("ConfigurationManager has been initialized.")

    def __getitem__(
            self,
            setting: str
            ) -> str | int | float | bool | list | None:
        """
        Get an item from the configuration.

        :param setting: The setting to get from the configuration.
        :type setting: str
        :raises ConfigurationError: If the setting is not in the
            configuration.
        :return: The setting from the configuration.
        :rtype: str | int | float | bool | list | None
        """

        # Get the setting from the configuration.
        for section in self.config:
            if setting in self.config[section]:

                # Redact sensitive information.
                if setting in ("password", "smtp_password", "shred_paths"):
                    value = "********"
                elif "password" in setting:
                    value = "********"
                else:
                    value = self.config[section][setting]
                LOGGER.debug(f"Setting '{setting}' has been retrieved: "
                             f"'{value}'."
                             )
                return self.config[section][setting]

        raise exceptions.ConfigurationError(
                f"Setting '{setting}' is not in the configuration."
                )

    def __setitem__(
            self,
            setting: str,
            value: str | int | bool | list | None
            ) -> None:
        """
        Set a new value in the configuration and save the changes to
        the config file.

        :param setting: The setting in the section.
        :type setting: str
        :param value: The value to set the configuration setting to.
        :type value: str | int | float | bool | list | None
        :raises ConfigurationError: If the setting is not in the
            configuration.
        :raises ConfigurationIntegrityError: If the configuration file
            could not be saved.
        :return: None.
        """

        # Validate input:
        # Read-only.
        if setting in ("release_hash",):
            raise exceptions.ConfigurationError(
                    f"Setting '{setting}' is read-only."
                    )

        # Only strings allowed.
        elif setting in ("action", "password",
                         "receiver_name", "receiver_email", "smtp_email",
                         "smtp_password", "smtp_server",
                         "version", "log_level",):
            if not (isinstance(value, str)
                    or value is None):
                raise exceptions.ConfigurationError(
                        f"Invalid type '{type(value)}' for setting "
                        f"'{setting}'. Only 'str' or 'None' is allowed."
                        )

        # Only integers allowed.
        elif setting in ("delay", "interval", "smtp_port"):
            if not isinstance(value, int):
                raise exceptions.ConfigurationError(
                        f"Invalid type '{type(value)}' for setting "
                        f"'{setting}'. Only 'int' is allowed."
                        )

        # Only boolean values allowed.
        elif setting in ("autostart", "check_updates", "delay_sound",
                         "usb_enabled", "bluetooth_enabled",
                         "bluetooth_enabled", "network_enabled",
                         "network_strict", "touchid", "shred_enabled",
                         "email_enabled", "take_photo"):
            if not isinstance(value, bool):
                raise exceptions.ConfigurationError(
                        f"Invalid type '{type(value)}' for setting "
                        f"'{setting}'. Only 'bool' is allowed."
                        )

        # Only lists allowed.
        elif setting in ("hotkey", "usb", "bluetooth", "network",
                         "shred_paths"):

            if not isinstance(value, list):
                raise exceptions.ConfigurationError(
                        f"Invalid type '{type(value)}' for setting "
                        f"'{setting}'. Only 'list' is allowed."
                        )

            # Deep check for paths to shred.
            if setting == "shred_paths":
                for path in value:
                    if not isinstance(path, str):
                        raise exceptions.ConfigurationError(
                                f"Invalid type '{type(path)}' for "
                                f"setting '{setting}'. Only 'str' is allowed."
                                )

            # Deep check for whitelist elements (only USB, Bluetooth and
            # Network class objects allowed).
            elif setting in ("usb", "bluetooth", "network"):
                for elem in value:
                    if not isinstance(elem, (USB, Bluetooth, Network)):
                        raise exceptions.ConfigurationError(
                                f"Invalid type '{type(elem)}' for "
                                f"setting '{setting}'. Only 'USB', "
                                f"'Bluetooth' and 'Network' is allowed."
                                )

        # Setting not in the configuration.
        else:
            raise exceptions.ConfigurationError(
                    f"Setting '{setting}' is not in the configuration."
                    )

        # Set the setting in the configuration.
        for section in self.config:
            if setting in self.config[section]:
                self.config[section][setting] = value
                break

        try:
            # Save the changes to the config file.
            self._save()

        except OSError as e:
            raise exceptions.ConfigurationError(e)

        except Exception as e:
            raise exceptions.ConfigurationIntegrityError(e)

        # Redact sensitive information.
        if setting in ("password", "smtp_password", "shred_paths"):
            value = "********"
        elif "password" in setting:
            value = "********"
        LOGGER.debug(f"Setting '{setting}' has been set: '{value}'.")

    def __repr__(self) -> str:
        """
        Return a string representation of the configuration manager.
        Not usable for direct class instantiation, but for debugging
        purposes and validation.

        :return: String representation of the configuration manager.
        :rtype: str
        """

        res = set()
        for section in self.config:
            for setting in self.config[section]:
                res.add(f"{setting}={self.config[section][setting]}")
        return f"{self.__class__.__name__}({', '.join(res)})"

    def _migrate(self) -> None:
        """
        If settings were added or removed in new version, we reflect
        these changes in the config file. Also, we migrate the user's
        settings, if they are still present/valid.

        :return: None.
        """

        config_rel = deepcopy(self.config_default)

        try:
            for cat, values in config_rel.items():
                for setting, value in values.items():
                    if setting in self.config.get(cat, {}):
                        # We do not migrate the old version or hash.
                        if setting == "version" or setting == "release_hash":
                            continue
                        config_rel[cat][setting] = (
                                self.config[cat][setting]
                        )

            # Save the updated config_default back to the config file.
            self.config = deepcopy(config_rel)
            self._save()

            LOGGER.info("Configuration has been migrated to the new version.")

        except Exception as e:
            LOGGER.warning(f"Could not migrate the configuration to the "
                           f"new version. Resetting to default. \n"
                           f"{e.__class__.__name__}: {e} \n"
                           f"{traceback.format_exc()}"
                           )
            self.reset()

    def _create(self) -> dict:
        """
        Create the configuration file from the default configuration,
        encrypt it, save it to disk and store the encryption key in the
        OS keyring.

        :return: The default configuration.
        :rtype: dict
        """

        # Generate a key for the encryption and store it in OS keyring.
        key: bytes = Fernet.generate_key()
        kr.set_password(
                "swiftGuard-key",
                "swiftguard@lennolium.dev",
                key.decode(),
                )

        # Encrypt the default configuration and save it to disk.
        fernet = Fernet(key)
        config_str = json.dumps(self.config_default)
        config_enc = fernet.encrypt(config_str.encode())

        with open(self.config_file, "wb") as f:
            f.write(config_enc)

        # Get hash of the config file (for runtime integrity checks) and
        # store it to memory and in OS keyring.
        self._config_hash = get_file_hash(self.config_file)
        kr.set_password(
                "swiftGuard-hash",
                "swiftguard@lennolium.dev",
                self._config_hash,
                )
        self.integrity()

        LOGGER.info("Configuration has been created.")

        return self.config_default

    def _load(self) -> dict:
        """
        Load the configuration from the config file on disk.

        :return: The configuration as a dictionary.
        :raises ConfigurationIntegrityError: If the configuration file
            has been tampered with.
        :rtype: dict
        """

        # Latest hash of the config file.
        self._config_hash = kr.get_password("swiftGuard-hash",
                                            "swiftguard@lennolium.dev"
                                            )
        self.integrity()

        # Retrieve the encryption key for the cfg from the keyring.
        key = kr.get_password("swiftGuard-key",
                              "swiftguard@lennolium.dev"
                              )
        fernet = Fernet(key=key)

        # Read the encrypted data from the file.
        with open(self.config_file, "rb") as f:
            config_enc = f.read()

        # Decrypt the data.
        config_str = fernet.decrypt(config_enc).decode()

        # Convert the string back to a dictionary.
        config = json.loads(s=config_str, object_hook=devices_from_json)

        LOGGER.debug("Configuration has been loaded from disk.")

        return config

    def _save(self) -> None:
        """
        Save the current configuration to the config file on disk.

        :return: None.
        """

        # Retrieve the key from the keyring
        key = kr.get_password("swiftGuard-key", "swiftguard@lennolium.dev")

        fernet = Fernet(key=key)

        # Convert the configuration to a string and encrypt it.
        config_str = json.dumps(self.config)
        config_enc = fernet.encrypt(config_str.encode())

        # Write the encrypted configuration to the file.
        with open(self.config_file, "wb") as f:
            f.write(config_enc)

        # Get hash of the config file (for runtime integrity checks) and
        # store it in memory and in the OS keyring.
        self._config_hash = get_file_hash(self.config_file)
        kr.set_password(
                "swiftGuard-hash",
                "swiftguard@lennolium.dev",
                self._config_hash,
                )
        self.integrity()

        LOGGER.debug("Configuration has been saved to disk.")

    def reset(self) -> None:
        """
        Reset the configuration to the default configuration and save the
        changes to the config file.

        :return: None.
        """

        # Reset the configuration to the default configuration.
        self.config = deepcopy(self.config_default)

        # Save the changes to the config file.
        self._save()

        LOGGER.info("Configuration has been reset to default.")

    def integrity(self) -> None:
        """
        Check the integrity of the configuration file.

        :raises ConfigurationIntegrityError: If the configuration file
            has been tampered with.
        :return: None.
        """

        # Get hash of the config file and check if it matches the last
        # saved hash.
        if (not self.config_file.exists(follow_symlinks=False)
                or self._config_hash != get_file_hash(self.config_file)):
            raise exceptions.ConfigurationIntegrityError(
                    f"Integrity of configuration file '{self.config_file}' "
                    f"compromised!"
                    )

    def whitelist(
            self,
            device: USB | Bluetooth | Network,
            add: bool = True,
            ) -> None:
        """
        Add or remove devices from the whitelist. The device type is
        auto-detected and added to the corresponding whitelist.

        :param device: The device to add/remove from the whitelist.
        :type device: USB | Bluetooth | Network
        :param add: True -> add to whitelist (default), False -> remove
            from the whitelist.
        :type add: bool
        :raises ConfigurationError: If the device type is unknown.
        :return: None.
        """

        # Check if the interface is known.
        if not isinstance(device, (USB, Bluetooth, Network)):
            raise exceptions.ConfigurationError(
                    f"Unknown device type: '{device.__class__.__name__}'."
                    f"Only USB, Bluetooth and Network classes are allowed."
                    )

        # Get the whitelist for the interface from the configuration.
        whitelist: list = self[device.__class__.__name__.lower()]

        # Add or remove the device from the whitelist.
        if add:
            whitelist.append(device)
            LOGGER.info(f"Added {device.__class__.__name__}-device "
                        f"to the whitelist: {device:out}"
                        )

        else:
            if device in whitelist:
                whitelist.remove(device)
                LOGGER.info(f"Removed {device.__class__.__name__}-device "
                            f"from the whitelist {device:out}"
                            )

            else:
                LOGGER.warning(f"{device.__class__.__name__}-device not in "
                               f"whitelist. Could not remove {device:out}"
                               )

        # Update the configuration with the new whitelist and save to
        # the config file on disk.
        self[device.__class__.__name__.lower()] = whitelist

#
# if __name__ == "__main__":
#     try:
#         CONF = ConfigurationManager()
#     except exceptions.ConfigurationError as e:
#         print("You need to reset swiftGuard. ConfigurationError:", e)
#         exit(1)
#
#     print("GET:", CONF["version"])
#     print("INTEGRITY:", CONF._config_hash)
#
#     CONF["version"] = "0.1.1"
#     print("SETTET:", CONF["version"])
#     print("INTEGRITY:", CONF._config_hash)
#
#     CONF = ConfigurationManager()
#     print("SINGLETON TEST:", CONF["version"])
#     print("INTEGRITY:", CONF._config_hash)
#
#     CONF.reset()
#     print("RESETTET:", CONF["version"])
#     print("INTEGRITY:", CONF._config_hash)
#
#     CONF["version"] = "0.1.0"
#     print("GET:", CONF["version"])
#     print("INTEGRITY:", CONF._config_hash)
