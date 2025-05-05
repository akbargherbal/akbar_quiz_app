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

Or:

```bash
pytest src/app_one/tests/test_views.py::TestClassName::test_specific_view_test
```

**5. Useful Pytest Options:** `-v`, `-s`, `-x`, `-m MARKER`.

---

**!! Anti-Pattern Warning !!**

- **Avoid `python manage.py test`:** While Django's default runner works for basic tests, it doesn't integrate as seamlessly with `pytest` fixtures (especially Playwright) and configuration. Stick to the `pytest` command.
- **Avoid Custom Runner Scripts:** Do not use separate Python scripts (`run_*.py`) to manage server startup or test execution. These often bypass `pytest-django`'s test database isolation, leading to hard-to-debug failures. Let `pytest` and its fixtures manage the test lifecycle.

---

## Key Concepts & Fixtures

- **Test Database:** `pytest-django` manages isolated test databases for tests marked `@pytest.mark.django_db`. **Required** for ORM/DB interaction.
- **`client` (Fixture):** For backend/integration tests (simulates requests). Use `def test_view(client):`.
- **`live_server` (Fixture):** For E2E tests needing DB state. Starts a **real server** on the **test database**. Access URL via `live_server.url`.
  - **!! Critical !! Use `live_server.url` for `page.goto()` in E2E tests.**
  - **!! Anti-Pattern Warning !!** Do not manually start `manage.py runserver` for tests. Do not use hardcoded URLs like `http://localhost:8000` or environment variables pointing to the development server in your tests. This _will_ cause database context mismatches and test failures.
- **`page` (Fixture):** For E2E tests. Provides a Playwright browser page. Use `def test_e2e(page, ...):`.
- **Custom Fixtures (`src/conftest.py`):** Define reusable setup (e.g., user creation, login).
  - **Benefit:** Reduces code duplication and improves maintainability.
  - **!! Anti-Pattern Warning !!** Avoid writing complex, repeated setup logic (like multi-step form filling or login sequences) directly inside multiple test functions. Extract it into a fixture.
- **`data-testid` Attribute:** Add `data-testid="your-unique-id"` to HTML for stable E2E locators. Use with `page.get_by_test_id("your-unique-id")`.
  - **Benefit:** Makes tests resilient to UI changes.
  - **!! Anti-Pattern Warning !!** Avoid relying heavily on CSS class selectors (especially utility classes like Tailwind's) or `:has-text` for locating elements in E2E tests, as these are brittle and prone to breaking.

## Test Types & Recommended Fixtures

- **Unit Tests (Models, Utils):** `@pytest.mark.django_db` (if ORM needed).
- **Integration Tests (Views, Forms):** `@pytest.mark.django_db`, `client`.
- **E2E / Browser Tests:**
  - Always: `page`.
  - If interacting with DB state: `@pytest.mark.django_db`, `live_server`.
  - If needs login state: Custom login fixture or perform login steps using `page` **and `live_server.url`**.

## Diagnostics & Troubleshooting

1.  **Pytest Output:** Check terminal errors/tracebacks. Use `-v -s`.
2.  **Browser Console Logs (E2E):** Check configured log files (e.g., `src/logs/e2e/js_console_errors.log`).
3.  **Failure Screenshots (E2E):** Check test output/code for save location (e.g., `src/screenshots/`).
4.  **Common Issues & Anti-Patterns:**
    - **DB Context (E2E):** Using hardcoded URLs? Missing `live_server` fixture? Test uses `live_server` but navigates via `localhost:8000`?
    **Fix:** Use `live_server.url` consistently.
    - **Missing Data:** Test DB is empty. Create needed data within the test/fixture using ORM calls.
    - **Auth Failures (E2E):** Login not using `live_server.url`? Using brittle verification after login?
    **Fix:** Use fixtures; verify by checking for _absence_ of logged-out elements (`to_be_hidden`).
    - **Locator Failures:** Using CSS classes or `:has-text`?
    **Fix:** Use `data-testid` or robust roles/IDs. Check for strict mode violations (multiple elements found).
    - **Flaky Tests:** Often caused by timing issues or race conditions. Use `expect()` assertions for their built-in waits. Avoid long `page.wait_for_timeout()`.
