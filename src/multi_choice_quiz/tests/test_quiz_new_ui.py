# src/multi_choice_quiz/tests/test_quiz_new_ui.py

from playwright.sync_api import Page, expect  # Import Page
import pytest
import os
import time
from django.conf import settings
from datetime import datetime  # Import datetime

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging for this specific app
logger = setup_test_logging("playwright_new_ui", "multi_choice_quiz")  # Pass app_name

# Skip the test if SERVER_URL is not defined in the environment
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")


@pytest.mark.skipif(
    not os.environ.get("RUN_E2E_TESTS"), reason="Set RUN_E2E_TESTS=1 to run E2E tests"
)
@pytest.mark.usefixtures("capture_console_errors", "django_server")  # Use fixtures
def test_new_quiz_ui_functionality(page: Page):
    """Test that the new quiz UI functions correctly with direct feedback."""
    # Define the app name for logging/screenshots
    app_name = "multi_choice_quiz"
    app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
    os.makedirs(app_log_dir, exist_ok=True)

    logger.info(f"Starting new UI E2E test against server: {SERVER_URL}")

    try:
        # Navigate to the quiz page (use a specific one if possible, e.g., quiz 1)
        quiz_url = f"{SERVER_URL}/quiz/1/"
        logger.info(f"Navigating to quiz page: {quiz_url}")
        page.goto(quiz_url, wait_until="domcontentloaded")

        # Check if the quiz loads
        logger.info("Checking if quiz loads with new UI")
        page.wait_for_selector(".quiz-container", state="visible", timeout=10000)
        expect(page.locator(".quiz-container")).to_be_visible()

        # Verify the progress bar is visible
        logger.info("Checking progress bar")
        expect(page.locator(".progress-bar-container")).to_be_visible()
        expect(page.locator(".progress-bar-fill")).to_be_visible()

        # Check if question is displayed
        expect(page.locator(".question-text")).to_be_visible()
        expect(page.locator(".question-container")).to_be_visible()

        # Check if options are displayed
        option_count = page.locator(".option-button").count()
        logger.info(f"Found {option_count} options")
        expect(option_count).to_be_greater_than(0)

        # Get total questions from progress indicator
        progress_text = page.locator(".progress-indicator").text_content()
        total_questions = int(progress_text.split("/")[1])
        logger.info(f"Total questions: {total_questions}")

        # --- Test first question interaction ---
        current_question = page.locator(".question-text").text_content()
        logger.info(f"Current question (1/{total_questions}): {current_question}")

        # Click the first option
        logger.info("Selecting the first option")
        first_option = page.locator(".option-button").first
        first_option.click()

        # Check immediate feedback
        logger.info("Checking direct visual feedback on options")
        feedback_selector = (
            ".option-button.correct-answer, .option-button.incorrect-answer"
        )
        page.wait_for_selector(
            feedback_selector, state="visible", timeout=5000
        )  # Increased timeout
        expect(page.locator(feedback_selector)).to_be_visible()

        # Wait for the automatic progression
        logger.info("Waiting for automatic progression to next question")
        page.wait_for_timeout(4500)  # Wait slightly longer than feedback duration

        # Verify we've moved to the next question (if not the only question)
        if total_questions > 1:
            expect(page.locator(".progress-indicator")).to_have_text(
                f"2/{total_questions}", timeout=5000
            )
            new_question = page.locator(".question-text").text_content()
            logger.info(f"New question (2/{total_questions}): {new_question}")
            expect(new_question).not_to_equal(current_question)
        else:
            logger.info("Only one question in quiz, checking for results screen.")
            expect(page.locator(".results-card")).to_be_visible(timeout=5000)

        # --- Continue the quiz until completion ---
        if total_questions > 1:
            logger.info("Continuing through quiz until completion")
            for q_num in range(2, total_questions + 1):
                logger.info(f"Answering question {q_num}/{total_questions}")
                # Ensure question is ready
                expect(page.locator(".progress-indicator")).to_have_text(
                    f"{q_num}/{total_questions}", timeout=5000
                )
                expect(page.locator(".option-button").first).to_be_enabled(timeout=5000)

                # Click the first option
                page.locator(".option-button").first.click()

                # Wait for feedback and progression
                page.wait_for_selector(feedback_selector, state="visible", timeout=5000)
                page.wait_for_timeout(4500)  # Progression delay

                # Check progress or results screen
                if q_num < total_questions:
                    expect(page.locator(".progress-indicator")).to_have_text(
                        f"{q_num + 1}/{total_questions}", timeout=5000
                    )
                else:
                    logger.info("Last question answered, expecting results card.")
                    expect(page.locator(".results-card")).to_be_visible(
                        timeout=10000
                    )  # Longer timeout for results

        # Verify we reached the results screen
        logger.info("Checking results screen")
        expect(page.locator(".results-card")).to_be_visible(timeout=5000)
        expect(page.locator(".results-title")).to_have_text("Quiz Completed!")
        expect(page.locator(".results-score")).to_be_visible()

        # Check for restart button and click it
        logger.info("Testing restart button")
        restart_button = page.locator(".restart-button")
        expect(restart_button).to_be_visible()
        restart_button.click()

        # Verify we're back at the beginning
        page.wait_for_timeout(500)  # Brief wait for restart to complete
        expect(page.locator(".question-text")).to_be_visible(timeout=5000)
        expect(page.locator(".results-card")).to_be_hidden()

        # Verify progress reset
        expect(page.locator(".progress-indicator")).to_have_text(
            f"1/{total_questions}", timeout=5000
        )

        logger.info("E2E test for new UI completed successfully")

    except Exception as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_new_ui_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise
