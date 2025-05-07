# src/multi_choice_quiz/tests/test_logging.py

import os
import sys
import logging
from django.conf import settings  # Assumes settings are configured

# Ensure the base logs directory exists
# logs_base_dir = os.path.join(settings.BASE_DIR, "logs")
# os.makedirs(logs_base_dir, exist_ok=True)


def setup_test_logging(logger_name: str, app_name: str):
    """
    Set up standardized logging for test files within a specific app's log directory.

    Args:
        logger_name: Name for the logger (e.g., __name__, test module name, test script name).
        app_name: The name of the Django app these tests belong to (e.g., 'pages', 'multi_choice_quiz').

    Returns:
        Configured logger instance.
    """
    app_log_dir = settings.LOGS_DIR / app_name  # NEW - uses Path object from settings

    # Create the app-specific directory if it doesn't exist
    os.makedirs(app_log_dir, exist_ok=True)

    # Create a logger instance
    logger = logging.getLogger(logger_name)

    # --- Important: Clear existing handlers to prevent duplicate logs ---
    # This is crucial if this function might be called multiple times for the same logger name
    if logger.handlers:
        logger.handlers.clear()

    # Set the logging level
    logger.setLevel(logging.INFO)
    # Prevent logs from propagating to the root logger if it has handlers
    logger.propagate = False

    # Define the log file path within the app-specific directory
    # Uses the logger_name to create a specific file (e.g., test_views.log, playwright_homepage.log)
    log_file = os.path.join(app_log_dir, f"{logger_name}.log")

    # Create File Handler (overwrite mode 'w')
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setLevel(logging.INFO)

    # Create Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Or match logger level

    # Create Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add Handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(
        f"Test logging initialized for '{logger_name}' in app '{app_name}'. Log file: {log_file}"
    )

    return logger
