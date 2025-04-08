# src/multi_choice_quiz/tests/test_quiz_new_ui.py

from playwright.sync_api import sync_playwright, expect
import pytest
import os
import time
from django.conf import settings

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging
logger = setup_test_logging("playwright_new_ui")

# Skip the test if SERVER_URL is not defined in the environment
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")


@pytest.mark.skipif(
    not os.environ.get("RUN_E2E_TESTS"), reason="Set RUN_E2E_TESTS=1 to run E2E tests"
)
def test_new_quiz_ui_functionality():
    """Test that the new quiz UI functions correctly with direct feedback."""
    logger.info(f"Starting new UI E2E test against server: {SERVER_URL}")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)  # Set to False for debugging
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            # Navigate to the quiz page
            logger.info("Navigating to homepage")
            page.goto(SERVER_URL)

            # Check if the quiz loads
            logger.info("Checking if quiz loads with new UI")
            page.wait_for_selector(".quiz-container", state="visible", timeout=5000)
            assert page.is_visible(".quiz-container"), "Quiz container not visible"

            # Verify the progress bar is visible
            logger.info("Checking progress bar")
            assert page.is_visible(
                ".progress-bar-container"
            ), "Progress bar not visible"
            assert page.is_visible(
                ".progress-bar-fill"
            ), "Progress bar fill not visible"

            # Check if question is displayed
            assert page.is_visible(".question-text"), "Question text not visible"
            assert page.is_visible(
                ".question-container"
            ), "Question container not visible"

            # Check if options are displayed
            option_count = page.locator(".option-button").count()
            logger.info(f"Found {option_count} options")
            assert option_count > 0, "No options found for the question"

            # Record the current question text
            current_question = page.locator(".question-text").text_content()
            logger.info(f"Current question: {current_question}")

            # Click the first option
            logger.info("Selecting the first option")
            first_option = page.locator(".option-button").first
            first_option.click()

            # Check immediate feedback: verify correct option is highlighted
            logger.info("Checking direct visual feedback on options")

            # Wait for option classes to update (should be immediate but give it a moment)
            page.wait_for_timeout(100)

            # Check if correct answer is highlighted with the 'correct-answer' class
            # (This may be the first option or another option depending on the question)
            correct_option = page.locator(".option-button.correct-answer")
            assert correct_option.is_visible(), "Correct option not highlighted"

            # Check if incorrect options either disappear or show as incorrect
            # depending on which one was selected
            disappearing_options = page.locator(".option-button.disappear")
            incorrect_selection = page.locator(".option-button.incorrect-answer")

            # Either some options should disappear or the selected option should be marked incorrect
            # (depending on whether the user selected correctly)
            assert (
                disappearing_options.count() > 0 or incorrect_selection.is_visible()
            ), "Neither disappearing options nor incorrect selection is visible"

            # Wait for the automatic progression (slightly longer than feedbackDuration)
            logger.info("Waiting for automatic progression to next question")
            page.wait_for_timeout(2500)  # Default feedbackDuration is 2000ms

            # Verify we've moved to the next question
            new_question = page.locator(".question-text").text_content()
            logger.info(f"New question: {new_question}")
            assert (
                new_question != current_question
            ), "Question did not change after automatic progression"

            # Continue the quiz by selecting the first option on each question until completed
            logger.info("Continuing through quiz until completion")

            # Click through the remaining questions
            while page.is_visible(".question-text") and not page.is_visible(
                ".results-card"
            ):
                current_question = page.locator(".question-text").text_content()
                logger.info(f"Current question: {current_question}")

                # Click the first option
                if page.locator(".option-button").first.is_visible():
                    page.locator(".option-button").first.click()
                    # Wait for automatic progression
                    page.wait_for_timeout(2500)

            # Verify we reached the results screen
            logger.info("Checking results screen")
            assert page.is_visible(
                ".results-card"
            ), "Results card not visible after completing quiz"
            assert page.is_visible(".results-title"), "Results title not visible"
            assert page.is_visible(".results-score"), "Results score not visible"

            # Check for restart button and click it
            logger.info("Testing restart button")
            restart_button = page.locator(".restart-button")
            assert restart_button.is_visible(), "Restart button not visible"
            restart_button.click()

            # Verify we're back at the beginning
            page.wait_for_timeout(500)  # Brief wait for restart to complete
            assert page.is_visible(
                ".question-text"
            ), "Question not visible after restart"
            assert not page.is_visible(
                ".results-card"
            ), "Results still visible after restart"

            # Verify progress reset
            progress_indicator = page.locator(".progress-indicator").text_content()
            assert (
                "1/" in progress_indicator
            ), "Progress indicator not reset to first question"

            logger.info("E2E test for new UI completed successfully")

        except Exception as e:
            # Take a screenshot on failure
            if not os.path.exists("logs"):
                os.makedirs("logs")
            page.screenshot(path="logs/new_ui_test_failure.png")
            logger.error(f"Test failed: {str(e)}")
            raise
        finally:
            # Clean up
            context.close()
            browser.close()


if __name__ == "__main__":
    # Allow running directly (not through pytest)
    os.environ["RUN_E2E_TESTS"] = "1"
    test_new_quiz_ui_functionality()
