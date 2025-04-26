# multi_choice_quiz/tests/test_mistakes_review_layout.py

import pytest
import os
import time
from playwright.sync_api import Page, expect

# --- Test Configuration ---
TARGET_QUIZ_URL = "http://127.0.0.1:8000/quiz/38/"
EXPECTED_TOTAL_QUESTIONS = 12
LARGE_VIEWPORT = {"width": 2560, "height": 1440}
SCREENSHOT_DIR = "test_results_standalone"
FAILURE_SCREENSHOT_PATH = os.path.join(
    SCREENSHOT_DIR, "mistakes_review_overflow_failure.png"
)
GENERAL_FAILURE_SCREENSHOT_PATH = os.path.join(
    SCREENSHOT_DIR, "general_test_failure.png"
)


def test_mistakes_review_overflow(page: Page):
    """
    Test if content in the Mistakes Review section overflows its container
    on large screens. Focuses on checking inner <pre> and <code> tags
    within the correct answer display.
    """
    # --- Test Setup ---
    print(
        "\n--- Starting test_mistakes_review_overflow (Standalone - Check Inner Code/Pre) ---"
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
        # (Quiz taking logic remains the same as previous version)
        for i in range(total_questions):
            current_q_num = i + 1
            print(f"Answering Question {current_q_num}/{total_questions}...")
            counter_locator = page.locator(
                f'#quiz-app-container div:has-text("{current_q_num}/{total_questions}")'
            ).first
            expect(counter_locator).to_be_visible(timeout=10000)
            first_option_button = page.locator(".option-button").nth(0)
            expect(first_option_button).to_be_visible(timeout=5000)
            expect(first_option_button).to_be_enabled(timeout=5000)
            time.sleep(0.2)  # Small pause
            first_option_button.click()
            # print(f"Clicked the first option for Question {current_q_num}.") # Reduce log noise
            if current_q_num < total_questions:
                next_q_num = current_q_num + 1
                next_counter_locator = page.locator(
                    f'#quiz-app-container div:has-text("{next_q_num}/{total_questions}")'
                ).first
                expect(next_counter_locator).to_be_visible(timeout=5000)
                # print(f"Transitioned to Question {next_q_num}.") # Reduce log noise
            else:
                print("Last question answered. Waiting for results panel...")

        # --- Verify Results and Layout ---
        print("Waiting for results panel to be visible...")
        results_panel = page.locator("#quiz-results-panel")
        results_panel.wait_for(state="visible", timeout=15000)
        print("Results panel is visible.")

        print(f"Setting viewport to: {LARGE_VIEWPORT}")
        page.set_viewport_size(LARGE_VIEWPORT)
        time.sleep(0.8)
        print("Viewport set.")

        mistakes_list = results_panel.locator(".mistakes-review-list")
        expect(mistakes_list).to_be_visible()
        print("Located mistakes review list.")

        mistake_items = mistakes_list.locator("li")
        item_count = mistake_items.count()
        print(f"Found {item_count} mistake list items.")
        no_mistakes_locator = mistakes_list.locator('li:has-text("No mistakes!")')

        if no_mistakes_locator.is_visible():
            pytest.skip("Quiz completed with no mistakes, cannot test overflow.")
        elif item_count == 0 and not no_mistakes_locator.is_visible():
            pytest.fail("Mistakes list is empty, but 'no mistakes' message not found.")

        print(
            "Checking INNER <pre> or <code> tags within mistake items for overflow..."
        )
        overflow_detected = False
        failure_details = ""

        for i in range(item_count):
            item_li = mistake_items.nth(i)
            item_container_div = item_li.locator('[data-testid="mistake-item-content"]')

            # Ensure it's a mistake item before proceeding
            if item_container_div.count() == 0:
                print(f"  Skipping Item {i+1} (likely not a mistake entry).")
                continue

            # Find potential code/pre tags *within* the correct answer part
            # Looking within the div that contains the "Correct:" text and the answer span
            answer_container = item_container_div.locator("div.text-gray-400")
            code_elements = answer_container.locator(
                "pre, code"
            )  # Target pre OR code tags
            code_element_count = code_elements.count()

            print(
                f"--- Checking Item {i+1}: Found {code_element_count} <pre>/<code> elements within answer."
            )

            if code_element_count > 0:
                for j in range(code_element_count):
                    element = code_elements.nth(j)
                    expect(element).to_be_visible()

                    dimensions = element.evaluate(
                        """
                        el => ({
                            clientWidth: el.clientWidth,
                            scrollWidth: el.scrollWidth,
                            tagName: el.tagName,
                            textContent: el.textContent.substring(0, 80) + '...' // Get text content
                        })
                    """
                    )
                    client_width = dimensions["clientWidth"]
                    scroll_width = dimensions["scrollWidth"]
                    tag_name = dimensions["tagName"]
                    element_text = dimensions["textContent"]

                    print(
                        f"  -> Checking Inner {tag_name}: clientWidth={client_width}, scrollWidth={scroll_width}"
                    )
                    # print(f"     Text: {element_text}") # Optional: print text content

                    # Check for overflow
                    if scroll_width > client_width + 1:
                        overflow_detected = True
                        failure_details = (
                            f"Overflow detected in Item {i+1} within INNER Element '{tag_name}'.\n"
                            f"  clientWidth={client_width}, scrollWidth={scroll_width}\n"
                            f"  Text Content Snippet: {element_text}\n"
                        )
                        print(f"    [FAIL] {failure_details}")
                        # Take screenshot immediately
                        print(
                            f"Saving failure screenshot to: {FAILURE_SCREENSHOT_PATH}"
                        )
                        results_bb = results_panel.bounding_box()
                        if results_bb:
                            page.screenshot(
                                path=FAILURE_SCREENSHOT_PATH,
                                full_page=False,
                                clip=results_bb,
                            )
                        else:
                            page.screenshot(
                                path=FAILURE_SCREENSHOT_PATH, full_page=True
                            )
                        break  # Stop checking elements within this item
            else:
                print(
                    f"  -> No inner <pre>/<code> tags found to check in Item {i+1}'s answer."
                )

            if overflow_detected:
                break  # Stop checking further items if overflow found in one

        # --- Final Assertion ---
        assert not overflow_detected, (
            f"INNER Content overflow detected in Mistakes Review section. Details:\n{failure_details}"
            f"Screenshot saved to {FAILURE_SCREENSHOT_PATH}"
        )

        print(
            "--- Test test_mistakes_review_overflow (Standalone - Check Inner Code/Pre) PASSED ---"
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
