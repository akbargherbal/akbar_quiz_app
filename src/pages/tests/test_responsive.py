# src/pages/tests/test_responsive.py (MODIFIED for Step 5.6)
# REFACTORED with data-testid locators & new profile structure checks

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
# Keep existing setup block
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
]

BREAKPOINTS = {
    "mobile": {"width": 375, "height": 667},
    "sm": {"width": 640, "height": 768},
    "md": {"width": 768, "height": 1024},
    "lg": {"width": 1024, "height": 768},
    "xl": {"width": 1280, "height": 800},
    "2xl": {"width": 1536, "height": 960},
}

SCREENSHOT_DIR = settings.SCREENSHOTS_DIR / "responsive"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Timeouts
DEFAULT_VISIBILITY_TIMEOUT = 20000
INSTANCE_WAIT_TIMEOUT = 10000
EVENT_WAIT_TIMEOUT = 8000
POST_EVENT_UI_TIMEOUT = 5000


# --- Helper Function ---
def get_screenshot_path(page_id: str, breakpoint_name: str, suffix: str = "") -> Path:
    filename = f"{page_id}_{breakpoint_name}{suffix}.png"
    return SCREENSHOT_DIR / filename


# --- Test Function for NON-PROFILE pages ---
# Keep test_responsive_layout_standard_pages exactly as it was in release_06.txt
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("page_path, page_id", PAGES_TO_TEST)
@pytest.mark.parametrize("bp_name, viewport", BREAKPOINTS.items())
def test_responsive_layout_standard_pages(
    page: Page,
    live_server,
    page_path: str,
    page_id: str,
    bp_name: str,
    viewport: dict,
):
    """
    Tests the responsive layout of standard pages (non-profile) across breakpoints.
    Uses live_server fixture. Assumes anonymous access is sufficient.
    """
    full_page_url = f"{live_server.url}{page_path}"

    # --- Use data-testid Locators ---
    login_link_locator = page.get_by_test_id("login-link")
    signup_link_locator = page.get_by_test_id("signup-link")
    profile_link_locator = page.get_by_test_id("profile-link")
    logout_button_locator = page.get_by_test_id("logout-button")

    print(
        f"\n--- Testing Standard Page: '{page_id}' at Breakpoint: '{bp_name}' ({viewport['width']}x{viewport['height']}) ---"
    )
    print(f"Target URL: {full_page_url}")

    # --- Direct Navigation ---
    try:
        print(f"Navigating directly to: {full_page_url}")
        page.goto(full_page_url, wait_until="networkidle")
        expect(page).to_have_url(re.compile(full_page_url.rstrip("/") + r"/?(\?.*)?"))
        print(f"Successfully navigated directly to page: {page.url}")
    except PlaywrightError as e:
        fail_screenshot_path = get_screenshot_path(page_id, bp_name, "_direct_nav_fail")
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed to navigate to page {full_page_url}: {e}. Screenshot: {fail_screenshot_path}"
        )

    # ========================================================================
    # --- Core Responsive Checks (Run for these pages) ---
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
                f"Header width: {header_box['width']:.1f}px (Viewport: {viewport['width']}px)"
            )
            assert header_box["width"] == pytest.approx(
                viewport["width"], abs=30
            ), f"Header width mismatch. Page: {page_id}, BP: {bp_name}"
        else:
            pytest.fail(
                f"Could not get bounding box for header. Page: {page_id}, BP: {bp_name}"
            )

        footer_box = footer.bounding_box()
        if footer_box:
            print(
                f"Footer width: {footer_box['width']:.1f}px (Viewport: {viewport['width']}px)"
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

    # --- Navigation Element Visibility Checks (Assuming Logged Out) ---
    print("Checking navigation visibility (Logged Out)...")
    try:
        # --- Use data-testid Locators ---
        mobile_toggle_button = page.get_by_test_id("mobile-menu-toggle")
        desktop_nav_container = page.get_by_test_id("desktop-nav")
        mobile_nav_container = page.get_by_test_id("mobile-nav")

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

            # Check visibility within the container using data-testid
            expect(mobile_nav_container.get_by_test_id("login-link")).to_be_visible()
            expect(mobile_nav_container.get_by_test_id("signup-link")).to_be_visible()
            expect(
                profile_link_locator
            ).to_be_hidden()  # Should not exist for anonymous
            expect(
                logout_button_locator
            ).to_be_hidden()  # Should not exist for anonymous

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

            # Check visibility within the container using data-testid
            expect(desktop_nav_container.get_by_test_id("login-link")).to_be_visible()
            expect(desktop_nav_container.get_by_test_id("signup-link")).to_be_visible()
            expect(profile_link_locator).to_be_hidden()
            expect(logout_button_locator).to_be_hidden()

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
                page.get_by_role("heading", name="Challenge Your Knowledge")
            ).to_be_visible(timeout=content_timeout)
            expect(page.get_by_role("heading", name="Featured Quizzes")).to_be_visible(
                timeout=content_timeout
            )
        elif page_id == "quizzes":
            expect(page.get_by_role("heading", name="Browse Quizzes")).to_be_visible(
                timeout=content_timeout
            )
            filter_container = page.locator("div:has(> h2:has-text('Filter by Topic'))")
            expect(filter_container).to_be_visible(timeout=content_timeout)
            expect(filter_container.get_by_role("link", name="All")).to_be_visible(
                timeout=content_timeout
            )
        elif page_id == "about":
            expect(page.get_by_role("heading", name="About QuizMaster")).to_be_visible(
                timeout=content_timeout
            )
            expect(page.get_by_role("heading", name="Our Mission")).to_be_visible(
                timeout=content_timeout
            )
        elif page_id == "login":
            expect(
                page.get_by_role("heading", name="Login to Your Account")
            ).to_be_visible(timeout=content_timeout)
            expect(page.locator("#username")).to_be_visible(timeout=content_timeout)
            expect(page.locator("#password")).to_be_visible(timeout=content_timeout)
            expect(page.get_by_role("button", name="Login")).to_be_visible(
                timeout=content_timeout
            )
        elif page_id == "signup":
            expect(
                page.get_by_role("heading", name="Create Your Account")
            ).to_be_visible(timeout=content_timeout)
            expect(page.locator("#id_username")).to_be_visible(timeout=content_timeout)
            expect(page.locator("#id_email")).to_be_visible(timeout=content_timeout)
            expect(page.locator("#id_password1")).to_be_visible(timeout=content_timeout)
            expect(page.locator("#id_password2")).to_be_visible(timeout=content_timeout)
            expect(page.get_by_role("button", name="Create Account")).to_be_visible(
                timeout=content_timeout
            )

    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_specific_content_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed page-specific content check for '{page_id}' at BP '{bp_name}'. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    print(
        f"--- Success: Standard Page '{page_id}' at Breakpoint '{bp_name}' passed all checks. ---"
    )


# --- Test Function for PROFILE page (MODIFIED for Step 5.6) ---
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("bp_name, viewport", BREAKPOINTS.items())
def test_profile_responsive_layout(
    admin_logged_in_page,  # Use the fixture
    live_server,
    bp_name: str,
    viewport: dict,
):
    """
    Tests the responsive layout of the profile page across breakpoints.
    Uses admin_logged_in_page fixture for authentication.
    Verifies the Mockup 1 structure (Stats above Tabs).
    """
    page, admin_user = admin_logged_in_page  # Unpack fixture
    page_id = "profile"
    page_path = reverse("pages:profile")
    full_page_url = f"{live_server.url}{page_path}"

    # --- Use data-testid Locators ---
    login_link_locator = page.get_by_test_id("login-link")
    signup_link_locator = page.get_by_test_id("signup-link")
    profile_link_locator = page.get_by_test_id("profile-link")
    logout_button_locator = page.get_by_test_id("logout-button")

    # --- NEW Locators for Profile Structure ---
    profile_header_container = page.locator(
        "div.bg-surface"
    ).first  # The main header box
    stats_cards_container = (
        page.locator("div.grid").locator("div.bg-surface").first.locator("xpath=..")
    )  # Find first card, go to parent grid
    tabs_container = page.locator(
        "div[x-data*='activeTab']"
    )  # Container with Alpine state
    history_tab_button = tabs_container.get_by_role("button", name="Quiz History")
    collections_tab_button = tabs_container.get_by_role("button", name="Collections")
    history_content_area = tabs_container.locator(
        "div[x-show=\"activeTab === 'history'\"]"
    )
    collections_content_area = tabs_container.locator(
        "div[x-show=\"activeTab === 'collections'\"]"
    )
    history_heading = history_content_area.get_by_role(
        "heading", name="Your Quiz History"
    )
    collections_heading = collections_content_area.get_by_role(
        "heading", name="Your Collections"
    )
    # --- End New Locators ---

    print(
        f"\n--- Testing PROFILE Page at Breakpoint: '{bp_name}' ({viewport['width']}x{viewport['height']}) ---"
    )
    print(f"User: {admin_user}")
    print(f"Target URL: {full_page_url}")

    # --- Direct Navigation (User is already logged in by fixture) ---
    try:
        print(f"Navigating directly to: {full_page_url}")
        page.goto(full_page_url, wait_until="networkidle")
        expect(page).to_have_url(re.compile(full_page_url.rstrip("/") + r"/?"))
        print(f"Successfully navigated to profile page: {page.url}")
    except PlaywrightError as e:
        fail_screenshot_path = get_screenshot_path(page_id, bp_name, "_direct_nav_fail")
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed to navigate to page {full_page_url}: {e}. Screenshot: {fail_screenshot_path}"
        )

    # ========================================================================
    # --- Core Responsive Checks (Run for profile page) ---
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
    # Keep existing width checks
    print("Checking element widths...")
    try:
        header_box = header.bounding_box()
        if header_box:
            print(
                f"Header width: {header_box['width']:.1f}px (Viewport: {viewport['width']}px)"
            )
            assert header_box["width"] == pytest.approx(
                viewport["width"], abs=30
            ), f"Header width mismatch. Page: {page_id}, BP: {bp_name}"
        else:
            pytest.fail(
                f"Could not get bounding box for header. Page: {page_id}, BP: {bp_name}"
            )

        footer_box = footer.bounding_box()
        if footer_box:
            print(
                f"Footer width: {footer_box['width']:.1f}px (Viewport: {viewport['width']}px)"
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

    # --- Navigation Element Visibility Checks (Assuming Logged In) ---
    # Keep existing navigation checks for logged-in user
    print("Checking navigation visibility (Logged In)...")
    try:
        mobile_toggle_button = page.get_by_test_id("mobile-menu-toggle")
        desktop_nav_container = page.get_by_test_id("desktop-nav")
        mobile_nav_container = page.get_by_test_id("mobile-nav")
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
            expect(mobile_nav_container.get_by_test_id("profile-link")).to_be_visible()
            expect(mobile_nav_container.get_by_test_id("logout-button")).to_be_visible()
            expect(login_link_locator).to_be_hidden()
            expect(signup_link_locator).to_be_hidden()
            assert (
                mobile_nav_items.count() == expected_nav_items
            ), f"Mobile nav item count mismatch. Page: {page_id}, BP: {bp_name}"
            mobile_toggle_button.click()  # Close menu
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
            expect(desktop_nav_container.get_by_test_id("profile-link")).to_be_visible()
            expect(
                desktop_nav_container.get_by_test_id("logout-button")
            ).to_be_visible()
            expect(login_link_locator).to_be_hidden()
            expect(signup_link_locator).to_be_hidden()
            assert (
                desktop_nav_items.count() == expected_nav_items
            ), f"Desktop nav item count mismatch. Page: {page_id}, BP: {bp_name}"
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(page_id, bp_name, "_nav_check_fail")
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Navigation check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    # --- Horizontal Overflow Check ---
    # Keep existing overflow check
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

    # --- Page-Specific Structure & Content Checks (Profile Page - Step 5.6) ---
    print("Checking NEW profile-specific structure and content...")
    try:
        content_timeout = 5000
        # Check header content (already partially covered by nav check)
        expect(
            profile_header_container.locator(f'h1:has-text("{admin_user}")')
        ).to_be_visible(timeout=content_timeout)
        expect(
            profile_header_container.get_by_role("link", name="Edit Profile")
        ).to_be_visible(timeout=content_timeout)

        # Check Stats Cards are visible
        expect(stats_cards_container, "Stats container visible").to_be_visible(
            timeout=content_timeout
        )
        expect(
            stats_cards_container.get_by_role("heading", name="Quizzes Taken")
        ).to_be_visible(timeout=content_timeout)
        expect(
            stats_cards_container.get_by_role("heading", name="Average Score")
        ).to_be_visible(timeout=content_timeout)
        # Add checks for the other two stat card headings if desired

        # Check Tabs Container and Buttons
        expect(tabs_container, "Tabs container visible").to_be_visible(
            timeout=content_timeout
        )
        expect(history_tab_button, "History tab button visible").to_be_visible(
            timeout=content_timeout
        )
        expect(collections_tab_button, "Collections tab button visible").to_be_visible(
            timeout=content_timeout
        )
        # Ensure other tabs (Favorites, Created) are NOT present
        expect(tabs_container.get_by_role("button", name="Favorites")).to_be_hidden()
        expect(
            tabs_container.get_by_role("button", name="Created Quizzes")
        ).to_be_hidden()

        # Check default tab content (History)
        expect(
            history_content_area, "History content area initially visible"
        ).to_be_visible(timeout=content_timeout)
        expect(history_heading, "History heading visible").to_be_visible(
            timeout=content_timeout
        )
        # Check collections content is initially hidden
        expect(
            collections_content_area, "Collections content initially hidden"
        ).to_be_hidden()

        # Check tab switching
        print("Switching to Collections tab...")
        collections_tab_button.click()
        page.wait_for_timeout(300)  # Allow Alpine transition
        expect(
            history_content_area, "History content hidden after switch"
        ).to_be_hidden()
        expect(
            collections_content_area, "Collections content visible after switch"
        ).to_be_visible(timeout=content_timeout)
        expect(collections_heading, "Collections heading visible").to_be_visible(
            timeout=content_timeout
        )

        print("Switching back to History tab...")
        history_tab_button.click()
        page.wait_for_timeout(300)  # Allow Alpine transition
        expect(
            history_content_area, "History content visible after switching back"
        ).to_be_visible(timeout=content_timeout)
        expect(
            collections_content_area, "Collections content hidden after switching back"
        ).to_be_hidden()

        # We don't check the *dynamic content* of the history list here,
        # just that the container and heading are present.
        # Dynamic content is tested in test_views.py and test_templates.py

    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_specific_content_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed NEW profile page structure/content check for '{page_id}' at BP '{bp_name}'. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    print(
        f"--- Success: PROFILE Page at Breakpoint '{bp_name}' passed all NEW structure checks. ---"
    )
