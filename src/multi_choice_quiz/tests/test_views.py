"""
Tests for the Django Quiz App views.
Tests the full flow of the quiz application served by Django.
"""

import pytest
from playwright.sync_api import Page, expect, Error
import os
import sys

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set environment variable to allow Django database operations in async context
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# --- Setup Logging ---
logger = setup_test_logging("test_views")


# --- Test Function ---
@pytest.mark.usefixtures("capture_console_errors")
def test_django_quiz_flow(page: Page, django_server):
    """
    Tests the full flow of the quiz application served by Django.
    """
    # Construct the quiz URL
    quiz_url = django_server

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
        logger.exception(f"FATAL: Failed to load page or find initial element.")
        pytest.fail(
            f"Setup failed: Could not load page or find initial element. Error: {e}"
        )
        return

    # Define locators once for reuse
    question_text_locator = page.locator(".question-text")
    progress_indicator_locator = page.locator(".progress-indicator")
    modal_overlay = page.locator(".modal-overlay")
    modal_button = modal_overlay.locator(".modal-button")

    # --- Check that the quiz has loaded properly ---
    logger.info("--- Checking quiz structure ---")
    try:
        # Verify that question text and progress indicators are visible
        expect(question_text_locator).to_be_visible()
        expect(progress_indicator_locator).to_be_visible()

        # Verify question text is not empty
        expect(question_text_locator).not_to_have_text("")

        # Check that progress indicator has the format "1/X"
        progress_text = progress_indicator_locator.text_content()
        logger.info(f"Progress indicator text: {progress_text}")
        assert "/" in progress_text, "Progress indicator doesn't have expected format"

        # Capture the total number of questions for later validation
        total_questions = int(progress_text.split("/")[1])
        logger.info(f"Total questions in quiz: {total_questions}")

        # Verify we have multiple option buttons
        options = page.locator(".option-button")
        option_count = options.count()
        logger.info(f"Found {option_count} options for the first question")
        assert option_count >= 2, "Expected at least 2 options per question"

    except Error as e:
        logger.exception("Failed to verify quiz structure")
        pytest.fail(f"Quiz structure verification failed: {e}")
        return

    # --- Test answering all questions ---
    logger.info("--- Testing full quiz flow ---")

    # Keep track of correct answers for score verification
    correct_answers = 0

    # For each question in the quiz
    for q_num in range(1, total_questions + 1):
        current_question = question_text_locator.text_content()
        logger.info(f"Question {q_num}: {current_question}")

        # Verify we're on the expected question number
        expect(progress_indicator_locator).to_have_text(f"{q_num}/{total_questions}")

        # Click the first option
        options = page.locator(".option-button")
        first_option = options.nth(0)
        option_text = first_option.text_content()
        logger.info(f"Selecting option: {option_text}")
        first_option.click()

        # Wait for feedback modal
        expect(modal_overlay).to_be_visible(timeout=3000)

        # Check if our answer was correct - using synchronous evaluate
        modal_container_class = page.evaluate(
            'document.querySelector(".modal-container").className'
        )
        is_correct = "modal-correct" in modal_container_class
        if is_correct:
            logger.info("Answer was correct!")
            correct_answers += 1
        else:
            logger.info("Answer was incorrect")

        # Click continue
        modal_button.click()
        expect(modal_overlay).to_be_hidden()

        # If not the last question, verify we moved to the next question
        if q_num < total_questions:
            # Wait for next question to load
            page.wait_for_timeout(500)  # Small delay for Alpine.js transitions

            # Verify the question text changed
            new_question = question_text_locator.text_content()
            logger.info(f"Next question: {new_question}")
            assert (
                new_question != current_question
            ), "Question did not change after continuing"

    # --- Results Screen ---
    logger.info("--- Testing Results Screen ---")
    try:
        results_card = page.locator(".results-card")
        logger.info("Waiting for results card to become visible...")
        expect(results_card).to_be_visible(timeout=5000)
        logger.info("Results card is visible.")

        # Verify quiz elements are hidden
        expect(page.locator(".question-card")).to_be_hidden()
        expect(page.locator(".options-container")).to_be_hidden()

        # Verify results title
        expect(results_card.locator(".results-title")).to_have_text("Quiz Completed!")

        # Verify score display format
        score_text = results_card.locator(".results-score").text_content()
        logger.info(f"Final score: {score_text}")
        assert (
            f"{correct_answers}" in score_text
        ), "Score doesn't match expected answers"
        assert f"{total_questions}" in score_text, "Total questions count mismatch"

        # Verify restart button is available
        restart_button = results_card.locator(".restart-button")
        expect(restart_button).to_be_visible()
        expect(restart_button).to_have_text("Play Again?")

    except Error as e:
        logger.exception("Assertion failed during Results Screen check.")
        pytest.fail(f"Test failed during Results Screen check. Error: {e}")

    # --- Test Restart ---
    logger.info("--- Testing Restart ---")
    try:
        logger.info("Clicking 'Play Again?' button...")
        restart_button = page.locator(".restart-button")
        restart_button.click()

        logger.info("Verifying quiz resets to first question...")
        expect(page.locator(".results-card")).to_be_hidden()
        expect(page.locator(".question-card")).to_be_visible(timeout=5000)
        expect(progress_indicator_locator).to_have_text(f"1/{total_questions}")

        # Verify options are enabled after restart
        first_option_after_restart = page.locator(".option-button").nth(0)
        expect(first_option_after_restart).to_be_enabled()

    except Error as e:
        logger.exception("Assertion failed during Restart check.")
        pytest.fail(f"Test failed during Restart check. Error: {e}")

    logger.info("--- Django Quiz Test Completed Successfully! ---")
