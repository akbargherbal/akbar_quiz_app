# src/conftest.py (Revised - django_server removed, admin_logged_in_page added, login verification updated)

import os
import django
import pytest
from playwright.sync_api import Page, expect, Error as PlaywrightError
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

# --- Import UserCollection for the fixture ---
from pages.models import UserCollection


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
User = get_user_model()

# --- Constants for the admin login fixture ---
ADMIN_FIXTURE_USER = "admin_fixture_user"
ADMIN_FIXTURE_PASS = "password123_fixture"


# src/conftest.py

# ... (other code) ...


@pytest.fixture(scope="function")
def admin_logged_in_page(page: Page, live_server):
    """
    Pytest fixture that:
    1. Ensures a specific admin user exists in the test database.
    2. Ensures a default collection exists for that user.
    3. Logs that user in via the Django frontend login page using Playwright.
    4. Yields the logged-in Playwright Page object and the username.
    """
    admin_user_username = ADMIN_FIXTURE_USER
    admin_pass = ADMIN_FIXTURE_PASS

    try:
        user, created = User.objects.update_or_create(
            username=admin_user_username,
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "email": f"{admin_user_username}@example.com",
            },
        )
        user.set_password(admin_pass)
        user.save()
        print(
            f"\n[Fixture] Ensured admin user '{admin_user_username}' exists ({'created' if created else 'updated'})."
        )

        UserCollection.objects.get_or_create(
            user=user,
            name="Admin Fixture Collection",  # Default collection name
            defaults={"description": "A default collection for admin_fixture_user."},
        )
        print(
            f"[Fixture] Ensured 'Admin Fixture Collection' exists for user '{admin_user_username}'."
        )
    except Exception as e:
        pytest.fail(
            f"[Fixture] Failed to ensure test user '{admin_user_username}' or collection: {e}"
        )

    frontend_login_url = f"{live_server.url}{reverse('login')}"
    print(f"[Fixture] Navigating page to frontend login: {frontend_login_url}")
    page.goto(frontend_login_url)

    print("[Fixture] On frontend login page. Filling credentials...")
    page.locator("#username").fill(admin_user_username)
    page.locator("#password").fill(admin_pass)

    print("[Fixture] Submitting frontend login form...")
    page.get_by_role("button", name="Login").click()

    try:
        desktop_nav_container = page.locator("nav[data-testid='desktop-nav']")
        profile_link_anchor = desktop_nav_container.get_by_test_id("profile-link")

        expect(profile_link_anchor).to_be_visible(timeout=10000)
        print("[Fixture] Profile link anchor is visible.")

        # --- MODIFIED AVATAR SPAN LOCATOR ---
        avatar_span = profile_link_anchor.locator("span").nth(0)
        expect(avatar_span).to_be_visible(timeout=5000)
        expect(avatar_span).to_have_text(admin_user_username[0].upper(), timeout=1000)
        # --- END MODIFIED AVATAR SPAN LOCATOR ---
        print(
            f"[Fixture] Avatar span with initial '{admin_user_username[0].upper()}' is visible."
        )

        profile_link_anchor.hover()
        page.wait_for_timeout(250)

        tooltip_actual_span = profile_link_anchor.locator("span").nth(1)
        expect(tooltip_actual_span).to_be_visible(timeout=5000)
        expect(tooltip_actual_span).to_have_text(admin_user_username, timeout=5000)
        print(
            f"[Fixture] Tooltip with username '{admin_user_username}' is visible on hover."
        )

        print(
            f"[Fixture] Successfully logged in as {admin_user_username} via frontend login. Desktop profile avatar and tooltip verified."
        )
    except Exception as e:
        try:
            screenshot_dir_base = settings.SCREENSHOTS_DIR / "fixture_failures"
            screenshot_dir_base.mkdir(parents=True, exist_ok=True)
            fail_screenshot_path = (
                screenshot_dir_base
                / f"fixture_frontend_login_fail_{admin_user_username}.png"
            )
            page.screenshot(path=fail_screenshot_path, full_page=True)
            print(f"[Fixture] Screenshot saved to {fail_screenshot_path}")
        except Exception as screen_err:
            print(f"[Fixture] Error taking screenshot: {screen_err}")
        pytest.fail(
            f"[Fixture] Frontend login verification failed after submit. Current URL: {page.url}. Error: {e}"
        )

    yield page, admin_user_username

    print(f"[Fixture] Teardown for admin_logged_in_page (user: {admin_user_username})")


# --- Console Errors Fixture (REVISED - Only fail on Page Errors) ---
@pytest.fixture(scope="function", autouse=True)
def capture_console_errors(page: Page, request):
    if "page" not in request.fixturenames:
        yield
        return

    logger = None
    if setup_test_logging:
        logger = setup_test_logging("js_console_errors", "e2e")
    else:
        import logging  # Fallback

        # Basic fallback logger setup
        logger = logging.getLogger("js_console_errors_fallback")
        if not logger.handlers:  # Avoid adding handlers multiple times
            logger.setLevel(logging.INFO)
            ch = logging.StreamHandler()
            ch.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(ch)
        print(
            "WARN: Using fallback logger for capture_console_errors due to import failure."
        )

    console_issues = []
    page_errors = []

    def handle_console(msg):
        log_text = f"BROWSER CONSOLE [{msg.type}]: {msg.text}"
        if logger:
            logger.info(log_text)
        if TAILWIND_WARNING_TEXT in msg.text:
            if logger:
                logger.debug(f"Ignoring known console message: {msg.text}")
            return
        if msg.type in ["error", "warning"]:
            console_issues.append(log_text)

    def handle_page_error(exc):
        log_text = f"BROWSER PAGE ERROR: {exc}"
        if logger:
            logger.error(log_text)
        page_errors.append(log_text)

    page.on("console", handle_console)
    page.on("pageerror", handle_page_error)

    yield

    page.remove_listener("console", handle_console)
    page.remove_listener("pageerror", handle_page_error)

    test_failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    all_reported_issues = console_issues + page_errors

    if all_reported_issues and logger:
        issue_summary = f"{len(console_issues)} console error/warning(s), {len(page_errors)} page error(s)"
        log_level_method = logger.error if page_errors else logger.warning
        log_level_method(
            f">>> JavaScript issues detected during test '{request.node.name}': {issue_summary}"
        )
        for i, issue in enumerate(all_reported_issues):
            log_level_method(f"  Issue {i+1}: {issue}")

        if not test_failed and page_errors:
            pytest.fail(
                f"{len(page_errors)} page error(s) detected during test '{request.node.name}'. Check logs.",
                pytrace=False,
            )
        elif not test_failed and console_issues:  # Only console issues, test passed
            logger.warning(
                f"Test '{request.node.name}' passed but had console issues (logged above). Not failing test."
            )


# --- Pytest hook to capture test outcome ---
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        setattr(item, "rep_call", rep)
