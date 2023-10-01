#!/usr/bin/env python3

"""
__main__.py: TODO: Headline...

start in cli: python3 -m swiftguard or python3 -m swiftguard --cli
or in gui: python3 -m swiftguard --gui.

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.2"
__build__ = "2023.2"
__date__ = "2023-09-28"
__status__ = "Prototype"

# Imports.
import argparse

from swiftguard.utils.helpers import check_os


def main():
    # Check if host OS is supported.
    check_os()

    # Create argument parser to let the user choose between CLI and GUI.
    parser = argparse.ArgumentParser(
        prog="swiftGuard",
        description=f"swiftGuard v{__version__} ({__build__})\n\n"
        "Anti-forensic macOS tray application designed to "
        "safeguard your system by monitoring USB ports. It ensures your "
        "device's security by automatically initiating either a system "
        "shutdown or hibernation if an unauthorized device connects or a "
        "connected device is unplugged. It offers the flexibility to whitelist"
        " designated devices, to select an action to be executed and to set a "
        "countdown timer, allowing to disarm the shutdown process."
        "It can be run as a CLI or as a GUI, see following options.",
        epilog="For more information: "
        "https://github.com/Lennolium/swiftGuard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # CLI argument.
    parser.add_argument(
        "-c", "--cli", action="store_true", help="starts in CLI mode (default)"
    )

    # GUI argument.
    parser.add_argument(
        "-g",
        "--gui",
        action="store_true",
        help="starts in GUI mode (recommended for desktop)",
    )

    # Parse arguments.
    args = parser.parse_args()

    # Start GUI: We just import the GUI here, because it adds a lot of
    # dependencies, and the CLI should be as lightweight as possible.
    if args.gui:
        from swiftguard import app

        app.main()

    # Start CLI (default).
    else:
        from swiftguard import cli

        cli.main()


if __name__ == "__main__":
    main()
