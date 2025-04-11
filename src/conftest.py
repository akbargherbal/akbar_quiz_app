# src/conftest.py (New or updated content)

import os
import sys
import time
import socket
import subprocess
import signal
import django
from django.core.management import call_command
import pytest
from playwright.sync_api import Page, expect

# --- Import the standardized logging setup ---
# Make sure the path is correct relative to src/
try:
    from multi_choice_quiz.tests.test_logging import setup_test_logging
except ImportError:
    # Handle potential import issues if structure changes
    print("Error: Could not import setup_test_logging. Check path.")
    sys.exit(1)


# Configure Django settings before tests run (if not already done globally)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# --- Constants ---
DJANGO_SERVER_PORT = 8000
DJANGO_SERVER_HOST = "localhost"
DJANGO_SERVER_URL = f"http://{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}"


# --- Helper function to check if port is available ---
def is_port_in_use(port, host="localhost"):
    """Check if a port is in use on the specified host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


# --- Django Server Fixture ---
@pytest.fixture(scope="session")
def django_server():
    """Start Django development server for testing."""
    # Log server setup to a general e2e log or specific server log
    logger = setup_test_logging("django_server_fixture", "e2e")  # Log to 'e2e' category
    logger.info("Setting up Django server for testing session...")

    # Check if port is already in use
    if is_port_in_use(DJANGO_SERVER_PORT):
        logger.warning(
            f"Port {DJANGO_SERVER_PORT} is already in use. Assuming Django server is running."
        )
        yield DJANGO_SERVER_URL
        return

    logger.info(f"Starting Django server at {DJANGO_SERVER_URL}")

    # Get the manage.py path (assuming src is the current directory when pytest runs)
    manage_py_path = os.path.join(os.getcwd(), "manage.py")

    # Ensure manage.py exists
    if not os.path.exists(manage_py_path):
        manage_py_path = os.path.join(
            os.path.dirname(__file__), "manage.py"
        )  # Try relative to conftest
        if not os.path.exists(manage_py_path):
            logger.error(
                f"Could not find manage.py at {manage_py_path} or {os.getcwd()}"
            )
            pytest.fail("manage.py not found")

    # First, ensure we have sample data
    logger.info("Adding sample quiz data...")
    try:
        # Ensure cwd is src/ for management commands
        project_root = os.path.dirname(manage_py_path)
        call_command(
            "add_sample_quizzes", verbosity=0
        )  # Use verbosity 0 for less output
        logger.info("Sample quizzes data check/add completed.")
    except Exception as e:
        logger.error(f"Failed to add sample quizzes: {str(e)}")
        # Decide if this is critical; maybe proceed anyway?
        # pytest.fail(f"Failed to add sample quizzes: {e}")

    # Start the Django server
    server_process = subprocess.Popen(
        [
            sys.executable,
            manage_py_path,
            "runserver",
            f"--noreload",  # Important for stability in tests
            f"{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=project_root,  # Run from project root
        # Prevent creation of new console window on Windows
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    # Wait for server to start
    max_wait_time = 15  # seconds
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
        logger.error(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
        logger.error(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
        server_process.terminate()
        pytest.fail("Django server failed to start")

    logger.info(
        f"Django server started successfully (PID: {server_process.pid}) at {DJANGO_SERVER_URL}"
    )

    # Yield the server URL
    yield DJANGO_SERVER_URL

    # Cleanup: Shutdown the server
    logger.info(f"Stopping Django server (PID: {server_process.pid})")
    # Send SIGTERM (more graceful)
    if sys.platform == "win32":
        os.kill(server_process.pid, signal.CTRL_BREAK_EVENT)  # Windows specific signal
    else:
        os.kill(server_process.pid, signal.SIGTERM)

    try:
        server_process.wait(timeout=5)
        logger.info("Django server stopped gracefully.")
    except subprocess.TimeoutExpired:
        logger.warning("Django server did not terminate gracefully, killing.")
        server_process.kill()
        server_process.wait()  # Ensure it's dead
        logger.info("Django server killed.")


# --- Console Errors Fixture ---
@pytest.fixture(scope="function")
def capture_console_errors(page: Page):
    """Capture JavaScript console errors during test."""
    # Log JS errors to a general 'e2e' category
    logger = setup_test_logging("js_console_errors", "e2e")  # CORRECTED: Added app_name
    errors = []
    # Listen for 'pageerror' events which indicate uncaught JS exceptions
    page.on("pageerror", lambda exc: errors.append(f"Page Error: {exc}"))
    # Listen for 'console' events of type 'error'
    page.on(
        "console",
        lambda msg: (
            errors.append(f"Console Error: {msg.text}") if msg.type == "error" else None
        ),
    )

    yield  # Run the test

    # After test runs, check if errors were captured
    if errors:
        logger.error(">>> JavaScript console/page errors detected during test run:")
        for i, error in enumerate(errors):
            logger.error(f"  Error {i+1}: {error}")
        pytest.fail(
            f"{len(errors)} JavaScript console/page error(s) detected. Check logs.",
            pytrace=False,
        )
