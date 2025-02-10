#!/usr/bin/env python3

"""
core/monitor.py: Get information about connected devices.

This module contains a Monitor class for managing the connected and
whitelisted devices. The Monitor class uses the system_profiler command
to gather information about the devices. It also includes methods for
validating the system_profiler binary and for extracting device
information from the output of the system_profiler command.


**Usage:**

- monitor = Monitor()  # Initialize the Monitor class.

- usb_devices = monitor.get_usb()  # Get the USB devices.

- bluetooth_devices = monitor.get_bluetooth()

- network_devices = monitor.get_network()

"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-02-22"
__status__ = "Prototype/Development/Production"

# Imports.
import abc
import logging
import plistlib
import random
import stat
import traceback
from pathlib import Path
from typing import Type

from PySide6.QtCore import (QMutex, QObject, QThread, QWaitCondition, Signal,
                            Slot)
from PySide6.QtGui import QGuiApplication

from swiftguard.init import exceptions as exc, models
from swiftguard.constants import C
from swiftguard.utils import helpers, process
from swiftguard.core import integrity
from swiftguard.core import devices

# Child logger.
LOGGER = logging.getLogger(__name__)


class MonitorManager(QObject, metaclass=models.SingletonQt):
    _BINARY_PATH: Path = Path("/usr/sbin/system_profiler")
    _BINARY_VALIDATION: tuple[str, int, int] | None = None

    # Signals for communication to main app.
    running_sig: Signal = Signal(bool)
    updated_sig: Signal = Signal(bool)

    def __init__(self) -> None:
        super().__init__()

        self.running: bool = False

        # All implemented interfaces to monitor (add more if needed).
        self.interfaces: dict[str, Type[Monitor]] = {
                "USB": MonitorUSB,
                "Bluetooth": MonitorBluetooth,
                "Network": MonitorNetwork,
                }

        self.monitors: dict[str, Monitor | None] = {
                "USB": None,
                "Bluetooth": None,
                "Network": None
                }

        self.devices: dict = {
                "USB": [[], []],
                "Bluetooth": [[], []],
                "Network": [[], []],
                }

        self.start()

    def start(self) -> None:

        for inter, monitor in self.interfaces.items():
            self.monitors[inter] = monitor()
            self.monitors[inter].running_sig.connect(self.on_running)
            self.monitors[inter].updated_sig.connect(self.on_updated)
            self.monitors[inter].start(priority=QThread.Priority.HighPriority)

        workers_str = ", ".join(
                [f"{monitor.__class__.__qualname__} (ID: {monitor.thread_id})"
                 for monitor in self.monitors.values()]
                )

        LOGGER.info(
                f"{self.__class__.__qualname__} started listening on device "
                f"interfaces: {workers_str}"
                )

        self.running = True
        self.running_sig.emit(True)

    def stop(self) -> None:

        # No monitor is running.
        if not any(monitor.running for monitor in self.monitors.values()):
            return

        for monitor in self.monitors.values():
            if monitor.running:
                monitor.stop()

        workers_str = ", ".join(
                [f"{monitor.__class__.__qualname__} (ID: {monitor.thread_id})"
                 for monitor in self.monitors.values()]
                )

        LOGGER.info(
                f"{self.__class__.__qualname__} stopped listening on device "
                f"interfaces: {workers_str}"
                )

        self.running = False
        self.running_sig.emit(False)

    @Slot(bool)
    def on_running(self, running: bool) -> None:

        # If one monitor worker is not running, we mark the whole
        # MonitorManager as not running.

        if not running:
            self.running = False
            self.running_sig.emit(False)

    @Slot(str)
    def on_updated(self, interface: str) -> None:

        # Current state of devices from interface monitor.
        devices_curr: tuple[list, list] = (
                sorted(self.monitors[interface].devices_connected),
                sorted(self.monitors[interface].devices_not_connected))

        # Last state of devices saved in MonitorManager.
        devices_last: tuple[list, list] = (
                sorted(self.devices[interface][0]),
                sorted(self.devices[interface][1]),
                )

        # Interface devices state changed -> Emit updated signal.
        if devices_curr != devices_last:
            self.devices[interface] = [
                    self.monitors[interface].devices_connected,
                    self.monitors[interface].devices_not_connected
                    ]
            self.updated_sig.emit(True)


class Monitor(QThread):
    """
    Class for managing USB, Bluetooth and Network devices. It includes
    methods for validating the system_profiler binary, for extracting
    device information from the output of the system_profiler command,
    and for getting the USB, Bluetooth and Network devices. The Monitor
    class uses the system_profiler command to gather information about
    the devices, and the device classes (USB, Bluetooth, Network) are
    used to store this information in a structured way.

    :cvar _BINARY_PATH: The path to the system_profiler binary.
    :type _BINARY_PATH: Path
    """

    _BINARY_PATH: Path = Path("/usr/sbin/system_profiler")
    _BINARY_VALIDATION: tuple[str, int, int] | None = None

    running_sig: Signal = Signal(bool)
    updated_sig: Signal = Signal(str)

    def __init__(self) -> None:
        """
        Initialize the Monitor class with empty lists for the different
        types of devices.

        :return: None
        """

        super().__init__()

        # Thread management and communication.
        self.running: bool = False
        self.thread_id: str | None = None
        self.mutex: QMutex = QMutex()
        self.condition: QWaitCondition = QWaitCondition()

        self.devices_connected = []
        self.devices_not_connected = []

    @property
    @abc.abstractmethod
    def sleep_interval(self) -> int:
        pass

    @Slot()
    def run(self) -> None:
        self.running = True
        self.thread_id = self._thread_id()
        self.running_sig.emit(True)

        try:
            while self.running:

                self._validate_binary()

                # Get the current state of devices.
                self.devices_connected, self.devices_not_connected = self.get()
                self.updated_sig.emit(
                        self.__class__.__name__.replace("Monitor", "")
                        )

                if not self.running:
                    break

                # Sleep for given interval.
                self.mutex.lock()
                self.condition.wait(
                        self.mutex,
                        (self.sleep_interval * 1000),
                        )
                self.mutex.unlock()

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

    def stop(self) -> None:

        if not self.running:
            LOGGER.info(
                    f"{self.__class__.__qualname__} (ID: {self.thread_id}) "
                    f"is not running, but stopping was requested."
                    )
            return

        # if hasattr(self, "result") and self.result:
        #     print("terminate in stop")
        #     self.result.terminate()

        self.running = False
        self.running_sig.emit(False)

        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()

        # Wait for the thread to finish.
        self.quit()
        if not self.wait(2500):
            self.terminate()
            self.wait(2500)

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

    def _validate_binary(
            self,
            permission: int = stat.S_IXUSR,
            ) -> None:
        """
        Validate a binary file by checking its permissions, hash and
        size and if they changed since the last check.

        :param permission: Permission to check for (default: S_IXUSR).
        :type permission: int
        :raise exc.BinaryIntegrityError: If the binary file is not a
            regular file, not executable or has changed.
        :return: None
        """

        # First check if file exists.
        if not self._BINARY_PATH.exists():
            raise exc.BinaryIntegrityError(
                    f"Needed binary '{self._BINARY_PATH}' not found!"
                    )

        binary_stat = self._BINARY_PATH.stat()

        # Check standard binary permissions (regular file, executable).
        if not (binary_stat.st_mode & stat.S_IFREG):
            raise exc.BinaryIntegrityError(
                    f"Binary '{self._BINARY_PATH}' is not a regular file! "
                    f"ST_MODE: {binary_stat.st_mode}."
                    )
        elif not (binary_stat.st_mode & permission):
            raise exc.BinaryIntegrityError(
                    f"Binary '{self._BINARY_PATH}' is not executable! "
                    f"ST_MODE: {binary_stat.st_mode}."
                    )

        # Not the first run, so check if the binary has changed.
        validation = self._BINARY_VALIDATION
        if validation:
            if ((integrity.get_file_hash(self._BINARY_PATH),
                 binary_stat.st_size,
                 binary_stat.st_mode,)
                    != validation):
                raise exc.BinaryIntegrityError(
                        f"Binary '{self._BINARY_PATH}' has changed!\n"
                        f"SIZE: exp={validation[1]}, "
                        f"got={binary_stat.st_size}; "
                        f"ST_MODE: exp={validation[2]}, "
                        f"got={binary_stat.st_mode};"
                        f"HASH: exp={validation[0]}, "
                        f"got={integrity.get_file_hash(self._BINARY_PATH)}."

                        )

        self._BINARY_VALIDATION = (
                integrity.get_file_hash(self._BINARY_PATH),
                binary_stat.st_size,
                binary_stat.st_mode,
                )

    def _run_system_profiler(
            self,
            bus: str,
            timeout: int = 5
            ) -> dict:
        """
        Run the system_profiler command and capture its output.
        For every run, the binary is first validated.

        :param bus: The bus to check (e.g. "USB", "Bluetooth", ...).
        :type bus: str
        :param timeout: Time to wait for respond from system_profiler,
            as Wi-Fi monitoring takes some time (default: 5 sec
            recommended for network: 15 sec).
        :type timeout: int
        :raise exc.BusNotSupportedError: If the bus is not supported.
        :raise exc.SystemProfilerError: If the system_profiler command
            fails.
        :return: The output of the system_profiler command.
        :rtype: dict
        """

        # Validate the input bus, to prevent command injection.
        if bus not in ("USB", "Bluetooth", "AirPort"):
            raise exc.BusNotSupportedError(
                    f"Bus '{bus}' not supported! "
                    f"Supported buses: 'USB', 'Bluetooth' and 'AirPort'."
                    )

        # Validate binary integrity for each run.
        self._validate_binary()

        self.result = process.Process(
                binary_path=self._BINARY_PATH,
                args=(f"SP{bus}DataType",
                      "-xml",
                      "-detailLevel",
                      "full"),
                timeout=timeout,
                blocking=True,
                ).run()

        # Return the output of the system_profiler command as parsed
        # plist (XML) -> dict.
        if self.result.return_code == 0:
            return plistlib.loads(
                    self.result.stdout.encode(),
                    fmt=plistlib.FMT_XML,
                    )[0]["_items"]

        # Timeout.
        elif self.result.return_code == 2:
            raise exc.SystemProfilerError(
                    f"Built-in binary 'system_profiler' timed out "
                    f"after {timeout} seconds!"
                    )

        # Error.
        else:
            raise exc.SystemProfilerError(
                    f"Not able to detect {bus} devices! "
                    f"Code={self.result.return_code}, "
                    f"Stdout={self.result.stdout}, "
                    f"Stderr={self.result.stderr}."
                    )

        # try:
        #     with subprocess.Popen(
        #             (
        #                     self._BINARY_PATH,
        #                     f"SP{bus}DataType",
        #                     "-xml",
        #                     "-detailLevel",
        #                     "full",
        #                     ),
        #             stdout=subprocess.PIPE,
        #             stderr=subprocess.PIPE,
        #             text=False,
        #             shell=False,
        #             start_new_session=True,  # Do not: preexec_fn=os.setsid
        #             ) as self.result:
        #
        #         output, error = self.result.communicate(timeout=timeout)
        #
        # except subprocess.TimeoutExpired:
        #     try:
        #         os.killpg(os.getpgid(self.result.pid), signal.SIGTERM)
        #
        #         # If the process is still running, kill it.
        #         if self.result.poll() is None:
        #             self.result.kill()
        #
        #     except ProcessLookupError:
        #         pass
        #
        #     raise exc.SystemProfilerError(
        #             f"Built-in binary 'system_profiler' timed out "
        #             f"after {timeout} seconds!"
        #             )
        #
        # # Negative return code means the process was terminated by a
        # # signal (POSIX only).
        # if self.result.returncode < 0:
        #
        #     # If the process is still running, kill it.
        #     if self.result.poll() is None:
        #         self.result.kill()
        #
        #     raise exc.SystemProfilerTerminated(
        #             "Gracefully terminated the 'system_profiler' process,
        #             to "
        #             "prevent hanging during application exit."
        #             )
        #
        # # If the return code is greater than 0, an error occurred.
        # elif self.result.returncode > 0:
        #     try:
        #         os.killpg(os.getpgid(self.result.pid), signal.SIGTERM)
        #
        #         # If the process is still running, terminate it.
        #         if self.result.poll() is None:
        #             self.result.terminate()
        #             self.result.wait()
        #
        #     except ProcessLookupError:
        #         pass
        #
        #     raise exc.SystemProfilerError(
        #             f"Not able to detect {bus} devices! Error: "
        #             f"{error.decode('utf-8').strip()}"
        #             )
        #
        # else:
        #     # Return the output of the system_profiler command as parsed
        #     # plist (XML) -> dict.
        #     return plistlib.loads(output)[0]["_items"]

        # try:
        #     # Terminate the process group.
        #     os.killpg(os.getpgid(self.result.pid), signal.SIGTERM)
        #
        #     # First try to kill the process.
        #     if self.result.poll() is None:
        #         self.result.kill()
        #         self.result.wait()
        #
        #     # Second try.
        #     if self.result.poll() is None:
        #         os.killpg(os.getpgid(self.result.pid), signal.SIGKILL)
        #
        # except Exception:
        #     pass

    @abc.abstractmethod
    def get(self) -> list[list[devices.Devices] | list]:
        """
        Must be implemented by subclasses.
        """
        pass


class MonitorUSB(Monitor):
    """
    ...
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def sleep_interval(self) -> int:
        return C.cfg.CFG["interval"]

    def _extract(self, result: dict) -> None:
        """
        This is a recursive function that checks if the devices are
        built-in. It also checks if there are items inside
        (e.g., USB hubs). If so, it will recursively check what's inside
        those items as well. It modifies the instances devices list.

        :param result: Pass the result of a previous call.
        :type result: dict
        :return: None.
        """

        # Do not take devices with "Built-in_Device=Yes".
        try:
            result["Built-in_Device"]

        except LookupError:
            # Check if vendor_id/product_id is available for this one.
            if "vendor_id" in result and "product_id" in result:

                # Vendor ID.
                try:
                    vendor_id = C.sec.MONITOR_RE.findall(
                            result["vendor_id"]
                            )[0].strip()
                except LookupError:
                    # This is not a standard vendor_id (probably
                    # apple_vendor_id instead of 0x....).
                    vendor_id = result.get("vendor_id",
                                           None
                                           )
                    vendor_id = vendor_id.strip() if vendor_id else None

                # Product ID.
                try:
                    product_id = C.sec.MONITOR_RE.findall(
                            result["product_id"]
                            )[0].strip()
                except LookupError:
                    # Assume this is not a standard product_id (0x....).
                    product_id = result.get("product_id",
                                            None
                                            )
                    product_id = product_id.strip() if product_id else None

                # Serial number.
                serial_num = result.get("serial_num",
                                        None
                                        )
                serial_num = serial_num.strip() if serial_num else None

                # Device name.
                name = result.get("_name",
                                  None
                                  )
                name = name.strip() if name else None

                # Manufacturer.
                manufacturer = result.get("manufacturer",
                                          None
                                          )
                manufacturer = manufacturer.strip() if manufacturer else None

                # If it is an Apple device, lookup the exact name, using
                # bcd_device (e.g. bcd: 13.04 -> iPhone 12 Pro Max)
                if vendor_id == "apple_vendor_id" and name.lower() in (
                        "iphone",
                        "ipod",
                        "ipad",
                        "watch",
                        ):
                    name = helpers.apple_lookup(
                            name=name,
                            bcd=result["bcd_device"]
                            )

                device = devices.USB(vendor_id,
                                     product_id,
                                     serial_num,
                                     name,
                                     manufacturer, )

                # TODO: testen ob die if abfrage notwendig ist!
                if device not in self.devices_connected:
                    self.devices_connected.append(device)

            # No vendor_id/product_id found for this device.
            else:
                pass

        # Check if there are items inside (e.g., for USB hubs).
        try:
            # Check what's inside the _items array (recursively).
            for result_deep in result["_items"]:
                self._extract(result_deep)

        except LookupError:
            pass

    def get(self) -> list[list[devices.USB] | list]:
        """
        The function returns a list with a list of USB instances each
        containing the following information:

            - vendor_id (e.g. '0x05ac' -> '05ac')
            - product_id (e.g. '0x12a8' -> '12a8')
            - serial number (if available, otherwise 'None')
            - device name (e.g. 'iPhone 12 Pro Max')
            - manufacturer (e.g. 'Apple Inc.')

        :return: A list with a list of USB device instances.
        :rtype: list[list[USB]]
        """

        # Reset the list.
        self.devices_connected: list[devices.USB] = []

        # Run the loop and return the list of devices.
        for result in self._run_system_profiler(bus="USB"):
            self._extract(result=result)

        return [self.devices_connected, []]


class MonitorBluetooth(Monitor):

    def __init__(self) -> None:
        super().__init__()

    @property
    def sleep_interval(self) -> int:
        return 5

    def _extract(self, result: dict) -> None:
        """
        Extract the Bluetooth devices from the system_profiler output
        and add them as instances to the class list.

        :param result: Pass the result of a previous call.
        :type result: dict
        :raise exc.BluetoothDisabledError: If Bluetooth is turned off.
        :raise exc.BluetoothControllerError: If the controller state
            (on/off) could not be determined.
        :return: None.
        """

        # Check if Bluetooth is turned on or off.
        try:
            if (result["controller_properties"]["controller_state"].endswith(
                    "_off"
                    )):
                raise exc.BluetoothDisabledError(
                        "Bluetooth is turned off."
                        )

        except LookupError:
            raise exc.BluetoothControllerError(
                    "Could not determine Bluetooth controller state."
                    )

        # Add devices as instances to the class list.
        for connection_status in ("device_connected", "device_not_connected"):
            try:
                for device in result[connection_status]:
                    for name, device_info in device.items():

                        # Vendor ID.
                        try:
                            vendor_id = C.sec.MONITOR_RE2.findall(
                                    device_info["device_vendorID"]
                                    )[0].strip()
                        except LookupError:
                            # This is not a standard vendor_id (probably
                            # apple_vendor_id instead of 0x....).
                            vendor_id = device_info.get("device_vendorID",
                                                        None
                                                        )
                            vendor_id = vendor_id.strip() if vendor_id else \
                                None

                        # Product ID.
                        try:
                            product_id = C.sec.MONITOR_RE2.findall(
                                    device_info["device_productID"]
                                    )[0].strip()
                        except LookupError:
                            # Assume this is not a standard product_id (
                            # 0x....).
                            product_id = device_info.get("device_productID",
                                                         None
                                                         )
                            product_id = product_id.strip() if product_id \
                                else None

                        # Serial number.
                        serial_num = device_info.get("device_serialNumber",
                                                     None
                                                     )
                        serial_num = serial_num.strip() if serial_num else None

                        # Device address (e.g. '8X:9G:UI:Z3:AB:09').
                        address = device_info.get("device_address",
                                                  None
                                                  )
                        address = address.strip() if address else None

                        # Device type (e.g. 'Headphones', 'Speaker', ...).
                        dev_type = device_info.get("device_minorType",
                                                   None
                                                   )
                        dev_type = dev_type.strip() if dev_type else None

                        device = devices.Bluetooth(vendor_id,
                                                   product_id,
                                                   serial_num,
                                                   name,
                                                   address,
                                                   dev_type, )

                        if connection_status == "device_connected":

                            if device not in self.devices_connected:
                                self.devices_connected.append(device)

                        else:
                            if (device not in
                                    self.devices_not_connected):
                                self.devices_not_connected.append(
                                        device
                                        )

            except LookupError:
                pass

    def get(self) -> list[list[devices.Bluetooth]]:
        """
        The function returns a list of two list (connected and
        not-connected) of  Bluetooth instances each containing the
        following information:

            - vendor_id (e.g. '0x05ac' -> '05ac')
            - product_id (e.g. '0x12a8' -> '12a8')
            - serial number (if available, otherwise 'None')
            - device name ('AirPods Pro')
            - device address (e.g. '8X:9G:UI:Z3:AB:09')
            - device type (e.g. 'Headphones', 'Speaker', ...)

        :return: A list of two lists of Bluetooth device instances.
        :rtype: list[list[Bluetooth], list[Bluetooth]]
        """

        # Reset the lists.
        self.devices_connected: list[devices.Bluetooth] = []
        self.devices_not_connected: list[devices.Bluetooth] = []

        # Run the loop and return the list of devices.
        for result in self._run_system_profiler(bus="Bluetooth"):
            self._extract(result)

        return [self.devices_connected,
                self.devices_not_connected, ]


class MonitorNetwork(Monitor):

    def __init__(self) -> None:
        super().__init__()

    @property
    def sleep_interval(self) -> int:
        return 15

    def _extract(self, result: dict) -> None:
        """
        Extract the Network devices from the system_profiler output and
        add them as instances to the class list.

        :param result: Pass the result of a previous call.
        :type result: dict
        :raise exc.NetworkDisabledError: If network (Wi-Fi/Ethernet) is
            turned off.
        :raise exc.NetworkControllerError: If the controller state
            (on/off) could not be determined.
        :return: None.
        """

        try:
            # Get the standard interface (en0).
            interface = None
            for interface in result["spairport_airport_interfaces"]:
                if interface["_name"] == "en0":
                    break

            controller_state = interface["spairport_status_information"]

        except LookupError:
            raise exc.NetworkControllerError(
                    "Could not determine network controller state."
                    )

        # Wi-Fi is disabled.
        if controller_state == "spairport_status_off":
            raise exc.NetworkDisabledError(
                    "Network (WiFi/Ethernet) is turned off."
                    )

        # Wi-Fi enabled and connected to a network.
        elif controller_state == "spairport_status_connected":
            try:
                networks_near = (
                        interface["spairport_airport_other_"
                                  "local_wireless_networks"])
                network_connected = interface[("spairport_current_"
                                               "network_information")]

            except LookupError:
                raise exc.NetworkControllerError(
                        "Could not find any Networks."
                        )

        # Wi-Fi is enabled, but not connected to any network.
        else:
            try:
                network_connected = None
                networks_near = (
                        interface["spairport_airport_"
                                  "local_wireless_networks"])

            except LookupError:
                raise exc.NetworkControllerError("Could not find any "
                                                 "Networks."
                                                 )

        # Add all networks (connected and not connected) as instances
        # to the class list.
        self.devices_not_connected = set()
        for network in networks_near:
            self.devices_not_connected.add(
                    devices.Network(name=network["_name"])
                    )

        # If we are connected to a network, add it to the list of
        # connected networks and remove it from the list of not
        # connected networks.
        self.devices_connected = set()
        if network_connected:
            devices_connected_inst = devices.Network(name=network_connected[
                "_name"]
                                                     )
            self.devices_connected.add(devices_connected_inst)
            try:
                self.devices_not_connected.remove(
                        devices_connected_inst
                        )
            except KeyError:
                pass

        # Convert to lists for easier handling.
        self.devices_not_connected = list(
                self.devices_not_connected
                )
        self.devices_connected = list(
                self.devices_connected
                )

    def get(self) -> list[list[devices.Network]]:
        """
        The function returns a list of two list (connected and
        not-connected) of Network instances each containing the
        following information:

            - name (e.g. 'MyNetwork')

        :return: A list of two lists of Network device instances.
        :rtype: list[list[Network], list[Network]]
        """

        # Reset the lists.
        self.devices_connected: list[devices.Network] = []
        self.devices_not_connected: list[devices.Network] = []

        # We need a longer timeout for Wi-Fi monitoring, as it takes
        # some time for the controller to scan for networks.
        for result in self._run_system_profiler(bus="AirPort", timeout=15):
            self._extract(result)

        return [self.devices_connected,
                self.devices_not_connected, ]


if __name__ == "__main__":
    import time

    qapp = QGuiApplication([])

    # dev = MonitorUSB()
    # dev2 = MonitorNetwork()

    dev_mgr = MonitorManager()


    def test_print(devs):
        print("test_print:", dev_mgr.devices)


    dev_mgr.updated_sig.connect(test_print)

    print("Checking devices...")
    # dev.start()
    # dev2.start()

    # dev_mgr.start()

    qapp.exec()
