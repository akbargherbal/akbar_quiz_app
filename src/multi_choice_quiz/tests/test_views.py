"""
Tests for the Django Quiz App views using Playwright.
Covers loading quizzes (default and specific ID) and basic UI interaction.
"""

import pytest
from playwright.sync_api import Page, expect, Error
import os
import sys
from django.conf import settings  # Import settings
from datetime import datetime  # Import datetime

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set environment variable to allow Django database operations in async context
# This is often needed for tests involving database access triggered by views.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# --- Setup Logging ---
# Pass app_name to the logging setup
logger = setup_test_logging("test_views", "multi_choice_quiz")


# --- Test Function ---
@pytest.mark.usefixtures(
    "capture_console_errors", "django_server"
)  # Use fixtures from conftest
def test_django_quiz_flow(page: Page):
    """
    Tests the full flow of the quiz application served by Django views.
    Loads the default quiz, answers questions, checks results, and restarts.
    """
    # Define the app name for logging/screenshots
    app_name = "multi_choice_quiz"
    app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
    os.makedirs(app_log_dir, exist_ok=True)

    # Construct the default quiz URL (should map to the home view which loads a quiz)
    quiz_url = (
        os.environ.get("SERVER_URL", "http://localhost:8000") + "/quiz/"
    )  # Use /quiz/ path

    logger.info(f"Starting Django quiz flow test. Loading: {quiz_url}")
    try:
        # Go to the page, wait for the load event
        page.goto(quiz_url, wait_until="domcontentloaded")
        logger.info(f"Page navigation to {quiz_url} attempted.")

        # Wait for Alpine.js to initialize and render quiz components
        logger.info(
            "Waiting for the first option button to become visible (max 10s)..."
        )
        first_option_button_selector = ".option-button >> nth=0"
        page.wait_for_selector(
            first_option_button_selector, state="visible", timeout=10000
        )
        logger.info("First option button is visible. Quiz has loaded successfully.")

    except Error as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_view_load_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(
            f"FATAL: Failed to load page or find initial element.", exc_info=True
        )
        pytest.fail(
            f"Setup failed: Could not load page or find initial element. Error: {e}"
        )
        return

    # Define locators once for reuse
    question_text_locator = page.locator(".question-text")
    progress_indicator_locator = page.locator(".progress-indicator")
    options_locator = page.locator(".option-button")
    results_card_locator = page.locator(".results-card")
    restart_button_locator = page.locator(".restart-button")
    feedback_selector = ".option-button.correct-answer, .option-button.incorrect-answer"

    # --- Check initial quiz structure ---
    logger.info("--- Checking initial quiz structure ---")
    try:
        expect(question_text_locator).to_be_visible()
        expect(progress_indicator_locator).to_be_visible()
        expect(question_text_locator).not_to_have_text("")

        progress_text = progress_indicator_locator.text_content()
        logger.info(f"Progress indicator text: {progress_text}")
        assert "/" in progress_text, "Progress indicator missing expected format 'N/M'"
        expect(progress_text).to_match(r"^\d+/\d+$")  # Regex check for N/M format

        total_questions = int(progress_text.split("/")[1])
        logger.info(f"Total questions in quiz: {total_questions}")
        assert total_questions > 0, "Quiz must have at least one question"

        option_count = options_locator.count()
        logger.info(f"Found {option_count} options for the first question")
        expect(option_count).to_be_greater_than_or_equal(2)

    except (Error, AssertionError) as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_view_structure_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error("Failed to verify initial quiz structure", exc_info=True)
        pytest.fail(f"Quiz structure verification failed: {e}")
        return

    # --- Answer all questions ---
    logger.info("--- Testing full quiz flow (answering questions) ---")
    try:
        for q_num in range(1, total_questions + 1):
            current_question = question_text_locator.text_content()
            logger.info(
                f"Answering Question {q_num}/{total_questions}: {current_question[:50]}..."
            )

            # Verify progress indicator
            expect(progress_indicator_locator).to_have_text(
                f"{q_num}/{total_questions}", timeout=5000
            )
            expect(options_locator.first).to_be_enabled(
                timeout=5000
            )  # Wait for options to be ready

            # Click the first option
            first_option = options_locator.first
            option_text = first_option.text_content()
            logger.info(f"Selecting option: {option_text[:50]}...")
            first_option.click()

            # Wait for visual feedback
            page.wait_for_selector(
                feedback_selector, state="visible", timeout=5000
            )  # Increased timeout
            logger.info(f"Feedback shown for Question {q_num}")

            # Wait for auto-progression (or results screen if last question)
            logger.info(f"Waiting for progression after Question {q_num}...")
            page.wait_for_timeout(4500)  # Wait slightly longer than feedback

            # Check state after progression
            if q_num < total_questions:
                logger.info(f"Checking progression to Question {q_num + 1}")
                expect(progress_indicator_locator).to_have_text(
                    f"{q_num + 1}/{total_questions}", timeout=5000
                )
            else:
                logger.info("Last question answered, checking for results screen")
                expect(results_card_locator).to_be_visible(
                    timeout=10000
                )  # Longer timeout for results

    except (Error, AssertionError) as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_view_answering_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(
            f"Failed during quiz answering flow (Question {q_num})", exc_info=True
        )
        pytest.fail(f"Test failed during answering flow. Error: {e}")
        return

    # --- Results Screen ---
    logger.info("--- Testing Results Screen ---")
    try:
        expect(results_card_locator).to_be_visible()
        logger.info("Results card is visible.")

        # Verify quiz elements are hidden
        expect(page.locator(".question-card")).to_be_hidden()
        expect(page.locator(".options-container")).to_be_hidden()

        # Verify title and score format
        expect(results_card_locator.locator(".results-title")).to_have_text(
            "Quiz Completed!"
        )
        expect(results_card_locator.locator(".results-score")).to_contain_text(
            "Your Score:"
        )
        expect(results_card_locator.locator(".results-score")).to_contain_text(
            f"out of {total_questions}"
        )

        # Verify restart button
        expect(restart_button_locator).to_be_visible()
        expect(restart_button_locator).to_have_text("Play Again?")

    except (Error, AssertionError) as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_view_results_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error("Assertion failed during Results Screen check.", exc_info=True)
        pytest.fail(f"Test failed during Results Screen check. Error: {e}")

    # --- Test Restart ---
    logger.info("--- Testing Restart ---")
    try:
        logger.info("Clicking 'Play Again?' button...")
        restart_button_locator.click()

        logger.info("Verifying quiz resets to first question...")
        expect(results_card_locator).to_be_hidden(
            timeout=5000
        )  # Wait for results to hide
        expect(page.locator(".question-card")).to_be_visible(timeout=5000)
        expect(progress_indicator_locator).to_have_text(
            f"1/{total_questions}", timeout=5000
        )

        # Verify options are enabled after restart
        expect(options_locator.first).to_be_enabled(timeout=5000)

    except (Error, AssertionError) as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_view_restart_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error("Assertion failed during Restart check.", exc_info=True)
        pytest.fail(f"Test failed during Restart check. Error: {e}")

    logger.info("--- Django Quiz View Test Completed Successfully! ---")


@pytest.mark.usefixtures("capture_console_errors", "django_server")
def test_specific_quiz_view(page: Page):
    """Tests loading a specific quiz using the quiz_detail view."""
    # Define the app name for logging/screenshots
    app_name = "multi_choice_quiz"
    app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
    os.makedirs(app_log_dir, exist_ok=True)

    # Assuming quiz ID 1 exists from sample data
    quiz_id = 1
    specific_quiz_url = (
        f"{os.environ.get('SERVER_URL', 'http://localhost:8000')}/quiz/{quiz_id}/"
    )

    logger.info(f"--- Testing specific quiz view (ID: {quiz_id}) ---")
    logger.info(f"Navigating to: {specific_quiz_url}")

    try:
        page.goto(specific_quiz_url, wait_until="domcontentloaded")
        page.wait_for_selector(".option-button", state="visible", timeout=10000)
        logger.info(f"Specific quiz page (ID: {quiz_id}) loaded successfully.")

        # Basic structure check
        expect(page.locator(".question-text")).to_be_visible()
        expect(page.locator(".progress-indicator")).to_be_visible()
        expect(page.locator(".option-button").count()).to_be_greater_than(0)

        logger.info(f"--- Specific Quiz View Test (ID: {quiz_id}) Passed! ---")

    except (Error, AssertionError) as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_view_specific_{quiz_id}_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(
            f"Failed to load or verify specific quiz view (ID: {quiz_id})",
            exc_info=True,
        )
        pytest.fail(f"Specific quiz view test failed. Error: {e}")
