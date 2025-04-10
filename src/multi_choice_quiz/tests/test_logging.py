# src/multi_choice_quiz/tests/test_logging.py

import os
import sys
import logging
from django.conf import settings


def setup_test_logging(test_name):
    """
    Set up standardized logging for test files.
    Uses the logs/multi_choice_quiz directory and consistent naming.

    Args:
        test_name: Name for the logger (typically the test module name)

    Returns:
        configured logger instance
    """
    # Define the app-specific log directory
    app_log_dir = os.path.join(settings.BASE_DIR, "logs", "multi_choice_quiz")

    # Create the app-specific directory if it doesn't exist
    os.makedirs(app_log_dir, exist_ok=True)

    # Create a logger
    logger = logging.getLogger(test_name)

    # Clear existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers.clear()

    # Set level
    logger.setLevel(logging.INFO)

    # Create file handler within the app-specific directory
    log_file = os.path.join(app_log_dir, f"{test_name}.log")  # Changed path
    file_handler = logging.FileHandler(log_file, mode="w")

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    # Create console handler for terminal output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Test logging initialized for {test_name}. Log file: {log_file}")

    return logger
