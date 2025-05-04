# src/pages/tests/test_responsive.py

import os
import re
import pytest
from playwright.sync_api import (
    Page,
    expect,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from pathlib import Path
import django

# --- Django Setup ---
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    print("Using core.settings for Django setup in test_responsive.py")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# --- Get User Model ---
User = get_user_model()

# --- Configuration Constants ---
PAGES_TO_TEST = [
    (reverse("pages:home"), "home"),
    (reverse("pages:quizzes"), "quizzes"),
    (reverse("pages:about"), "about"),
    (reverse("login"), "login"),
    (reverse("pages:signup"), "signup"),
    (reverse("pages:profile"), "profile"),
]

BREAKPOINTS = {
    "mobile": {"width": 375, "height": 667},
    "sm": {"width": 640, "height": 768},
    "md": {"width": 768, "height": 1024},
    "lg": {"width": 1024, "height": 768},
    "xl": {"width": 1280, "height": 800},
    "2xl": {"width": 1536, "height": 960},
}

SCREENSHOT_DIR = Path(__file__).parent.parent.parent / "screenshots" / "responsive"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


# --- Helper Function ---
def get_screenshot_path(page_id: str, breakpoint_name: str, suffix: str = "") -> Path:
    filename = f"{page_id}_{breakpoint_name}{suffix}.png"
    return SCREENSHOT_DIR / filename


# --- Test Function ---


# Use django_db marker for database access within the test function itself
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("page_path, page_id", PAGES_TO_TEST)
@pytest.mark.parametrize("bp_name, viewport", BREAKPOINTS.items())
def test_responsive_layout(
    page: Page,
    live_server,  # Use live_server fixture
    page_path: str,
    page_id: str,
    bp_name: str,
    viewport: dict,
):
    """
    Tests the responsive layout of various pages across defined breakpoints.
    Uses pytest-django's live_server fixture for correct DB context.
    Handles login requirement for the profile page.
    """
    # Construct URLs using live_server.url
    full_page_url = f"{live_server.url}{page_path}"
    login_url = f"{live_server.url}{reverse('login')}"
    login_redirect_path = (
        settings.LOGIN_REDIRECT_URL
        if settings.LOGIN_REDIRECT_URL.startswith("/")
        else "/" + settings.LOGIN_REDIRECT_URL
    )
    expected_redirect_url = f"{live_server.url}{login_redirect_path}".rstrip("/") + "/"

    test_user = "testuser_resp_profile"
    test_pass = "password123!"
    profile_link_text = f"Profile ({test_user})"
    profile_link_locator = page.locator(f'a:has-text("{profile_link_text}")')
    # --- Add locators for logged-out links ---
    # Scope them to header nav to be more specific
    login_link_locator = page.locator('header nav a:has-text("Login")')
    signup_link_locator = page.locator('header nav a:has-text("Sign Up")')
    # --- End Add locators ---

    print(
        f"\n--- Testing Page: '{page_id}' at Breakpoint: '{bp_name}' ({viewport['width']}x{viewport['height']}) ---"
    )
    print(f"Target URL: {full_page_url}")

    logged_in = False

    # --- Login Handling (Conditional for Profile Page) ---
    if page_id == "profile":
        print("Profile page requires login. Attempting...")

        # 1. Ensure clean slate and create user reliably (using create_user)
        try:
            User.objects.filter(username=test_user).delete()
            print(f"Ensured user '{test_user}' is deleted before creation.")
            user = User.objects.create_user(
                username=test_user,
                password=test_pass,
                email=f"{test_user}@example.com",
                is_active=True,
            )
            print(f"User '{test_user}' created successfully in test DB.")
            refetched_user = User.objects.get(username=test_user)
            assert refetched_user.check_password(test_pass)
            print(
                f"Password check successful immediately after create_user for {test_user}"
            )
        except User.DoesNotExist:
            pytest.fail(
                f"FATAL: User {test_user} not found immediately after create_user."
            )
        except Exception as e:
            pytest.fail(f"Failed to create test user '{test_user}': {e}")

        # 2. Navigate to login page
        try:
            print(f"Navigating to login page: {login_url}")
            page.goto(login_url, wait_until="networkidle")
            expect(page).to_have_url(
                re.compile(login_url.rstrip("/") + r"/?(\?next=.*)?")
            )
            print(f"Successfully on login page: {page.url}")
        except PlaywrightError as e:
            fail_screenshot_path = get_screenshot_path(
                page_id, bp_name, "_login_nav_fail"
            )
            page.screenshot(path=fail_screenshot_path, full_page=True)
            pytest.fail(
                f"Failed to navigate to login page {login_url}: {e}. Screenshot: {fail_screenshot_path}"
            )

        # 3. Fill credentials and submit login form
        try:
            username_input = page.locator("#username")
            password_input = page.locator("#password")
            submit_button = page.locator('button[type="submit"], input[type="submit"]')

            print("Locating login form elements...")
            expect(username_input).to_be_visible(timeout=10000)
            expect(password_input).to_be_visible(timeout=10000)
            expect(submit_button).to_be_enabled(timeout=10000)
            print("Login form elements located.")

            username_input.fill(test_user)
            password_input.fill(test_pass)
            print("Credentials filled.")

            print("Clicking login submit button...")
            submit_button.click()

            print("Waiting for potential redirect after login submit...")
            page.wait_for_load_state("networkidle", timeout=15000)
            current_url_after_login = page.url.rstrip("/") + "/"
            print(f"URL after login attempt: {current_url_after_login}")

            # 4. Check if login was successful (redirected to expected URL)
            if current_url_after_login == expected_redirect_url:
                print(f"Successfully redirected to: {current_url_after_login}")
                logged_in = True

                # 5. Verify login state on the redirected page
                print("Verifying login status on redirected page...")
                header_after_login = page.locator("header").first
                expect(header_after_login).to_be_visible(timeout=5000)
                try:
                    # --- START MODIFICATION: Check logged-out links are hidden ---
                    expect(login_link_locator).to_be_hidden(timeout=5000)
                    expect(signup_link_locator).to_be_hidden(timeout=5000)
                    print(
                        f"Confirmed logged-out links ('Login', 'Sign Up') are hidden on {current_url_after_login}"
                    )
                    # --- END MODIFICATION ---
                except (PlaywrightError, AssertionError) as e:
                    fail_screenshot_path = get_screenshot_path(
                        page_id, bp_name, "_login_verify_fail"
                    )
                    page.screenshot(path=fail_screenshot_path, full_page=True)
                    # Updated failure message
                    pytest.fail(
                        f"Login verification failed: Logged-out links ('Login'/'Sign Up') were not hidden after redirect. Error: {e}. Screenshot: {fail_screenshot_path}"
                    )

                # 6. Navigate to the actual profile page
                print(
                    f"Login successful. Navigating to target profile page: {full_page_url}"
                )
                page.goto(full_page_url, wait_until="networkidle")
                page.wait_for_timeout(500)
                expect(page).to_have_url(re.compile(full_page_url.rstrip("/") + r"/?"))
                print("Successfully navigated to profile page.")

            else:
                # Login failed
                print("Login redirect failed. Checking for error messages...")
                error_container_locator = page.locator(
                    "div[role='alert']:has(strong:has-text('Error:'))"
                )
                error_text = "Login error message container not found or not visible."
                try:
                    if error_container_locator.is_visible(timeout=2000):
                        error_text = error_container_locator.text_content(timeout=1000)
                except PlaywrightTimeoutError:
                    print("Timeout waiting for error message container visibility.")
                except PlaywrightError as e:
                    print(f"Error checking for login error message: {e}")

                fail_screenshot_path = get_screenshot_path(
                    page_id, bp_name, "_login_redirect_fail"
                )
                page.screenshot(path=fail_screenshot_path, full_page=True)
                pytest.fail(
                    f"Login redirect failed. Expected URL '{expected_redirect_url}', but ended up at '{current_url_after_login}'. "
                    f"Error messages found: '{error_text}'. Screenshot: {fail_screenshot_path}"
                )

        except PlaywrightTimeoutError as e:
            current_url_on_timeout = page.url
            fail_screenshot_path = get_screenshot_path(
                page_id, bp_name, "_login_timeout_fail"
            )
            page.screenshot(path=fail_screenshot_path, full_page=True)
            pytest.fail(
                f"Timeout during login process. Current URL: '{current_url_on_timeout}'. Error: {e}. Screenshot: {fail_screenshot_path}"
            )
        except (PlaywrightError, AssertionError) as e:
            current_url_on_error = page.url
            fail_screenshot_path = get_screenshot_path(
                page_id, bp_name, "_login_playwright_fail"
            )
            page.screenshot(path=fail_screenshot_path, full_page=True)
            pytest.fail(
                f"Playwright/Assertion error during login process. Current URL: '{current_url_on_error}'. Error: {e}. Screenshot: {fail_screenshot_path}"
            )
        except Exception as e:
            fail_screenshot_path = get_screenshot_path(
                page_id, bp_name, "_login_unexpected_fail"
            )
            page.screenshot(path=fail_screenshot_path, full_page=True)
            pytest.fail(
                f"Unexpected Python error during login/profile navigation: {e}. Screenshot: {fail_screenshot_path}"
            )

    else:
        # --- Direct Navigation (For pages not requiring login) ---
        try:
            print(f"Navigating directly to: {full_page_url}")
            page.goto(full_page_url, wait_until="networkidle")
            expect(page).to_have_url(
                re.compile(full_page_url.rstrip("/") + r"/?(\?.*)?")
            )
            print(f"Successfully navigated directly to page: {page.url}")
        except PlaywrightError as e:
            fail_screenshot_path = get_screenshot_path(
                page_id, bp_name, "_direct_nav_fail"
            )
            page.screenshot(path=fail_screenshot_path, full_page=True)
            pytest.fail(
                f"Failed to navigate to page {full_page_url}: {e}. Screenshot: {fail_screenshot_path}"
            )

    # ========================================================================
    # --- Core Responsive Checks (Run for ALL pages after navigation/login) ---
    # ========================================================================

    print(
        f"Setting viewport to {bp_name} ({viewport['width']}x{viewport['height']})..."
    )
    page.set_viewport_size(viewport)
    page.wait_for_timeout(300)

    print("Taking screenshot...")
    screenshot_path = get_screenshot_path(page_id, bp_name)
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")
    except PlaywrightError as e:
        print(f"WARN: Failed to take screenshot {screenshot_path}: {e}")

    # --- Locate Core Layout Elements ---
    header = page.locator("header").first
    main_content = page.locator("main").first
    footer = page.locator("footer").first

    # --- Visibility and Basic Content Checks ---
    print("Checking core element visibility and content...")
    try:
        expect(header, f"Header visible on {page_id} at {bp_name}").to_be_visible()
        expect(
            main_content, f"Main content visible on {page_id} at {bp_name}"
        ).to_be_visible()
        expect(footer, f"Footer visible on {page_id} at {bp_name}").to_be_visible()
        expect(main_content, "Main content not empty").not_to_be_empty()
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(page_id, bp_name, "_visibility_fail")
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Core layout visibility/content check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    # --- Width Checks (Approximate) ---
    print("Checking element widths...")
    try:
        header_box = header.bounding_box()
        if header_box:
            print(
                f"Header width: {header_box['width']}px (Viewport: {viewport['width']}px)"
            )
            assert header_box["width"] == pytest.approx(
                viewport["width"], abs=25
            ), f"Header width mismatch. Page: {page_id}, BP: {bp_name}"
        else:
            pytest.fail(
                f"Could not get bounding box for header. Page: {page_id}, BP: {bp_name}"
            )

        footer_box = footer.bounding_box()
        if footer_box:
            print(
                f"Footer width: {footer_box['width']}px (Viewport: {viewport['width']}px)"
            )
            assert (
                footer_box["width"] > viewport["width"] * 0.8
            ), f"Footer width too small. Page: {page_id}, BP: {bp_name}"
        else:
            print(
                f"WARN: Could not get bounding box for footer. Page: {page_id}, BP: {bp_name}"
            )
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_width_check_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Width check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    # --- Navigation Element Visibility Checks ---
    print("Checking navigation visibility...")
    try:
        mobile_toggle_button = header.locator('button:has(svg > path[d*="M4 6h16"])')
        desktop_nav_container = header.locator("nav.hidden.md\\:flex")
        mobile_nav_container = header.locator("nav[x-show='open']")

        # Determine login status by checking if the profile link *exists* (even if hidden)
        # Using count() is safer than is_visible() here for state check
        is_currently_logged_in = profile_link_locator.count() > 0
        print(
            f"Login state for nav check: {'Logged In' if is_currently_logged_in else 'Logged Out'}"
        )
        expected_nav_items = 5

        is_mobile_breakpoint = viewport["width"] < 768
        if is_mobile_breakpoint:
            print("Mobile breakpoint: Checking mobile nav...")
            expect(mobile_toggle_button, "Mobile toggle visible").to_be_visible()
            expect(desktop_nav_container, "Desktop nav hidden").to_be_hidden()
            expect(mobile_nav_container, "Mobile nav initially hidden").to_be_hidden()

            mobile_toggle_button.click()
            page.wait_for_timeout(300)
            expect(
                mobile_nav_container, "Mobile nav visible after toggle"
            ).to_be_visible()

            mobile_nav_items = mobile_nav_container.locator("a, form > button")
            mobile_item_count = mobile_nav_items.count()
            print(f"Found {mobile_item_count} items in mobile nav.")
            assert (
                mobile_item_count == expected_nav_items
            ), f"Mobile nav item count mismatch. Expected {expected_nav_items}, Found {mobile_item_count}. Page: {page_id}, BP: {bp_name}"

            mobile_toggle_button.click()
            page.wait_for_timeout(300)
            expect(
                mobile_nav_container, "Mobile nav hidden after closing"
            ).to_be_hidden()
        else:
            print("Desktop breakpoint: Checking desktop nav...")
            expect(mobile_toggle_button, "Mobile toggle hidden").to_be_hidden()
            expect(desktop_nav_container, "Desktop nav visible").to_be_visible()
            expect(mobile_nav_container, "Mobile nav container hidden").to_be_hidden()

            desktop_nav_items = desktop_nav_container.locator("a, form > button")
            desktop_item_count = desktop_nav_items.count()
            print(f"Found {desktop_item_count} items in desktop nav.")
            assert (
                desktop_item_count == expected_nav_items
            ), f"Desktop nav item count mismatch. Expected {expected_nav_items}, Found {desktop_item_count}. Page: {page_id}, BP: {bp_name}"

    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(page_id, bp_name, "_nav_check_fail")
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Navigation check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    # --- Horizontal Overflow Check ---
    print("Checking for horizontal overflow...")
    try:
        body_scroll_width = page.evaluate("document.body.scrollWidth")
        body_client_width = page.evaluate("document.body.clientWidth")
        doc_scroll_width = page.evaluate("document.documentElement.scrollWidth")
        doc_client_width = page.evaluate("document.documentElement.clientWidth")

        body_overflow = body_scroll_width > (body_client_width + 1)
        doc_overflow = doc_scroll_width > (doc_client_width + 1)

        print(
            f"Body scroll/client: {body_scroll_width}/{body_client_width}, Doc scroll/client: {doc_scroll_width}/{doc_client_width}"
        )
        assert (
            not body_overflow
        ), f"Body overflow detected ({body_scroll_width} > {body_client_width}). Page: {page_id}, BP: {bp_name}. Screenshot: {screenshot_path}"
        assert (
            not doc_overflow
        ), f"Document overflow detected ({doc_scroll_width} > {doc_client_width}). Page: {page_id}, BP: {bp_name}. Screenshot: {screenshot_path}"
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_overflow_check_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Overflow check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    # --- Page-Specific Content Checks (Basic examples) ---
    print("Checking basic page-specific content...")
    try:
        content_timeout = 5000
        if page_id == "home":
            expect(
                page.locator('h1:has-text("Challenge Your Knowledge")')
            ).to_be_visible(timeout=content_timeout)
            expect(page.locator('h2:has-text("Featured Quizzes")')).to_be_visible(
                timeout=content_timeout
            )
        elif page_id == "quizzes":
            expect(page.locator('h1:has-text("Browse Quizzes")')).to_be_visible(
                timeout=content_timeout
            )
            filter_container = page.locator("div:has(> h2:has-text('Filter by Topic'))")
            expect(filter_container).to_be_visible(timeout=content_timeout)
            expect(filter_container.get_by_role("link", name="All")).to_be_visible(
                timeout=content_timeout
            )
        elif page_id == "about":
            expect(page.locator('h1:has-text("About QuizMaster")')).to_be_visible(
                timeout=content_timeout
            )
            expect(page.locator('h2:has-text("Our Mission")')).to_be_visible(
                timeout=content_timeout
            )
        elif page_id == "login":
            expect(
                page.locator(
                    '//h1[contains(text(),"Login")] | //h2[contains(text(),"Log in")]'
                ).first
            ).to_be_visible(timeout=content_timeout)
            expect(page.locator("#username")).to_be_visible(timeout=content_timeout)
            expect(page.locator("#password")).to_be_visible(timeout=content_timeout)
            expect(
                page.locator('button[type="submit"], input[type="submit"]')
            ).to_be_visible(timeout=content_timeout)
        elif page_id == "signup":
            expect(page.locator('h1:has-text("Create Your Account")')).to_be_visible(
                timeout=content_timeout
            )
            expect(page.locator("#id_username")).to_be_visible(timeout=content_timeout)
            expect(page.locator("#id_email")).to_be_visible(timeout=content_timeout)
            expect(page.locator("#id_password1")).to_be_visible(timeout=content_timeout)
            expect(page.locator("#id_password2")).to_be_visible(timeout=content_timeout)
            expect(
                page.locator('button[type="submit"]:has-text("Create Account")')
            ).to_be_visible(timeout=content_timeout)
        elif page_id == "profile":
            # This check runs *after* successful navigation was confirmed earlier
            expect(page.locator(f'h1:has-text("{test_user}")').first).to_be_visible(
                timeout=content_timeout
            )
            expect(page.locator('h2:has-text("Your Quiz History")')).to_be_visible(
                timeout=content_timeout
            )
            expect(page.locator('button:has-text("Quiz History")')).to_be_visible(
                timeout=content_timeout
            )  # Tab
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_specific_content_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed page-specific content check for '{page_id}' at BP '{bp_name}'. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    print(
        f"--- Success: Page '{page_id}' at Breakpoint '{bp_name}' passed all checks. ---"
    )
