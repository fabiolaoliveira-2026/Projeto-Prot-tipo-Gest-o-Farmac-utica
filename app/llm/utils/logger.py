"""Logging helpers to unify console and optional file outputs across the project.

This module provides a thin wrapper around Python's logging to standardize how messages are emitted
by CLI tools and library code.
"""

import sys
import logging

# Set the logging level to INFO
logging.basicConfig(
    level=logging.INFO,
)


class Logger:
    """A Logger class to manage logging functionality.

    This class encapsulates a logger instance to provide a convenient way
    to log messages at various levels (info, debug, warning, error). By default,
    logs are sent to stdout (console). Optionally, a name and/or a file handler
    can be added to the logger for customization.

    Args:
        name (str | None): Optional name for the logger. If not provided, the module's name will be used.
        filepath (str | None): Optional file path for the log file. If provided, a file handler will be added to the logger.
    """

    def __init__(self, name: str | None = None, filepath: str | None = None) -> None:
        self.logger = logging.getLogger(name or __name__)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Add a StreamHandler to direct logs to stdout
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(self.stream_handler)

        if filepath:
            self.file_handler = logging.FileHandler(filepath)
            self.logger.addHandler(self.file_handler)

    def info(self, message: str) -> None:
        """Log an informational message.

        Args:
            message (str): The message to log.
        """
        self.logger.info(message)

    def debug(self, message: str) -> None:
        """Log a debug message.

        Args:
            message (str): The message to log.
        """
        self.logger.debug(message)

    def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message (str): The message to log.
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message (str): The message to log.
        """
        self.logger.error(message)
