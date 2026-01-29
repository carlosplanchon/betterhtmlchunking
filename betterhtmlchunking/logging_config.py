#!/usr/bin/env python3

import logging
import sys

# Module name for the library
LOGGER_NAME = "betterhtmlchunking"


def get_logger(module_name: str) -> logging.Logger:
    """Get a logger for a specific module within the betterhtmlchunking package.

    Parameters
    ----------
    module_name : str
        The name of the module (e.g., 'tree_regions_system', 'render_system')

    Returns
    -------
    logging.Logger
        Configured logger for the module
    """
    return logging.getLogger(f"{LOGGER_NAME}.{module_name}")


def setup_root_logger(level: int = logging.WARNING) -> logging.Logger:
    """Setup the root logger for the betterhtmlchunking package.

    This should be called once at the application entry point (CLI or library usage).

    Parameters
    ----------
    level : int
        The logging level (default: logging.WARNING)

    Returns
    -------
    logging.Logger
        The configured root logger
    """
    logger = logging.getLogger(LOGGER_NAME)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger


def set_log_level(level: int) -> None:
    """Change the logging level for the entire betterhtmlchunking package.

    Parameters
    ----------
    level : int
        The new logging level (e.g., logging.DEBUG, logging.INFO)
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
