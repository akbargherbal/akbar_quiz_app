# src/multi_choice_quiz/tests/test_quiz_e2e.py (Refactored with Data Creation and re import)

from playwright.sync_api import Page, expect
import pytest
import os
import re  # <<< ADD THIS IMPORT >>>
from django.conf import settings
from django.urls import reverse
from datetime import datetime
from multi_choice_quiz.models import Quiz, Question, Option, Topic

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging for this specific app/test file
logger = setup_test_logging(__name__, "multi_choice_quiz")


@pytest.mark.usefixtures("capture_console_errors")
@pytest.mark.django_db  # Ensures DB access for ORM calls and live_server
def test_quiz_loads_and_functions(page: Page, live_server):
    """Test that the quiz loads and basic functionality works using live_server."""
    app_name = "multi_choice_quiz"
    # --- NEW: Define Screenshot Dir Consistently ---
    E2E_SCREENSHOT_DIR = (
        settings.SCREENSHOTS_DIR / app_name / "e2e_quiz_test"
    )  # Specific sub-folder
    E2E_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"E2E Quiz screenshots will be saved under: {E2E_SCREENSHOT_DIR}")
    # --- END NEW ---

    # --- START: Create Test Data ---
    logger.info("Creating necessary test data (Quiz ID 1)...")
    try:
        topic, _ = Topic.objects.get_or_create(name="E2E Test Topic")
        quiz1, created = Quiz.objects.update_or_create(
            id=1, defaults={"title": "E2E Test Quiz 1", "is_active": True}
        )
        if created:
            quiz1.topics.add(topic)

        q1, _ = Question.objects.update_or_create(
            quiz=quiz1,
            position=1,
            defaults={"text": "E2E Question 1?", "is_active": True},
        )
        Option.objects.update_or_create(
            question=q1, position=1, defaults={"text": "E2E Opt 1", "is_correct": True}
        )
        Option.objects.update_or_create(
            question=q1, position=2, defaults={"text": "E2E Opt 2", "is_correct": False}
        )

        q2, _ = Question.objects.update_or_create(
            quiz=quiz1,
            position=2,
            defaults={"text": "E2E Question 2?", "is_active": True},
        )
        Option.objects.update_or_create(
            question=q2, position=1, defaults={"text": "E2E Opt 3", "is_correct": False}
        )
        Option.objects.update_or_create(
            question=q2, position=2, defaults={"text": "E2E Opt 4", "is_correct": True}
        )

        logger.info(f"Test data created/ensured for Quiz ID: {quiz1.id}")
    except Exception as e:
        logger.error(f"Failed to create test data: {e}")
        pytest.fail(f"Test data creation failed: {e}")
        return
    # --- END: Create Test Data ---

    try:
        quiz_app_url = f"{live_server.url}{reverse('multi_choice_quiz:quiz_detail', args=[quiz1.id])}"  # Use quiz1.id
        logger.info(f"Starting E2E test against live server: {live_server.url}")
        logger.info(f"Target quiz URL: {quiz_app_url}")
    except Exception as e:
        logger.error(f"Failed to reverse URL for quiz {quiz1.id}: {e}")
        pytest.fail("Could not construct quiz URL. Check URL names.")
        return

    try:
        logger.info(f"Navigating to quiz app URL: {quiz_app_url}")
        page.goto(quiz_app_url, wait_until="domcontentloaded")

        screenshot_path = E2E_SCREENSHOT_DIR / "initial_page_load_quiz_e2e.png"  # NEW
        page.screenshot(path=screenshot_path)
        logger.info(f"Initial page screenshot saved to: {screenshot_path}")

        logger.info("Checking if quiz loads using #quiz-app-container")
        quiz_container_locator = page.locator("#quiz-app-container")
        expect(quiz_container_locator).to_be_visible(timeout=10000)
        logger.info("Quiz container (#quiz-app-container) is visible.")

        question_text_locator = page.locator("#question-text")
        expect(question_text_locator).to_be_visible(timeout=5000)
        logger.info("Question text element is visible.")

        option_buttons_locator = page.locator(".option-button")
        option_count = option_buttons_locator.count()
        logger.info(f"Found {option_count} options")
        assert option_count > 0, f"Expected more than 0 options, found {option_count}"
        logger.info("Assertion passed: Option count is greater than 0.")

        logger.info("Selecting the first option")
        first_option = option_buttons_locator.first
        expect(first_option).to_be_enabled(timeout=5000)
        first_option.click()

        logger.info("Waiting for visual feedback")
        feedback_selector = ".option-button[class*='!bg-green-500'], .option-button[class*='!bg-red-500']"
        feedback_element = page.locator(feedback_selector).first
        expect(feedback_element).to_be_visible(timeout=5000)
        logger.info("Feedback visual state detected.")

        total_questions = 0
        try:
            progress_indicator_locator = page.locator(
                "#status-bar div[x-text*='currentQuestionIndex + 1']"
            )
            expect(progress_indicator_locator).to_be_visible(timeout=5000)
            progress_text = progress_indicator_locator.text_content(timeout=5000)
            # <<< FIX: Correct the regex to remove the space after / >>>
            total_questions_match = re.search(
                r"/(\d+)", progress_text
            )  # No space after /
            if not total_questions_match:
                # Raise the error correctly including the text we tried to parse
                raise ValueError(
                    f"Could not parse total questions from indicator text: '{progress_text}' using regex r'/(\\d+)'"
                )
            total_questions = int(total_questions_match.group(1))
            logger.info(f"Determined total questions: {total_questions}")
            if total_questions <= 0:
                pytest.fail("Invalid question count determined (must be > 0).")
        except Exception as e:
            logger.error(f"Could not determine question count: {e}")
            pytest.fail(
                f"Failed to determine question count: {e}"
            )  # Include exception in fail message
            return  # Keep linters happy

        progression_wait_timeout = 7000
        logger.info(
            f"Waiting up to {progression_wait_timeout}ms for automatic progression..."
        )

        if total_questions > 1:
            expect(progress_indicator_locator).to_have_text(
                f"2/{total_questions}", timeout=progression_wait_timeout
            )
            logger.info("Progressed to question 2.")
            expect(option_buttons_locator.first).to_be_enabled(timeout=5000)
            logger.info("First option is enabled, confirming progression.")
        else:
            results_card_locator = page.locator("#quiz-results-panel")
            expect(results_card_locator).to_be_visible(timeout=progression_wait_timeout)
            logger.info("Single question quiz, results panel appeared.")

        logger.info("Quiz load and initial interaction test completed successfully")

    except Exception as e:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_quiz_e2e_{timestamp}.png"
        screenshot_path = E2E_SCREENSHOT_DIR / screenshot_filename  # NEW
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(f"Test failed: {str(e)}", exc_info=True)
        pytest.fail(f"Test failed: {str(e)}")
