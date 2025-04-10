#!/usr/bin/env python
# Save as src/run_pages_e2e_tests.py

import os
import subprocess
import sys
import time
import socket
import logging
from datetime import datetime


def setup_logger():
    """Set up a logger for the runner script."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "pages")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set up file and console logging
    log_file = os.path.join(logs_dir, f"e2e_runner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logger = logging.getLogger("pages_e2e_runner")
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def is_port_in_use(port, host="localhost"):
    """Check if a port is in use on the specified host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def ensure_server_running(logger):
    """Ensure the Django development server is running."""
    server_port = 8000
    server_host = "localhost"

    # Check if the server is already running
    if is_port_in_use(server_port, server_host):
        logger.info(f"✓ Server already running at http://{server_host}:{server_port}")
        return True

    # If not, start the server
    logger.info(f"Starting Django server at http://{server_host}:{server_port}...")

    # Start the server in a separate process
    server_process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"{server_host}:{server_port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to start
    max_wait_time = 10  # seconds
    start_time = time.time()
    server_started = False

    while time.time() - start_time < max_wait_time:
        if is_port_in_use(server_port, server_host):
            server_started = True
            break
        time.sleep(0.5)

    if not server_started:
        stdout, stderr = server_process.communicate(timeout=1)
        logger.error(f"ERROR: Django server failed to start in {max_wait_time} seconds.")
        logger.error(f"STDOUT: {stdout.decode('utf-8')}")
        logger.error(f"STDERR: {stderr.decode('utf-8')}")
        server_process.terminate()
        return False

    logger.info(f"✓ Django server started successfully")
    return True


def ensure_sample_data(logger):
    """Ensure sample quiz data is loaded for pages app testing."""
    logger.info("Checking/adding sample quiz data...")
    try:
        # Call the management command to add sample quizzes
        # This is safe to run multiple times as it checks if data exists first
        subprocess.run([sys.executable, "manage.py", "add_sample_quizzes"], check=True)
        logger.info("✓ Sample data check completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR: Failed to add sample quizzes: {e}")
        return False


def setup_test_environment(logger):
    """Setup the test environment by ensuring directory structure."""
    # Ensure pages app tests directory exists
    pages_tests_dir = os.path.join("pages", "tests")
    os.makedirs(pages_tests_dir, exist_ok=True)
    
    # Ensure pages app logs directory exists
    pages_logs_dir = os.path.join("logs", "pages")
    os.makedirs(pages_logs_dir, exist_ok=True)
    
    # Create an __init__.py file in the tests directory if it doesn't exist
    init_file = os.path.join(pages_tests_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("# Pages app tests package\n")
        logger.info(f"Created {init_file}")
    
    logger.info("✓ Test environment setup complete")
    return True


def main():
    """Run the Playwright E2E tests for pages templates."""
    # Set up logger
    logger = setup_logger()
    
    logger.info("=" * 70)
    logger.info("PAGES APP E2E TEST RUNNER")
    logger.info("=" * 70)
    
    # Ensure we're in the src directory
    if not os.path.exists("manage.py"):
        logger.error("ERROR: This script must be run from the src directory")
        return 1

    # Set up test environment
    if not setup_test_environment(logger):
        return 1

    # First ensure sample data is available
    if not ensure_sample_data(logger):
        return 1

    # Make sure the server is running
    if not ensure_server_running(logger):
        return 1

    # Set environment variables
    os.environ["RUN_E2E_TESTS"] = "1"
    os.environ["SERVER_URL"] = "http://localhost:8000"
    logger.info("Environment variables set for E2E tests")

    # Verify the test file exists
    test_file = "pages/tests/test_templates.py"
    if not os.path.exists(test_file):
        logger.error(f"ERROR: Test file '{test_file}' not found.")
        logger.error("Make sure to create the test file before running this script.")
        return 1

    # Run the tests
    logger.info(f"Running Playwright tests for pages app...")
    logger.info("-" * 70)
    
    # Execute pytest targeting only the pages test file
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v"],
            check=False,  # Don't raise exception if tests fail
        )
        
        if result.returncode == 0:
            logger.info("=" * 70)
            logger.info("✓ Pages app E2E tests completed successfully!")
            return 0
        else:
            logger.error("=" * 70)
            logger.error("✗ Pages app E2E tests failed.")
            logger.error(f"Check logs in logs/pages/ directory for details.")
            return result.returncode
    
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
