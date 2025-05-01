# src/pages/tests/test_templates.py

import pytest
import re  # Import regular expressions
from playwright.sync_api import Page, expect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone  # Import timezone
from multi_choice_quiz.models import Quiz, QuizAttempt  # Import models

# --- Constants ---
# Use environment variable set by the runner script, or default for local debugging
BASE_URL = "http://localhost:8000"


# --- Helper Function to Create User ---
# (Extracted for reusability)
def create_test_user(username, password, is_staff=True, is_superuser=True):
    User = get_user_model()
    try:
        user, created = User.objects.get_or_create(username=username)
        if created or not user.has_usable_password():
            user.set_password(password)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            print(f"Ensured user '{username}' exists and has password.")
        else:
            # Ensure password is set if user already exists and is unusable
            if not user.has_usable_password():
                user.set_password(password)
                user.save()
                print(f"Set password for existing user: {username}")
            else:
                print(f"Using existing user: {username}")
        return user
    except Exception as e:
        pytest.fail(f"Failed to get or create test user '{username}': {e}")


# --- Helper Function to Log In via Admin ---
# (Extracted for reusability)
def login_via_admin(page: Page, username, password):
    admin_login_url = BASE_URL + "/admin/login/"
    page.goto(admin_login_url)
    page.locator("#id_username").fill(username)
    page.locator("#id_password").fill(password)
    page.get_by_role("button", name="Log in").click()
    # Wait for admin dashboard element
    expect(page.locator("#user-tools")).to_be_visible(timeout=10000)
    print(f"Successfully logged in as {username} via /admin/")


# --- Test Cases ---


def test_home_page_loads_and_title(page: Page):
    """Verify the home page loads and has the correct title."""
    home_url = BASE_URL + reverse("pages:home")
    page.goto(home_url)
    expect(page).to_have_title(re.compile("Home | QuizMaster"))
    # Check for a key element to ensure content loaded
    expect(
        page.get_by_role("heading", name="Challenge Your Knowledge with QuizMaster")
    ).to_be_visible()


def test_anonymous_user_navigation(page: Page):
    """Verify navigation links shown for an anonymous user."""
    home_url = BASE_URL + reverse("pages:home")
    page.goto(home_url)

    # Get the header element for context (helps avoid finding links elsewhere)
    header = page.locator("header")

    # Check visible links/buttons for anonymous users
    # Using get_by_role is generally preferred
    expect(header.get_by_role("link", name="Login")).to_be_visible()
    expect(header.get_by_role("link", name="Sign Up")).to_be_visible()

    # Check hidden links/buttons for anonymous users
    # Use regex for Profile link to avoid issues with username potentially appearing later
    expect(header.get_by_role("link", name=re.compile("Profile"))).not_to_be_visible()
    # The logout button is inside a form
    expect(header.get_by_role("button", name="Logout")).not_to_be_visible()


@pytest.mark.django_db(transaction=True)  # Needed to ensure User exists
def test_authenticated_user_navigation(page: Page):
    """Verify navigation links shown for an authenticated user."""
    # --- Log in User via Admin ---
    username = "testuser_nav"
    password = "password123"
    create_test_user(username, password)  # Use helper
    login_via_admin(page, username, password)  # Use helper

    # --- Navigate to Homepage after login ---
    home_url = BASE_URL + reverse("pages:home")
    page.goto(home_url)
    print(f"Navigated to homepage: {home_url}")  # Debugging

    # --- Verify Navigation Links ---
    header = page.locator("header")

    # Check hidden links/buttons for authenticated users
    expect(header.get_by_role("link", name="Login")).not_to_be_visible()
    expect(header.get_by_role("link", name="Sign Up")).not_to_be_visible()

    # Check visible links/buttons for authenticated users
    # Use regex for Profile link to account for username
    expect(
        header.get_by_role("link", name=re.compile(f"Profile \\({username}\\)"))
    ).to_be_visible()
    # Check the Logout button (inside its form)
    expect(header.get_by_role("button", name="Logout")).to_be_visible()


def test_about_page_loads(page: Page):
    """Verify the about page loads."""
    about_url = BASE_URL + reverse("pages:about")
    page.goto(about_url)
    expect(page).to_have_title(re.compile("About | QuizMaster"))
    expect(page.get_by_role("heading", name="About QuizMaster")).to_be_visible()


def test_quizzes_page_loads(page: Page):
    """Verify the quizzes page loads."""
    quizzes_url = BASE_URL + reverse("pages:quizzes")
    page.goto(quizzes_url)
    expect(page).to_have_title(re.compile("Quizzes | QuizMaster"))
    expect(page.get_by_role("heading", name="Browse Quizzes")).to_be_visible()


def test_login_page_loads(page: Page):
    """Verify the placeholder login page loads."""
    login_url = BASE_URL + reverse("pages:login")
    page.goto(login_url)
    expect(page).to_have_title(re.compile("Login | QuizMaster"))
    expect(page.get_by_role("heading", name="Login to Your Account")).to_be_visible()
    # Check for the non-functional notice
    expect(page.locator("text=Note: This is a placeholder page")).to_be_visible()


def test_signup_page_loads(page: Page):
    """Verify the placeholder signup page loads."""
    signup_url = BASE_URL + reverse("pages:signup")
    page.goto(signup_url)
    expect(page).to_have_title(re.compile("Sign Up | QuizMaster"))
    expect(page.get_by_role("heading", name="Create Your Account")).to_be_visible()
    # Check for the non-functional notice
    expect(page.locator("text=Note: This is a placeholder page")).to_be_visible()


@pytest.mark.django_db(transaction=True)
def test_profile_page_structure_when_authenticated(
    page: Page,
):  # Renamed from loads_when_authenticated
    """Verify the basic profile page structure loads when logged in."""
    # --- Login User ---
    username = "testuser_prof_struct"
    password = "password123"
    user = create_test_user(username, password)  # Use helper
    login_via_admin(page, username, password)  # Use helper

    # --- Navigate directly to profile page ---
    profile_url = BASE_URL + reverse("pages:profile")
    page.goto(profile_url)

    # --- Verify Profile Page Structure ---
    expect(page).to_have_url(profile_url)  # Ensure no redirect happened
    expect(page).to_have_title(
        re.compile(f"{username}'s Profile | QuizMaster")
    )  # Check dynamic title

    # Check for dynamic user info elements

    # --- START FIX for Avatar Check ---
    # Locate the avatar div using a more stable selector (e.g., class combination)
    # We use a class that's likely unique to the avatar container
    avatar_div = page.locator(
        "div.rounded-full.flex.items-center.justify-center.bg-accent-primary"
    )
    # Check if this div is visible
    expect(avatar_div).to_be_visible()
    # Assert the text content *of this specific div* is the correct initial
    expect(avatar_div).to_have_text(username[0].upper())
    # --- END FIX for Avatar Check ---

    # Check for username/full name heading (this locator should be okay)
    expect(page.get_by_role("heading", name=re.compile(username))).to_be_visible()
    # Check for member since (just check text exists)
    expect(page.locator("text=Member since:")).to_be_visible()

    # Check for the main history section heading
    expect(page.get_by_role("heading", name="Your Quiz History")).to_be_visible()

    # Check for the placeholder notice at the bottom
    expect(
        page.locator(
            "text=Note: Edit Profile, Stats, Favorites, and Created Quizzes are currently placeholders."
        )
    ).to_be_visible()


@pytest.mark.django_db(transaction=True)
def test_profile_page_shows_empty_history(page: Page):
    """Verify the 'no attempts' message shows for a user with no history."""
    # --- Login User (ensure this user has no attempts) ---
    username = "testuser_empty_hist"
    password = "password123"
    # Create user but DO NOT create attempts for them
    user = create_test_user(username, password)
    login_via_admin(page, username, password)  # Use helper

    # --- Navigate directly to profile page ---
    profile_url = BASE_URL + reverse("pages:profile")
    page.goto(profile_url)

    # --- Verify Empty History Message ---
    expect(page.get_by_role("heading", name="Your Quiz History")).to_be_visible()
    # Check specifically for the empty message text
    expect(page.locator("text=You haven't completed any quizzes yet.")).to_be_visible()
    # Check for the link within the empty message
    expect(page.get_by_role("link", name="Find a quiz to take!")).to_be_visible()
