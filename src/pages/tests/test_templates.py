# src/pages/tests/test_templates.py (Corrected for Viewport and Locator Specificity)

import pytest
import re
import os
from playwright.sync_api import Page, expect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client as DjangoClient
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

User = get_user_model()

BASE_URL = os.environ.get("SERVER_URL", "http://localhost:8000")
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "pages")
os.makedirs(LOG_DIR, exist_ok=True)

# Define standard viewports
DESKTOP_VIEWPORT = {"width": 1280, "height": 720}
MOBILE_VIEWPORT = {"width": 375, "height": 667}  # Example: iPhone SE size


def setup_logged_in_user(username, password):
    """Ensures user exists and returns logged-in Django Client."""
    try:
        user = User.objects.get(username=username)
        print(f"User '{username}' already exists.")
    except User.DoesNotExist:
        user = User.objects.create_user(username=username, password=password)
        print(f"Created user '{username}'.")
    if not user.has_usable_password():
        user.set_password(password)
        user.save()
        print(f"Ensured user '{username}' exists and has password.")

    django_client = DjangoClient()
    logged_in = django_client.login(username=username, password=password)
    if not logged_in:
        print(
            f"ERROR: Django Client login failed for user '{username}'. Check credentials/backend."
        )
        pytest.fail(f"Setup failed: Could not log in Django client as '{username}'")
    print(f"Successfully logged in Django client as {username}.")
    return django_client


# --- Tests ---


def test_home_page_loads_and_title(page: Page):
    """Verify the home page loads and has the correct title."""
    page.set_viewport_size(DESKTOP_VIEWPORT)  # Ensure desktop size for consistency
    page.goto(BASE_URL + reverse("pages:home"))
    expect(page).to_have_title(re.compile("Home | QuizMaster"))
    expect(page.get_by_role("heading", name="Challenge Your Knowledge")).to_be_visible()


def test_quizzes_page_loads(page: Page):
    """Verify the quizzes page loads."""
    page.set_viewport_size(DESKTOP_VIEWPORT)  # Ensure desktop size
    page.goto(BASE_URL + reverse("pages:quizzes"))
    expect(page).to_have_title(re.compile("Quizzes | QuizMaster"))
    expect(page.get_by_role("heading", name="Browse Quizzes")).to_be_visible()


def test_about_page_loads(page: Page):
    """Verify the about page loads."""
    page.set_viewport_size(DESKTOP_VIEWPORT)  # Ensure desktop size
    page.goto(BASE_URL + reverse("pages:about"))
    expect(page).to_have_title(re.compile("About | QuizMaster"))
    expect(page.get_by_role("heading", name="About QuizMaster")).to_be_visible()


# --- Navigation Tests ---


def test_anonymous_user_navigation(page: Page):
    """Verify navigation links for anonymous users."""
    # --- Desktop checks ---
    print("\n--- Running Anonymous Desktop Nav Checks ---")
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(BASE_URL + reverse("pages:home"))
    page.wait_for_load_state("networkidle")  # Wait for stability

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
    page.goto(BASE_URL + reverse("pages:home"))  # Reload page in new viewport
    page.wait_for_load_state("networkidle")  # Wait for stability

    mobile_menu_button = page.locator("div.md\\:hidden > button")
    # Assert button is now visible before clicking
    expect(mobile_menu_button).to_be_visible(
        timeout=5000
    )  # Add timeout for visibility check
    print("Mobile menu button found and is visible.")
    mobile_menu_button.click()
    print("Clicked mobile menu button.")

    # Locate the revealed mobile navigation menu
    mobile_nav = page.locator("nav[x-show='open']")
    expect(mobile_nav).to_be_visible(timeout=2000)  # Wait for dropdown animation
    print("Mobile nav dropdown is visible.")

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
def test_authenticated_user_navigation(page: Page):
    """Verify navigation links for authenticated users."""
    admin_user = "testuser_nav"
    admin_pass = "password123"
    try:
        user = User.objects.get(username=admin_user)
        # Ensure the user is active and staff/super for admin login
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(admin_pass)
        user.save()
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=admin_user,
            password=admin_pass,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
    print(f"\nEnsured user '{admin_user}' exists and is configured for admin login.")

    # --- Login via Admin ---
    admin_login_url = BASE_URL + reverse("admin:index")
    page.goto(admin_login_url)
    if "login" in page.url:
        page.locator("#id_username").fill(admin_user)
        page.locator("#id_password").fill(admin_pass)
        page.locator('input[type="submit"]').click()
        # Wait for admin page load after login
        expect(page.get_by_role("heading", name="Site administration")).to_be_visible(
            timeout=10000
        )
        print(f"Successfully logged in as {admin_user} via /admin/")
    else:
        # Check if we are already on admin page
        expect(page.get_by_role("heading", name="Site administration")).to_be_visible(
            timeout=5000
        )
        print(f"Already logged in or admin page loaded directly for {admin_user}.")

    # --- Desktop checks ---
    print("--- Running Authenticated Desktop Nav Checks ---")
    page.set_viewport_size(DESKTOP_VIEWPORT)
    home_url = BASE_URL + reverse("pages:home")
    page.goto(home_url)
    page.wait_for_load_state("networkidle")  # Wait for stability
    print(f"Navigated to homepage: {home_url}")

    desktop_nav = page.locator("nav.hidden.md\\:flex")
    expect(desktop_nav).to_be_visible()
    profile_link_desktop = desktop_nav.get_by_role(
        "link", name=re.compile(f"Profile \\({admin_user}\\)")
    )
    expect(profile_link_desktop).to_be_visible()
    expect(profile_link_desktop).to_have_attribute("href", reverse("pages:profile"))

    # Check the Logout *button* within its form
    logout_button_desktop = desktop_nav.locator(
        "form[action*='logout'] > button:has-text('Logout')"
    )
    expect(logout_button_desktop).to_be_visible()

    expect(desktop_nav.get_by_role("link", name="Login")).not_to_be_visible()
    expect(desktop_nav.get_by_role("link", name="Sign Up")).not_to_be_visible()
    print("Desktop checks passed.")

    # --- Mobile checks ---
    print("--- Running Authenticated Mobile Nav Checks ---")
    page.set_viewport_size(MOBILE_VIEWPORT)
    page.goto(home_url)  # Reload page in new viewport
    page.wait_for_load_state("networkidle")  # Wait for stability

    mobile_menu_button = page.locator("div.md\\:hidden > button")
    # Assert button is now visible before clicking
    expect(mobile_menu_button).to_be_visible(timeout=5000)
    print("Mobile menu button found and is visible.")
    mobile_menu_button.click()
    print("Clicked mobile menu button.")

    # Locate the revealed mobile navigation menu
    mobile_nav = page.locator("nav[x-show='open']")
    expect(mobile_nav).to_be_visible(timeout=2000)  # Wait for dropdown animation
    print("Mobile nav dropdown is visible.")

    profile_link_mobile = mobile_nav.get_by_role(
        "link", name=re.compile(f"Profile \\({admin_user}\\)")
    )
    expect(profile_link_mobile).to_be_visible()
    expect(profile_link_mobile).to_have_attribute("href", reverse("pages:profile"))

    # Check the Logout *button* within its form
    logout_button_mobile = mobile_nav.locator(
        "form[action*='logout'] > button:has-text('Logout')"
    )
    expect(logout_button_mobile).to_be_visible()

    expect(mobile_nav.get_by_role("link", name="Login")).not_to_be_visible()
    expect(mobile_nav.get_by_role("link", name="Sign Up")).not_to_be_visible()
    print("Mobile checks passed.")


# --- Remaining tests unchanged ---


def test_login_page_loads(page: Page):
    """Verify the standard Django login page loads."""
    page.set_viewport_size(DESKTOP_VIEWPORT)  # Ensure desktop size
    login_url = BASE_URL + reverse("login")
    page.goto(login_url)
    expect(page).to_have_title(re.compile("Login | QuizMaster"))
    expect(page.get_by_role("heading", name="Login to Your Account")).to_be_visible()
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="password"]')).to_be_visible()


def test_signup_page_loads(page: Page):
    """Verify the signup page loads correctly (without placeholder text)."""
    page.set_viewport_size(DESKTOP_VIEWPORT)  # Ensure desktop size
    signup_url = BASE_URL + reverse("pages:signup")
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
def test_profile_page_structure_when_authenticated(page: Page):
    """Check basic structure of the profile page for a logged-in user."""
    admin_user = "testuser_prof_struct"
    admin_pass = "password123"
    try:
        user = User.objects.get(username=admin_user)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(admin_pass)
        user.save()
    except User.DoesNotExist:
        User.objects.create_user(
            username=admin_user,
            password=admin_pass,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
    print(f"\nEnsured user '{admin_user}' exists and is configured for admin login.")

    admin_login_url = BASE_URL + reverse("admin:index")
    page.goto(admin_login_url)
    if "login" in page.url:
        page.locator("#id_username").fill(admin_user)
        page.locator("#id_password").fill(admin_pass)
        page.locator('input[type="submit"]').click()
        expect(page.get_by_role("heading", name="Site administration")).to_be_visible(
            timeout=10000
        )
        print(f"Successfully logged in as {admin_user} via /admin/")
    else:
        expect(page.get_by_role("heading", name="Site administration")).to_be_visible(
            timeout=5000
        )
        print(f"Already logged in or admin page loaded directly for {admin_user}.")

    profile_url = BASE_URL + reverse("pages:profile")
    page.set_viewport_size(DESKTOP_VIEWPORT)  # Ensure desktop size for profile check
    page.goto(profile_url)
    page.wait_for_load_state("networkidle")

    expect(page).to_have_title(re.compile(f"{admin_user}'s Profile | QuizMaster"))
    # Profile header check
    expect(
        page.locator(f'h1:has-text("{admin_user}")')
    ).to_be_visible()  # More specific check for username
    # Tab check
    expect(page.get_by_role("button", name="Quiz History")).to_be_visible()
    expect(page.get_by_role("button", name="Favorites")).to_be_visible()
    # Check avatar placeholder existence (can be refined if you add specific class/id)
    expect(
        page.locator(f'div:has-text("{admin_user[0].upper()}")').first
    ).to_be_visible()
    print("Profile page structure checks passed.")


@pytest.mark.django_db
def test_profile_page_shows_empty_history(page: Page):
    """Verify profile page shows empty history message for new user."""
    admin_user = "testuser_empty_hist"
    admin_pass = "password123"
    try:
        user = User.objects.get(username=admin_user)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(admin_pass)
        user.save()
    except User.DoesNotExist:
        User.objects.create_user(
            username=admin_user,
            password=admin_pass,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
    print(f"\nEnsured user '{admin_user}' exists and is configured for admin login.")

    admin_login_url = BASE_URL + reverse("admin:index")
    page.goto(admin_login_url)
    if "login" in page.url:
        page.locator("#id_username").fill(admin_user)
        page.locator("#id_password").fill(admin_pass)
        page.locator('input[type="submit"]').click()
        expect(page.get_by_role("heading", name="Site administration")).to_be_visible(
            timeout=10000
        )
        print(f"Successfully logged in as {admin_user} via /admin/")
    else:
        expect(page.get_by_role("heading", name="Site administration")).to_be_visible(
            timeout=5000
        )
        print(f"Already logged in or admin page loaded directly for {admin_user}.")

    profile_url = BASE_URL + reverse("pages:profile")
    page.set_viewport_size(DESKTOP_VIEWPORT)  # Ensure desktop size
    page.goto(profile_url)
    page.wait_for_load_state("networkidle")

    # Verify the empty history message is visible within the correct tab
    # Ensure the 'History' tab is clicked or is default
    history_tab_content = page.locator("div[x-show=\"activeTab === 'history'\"]")
    expect(
        history_tab_content.locator("text=You haven't completed any quizzes yet.")
    ).to_be_visible()
    # Check that a placeholder for an actual quiz attempt isn't visible
    expect(
        page.locator("text=History Quiz")
    ).not_to_be_visible()  # Assuming "History Quiz" might be a sample title
    print("Empty history message check passed.")
