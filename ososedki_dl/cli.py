"""Command-line interface for the program."""

import configparser
from argparse import Namespace

from core_helpers.cli import setup_parser
from rich import print

from ososedki_dl.config import (print_entire_config,
                                print_specific_config_field,
                                update_config_file)

from .consts import CONFIG_FILE, PACKAGE
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
        "-f",
        "--config-file",
        dest="config_file",
        type=str,
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
    # Read both configuration file and command-line arguments
    config = configparser.ConfigParser()
    try:
        config.read(CONFIG_FILE)

        if not args.print_config:
            print_entire_config(config)
        elif len(args.print_config) == 1:
            print_specific_config_field(config, args.print_config[0])
        else:
            update_config_file(config, args.print_config)
            # Save updated config
            with open(CONFIG_FILE, "w") as f:
                config.write(f)

    except configparser.Error as e:
        print(f"Error parsing config file: {e}")
    except IOError as e:
        print(f"Error accessing config file: {e}")
