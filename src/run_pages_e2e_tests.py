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
    log_file = os.path.join(
        logs_dir, f"e2e_runner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    logger = logging.getLogger("pages_e2e_runner")
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(
        log_file, encoding="utf-8"
    )  # Specify UTF-8 encoding
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(message)s")
    # Attempt to set console encoding, though this might not always work reliably across platforms/terminals
    try:
        console_handler.setStream(
            open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
        )
    except Exception:  # Fallback if setting encoding fails
        pass
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def is_port_in_use(port, host="localhost"):
    """Check if a port is in use on the specified host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            return s.connect_ex((host, port)) == 0
        except socket.gaierror:  # Handle case where host cannot be resolved
            return False


def ensure_server_running(logger):
    """Ensure the Django development server is running."""
    server_port = 8000
    server_host = "localhost"

    # Check if the server is already running
    if is_port_in_use(server_port, server_host):
        logger.info(f"OK: Server already running at http://{server_host}:{server_port}")
        return True

    # If not, start the server
    logger.info(f"Starting Django server at http://{server_host}:{server_port}...")

    # Start the server in a separate process
    try:
        server_process = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", f"{server_host}:{server_port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Prevent creation of new console window on Windows
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except FileNotFoundError:
        logger.error(
            "ERROR: 'manage.py' not found. Make sure you are in the 'src' directory."
        )
        return False
    except Exception as e:
        logger.error(f"ERROR: Failed to start server process: {e}")
        return False

    # Wait for the server to start
    max_wait_time = 15  # Increased wait time
    start_time = time.time()
    server_started = False

    while time.time() - start_time < max_wait_time:
        if is_port_in_use(server_port, server_host):
            server_started = True
            break
        time.sleep(0.5)

    if not server_started:
        # Attempt to read output if server failed
        try:
            stdout, stderr = server_process.communicate(timeout=1)
            logger.error(
                f"ERROR: Django server failed to start in {max_wait_time} seconds."
            )
            logger.error(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
            logger.error(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
        except subprocess.TimeoutExpired:
            logger.error(f"ERROR: Django server process communication timed out.")
        except Exception as comm_err:
            logger.error(f"ERROR: Error getting server process output: {comm_err}")

        # Terminate the process if it's still running
        if server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server process did not terminate gracefully.")
                server_process.kill()

        return False

    logger.info(f"OK: Django server started successfully (PID: {server_process.pid})")
    # Store the process globally or return it if you need to manage it later (e.g., shutdown)
    # For now, we assume it runs until the script exits or is interrupted.
    return True


def ensure_sample_data(logger):
    """Ensure sample quiz data is loaded for pages app testing."""
    logger.info("Checking/adding sample quiz data...")
    try:
        # Call the management command to add sample quizzes
        # This is safe to run multiple times as it checks if data exists first
        result = subprocess.run(
            [sys.executable, "manage.py", "add_sample_quizzes"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        logger.info("OK: Sample data check completed")
        # Log output from the command if needed
        # logger.debug(f"add_sample_quizzes STDOUT:\n{result.stdout}")
        return True
    except FileNotFoundError:
        logger.error("ERROR: 'manage.py' not found. Cannot add sample data.")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"ERROR: Failed to add sample quizzes: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(
            f"ERROR: An unexpected error occurred during sample data check: {e}"
        )
        return False


def setup_test_environment(logger):
    """Setup the test environment by ensuring directory structure."""
    try:
        # Ensure pages app tests directory exists
        pages_tests_dir = os.path.join("pages", "tests")
        os.makedirs(pages_tests_dir, exist_ok=True)

        # Ensure pages app logs directory exists
        pages_logs_dir = os.path.join("logs", "pages")
        os.makedirs(pages_logs_dir, exist_ok=True)

        # Create an __init__.py file in the tests directory if it doesn't exist
        init_file = os.path.join(pages_tests_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write("# Pages app tests package\n")
            logger.info(f"Created {init_file}")

        logger.info("OK: Test environment setup complete")
        return True
    except OSError as e:
        logger.error(f"ERROR: Could not set up test environment directories: {e}")
        return False


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
    # Ensure Django settings module is explicitly set for pytest-django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    logger.info("Environment variables set for E2E tests")

    # Verify the test file exists
    test_file = "pages/tests/test_templates.py"
    if not os.path.exists(test_file):
        logger.error(f"ERROR: Test file '{test_file}' not found.")
        logger.error("Make sure the test file exists before running this script.")
        return 1

    # Run the tests
    logger.info(f"Running Playwright tests for pages app: {test_file}")
    logger.info("-" * 70)

    # Execute pytest targeting only the pages test file
    # Using subprocess.run ensures we capture return code
    return_code = 1  # Default to failure
    try:
        # Use 'pytest' command directly if it's in PATH, otherwise use 'python -m pytest'
        # Add '-s' to disable output capture by pytest itself, letting our logger handle it
        # Add '--capture=no' as another way to attempt disabling capture
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--capture=no"],
            check=False,  # Don't raise exception if tests fail
            # text=True, # Ensures stdout/stderr are strings
            # encoding='utf-8', # Specify encoding
        )
        return_code = result.returncode

        if return_code == 0:
            logger.info("=" * 70)
            logger.info("OK: Pages app E2E tests completed successfully!")
        else:
            logger.error("=" * 70)
            logger.error(
                f"FAIL: Pages app E2E tests failed (pytest exit code: {return_code})."
            )
            logger.error(f"Check logs in logs/pages/ directory for details.")

    except FileNotFoundError:
        logger.error(
            "ERROR: 'pytest' command not found. Make sure pytest is installed and in your PATH."
        )
    except Exception as e:
        logger.error(f"ERROR: An unexpected error occurred while running tests: {e}")

    return return_code


if __name__ == "__main__":
    sys.exit(main())
