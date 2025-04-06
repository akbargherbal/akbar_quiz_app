import pytest
from playwright.sync_api import Page, expect, Error
import logging
import os
import sys
import subprocess
import time
import socket
import signal
from urllib.parse import urlparse

# --- Constants ---
DJANGO_SERVER_PORT = 8000
DJANGO_SERVER_HOST = 'localhost'
DJANGO_SERVER_URL = f'http://{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}'

# --- Helper function to check if port is available ---
def is_port_in_use(port, host='localhost'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

# --- Logging Setup ---
# Get the directory containing this script
current_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_dir, "test_django_quiz.log")
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_formatter = logging.Formatter(log_format)

# Get or create the logger
logger = logging.getLogger("test_django_quiz")
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(log_file_path, mode="w")
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Create console handler
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

logger.info("Logging setup complete. File handler directed to: %s", log_file_path)

# --- Django Server Fixture ---
@pytest.fixture(scope="session")
def django_server():
    """Start Django development server for testing."""
    # First check if the port is already in use
    if is_port_in_use(DJANGO_SERVER_PORT):
        logger.warning(f"Port {DJANGO_SERVER_PORT} is already in use. Assuming Django server is running.")
        yield DJANGO_SERVER_URL
        return
    
    logger.info(f"Starting Django server at {DJANGO_SERVER_URL}")
    
    # Get the manage.py path
    src_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
    manage_py_path = os.path.join(src_dir, "manage.py")
    
    # Start the Django server
    server_process = subprocess.Popen(
        [sys.executable, manage_py_path, "runserver", f"{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=src_dir
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

# --- Fixture to Capture Console Errors ---
@pytest.fixture(scope="function")
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
        logger.info("Waiting for the first option button to become visible (max 10s)...")
        first_option_button_selector = ".option-button >> nth=0"
        page.wait_for_selector(first_option_button_selector, state="visible", timeout=10000)
        logger.info("First option button is visible. Quiz has loaded successfully.")
        
    except Error as e:
        logger.exception(f"FATAL: Failed to load page or find initial element.")
        pytest.fail(f"Setup failed: Could not load page or find initial element. Error: {e}")
        return
    
    # Define locators once for reuse
    question_text_locator = page.locator(".question-text")
    progress_indicator_locator = page.locator(".progress-indicator")
    modal_overlay = page.locator(".modal-overlay")
    modal_button = modal_overlay.locator(".modal-button")
    
    # --- Question 1: Capital of France ---
    logger.info("--- Testing Question 1 ---")
    try:
        logger.info("Verifying Question 1 text and progress...")
        expect(question_text_locator).to_have_text("What is the capital of France?", timeout=5000)
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
        logger.exception("Assertion failed during Question 1.")
        pytest.fail(f"Test failed during Question 1. Error: {e}")
    
    # --- Question 2: Longest River ---
    logger.info("--- Testing Question 2 ---")
    try:
        logger.info("Verifying Question 2 text and progress...")
        expect(question_text_locator).to_have_text("Which river is the longest in the world?", timeout=5000)
        expect(progress_indicator_locator).to_have_text("2/3")
        logger.info("Question 2 text and progress verified.")
        
        amazon_option = page.locator(".option-button", has_text="Amazon")
        expect(amazon_option).to_be_visible()
        logger.info("Clicking 'Amazon' option (incorrect).")
        amazon_option.click()
        
        logger.info("Verifying incorrect answer modal for Question 2...")
        expect(modal_overlay).to_be_visible()
        expect(modal_overlay.locator(".modal-container.modal-incorrect")).to_be_visible()
        expect(modal_overlay.locator(".modal-message")).to_have_text("Incorrect!")
        expect(modal_overlay.locator(".modal-explanation")).to_contain_text("The correct answer was: Nile")
        logger.info("Incorrect answer modal verified for Question 2.")
        
        logger.info("Closing modal for Question 2...")
        modal_button.click()
        expect(modal_overlay).to_be_hidden()
        
    except Error as e:
        logger.exception("Assertion failed during Question 2.")
        pytest.fail(f"Test failed during Question 2. Error: {e}")
    
    # --- Question 3: Highest Mountain ---
    logger.info("--- Testing Question 3 ---")
    try:
        logger.info("Verifying Question 3 text and progress...")
        expect(question_text_locator).to_have_text("What is the highest mountain peak in the world?", timeout=5000)
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
        logger.exception("Assertion failed during Question 3.")
        pytest.fail(f"Test failed during Question 3. Error: {e}")
    
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
        expect(results_card.locator(".results-score")).to_contain_text("Your Score: 2 out of 3")
        logger.info("Results title and score verified.")
        
        logger.info("Verifying results summary details...")
        summary_items = results_card.locator(".result-item")
        expect(summary_items).to_have_count(3)
        expect(summary_items.nth(0)).to_contain_text("✅")
        expect(summary_items.nth(0)).to_contain_text("What is the capital of France?")
        expect(summary_items.nth(1)).to_contain_text("❌")
        expect(summary_items.nth(1)).to_contain_text("Which river is the longest in the world?")
        expect(summary_items.nth(1)).to_contain_text("(Correct: Nile)")
        expect(summary_items.nth(2)).to_contain_text("✅")
        expect(summary_items.nth(2)).to_contain_text("What is the highest mountain peak in the world?")
        logger.info("Results summary details verified.")
        
        restart_button = results_card.locator(".restart-button")
        expect(restart_button).to_be_visible()
        expect(restart_button).to_have_text("Play Again?")
        logger.info("Restart button verified.")
        
    except Error as e:
        logger.exception("Assertion failed during Results Screen check.")
        pytest.fail(f"Test failed during Results Screen check. Error: {e}")
    
    # --- Test Restart ---
    logger.info("--- Testing Restart ---")
    try:
        logger.info("Clicking 'Play Again?' button...")
        restart_button = page.locator(".restart-button")
        restart_button.click()
        
        logger.info("Verifying quiz resets to Question 1...")
        expect(page.locator(".results-card")).to_be_hidden()
        expect(page.locator(".question-card")).to_be_visible(timeout=5000)
        expect(question_text_locator).to_have_text("What is the capital of France?", timeout=5000)
        expect(progress_indicator_locator).to_have_text("1/3")
        logger.info("Quiz reset to Question 1 verified.")
        
        logger.info("Verifying options are enabled after restart...")
        paris_option_after_restart = page.locator(".option-button", has_text="Paris")
        expect(paris_option_after_restart).to_be_enabled()
        logger.info("'Paris' option is enabled after restart.")
        
    except Error as e:
        logger.exception("Assertion failed during Restart check.")
        pytest.fail(f"Test failed during Restart check. Error: {e}")
    
    logger.info("--- Django Quiz Test Completed Successfully! ---")