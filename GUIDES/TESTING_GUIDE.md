# Testing Guide: Django Project (Pytest Standard)

This guide outlines recommended practices for running automated tests in a Django project structured with a `src/` root, using `pytest` and common testing plugins. **It emphasizes using `pytest` directly and avoiding patterns that lead to flaky or unreliable tests.**

## Assumed Project Structure

```
project_root/
└── src/
    ├── core/                 # Contains settings.py, root urls.py, etc.
    ├── app_one/              # Django app
    │   ├── tests/
    │   │   └── test_*.py
    │   └── ...
    ├── app_two/              # Another Django app
    │   ├── tests/
    │   │   └── test_*.py
    │   └── ...
    ├── manage.py
    ├── pytest.ini            # Pytest configuration here
    ├── conftest.py           # Project-level fixtures (optional)
    ├── requirements.txt
    ├── test_requirements.txt # Or however test deps are listed
    ├── logs/                 # Directory for test logs (auto-generated)
    └── screenshots/          # Directory for E2E failure screenshots (auto-generated)

```

## Core Testing Stack

Ensure these are in your test requirements:

- **`pytest`**: The test runner.
- **`pytest-django`**: Django integration (test DB, `client`, `live_server`).
- **`pytest-playwright`**: Browser/E2E testing (`page` fixture).
- **`playwright`**: Browser automation library.
- **`unittest.mock`**: (Part of Python's standard library) For mocking external dependencies in tests.

## Initial Setup

1.  **Activate Virtual Environment.**
2.  **Install Dependencies:** `pip install -r requirements.txt && pip install -r test_requirements.txt` (Adjust).
3.  **Install Playwright Browsers:** `playwright install` (run once).
4.  **Configure `src/pytest.ini`:**
    ```ini
    [pytest]
    DJANGO_SETTINGS_MODULE = core.settings # Point to your core settings
    python_files = test_*.py tests.py *_test.py test.py
    # Optional: Define custom markers
    # markers =
    #     slow: Mark test as slow.
    ```

## Running Tests with Pytest (Recommended Approach)

**Always run `pytest` commands from the `src/` directory.** This is the standard way to leverage all integrated features and fixtures.

**1. Running All Tests:**

```bash
pytest
```

**2. Running Tests for a Specific App:**

```bash
pytest src/app_one/
```

**3. Running Tests in a Specific File:**

```bash
pytest src/app_one/tests/test_views.py
```

**4. Running a Specific Test Function:**

```bash
pytest -k specific_view_test
```

Or (for `TestCase` methods or specific pytest functions):

```bash
pytest src/app_one/tests/test_views.py::TestClassName::test_specific_view_test
```

**5. Useful Pytest Options:** `-v` (verbose), `-s` (show print statements), `-x` (stop on first failure), `-m MARKER` (run tests with a specific marker).

---

**!! Anti-Pattern Warning !!**

- **Avoid `python manage.py test`:** While Django's default runner works for basic tests, it doesn't integrate as seamlessly with `pytest` fixtures (especially Playwright) and configuration. Stick to the `pytest` command.
- **Avoid Custom Runner Scripts:** Do not use separate Python scripts (`run_*.py`) to manage server startup or test execution. These often bypass `pytest-django`'s test database isolation, leading to hard-to-debug failures. Let `pytest` and its fixtures manage the test lifecycle.

---

## Key Concepts & Fixtures

- **Test Database:** `pytest-django` manages isolated test databases for tests marked `@pytest.mark.django_db`. **Required** for ORM/DB interaction.
- **`client` (Fixture):** For backend/integration tests (simulates requests without a browser). Use `def test_view(client):`. Provided by `pytest-django`.
- **`live_server` (Fixture):** For E2E tests needing DB state. Starts a **real Django server** on a dynamic port, connected to the **test database**. Access URL via `live_server.url`.
  - **!! Critical !! Use `live_server.url` for `page.goto()` in E2E tests.**
  - **!! Anti-Pattern Warning !!** Do not manually start `manage.py runserver` for tests. Do not use hardcoded URLs like `http://localhost:8000` or environment variables pointing to the development server in your tests. This _will_ cause database context mismatches and test failures.
- **`page` (Fixture):** For E2E tests. Provides a Playwright browser page. Use `def test_e2e(page, ...):`. Provided by `pytest-playwright`.
- **Custom Fixtures (`src/conftest.py`):** Define reusable setup (e.g., user creation, admin login sequences).
  - **Benefit:** Reduces code duplication and improves maintainability.
  - **!! Anti-Pattern Warning !!** Avoid writing complex, repeated setup logic (like multi-step form filling or login sequences) directly inside multiple test functions. Extract it into a fixture.
- **`data-testid` Attribute:** Add `data-testid="your-unique-id"` to HTML for stable E2E locators. Use with `page.get_by_test_id("your-unique-id")`.
  - **Benefit:** Makes tests resilient to UI changes.
  - **!! Anti-Pattern Warning !!** Avoid relying heavily on CSS class selectors (especially utility classes like Tailwind's) or `:has-text` for locating elements in E2E tests, as these are brittle and prone to breaking.
- **Mocking External Dependencies (`unittest.mock`):** For tests that involve code interacting with external systems (file system, APIs, external libraries), Python's built-in `unittest.mock.patch` is essential. This allows you to replace parts of the system your code uses with mock objects, controlling their behavior and isolating your test from actual external interactions. This is particularly important for utility scripts and management commands.

## Test Types & Recommended Fixtures/Approaches

- **Unit Tests (Models, Utils not needing Django context):** No special Django fixtures usually needed. Focus on pure Python logic.
- **Unit/Integration Tests (Models, Utils, Forms needing DB/Django context):**
    - `@pytest.mark.django_db` (if ORM/DB needed).
    - `TestCase` from `django.test` can also be used if preferred for Django-specific assertions and structure, and `pytest` will run these tests too.
- **Integration Tests (Views, API Endpoints - no browser):**
    - `@pytest.mark.django_db`.
    - `client` (or `admin_client`) from `pytest-django` (or `django.test.Client` within `TestCase`).
- **E2E / Browser Tests:**
    - Always: `page` (from `pytest-playwright`).
    - If interacting with DB state via the server: `@pytest.mark.django_db`, `live_server`.
    - If needs login state: Custom login fixture (e.g., `admin_logged_in_page`) or perform login steps using `page` **and `live_server.url`**.
- **Utility Scripts & Management Commands:**
  - **Invocation:** Often tested by importing the script/command module and calling its main function (e.g., `main()`) or `handle()` method directly.
  - **Argument Simulation:** Use `unittest.mock.patch.object(sys, 'argv', ...)` to simulate command-line arguments.
  - **Input Simulation:** Use `unittest.mock.patch('builtins.input', ...)` to simulate user input.
  - **Dependency Mocking:** Heavily rely on `unittest.mock.patch` to mock file system operations, API calls, or other external interactions. (See "Safe File System Interactions" below).
  - **Output/Log Capturing:** For `unittest.TestCase`-based tests, use `self.assertLogs('logger_name', level='INFO')` to capture log output from the script. For `pytest`-style tests, explore the `caplog` fixture.
  - **Database:** Use `@pytest.mark.django_db` if the script interacts with the Django ORM.

## Best Practices & Advanced Topics

### Robust Locators (E2E)

- **Prefer `data-testid`:** Add `data-testid="your-unique-id"` to HTML elements. Use `page.get_by_test_id("your-unique-id")`. This is the most resilient to style/structure changes.
- **User-Facing Attributes:** Use `page.get_by_role()`, `page.get_by_label()`, `page.get_by_placeholder()`, `page.get_by_text()` where appropriate.
- **Avoid Brittle Selectors:** Minimize reliance on complex CSS paths or auto-generated class names (like many Tailwind classes). Avoid overly broad text matches (`:has-text("Submit")` if there are many submit buttons).

### Assertions

- **Assert Specific Outcomes:** Don't just check for 200 status codes. Verify content, state changes in the DB, or UI changes.
- **Visibility in E2E:** Be mindful of responsive design. An element might be "present" but not "visible" due to CSS (e.g., in a collapsed mobile menu). Assert visibility within the correct context.
- **Absence of Elements:** Sometimes, it's more robust to assert that an old state/element is *no longer* present/visible (e.g., login link `to_be_hidden()` after successful login).

### Waits & Timeouts (E2E)

- **Use Playwright's Auto-Waiting:** `expect()` assertions have built-in auto-waiting.
- **Explicit Waits:** Use `page.wait_for_load_state()`, `page.wait_for_url()`, `page.wait_for_selector()` when necessary.
- **Avoid `page.wait_for_timeout()`:** Use this sparingly, only as a last resort for debugging or specific known timing issues. Over-reliance can lead to flaky or slow tests.

### Safe File System Interactions in Tests

**!! Critical Warning !!** Tests interacting with the file system require extreme care to avoid accidentally modifying or deleting real project files or system directories.

1.  **Isolate Test Artifacts:**
    *   **Always** use Python's `tempfile` module (e.g., `tempfile.mkdtemp()`) to create unique, isolated temporary directories for each test run or test class that needs to read/write files.
    *   Conduct all test-related file operations *within* this temporary directory.

2.  **Careful Cleanup (`tearDown`, `addfinalizer`):**
    *   When cleaning up temporary directories (e.g., in `tearDown` for `TestCase` or using `request.addfinalizer` in pytest fixtures), use `shutil.rmtree(self.temporary_directory_path)`.
    *   **Crucially, ensure the path passed to `shutil.rmtree` is *always* the one created by `tempfile.mkdtemp()`** and not a hardcoded or project-relative path that could be misinterpreted.
    *   Verify the temporary directory exists before attempting to remove it.

3.  **Targeted Mocking for Scripts:**
    *   When testing scripts that operate on specific project directories (like `QUIZ_COLLECTIONS`):
        *   Identify the exact absolute path the script will calculate and attempt to use.
        *   Use `unittest.mock.patch` to intercept file system calls (`Path.is_dir`, `Path.glob`, `os.path.exists`, etc.) made by the script.
        *   Use a `side_effect` function on the mock to check if the call targets the script's intended real path.
            *   If it does, redirect the operation to act on your *safe, temporary, mock-controlled directory*.
            *   If it does not, allow the original method to proceed (so the script can, for example, still find its own `__file__` location).
    *   Employ `autospec=True` with `@patch` to ensure mock signatures align with the real objects, helping to catch errors in how mocks are called or how `side_effect` functions are defined.

4.  **Never Hardcode Project Paths for Deletion:** Avoid `shutil.rmtree("project_data_dir")` or similar in tests.

## Diagnostics & Troubleshooting

1.  **Pytest Output:** Check terminal errors/tracebacks. Use `-v -s`.
2.  **Browser Console Logs (E2E):** Check configured log files (e.g., `src/logs/e2e/js_console_errors.log` or as configured by `capture_console_errors` fixture).
3.  **Failure Screenshots (E2E):** Check test output/code for save location (e.g., `src/screenshots/`).
4.  **Mock Call Assertions:** When using mocks, use assertions like `mock_object.assert_called_once_with(...)` to verify they were used as expected.
5.  **Common Issues & Anti-Patterns:**
    - **DB Context (E2E):** Using hardcoded URLs? Missing `live_server` fixture? Test uses `live_server` but navigates via `localhost:8000`?
    **Fix:** Use `live_server.url` consistently.
    - **Missing Test Data:** Test DB is empty. Create needed data within the test/fixture using ORM calls.
    - **Auth Failures (E2E):** Login not using `live_server.url`? Using brittle verification after login?
    **Fix:** Use fixtures; verify by checking for _absence_ of logged-out elements (`to_be_hidden`).
    - **Locator Failures:** Using CSS classes or `:has-text` too broadly?
    **Fix:** Use `data-testid` or robust roles/IDs. Check for strict mode violations (multiple elements found).
    - **Flaky Tests:** Often caused by timing issues or race conditions. Use `expect()` assertions for their built-in waits. Avoid long `page.wait_for_timeout()`.
    - **Script Test Mocking:** Script interacting with real file system instead of mocks? Mocks not correctly intercepting calls? Output not captured?
    **Fix:** Review mock targets, `side_effect` logic, and output capturing (`self.assertLogs`).

