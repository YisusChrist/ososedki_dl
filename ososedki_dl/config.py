"""Configuration module for the project."""

import tkinter as tk
from argparse import Namespace
from configparser import ConfigParser
from pathlib import Path
from tkinter import filedialog

from rich import print

from .cli import exit_session
from .consts import CONFIG_FILE, DEFAULT_DEST_PATH, EXIT_FAILURE
from .logs import logger


def get_path_from_dialog(title: str) -> Path:
    """
    Get the path from the file dialog.

    Args:
        title (str): The title of the file dialog.

    Returns:
        Path: The path selected by the user.
    """
    logger.debug("Getting path from file dialog")

    root = tk.Tk()
    root.withdraw()  # Hide the main window

    path = Path(filedialog.askdirectory(initialdir=".", title=title)).resolve()
    logger.info("Path selected: %s", path)

    return path


def input_valid_path(prompt: str, default_path: Path) -> Path:
    """
    Prompt the user for a valid path.

    Args:
        prompt (str): The prompt message.
        default_path (Path): The default path.

    Returns:
        Path: The user-provided or default path.
    """
    while True:
        print(f"[green]{prompt}[/] [grey53](default: {default_path})[/]: ", end="")
        user_input = input().strip() or str(default_path)
        path = Path(user_input).resolve()

        if path.exists() and path.is_dir():
            return path

        print("Invalid path. Please enter a valid directory.")


def create_config_file(interactive: bool = False) -> None:
    """
    Create the configuration file.
    """
    logger.debug("Creating configuration file at '%s'", CONFIG_FILE)

    config = ConfigParser()
    config.add_section("Paths")

    dest_path: Path = (
        get_path_from_dialog(title="Select Destination Path")
        if interactive
        else input_valid_path("Enter the destination path", DEFAULT_DEST_PATH)
    )

    logger.info("Destination path: %s", dest_path)

    config.set("Paths", "dest_path", str(dest_path))

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)

    if dest_path == DEFAULT_DEST_PATH:
        msg: str = (
            f"Configuration file created at '{CONFIG_FILE}' with default"
            "paths. Please edit the configuration file to change the paths."
        )
        print(f"[yellow]{msg}[/]")
        logger.warning(msg)
    else:
        logger.info(
            "Configuration file created at '%s' with user-defined paths.", CONFIG_FILE
        )


def configure_paths(args: Namespace) -> Path:
    """
    Get the source and destination path values from the configuration file or
    the command-line arguments.

    Args:
        args (Namespace): The parsed command-line arguments.

    Returns:
        Path: The source and destination path values.
    """
    logger.debug("Configuring paths")

    if not CONFIG_FILE.is_file():
        # Configuration file doesn't exist, prompt the user for values and create the file
        # Warn the user that the configuration file doesn't exist
        print(
            "[yellow]Configuration file doesn't exist. "
            f"Creating configuration file at {CONFIG_FILE}[/]"
        )
        create_config_file(interactive=args.interactive)

    config_file: Path = CONFIG_FILE
    if args.config_file:
        config_file = Path(args.config_file).resolve()

    if not config_file.is_file():
        logger.error("Configuration file '%s' does not exist", config_file)
        exit_session(EXIT_FAILURE)

    # Read both configuration file and command-line arguments
    config = ConfigParser()
    config.read(config_file)

    dest_path: Path = Path(
        args.dest_path or config.get("Paths", "dest_path", fallback=DEFAULT_DEST_PATH)
    ).resolve()

    return dest_path
