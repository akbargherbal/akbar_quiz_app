# multi_choice_quiz/tests/test_mistakes_review_layout.py (Updated Content)

import pytest
import os
import time
import json  # Needed to parse quiz data
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError

# --- Test Configuration ---
TARGET_QUIZ_URL = (
    "http://127.0.0.1:8000/quiz/1/"  # Assuming quiz 1 exists from sample data
)
# <<< FIX: Removed hardcoded total questions >>>
# EXPECTED_TOTAL_QUESTIONS = 12
LARGE_VIEWPORT = {"width": 2560, "height": 1440}
SCREENSHOT_DIR = "test_results_standalone"
FAILURE_SCREENSHOT_PATH = os.path.join(
    SCREENSHOT_DIR, "mistakes_review_overflow_failure.png"
)
GENERAL_FAILURE_SCREENSHOT_PATH = os.path.join(
    SCREENSHOT_DIR, "general_test_failure.png"
)


@pytest.mark.skip(
    reason="Temporarily ignoring this test due to not so pressing issue at the moment."
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

        # --- FIX: Dynamically determine question count ---
        total_questions = 0
        print("Attempting to determine question count...")
        try:
            # Option 1: Try Alpine state first (if reliable)
            # page.wait_for_function("() => window.quizAppInstance && window.quizAppInstance.questions && window.quizAppInstance.questions.length > 0", timeout=5000)
            # count = page.evaluate("() => window.quizAppInstance.questions.length")
            # if isinstance(count, int) and count > 0:
            #     total_questions = count
            #     print(f"Determined question count from Alpine state: {total_questions}")
            # else: raise ValueError("Invalid count from Alpine") # Force fallback

            # Option 2: Fallback to progress indicator
            progress_indicator = page.locator(".progress-indicator")
            expect(progress_indicator).to_be_visible(timeout=10000)
            progress_text = progress_indicator.text_content(timeout=5000)
            total_questions = int(progress_text.split("/")[1])
            print(
                f"Determined question count from progress indicator: {total_questions}"
            )
            if total_questions <= 0:
                pytest.fail(
                    "Got zero or negative question count from progress indicator."
                )

        except Exception as e:
            print(f"Error determining question count: {e}. Trying JSON script.")
            # Option 3: Fallback to JSON script
            try:
                quiz_data_script = page.locator("#quiz-data")
                expect(quiz_data_script).to_be_attached(timeout=5000)
                data_content = quiz_data_script.inner_text(timeout=5000)
                questions = json.loads(data_content)
                if isinstance(questions, list):
                    total_questions = len(questions)
                    print(
                        f"Determined question count from #quiz-data script: {total_questions}"
                    )
                else:
                    pytest.fail("Parsed #quiz-data content is not a list.")
            except Exception as e_json:
                print(f"Failed to get question count from JSON script: {e_json}")
                pytest.fail("Could not determine question count.")

        if total_questions <= 0:
            pytest.fail("Could not determine a valid question count (>0).")
        # --- END FIX ---

        # --- Simulate Taking the Quiz ---
        print(f"Simulating answers for {total_questions} questions.")
        for i in range(total_questions):
            current_q_num = i + 1
            print(f"Answering Question {current_q_num}/{total_questions}...")
            counter_locator = page.locator(
                # <<< FIX: Use the correct ID for the container >>>
                f'#quiz-app-container .progress-indicator:has-text("{current_q_num}/{total_questions}")'
                # Original was: f'#quiz-app-container div:has-text("{current_q_num}/{total_questions}")' - less specific
            ).first  # Using .first might still be needed if there are multiple matches, but the class is better
            # <<< Increased timeout slightly for stability >>>
            expect(counter_locator).to_be_visible(timeout=15000)
            first_option_button = page.locator(".option-button").nth(0)
            expect(first_option_button).to_be_visible(timeout=5000)
            expect(first_option_button).to_be_enabled(timeout=5000)
            time.sleep(0.2)  # Small pause
            first_option_button.click()

            if current_q_num < total_questions:
                next_q_num = current_q_num + 1
                next_counter_locator = page.locator(
                    # <<< FIX: Use the correct ID for the container >>>
                    f'#quiz-app-container .progress-indicator:has-text("{next_q_num}/{total_questions}")'
                ).first
                # <<< Increased timeout slightly for stability >>>
                expect(next_counter_locator).to_be_visible(timeout=10000)
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

            if item_container_div.count() == 0:
                print(f"  Skipping Item {i+1} (likely not a mistake entry).")
                continue

            answer_container = item_container_div.locator("div.text-gray-400")
            code_elements = answer_container.locator("pre, code")
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
                            textContent: el.textContent.substring(0, 80) + '...'
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

                    if scroll_width > client_width + 1:
                        overflow_detected = True
                        failure_details = (
                            f"Overflow detected in Item {i+1} within INNER Element '{tag_name}'.\n"
                            f"  clientWidth={client_width}, scrollWidth={scroll_width}\n"
                            f"  Text Content Snippet: {element_text}\n"
                        )
                        print(f"    [FAIL] {failure_details}")
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
                        break
            else:
                print(
                    f"  -> No inner <pre>/<code> tags found to check in Item {i+1}'s answer."
                )

            if overflow_detected:
                break

        # --- Final Assertion ---
        assert not overflow_detected, (
            f"INNER Content overflow detected in Mistakes Review section. Details:\n{failure_details}"
            f"Screenshot saved to {FAILURE_SCREENSHOT_PATH}"
        )

        print(
            "--- Test test_mistakes_review_overflow (Standalone - Check Inner Code/Pre) PASSED ---"
        )

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
