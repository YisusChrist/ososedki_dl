"""Command-line interface for the program."""

import sys
from argparse import Namespace
from typing import NoReturn

from core_helpers.cli import setup_parser
from rich import print

from .consts import EXIT_FAILURE, LOG_PATH, PACKAGE
from .consts import __desc__ as DESC
from .consts import __version__ as VERSION


def get_parsed_args() -> Namespace:
    """
    Parse and return command-line arguments.

    Returns:
        The parsed arguments as an Namespace object.
    """
    parser, g_main = setup_parser(
        package=PACKAGE,
        description=DESC,
        version=VERSION,
    )

    # Destination path argument
    g_main.add_argument(
        "-dst",
        "--destination",
        dest="dest_path",
        type=str,
        help="Specify the destination path for moving profiles.",
    )
    # Config file argument
    g_main.add_argument(
        "-c",
        "--config",
        dest="config_file",
        type=str,
        help="Specify a configuration file.",
    )
    # Create config file interactive
    g_main.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        default=False,
        help="Enable interactive mode for the program",
    )

    return parser.parse_args()


def exit_session(exit_value: int) -> NoReturn:
    """
    Exit the program with the given exit value.

    Args:
        exit_value (int): The POSIX exit value to exit with.
    """
    # logger.info("End of session")
    # Check if the exit_value is a valid POSIX exit value
    if not 0 <= exit_value <= 255:
        exit_value = EXIT_FAILURE

    if exit_value == EXIT_FAILURE:
        print(
            "\n[red]There were errors during the execution of the script. "
            f"Check the logs at '{LOG_PATH}' for more information.[/]"
        )

    # Exit the program with the given exit value
    sys.exit(exit_value)
