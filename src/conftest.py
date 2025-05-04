# src/conftest.py (Revised - django_server fixture removed)

import os
import sys
import time

# import socket # <<< REMOVED >>> No longer needed for port check
import subprocess

# import signal # <<< REMOVED >>> No longer needed for server termination
import django

# from django.core.management import call_command # <<< REMOVED >>> Was only used by django_server
import pytest
from playwright.sync_api import Page, expect, Error as PlaywrightError

# --- Import the standardized logging setup ---
# Note: Ensure this path is correct relative to your project structure
# If multi_choice_quiz is directly under src, this should work.
try:
    # Assuming setup_test_logging might still be used by other potential fixtures or tests directly
    from multi_choice_quiz.tests.test_logging import setup_test_logging
except ImportError:
    print(
        "Error: Could not import setup_test_logging from multi_choice_quiz.tests.test_logging. Check path."
    )
    # Consider if this should be a fatal error or just a warning depending on usage
    # sys.exit(1)
    setup_test_logging = None  # Define as None to avoid NameErrors if used later

# Configure Django settings before tests run
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# --- Constants ---
# <<< REMOVED >>> Django server constants removed as the fixture is gone
# DJANGO_SERVER_PORT = 8000
# DJANGO_SERVER_HOST = "localhost"
# DJANGO_SERVER_URL = f"http://{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}"

# --- Text of the warning message to ignore ---
TAILWIND_WARNING_TEXT = (
    # Using a specific part of the message is more robust
    "cdn.tailwindcss.com should not be used in production."
)


# <<< REMOVED >>> Helper function to check if port is available
# def is_port_in_use(port, host="localhost"):
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         return s.connect_ex((host, port)) == 0


# <<< REMOVED >>> Django Server Fixture
# @pytest.fixture(scope="session")
# def django_server():
#     # ... (entire fixture definition removed) ...
#     pass


# --- Console Errors Fixture (REVISED with Filtering) ---
# This fixture remains useful for capturing JS errors during Playwright tests
@pytest.fixture(scope="function", autouse=True)
def capture_console_errors(page: Page, request):
    """Capture JavaScript console/page errors, ignoring specific warnings."""
    # Use the imported logger setup if available
    logger = None
    if setup_test_logging:
        logger = setup_test_logging("js_console_errors", "e2e")
    else:
        # Basic fallback logger if import failed
        import logging

        logger = logging.getLogger("js_console_errors_fallback")
        if not logger.hasHandlers():
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        print(
            "WARN: Using fallback logger for capture_console_errors due to import failure."
        )

    errors = []
    page_errors = []

    def handle_console(msg):
        log_text = f"BROWSER CONSOLE [{msg.type}]: {msg.text}"
        logger.info(log_text)  # Log all messages for visibility

        # <<< FILTERING >>>
        if TAILWIND_WARNING_TEXT in msg.text:
            logger.debug(f"Ignoring known console message: {msg.text}")
            return  # Don't treat this specific warning as an error
        # <<< END FILTERING >>>

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

    all_js_issues = errors + page_errors
    if all_js_issues:
        issue_summary = (
            f"{len(errors)} console error/warning(s), {len(page_errors)} page error(s)"
        )
        log_level = logger.warning if test_failed else logger.error
        log_level(
            f">>> JavaScript issues detected during test '{request.node.name}': {issue_summary}"
        )
        for i, issue in enumerate(all_js_issues):
            log_level(f"  Issue {i+1}: {issue}")

        # Fail the test only if it hadn't already failed for other reasons
        # and if there were actual issues captured after filtering.
        if not test_failed:
            pytest.fail(
                f"{issue_summary} detected during test '{request.node.name}'. Check logs (e.g., console output or js_console_errors.log if configured).",
                pytrace=False,
            )


# --- Pytest hook to capture test outcome ---
# This hook remains useful for the capture_console_errors fixture
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        setattr(item, "rep_call", rep)
