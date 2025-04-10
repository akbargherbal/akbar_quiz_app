# src/multi_choice_quiz/tests/test_quiz_e2e.py

from playwright.sync_api import sync_playwright, expect
import pytest
import os
import sys
import time
from django.conf import settings

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging
logger = setup_test_logging("playwright_tests")

# Skip the test if SERVER_URL is not defined in the environment
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")


@pytest.mark.skipif(
    not os.environ.get("RUN_E2E_TESTS"), reason="Set RUN_E2E_TESTS=1 to run E2E tests"
)
def test_quiz_loads_and_functions():
    """Test that the quiz loads and basic functionality works."""
    logger.info(f"Starting E2E test against server: {SERVER_URL}")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)  # Set to True for CI/production
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            # Define the correct URL for the quiz app's entry point
            quiz_app_url = f"{SERVER_URL}/quiz/"

            # Navigate to the quiz app page
            logger.info(f"Navigating to quiz app URL: {quiz_app_url}")
            page.goto(quiz_app_url)  # Use the specific quiz app URL

            # Check if the quiz loads
            logger.info("Checking if quiz loads")
            page.wait_for_selector(".quiz-container", state="visible", timeout=5000)
            assert page.is_visible(".quiz-container"), "Quiz container not visible"

            # Check if question is displayed
            assert page.is_visible(".question-text"), "Question text not visible"

            # Check if options are displayed
            option_count = page.locator(".option-button").count()
            logger.info(f"Found {option_count} options")
            assert option_count > 0, "No options found for the question"

            # Click the first option
            logger.info("Selecting the first option")
            page.locator(".option-button").first.click()

            # Wait for feedback (correct option highlighting or incorrect selection) to appear
            logger.info("Waiting for visual feedback")
            # Either the correct answer should be visible or incorrect selection
            page.wait_for_selector(
                ".option-button.correct-answer, .option-button.incorrect-answer",
                state="visible",
                timeout=3000,
            )

            # Verify feedback is visible
            assert page.is_visible(".option-button.correct-answer") or page.is_visible(
                ".option-button.incorrect-answer"
            ), "Visual feedback not shown after selecting an option"

            # Wait for auto-progression
            logger.info("Waiting for automatic progression...")
            page.wait_for_timeout(2500)  # Slightly longer than feedbackDuration

            # Verify auto-progression (check for new options being enabled)
            # This assumes we've progressed to a new question where options should be clickable
            assert page.locator(
                ".option-button"
            ).first.is_enabled(), "Options not enabled after auto-progression"

            # Log success
            logger.info("E2E test completed successfully")

        except Exception as e:
            # Define the app-specific log directory for screenshots
            app_log_dir = os.path.join(settings.BASE_DIR, "logs", "multi_choice_quiz")

            # Create the app-specific directory if it doesn't exist
            os.makedirs(
                app_log_dir, exist_ok=True
            )  # Use exist_ok=True to avoid error if it already exists

            # Define the full path for the screenshot within the app directory
            screenshot_path = os.path.join(
                app_log_dir, "test_failure.png"
            )  # Changed path

            # Take a screenshot on failure using the new path
            page.screenshot(path=screenshot_path)

            logger.error(f"Test failed: {str(e)}")
            logger.error(f"Screenshot saved to: {screenshot_path}")  # Log the path
            raise
        finally:
            # Clean up
            context.close()
            browser.close()


if __name__ == "__main__":
    # Allow running directly (not through pytest)
    os.environ["RUN_E2E_TESTS"] = "1"
    test_quiz_loads_and_functions()
