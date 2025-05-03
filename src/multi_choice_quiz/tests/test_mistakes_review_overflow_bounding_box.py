# multi_choice_quiz/tests/test_mistakes_review_layout.py

import pytest
import os
import time
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError


# --- Test Configuration ---
TARGET_QUIZ_URL = "http://127.0.0.1:8000/quiz/1/"
EXPECTED_TOTAL_QUESTIONS = 12
LARGE_VIEWPORT = {"width": 2560, "height": 1440}  # Keep wide viewport
SCREENSHOT_DIR = "test_results_standalone"
FAILURE_SCREENSHOT_PATH = os.path.join(
    SCREENSHOT_DIR, "mistakes_review_overflow_failure.png"
)
GENERAL_FAILURE_SCREENSHOT_PATH = os.path.join(
    SCREENSHOT_DIR, "general_test_failure.png"
)
# *** Question known to have a <pre> block in its correct answer ***
PRE_BLOCK_QUESTION_TEXT_SNIPPET = "subclass Django's UserCreationForm"  # Q7 text


def test_mistakes_review_overflow_bounding_box(page: Page):
    """
    Test if content (specifically <pre> blocks) in the Mistakes Review
    section visually overflows its container's bounding box on large screens.
    """
    # --- Test Setup ---
    print(
        "\n--- Starting test_mistakes_review_overflow (Standalone - Bounding Box Check) ---"
    )
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    print(f"Screenshots will be saved in: {os.path.abspath(SCREENSHOT_DIR)}")
    logs = []
    page.on(
        "console", lambda msg: logs.append(f"BROWSER CONSOLE [{msg.type}]: {msg.text}")
    )
    print("Attached console log listener.")

    try:
        print(f"Navigating to target quiz: {TARGET_QUIZ_URL}")
        page.goto(TARGET_QUIZ_URL, wait_until="domcontentloaded")
        print("Initial navigation complete. Waiting for quiz elements...")
        page.locator("#quiz-app-container").wait_for(state="visible", timeout=15000)
        page.locator(".option-button").first.wait_for(state="visible", timeout=15000)
        print("Quiz app container and first option loaded.")

        # --- Simulate Taking the Quiz ---
        total_questions = EXPECTED_TOTAL_QUESTIONS
        print(f"Simulating answers for {total_questions} questions.")
        # (Quiz taking logic - shortened logs)
        for i in range(total_questions):
            current_q_num = i + 1
            # print(f"Answering Question {current_q_num}/{total_questions}...") # Less verbose
            counter_locator = page.locator(
                f'#quiz-app-container div:has-text("{current_q_num}/{total_questions}")'
            ).first
            expect(counter_locator).to_be_visible(timeout=10000)
            first_option_button = page.locator(".option-button").nth(0)
            expect(first_option_button).to_be_visible(timeout=5000)
            expect(first_option_button).to_be_enabled(timeout=5000)
            time.sleep(0.2)
            first_option_button.click()
            if current_q_num < total_questions:
                next_q_num = current_q_num + 1
                next_counter_locator = page.locator(
                    f'#quiz-app-container div:has-text("{next_q_num}/{total_questions}")'
                ).first
                expect(next_counter_locator).to_be_visible(timeout=5000)
            else:
                print("Last question answered. Waiting for results panel...")

        # --- Verify Results and Layout ---
        print("Waiting for results panel to be visible...")
        results_panel = page.locator("#quiz-results-panel")
        results_panel.wait_for(state="visible", timeout=15000)
        print("Results panel is visible.")

        print(f"Setting viewport to: {LARGE_VIEWPORT}")
        page.set_viewport_size(LARGE_VIEWPORT)
        time.sleep(0.8)  # Wait for reflow
        print("Viewport set.")

        mistakes_list = results_panel.locator(".mistakes-review-list")
        expect(mistakes_list).to_be_visible()
        print("Located mistakes review list.")

        # --- Locate the specific mistake item containing the <pre> block ---
        # Find the list item based on known question text
        print(
            f"Looking for mistake item containing text: '{PRE_BLOCK_QUESTION_TEXT_SNIPPET}'"
        )
        # This locator finds an `li` that contains a `div` which contains the snippet
        target_mistake_li = mistakes_list.locator(
            f"li:has(div:has-text('{PRE_BLOCK_QUESTION_TEXT_SNIPPET}'))"
        )

        try:
            target_mistake_li.wait_for(state="visible", timeout=5000)
            print("Found target mistake list item (Q7).")
        except PlaywrightTimeoutError:
            pytest.skip(
                f"Could not find the specific mistake item for '{PRE_BLOCK_QUESTION_TEXT_SNIPPET}'. "
                f"Was the question answered incorrectly?"
            )

        # Locate the <pre> tag within this specific list item's answer section
        pre_element = target_mistake_li.locator(
            'div[data-testid="mistake-item-content"] div.text-gray-400 pre'
        )
        expect(pre_element).to_be_visible()
        print("Located <pre> element within the target mistake item.")

        # Locate the container div for comparison
        container_div = target_mistake_li.locator(
            'div[data-testid="mistake-item-content"]'
        )
        expect(container_div).to_be_visible()
        print("Located container div for the target mistake item.")

        # --- Perform Bounding Box Comparison ---
        print("Getting bounding boxes...")
        # It's crucial that the elements are fully scrolled into view if necessary
        # For this layout, they should be, but add scroll_if_needed=True just in case
        pre_box = pre_element.bounding_box(timeout=5000)
        container_box = container_div.bounding_box(timeout=5000)

        if not pre_box:
            pytest.fail("Could not get bounding box for the <pre> element.")
        if not container_box:
            pytest.fail("Could not get bounding box for the container div.")

        print(
            f"  Pre Element Box: x={pre_box['x']:.1f}, y={pre_box['y']:.1f}, width={pre_box['width']:.1f}, height={pre_box['height']:.1f}"
        )
        print(
            f"  Container Div Box: x={container_box['x']:.1f}, y={container_box['y']:.1f}, width={container_box['width']:.1f}, height={container_box['height']:.1f}"
        )

        # Calculate right edges
        pre_right_edge = pre_box["x"] + pre_box["width"]
        container_right_edge = container_box["x"] + container_box["width"]
        print(
            f"  Calculated Right Edges: Pre={pre_right_edge:.1f}, Container={container_right_edge:.1f}"
        )

        # Assertion: Pre's right edge should be <= container's right edge (allow tolerance)
        tolerance = 1.0  # pixels
        overflow_detected = pre_right_edge > container_right_edge + tolerance
        failure_details = ""

        if overflow_detected:
            failure_details = (
                f"Visual Overflow Detected! <pre> element's right edge ({pre_right_edge:.1f}) "
                f"extends beyond container div's right edge ({container_right_edge:.1f}) "
                f"by more than {tolerance}px."
            )
            print(f"  [FAIL] {failure_details}")
            print(f"Saving failure screenshot to: {FAILURE_SCREENSHOT_PATH}")
            results_bb = results_panel.bounding_box()
            if results_bb:
                page.screenshot(
                    path=FAILURE_SCREENSHOT_PATH, full_page=False, clip=results_bb
                )
            else:
                page.screenshot(path=FAILURE_SCREENSHOT_PATH, full_page=True)

        # --- Final Assertion ---
        assert not overflow_detected, (
            f"Bounding box check failed. {failure_details}\n"
            f"Screenshot saved to {FAILURE_SCREENSHOT_PATH}"
        )

        print(
            "--- Test test_mistakes_review_overflow (Standalone - Bounding Box Check) PASSED ---"
        )

    # (Exception and Finally blocks remain the same)
    except Exception as e:
        print(f"\n--- Test failed with exception: {e} ---")
        print("\n--- Browser Console Logs ---")
        for log in logs:
            print(log)
        print("--------------------------\n")
        print(
            f"Saving general failure screenshot to: {GENERAL_FAILURE_SCREENSHOT_PATH}"
        )
        page.screenshot(path=GENERAL_FAILURE_SCREENSHOT_PATH, full_page=True)
        raise

    finally:
        print("\n--- Browser Console Logs (End of Test) ---")
        for log in logs:
            print(log)
        print("----------------------------------------\n")
