# src/multi_choice_quiz/tests/test_database_quiz.py

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
from django.urls import reverse  # <<< ADD reverse import
import re  # <<< ADD re import
from pathlib import Path  # <<< Use Path

# Import our standardized logging setup
from multi_choice_quiz.tests.test_logging import setup_test_logging

# --- Setup Logging ---
logger = setup_test_logging("test_database_quiz", "multi_choice_quiz")


# --- Test Function ---
@pytest.mark.django_db  # <<< ADD django_db marker if accessing DB directly too
@pytest.mark.usefixtures("capture_console_errors")  # Use fixture from conftest.py
def test_database_quiz_flow(page: Page, live_server):  # <<< CHANGE fixture name here
    """
    Test that the quiz loads data from the database correctly.
    Verify the transformation from database format to frontend format works.
    Simulates the quiz flow and checks results screen.
    """
    # Define the app name for logging/screenshots
    app_name = "multi_choice_quiz"

    # --- Define Screenshot Dir Consistently --- # <<< NEW
    SCREENSHOT_DIR = settings.BASE_DIR / "screenshots" / app_name
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Screenshots will be saved under: {SCREENSHOT_DIR}")
    # --- End New Screenshot Dir ---

    # --- ADD Test Data Creation --- # <<< NEW - Quiz 1 must exist in test DB
    logger.info("Creating necessary test data (Quiz ID 1)...")
    try:
        from multi_choice_quiz.models import (
            Quiz,
            Question,
            Option,
            Topic,
        )  # Import models here

        topic, _ = Topic.objects.get_or_create(name="DB Quiz Test Topic")
        quiz1, created = Quiz.objects.update_or_create(
            id=1, defaults={"title": "DB Quiz Test Quiz 1", "is_active": True}
        )
        if created:
            quiz1.topics.add(topic)
        q1, _ = Question.objects.update_or_create(
            quiz=quiz1, position=1, defaults={"text": "DBQ1?"}
        )
        Option.objects.update_or_create(
            question=q1, position=1, defaults={"text": "DBQ1 Opt1", "is_correct": True}
        )
        Option.objects.update_or_create(
            question=q1, position=2, defaults={"text": "DBQ1 Opt2"}
        )
        q2, _ = Question.objects.update_or_create(
            quiz=quiz1, position=2, defaults={"text": "DBQ2?"}
        )
        Option.objects.update_or_create(
            question=q2, position=1, defaults={"text": "DBQ2 Opt1"}
        )
        Option.objects.update_or_create(
            question=q2, position=2, defaults={"text": "DBQ2 Opt2", "is_correct": True}
        )
        logger.info(f"Test data created/ensured for Quiz ID: {quiz1.id}")
    except Exception as e:
        logger.error(f"Failed to create test data: {e}")
        pytest.fail(f"Test data creation failed: {e}")
        return
    # --- End Test Data Creation ---

    # Constants for waits
    INCORRECT_FEEDBACK_DURATION_MS = 6000
    WAIT_BUFFER_MS = 1000
    PROGRESSION_WAIT_TIMEOUT = INCORRECT_FEEDBACK_DURATION_MS + WAIT_BUFFER_MS

    quiz_url = (
        f"{live_server.url}{reverse('multi_choice_quiz:quiz_detail', args=[quiz1.id])}"
    )

    logger.info(f"Starting database quiz test. Loading: {quiz_url}")
    try:
        # Go to the page
        page.goto(quiz_url, wait_until="domcontentloaded")
        logger.info(f"Page navigation to {quiz_url} attempted.")

        # Wait for Alpine.js to initialize
        logger.info("Waiting for quiz container and first option button...")
        quiz_container_locator = page.locator("#quiz-app-container")
        first_option_button_locator = quiz_container_locator.locator(
            ".option-button"
        ).first
        expect(quiz_container_locator).to_be_visible(timeout=10000)
        expect(first_option_button_locator).to_be_visible(timeout=10000)
        logger.info("Quiz container and first option are visible.")

        # Get JSON data
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
            return

        # Get locators
        question_text_locator = page.locator("#question-text")
        progress_indicator_locator = page.locator(
            "#status-bar div[x-text*='currentQuestionIndex + 1']"
        )
        results_card_locator = page.locator("#quiz-results-panel")

        # Verify first question display
        expect(question_text_locator).to_be_visible(timeout=5000)
        expect(progress_indicator_locator).to_have_text(
            re.compile(rf"1\s*/\s*{total_questions}"), timeout=5000
        )
        logger.info(f"Verified display for question 1/{total_questions}")

        # Interact with the first question
        logger.info("Answering question 1...")
        first_option = page.locator(".option-button").first
        expect(first_option).to_be_enabled(timeout=5000)
        first_option.click()
        logger.info("Clicked first option for question 1.")

        # Wait for progression
        logger.info(
            f"Waiting up to {PROGRESSION_WAIT_TIMEOUT}ms for progression to Q2 or results..."
        )
        if total_questions > 1:
            expect(
                progress_indicator_locator, "Progress indicator should update to Q2"
            ).to_have_text(
                re.compile(rf"2\s*/\s*{total_questions}"),
                timeout=PROGRESSION_WAIT_TIMEOUT,
            )
            page.wait_for_timeout(100)
            logger.info("Progress indicator updated to 2. Progressed to next question.")
        else:
            expect(
                results_card_locator, "Results panel should appear after Q1"
            ).to_be_visible(timeout=PROGRESSION_WAIT_TIMEOUT)
            logger.info("Single question quiz. Results panel appeared.")

        # Complete the rest of the quiz
        if total_questions > 1:
            logger.info("Completing the rest of the quiz...")
            for i in range(1, total_questions):
                q_num = i + 1
                logger.info(f"Answering question {q_num}/{total_questions}")

                # Wait for elements
                expect(
                    progress_indicator_locator,
                    f"Progress indicator should show {q_num}",
                ).to_have_text(
                    re.compile(rf"{q_num}\s*/\s*{total_questions}"),
                    timeout=7000,
                )
                expect(
                    question_text_locator,
                    f"Question text for Q{q_num} should be visible",
                ).to_be_visible(timeout=5000)
                current_options = page.locator(".option-button")
                expect(
                    current_options.first,
                    f"First option for Q{q_num} should be enabled",
                ).to_be_enabled(timeout=5000)
                logger.info(f"Elements for Q{q_num} are ready.")

                # Click first option
                option_to_click = current_options.first
                option_to_click.click()
                logger.info(f"Clicked first option for Q{q_num}.")

                # Wait for progression
                logger.info(
                    f"Waiting up to {PROGRESSION_WAIT_TIMEOUT}ms for progression after Q{q_num}..."
                )
                if q_num < total_questions:
                    next_q_num = q_num + 1
                    expect(
                        progress_indicator_locator,
                        f"Progress indicator should update to Q{next_q_num}",
                    ).to_have_text(
                        re.compile(rf"{next_q_num}\s*/\s*{total_questions}"),
                        timeout=PROGRESSION_WAIT_TIMEOUT,
                    )
                    page.wait_for_timeout(100)
                    logger.info(f"Progressed to question {next_q_num}.")
                else:
                    expect(
                        results_card_locator,
                        "Results panel should appear after last question",
                    ).to_be_visible(timeout=PROGRESSION_WAIT_TIMEOUT)
                    logger.info("Last question answered. Results panel appeared.")

        # --- Test the results screen ---
        logger.info("Checking results screen content...")
        expect(results_card_locator, "Results panel should be visible").to_be_visible(
            timeout=5000
        )

        # Verify results title
        expect(
            results_card_locator.locator('h3:text("Quiz Results")'),
            "Results title check",
        ).to_be_visible()

        # --- START REVISED SCORE CHECK ---
        # Locate the specific inner span holding the total questions count via x-text
        total_questions_span = results_card_locator.locator(
            'span[x-text="questions.length"]'
        )
        expect(total_questions_span, "Total questions display check").to_be_visible(
            timeout=5000
        )
        # Check its text content matches the total
        expect(total_questions_span, "Total questions value check").to_have_text(
            str(total_questions)
        )

        # Also verify the score part is visible (we know its value is dynamic via x-text)
        score_value_span = results_card_locator.locator('span[x-text="score"]')
        expect(score_value_span, "Score value display check").to_be_visible(
            timeout=5000
        )
        # --- END REVISED SCORE CHECK ---

        # Verify the restart button works
        restart_button = results_card_locator.locator('button:text("Play Again")')
        expect(restart_button, "Restart button check").to_be_visible()
        expect(restart_button, "Restart button enabled check").to_be_enabled()
        restart_button.click()
        logger.info("Clicked restart button.")

        # --- Verify quiz restart ---
        logger.info("Verifying quiz restart...")
        expect(results_card_locator, "Results panel hidden after restart").to_be_hidden(
            timeout=5000
        )
        expect(
            question_text_locator, "Question text visible after restart"
        ).to_be_visible(timeout=5000)
        expect(
            progress_indicator_locator, "Progress indicator reset check"
        ).to_have_text(re.compile(rf"1\s*/\s*{total_questions}"), timeout=5000)
        expect(
            page.locator(".option-button").first, "First option enabled after restart"
        ).to_be_enabled(timeout=5000)
        logger.info("Quiz successfully restarted.")

        logger.info("Database quiz test completed successfully!")

    except (PlaywrightError, Exception) as e:
        # Screenshot on failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_db_quiz_{timestamp}.png"
        screenshot_path = SCREENSHOT_DIR / screenshot_filename
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(f"Test failed: {str(e)}", exc_info=True)
        pytest.fail(f"Test failed: {str(e)}")
