### Consolidated Context for Future Sessions (QuizMaster Testing)

**(Project):** Django Quiz App ("QuizMaster")
**(Core Tech):** Django, Python, Tailwind CSS (CDN)
**(Testing Stack):** `pytest`, `pytest-django`, `pytest-playwright`

**I. Overall Project Goal (Testing):**
To establish a robust, reliable, and maintainable automated test suite that covers critical application functionality, including backend logic, API endpoints, and End-to-End (E2E) user flows. This involves refactoring existing LLM-generated tests and applying testing best practices.

**II. Historical Challenges & Key Resolutions:**

A.  **E2E Test Flakiness - Database Context & Server Management (Sessions 1-3):**
    *   **Problem:** Initial E2E tests (e.g., `pages/tests/test_responsive.py`, `pages/tests/test_templates.py`, `multi_choice_quiz/tests/test_quiz_e2e.py`) were highly unreliable. Failures often manifested as "user not found" during login or data not appearing as expected. The root cause was a mismatch between the database used by the test server and the database context for ORM operations within the tests. Custom runner scripts (`run_*.py`) or a custom `django_server` fixture started a Django server using the **development database**. In contrast, tests marked `@pytest.mark.django_db` operated on an isolated **test database**.
    *   **Resolution:**
        1.  **Standardized on `live_server`:** All E2E tests requiring server interaction with test database state were refactored to use `pytest-django`'s built-in `live_server` fixture.
        2.  **Consistent URL Usage:** All E2E test navigation (`page.goto()`) and form submissions now use `live_server.url` to ensure interaction with the correct test server.
        3.  **Removed Custom Runners/Fixtures:** Deleted all `run_*.py` scripts and the custom `django_server` fixture from `src/conftest.py`. Test execution is now solely via the `pytest` command from the `src/` directory.

B.  **E2E Test Flakiness - Assertions & Test Data (Sessions 1-3):**
    *   **Problem (Assertions):** Initial visibility assertions (e.g., `expect(...).to_be_visible()` for a "Profile" link after login) were brittle, especially in responsive tests where elements might be present but hidden (e.g., in a collapsed mobile menu).
    *   **Resolution (Assertions):** Assertions were made more robust, often by checking for the *absence* of previous state elements (e.g., `expect(login_link_locator).to_be_hidden()`).
    *   **Problem (Test Data):** Tests sometimes failed because they assumed specific data (e.g., Quiz ID 1) existed, but test databases start empty.
    *   **Resolution (Test Data):** Tests requiring specific database records now explicitly create that data using Django's ORM within the test function or via dedicated data-creation fixtures.

C.  **E2E Test Maintainability & Locators (Sessions 2-3):**
    *   **Problem (Duplication):** Admin login sequences were repeated across multiple E2E tests.
    *   **Resolution (DRY Principle):** Created a reusable `admin_logged_in_page` fixture in `src/conftest.py` to handle admin user creation and Playwright login, simplifying tests.
    *   **Problem (Brittle Locators):** Some tests used locators based on CSS classes or ambiguous text.
    *   **Resolution (Robust Locators):** Began transitioning to more robust locators, notably by adding `data-testid` attributes to navigation elements in `pages/base.html` and updating `pages/tests/test_responsive.py` to use `page.get_by_test_id()`.

D.  **Console Error Handling (Session 2):**
    *   **Problem:** The `capture_console_errors` fixture was failing tests due to benign browser console warnings (e.g., Tailwind CDN message).
    *   **Resolution:** Modified the fixture to distinguish between fatal JavaScript *page errors* (which should fail a test) and *console warnings/errors* (which are logged but don't fail the test if it otherwise passes and there are no page errors).

E.  **Backend Test Refinement (Session 4):**
    *   **Problem (Test Interference):** Identified and fixed test failures in `multi_choice_quiz/tests/test_views.py` caused by test methods within a `TestCase` class unintentionally modifying shared state created by `setUpTestData`.
    *   **Resolution (Isolation):** Refactored affected tests to create data locally within test methods where isolation was critical.
    *   **Review:** Reviewed and confirmed the stability of `core/tests/test_phase*.py` and `multi_choice_quiz/tests/test_models.py`.

F.  **Script Testing & File System Safety (Session 4 & Current):**
    *   **Problem (Mocking Complexity & Safety):** Testing `dir_import_chapter_quizzes.py` was challenging due to complex file system interactions. An early attempt at mocking led to the **accidental deletion of the project's `QUIZ_COLLECTIONS` directory**.
    *   **Resolution (Safety & Mocking):**
        1.  The `QUIZ_COLLECTIONS` directory was restored via `git reset --hard`.
        2.  The test script (`test_dir_import_chapter_quizzes.py`) was completely rewritten to:
            *   Use `tempfile.mkdtemp()` for creating isolated temporary directories for test artifacts, ensuring `tearDown` only removes these safe, temporary locations.
            *   Employ a more robust and targeted mocking strategy for `pathlib.Path` methods (`is_dir`, `glob`) using `side_effect` functions that differentiate between the script's target directory and other paths.
            *   Utilize `autospec=True` in `@patch` decorators for stricter mock signatures.
            *   Capture script log output using `self.assertLogs()` instead of patching `sys.stdout`.
        3.  These changes resulted in all tests for `dir_import_chapter_quizzes.py` passing reliably and safely.

G.  **Documentation (Session 3 & Current):**
    *   **Problem:** The `TESTING_GUIDE.md` was outdated.
    *   **Resolution:** The guide has been progressively rewritten to reflect current best practices, fixture usage, and lessons learned, including advice on script testing and file system safety.

**III. Current State & Immediate Next Steps:**

*   **Overall Stability:** The core E2E test suite and backend integration tests are significantly more stable and reliable due to consistent fixture usage, explicit data creation, and improved assertion/locator strategies. Script testing for `dir_import_chapter_quizzes.py` is now robust and safe.
*   **Code Rendering Decision:** A key decision has been made: **Questions containing multi-line code blocks (`<pre>` tags) will be excluded from the quiz data at the source/import stage.** This simplifies the problem of complex code rendering in the UI.
*   **Skipped E2E Tests:** The E2E tests `test_code_display.py` and `test_mistakes_review_*.py` (which were skipped due to previous rendering issues with `<pre>` tags) are now largely obsolete in their original intent.

*   **Immediate Plan:**
    1.  **Focused Manual Visual Verification (Inline `<code>`):**
        *   **Prepare Data:** Create a small `.pkl` file with questions/options using *only inline `<code>` elements* (no `<pre>`). Ensure some will appear in the "Mistakes Review" panel.
        *   **Load & Test:** Import this data into the development DB using `python src/dir_import_chapter_quizzes.py --import-dir`. Run `manage.py runserver`. Manually test the quiz across viewports, focusing on how inline `<code>` renders in questions and in the "Mistakes Review" panel. Check for legibility, styling consistency, and minor layout issues.
        *   **Document:** Take screenshots.
    2.  **Finalize Decision on Skipped E2E Tests:**
        *   Based on the manual verification of inline `<code>` rendering:
            *   If inline `<code>` rendering is acceptable, **the strong recommendation is to delete `test_code_display.py` and `test_mistakes_review_*.py`**. Their original purpose (handling `<pre>` tag complexities) is voided by the data exclusion policy.
            *   If minor CSS tweaks are needed for inline `<code>`, address them.
            *   Consider if a *new, very simple* E2E test to verify basic inline `<code>` presence/styling is warranted, or if manual checks and data filtering suffice.
    3.  **Update `TESTING_GUIDE.md`:** Incorporate the decision about `<pre>` tag exclusion and its impact on testing strategy.
    4.  **Broader Test Suite Review:** Proceed to evaluate remaining backend test files like `multi_choice_quiz/tests/test_utils.py`.

**IV. Synthesized Lessons Learned:**

1.  **Standardize on Framework Fixtures:** Use `live_server`, `page`, `@pytest.mark.django_db`, `client` for their intended purposes to ensure correct context and isolation.
2.  **Explicit Test Data Management:** Test databases start empty; create all necessary data within the test's scope or via fixtures.
3.  **Robust Assertions & Locators:** Assert specific outcomes. Prefer `data-testid` and user-facing attributes for locators. `to_be_hidden()` can be more robust than `to_be_visible()` for certain dynamic UI states.
4.  **DRY Principle with Fixtures:** Extract common setup (e.g., logins, complex data creation) into reusable `pytest` fixtures in `src/conftest.py`.
5.  **Use `pytest` Directly:** Avoid custom runner scripts; they often interfere with testing framework mechanisms.
6.  **Safe File System Testing:**
    *   **Always use `tempfile.mkdtemp()`** for test-generated files/directories.
    *   Ensure cleanup (`shutil.rmtree`) *only* targets these temporary locations.
    *   Use targeted mocking (`@patch` with `side_effect`, `autospec=True`) for scripts interacting with the file system to redirect their operations to safe, controlled temporary areas.
7.  **Effective Mocking:** Understand `unittest.mock` for isolating code from external dependencies (file system, APIs, `sys.argv`, `builtins.input`).
8.  **Reliable Output Capturing:** Use `self.assertLogs()` (for `TestCase`) or `caplog` (for pytest functions) to capture log output from scripts/modules under test.
9.  **Git for Safety:** Regular commits are crucial. Understand the power and risks of commands like `git reset --hard`.
10. **Data Pipeline as a Control Point:** Filtering or sanitizing data at the import stage (e.g., excluding `<pre>` tags) can simplify UI development and reduce the need for complex rendering tests. Test the data pipeline itself.
11. **Iterative Improvement:** Testing is an ongoing process of refinement. Regularly review and improve tests as the application and understanding evolve.

