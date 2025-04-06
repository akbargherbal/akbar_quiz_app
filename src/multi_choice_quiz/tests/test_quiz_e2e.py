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
            # Navigate to the quiz page
            logger.info("Navigating to homepage")
            page.goto(SERVER_URL)

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

            # Wait for the modal to appear
            logger.info("Waiting for feedback modal to appear")
            page.wait_for_selector(".modal-container", state="visible", timeout=5000)

            # Check if feedback modal appears
            logger.info("Checking for feedback modal")
            assert page.is_visible(
                ".modal-container"
            ), "Feedback modal not shown after selecting an option"

            # Get the continue button and click it
            logger.info("Clicking continue button")
            continue_button = page.locator(".modal-button")
            # Ensure the button is visible and enabled
            continue_button.wait_for(state="visible", timeout=3000)
            # Click the button
            continue_button.click()

            # Wait for the modal to disappear with a longer timeout
            logger.info("Waiting for modal to disappear")
            page.wait_for_selector(".modal-container", state="hidden", timeout=5000)

            # Double-check that the modal is really gone
            assert not page.is_visible(
                ".modal-container"
            ), "Feedback modal still visible after clicking continue"

            # Log success
            logger.info("E2E test completed successfully")

        except Exception as e:
            # Take a screenshot on failure
            if not os.path.exists("logs"):
                os.makedirs("logs")
            page.screenshot(path="logs/test_failure.png")
            logger.error(f"Test failed: {str(e)}")
            raise
        finally:
            # Clean up
            context.close()
            browser.close()


if __name__ == "__main__":
    # Allow running directly (not through pytest)
    os.environ["RUN_E2E_TESTS"] = "1"
    test_quiz_loads_and_functions()
