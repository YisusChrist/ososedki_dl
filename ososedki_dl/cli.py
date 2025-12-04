"""Command-line interface for the program."""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import TYPE_CHECKING

from core_helpers.logs import logger
from core_helpers.cli import setup_parser
from rich import print

from .config import print_entire_config, print_specific_config_field, update_config_file
from .consts import CONFIG_FILE, PACKAGE
from .consts import __desc__ as DESC
from .consts import __version__ as VERSION

if TYPE_CHECKING:
    from argparse import Namespace


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
        type=Path,
        help="Specify the destination path for moving profiles.",
    )
    # Config file argument
    g_main.add_argument(
        "-f",
        "--config-file",
        dest="config_file",
        type=Path,
        help="Specify a configuration file to use instead of the default one.",
    )
    # Create config file interactive
    g_main.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        default=False,
        help="Enable interactive mode during the creation of the config file.",
    )
    # Enable cached requests
    g_main.add_argument(
        "-c",
        "--cache",
        action="store_true",
        default=False,
        help="Enable caching support for the requests.",
    )
    g_main.add_argument(
        "-cch",
        "--check-cache",
        action="store_true",
        default=False,
        help="Check for cached downloads before downloading.",
    )

    g_user = parser.add_argument_group("User Options")
    g_user.add_argument(
        "-cd",
        "--config-dir",
        action="store_true",
        default=False,
        help="Show config directory path and exit.",
    )
    g_user.add_argument(
        "-ld",
        "--log-dir",
        action="store_true",
        default=False,
        help="Shows log directory path and exit.",
    )
    g_user.add_argument(
        "-pc",
        "--print-config",
        nargs="*",
        metavar=("field", "value"),
        help=f"""\
1. Print all config fields and values:
[green]{PACKAGE} print-config[/]

2. Print one config field's value:
[green]{PACKAGE} print-config [cyan]<field>[/][/]

Example usage:
[green]{PACKAGE} print-config destination[/]

3. Change value of one or multiple config fields.
[green]{PACKAGE} print-config [cyan]<field> <value>[/] [[cyan]<field> <value>[/] ...][/]""",
    )
    g_user.add_argument(
        "-l",
        "--list-supported-sites",
        action="store_true",
        default=False,
        help="List all the supported sites and exit.",
    )

    return parser.parse_args()


def handle_config_command(args: Namespace) -> None:
    """
    Handle the 'print-config' command.

    Args:
        args (Namespace): The parsed arguments.
    """
    logger.debug("Handling config command")

    # Read both configuration file and command-line arguments
    config = configparser.ConfigParser()
    try:
        logger.info(f"Reading config file: {CONFIG_FILE}")
        config.read(CONFIG_FILE)

        if not args.print_config:
            logger.debug("Printing entire config")
            print_entire_config(config)
        elif len(args.print_config) == 1:
            logger.debug(f"Printing specific config field: {args.print_config[0]}")
            print_specific_config_field(config, args.print_config[0])
        else:
            logger.debug("Updating config fields")
            update_config_file(config, args.print_config)
            # Save updated config
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                config.write(f)
            logger.info("Config file updated successfully.")
            print("[green]Config file updated successfully.[/]")

    except configparser.Error as e:
        logger.exception("Error parsing config file")
        print(f"Error parsing config file: {e}")
    except IOError as e:
        logger.exception("Error accessing config file")
        print(f"Error accessing config file: {e}")
