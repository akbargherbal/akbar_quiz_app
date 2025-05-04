# src/multi_choice_quiz/tests/test_database_quiz.py (REVISED Locator for Progress)

import pytest
import os
import sys
import time
import socket
import json
import signal
import subprocess
from playwright.sync_api import Page, expect, Error as PlaywrightError
from django.core.management import call_command
from django.conf import settings
from datetime import datetime

# Import our standardized logging setup
from multi_choice_quiz.tests.test_logging import setup_test_logging

# --- Constants ---
DJANGO_SERVER_PORT = 8000
DJANGO_SERVER_HOST = "localhost"
DJANGO_SERVER_URL = f"http://{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}"

# Define current_dir before any functions
current_dir = os.path.dirname(os.path.abspath(__file__))


# --- Setup Logging ---
logger = setup_test_logging("test_database_quiz", "multi_choice_quiz")


# --- Tests ---
@pytest.mark.usefixtures("capture_console_errors")  # Use fixture from conftest.py
def test_database_quiz_flow(page: Page, django_server):
    """
    Test that the quiz loads data from the database correctly, matching app_old.js logic.
    Verify the transformation from database format to frontend format works.
    """
    # Define the app name for logging/screenshots
    app_name = "multi_choice_quiz"
    app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
    os.makedirs(app_log_dir, exist_ok=True)

    # Constants from app_old.js for waits
    INCORRECT_FEEDBACK_DURATION_MS = 6000
    # Add a buffer to account for script execution time
    WAIT_BUFFER_MS = 1000
    PROGRESSION_WAIT_TIMEOUT = (
        INCORRECT_FEEDBACK_DURATION_MS + WAIT_BUFFER_MS
    )  # Max wait time after click

    quiz_url = django_server + "/quiz/1/"  # Try loading quiz 1 explicitly

    logger.info(f"Starting database quiz test (for app_old.js). Loading: {quiz_url}")
    try:
        # Go to the page
        page.goto(quiz_url, wait_until="domcontentloaded")
        logger.info(f"Page navigation to {quiz_url} attempted.")

        # Wait for Alpine.js to initialize (check container and first option)
        logger.info("Waiting for quiz container and first option button...")
        quiz_container_locator = page.locator("#quiz-app-container")
        first_option_button_locator = quiz_container_locator.locator(
            ".option-button"
        ).first

        expect(quiz_container_locator).to_be_visible(timeout=10000)
        expect(first_option_button_locator).to_be_visible(timeout=10000)
        logger.info("Quiz container and first option are visible.")

        # Optionally wait for window.quizAppInstance (if needed for complex checks later)
        # page.wait_for_function("() => window.quizAppInstance !== undefined && window.quizAppInstance !== null", timeout=5000)
        # logger.info("window.quizAppInstance is available.")

        # --- Get JSON data ---
        json_data = page.evaluate(
            "() => { try { return JSON.parse(document.getElementById('quiz-data').textContent); } catch(e) { return null; } }"
        )

        if not json_data:
            logger.error("No valid quiz data JSON found embedded in the page.")
            pytest.fail("Quiz data JSON is empty or missing.")
            return

        logger.info(f"Quiz data loaded: {len(json_data)} questions")
        total_questions = len(json_data)
        if total_questions == 0:
            pytest.fail("Test cannot proceed with 0 questions loaded.")

        # Get locators for reused elements (use IDs where available)
        question_text_locator = page.locator("#question-text")
        # <<< FIX: Correct locator for the question counter div >>>
        # Target the div within #status-bar that has the specific x-text attribute structure
        progress_indicator_locator = page.locator(
            "#status-bar div[x-text*='currentQuestionIndex + 1']"
        )
        # <<< END FIX >>>
        results_card_locator = page.locator("#quiz-results-panel")  # Use ID

        # --- Verify first question display ---
        expect(question_text_locator).to_be_visible(timeout=5000)
        expect(progress_indicator_locator).to_have_text(
            f"1/{total_questions}", timeout=5000
        )
        logger.info(f"Verified display for question 1/{total_questions}")  # Added log

        # --- Interact with the first question ---
        logger.info("Answering question 1...")
        first_option = page.locator(".option-button").first  # Re-locate to be safe
        expect(first_option).to_be_enabled(timeout=5000)
        first_option.click()
        logger.info("Clicked first option for question 1.")

        # --- Wait for progression based on app_old.js timer ---
        logger.info(
            f"Waiting up to {PROGRESSION_WAIT_TIMEOUT}ms for progression to Q2 or results..."
        )
        if total_questions > 1:
            # Wait for the progress indicator to update to the next question number
            expect(
                progress_indicator_locator, "Progress indicator should update to Q2"
            ).to_have_text(f"2/{total_questions}", timeout=PROGRESSION_WAIT_TIMEOUT)
            page.wait_for_timeout(100)  # Small pause for UI sync after indicator change
            logger.info("Progress indicator updated to 2. Progressed to next question.")
        else:
            # If only one question, wait for the results card
            expect(
                results_card_locator, "Results panel should appear after Q1"
            ).to_be_visible(timeout=PROGRESSION_WAIT_TIMEOUT)
            logger.info("Single question quiz. Results panel appeared.")

        # --- Complete the rest of the quiz ---
        if total_questions > 1:
            logger.info("Completing the rest of the quiz...")
            for i in range(
                1, total_questions
            ):  # Start from the second question (index 1)
                q_num = i + 1  # Current question number (2, 3, ...)
                logger.info(f"Answering question {q_num}/{total_questions}")

                # --- Wait for current question elements to be ready ---
                # Progress indicator check already happened for Q2, check for Q3 onwards
                # <<< FIX: Ensure we check the *correct* indicator >>>
                expect(
                    progress_indicator_locator,
                    f"Progress indicator should show {q_num}",
                ).to_have_text(
                    f"{q_num}/{total_questions}",
                    timeout=7000,  # Standard wait for element state
                )
                # <<< END FIX >>>

                expect(
                    question_text_locator,
                    f"Question text for Q{q_num} should be visible",
                ).to_be_visible(timeout=5000)
                # Ensure options for the current question are enabled
                current_options = page.locator(".option-button")
                expect(
                    current_options.first,
                    f"First option for Q{q_num} should be enabled",
                ).to_be_enabled(timeout=5000)
                logger.info(f"Elements for Q{q_num} are ready.")

                # --- Click the first option ---
                option_to_click = current_options.first
                option_to_click.click()
                logger.info(f"Clicked first option for Q{q_num}.")

                # --- Wait for progression ---
                logger.info(
                    f"Waiting up to {PROGRESSION_WAIT_TIMEOUT}ms for progression after Q{q_num}..."
                )
                if q_num < total_questions:
                    # Wait for the next question number to appear in the indicator
                    next_q_num = q_num + 1
                    # <<< FIX: Ensure we check the *correct* indicator >>>
                    expect(
                        progress_indicator_locator,
                        f"Progress indicator should update to Q{next_q_num}",
                    ).to_have_text(
                        f"{next_q_num}/{total_questions}",
                        timeout=PROGRESSION_WAIT_TIMEOUT,
                    )
                    # <<< END FIX >>>
                    page.wait_for_timeout(100)  # Small pause for UI sync
                    logger.info(f"Progressed to question {next_q_num}.")
                else:
                    # This is the last question, wait for the results card
                    expect(
                        results_card_locator,
                        "Results panel should appear after last question",
                    ).to_be_visible(timeout=PROGRESSION_WAIT_TIMEOUT)
                    logger.info("Last question answered. Results panel appeared.")

        # --- Test the results screen ---
        logger.info("Checking results screen content...")
        expect(results_card_locator, "Results panel should be visible").to_be_visible(
            timeout=5000
        )  # Already waited, quick check

        # Verify results title and score (using relative locators within the results card)
        expect(
            results_card_locator.locator('h3:text("Quiz Results")'),
            "Results title check",
        ).to_be_visible()
        # Find span containing score fraction (e.g., "1 / 3", "2 / 3")
        score_span = results_card_locator.locator(
            "span.text-gray-200", has_text=f"/ {total_questions}"
        )
        expect(score_span, "Score display check").to_be_visible()
        expect(score_span).to_contain_text(f"/ {total_questions}")

        # Verify the restart button works
        restart_button = results_card_locator.locator('button:text("Play Again")')
        expect(restart_button, "Restart button check").to_be_visible()
        expect(restart_button, "Restart button enabled check").to_be_enabled()
        restart_button.click()
        logger.info("Clicked restart button.")

        # --- Verify quiz restart ---
        logger.info("Verifying quiz restart...")
        # Wait for results card to disappear
        expect(results_card_locator, "Results panel hidden after restart").to_be_hidden(
            timeout=5000
        )
        # Wait for first question elements to reappear
        expect(
            question_text_locator, "Question text visible after restart"
        ).to_be_visible(timeout=5000)
        # <<< FIX: Ensure we check the *correct* indicator >>>
        expect(
            progress_indicator_locator, "Progress indicator reset check"
        ).to_have_text(f"1/{total_questions}", timeout=5000)
        # <<< END FIX >>>
        # Check if first option is enabled again
        expect(
            page.locator(".option-button").first, "First option enabled after restart"
        ).to_be_enabled(timeout=5000)
        logger.info("Quiz successfully restarted.")

        logger.info("Database quiz test (for app_old.js) completed successfully!")

    except (PlaywrightError, Exception) as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_db_quiz_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(f"Test failed: {str(e)}", exc_info=True)
        pytest.fail(f"Test failed: {str(e)}")
