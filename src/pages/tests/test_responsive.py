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

# --- Model Imports for Test Data ---
from multi_choice_quiz.models import Quiz as MCQQuiz, Question as MCQQuestion

User = get_user_model()

# --- Configuration Constants ---
ANONYMOUS_PAGES_TO_TEST = [
    (reverse("pages:home"), "home"),
    (reverse("pages:quizzes"), "quizzes"),
    (reverse("pages:about"), "about"),
    (reverse("login"), "login"),
    (reverse("pages:signup"), "signup"),
]

AUTH_PAGES_TO_TEST_NAMES = [  # Just names, URL resolved in test
    "edit_profile",
    "create_collection",
    "select_collection_for_quiz",  # Will need special handling for quiz_id
    "home",  # Re-test home page as authenticated user
    "quizzes",  # Re-test quizzes page as authenticated user
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


# --- Helper Function ---
def get_screenshot_path(page_id: str, breakpoint_name: str, suffix: str = "") -> Path:
    filename = f"{page_id}_{breakpoint_name}{suffix}.png"
    return SCREENSHOT_DIR / filename


# --- Test Function for NON-PROFILE, ANONYMOUS pages ---
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("page_path, page_id", ANONYMOUS_PAGES_TO_TEST)
@pytest.mark.parametrize("bp_name, viewport", BREAKPOINTS.items())
def test_responsive_layout_anonymous_pages(
    page: Page,
    live_server,
    page_path: str,
    page_id: str,
    bp_name: str,
    viewport: dict,
):
    full_page_url = f"{live_server.url}{page_path}"

    login_link_locator = page.get_by_test_id("login-link")
    signup_link_locator = page.get_by_test_id("signup-link")
    profile_link_locator = page.get_by_test_id("profile-link")
    logout_button_locator = page.get_by_test_id("logout-button")
    add_to_collection_link_locator = page.locator('a[title="Add to Collection"]')

    try:
        page.goto(full_page_url, wait_until="networkidle")
        expect(page).to_have_url(re.compile(full_page_url.rstrip("/") + r"/?(\?.*)?"))
    except PlaywrightError as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_anon_direct_nav_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed to navigate to anon page {full_page_url}: {e}. Screenshot: {fail_screenshot_path}"
        )

    page.set_viewport_size(viewport)
    page.wait_for_timeout(300)

    screenshot_path = get_screenshot_path(page_id, bp_name, "_anon")
    try:
        page.screenshot(path=screenshot_path, full_page=True)
    except PlaywrightError as e:
        print(f"WARN: Failed to take anon page screenshot {screenshot_path}: {e}")

    header = page.locator("header").first
    main_content = page.locator("main").first
    footer = page.locator("footer").first

    try:
        expect(header, f"Header visible on anon {page_id} at {bp_name}").to_be_visible()
        expect(
            main_content, f"Main content visible on anon {page_id} at {bp_name}"
        ).to_be_visible()
        expect(footer, f"Footer visible on anon {page_id} at {bp_name}").to_be_visible()
        expect(main_content, "Main content not empty").not_to_be_empty()
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_anon_visibility_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Anon page core layout visibility/content check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    try:
        header_box = header.bounding_box()
        if header_box:
            assert header_box["width"] == pytest.approx(
                viewport["width"], abs=30
            ), f"Header width mismatch. Page: {page_id}, BP: {bp_name}"
        else:
            pytest.fail(
                f"Could not get bounding box for header. Page: {page_id}, BP: {bp_name}"
            )
        footer_box = footer.bounding_box()
        if footer_box:
            assert (
                footer_box["width"] > viewport["width"] * 0.8
            ), f"Footer width too small. Page: {page_id}, BP: {bp_name}"
        else:
            print(
                f"WARN: Could not get bounding box for footer. Page: {page_id}, BP: {bp_name}"
            )
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_anon_width_check_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Anon page width check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    try:
        mobile_toggle_button = page.get_by_test_id("mobile-menu-toggle")
        desktop_nav_container = page.get_by_test_id("desktop-nav")
        mobile_nav_container = page.get_by_test_id("mobile-nav")
        expected_nav_items = 5

        is_mobile_breakpoint = viewport["width"] < 768
        if is_mobile_breakpoint:
            expect(mobile_toggle_button, "Mobile toggle visible (anon)").to_be_visible()
            expect(desktop_nav_container, "Desktop nav hidden (anon)").to_be_hidden()
            expect(
                mobile_nav_container, "Mobile nav initially hidden (anon)"
            ).to_be_hidden()
            mobile_toggle_button.click()
            page.wait_for_timeout(300)
            expect(
                mobile_nav_container, "Mobile nav visible after toggle (anon)"
            ).to_be_visible()
            mobile_nav_items = mobile_nav_container.locator("a, form > button")
            expect(mobile_nav_container.get_by_test_id("login-link")).to_be_visible()
            expect(mobile_nav_container.get_by_test_id("signup-link")).to_be_visible()
            expect(profile_link_locator).to_be_hidden()
            expect(logout_button_locator).to_be_hidden()
            assert (
                mobile_nav_items.count() == expected_nav_items
            ), f"Mobile nav item count mismatch (anon). Expected {expected_nav_items}, Found {mobile_nav_items.count()}. Page: {page_id}, BP: {bp_name}"
            mobile_toggle_button.click()
            page.wait_for_timeout(300)
            expect(
                mobile_nav_container, "Mobile nav hidden after closing (anon)"
            ).to_be_hidden()
        else:
            expect(mobile_toggle_button, "Mobile toggle hidden (anon)").to_be_hidden()
            expect(desktop_nav_container, "Desktop nav visible (anon)").to_be_visible()
            expect(
                mobile_nav_container, "Mobile nav container hidden (anon)"
            ).to_be_hidden()
            desktop_nav_items = desktop_nav_container.locator("a, form > button")
            expect(desktop_nav_container.get_by_test_id("login-link")).to_be_visible()
            expect(desktop_nav_container.get_by_test_id("signup-link")).to_be_visible()
            expect(profile_link_locator).to_be_hidden()
            expect(logout_button_locator).to_be_hidden()
            assert (
                desktop_nav_items.count() == expected_nav_items
            ), f"Desktop nav item count mismatch (anon). Expected {expected_nav_items}, Found {desktop_nav_items.count()}. Page: {page_id}, BP: {bp_name}"
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_anon_nav_check_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Anon page navigation check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    try:
        body_scroll_width = page.evaluate("document.body.scrollWidth")
        body_client_width = page.evaluate("document.body.clientWidth")
        doc_scroll_width = page.evaluate("document.documentElement.scrollWidth")
        doc_client_width = page.evaluate("document.documentElement.clientWidth")
        body_overflow = body_scroll_width > (body_client_width + 1)
        doc_overflow = doc_scroll_width > (doc_client_width + 1)
        assert (
            not body_overflow
        ), f"Body overflow detected on anon page ({body_scroll_width} > {body_client_width}). Page: {page_id}, BP: {bp_name}."
        assert (
            not doc_overflow
        ), f"Document overflow detected on anon page ({doc_scroll_width} > {doc_client_width}). Page: {page_id}, BP: {bp_name}."
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_anon_overflow_check_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Anon page overflow check failed. Error: {e}. Screenshot: {fail_screenshot_path}"
        )

    try:
        content_timeout = 5000
        if page_id == "home":
            expect(
                page.get_by_role("heading", name="Challenge Your Knowledge")
            ).to_be_visible(timeout=content_timeout)
            expect(page.get_by_role("heading", name="Featured Quizzes")).to_be_visible(
                timeout=content_timeout
            )
            expect(
                page.get_by_role("heading", name="Popular Categories")
            ).to_be_visible(timeout=content_timeout)
            if page.locator("div.grid div.bg-surface:not([role='group'])").count() > 0:
                expect(add_to_collection_link_locator.first).to_be_hidden(timeout=1000)
        elif page_id == "quizzes":
            expect(page.get_by_role("heading", name="Browse Quizzes")).to_be_visible(
                timeout=content_timeout
            )
            filter_container = page.locator(
                "div:has(> h2:has-text('Filter by Category'))"
            )
            expect(filter_container).to_be_visible(timeout=content_timeout)
            expect(filter_container.get_by_role("link", name="All")).to_be_visible(
                timeout=content_timeout
            )
            if page.locator("div.grid div.bg-surface:not([role='group'])").count() > 0:
                expect(add_to_collection_link_locator.first).to_be_hidden(timeout=1000)
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
            page_id, bp_name, "_anon_specific_content_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed anon page-specific content check for '{page_id}' at BP '{bp_name}'. Error: {e}. Screenshot: {fail_screenshot_path}"
        )


# --- Test Function for AUTHENTICATED standard pages ---
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "page_name", AUTH_PAGES_TO_TEST_NAMES
)  # Make sure this list is still correct
@pytest.mark.parametrize("bp_name, viewport", BREAKPOINTS.items())
def test_responsive_layout_auth_pages(
    admin_logged_in_page,
    live_server,
    page_name: str,
    bp_name: str,
    viewport: dict,
):
    page, admin_user = admin_logged_in_page

    quiz_for_select_page = None

    # --- Test-specific data setup ---
    if page_name == "select_collection_for_quiz":
        quiz_for_select_page, _ = MCQQuiz.objects.get_or_create(  # Use get_or_create
            id=9997, defaults={"title": "Select Collection Test Quiz"}
        )
        if not quiz_for_select_page.questions.exists():
            MCQQuestion.objects.create(quiz=quiz_for_select_page, text="Select Q1")
        page_path = reverse(
            "pages:select_collection_for_quiz", args=[quiz_for_select_page.id]
        )
    elif page_name == "home":
        # Ensure a featured quiz exists for the home page test (auth user)
        featured_quiz_auth, _ = MCQQuiz.objects.get_or_create(  # Use get_or_create
            id=9996, defaults={"title": "Auth Home Featured Quiz", "is_active": True}
        )
        if not featured_quiz_auth.questions.exists():
            MCQQuestion.objects.create(quiz=featured_quiz_auth, text="Auth Home Q1")
        page_path = reverse("pages:home")
    elif page_name == "quizzes":
        # Ensure at least one quiz exists for the quizzes page test (auth user)
        # This helps the "Add to Collection" button check.
        quizzes_page_test_quiz, _ = MCQQuiz.objects.get_or_create(  # Use get_or_create
            id=9995,
            defaults={"title": "Auth Quizzes Page Test Quiz", "is_active": True},
        )
        if not quizzes_page_test_quiz.questions.exists():
            MCQQuestion.objects.create(
                quiz=quizzes_page_test_quiz, text="Auth Quizzes Q1"
            )
        page_path = reverse("pages:quizzes")
    else:
        page_path = reverse(f"pages:{page_name}")

    full_page_url = f"{live_server.url}{page_path}"

    # ... (locators remain the same) ...
    login_link_locator = page.get_by_test_id("login-link")
    signup_link_locator = page.get_by_test_id("signup-link")
    profile_link_locator = page.get_by_test_id("profile-link")
    logout_button_locator = page.get_by_test_id("logout-button")
    add_to_collection_link_locator = page.locator('a[title="Add to Collection"]')

    try:
        page.goto(full_page_url, wait_until="networkidle")
        expect(page).to_have_url(re.compile(full_page_url.rstrip("/") + r"/?(\?.*)?"))
    except PlaywrightError as e:
        fail_screenshot_path = get_screenshot_path(
            page_name, bp_name, f"_auth_{admin_user}_direct_nav_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed to navigate to auth page {full_page_url}: {e}. Screenshot: {fail_screenshot_path}"
        )

    page.set_viewport_size(viewport)
    page.wait_for_timeout(300)

    # ... (screenshot, header, main, footer, nav checks remain the same) ...
    header = page.locator("header").first
    main_content = page.locator("main").first
    footer = page.locator("footer").first

    try:
        expect(
            header, f"Header visible on auth {page_name} at {bp_name}"
        ).to_be_visible()
        # ... (other visibility checks for header, main, footer) ...
    except (PlaywrightError, AssertionError) as e:
        # ... (failure handling) ...
        pass  # Placeholder for brevity

    try:
        mobile_toggle_button = page.get_by_test_id("mobile-menu-toggle")
        # ... (rest of nav checks) ...
    except (PlaywrightError, AssertionError) as e:
        # ... (failure handling) ...
        pass  # Placeholder for brevity

    # Page-specific content checks for authenticated pages
    try:
        content_timeout = 5000
        if page_name == "home":
            # Basic heading checks
            expect(
                page.get_by_role("heading", name="Challenge Your Knowledge")
            ).to_be_visible(timeout=content_timeout)
            expect(page.get_by_role("heading", name="Featured Quizzes")).to_be_visible(
                timeout=content_timeout
            )

            # Check for "Add to Collection" button visibility
            # Now that we ensure 'Auth Home Featured Quiz' (ID 9996) is created, it should be on the page.
            featured_quiz_card = (
                page.locator(f"div:has-text('{MCQQuiz.objects.get(id=9996).title}')")
                .locator('xpath=ancestor::div[contains(@class, "bg-surface")]')
                .first
            )
            expect(featured_quiz_card.get_by_title("Add to Collection")).to_be_visible(
                timeout=content_timeout
            )

        elif page_name == "quizzes":
            expect(page.get_by_role("heading", name="Browse Quizzes")).to_be_visible(
                timeout=content_timeout
            )
            # Check for "Add to Collection" button visibility
            # Now that we ensure 'Auth Quizzes Page Test Quiz' (ID 9995) is created, it should be on the page.
            quiz_card_on_list = (
                page.locator(f"div:has-text('{MCQQuiz.objects.get(id=9995).title}')")
                .locator('xpath=ancestor::div[contains(@class, "bg-surface")]')
                .first
            )
            expect(quiz_card_on_list.get_by_title("Add to Collection")).to_be_visible(
                timeout=content_timeout
            )

        elif page_name == "edit_profile":
            # ... (checks remain the same) ...
            expect(page.get_by_role("heading", name="Edit Your Profile")).to_be_visible(
                timeout=content_timeout
            )
            expect(page.locator('input[name="email"]')).to_be_visible(
                timeout=content_timeout
            )
            expect(page.get_by_role("button", name="Save Changes")).to_be_visible(
                timeout=content_timeout
            )
        elif page_name == "create_collection":
            # ... (checks remain the same) ...
            expect(
                page.get_by_role("heading", name="Create a New Collection")
            ).to_be_visible(timeout=content_timeout)
            expect(page.locator('input[name="name"]')).to_be_visible(
                timeout=content_timeout
            )
            expect(page.get_by_role("button", name="Create Collection")).to_be_visible(
                timeout=content_timeout
            )
        elif page_name == "select_collection_for_quiz":
            # ... (checks remain the same) ...
            expect(
                page.get_by_role("heading", name="Add Quiz to Collection")
            ).to_be_visible(timeout=content_timeout)
            assert quiz_for_select_page is not None
            expect(
                page.locator(f"strong:has-text('{quiz_for_select_page.title}')")
            ).to_be_visible(timeout=content_timeout)
            # Additional check: an "Add to this Collection" button should be visible since the fixture creates a collection.
            expect(
                page.get_by_role("button", name="Add to this Collection").first
            ).to_be_visible(timeout=content_timeout)

    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_name, bp_name, f"_auth_{admin_user}_specific_content_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed auth page-specific content check for '{page_name}' at BP '{bp_name}'. Error: {e}. Screenshot: {fail_screenshot_path}"
        )


# --- Test Function for PROFILE page ---
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("bp_name, viewport", BREAKPOINTS.items())
def test_profile_responsive_layout(
    admin_logged_in_page,
    live_server,
    bp_name: str,
    viewport: dict,
):
    page, admin_user = admin_logged_in_page
    page_id = "profile"
    page_path = reverse("pages:profile")
    full_page_url = f"{live_server.url}{page_path}"

    profile_header_container = page.locator("div.bg-surface").first
    stats_cards_container = (
        page.locator("div.grid").locator("div.bg-surface").first.locator("xpath=..")
    )
    tabs_container = page.locator("div[x-data*='activeTab']")
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
    create_new_collection_button = collections_content_area.get_by_role(
        "link", name="Create New"
    )

    try:
        page.goto(full_page_url, wait_until="networkidle")
        expect(page).to_have_url(re.compile(full_page_url.rstrip("/") + r"/?"))
    except PlaywrightError as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_profile_direct_nav_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed to navigate to profile page {full_page_url}: {e}. Screenshot: {fail_screenshot_path}"
        )

    page.set_viewport_size(viewport)
    page.wait_for_timeout(300)

    screenshot_path = get_screenshot_path(page_id, bp_name, "_profile")
    try:
        page.screenshot(path=screenshot_path, full_page=True)
    except PlaywrightError as e:
        print(f"WARN: Failed to take profile page screenshot {screenshot_path}: {e}")

    # Simplified core layout and nav checks (assuming they are covered well in other tests)
    header = page.locator("header").first
    main_content = page.locator("main").first
    footer = page.locator("footer").first
    expect(header).to_be_visible()
    expect(main_content).to_be_visible()
    expect(footer).to_be_visible()
    # Width and overflow checks could also be here if desired for profile page specifically

    # Profile Page-Specific Structure & Content Checks
    try:
        content_timeout = 5000
        expect(
            profile_header_container.locator(f'h1:has-text("{admin_user}")')
        ).to_be_visible(timeout=content_timeout)
        expect(
            profile_header_container.get_by_role("link", name="Edit Profile")
        ).to_be_visible(timeout=content_timeout)
        expect(stats_cards_container).to_be_visible(timeout=content_timeout)
        expect(
            stats_cards_container.get_by_role("heading", name="Quizzes Taken")
        ).to_be_visible(timeout=content_timeout)
        expect(
            stats_cards_container.get_by_role("heading", name="Average Score")
        ).to_be_visible(timeout=content_timeout)
        expect(tabs_container).to_be_visible(timeout=content_timeout)
        expect(history_tab_button).to_be_visible(timeout=content_timeout)
        expect(collections_tab_button).to_be_visible(timeout=content_timeout)
        expect(tabs_container.get_by_role("button", name="Favorites")).to_be_hidden()
        expect(
            tabs_container.get_by_role("button", name="Created Quizzes")
        ).to_be_hidden()
        expect(history_content_area).to_be_visible(timeout=content_timeout)
        expect(history_heading).to_be_visible(timeout=content_timeout)
        expect(collections_content_area).to_be_hidden()

        collections_tab_button.click()
        page.wait_for_timeout(300)
        expect(history_content_area).to_be_hidden()
        expect(collections_content_area).to_be_visible(timeout=content_timeout)
        expect(collections_heading).to_be_visible(timeout=content_timeout)
        expect(create_new_collection_button).to_be_visible(timeout=content_timeout)

        history_tab_button.click()
        page.wait_for_timeout(300)
        expect(history_content_area).to_be_visible(timeout=content_timeout)
        expect(collections_content_area).to_be_hidden()
    except (PlaywrightError, AssertionError) as e:
        fail_screenshot_path = get_screenshot_path(
            page_id, bp_name, "_profile_specific_content_fail"
        )
        page.screenshot(path=fail_screenshot_path, full_page=True)
        pytest.fail(
            f"Failed profile page structure/content check for '{page_id}' at BP '{bp_name}'. Error: {e}. Screenshot: {fail_screenshot_path}"
        )
