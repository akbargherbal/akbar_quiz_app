# src/conftest.py (Revised - django_server removed, admin_logged_in_page added)

import os
import sys
import time
import subprocess
import re  # <<< Added for URL regex matching in fixture
import django
import pytest
from playwright.sync_api import Page, expect, Error as PlaywrightError
from django.contrib.auth import get_user_model  # <<< Added for fixture
from django.urls import reverse  # <<< Added for fixture

# --- Import the standardized logging setup ---
try:
    from multi_choice_quiz.tests.test_logging import setup_test_logging
except ImportError:
    print(
        "Error: Could not import setup_test_logging from multi_choice_quiz.tests.test_logging. Check path."
    )
    setup_test_logging = None

# Configure Django settings before tests run
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# --- Text of the warning message to ignore ---
TAILWIND_WARNING_TEXT = "cdn.tailwindcss.com should not be used in production."

# --- Get User Model ---
User = get_user_model()  # <<< Added for fixture

# --- Constants for the admin login fixture ---
ADMIN_FIXTURE_USER = "admin_fixture_user"
ADMIN_FIXTURE_PASS = "password123_fixture"


# --- NEW FIXTURE DEFINITION ---
@pytest.fixture(scope="function")  # Run login for each test function using this fixture
def admin_logged_in_page(page: Page, live_server):
    """
    Pytest fixture that:
    1. Ensures a specific admin user exists in the test database.
    2. Logs that user in via the Django admin login page using Playwright.
    3. Yields the logged-in Playwright Page object and the username.
    """
    admin_user = ADMIN_FIXTURE_USER
    admin_pass = ADMIN_FIXTURE_PASS

    # --- 1. Ensure user exists in test DB ---
    try:
        user, created = User.objects.update_or_create(
            username=admin_user,
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "email": f"{admin_user}@example.com",
            },
        )
        user.set_password(admin_pass)
        user.save()
        print(
            f"\n[Fixture] Ensured admin user '{admin_user}' exists ({'created' if created else 'updated'})."
        )
    except Exception as e:
        pytest.fail(f"[Fixture] Failed to ensure test user '{admin_user}': {e}")

    # --- 2. Perform login via Playwright ---
    admin_login_url = f"{live_server.url}{reverse('admin:index')}"
    print(f"[Fixture] Navigating page to admin login: {admin_login_url}")
    page.goto(admin_login_url)

    if "login" in page.url:
        print("[Fixture] On login page. Filling admin credentials...")
        page.locator("#id_username").fill(admin_user)
        page.locator("#id_password").fill(admin_pass)
        print("[Fixture] Submitting admin login form...")
        page.locator('input[type="submit"]').click()
        try:
            expect(
                page.get_by_role("heading", name="Site administration")
            ).to_be_visible(timeout=10000)
            print(f"[Fixture] Successfully logged in as {admin_user} via /admin/")
        except Exception as e:
            try:
                screenshot_dir = os.path.join(
                    os.path.dirname(__file__), "playwright_screenshots"
                )
                os.makedirs(screenshot_dir, exist_ok=True)
                fail_screenshot_path = os.path.join(
                    screenshot_dir, f"fixture_login_fail_{admin_user}.png"
                )
                page.screenshot(path=fail_screenshot_path, full_page=True)
                print(f"[Fixture] Screenshot saved to {fail_screenshot_path}")
            except Exception as screen_err:
                print(f"[Fixture] Error taking screenshot: {screen_err}")
            pytest.fail(f"[Fixture] Login verification failed after submit. Error: {e}")
    else:
        try:
            expect(
                page.get_by_role("heading", name="Site administration")
            ).to_be_visible(timeout=5000)
            print(
                f"[Fixture] Already logged in or admin page loaded directly for {admin_user}."
            )
        except Exception as e:
            try:
                screenshot_dir = os.path.join(
                    os.path.dirname(__file__), "playwright_screenshots"
                )
                os.makedirs(screenshot_dir, exist_ok=True)
                fail_screenshot_path = os.path.join(
                    screenshot_dir, f"fixture_admin_load_fail_{admin_user}.png"
                )
                page.screenshot(path=fail_screenshot_path, full_page=True)
                print(f"[Fixture] Screenshot saved to {fail_screenshot_path}")
            except Exception as screen_err:
                print(f"[Fixture] Error taking screenshot: {screen_err}")
            pytest.fail(
                f"[Fixture] Expected admin dashboard, but failed verification. Error: {e}"
            )

    # --- 3. Yield page and username to the test ---
    yield page, admin_user

    # --- Teardown (Optional) ---
    print(f"[Fixture] Teardown for admin_logged_in_page (user: {admin_user})")


# --- END NEW FIXTURE DEFINITION ---


# --- Console Errors Fixture (REVISED with Filtering) ---
@pytest.fixture(scope="function", autouse=True)
def capture_console_errors(page: Page, request):
    """Capture JavaScript console/page errors, ignoring specific warnings."""
    logger = None
    if setup_test_logging:
        logger = setup_test_logging("js_console_errors", "e2e")
    else:
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
        logger.info(log_text)
        if TAILWIND_WARNING_TEXT in msg.text:
            logger.debug(f"Ignoring known console message: {msg.text}")
            return
        if msg.type in ["error", "warning"]:
            errors.append(log_text)

    def handle_page_error(exc):
        log_text = f"BROWSER PAGE ERROR: {exc}"
        logger.error(log_text)
        page_errors.append(log_text)

    page.on("console", handle_console)
    page.on("pageerror", handle_page_error)

    yield

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
        if not test_failed:
            pytest.fail(
                f"{issue_summary} detected during test '{request.node.name}'. Check logs.",
                pytrace=False,
            )


# --- Pytest hook to capture test outcome ---
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        setattr(item, "rep_call", rep)
