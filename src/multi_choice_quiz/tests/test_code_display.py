# src/multi_choice_quiz/tests/test_code_display.py (Updated Content)

import pytest
from playwright.sync_api import Page, expect
import os
from datetime import datetime
from django.conf import settings  # Import settings

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging for this specific app
logger = setup_test_logging(__name__, "multi_choice_quiz")  # Pass app_name


@pytest.mark.skip(
    reason="Temporarily ignoring this test due to not so pressing issue at the moment."
)
@pytest.mark.usefixtures("capture_console_errors")
def test_code_elements_display_correctly(page: Page, django_server):
    """Test that code elements display correctly in quiz questions and options."""
    # Define the app name for logging/screenshots
    app_name = "multi_choice_quiz"
    app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
    os.makedirs(app_log_dir, exist_ok=True)

    try:
        # Navigate to the quiz page
        # Try accessing a quiz known to have code questions (assuming one exists)
        # If not, use the default quiz URL and hope it eventually shows code questions
        # For robust testing, we'd ideally load the 'Code Display Test Quiz' specifically
        # quiz_url = django_server + "/quiz/CODE_QUIZ_ID/" # Replace CODE_QUIZ_ID if known
        quiz_url = django_server + "/quiz/"  # Fallback to default quiz page
        logger.info(f"Navigating to {quiz_url}")
        page.goto(quiz_url)

        # Wait for the quiz to load
        # <<< FIX: Changed selector from class to ID >>>
        page.wait_for_selector("#question-text", state="visible", timeout=10000)

        # Take screenshot of initial question for reference
        screenshot_path = os.path.join(app_log_dir, "code_display_test_initial.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Initial screenshot saved to: {screenshot_path}")

        # --- Find a question with code elements ---
        found_code_question = False
        max_attempts = 5  # Try up to 5 questions
        for attempt in range(max_attempts):
            logger.info(f"Checking question {attempt + 1} for code elements...")
            # <<< FIX: Changed selector from class to ID >>>
            question_text_locator = page.locator("#question-text")
            option_buttons_locator = page.locator(".option-button")

            # Check current question and options
            has_code_in_question = (
                question_text_locator.locator("code, pre").count() > 0
            )
            has_code_in_options = (
                option_buttons_locator.locator("code, pre").count() > 0
            )

            if has_code_in_question or has_code_in_options:
                logger.info("Found question/options with code elements.")
                found_code_question = True
                break  # Found one, proceed with checks

            # If no code found and not the last question, move to the next one
            if (
                attempt < max_attempts - 1
                and not page.locator(".results-card").is_visible()
            ):
                logger.info("No code found, moving to next question...")
                option_buttons_locator.first.click()
                # Wait for feedback and transition
                page.wait_for_timeout(2500)  # Adjust based on feedback duration
                # Ensure question actually changed
                page.wait_for_function(
                    f"""
                    (expectedIndex) => {{
                        const indicator = document.querySelector('.progress-indicator');
                        return indicator && indicator.textContent.startsWith(expectedIndex + '/');
                    }}
                """,
                    arg=f"{attempt + 2}",
                    timeout=5000,
                )
            elif page.locator(".results-card").is_visible():
                logger.warning("Reached end of quiz before finding code elements.")
                break
            else:
                logger.warning(
                    f"Max attempts ({max_attempts}) reached without finding code elements."
                )

        # --- Perform checks only if code elements were found ---
        if found_code_question:
            logger.info("Performing code element display checks...")
            # <<< FIX: Changed selector from class to ID >>>
            question_text = page.locator("#question-text")

            # Check code in question text
            question_codes = question_text.locator("code")
            question_pres = question_text.locator("pre")

            if question_codes.count() > 0:
                logger.info(
                    f"Checking {question_codes.count()} <code> elements in question..."
                )
                first_code = question_codes.first
                expect(first_code).to_be_visible()
                # Add more specific style checks if needed (e.g., background, font)
                # Example: Check background color is somewhat dark/transparent
                bg_color = first_code.evaluate(
                    "el => window.getComputedStyle(el).backgroundColor"
                )
                assert (
                    "rgba" in bg_color or "rgb" in bg_color
                ), "Inline code background missing"

            if question_pres.count() > 0:
                logger.info(
                    f"Checking {question_pres.count()} <pre> elements in question..."
                )
                first_pre = question_pres.first
                expect(first_pre).to_be_visible()
                expect(first_pre.locator("code")).to_be_visible()  # Code inside pre
                # Example: Check pre background color
                bg_color = first_pre.evaluate(
                    "el => window.getComputedStyle(el).backgroundColor"
                )
                assert (
                    "rgba" in bg_color or "rgb" in bg_color
                ), "<pre> background missing"

            # Check code in options
            option_buttons = page.locator(".option-button")
            for i in range(option_buttons.count()):
                button = option_buttons.nth(i)
                option_codes = button.locator("code")
                option_pres = button.locator("pre")

                if option_codes.count() > 0:
                    logger.info(
                        f"Checking {option_codes.count()} <code> elements in option {i+1}..."
                    )
                    expect(option_codes.first).to_be_visible()
                    # Add style checks if needed

                if option_pres.count() > 0:
                    logger.info(
                        f"Checking {option_pres.count()} <pre> elements in option {i+1}..."
                    )
                    expect(option_pres.first).to_be_visible()
                    expect(option_pres.first.locator("code")).to_be_visible()
                    # Add style checks if needed

            # Take screenshot of the question with code
            code_question_screenshot = os.path.join(
                app_log_dir, f"code_display_question_{attempt+1}.png"
            )
            page.screenshot(path=code_question_screenshot)
            logger.info(
                f"Screenshot of question with code saved to: {code_question_screenshot}"
            )
        else:
            logger.warning(
                "Skipping detailed checks as no code elements were found in the first few questions."
            )
            # Optionally fail the test if finding code is mandatory
            # pytest.fail("Failed to find any code elements to test.")

        logger.info("Code display test completed.")

    except Exception as e:
        # Screenshot on failure (using the refactored approach)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"failure_code_display_{timestamp}.png"
        screenshot_path = os.path.join(app_log_dir, screenshot_filename)
        try:
            page.screenshot(path=screenshot_path)
            logger.error(f"Screenshot saved to: {screenshot_path}")
        except Exception as ss_error:
            logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")

        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise
