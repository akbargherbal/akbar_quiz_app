# src/pages/tests/test_templates.py (Corrected for Profile Structure Changes)

import pytest
import re
import os
from playwright.sync_api import Page, expect
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

# --- Constants ---
DESKTOP_VIEWPORT = {"width": 1280, "height": 720}
MOBILE_VIEWPORT = {"width": 375, "height": 667}

# --- Tests ---


def test_home_page_loads_and_title(page: Page, live_server):
    page.set_viewport_size(DESKTOP_VIEWPORT)
    home_url = f"{live_server.url}{reverse('pages:home')}"
    page.goto(home_url)
    expect(page).to_have_title(re.compile("Home | QuizMaster"))
    expect(page.get_by_role("heading", name="Challenge Your Knowledge")).to_be_visible()


def test_quizzes_page_loads(page: Page, live_server):
    page.set_viewport_size(DESKTOP_VIEWPORT)
    quizzes_url = f"{live_server.url}{reverse('pages:quizzes')}"
    page.goto(quizzes_url)
    expect(page).to_have_title(re.compile("Quizzes | QuizMaster"))
    expect(page.get_by_role("heading", name="Browse Quizzes")).to_be_visible()


def test_about_page_loads(page: Page, live_server):
    page.set_viewport_size(DESKTOP_VIEWPORT)
    about_url = f"{live_server.url}{reverse('pages:about')}"
    page.goto(about_url)
    expect(page).to_have_title(re.compile("About | QuizMaster"))
    expect(page.get_by_role("heading", name="About QuizMaster")).to_be_visible()


def test_anonymous_user_navigation(page: Page, live_server):
    # --- Desktop checks ---
    print("\n--- Running Anonymous Desktop Nav Checks ---")
    page.set_viewport_size(DESKTOP_VIEWPORT)
    home_url = f"{live_server.url}{reverse('pages:home')}"
    page.goto(home_url)
    page.wait_for_load_state("networkidle")
    desktop_nav = page.locator("nav.hidden.md\\:flex")
    expect(desktop_nav).to_be_visible()
    expect(desktop_nav.get_by_role("link", name="Login")).to_be_visible()
    expect(desktop_nav.get_by_role("link", name="Login")).to_have_attribute(
        "href", reverse("login")
    )
    expect(desktop_nav.get_by_role("link", name="Sign Up")).to_be_visible()
    expect(desktop_nav.get_by_role("link", name="Sign Up")).to_have_attribute(
        "href", reverse("pages:signup")
    )
    expect(
        desktop_nav.get_by_role("link", name="Profile", exact=True)
    ).not_to_be_visible()
    expect(desktop_nav.get_by_role("button", name="Logout")).not_to_be_visible()
    print("Desktop checks passed.")

    # --- Mobile checks ---
    print("--- Running Anonymous Mobile Nav Checks ---")
    page.set_viewport_size(MOBILE_VIEWPORT)
    page.goto(home_url)
    page.wait_for_load_state("networkidle")
    mobile_menu_button = page.locator("div.md\\:hidden > button")
    expect(mobile_menu_button).to_be_visible(timeout=5000)
    mobile_menu_button.click()
    mobile_nav = page.locator("nav[x-show='open']")
    expect(mobile_nav).to_be_visible(timeout=2000)
    expect(mobile_nav.get_by_role("link", name="Login")).to_be_visible()
    expect(mobile_nav.get_by_role("link", name="Login")).to_have_attribute(
        "href", reverse("login")
    )
    expect(mobile_nav.get_by_role("link", name="Sign Up")).to_be_visible()
    expect(mobile_nav.get_by_role("link", name="Sign Up")).to_have_attribute(
        "href", reverse("pages:signup")
    )
    expect(
        mobile_nav.get_by_role("link", name="Profile", exact=True)
    ).not_to_be_visible()
    expect(mobile_nav.get_by_role("button", name="Logout")).not_to_be_visible()
    print("Mobile checks passed.")


@pytest.mark.django_db
def test_authenticated_user_navigation(admin_logged_in_page, live_server):
    """Verify navigation links for authenticated users using fixture."""
    page, admin_user = admin_logged_in_page
    print(f"\n--- Running Authenticated Desktop Nav Checks (User: {admin_user}) ---")

    # --- Desktop checks ---
    page.set_viewport_size(DESKTOP_VIEWPORT)
    home_url = f"{live_server.url}{reverse('pages:home')}"
    print(f"Navigating to homepage: {home_url}")
    page.goto(home_url)
    page.wait_for_load_state("networkidle")

    desktop_nav = page.locator("nav.hidden.md\\:flex")
    expect(desktop_nav).to_be_visible()
    profile_link_desktop = desktop_nav.get_by_role(
        "link", name=re.compile(f"Profile \\({admin_user}\\)")
    )
    expect(profile_link_desktop).to_be_visible()
    expect(profile_link_desktop).to_have_attribute("href", reverse("pages:profile"))

    logout_button_desktop = desktop_nav.locator(
        "form[action*='logout'] > button:has-text('Logout')"
    )
    expect(logout_button_desktop).to_be_visible()

    expect(desktop_nav.get_by_role("link", name="Login")).not_to_be_visible()
    expect(desktop_nav.get_by_role("link", name="Sign Up")).not_to_be_visible()
    print("Desktop checks passed.")

    # --- Mobile checks ---
    print(f"--- Running Authenticated Mobile Nav Checks (User: {admin_user}) ---")
    page.set_viewport_size(MOBILE_VIEWPORT)
    page.goto(home_url)  # Reload page in new viewport
    page.wait_for_load_state("networkidle")

    mobile_menu_button = page.locator("div.md\\:hidden > button")
    expect(mobile_menu_button).to_be_visible(timeout=5000)
    mobile_menu_button.click()

    mobile_nav = page.locator("nav[x-show='open']")
    expect(mobile_nav).to_be_visible(timeout=2000)

    profile_link_mobile = mobile_nav.get_by_role(
        "link", name=re.compile(f"Profile \\({admin_user}\\)")
    )
    expect(profile_link_mobile).to_be_visible()
    expect(profile_link_mobile).to_have_attribute("href", reverse("pages:profile"))

    logout_button_mobile = mobile_nav.locator(
        "form[action*='logout'] > button:has-text('Logout')"
    )
    expect(logout_button_mobile).to_be_visible()

    expect(mobile_nav.get_by_role("link", name="Login")).not_to_be_visible()
    expect(mobile_nav.get_by_role("link", name="Sign Up")).not_to_be_visible()
    print("Mobile checks passed.")


def test_login_page_loads(page: Page, live_server):
    page.set_viewport_size(DESKTOP_VIEWPORT)
    login_url = f"{live_server.url}{reverse('login')}"
    page.goto(login_url)
    expect(page).to_have_title(re.compile("Login | QuizMaster"))
    expect(page.get_by_role("heading", name="Login to Your Account")).to_be_visible()
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="password"]')).to_be_visible()


def test_signup_page_loads(page: Page, live_server):
    page.set_viewport_size(DESKTOP_VIEWPORT)
    signup_url = f"{live_server.url}{reverse('pages:signup')}"
    page.goto(signup_url)
    expect(page).to_have_title(re.compile("Sign Up | QuizMaster"))
    expect(page.get_by_role("heading", name="Create Your Account")).to_be_visible()
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="email"]')).to_be_visible()
    expect(page.locator('input[name="password1"]')).to_be_visible()
    expect(page.locator('input[name="password2"]')).to_be_visible()
    expect(
        page.locator('button[type="submit"]:has-text("Create Account")')
    ).to_be_visible()


@pytest.mark.django_db
def test_profile_page_structure_when_authenticated(admin_logged_in_page, live_server):
    """Check basic structure of the profile page using fixture."""
    page, admin_user = admin_logged_in_page
    print(f"\n--- Checking Profile Structure (User: {admin_user}) ---")

    profile_url = f"{live_server.url}{reverse('pages:profile')}"
    page.set_viewport_size(DESKTOP_VIEWPORT)
    print(f"Navigating to profile page: {profile_url}")
    page.goto(profile_url)
    page.wait_for_load_state("networkidle")

    expect(page).to_have_title(re.compile(f"{admin_user}'s Profile | QuizMaster"))
    expect(page.locator(f'h1:has-text("{admin_user}")')).to_be_visible()
    expect(page.get_by_role("button", name="Quiz History")).to_be_visible()
    # --- START MODIFICATION ---
    # Check for "Collections" button instead of "Favorites"
    expect(page.get_by_role("button", name="Collections")).to_be_visible()
    # Optionally, assert "Favorites" is NOT visible
    expect(page.get_by_role("button", name="Favorites")).not_to_be_visible()
    # --- END MODIFICATION ---
    expect(
        page.locator(f'div:has-text("{admin_user[0].upper()}")').first
    ).to_be_visible()
    print("Profile page structure checks passed.")


@pytest.mark.django_db
def test_profile_page_shows_empty_history(admin_logged_in_page, live_server):
    """Verify profile page shows empty history message using fixture."""
    page, admin_user = admin_logged_in_page
    print(f"\n--- Checking Profile Empty History (User: {admin_user}) ---")

    profile_url = f"{live_server.url}{reverse('pages:profile')}"
    page.set_viewport_size(DESKTOP_VIEWPORT)
    print(f"Navigating to profile page: {profile_url}")
    page.goto(profile_url)
    page.wait_for_load_state("networkidle")

    history_tab_content = page.locator("div[x-show=\"activeTab === 'history'\"]")
    # Check within the history tab content
    expect(
        history_tab_content.locator("text=You haven't completed any quizzes yet.")
    ).to_be_visible()
    # Ensure example attempt text is not visible
    expect(history_tab_content.locator("text=History Quiz")).not_to_be_visible()
    print("Empty history message check passed.")
