# tests/test_responsive.py
import pytest
import os
# Renamed expect to expect_pw to avoid confusion with numerical checks
from playwright.sync_api import Page, expect as expect_pw, Locator, TimeoutError as PlaywrightTimeoutError
import time
import json
import logging
import uuid # Import uuid for unique flag names

# --- Setup Logging ---
log_format = '%(asctime)s - %(levelname)s - %(name)s - [%(filename)s:%(lineno)d] - %(message)s'
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
BASE_URL = "http://127.0.0.1:8000"
# !!! IMPORTANT: Ensure Quiz ID 1 exists with > 0 questions, e.g., via add_sample_quizzes !!!
QUIZ_URL = "/quiz/41/"
SCREENSHOT_DIR = "playwright_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Timeouts (consider adjusting based on actual performance)
DEFAULT_VISIBILITY_TIMEOUT = 20000 # ms for elements to become visible initially
INSTANCE_WAIT_TIMEOUT = 10000      # ms to wait specifically for window.quizAppInstance
# Timeout for waiting for custom events (should cover longest feedback + processing)
# app.js has 5000ms for incorrect feedback. Add buffer.
EVENT_WAIT_TIMEOUT = 8000          # ms
# Timeout for UI elements to render *after* an event has fired
POST_EVENT_UI_TIMEOUT = 5000       # ms


# --- Helper Functions ---
def check_results_panel_visibility(page: Page, breakpoint_name: str):
    """Checks visibility of key elements within the results panel."""
    logger.info(f"Checking results panel visibility at {breakpoint_name}...")

    # --- Use the specific ID for the results panel ---
    results_panel_locator_str = '#quiz-results-panel'
    logger.info(f"Using locator: {results_panel_locator_str}")
    results_panel = page.locator(results_panel_locator_str)
    # -------------------------------------------------

    # Ensure the container itself is visible first
    # Increased timeout slightly just in case transition takes a moment longer
    expect_pw(results_panel, f"Results panel container should be visible at {breakpoint_name}").to_be_visible(timeout=POST_EVENT_UI_TIMEOUT + 3000) # Extra time after completion event
    logger.info("Results panel container is visible.")

    results_heading = results_panel.locator('h3:text("Quiz Results")')
    expect_pw(results_heading, f"Results heading should be visible at {breakpoint_name}").to_be_visible()

    stats_section = results_panel.locator('div:has-text("Rating")').first
    expect_pw(stats_section, f"Stats section should be visible at {breakpoint_name}").to_be_visible()
    expect_pw(stats_section.locator('span:text("Score")'), "Score label should be visible").to_be_visible()
    expect_pw(stats_section.locator('span:text("Percentage")'), "Percentage label should be visible").to_be_visible()
    expect_pw(stats_section.locator('span:text("Time")'), "Time label should be visible").to_be_visible()
    expect_pw(stats_section.locator('span:text("Rating")'), "Rating label should be visible").to_be_visible()

    mistakes_section = results_panel.locator('div:has-text("Mistakes Review")').first
    expect_pw(mistakes_section, f"Mistakes section should be visible at {breakpoint_name}").to_be_visible()
    mistakes_list = mistakes_section.locator("ul")
    expect_pw(mistakes_list, f"Mistakes list should be visible at {breakpoint_name}").to_be_visible()

    go_home_button = results_panel.locator('a[href="/"]:text("Go Home")')
    expect_pw(go_home_button, f"Go Home button should be visible at {breakpoint_name}").to_be_visible()
    expect_pw(go_home_button, f"Go Home button should be enabled at {breakpoint_name}").to_be_enabled()

    play_again_button = results_panel.locator('button:text("Play Again")')
    expect_pw(play_again_button, f"Play Again button should be visible at {breakpoint_name}").to_be_visible()
    expect_pw(play_again_button, f"Play Again button should be enabled at {breakpoint_name}").to_be_enabled()

    logger.info(f"Results panel checks passed for {breakpoint_name}.")


# --- Test Function ---
@pytest.mark.parametrize("name, size", BREAKPOINTS.items())
def test_results_layout_responsiveness(page: Page, name: str, size: dict):
    """
    Test the layout of the quiz results view across different breakpoints
    by answering questions and synchronizing with wait_for_function.
    """
    test_name = f"test_results_layout_responsiveness[{name}]"
    logger.info(f"--- Starting Test: {test_name} ({size['width']}x{size['height']}) ---")
    page.set_viewport_size(size)

    # --- ADDED: Set up listeners for browser console/errors ---
    page.on("console", lambda msg: logger.info(f"BROWSER CONSOLE [{msg.type}]: {msg.text}"))
    page.on("pageerror", lambda exc: logger.error(f"BROWSER PAGE ERROR: {exc}"))
    logger.info("Added browser console and page error listeners.")
    # --- END OF ADDED LISTENERS ---

    try:
        page.goto(f"{BASE_URL}{QUIZ_URL}")
        logger.info(f"Navigated to {page.url}")

        # --- Wait for Quiz to Load & Alpine Instance ---
        logger.info("Waiting for Alpine component to initialize...")
        quiz_container = page.locator("#quiz-app-container")
        expect_pw(quiz_container, "Quiz container should become visible").to_be_visible(timeout=DEFAULT_VISIBILITY_TIMEOUT)
        expect_pw(quiz_container, "Quiz container should have x-data").to_have_attribute("x-data", "quizApp()", timeout=5000)

        try:
            logger.info(f"Waiting up to {INSTANCE_WAIT_TIMEOUT}ms for window.quizAppInstance...")
            page.wait_for_function(
                "() => typeof window.quizAppInstance !== 'undefined' && window.quizAppInstance !== null && typeof window.quizAppInstance.init === 'function'",
                timeout=INSTANCE_WAIT_TIMEOUT
            )
            logger.info("window.quizAppInstance is available.")
            # Also ensure TESTING_MODE is set for events to fire
            logger.info(f"Waiting up to 2000ms for window.TESTING_MODE === true...")
            page.wait_for_function("() => window.TESTING_MODE === true", timeout=2000)
            logger.info("window.TESTING_MODE confirmed true.")

        except PlaywrightTimeoutError:
            logger.error("Timeout waiting for window.quizAppInstance or TESTING_MODE. Check app.js init.")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"results_INSTANCE_TIMEOUT_ERROR_{name}.png"))
            pytest.fail("window.quizAppInstance did not become available or TESTING_MODE not set.")
            return

        first_option = page.locator("#quiz-app-container button.option-button").first
        expect_pw(first_option, "First option button should render after init").to_be_visible(timeout=DEFAULT_VISIBILITY_TIMEOUT)
        expect_pw(first_option, "First option button should have text content").not_to_be_empty(timeout=5000)
        logger.info("Quiz component initialized and first question rendered.")

        # --- Determine Question Count (Robustly) ---
        question_count = 0
        logger.info("Attempting to determine question count...")
        try:
            # Prefer Alpine state
            count = page.evaluate("() => window.quizAppInstance?.questions?.length") # No timeout arg needed
            if isinstance(count, int) and count > 0:
                question_count = count
                logger.info(f"Determined question count from Alpine state: {question_count}")
            else:
                 logger.warning(f"Alpine state returned invalid count ({count}). Falling back.")
                 raise ValueError("Invalid count from Alpine")
        except Exception as e_alpine:
            logger.warning(f"Error getting count from Alpine ({e_alpine}). Trying JSON script fallback...")
            try:
                 quiz_data_script = page.locator("#quiz-data")
                 # Use to_be_attached, not to_be_visible for script tags
                 expect_pw(quiz_data_script, "Quiz data script should be attached").to_be_attached(timeout=5000)
                 data_content = quiz_data_script.inner_text(timeout=5000)
                 questions = json.loads(data_content)
                 if isinstance(questions, list):
                     question_count = len(questions)
                     logger.info(f"Determined question count from #quiz-data script: {question_count}")
                 else:
                     logger.error("Parsed #quiz-data content is not a list.")
                     question_count = 0
            except Exception as e_json:
                logger.error(f"Failed to get question count from JSON script: {e_json}")
                question_count = 0

        if question_count <= 0:
            logger.error("Could not determine a valid question count (>0). Ensure Quiz ID 1 exists and has questions.")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"results_NO_QUESTIONS_ERROR_{name}.png"))
            pytest.fail("Failed to determine question count for the quiz.")
            return

        # --- Click Through the Quiz Using Event Synchronization ---
        logger.info(f"Answering {question_count} questions...")
        for i in range(question_count):
            q_num = i + 1
            logger.info(f"--- Answering Question {q_num}/{question_count} ---")

            expected_event_name = f"quiz:{'question-changed' if i < question_count - 1 else 'quiz-completed'}"
            logger.info(f"Expecting event '{expected_event_name}' after this answer.")

            # Ensure current options are ready before interacting
            current_options = page.locator("#quiz-app-container button.option-button")
            expect_pw(current_options.first, f"Options for Q{q_num} should be visible before click").to_be_visible(timeout=POST_EVENT_UI_TIMEOUT)
            option_to_click = current_options.first
            expect_pw(option_to_click, f"Option 1 for Q{q_num} should be enabled before click").to_be_enabled(timeout=POST_EVENT_UI_TIMEOUT)


            # --- MODIFIED: Use wait_for_function with injected listener ---
            listener_flag_name = f"__pw_event_{expected_event_name.replace(':', '_')}_{uuid.uuid4().hex}"
            listener_detail_name = f"{listener_flag_name}_detail"
            listener_function_name = f"{listener_flag_name}_func"

            logger.info(f"Injecting listener for '{expected_event_name}' using flag '{listener_flag_name}'")
            # Inject the listener using page.evaluate
            page.evaluate(f"""() => {{
                window['{listener_flag_name}'] = false;
                window['{listener_detail_name}'] = null;
                window['{listener_function_name}'] = (event) => {{
                    console.log('INTERNAL LISTENER: Event {expected_event_name} caught!');
                    window['{listener_flag_name}'] = true;
                    window['{listener_detail_name}'] = event.detail;
                }};
                document.addEventListener('{expected_event_name}', window['{listener_function_name}']);
                console.log('INTERNAL LISTENER: Added listener for {expected_event_name}');
            }}""")

            # Click the option
            logger.info(f"Clicking first option for Q{q_num}...")
            option_to_click.click()
            logger.info(f"Clicked first option for question {q_num}. Now waiting for flag '{listener_flag_name}'...")

            # Wait for the flag to be set by the event listener
            try:
                page.wait_for_function(
                    f"() => window['{listener_flag_name}'] === true",
                    timeout=EVENT_WAIT_TIMEOUT
                )
                # Optional: Get event detail
                event_detail = page.evaluate(f"() => window['{listener_detail_name}']")
                logger.info(f"Flag '{listener_flag_name}' received. Event '{expected_event_name}' confirmed. Detail: {event_detail}")

            except PlaywrightTimeoutError:
                logger.error(f"Timeout waiting for flag '{listener_flag_name}' for event '{expected_event_name}' after clicking Q{q_num}.")
                page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"results_FLAG_TIMEOUT_Q{q_num}_{name}.png"))
                pytest.fail(f"Timed out waiting for injected listener flag for event '{expected_event_name}' on Q{q_num} at {name}")
            except Exception as e:
                 logger.error(f"Error occurred while waiting for flag '{listener_flag_name}' on Q{q_num}: {e}")
                 page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"results_FLAG_ERROR_Q{q_num}_{name}.png"))
                 pytest.fail(f"Error during flag wait on Q{q_num} at {name}: {e}")
            finally:
                # Clean up the injected listener and flags
                logger.info(f"Cleaning up listener and flags for {listener_flag_name}")
                page.evaluate(f"""() => {{
                    if (window['{listener_function_name}']) {{
                        document.removeEventListener('{expected_event_name}', window['{listener_function_name}']);
                        console.log('INTERNAL LISTENER: Removed listener for {expected_event_name}');
                    }}
                    delete window['{listener_flag_name}'];
                    delete window['{listener_detail_name}'];
                    delete window['{listener_function_name}'];
                }}""")
            # --- END OF MODIFIED SECTION ---


            # (CRUCIAL) After event, wait for the *next* UI state to be ready
            if expected_event_name == "quiz:question-changed":
                next_q_num = q_num + 1
                logger.info(f"Event confirmed, waiting for Q{next_q_num}'s options to render (max {POST_EVENT_UI_TIMEOUT}ms)...")
                next_options = page.locator("#quiz-app-container button.option-button")
                try:
                    # Wait specifically for the *new* options to appear and be ready
                    expect_pw(next_options.first, f"First option for Q{next_q_num} should appear after event").to_be_visible(timeout=POST_EVENT_UI_TIMEOUT)
                    expect_pw(next_options.first, f"First option for Q{next_q_num} should be enabled after event").to_be_enabled(timeout=POST_EVENT_UI_TIMEOUT)
                    logger.info(f"Q{next_q_num}'s options are ready.")
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout waiting for Q{next_q_num}'s options to render after '{expected_event_name}'.")
                    page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"results_NEXT_Q_RENDER_TIMEOUT_Q{next_q_num}_{name}.png"))
                    pytest.fail(f"Timed out waiting for Q{next_q_num} render at {name}")

            elif expected_event_name == "quiz:quiz-completed":
                 logger.info("Quiz completed event confirmed. Results panel should appear shortly.")
                 # The check_results_panel_visibility helper function will now wait for the panel


        # --- Test the Results Panel Layout at the specific breakpoint ---
        logger.info(f"--- Testing Results Panel Layout for Breakpoint: {name} ---")

        # 1. Verify Results Panel Elements Visibility (includes waiting for the panel)
        check_results_panel_visibility(page, name) # This function now has waits built-in

        # 2. Capture Screenshot (after verifying visibility)
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"quiz_results_{name}.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")

        # 3. Check Button Layout (Stacking vs Row)
        # Use the robust ID locator
        results_panel = page.locator('#quiz-results-panel')
        play_again_button = results_panel.locator('button:text("Play Again")')
        go_home_button = results_panel.locator('a[href="/"]:text("Go Home")')

        # Bounding box checks require elements to be visible, which check_results_panel_visibility ensures
        play_again_box = play_again_button.bounding_box(timeout=2000) # Short timeout ok here
        go_home_box = go_home_button.bounding_box(timeout=2000)

        if play_again_box and go_home_box:
            button_height = play_again_box['height']
            button_width = play_again_box['width']
            y_diff = abs(play_again_box['y'] - go_home_box['y'])
            x_diff = abs(play_again_box['x'] - go_home_box['x'])

            # Tailwind class `sm:flex-row` in index.html dictates layout change at 640px
            if size["width"] < 640:
                 logger.info(f"Verifying button stacking for {name} (< 640px)")
                 # --- MODIFIED: Use standard Python assert ---
                 assert y_diff > (button_height * 0.5), f"Y diff ({y_diff:.1f}) should be > ~0.5 button height ({button_height * 0.5:.1f}) (stacked) at {name}"
                 assert x_diff < (button_width * 0.5), f"X diff ({x_diff:.1f}) should be relatively small (stacked) at {name}"
                 # --- END MODIFICATION ---
                 logger.info(f"Button stacking verified for {name}.")
            else:
                 logger.info(f"Verifying button row layout for {name} (>= 640px)")
                 # --- MODIFIED: Use standard Python assert ---
                 assert y_diff < 15, f"Y diff ({y_diff:.1f}) should be small (< 15px) (row) at {name}" # Allow tolerance for alignment
                 assert x_diff > (button_width * 0.5), f"X diff ({x_diff:.1f}) should be > ~0.5 button width ({button_width * 0.5:.1f}) (row) at {name}"
                 # --- END MODIFICATION ---
                 logger.info(f"Button row layout verified for {name}.")
        else:
            logger.warning(f"Could not get bounding boxes for action buttons at {name}. Skipping layout check.")
            # Fail if boxes are None, as visibility should have been confirmed by check_results_panel_visibility
            if not play_again_box: pytest.fail(f"Could not get bounding box for 'Play Again' button at {name} after it was deemed visible.")
            if not go_home_box: pytest.fail(f"Could not get bounding box for 'Go Home' button at {name} after it was deemed visible.")


        logger.info(f"--- Test Completed Successfully: {test_name} ---")

    except PlaywrightTimeoutError as e:
        logger.error(f"\n!!! Playwright Timeout Error Occurred during {test_name} !!!")
        error_details = str(e)
        # Try to get the specific timeout message from the exception if available
        timeout_message = getattr(e, 'message', error_details)
        logger.error(f"Timeout details: {timeout_message}")
        error_screenshot_path = os.path.join(SCREENSHOT_DIR, f"results_TIMEOUT_ERROR_{name}.png")
        try:
             page.screenshot(path=error_screenshot_path, full_page=True)
             logger.info(f"Timeout error screenshot saved to {error_screenshot_path}")
             html_content = page.content()
             html_path = os.path.join(SCREENSHOT_DIR, f"results_TIMEOUT_ERROR_{name}.html")
             with open(html_path, "w", encoding="utf-8") as f: f.write(html_content)
             logger.info(f"Timeout error HTML saved to {html_path}")
        except Exception as diag_error:
            logger.error(f"Could not save diagnostic info on timeout: {diag_error}")
        pytest.fail(f"Playwright TimeoutError in {test_name}: {timeout_message}")

    except Exception as e:
        logger.exception(f"\n!!! An unexpected error occurred during {test_name} !!!") # Includes traceback
        error_screenshot_path = os.path.join(SCREENSHOT_DIR, f"results_UNEXPECTED_ERROR_{name}.png")
        try:
             page.screenshot(path=error_screenshot_path, full_page=True)
             logger.info(f"Unexpected error screenshot saved to {error_screenshot_path}")
             html_content = page.content()
             html_path = os.path.join(SCREENSHOT_DIR, f"results_UNEXPECTED_ERROR_{name}.html")
             with open(html_path, "w", encoding="utf-8") as f: f.write(html_content)
             logger.info(f"Unexpected error HTML saved to {html_path}")
        except Exception as diag_error:
            logger.error(f"Could not save diagnostic info on unexpected error: {diag_error}")
        pytest.fail(f"Unexpected error in {test_name}: {e}")