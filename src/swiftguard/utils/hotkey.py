#!/usr/bin/env python3

"""
hotkey.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-03-05"
__status__ = "Prototype/Development/Production"

# Imports.
import logging
import signal

from PySide6.QtCore import QCoreApplication, QDateTime, QTimer
from PySide6.QtWidgets import QApplication
from quickmachotkey import ModifierKey, VirtualKey, mask, quickHotKey
from quickmachotkey.constants import cmdKey, shiftKey

from swiftguard.app import tray
from swiftguard.init import exceptions as exc
from swiftguard.constants import C

# Child logger.
LOGGER = logging.getLogger(__name__)


class HotKeyManager:
    class _MockConf:
        # Mock config class for integrating quickMacHotKey with the
        # standard swiftguard config handling.
        path = None

        def __init__(self, vk: VirtualKey, mk: mask) -> None:
            self.fullyQualifiedName: str = "app.HotKeyManager._handler"
            self.virtualKey: VirtualKey = vk
            self.modifierMask: ModifierKey = mk

        def loadConfiguration(self, _) -> tuple[VirtualKey, ModifierKey]:
            return self.virtualKey, self.modifierMask

        def saveConfiguration(self, _, vk: VirtualKey, mk: mask) -> None:
            self.virtualKey: VirtualKey = vk
            self.modifierMask: mask = mk

    # Initialize the global hotkey handler.
    mock_config = _MockConf(vk=VirtualKey(2),
                            mk=mask(cmdKey, shiftKey
                                    )
                            )

    def __init__(self) -> None:
        # Load the hotkey from the config.
        hotkey = C.cfg.CFG["hotkey"]
        self._handler.configure(virtualKey=VirtualKey(hotkey[0]),
                                modifierMask=mask(*hotkey[1])
                                )

        LOGGER.debug(f"Hotkeys initialized (key: '{hotkey[0]}', modifiers: "
                     f"'{hotkey[1]}')."
                     )

    @staticmethod
    @quickHotKey(
            virtualKey=VirtualKey(2),  # D
            modifierMask=mask(ModifierKey(256),  # shiftKey
                              ModifierKey(512)
                              ),  # cmdKey
            configurator=mock_config,
            )
    def _handler() -> None:
        print("Hotkey pressed!")
        app = QApplication.instance()
        app.tray.test_print()
        # TODO: Implement the hotkey action, that should be executed.

    def change(self, key: int, mods: list[int]) -> None:
        LOGGER.debug(f"Hotkeys were changed (key: '{key}', modifiers: "
                     f"'{mods}')."
                     )

        # Create modifier mask.
        mod_mask = [ModifierKey(mod) for mod in mods]

        # Change the hotkey.
        self._handler.configure(virtualKey=VirtualKey(key),
                                modifierMask=mask(*mod_mask)
                                )

        # Save to config.
        C.cfg.CFG["hotkey"] = (key, mods)
