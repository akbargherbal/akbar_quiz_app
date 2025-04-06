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

# Import the shared logging utility
from .test_utils import setup_test_logging

# --- Constants ---
DJANGO_SERVER_PORT = 8000
DJANGO_SERVER_HOST = "localhost"
DJANGO_SERVER_URL = f"http://{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}"


# --- Helper function to check if port is available ---
def is_port_in_use(port, host="localhost"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


# --- Setup Logging ---
logger = setup_test_logging("test_database_quiz")


# --- Django Server Fixture ---
@pytest.fixture(scope="session")
def django_server():
    """Start Django development server for testing."""
    # Check if port is already in use
    if is_port_in_use(DJANGO_SERVER_PORT):
        logger.warning(
            f"Port {DJANGO_SERVER_PORT} is already in use. Assuming Django server is running."
        )
        yield DJANGO_SERVER_URL
        return

    logger.info(f"Starting Django server at {DJANGO_SERVER_URL}")

    # Get the manage.py path (assuming we're in the app directory)
    src_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
    manage_py_path = os.path.join(src_dir, "manage.py")

    # First, ensure we have sample data
    logger.info("Adding sample quiz data...")
    try:
        # Use Django's call_command to run the management command
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
        import django

        django.setup()

        # Call the management command to add sample quizzes
        call_command("add_sample_quizzes")
        logger.info("Sample quizzes added successfully")
    except Exception as e:
        logger.error(f"Failed to add sample quizzes: {str(e)}")

    # Start the Django server
    server_process = subprocess.Popen(
        [
            sys.executable,
            manage_py_path,
            "runserver",
            f"{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=src_dir,
    )

    # Wait for server to start
    max_wait_time = 10  # seconds
    start_time = time.time()
    server_started = False

    while time.time() - start_time < max_wait_time:
        if is_port_in_use(DJANGO_SERVER_PORT):
            server_started = True
            break
        time.sleep(0.5)

    if not server_started:
        stdout, stderr = server_process.communicate(timeout=1)
        logger.error(f"Django server failed to start in {max_wait_time} seconds.")
        logger.error(f"STDOUT: {stdout.decode('utf-8')}")
        logger.error(f"STDERR: {stderr.decode('utf-8')}")
        server_process.terminate()
        pytest.fail("Django server failed to start")

    logger.info(f"Django server started successfully at {DJANGO_SERVER_URL}")

    # Yield the server URL
    yield DJANGO_SERVER_URL

    # Cleanup: Shutdown the server
    logger.info("Stopping Django server")
    os.kill(server_process.pid, signal.SIGTERM)
    server_process.wait(timeout=5)
    logger.info("Django server stopped")


# --- Console Errors Fixture ---
@pytest.fixture(scope="function")
def capture_console_errors(page: Page):
    """Capture JavaScript console errors during test."""
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    yield
    if errors:
        logger.error(">>> JavaScript console errors detected during test run:")
        for i, error in enumerate(errors):
            logger.error(f"  Console Error {i+1}: {error}")
        pytest.fail(
            f"{len(errors)} JavaScript console error(s) detected. Check logs.",
            pytrace=False,
        )


# --- Tests ---


@pytest.mark.usefixtures("capture_console_errors")
def test_database_quiz_flow(page: Page, django_server):
    """
    Test that the quiz loads data from the database correctly.
    Verify the transformation from database format to frontend format works.
    """
    quiz_url = django_server

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
        correct_option = page.locator(".option-button", has_text=correct_option_text)
        correct_option.click()

        # Check that we get a "Correct!" modal
        modal_overlay = page.locator(".modal-overlay")
        expect(modal_overlay).to_be_visible(timeout=3000)
        expect(modal_overlay.locator(".modal-container.modal-correct")).to_be_visible()
        expect(modal_overlay.locator(".modal-message")).to_have_text("Correct!")

        # Close the modal
        modal_button = modal_overlay.locator(".modal-button")
        modal_button.click()
        expect(modal_overlay).to_be_hidden()

        # --- Complete the entire quiz ---
        logger.info("Completing the rest of the quiz...")

        # For each remaining question, click any option and continue
        for i in range(1, len(json_data)):
            # Wait for the question to be visible
            expect(question_text_locator).to_be_visible()

            # Click the first option
            option = page.locator(".option-button >> nth=0")
            option.click()

            # Wait for the modal and close it
            expect(modal_overlay).to_be_visible()
            modal_button.click()

            if i < len(json_data) - 1:
                # Verify we're on the next question
                expect(progress_indicator_locator).to_have_text(
                    f"{i+2}/{len(json_data)}"
                )

        # --- Test the results screen ---
        results_card = page.locator(".results-card")
        logger.info("Checking results screen...")
        expect(results_card).to_be_visible(timeout=5000)

        # Verify results title and score
        expect(results_card.locator(".results-title")).to_have_text("Quiz Completed!")
        # We don't know the exact score since we just clicked randomly, so just check format
        expect(results_card.locator(".results-score")).to_contain_text("Your Score:")
        expect(results_card.locator(".results-score")).to_contain_text(
            f"out of {len(json_data)}"
        )

        # Verify the restart button works
        restart_button = results_card.locator(".restart-button")
        expect(restart_button).to_be_visible()
        restart_button.click()

        # Verify we're back on the first question
        expect(question_text_locator).to_be_visible()
        expect(progress_indicator_locator).to_have_text(f"1/{len(json_data)}")

        logger.info("Database quiz test completed successfully!")

    except Error as e:
        logger.exception(f"Test failed: {str(e)}")
        pytest.fail(f"Test failed: {str(e)}")


@pytest.mark.usefixtures("capture_console_errors")
def test_specific_quiz_route(page: Page, django_server):
    """
    Test that we can load a specific quiz by ID.
    This should demonstrate the URL routing works correctly.
    """
    # Assuming there's at least one quiz with ID 1
    quiz_url = f"{django_server}quiz/1/"

    logger.info(f"Testing specific quiz route: {quiz_url}")
    try:
        # Go to the page
        page.goto(quiz_url, wait_until="domcontentloaded")

        # Wait for the quiz to load
        page.wait_for_selector(".option-button", state="visible", timeout=10000)

        # Verify we have quiz elements
        expect(page.locator(".question-text")).to_be_visible()
        expect(page.locator(".progress-indicator")).to_be_visible()

        logger.info("Specific quiz route test passed!")

    except Error as e:
        logger.exception(f"Specific quiz route test failed: {str(e)}")
        pytest.fail(f"Test failed: {str(e)}")
