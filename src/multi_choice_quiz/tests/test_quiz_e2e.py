# src/multi_choice_quiz/tests/test_quiz_e2e.py

from playwright.sync_api import Page, expect  # Import Page
import pytest
import os
import sys
import time
from django.conf import settings
from datetime import datetime  # Import datetime

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging for this specific app
logger = setup_test_logging("playwright_tests", "multi_choice_quiz")  # Pass app_name

# Skip the test if SERVER_URL is not defined in the environment
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")


@pytest.mark.skipif(
    not os.environ.get("RUN_E2E_TESTS"), reason="Set RUN_E2E_TESTS=1 to run E2E tests"
)
@pytest.mark.usefixtures(
    "capture_console_errors", "django_server"
)  # Use fixtures from conftest
def test_quiz_loads_and_functions(
    page: Page,
):  # django_server fixture is used implicitly now
    """Test that the quiz loads and basic functionality works."""
    # Define the app name for logging/screenshots
    app_name = "multi_choice_quiz"
    app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
    os.makedirs(app_log_dir, exist_ok=True)

    logger.info(f"Starting E2E test against server: {SERVER_URL}")

    try:
        # Define the correct URL for the quiz app's entry point
        quiz_app_url = f"{SERVER_URL}/quiz/"  # Use the specific quiz app URL

        # Navigate to the quiz app page
        logger.info(f"Navigating to quiz app URL: {quiz_app_url}")
        page.goto(quiz_app_url, wait_until="domcontentloaded")

        # Take a screenshot before waiting to see what's actually rendering
        screenshot_path = os.path.join(app_log_dir, "initial_page_load_e2e.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Initial page screenshot saved to: {screenshot_path}")

        # Check if the quiz loads - with increased timeout
        logger.info("Checking if quiz loads using #quiz-app-container")
        page.wait_for_selector("#quiz-app-container", state="visible", timeout=10000)
        expect(page.locator("#quiz-app-container")).to_be_visible()
        logger.info("Quiz container (#quiz-app-container) is visible.")

        # Check if question is displayed
        expect(page.locator("#question-text")).to_be_visible()
        logger.info("Question text element is visible.")

        # Check if options are displayed
        option_count = page.locator(".option-button").count()
        logger.info(f"Found {option_count} options")
        # --- CORRECTION 3: Use standard Python assert for integer check ---
        assert (
            option_count > 0
        ), f"Expected more than 0 options, but found {option_count}"
        # --- END CORRECTION 3 ---
        logger.info("Assertion passed: Option count is greater than 0.")

        # Click the first option
        logger.info("Selecting the first option")
        page.locator(".option-button").first.click()

        # Wait for feedback (correct option highlighting or incorrect selection) to appear
        logger.info("Waiting for visual feedback")
        feedback_selector = ".option-button[class*='!bg-green-500'], .option-button[class*='!bg-red-500']"
        page.wait_for_selector(
            feedback_selector,
            state="visible",
            timeout=5000,
        )
        logger.info("Feedback visual state detected.")

        # Verify feedback is visible
        expect(page.locator(feedback_selector).first).to_be_visible()

        # Wait for auto-progression
        logger.info("Waiting for automatic progression (approx 4-6 seconds)...")
        page.wait_for_timeout(6500)  # Wait slightly longer than the longest feedback

        # Verify auto-progression
        logger.info("Verifying progression by checking if first option is enabled.")
        expect(page.locator(".option-button").first).to_be_enabled(timeout=5000)
        logger.info("First option is enabled, assuming progression occurred.")

        # Log success
        logger.info("E2E test completed successfully")

    except Exception as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_e2e_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise
    # Playwright context is managed by pytest-playwright fixture, no need to close manually
