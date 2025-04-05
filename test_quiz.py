import pytest
from playwright.sync_api import Page, expect, Error
import pathlib
import os
import logging
import sys  # Import sys for explicit stream handling

# --- File Path Setup ---
# Get the absolute path to the directory containing this script
current_dir = pathlib.Path(__file__).parent.resolve()
# Construct the file URL for index.html
html_file_path = os.path.abspath(os.path.join(current_dir, "index.html"))
# Ensure it's formatted as a file URL
html_file_url = f"file://{html_file_path}"

# --- Explicit Logging Setup ---
log_file_path = os.path.join(current_dir, "test_quiz.log")
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_formatter = logging.Formatter(log_format)

# Get the root logger
root_logger = logging.getLogger("")
root_logger.setLevel(logging.INFO)  # Set the minimum level for the root logger

# --- File Handler ---
# Create file handler which logs messages to a file
try:
    # Remove existing handlers matching the file path to avoid duplication if script/pytest reloads
    for handler in root_logger.handlers[:]:
        if (
            isinstance(handler, logging.FileHandler)
            and handler.baseFilename == log_file_path
        ):
            root_logger.removeHandler(handler)
        # Also remove potential default console handlers added by pytest if needed, though adding ours is usually sufficient
        # elif isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
        # root_logger.removeHandler(handler) # Be cautious removing pytest's handlers

    file_handler = logging.FileHandler(log_file_path, mode="w")  # 'w' to overwrite
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)  # Set level for this handler
    root_logger.addHandler(file_handler)
except Exception as e:
    print(
        f"Error setting up file logger: {e}", file=sys.stderr
    )  # Use print if logger fails

# --- Console Handler ---
# Create console handler which logs messages to console (stderr by default)
try:
    # Check if a similar console handler already exists
    has_console_handler = any(
        isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr)
        for h in root_logger.handlers
    )

    if not has_console_handler:
        console_handler = logging.StreamHandler(sys.stderr)  # Log to standard error
        console_handler.setFormatter(log_formatter)  # Use the same format
        console_handler.setLevel(logging.INFO)  # Set level for console output
        root_logger.addHandler(console_handler)
except Exception as e:
    print(
        f"Error setting up console logger: {e}", file=sys.stderr
    )  # Use print if logger fails


# Create a logger instance specifically for this test module
# It will inherit handlers/settings from the root logger
logger = logging.getLogger(__name__)
logger.info("Logging setup complete. File handler directed to: %s", log_file_path)


# --- Fixture to Capture Console Errors ---
@pytest.fixture(scope="function", autouse=True)
def capture_console_errors(page: Page):
    """Listens for and logs any JavaScript console errors during the test."""
    errors = []
    # Use a lambda to capture the exception object correctly
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    yield
    if errors:
        logger.error(">>> JavaScript console errors detected during test run:")
        for i, error in enumerate(errors):
            logger.error(f"  Console Error {i+1}: {error}")
        # Uncomment the next line if you want console errors to fail the test
        # pytest.fail("JavaScript console errors detected.", pytrace=False)


# --- Test Function ---
def test_quiz_flow(page: Page):
    """
    Tests the full flow of the quiz application using logging and waits.
    Logs are sent to 'test_quiz.log' and the console.
    """
    logger.info(f"Starting quiz flow test. Loading: {html_file_url}")
    try:
        # Go to the page, wait for the load event
        page.goto(html_file_url, wait_until="domcontentloaded")  # Try domcontentloaded
        logger.info(f"Page navigation to {html_file_url} attempted.")

        # *** Wait for a key element rendered by Alpine.js ***
        logger.info(
            "Waiting for the first option button to become visible (max 10s)..."
        )
        first_option_button_selector = ".option-button >> nth=0"
        page.wait_for_selector(
            first_option_button_selector, state="visible", timeout=10000
        )
        logger.info("First option button is visible. Assuming Alpine.js initialized.")

    except Error as e:
        logger.exception(
            f"FATAL: Failed to load page or find initial element.", exc_info=e
        )  # Log exception details
        pytest.fail(
            f"Setup failed: Could not load page or find initial element. Check {log_file_path} for details. Error: {e}",
            pytrace=False,
        )
        return  # Stop test if setup fails

    # Define locators once for reuse if applicable
    question_text_locator = page.locator(".question-text")
    progress_indicator_locator = page.locator(".progress-indicator")
    modal_overlay = page.locator(".modal-overlay")
    modal_button = modal_overlay.locator(".modal-button")

    # --- Question 1: Capital of France (Correct Answer) ---
    logger.info("--- Testing Question 1 ---")
    try:
        logger.info("Verifying Question 1 text and progress...")
        expect(question_text_locator).to_have_text(
            "What is the capital of France?", timeout=5000
        )
        expect(progress_indicator_locator).to_have_text("1/3")
        logger.info("Question 1 text and progress verified.")

        paris_option = page.locator(".option-button", has_text="Paris")
        expect(paris_option).to_be_visible()
        logger.info("Clicking 'Paris' option.")
        paris_option.click()

        logger.info("Verifying correct answer modal for Question 1...")
        expect(modal_overlay).to_be_visible(timeout=3000)
        expect(modal_overlay.locator(".modal-container.modal-correct")).to_be_visible()
        expect(modal_overlay.locator(".modal-message")).to_have_text("Correct!")
        logger.info("Correct answer modal verified for Question 1.")

        logger.info("Closing modal for Question 1...")
        modal_button.click()
        expect(modal_overlay).to_be_hidden()

    except Error as e:
        logger.exception("Assertion failed during Question 1.", exc_info=e)
        pytest.fail(
            f"Test failed during Question 1. Check {log_file_path} for details. Error: {e}",
            pytrace=False,
        )

    # --- Question 2: Longest River (Incorrect Answer) ---
    logger.info("--- Testing Question 2 ---")
    try:
        logger.info("Verifying Question 2 text and progress...")
        expect(question_text_locator).to_have_text(
            "Which river is the longest in the world?", timeout=5000
        )
        expect(progress_indicator_locator).to_have_text("2/3")
        logger.info("Question 2 text and progress verified.")

        amazon_option = page.locator(".option-button", has_text="Amazon")
        expect(amazon_option).to_be_visible()
        logger.info("Clicking 'Amazon' option (incorrect).")
        amazon_option.click()

        logger.info("Verifying incorrect answer modal for Question 2...")
        expect(modal_overlay).to_be_visible()
        expect(
            modal_overlay.locator(".modal-container.modal-incorrect")
        ).to_be_visible()
        expect(modal_overlay.locator(".modal-message")).to_have_text("Incorrect!")
        expect(modal_overlay.locator(".modal-explanation")).to_contain_text(
            "The correct answer was: Nile"
        )
        logger.info("Incorrect answer modal verified for Question 2.")

        logger.info("Closing modal for Question 2...")
        modal_button.click()
        expect(modal_overlay).to_be_hidden()

    except Error as e:
        logger.exception("Assertion failed during Question 2.", exc_info=e)
        pytest.fail(
            f"Test failed during Question 2. Check {log_file_path} for details. Error: {e}",
            pytrace=False,
        )

    # --- Question 3: Highest Mountain (Correct Answer) ---
    logger.info("--- Testing Question 3 ---")
    try:
        logger.info("Verifying Question 3 text and progress...")
        expect(question_text_locator).to_have_text(
            "What is the highest mountain peak in the world?", timeout=5000
        )
        expect(progress_indicator_locator).to_have_text("3/3")
        logger.info("Question 3 text and progress verified.")

        everest_option = page.locator(".option-button", has_text="Mount Everest")
        expect(everest_option).to_be_visible()
        logger.info("Clicking 'Mount Everest' option.")
        everest_option.click()

        logger.info("Verifying correct answer modal for Question 3...")
        expect(modal_overlay).to_be_visible()
        expect(modal_overlay.locator(".modal-container.modal-correct")).to_be_visible()
        expect(modal_overlay.locator(".modal-message")).to_have_text("Correct!")
        logger.info("Correct answer modal verified for Question 3.")

        logger.info("Closing modal for Question 3 (proceeding to results)...")
        modal_button.click()
        expect(modal_overlay).to_be_hidden()

    except Error as e:
        logger.exception("Assertion failed during Question 3.", exc_info=e)
        pytest.fail(
            f"Test failed during Question 3. Check {log_file_path} for details. Error: {e}",
            pytrace=False,
        )

    # --- Results Screen ---
    logger.info("--- Testing Results Screen ---")
    try:
        results_card = page.locator(".results-card")
        logger.info("Waiting for results card to become visible...")
        expect(results_card).to_be_visible(timeout=5000)
        logger.info("Results card is visible.")

        expect(page.locator(".question-card")).to_be_hidden()
        expect(page.locator(".options-container")).to_be_hidden()
        logger.info("Quiz view elements (question/options) are hidden.")

        logger.info("Verifying results title and score...")
        expect(results_card.locator(".results-title")).to_have_text("Quiz Completed!")
        expect(results_card.locator(".results-score")).to_contain_text(
            "Your Score: 2 out of 3"
        )
        logger.info("Results title and score verified.")

        logger.info("Verifying results summary details...")
        summary_items = results_card.locator(".result-item")
        expect(summary_items).to_have_count(3)
        expect(summary_items.nth(0)).to_contain_text("✅")
        expect(summary_items.nth(0)).to_contain_text("What is the capital of France?")
        expect(summary_items.nth(1)).to_contain_text("❌")
        expect(summary_items.nth(1)).to_contain_text(
            "Which river is the longest in the world?"
        )
        expect(summary_items.nth(1)).to_contain_text("(Correct: Nile)")
        expect(summary_items.nth(2)).to_contain_text("✅")
        expect(summary_items.nth(2)).to_contain_text(
            "What is the highest mountain peak in the world?"
        )
        logger.info("Results summary details verified.")

        restart_button = results_card.locator(".restart-button")
        expect(restart_button).to_be_visible()
        expect(restart_button).to_have_text("Play Again?")
        logger.info("Restart button verified.")

    except Error as e:
        logger.exception("Assertion failed during Results Screen check.", exc_info=e)
        pytest.fail(
            f"Test failed during Results Screen check. Check {log_file_path} for details. Error: {e}",
            pytrace=False,
        )

    # --- Test Restart ---
    logger.info("--- Testing Restart ---")
    try:
        logger.info("Clicking 'Play Again?' button...")
        restart_button = page.locator(".restart-button")
        restart_button.click()

        logger.info("Verifying quiz resets to Question 1...")
        expect(page.locator(".results-card")).to_be_hidden()
        expect(page.locator(".question-card")).to_be_visible(timeout=5000)
        expect(question_text_locator).to_have_text(
            "What is the capital of France?", timeout=5000
        )
        expect(progress_indicator_locator).to_have_text("1/3")
        logger.info("Quiz reset to Question 1 verified.")

        logger.info("Verifying options are enabled after restart...")
        paris_option_after_restart = page.locator(".option-button", has_text="Paris")
        expect(paris_option_after_restart).to_be_enabled()
        logger.info("'Paris' option is enabled after restart.")

    except Error as e:
        logger.exception("Assertion failed during Restart check.", exc_info=e)
        pytest.fail(
            f"Test failed during Restart check. Check {log_file_path} for details. Error: {e}",
            pytrace=False,
        )

    logger.info("--- Quiz Test Completed Successfully! ---")