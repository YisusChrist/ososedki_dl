import sys
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter
from typing import NoReturn

from rich import print

from .consts import __version__ as VERSION
from .consts import EXIT_FAILURE, LOG_PATH


def get_parsed_args() -> Namespace:
    """
    Parse and return command-line arguments.

    Returns:
        The parsed arguments as an Namespace object.
    """
    parser = ArgumentParser(
        description="[Insert description]",  # Program description
        formatter_class=RawTextHelpFormatter,  # Disable line wrapping
        allow_abbrev=False,  # Disable abbreviations
        add_help=False,  # Disable default help
    )

    g_targets = parser.add_argument_group("Options to add URLs")
    # g_targets.add_argument("...")

    g_misc = parser.add_argument_group("Miscellaneous Options")
    # Help
    g_misc.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit."
    )
    # Verbose
    g_misc.add_argument(
        "-t",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help="Show log messages on screen. Default is False.",
    )
    # Debug
    g_misc.add_argument(
        "-d",
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="Activate debug logs. Default is False.",
    )
    g_misc.add_argument(
        "-v",
        "--version",
        action="version",
        help="Show version number and exit.",
        version=f"%(prog)s version {VERSION}",
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
            "[red]There were errors during the execution of the script. "
            f"Check the logs at {LOG_PATH} for more information.[/]"
        )

    # Exit the program with the given exit value
    sys.exit(exit_value)
