"""Logging configuration."""

from core_helpers.logs import logger

from .consts import DEBUG, LOG_FILE, PACKAGE

# Automatically sets up and returns the cached logger instance
logger.setup_logger(PACKAGE, LOG_FILE, DEBUG)
