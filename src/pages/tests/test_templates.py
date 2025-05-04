# src/pages/tests/test_templates.py (Refactored to use live_server)

import pytest
import re
import os
from playwright.sync_api import Page, expect
from django.urls import reverse
from django.contrib.auth import get_user_model
# from django.test import Client as DjangoClient # Keep if setup_logged_in_user is used
# from django.contrib.staticfiles.testing import StaticLiveServerTestCase # Not needed

User = get_user_model()

# <<< CHANGE >>> Remove BASE_URL definition and related os import
# BASE_URL = os.environ.get("SERVER_URL", "http://localhost:8000")

# --- Keep LOG_DIR if needed for other purposes, but it's not used in this snippet ---
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "pages")
os.makedirs(LOG_DIR, exist_ok=True)

# Define standard viewports
DESKTOP_VIEWPORT = {"width": 1280, "height": 720}
MOBILE_VIEWPORT = {"width": 375, "height": 667}  # Example: iPhone SE size

# --- Keep helper function if needed, but it uses DjangoClient, not Playwright directly ---
# Note: This helper is mostly for backend state setup before Playwright interaction.
# It works correctly with @pytest.mark.django_db.
# Consider converting to a pytest fixture for better integration if desired later.
# from django.test import Client as DjangoClient
# def setup_logged_in_user(username, password):
#     """Ensures user exists and returns logged-in Django Client."""
#     try:
#         user = User.objects.get(username=username)
#         print(f"User '{username}' already exists.")
#     except User.DoesNotExist:
#         user = User.objects.create_user(username=username, password=password)
#         print(f"Created user '{username}'.")
#     if not user.has_usable_password():
#         user.set_password(password)
#         user.save()
#         print(f"Ensured user '{username}' exists and has password.")

#     django_client = DjangoClient()
#     logged_in = django_client.login(username=username, password=password)
#     if not logged_in:
#         print(
#             f"ERROR: Django Client login failed for user '{username}'. Check credentials/backend."
#         )
#         pytest.fail(f"Setup failed: Could not log in Django client as '{username}'")
#     print(f"Successfully logged in Django client as {username}.")
#     return django_client

# --- Tests ---

# <<< CHANGE >>> Add live_server fixture to signature
def test_home_page_loads_and_title(page: Page, live_server):
    """Verify the home page loads and has the correct title."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    # <<< CHANGE >>> Use live_server.url
    home_url = f"{live_server.url}{reverse('pages:home')}"
    page.goto(home_url)
    expect(page).to_have_title(re.compile("Home | QuizMaster"))
    expect(page.get_by_role("heading", name="Challenge Your Knowledge")).to_be_visible()


# <<< CHANGE >>> Add live_server fixture to signature
def test_quizzes_page_loads(page: Page, live_server):
    """Verify the quizzes page loads."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    # <<< CHANGE >>> Use live_server.url
    quizzes_url = f"{live_server.url}{reverse('pages:quizzes')}"
    page.goto(quizzes_url)
    expect(page).to_have_title(re.compile("Quizzes | QuizMaster"))
    expect(page.get_by_role("heading", name="Browse Quizzes")).to_be_visible()


# <<< CHANGE >>> Add live_server fixture to signature
def test_about_page_loads(page: Page, live_server):
    """Verify the about page loads."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    # <<< CHANGE >>> Use live_server.url
    about_url = f"{live_server.url}{reverse('pages:about')}"
    page.goto(about_url)
    expect(page).to_have_title(re.compile("About | QuizMaster"))
    expect(page.get_by_role("heading", name="About QuizMaster")).to_be_visible()


# --- Navigation Tests ---

# <<< CHANGE >>> Add live_server fixture to signature
def test_anonymous_user_navigation(page: Page, live_server):
    """Verify navigation links for anonymous users."""
    # --- Desktop checks ---
    print("\n--- Running Anonymous Desktop Nav Checks ---")
    page.set_viewport_size(DESKTOP_VIEWPORT)
    # <<< CHANGE >>> Use live_server.url
    home_url = f"{live_server.url}{reverse('pages:home')}"
    page.goto(home_url)
    page.wait_for_load_state("networkidle")

    desktop_nav = page.locator("nav.hidden.md\\:flex")
    expect(desktop_nav).to_be_visible()
    expect(desktop_nav.get_by_role("link", name="Login")).to_be_visible()
    expect(desktop_nav.get_by_role("link", name="Login")).to_have_attribute(
        "href", reverse("login") # href attribute doesn't need full URL
    )
    expect(desktop_nav.get_by_role("link", name="Sign Up")).to_be_visible()
    expect(desktop_nav.get_by_role("link", name="Sign Up")).to_have_attribute(
        "href", reverse("pages:signup") # href attribute doesn't need full URL
    )
    expect(
        desktop_nav.get_by_role("link", name="Profile", exact=True)
    ).not_to_be_visible()
    expect(desktop_nav.get_by_role("button", name="Logout")).not_to_be_visible()
    print("Desktop checks passed.")

    # --- Mobile checks ---
    print("--- Running Anonymous Mobile Nav Checks ---")
    page.set_viewport_size(MOBILE_VIEWPORT)
    # <<< CHANGE >>> Use live_server.url (reload page)
    page.goto(home_url)
    page.wait_for_load_state("networkidle")

    mobile_menu_button = page.locator("div.md\\:hidden > button")
    expect(mobile_menu_button).to_be_visible(timeout=5000)
    print("Mobile menu button found and is visible.")
    mobile_menu_button.click()
    print("Clicked mobile menu button.")

    mobile_nav = page.locator("nav[x-show='open']")
    expect(mobile_nav).to_be_visible(timeout=2000)
    print("Mobile nav dropdown is visible.")

    expect(mobile_nav.get_by_role("link", name="Login")).to_be_visible()
    expect(mobile_nav.get_by_role("link", name="Login")).to_have_attribute(
        "href", reverse("login") # href attribute doesn't need full URL
    )
    expect(mobile_nav.get_by_role("link", name="Sign Up")).to_be_visible()
    expect(mobile_nav.get_by_role("link", name="Sign Up")).to_have_attribute(
        "href", reverse("pages:signup") # href attribute doesn't need full URL
    )
    expect(
        mobile_nav.get_by_role("link", name="Profile", exact=True)
    ).not_to_be_visible()
    expect(mobile_nav.get_by_role("button", name="Logout")).not_to_be_visible()
    print("Mobile checks passed.")


@pytest.mark.django_db
# <<< CHANGE >>> Add live_server fixture to signature
def test_authenticated_user_navigation(page: Page, live_server):
    """Verify navigation links for authenticated users."""
    admin_user = "testuser_nav"
    admin_pass = "password123"
    try:
        user = User.objects.get(username=admin_user)
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
    # <<< CHANGE >>> Use live_server.url
    admin_login_url = f"{live_server.url}{reverse('admin:index')}"
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

    # --- Desktop checks ---
    print("--- Running Authenticated Desktop Nav Checks ---")
    page.set_viewport_size(DESKTOP_VIEWPORT)
    # <<< CHANGE >>> Use live_server.url
    home_url = f"{live_server.url}{reverse('pages:home')}"
    page.goto(home_url)
    page.wait_for_load_state("networkidle")
    print(f"Navigated to homepage: {home_url}")

    desktop_nav = page.locator("nav.hidden.md\\:flex")
    expect(desktop_nav).to_be_visible()
    profile_link_desktop = desktop_nav.get_by_role(
        "link", name=re.compile(f"Profile \\({admin_user}\\)")
    )
    expect(profile_link_desktop).to_be_visible()
    expect(profile_link_desktop).to_have_attribute(
        "href", reverse("pages:profile") # href attribute doesn't need full URL
    )

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
    # <<< CHANGE >>> Use live_server.url (reload)
    page.goto(home_url)
    page.wait_for_load_state("networkidle")

    mobile_menu_button = page.locator("div.md\\:hidden > button")
    expect(mobile_menu_button).to_be_visible(timeout=5000)
    print("Mobile menu button found and is visible.")
    mobile_menu_button.click()
    print("Clicked mobile menu button.")

    mobile_nav = page.locator("nav[x-show='open']")
    expect(mobile_nav).to_be_visible(timeout=2000)
    print("Mobile nav dropdown is visible.")

    profile_link_mobile = mobile_nav.get_by_role(
        "link", name=re.compile(f"Profile \\({admin_user}\\)")
    )
    expect(profile_link_mobile).to_be_visible()
    expect(profile_link_mobile).to_have_attribute(
        "href", reverse("pages:profile") # href attribute doesn't need full URL
    )

    logout_button_mobile = mobile_nav.locator(
        "form[action*='logout'] > button:has-text('Logout')"
    )
    expect(logout_button_mobile).to_be_visible()

    expect(mobile_nav.get_by_role("link", name="Login")).not_to_be_visible()
    expect(mobile_nav.get_by_role("link", name="Sign Up")).not_to_be_visible()
    print("Mobile checks passed.")


# --- Remaining tests ---

# <<< CHANGE >>> Add live_server fixture to signature
def test_login_page_loads(page: Page, live_server):
    """Verify the standard Django login page loads."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    # <<< CHANGE >>> Use live_server.url
    login_url = f"{live_server.url}{reverse('login')}" # Note: Uses built-in 'login' name
    page.goto(login_url)
    # Check title based on registration/login.html template
    expect(page).to_have_title(re.compile("Login | QuizMaster"))
    # Check heading based on registration/login.html template
    expect(page.get_by_role("heading", name="Login to Your Account")).to_be_visible()
    expect(page.locator('input[name="username"]')).to_be_visible() # Use name attribute
    expect(page.locator('input[name="password"]')).to_be_visible() # Use name attribute


# <<< CHANGE >>> Add live_server fixture to signature
def test_signup_page_loads(page: Page, live_server):
    """Verify the signup page loads correctly (without placeholder text)."""
    page.set_viewport_size(DESKTOP_VIEWPORT)
    # <<< CHANGE >>> Use live_server.url
    signup_url = f"{live_server.url}{reverse('pages:signup')}"
    page.goto(signup_url)
    expect(page).to_have_title(re.compile("Sign Up | QuizMaster"))
    expect(page.get_by_role("heading", name="Create Your Account")).to_be_visible()
    # Using name attributes which are standard for the SignUpForm
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="email"]')).to_be_visible()
    expect(page.locator('input[name="password1"]')).to_be_visible()
    expect(page.locator('input[name="password2"]')).to_be_visible()
    expect(
        page.locator('button[type="submit"]:has-text("Create Account")')
    ).to_be_visible()


@pytest.mark.django_db
# <<< CHANGE >>> Add live_server fixture to signature
def test_profile_page_structure_when_authenticated(page: Page, live_server):
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

    # <<< CHANGE >>> Use live_server.url
    admin_login_url = f"{live_server.url}{reverse('admin:index')}"
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

    # <<< CHANGE >>> Use live_server.url
    profile_url = f"{live_server.url}{reverse('pages:profile')}"
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(profile_url)
    page.wait_for_load_state("networkidle")

    expect(page).to_have_title(re.compile(f"{admin_user}'s Profile | QuizMaster"))
    expect(
        page.locator(f'h1:has-text("{admin_user}")')
    ).to_be_visible()
    expect(page.get_by_role("button", name="Quiz History")).to_be_visible()
    expect(page.get_by_role("button", name="Favorites")).to_be_visible()
    expect(
        page.locator(f'div:has-text("{admin_user[0].upper()}")').first
    ).to_be_visible()
    print("Profile page structure checks passed.")


@pytest.mark.django_db
# <<< CHANGE >>> Add live_server fixture to signature
def test_profile_page_shows_empty_history(page: Page, live_server):
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

    # <<< CHANGE >>> Use live_server.url
    admin_login_url = f"{live_server.url}{reverse('admin:index')}"
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

    # <<< CHANGE >>> Use live_server.url
    profile_url = f"{live_server.url}{reverse('pages:profile')}"
    page.set_viewport_size(DESKTOP_VIEWPORT)
    page.goto(profile_url)
    page.wait_for_load_state("networkidle")

    history_tab_content = page.locator("div[x-show=\"activeTab === 'history'\"]")
    expect(
        history_tab_content.locator("text=You haven't completed any quizzes yet.")
    ).to_be_visible()
    expect(
        page.locator("text=History Quiz") # Check for example attempt text
    ).not_to_be_visible()
    print("Empty history message check passed.")