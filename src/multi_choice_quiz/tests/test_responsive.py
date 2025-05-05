# src/multi_choice_quiz/tests/test_responsive.py # <<< CORRECT FILE PATH
import pytest
import os
import json
import logging
import uuid
from playwright.sync_api import (  # <<< Import directly
    Page,
    expect as expect_pw,  # <<< Rename expect
    Locator,
    TimeoutError as PlaywrightTimeoutError,
)
from django.conf import settings  # <<< Import settings
from django.urls import reverse  # <<< Import reverse
from pathlib import Path  # <<< Use Path

# --- Setup Logging --- # <<< Logging already setup, good
log_format = (
    "%(asctime)s - %(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s"
)
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# --- Constants ---
BREAKPOINTS = {
    "mobile": {"width": 375, "height": 667},
    "sm": {"width": 640, "height": 768},
    "md": {"width": 768, "height": 1024},
    "lg": {"width": 1024, "height": 768},
    "xl": {"width": 1280, "height": 800},
    "2xl": {"width": 1536, "height": 960},
}
# BASE_URL = "http://127.0.0.1:8000" # <<< DELETE BASE_URL
# QUIZ_URL = "/quiz/1/" # <<< DELETE QUIZ_URL

# --- Screenshot Dir Setup --- # <<< NEW Consistent Setup
APP_NAME = "multi_choice_quiz"  # <<< Define App Name
SCREENSHOT_DIR = settings.BASE_DIR / "screenshots" / APP_NAME
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"Screenshots will be saved under: {SCREENSHOT_DIR}")
# --- End Screenshot Dir Setup ---

# Timeouts (consider adjusting based on actual performance)
DEFAULT_VISIBILITY_TIMEOUT = 20000  # ms for elements to become visible initially
INSTANCE_WAIT_TIMEOUT = 10000  # ms to wait specifically for window.quizAppInstance
EVENT_WAIT_TIMEOUT = 8000  # ms
POST_EVENT_UI_TIMEOUT = 5000  # ms


# --- Helper Functions ---
def check_results_panel_visibility(page: Page, breakpoint_name: str):
    """Checks visibility of key elements within the results panel."""
    logger.info(f"Checking results panel visibility at {breakpoint_name}...")
    results_panel_locator_str = "#quiz-results-panel"
    logger.info(f"Using locator: {results_panel_locator_str}")
    results_panel = page.locator(results_panel_locator_str)

    expect_pw(
        results_panel, f"Results panel container should be visible at {breakpoint_name}"
    ).to_be_visible(timeout=POST_EVENT_UI_TIMEOUT + 3000)
    logger.info("Results panel container is visible.")

    results_heading = results_panel.locator('h3:text("Quiz Results")')
    expect_pw(
        results_heading, f"Results heading should be visible at {breakpoint_name}"
    ).to_be_visible()

    # --- Updated Locators based on template ---
    stats_container = results_panel.locator(
        "div.pb-5.border-b"
    )  # More specific container for stats
    expect_pw(
        stats_container,
        f"Stats section container should be visible at {breakpoint_name}",
    ).to_be_visible()

    expect_pw(
        stats_container.locator('span:text("Rating")'), "Rating label should be visible"
    ).to_be_visible()
    expect_pw(
        stats_container.locator('span:text("Score")'), "Score label should be visible"
    ).to_be_visible()
    expect_pw(
        stats_container.locator('span:text("Percentage")'),
        "Percentage label should be visible",
    ).to_be_visible()
    expect_pw(
        stats_container.locator('span:text("Time")'), "Time label should be visible"
    ).to_be_visible()

    mistakes_section = results_panel.locator('div:has-text("Mistakes Review")').first
    expect_pw(
        mistakes_section, f"Mistakes section should be visible at {breakpoint_name}"
    ).to_be_visible()
    mistakes_list = mistakes_section.locator(
        "ul.mistakes-review-list"
    )  # Be more specific
    expect_pw(
        mistakes_list, f"Mistakes list should be visible at {breakpoint_name}"
    ).to_be_visible()

    # --- Updated Button Locators ---
    go_home_button = results_panel.locator('a:text("Go Home")')
    expect_pw(
        go_home_button, f"Go Home button should be visible at {breakpoint_name}"
    ).to_be_visible()
    expect_pw(
        go_home_button, f"Go Home button should be enabled at {breakpoint_name}"
    ).to_be_enabled()  # Links are usually enabled if visible

    play_again_button = results_panel.locator('button:text("Play Again")')
    expect_pw(
        play_again_button, f"Play Again button should be visible at {breakpoint_name}"
    ).to_be_visible()
    expect_pw(
        play_again_button, f"Play Again button should be enabled at {breakpoint_name}"
    ).to_be_enabled()

    logger.info(f"Results panel checks passed for {breakpoint_name}.")


# --- Helper Function for Screenshots --- # <<< NEW
def get_screenshot_path(breakpoint_name: str, suffix: str = "") -> Path:
    filename = f"responsive_results_{breakpoint_name}{suffix}.png"
    return SCREENSHOT_DIR / filename


def get_html_path(breakpoint_name: str, suffix: str = "") -> Path:
    filename = f"responsive_results_{breakpoint_name}{suffix}.html"
    return SCREENSHOT_DIR / filename


# --- End Helper Function ---


# --- Test Function ---
@pytest.mark.django_db  # <<< ADD django_db marker
@pytest.mark.parametrize("name, size", BREAKPOINTS.items())
def test_results_layout_responsiveness(
    page: Page, live_server, name: str, size: dict
):  # <<< ADD live_server
    """
    Test the layout of the quiz results view across different breakpoints
    by answering questions and synchronizing with wait_for_function.
    """
    test_name = f"test_results_layout_responsiveness[{name}]"
    logger.info(
        f"--- Starting Test: {test_name} ({size['width']}x{size['height']}) ---"
    )
    page.set_viewport_size(size)

    # --- ADDED: Set up listeners for browser console/errors ---
    page.on(
        "console", lambda msg: logger.info(f"BROWSER CONSOLE [{msg.type}]: {msg.text}")
    )
    page.on("pageerror", lambda exc: logger.error(f"BROWSER PAGE ERROR: {exc}"))
    logger.info("Added browser console and page error listeners.")
    # --- END OF ADDED LISTENERS ---

    # --- ADD Test Data Creation --- # <<< NEW - Quiz 1 must exist in test DB
    logger.info("Creating necessary test data (Quiz ID 1)...")
    try:
        from multi_choice_quiz.models import (
            Quiz,
            Question,
            Option,
            Topic,
        )  # Import here

        topic, _ = Topic.objects.get_or_create(name="Responsive Test Topic")
        quiz1, created = Quiz.objects.update_or_create(
            id=1, defaults={"title": "Responsive Test Quiz 1", "is_active": True}
        )
        if created:
            quiz1.topics.add(topic)
        q1, _ = Question.objects.update_or_create(
            quiz=quiz1, position=1, defaults={"text": "Resp Q1?"}
        )
        Option.objects.update_or_create(
            question=q1, position=1, defaults={"text": "Resp Opt1", "is_correct": True}
        )
        Option.objects.update_or_create(
            question=q1, position=2, defaults={"text": "Resp Opt2"}
        )
        q2, _ = Question.objects.update_or_create(
            quiz=quiz1, position=2, defaults={"text": "Resp Q2?"}
        )
        Option.objects.update_or_create(
            question=q2, position=1, defaults={"text": "Resp Opt3"}
        )
        Option.objects.update_or_create(
            question=q2, position=2, defaults={"text": "Resp Opt4", "is_correct": True}
        )
        logger.info(f"Test data created/ensured for Quiz ID: {quiz1.id}")
    except Exception as e:
        logger.error(f"Failed to create test data: {e}")
        pytest.fail(f"Test data creation failed: {e}")
        return
    # --- End Test Data Creation ---

    # --- Use live_server.url --- # <<< NEW
    target_url = (
        f"{live_server.url}{reverse('multi_choice_quiz:quiz_detail', args=[quiz1.id])}"
    )
    logger.info(f"Target URL: {target_url}")
    # --- End URL ---

    try:
        # page.goto(f"{BASE_URL}{QUIZ_URL}") # <<< OLD
        page.goto(
            target_url, wait_until="networkidle"
        )  # <<< Use new target_url and networkidle
        logger.info(f"Navigated to {page.url}")

        # --- Wait for Quiz to Load & Alpine Instance ---
        logger.info("Waiting for Alpine component to initialize...")
        quiz_container = page.locator("#quiz-app-container")
        expect_pw(quiz_container, "Quiz container should become visible").to_be_visible(
            timeout=DEFAULT_VISIBILITY_TIMEOUT
        )
        expect_pw(
            quiz_container, "Quiz container should have x-data"
        ).to_have_attribute("x-data", "quizApp()", timeout=5000)

        try:
            logger.info(
                f"Waiting up to {INSTANCE_WAIT_TIMEOUT}ms for window.quizAppInstance..."
            )
            page.wait_for_function(
                "() => typeof window.quizAppInstance !== 'undefined' && window.quizAppInstance !== null && typeof window.quizAppInstance.init === 'function'",
                timeout=INSTANCE_WAIT_TIMEOUT,
            )
            logger.info("window.quizAppInstance is available.")
            # Also ensure TESTING_MODE is set for events to fire
            # TESTING_MODE should be set automatically in app.js init now.
            # logger.info(f"Waiting up to 2000ms for window.TESTING_MODE === true...")
            # page.wait_for_function("() => window.TESTING_MODE === true", timeout=2000)
            # logger.info("window.TESTING_MODE confirmed true.")

        except PlaywrightTimeoutError:
            logger.error(
                "Timeout waiting for window.quizAppInstance. Check app.js init."
            )
            instance_fail_path = get_screenshot_path(name, "_INSTANCE_TIMEOUT_ERROR")
            page.screenshot(path=instance_fail_path)
            pytest.fail(
                f"window.quizAppInstance did not become available. Screenshot: {instance_fail_path}"
            )
            return

        first_option = page.locator("#quiz-app-container button.option-button").first
        expect_pw(
            first_option, "First option button should render after init"
        ).to_be_visible(timeout=DEFAULT_VISIBILITY_TIMEOUT)
        expect_pw(
            first_option, "First option button should have text content"
        ).not_to_be_empty(timeout=5000)
        logger.info("Quiz component initialized and first question rendered.")

        # --- Determine Question Count (Robustly) ---
        question_count = 0
        logger.info("Attempting to determine question count...")
        try:
            # Prefer Alpine state
            count = page.evaluate("() => window.quizAppInstance?.questions?.length")
            if isinstance(count, int) and count > 0:
                question_count = count
                logger.info(
                    f"Determined question count from Alpine state: {question_count}"
                )
            else:
                logger.warning(f"Alpine state returned invalid count ({count}).")
                raise ValueError("Invalid count from Alpine")
        except Exception as e_alpine:
            logger.warning(
                f"Error getting count from Alpine ({e_alpine}). Trying JSON script."
            )
            try:
                quiz_data_script = page.locator("#quiz-data")
                expect_pw(quiz_data_script, "Quiz data script attached").to_be_attached(
                    timeout=5000
                )
                data_content = quiz_data_script.inner_text(timeout=5000)
                questions = json.loads(data_content)
                if isinstance(questions, list):
                    question_count = len(questions)
                    logger.info(
                        f"Determined question count from #quiz-data: {question_count}"
                    )
                else:
                    question_count = 0
            except Exception as e_json:
                logger.error(f"Failed to get question count from JSON script: {e_json}")
                question_count = 0

        if question_count <= 0:
            logger.error(
                "Could not determine a valid question count (>0). Ensure Quiz ID 1 exists and has questions."
            )
            no_q_fail_path = get_screenshot_path(name, "_NO_QUESTIONS_ERROR")
            page.screenshot(path=no_q_fail_path)
            pytest.fail(
                f"Failed to determine question count. Screenshot: {no_q_fail_path}"
            )
            return

        # --- Click Through the Quiz Using Event Synchronization ---
        logger.info(f"Answering {question_count} questions...")
        for i in range(question_count):
            q_num = i + 1
            logger.info(f"--- Answering Question {q_num}/{question_count} ---")

            expected_event_name = f"quiz:{'question-changed' if i < question_count - 1 else 'quiz-completed'}"
            logger.info(f"Expecting event '{expected_event_name}' after this answer.")

            current_options = page.locator("#quiz-app-container button.option-button")
            expect_pw(
                current_options.first, f"Options for Q{q_num} visible"
            ).to_be_visible(timeout=POST_EVENT_UI_TIMEOUT)
            option_to_click = current_options.first
            expect_pw(option_to_click, f"Option 1 for Q{q_num} enabled").to_be_enabled(
                timeout=POST_EVENT_UI_TIMEOUT
            )

            # Inject listener and wait for flag (Modified section from previous fix)
            listener_flag_name = (
                f"__pw_event_{expected_event_name.replace(':', '_')}_{uuid.uuid4().hex}"
            )
            listener_detail_name = f"{listener_flag_name}_detail"
            listener_function_name = f"{listener_flag_name}_func"
            logger.info(
                f"Injecting listener for '{expected_event_name}' using flag '{listener_flag_name}'"
            )
            page.evaluate(
                f"""() => {{
                window['{listener_flag_name}'] = false; window['{listener_detail_name}'] = null;
                window['{listener_function_name}'] = (event) => {{ console.log('INTERNAL LISTENER: Event {expected_event_name} caught!'); window['{listener_flag_name}'] = true; window['{listener_detail_name}'] = event.detail; }};
                document.addEventListener('{expected_event_name}', window['{listener_function_name}']);
                console.log('INTERNAL LISTENER: Added listener for {expected_event_name}'); }}"""
            )
            logger.info(f"Clicking first option for Q{q_num}...")
            option_to_click.click()
            logger.info(f"Clicked. Waiting for flag '{listener_flag_name}'...")
            try:
                page.wait_for_function(
                    f"() => window['{listener_flag_name}'] === true",
                    timeout=EVENT_WAIT_TIMEOUT,
                )
                event_detail = page.evaluate(f"() => window['{listener_detail_name}']")
                logger.info(
                    f"Flag received. Event '{expected_event_name}' confirmed. Detail: {event_detail}"
                )
            except PlaywrightTimeoutError:
                logger.error(
                    f"Timeout waiting for flag '{listener_flag_name}' for event '{expected_event_name}' after Q{q_num}."
                )
                flag_timeout_path = get_screenshot_path(name, f"_FLAG_TIMEOUT_Q{q_num}")
                page.screenshot(path=flag_timeout_path)
                pytest.fail(
                    f"Timed out waiting for event '{expected_event_name}' on Q{q_num} at {name}. Screenshot: {flag_timeout_path}"
                )
            except Exception as e:
                logger.error(
                    f"Error waiting for flag '{listener_flag_name}' on Q{q_num}: {e}"
                )
                flag_error_path = get_screenshot_path(name, f"_FLAG_ERROR_Q{q_num}")
                page.screenshot(path=flag_error_path)
                pytest.fail(
                    f"Error during flag wait on Q{q_num} at {name}. Screenshot: {flag_error_path}"
                )
            finally:
                logger.info(f"Cleaning up listener and flags for {listener_flag_name}")
                page.evaluate(
                    f"""() => {{ if (window['{listener_function_name}']) {{ document.removeEventListener('{expected_event_name}', window['{listener_function_name}']); console.log('INTERNAL LISTENER: Removed listener for {expected_event_name}'); }}
                    delete window['{listener_flag_name}']; delete window['{listener_detail_name}']; delete window['{listener_function_name}']; }}"""
                )
            # End Modified Section

            # Wait for next UI state
            if expected_event_name == "quiz:question-changed":
                next_q_num = q_num + 1
                logger.info(f"Waiting for Q{next_q_num} options to render...")
                next_options = page.locator("#quiz-app-container button.option-button")
                try:
                    expect_pw(
                        next_options.first, f"Q{next_q_num} option visible"
                    ).to_be_visible(timeout=POST_EVENT_UI_TIMEOUT)
                    expect_pw(
                        next_options.first, f"Q{next_q_num} option enabled"
                    ).to_be_enabled(timeout=POST_EVENT_UI_TIMEOUT)
                    logger.info(f"Q{next_q_num} options ready.")
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout waiting for Q{next_q_num} options render.")
                    next_q_render_path = get_screenshot_path(
                        name, f"_NEXT_Q_RENDER_TIMEOUT_Q{next_q_num}"
                    )
                    page.screenshot(path=next_q_render_path)
                    pytest.fail(
                        f"Timed out waiting for Q{next_q_num} render at {name}. Screenshot: {next_q_render_path}"
                    )
            elif expected_event_name == "quiz:quiz-completed":
                logger.info("Quiz completed event confirmed.")

        # --- Test the Results Panel Layout ---
        logger.info(f"--- Testing Results Panel Layout for Breakpoint: {name} ---")
        check_results_panel_visibility(page, name)

        screenshot_path = get_screenshot_path(name, "_results")  # Suffix results
        page.screenshot(path=screenshot_path)
        logger.info(f"Results Screenshot saved to {screenshot_path}")

        # Check Button Layout
        results_panel = page.locator("#quiz-results-panel")
        play_again_button = results_panel.locator('button:text("Play Again")')
        go_home_button = results_panel.locator('a:text("Go Home")')  # Updated selector
        play_again_box = play_again_button.bounding_box(timeout=2000)
        go_home_box = go_home_button.bounding_box(timeout=2000)
        if play_again_box and go_home_box:
            button_height = play_again_box["height"]
            button_width = play_again_box["width"]
            y_diff = abs(play_again_box["y"] - go_home_box["y"])
            x_diff = abs(play_again_box["x"] - go_home_box["x"])
            if size["width"] < 640:  # Check breakpoint
                logger.info(f"Verifying button stacking for {name}")
                assert y_diff > (
                    button_height * 0.5
                ), f"Stacking fail (Y diff {y_diff:.1f}) at {name}"
                assert x_diff < (
                    button_width * 0.5
                ), f"Stacking fail (X diff {x_diff:.1f}) at {name}"
                logger.info(f"Button stacking verified for {name}.")
            else:
                logger.info(f"Verifying button row layout for {name}")
                assert y_diff < 15, f"Row fail (Y diff {y_diff:.1f}) at {name}"
                assert x_diff > (
                    button_width * 0.5
                ), f"Row fail (X diff {x_diff:.1f}) at {name}"
                logger.info(f"Button row layout verified for {name}.")
        else:
            if not play_again_box:
                pytest.fail(f"No bounding box for 'Play Again' button at {name}")
            if not go_home_box:
                pytest.fail(f"No bounding box for 'Go Home' button at {name}")

        logger.info(f"--- Test Completed Successfully: {test_name} ---")

    except PlaywrightTimeoutError as e:
        logger.error(f"\n!!! Playwright Timeout Error: {test_name} !!!")
        timeout_message = getattr(e, "message", str(e))
        logger.error(f"Timeout details: {timeout_message}")
        error_screenshot_path = get_screenshot_path(name, "_TIMEOUT_ERROR")
        error_html_path = get_html_path(name, "_TIMEOUT_ERROR")
        try:
            page.screenshot(path=error_screenshot_path, full_page=True)
            logger.info(f"Timeout screenshot: {error_screenshot_path}")
            with open(error_html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            logger.info(f"Timeout HTML: {error_html_path}")
        except Exception as diag_error:
            logger.error(f"Could not save diagnostics: {diag_error}")
        pytest.fail(f"TimeoutError in {test_name}: {timeout_message}")

    except Exception as e:
        logger.exception(f"\n!!! Unexpected Error: {test_name} !!!")
        error_screenshot_path = get_screenshot_path(name, "_UNEXPECTED_ERROR")
        error_html_path = get_html_path(name, "_UNEXPECTED_ERROR")
        try:
            page.screenshot(path=error_screenshot_path, full_page=True)
            logger.info(f"Error screenshot: {error_screenshot_path}")
            with open(error_html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            logger.info(f"Error HTML: {error_html_path}")
        except Exception as diag_error:
            logger.error(f"Could not save diagnostics: {diag_error}")
        pytest.fail(f"Unexpected error in {test_name}: {e}")
