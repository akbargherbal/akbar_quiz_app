"""
Shared utilities for test logging.
"""

import os
import sys
import logging
import time


def setup_test_logging(test_name):
    """
    Set up consistent logging for tests.
    
    Args:
        test_name: Name to use for the logger and log file
        
    Returns:
        logger: Configured logger instance
    """
    # Get the directory containing the test file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add timestamp to log file name to avoid overwriting
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file_path = os.path.join(current_dir, f"{test_name}_{timestamp}.log")
    
    # Set up formatter
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_formatter = logging.Formatter(log_format)
    
    # Get or create the logger
    logger = logging.getLogger(test_name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_file_path, mode="w")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging setup complete. File handler directed to: {log_file_path}")
    return logger
