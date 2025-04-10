import pytest
import os
import sys
import time
import socket
import json
import signal
import subprocess
from playwright.sync_api import Page, expect, Error
from django.core.management import call_command
from django.conf import settings  # Import settings
from datetime import datetime  # Import datetime

# Import our standardized logging setup
from multi_choice_quiz.tests.test_logging import setup_test_logging

# --- Constants ---
DJANGO_SERVER_PORT = 8000
DJANGO_SERVER_HOST = "localhost"
DJANGO_SERVER_URL = f"http://{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}"

# Define current_dir before any functions
current_dir = os.path.dirname(os.path.abspath(__file__))


# --- Setup Logging ---
# Pass app_name to the logging setup
logger = setup_test_logging("test_database_quiz", "multi_choice_quiz")

# Note: The django_server and capture_console_errors fixtures are now defined
# in conftest.py and will be automatically discovered by pytest.
# We remove their definitions from this file to avoid duplication.


# --- Tests ---
@pytest.mark.usefixtures("capture_console_errors")
def test_database_quiz_flow(page: Page, django_server):
    """
    Test that the quiz loads data from the database correctly.
    Verify the transformation from database format to frontend format works.
    """
    # Define the app name for logging/screenshots
    app_name = "multi_choice_quiz"
    app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
    os.makedirs(app_log_dir, exist_ok=True)

    quiz_url = django_server + "/quiz/1/"  # Try loading quiz 1 explicitly

    logger.info(f"Starting database quiz test. Loading: {quiz_url}")
    try:
        # Go to the page
        page.goto(quiz_url, wait_until="domcontentloaded")
        logger.info(f"Page navigation to {quiz_url} attempted.")

        # Wait for Alpine.js to initialize
        logger.info("Waiting for the first option button to become visible...")
        first_option_button_selector = ".option-button >> nth=0"
        page.wait_for_selector(
            first_option_button_selector, state="visible", timeout=10000
        )
        logger.info("First option button is visible. Quiz has loaded successfully.")

        # --- Test the first question ---
        question_text_locator = page.locator(".question-text")
        progress_indicator_locator = page.locator(".progress-indicator")

        # Get JSON data from the page to verify transformations
        json_data = page.evaluate(
            "() => { return JSON.parse(document.getElementById('quiz-data').textContent); }"
        )

        # Handle potential empty data scenario
        if not json_data:
            logger.error("No quiz data found embedded in the page.")
            pytest.fail("Quiz data JSON is empty or missing.")
            return

        logger.info(f"Quiz data loaded: {len(json_data)} questions")

        # Verify that the data has been transformed correctly (0-based indexing)
        first_question = json_data[0]
        logger.info(f"First question: {first_question['text']}")
        logger.info(f"Options: {first_question['options']}")
        logger.info(f"Answer index (0-based): {first_question['answerIndex']}")

        # Check that answerIndex is a number and within range
        assert isinstance(
            first_question["answerIndex"], int
        ), "answerIndex is not an integer"
        assert (
            0 <= first_question["answerIndex"] < len(first_question["options"])
        ), "answerIndex out of range"

        # Interact with the quiz to verify functionality
        # Find the correct option based on answerIndex
        correct_option_text = first_question["options"][first_question["answerIndex"]]
        logger.info(f"Correct option text: {correct_option_text}")

        # Click the correct option
        correct_option = page.locator(
            ".option-button", has_text=correct_option_text
        ).first
        correct_option.click()

        # Check that we get correct visual feedback (option glows green)
        correct_option_class = page.locator(".option-button.correct-answer")
        expect(correct_option_class).to_be_visible(timeout=3000)

        # Wait for auto-progression to next question
        logger.info("Waiting for auto-progression...")
        page.wait_for_timeout(4500)  # Increased wait time

        # --- Complete the entire quiz ---
        logger.info("Completing the rest of the quiz...")
        total_questions = len(json_data)

        for i in range(1, total_questions):
            logger.info(f"Answering question {i+1}/{total_questions}")
            # Wait for the question to be visible and options ready
            expect(question_text_locator).to_be_visible(timeout=5000)
            expect(progress_indicator_locator).to_have_text(f"{i+1}/{total_questions}")
            expect(page.locator(".option-button").first).to_be_enabled(timeout=5000)

            # Click the first option
            option = page.locator(".option-button >> nth=0")
            option.click()

            # Wait for feedback display before progression starts
            page.wait_for_selector(
                ".option-button.correct-answer, .option-button.incorrect-answer",
                state="visible",
                timeout=3000,
            )

            # Wait for auto-progression to next question or results
            page.wait_for_timeout(4500)  # Increased wait time

            # Verify progression (unless it's the last question)
            if i < total_questions - 1:
                expect(progress_indicator_locator).to_have_text(
                    f"{i+2}/{total_questions}", timeout=5000
                )
            else:
                # On last question, expect results card
                logger.info("Last question answered, expecting results card.")
                expect(page.locator(".results-card")).to_be_visible(
                    timeout=10000
                )  # Longer timeout for results

        # --- Test the results screen ---
        results_card = page.locator(".results-card")
        logger.info("Checking results screen...")
        expect(results_card).to_be_visible(timeout=5000)

        # Verify results title and score
        expect(results_card.locator(".results-title")).to_have_text("Quiz Completed!")
        expect(results_card.locator(".results-score")).to_contain_text("Your Score:")
        expect(results_card.locator(".results-score")).to_contain_text(
            f"out of {total_questions}"
        )

        # Verify the restart button works
        restart_button = results_card.locator(".restart-button")
        expect(restart_button).to_be_visible()
        restart_button.click()

        # Verify we're back on the first question
        expect(question_text_locator).to_be_visible(timeout=5000)
        expect(progress_indicator_locator).to_have_text(
            f"1/{total_questions}", timeout=5000
        )

        logger.info("Database quiz test completed successfully!")

    except (Error, Exception) as e:
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
