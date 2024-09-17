"""Logging configuration."""

from logging import Logger

from core_helpers.logs import setup_logger

from .consts import DEBUG, LOG_FILE, PACKAGE

# Automatically sets up and returns the cached logger instance
logger: Logger = setup_logger(PACKAGE, LOG_FILE, DEBUG)
