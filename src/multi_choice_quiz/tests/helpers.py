"""Helper functions and utilities for testing."""

import os
import sys
import time
import logging


def setup_test_logging(test_name):
    """Set up logging for tests with timestamp-based filenames."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file_path = os.path.join(current_dir, f"{test_name}_{timestamp}.log")

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_formatter = logging.Formatter(log_format)

    logger = logging.getLogger(test_name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, mode="w")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logging setup complete. File handler directed to: {log_file_path}")
    return logger
