# src/multi_choice_quiz/tests/test_quiz_e2e.py

from playwright.sync_api import sync_playwright
import pytest
import os
import sys
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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the quiz page
            logger.info("Navigating to homepage")
            page.goto(SERVER_URL)

            # Check if the quiz loads
            logger.info("Checking if quiz loads")
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

            # Check if feedback modal appears
            logger.info("Checking for feedback modal")
            assert page.is_visible(
                ".modal-container"
            ), "Feedback modal not shown after selecting an option"

            # Click continue button
            logger.info("Clicking continue button")
            page.locator(".modal-button").click()

            # Verify modal closed
            assert not page.is_visible(
                ".modal-container"
            ), "Feedback modal still visible after clicking continue"

            # Log success
            logger.info("E2E test completed successfully")

        except Exception as e:
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
