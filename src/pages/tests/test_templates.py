# src/pages/tests/test_templates.py (Modifications shown)

import pytest
import os
import time
from datetime import datetime
from django.conf import settings
from playwright.sync_api import expect, Page

# Import standardized logging setup
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging with app-specific name
logger = setup_test_logging(__name__, "pages")

# Skip the test if SERVER_URL is not defined in the environment
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")


@pytest.mark.usefixtures(
    "capture_console_errors", "django_server"
)  # Use fixtures from src/conftest.py
def test_home_page_template(page: Page, django_server):
    """Test that the home page loads with the new template."""
    try:
        # Navigate to the home page
        logger.info(f"Navigating to home page: {django_server}")
        page.goto(django_server)

        # Check if the page loads
        page.wait_for_selector(
            "text=Challenge Your Knowledge with QuizMaster", timeout=5000
        )

        # Verify key elements using the new color scheme (MORE SPECIFIC LOCATORS)
        # Target the H1 specifically for the main title
        expect(page.locator("h1.text-accent-heading")).to_be_visible()
        # Target the specific "Browse Quizzes" button
        expect(
            page.locator("a.bg-accent-primary:has-text('Browse Quizzes')")
        ).to_be_visible()

        # Take a screenshot for reference
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", "pages")
        os.makedirs(app_log_dir, exist_ok=True)
        screenshot_path = os.path.join(app_log_dir, "home_page.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Home page screenshot saved to: {screenshot_path}")

        logger.info("Home page test completed successfully")

    except Exception as e:
        # (Error handling remains the same)
        app_name = "pages"
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
        os.makedirs(app_log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_home_{timestamp}.png"  # Renamed for clarity
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            if "page" in locals() and hasattr(page, "screenshot"):
                page.screenshot(path=screenshot_path)
                logger.error(f"Screenshot saved to: {screenshot_path}")
            else:
                logger.error(
                    "Could not save screenshot: 'page' object not available or invalid."
                )
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")
        if "logger" in locals() and hasattr(logger, "error"):
            logger.error(f"Test failed: {str(e)}", exc_info=True)
        else:
            print(f"Test failed (logger not available): {str(e)}")
        raise


@pytest.mark.usefixtures("capture_console_errors", "django_server")
def test_quizzes_page_template(page: Page, django_server):
    """Test that the quizzes page loads with the new template."""
    try:
        # Navigate to the quizzes page
        quizzes_url = f"{django_server}/quizzes/"
        logger.info(f"Navigating to quizzes page: {quizzes_url}")
        page.goto(quizzes_url)

        # Check if the page loads
        page.wait_for_selector("text=Browse Quizzes", timeout=5000)

        # Verify quiz cards with the new design
        quiz_cards = page.locator(".grid .bg-surface").count()
        logger.info(f"Found {quiz_cards} quiz cards")
        # Ensure at least one card is found if data exists
        if quiz_cards > 0:
            expect(page.locator(".grid .bg-surface").first).to_be_visible()

        # Verify color scheme elements (MORE SPECIFIC LOCATOR)
        # Check the 'All' filter button specifically
        expect(page.locator("a.bg-tag-bg:has-text('All')")).to_be_visible()
        # Or check one of the topic spans within a card
        if quiz_cards > 0:
            expect(page.locator(".grid .bg-surface .bg-tag-bg").first).to_be_visible()

        # Take a screenshot for reference
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", "pages")
        os.makedirs(app_log_dir, exist_ok=True)
        screenshot_path = os.path.join(app_log_dir, "quizzes_page.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Quizzes page screenshot saved to: {screenshot_path}")

        logger.info("Quizzes page test completed successfully")

    except Exception as e:
        # (Error handling remains the same)
        app_name = "pages"
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
        os.makedirs(app_log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_quizzes_{timestamp}.png"  # Renamed
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            if "page" in locals() and hasattr(page, "screenshot"):
                page.screenshot(path=screenshot_path)
                logger.error(f"Screenshot saved to: {screenshot_path}")
            else:
                logger.error(
                    "Could not save screenshot: 'page' object not available or invalid."
                )
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")
        if "logger" in locals() and hasattr(logger, "error"):
            logger.error(f"Test failed: {str(e)}", exc_info=True)
        else:
            print(f"Test failed (logger not available): {str(e)}")
        raise


@pytest.mark.usefixtures("capture_console_errors", "django_server")
def test_about_page_template(page: Page, django_server):
    """Test that the about page loads with the new template."""
    try:
        # Navigate to the about page
        about_url = f"{django_server}/about/"
        logger.info(f"Navigating to about page: {about_url}")
        page.goto(about_url)

        # Check if the page loads
        page.wait_for_selector("text=About QuizMaster", timeout=5000)

        # Verify key content sections (MORE SPECIFIC LOCATORS)
        expect(page.locator("h2:has-text('Our Mission')")).to_be_visible()
        expect(page.locator("h2:has-text('Our Story')")).to_be_visible()
        # Target the heading specifically
        expect(page.locator("h2:has-text('Contact Us')")).to_be_visible()

        # Take a screenshot for reference
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", "pages")
        os.makedirs(app_log_dir, exist_ok=True)
        screenshot_path = os.path.join(app_log_dir, "about_page.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"About page screenshot saved to: {screenshot_path}")

        logger.info("About page test completed successfully")

    except Exception as e:
        # (Error handling remains the same)
        app_name = "pages"
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
        os.makedirs(app_log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_about_{timestamp}.png"  # Renamed
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            if "page" in locals() and hasattr(page, "screenshot"):
                page.screenshot(path=screenshot_path)
                logger.error(f"Screenshot saved to: {screenshot_path}")
            else:
                logger.error(
                    "Could not save screenshot: 'page' object not available or invalid."
                )
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")
        if "logger" in locals() and hasattr(logger, "error"):
            logger.error(f"Test failed: {str(e)}", exc_info=True)
        else:
            print(f"Test failed (logger not available): {str(e)}")
        raise


# ... (rest of the tests: login, signup, profile - should be okay as they passed) ...


@pytest.mark.usefixtures("capture_console_errors", "django_server")
def test_login_page_template(page: Page, django_server):
    """Test that the login page loads with the new template."""
    try:
        # Navigate to the login page
        login_url = f"{django_server}/login/"
        logger.info(f"Navigating to login page: {login_url}")
        page.goto(login_url)

        # Check if the page loads
        page.wait_for_selector("text=Login to Your Account", timeout=5000)

        # Verify form fields
        expect(page.locator("input#email")).to_be_visible()
        expect(page.locator("input#password")).to_be_visible()
        expect(page.locator("button:has-text('Login')")).to_be_visible()

        # Verify notice banner
        expect(page.locator("text=This is a placeholder page")).to_be_visible()

        # Take a screenshot for reference
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", "pages")
        os.makedirs(app_log_dir, exist_ok=True)
        screenshot_path = os.path.join(app_log_dir, "login_page.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Login page screenshot saved to: {screenshot_path}")

        logger.info("Login page test completed successfully")

    except Exception as e:
        # (Error handling remains the same)
        app_name = "pages"
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
        os.makedirs(app_log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_login_{timestamp}.png"  # Renamed
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            if "page" in locals() and hasattr(page, "screenshot"):
                page.screenshot(path=screenshot_path)
                logger.error(f"Screenshot saved to: {screenshot_path}")
            else:
                logger.error(
                    "Could not save screenshot: 'page' object not available or invalid."
                )
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")
        if "logger" in locals() and hasattr(logger, "error"):
            logger.error(f"Test failed: {str(e)}", exc_info=True)
        else:
            print(f"Test failed (logger not available): {str(e)}")
        raise


@pytest.mark.usefixtures("capture_console_errors", "django_server")
def test_signup_page_template(page: Page, django_server):
    """Test that the signup page loads with the new template."""
    try:
        # Navigate to the signup page
        signup_url = f"{django_server}/signup/"
        logger.info(f"Navigating to signup page: {signup_url}")
        page.goto(signup_url)

        # Check if the page loads
        page.wait_for_selector("text=Create Your Account", timeout=5000)

        # Verify form fields
        expect(page.locator("input#name")).to_be_visible()
        expect(page.locator("input#email")).to_be_visible()
        expect(page.locator("input#password")).to_be_visible()
        expect(page.locator("input#confirm-password")).to_be_visible()
        expect(page.locator("button:has-text('Create Account')")).to_be_visible()

        # Verify notice banner
        expect(page.locator("text=This is a placeholder page")).to_be_visible()

        # Take a screenshot for reference
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", "pages")
        os.makedirs(app_log_dir, exist_ok=True)
        screenshot_path = os.path.join(app_log_dir, "signup_page.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Signup page screenshot saved to: {screenshot_path}")

        logger.info("Signup page test completed successfully")

    except Exception as e:
        # (Error handling remains the same)
        app_name = "pages"
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
        os.makedirs(app_log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_signup_{timestamp}.png"  # Renamed
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            if "page" in locals() and hasattr(page, "screenshot"):
                page.screenshot(path=screenshot_path)
                logger.error(f"Screenshot saved to: {screenshot_path}")
            else:
                logger.error(
                    "Could not save screenshot: 'page' object not available or invalid."
                )
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")
        if "logger" in locals() and hasattr(logger, "error"):
            logger.error(f"Test failed: {str(e)}", exc_info=True)
        else:
            print(f"Test failed (logger not available): {str(e)}")
        raise


@pytest.mark.usefixtures("capture_console_errors", "django_server")
def test_profile_page_template(page: Page, django_server):
    """Test that the profile page loads with the new template."""
    try:
        # Navigate to the profile page
        profile_url = f"{django_server}/profile/"
        logger.info(f"Navigating to profile page: {profile_url}")
        page.goto(profile_url)

        # Check if the page loads
        page.wait_for_selector("text=John Doe", timeout=5000)

        # Verify key profile sections
        expect(
            page.locator(".w-24.h-24.bg-accent-primary")
        ).to_be_visible()  # Profile avatar
        expect(page.locator("text=Quizzes Taken")).to_be_visible()

        # Check tabs functionality
        page.locator("button:has-text('Favorites')").click()
        expect(page.locator("text=Your Favorite Quizzes")).to_be_visible()

        page.locator("button:has-text('Created Quizzes')").click()
        expect(page.locator("text=Quizzes You've Created")).to_be_visible()

        # Take a screenshot for reference
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", "pages")
        os.makedirs(app_log_dir, exist_ok=True)
        screenshot_path = os.path.join(app_log_dir, "profile_page.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Profile page screenshot saved to: {screenshot_path}")

        logger.info("Profile page test completed successfully")

    except Exception as e:
        # (Error handling remains the same)
        app_name = "pages"
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
        os.makedirs(app_log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_profile_{timestamp}.png"  # Renamed
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            if "page" in locals() and hasattr(page, "screenshot"):
                page.screenshot(path=screenshot_path)
                logger.error(f"Screenshot saved to: {screenshot_path}")
            else:
                logger.error(
                    "Could not save screenshot: 'page' object not available or invalid."
                )
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")
        if "logger" in locals() and hasattr(logger, "error"):
            logger.error(f"Test failed: {str(e)}", exc_info=True)
        else:
            print(f"Test failed (logger not available): {str(e)}")
        raise


if __name__ == "__main__":
    print("This test should be run with pytest")
