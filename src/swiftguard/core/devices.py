#!/usr/bin/env python3

"""
This module contains classes for representing different types of
devices (USB, Bluetooth, Network). They are used to store the
information gathered by the Monitor class in a structured way.
The device classes include methods for comparing devices and for
generating a hash of a device, which can be used to detect changes in
the device configuration.
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-03-07"
__status__ = "Prototype/Development/Production"


# Imports.


class Devices:
    """
    Abstract base class for USB, Bluetooth and Network devices. It
    includes methods for comparing devices and generating a hash of a
    device, which can be used to detect changes in the device
    configuration.

    :cvar __slots__: The slots of the class for faster attribute access.
    :type __slots__: tuple
    """

    __slots__: tuple = ()

    def __repr__(self) -> str:
        """
        Return a string representation of the object with all its public
        attributes.

        :return: A string representation of the object.
        :rtype: str
        """

        res = [f"{attr}='{getattr(self, attr)}'" for attr in self.__slots__]
        return f"{type(self).__name__}({', '.join(res)})"

    def __format__(self, format_spec: str) -> str:
        """
        Return a nicely formatted representation of the object for
        use as user output.

        :param format_spec: The format specification.
        :type format_spec: str
        :return: A formatted string representation of the object.
        :rtype: str
        """

        if format_spec == "":
            return repr(self)

        elif format_spec == "out":
            return f">> {repr(self).split('(')[1].split(')')[0]} <<"

        else:
            return format(str(self), format_spec)

    def __eq__(self, other) -> bool:
        """
        Check if two objects are equal by comparing all their public
        attributes.

        :param other: The other object to compare with.
        :type other: Devices
        :return: True if the objects are equal, False otherwise.
        :rtype: bool
        """

        # Check if the other object is of the same class.
        if not isinstance(other, self.__class__):
            return False

        # Check if all attributes are equal (except whitelisted).
        for attr in self.__slots__:
            if attr.startswith("allowed"):
                continue

            if getattr(self, attr) != getattr(other, attr):
                return False

        return True

    def __lt__(self, other) -> bool:
        if not isinstance(other, Devices):
            return NotImplemented
        
        return getattr(self, "name", "") < getattr(other, "name", "")

    def __hash__(self) -> int:
        """
        Return a hash of object by hashing all its public attributes.

        :return: A hash of the object.
        :rtype: int
        """

        attrs: dict = {attr: getattr(self, attr)
                       for attr in self.__slots__
                       if not attr.startswith("allowed")}
        return hash(tuple(attrs.values()))

    def to_json(self) -> dict:
        """
        Create a dictionary containing all the public attributes of the
        object. Useful for serialization.

        :return: A dictionary of all attributes.
        :rtype: dict
        """

        return {attr: getattr(self, attr, None) for attr in self.__slots__}

    @classmethod
    def from_json(cls, data: dict) -> Devices | USB | Bluetooth | Network:
        """
        Create a new instance of the class from a dictionary.
        Useful for deserialization.

        :param data: The dictionary containing the attributes of the
            object.
        :type data: dict
        :return: A new instance of the class.
        :rtype: Devices | USB | Bluetooth | Network
        """

        return cls(**data)


class USB(Devices):
    """
    Class for representing USB devices. It includes the vendor ID, the
    product ID, the serial number, the name and the manufacturer of the
    USB device. It inherits from the Devices class and includes the
    class dunder methods for comparing devices and generating a hash of
    a device.

    :cvar __slots__: The slots of the class for faster attribute access.
    :type __slots__: tuple
    """

    __slots__: tuple = ("vendor_id", "product_id", "serial_num", "name",
                        "manufacturer", "allowed")

    def __init__(
            self,
            vendor_id: str,
            product_id: str,
            serial_num: str,
            name: str,
            manufacturer: str,
            allowed: bool = False,
            ) -> None:
        """
        Initialize a USB device with the class dunder methods from the
        Devices class.

        :param vendor_id: The vendor ID of the USB device.
        :type vendor_id: str
        :param product_id:  The product ID of the USB device.
        :type product_id: str
        :param serial_num: The serial number of the USB device.
        :type serial_num: str
        :param name: The name of the USB device.
        :type name: str
        :param manufacturer: The manufacturer of the USB device.
        :type manufacturer: str
        :param allowed: Whether the device is whitelisted or not
            (default: False).
        :type allowed: bool
        :return: None
        """

        self.vendor_id: str = vendor_id
        self.product_id: str = product_id
        self.serial_num: str = serial_num
        self.name: str = name
        self.manufacturer: str = manufacturer

        self.allowed: bool = allowed


class Bluetooth(Devices):
    """
    Class for representing Bluetooth devices. It includes the vendor ID,
    the product ID, the serial number, the name, the address and the type
    of the Bluetooth device. It inherits from the Devices class.

    :cvar __slots__: The slots of the class for faster attribute access.
    :type __slots__: tuple
    """

    __slots__: tuple = ("vendor_id", "product_id", "serial_num", "name",
                        "address", "type", "allowed")

    def __init__(
            self,
            vendor_id: str,
            product_id: str,
            serial_num: str,
            name: str,
            address: str,
            type: str,
            allowed: bool = False,
            ) -> None:
        """
        Initialize a Bluetooth device with the class dunder methods from
        the Devices class.

        :param vendor_id: The vendor ID of the Bluetooth device.
        :type vendor_id: str
        :param product_id:  The product ID of the Bluetooth device.
        :type product_id: str
        :param serial_num: The serial number of the Bluetooth device.
        :type serial_num: str
        :param name: The name of the Bluetooth device.
        :type name: str
        :param address: The address of the Bluetooth device.
        :type address: str
        :param type: The type of the Bluetooth device.
        :type type: str
        :param allowed: Whether the device is whitelisted or not
            (default: False).
        :type allowed: bool
        :return: None
        """

        self.vendor_id: str = vendor_id
        self.product_id: str = product_id
        self.serial_num: str = serial_num
        self.name: str = name
        self.address: str = address
        self.type: str = type

        self.allowed: bool = allowed


class Network(Devices):
    """
    Class for representing Network devices. It includes the name of the
    network. It inherits from the Devices class.

    :cvar __slots__: The slots of the class for faster attribute access.
    :type __slots__: tuple
    """

    __slots__: tuple = ("name", "allowed")

    def __init__(
            self,
            name: str,
            allowed: bool = False
            ) -> None:
        """
        Initialize a Network device with the class dunder methods from
        the Devices class.

        :param name: The name of the network.
        :type name: str
        :param allowed: Whether the device is whitelisted or not
            (default: False).
        :type allowed: bool
        :return: None
        """

        self.name: str = name

        self.allowed: bool = allowed
