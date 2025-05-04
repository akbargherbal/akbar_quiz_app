# src/conftest.py

import os
import sys
import time
import socket
import subprocess
import signal
import django
from django.core.management import call_command
import pytest
from playwright.sync_api import Page, expect, Error as PlaywrightError

# --- Import the standardized logging setup ---
try:
    from multi_choice_quiz.tests.test_logging import setup_test_logging
except ImportError:
    print("Error: Could not import setup_test_logging. Check path.")
    sys.exit(1)

# Configure Django settings before tests run
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# --- Constants ---
DJANGO_SERVER_PORT = 8000
DJANGO_SERVER_HOST = "localhost"
DJANGO_SERVER_URL = f"http://{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}"

# --- Text of the warning message to ignore ---
TAILWIND_WARNING_TEXT = (
    # --- MODIFIED: Use a more specific part of the message ---
    "cdn.tailwindcss.com should not be used in production."
)


# --- Helper function to check if port is available ---
def is_port_in_use(port, host="localhost"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


# --- Django Server Fixture ---
@pytest.fixture(scope="session")
def django_server():
    logger = setup_test_logging("django_server_fixture", "e2e")
    logger.info("Setting up Django server for testing session...")

    if is_port_in_use(DJANGO_SERVER_PORT):
        logger.warning(
            f"Port {DJANGO_SERVER_PORT} is already in use. Assuming Django server is running."
        )
        yield DJANGO_SERVER_URL
        return

    logger.info(f"Starting Django server at {DJANGO_SERVER_URL}")
    manage_py_path = os.path.join(os.getcwd(), "manage.py")
    if not os.path.exists(manage_py_path):
        # Try relative path from conftest.py
        manage_py_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "manage.py")
        )
        if not os.path.exists(manage_py_path):
            logger.error(
                f"Could not find manage.py relative to {__file__} or in {os.getcwd()}"
            )
            pytest.fail("manage.py not found")

    # --- Note: Removing sample data addition from here, potentially conflicting with django_db ---
    # logger.info("Adding sample quiz data...")
    # try:
    #     # Ensure the project root is correctly identified for management commands
    #     project_root = os.path.dirname(manage_py_path)
    #     call_command("add_sample_quizzes", verbosity=0)
    #     logger.info("Sample quizzes data check/add completed.")
    # except Exception as e:
    #     logger.error(f"Failed to add sample quizzes: {str(e)}")
    #     # Optionally fail the test if sample data is crucial
    #     # pytest.fail(f"Failed to add sample quizzes: {str(e)}")

    server_process = subprocess.Popen(
        [
            sys.executable,
            manage_py_path,
            "runserver",
            "--noreload",
            f"{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # --- MODIFIED: Determine project_root more reliably ---
        cwd=os.path.dirname(manage_py_path),  # Run from directory containing manage.py
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    max_wait_time = 15
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

    yield DJANGO_SERVER_URL

    logger.info(f"Stopping Django server (PID: {server_process.pid})")
    if sys.platform == "win32":
        try:
            # --- MODIFIED: Use SIGTERM on Windows too for simplicity, Popen handles it ---
            server_process.terminate()
            # os.kill(server_process.pid, signal.CTRL_BREAK_EVENT) # Keep as fallback?
        except OSError as e:
            logger.warning(
                f"Could not send terminate signal (server might already be stopped): {e}"
            )
    else:
        server_process.terminate()

    try:
        server_process.wait(timeout=5)
        logger.info("Django server stopped gracefully.")
    except subprocess.TimeoutExpired:
        logger.warning("Django server did not terminate gracefully, killing.")
        server_process.kill()
        server_process.wait()
        logger.info("Django server killed.")


# --- Console Errors Fixture (REVISED with Filtering) ---
@pytest.fixture(scope="function", autouse=True)
def capture_console_errors(page: Page, request):
    """Capture JavaScript console/page errors, ignoring specific warnings."""
    logger = setup_test_logging("js_console_errors", "e2e")
    errors = []
    page_errors = []

    def handle_console(msg):
        log_text = f"BROWSER CONSOLE [{msg.type}]: {msg.text}"
        # Log ALL console messages first for debugging visibility
        # (adjust level if too verbose, e.g., logger.debug)
        logger.info(log_text)

        # <<< START FILTERING >>>
        # Ignore the specific Tailwind CSS production warning by checking if the
        # constant text is part of the message text.
        if TAILWIND_WARNING_TEXT in msg.text:
            logger.debug(f"Ignoring known console message: {msg.text}")
            return  # Don't treat this specific warning as an error
        # <<< END FILTERING >>>

        # Only add actual errors or warnings (that were not filtered out)
        if msg.type in ["error", "warning"]:
            errors.append(log_text)

    def handle_page_error(exc):
        log_text = f"BROWSER PAGE ERROR: {exc}"
        logger.error(log_text)
        page_errors.append(log_text)

    page.on("console", handle_console)
    page.on("pageerror", handle_page_error)

    yield  # Run the test function

    page.remove_listener("console", handle_console)
    page.remove_listener("pageerror", handle_page_error)

    test_failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed

    # Combine only the *captured* errors (excluding the filtered Tailwind warning)
    all_js_issues = errors + page_errors
    if all_js_issues:
        issue_summary = (
            f"{len(errors)} console error/warning(s), {len(page_errors)} page error(s)"
        )
        # Log the summary differently if the test itself passed vs failed
        log_level = logger.warning if test_failed else logger.error
        log_level(
            f">>> JavaScript issues detected during test '{request.node.name}': {issue_summary}"
        )
        for i, issue in enumerate(all_js_issues):
            # Log the actual issues that caused the failure/warning
            log_level(f"  Issue {i+1}: {issue}")

        # Fail the test only if it hadn't already failed for other reasons
        # and if there were actual issues captured after filtering.
        if not test_failed:
            pytest.fail(
                f"{issue_summary} detected during test '{request.node.name}'. Check 'js_console_errors.log'.",
                pytrace=False,
            )


# --- Pytest hook to capture test outcome ---
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        setattr(item, "rep_call", rep)
