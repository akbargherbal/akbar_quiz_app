"""
Pytest configuration file for multi_choice_quiz app tests.
This file contains shared fixtures and configuration for all tests.
"""

import os
import sys
import time
import socket
import logging
import subprocess
import signal
import django
from django.core.management import call_command

# Configure Django settings before tests run
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# --- Constants ---
DJANGO_SERVER_PORT = 8000
DJANGO_SERVER_HOST = "localhost"
DJANGO_SERVER_URL = f"http://{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}"


# --- Helper for shared logging ---
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


# --- Helper function to check if port is available ---
def is_port_in_use(port, host="localhost"):
    """Check if a port is in use on the specified host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


# --- Django Server Fixture ---
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def django_server():
    """Start Django development server for testing."""
    logger = setup_test_logging("django_server")

    # Check if port is already in use
    if is_port_in_use(DJANGO_SERVER_PORT):
        logger.warning(
            f"Port {DJANGO_SERVER_PORT} is already in use. Assuming Django server is running."
        )
        yield DJANGO_SERVER_URL
        return

    logger.info(f"Starting Django server at {DJANGO_SERVER_URL}")

    # Get the manage.py path (assuming we're in the tests directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.abspath(
        os.path.join(current_dir, os.pardir, os.pardir, os.pardir)
    )
    manage_py_path = os.path.join(src_dir, "manage.py")

    # First, ensure we have sample data
    logger.info("Adding sample quiz data...")
    try:
        # Call the management command to add sample quizzes
        call_command("add_sample_quizzes")
        logger.info("Sample quizzes added successfully")
    except Exception as e:
        logger.error(f"Failed to add sample quizzes: {str(e)}")

    # Start the Django server
    server_process = subprocess.Popen(
        [
            sys.executable,
            manage_py_path,
            "runserver",
            f"{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=src_dir,
    )

    # Wait for server to start
    max_wait_time = 10  # seconds
    start_time = time.time()
    server_started = False

    while time.time() - start_time < max_wait_time:
        if is_port_in_use(DJANGO_SERVER_PORT):
            server_started = True
            break
        time.sleep(0.5)

    if not server_started:
        stdout, stderr = server_process.communicate(timeout=1)
        logger.error(f"Django server failed to start in {max_wait_time} seconds.")
        logger.error(f"STDOUT: {stdout.decode('utf-8')}")
        logger.error(f"STDERR: {stderr.decode('utf-8')}")
        server_process.terminate()
        pytest.fail("Django server failed to start")

    logger.info(f"Django server started successfully at {DJANGO_SERVER_URL}")

    # Yield the server URL
    yield DJANGO_SERVER_URL

    # Cleanup: Shutdown the server
    logger.info("Stopping Django server")
    os.kill(server_process.pid, signal.SIGTERM)
    server_process.wait(timeout=5)
    logger.info("Django server stopped")


# --- Console Errors Fixture ---
@pytest.fixture(scope="function")
def capture_console_errors(page: Page):
    """Capture JavaScript console errors during test."""
    logger = setup_test_logging("js_console_errors")
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    yield
    if errors:
        logger.error(">>> JavaScript console errors detected during test run:")
        for i, error in enumerate(errors):
            logger.error(f"  Console Error {i+1}: {error}")
        pytest.fail(
            f"{len(errors)} JavaScript console error(s) detected. Check logs.",
            pytrace=False,
        )
