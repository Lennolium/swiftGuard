#!/usr/bin/env python3

"""
test_cli.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2023.3"
__date__ = "2023-10-09"
__status__ = "Development"

# Imports.

import signal
from unittest.mock import patch

import pytest

from swiftguard.cli import exit_handler, handle_exception, main


############################################
#            handle_exception()            #
############################################


# Happy path
@pytest.mark.parametrize(
    "exc_type, exc_value, exc_traceback",
    [
        (
            ValueError,
            ValueError("Test error"),
            "traceback",
        ),
        (
            OSError,
            OSError(2, "No such file"),
            "traceback",
        ),
        (
            IndexError,
            IndexError("list index out of range"),
            "traceback",
        ),
    ],
    ids=["builtin", "oserror", "indexerror"],
)
@patch("swiftguard.cli.LOGGER", autospec=True)
@patch("swiftguard.cli.exit_handler", autospec=True)
def test_handle_exception_happy(
    mock_exit_handler, mock_logger, exc_type, exc_value, exc_traceback
):
    # Act
    handle_exception(exc_type, exc_value, exc_traceback)

    # Assert
    mock_logger.critical.assert_called_once()
    mock_exit_handler.assert_called_once_with(error=True)


# Edge case
@patch("swiftguard.cli.LOGGER", autospec=True)
@patch("swiftguard.cli.exit_handler", autospec=True)
def test_handle_keyboard_interrupt(mock_exit_handler, mock_logger):
    # Act
    handle_exception(KeyboardInterrupt, KeyboardInterrupt(), None)

    # Assert
    mock_logger.critical.assert_not_called()
    mock_exit_handler.assert_not_called()


# Error case
@pytest.mark.parametrize(
    "exc_type, exc_value, exc_traceback",
    [(None, None, None)],
    ids=["missing_args"],
)
def test_handle_exception_missing_args(exc_type, exc_value, exc_traceback):
    # Act and Assert
    with pytest.raises(TypeError):
        handle_exception(exc_type, exc_value, exc_traceback)


############################################
#              exit_handler()              #
############################################


# Happy path
@pytest.mark.parametrize(
    "signum, frame, error",
    [
        (signal.SIGINT, None, False),  # SIGINT signal
        (signal.SIGTERM, None, False),  # SIGTERM signal
    ],
    ids=["sigint", "sigterm"],
)
@patch("swiftguard.cli.LOGGER.info", autospec=True)
@patch("swiftguard.cli.sys.exit", autospec=True)
def test_exit_handler_happy(
    mock_sys_exit, mock_logger, signum, frame, error, monkeypatch
):
    # Act
    exit_handler(signum, frame, error)

    # Assert
    mock_logger.assert_called_once_with("Exiting the application properly ...")
    mock_sys_exit.assert_called_once_with(0)


# Edge case
@patch("swiftguard.cli.LOGGER.info", autospec=True)
@patch("swiftguard.cli.sys.exit", autospec=True)
def test_exit_handler_no_params(mock_sys_exit, mock_logger, monkeypatch):
    # Act
    exit_handler()

    # Assert
    mock_logger.assert_called_once_with("Exiting the application properly ...")
    mock_sys_exit.assert_called_once_with(0)


# Error case
@pytest.mark.parametrize("error", [True], ids=["error"])
@patch("swiftguard.cli.LOGGER.critical", autospec=True)
@patch("swiftguard.cli.sys.exit", autospec=True)
def test_exit_handler_error(mock_sys_exit, mock_logger, error, monkeypatch):
    # Act
    exit_handler(error=error)

    # Assert
    mock_logger.assert_called_once_with(
        "A critical error occurred that caused the application to exit unexpectedly."
    )
    mock_sys_exit.assert_called_once()


############################################
#                  main()                 #
############################################


# Happy path
def test_main_happy(monkeypatch):
    # Arrange
    with patch("swiftguard.cli.startup"), patch(
        "swiftguard.cli.set_level_dest"
    ), patch("builtins.print"), patch("swiftguard.cli.Worker") as mock_worker:
        mock_worker_instance = mock_worker.return_value
        mock_worker_loop = mock_worker_instance.loop

        # Act
        with pytest.raises(SystemExit) as e:
            main()

        # Assert
        assert e.value.code == 0
        mock_worker_loop.assert_called_once()


# Edge case
def test_main_print_suppressed(monkeypatch):
    # Arrange
    with patch("swiftguard.cli.startup") as mock_startup, patch(
        "swiftguard.cli.set_level_dest"
    ), patch("builtins.print"), patch("swiftguard.cli.Worker"):
        mock_startup.return_value = {"Application": {"log": "syslog"}}

        # Act and Assert
        with pytest.raises(SystemExit):
            main()


# Error case
def test_main_error(monkeypatch):
    # Arrange
    with patch("swiftguard.cli.startup") as mock_startup:
        mock_startup.side_effect = Exception("Error!")

        # Act and Assert
        with pytest.raises(Exception, match="Error!"):
            main()
