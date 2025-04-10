**LLM Instruction Guide: Implementing Tests and Logging for New Django Apps**

**Objective:** Generate Django and/or Playwright tests for the new `[AppName]` app, ensuring they adhere to the established logging standards within this project for consistency and maintainability.

**Context Files & Code (Reference Implementation):**

*   Use the following code snippets and configurations as the definitive guide for implementing test logging. These represent the optimized standard derived from existing apps.

**1. Refactored Logging Utility Function:**

*   **Purpose:** This function sets up logging for individual test files/modules, directing output to the correct app-specific directory.
*   **Location:** This function should ideally reside in a shared testing utility location accessible by all apps, or if not yet centralized, the LLM should use this exact implementation logic when creating logging setup for the new app.
*   **Code:**
    ```python
    # src/multi_choice_quiz/tests/test_logging.py (or a future shared location)
    import os
    import sys
    import logging
    from django.conf import settings # Assumes settings are configured

    def setup_test_logging(logger_name: str, app_name: str):
        """
        Set up standardized logging for test files within a specific app's log directory.

        Args:
            logger_name: Name for the logger (e.g., __name__, test module name, test script name).
            app_name: The name of the Django app these tests belong to (e.g., 'pages', 'multi_choice_quiz').

        Returns:
            Configured logger instance.
        """
        # Define the app-specific log directory path
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)

        # Create the app-specific directory if it doesn't exist
        os.makedirs(app_log_dir, exist_ok=True)

        # Create a logger instance
        logger = logging.getLogger(logger_name)

        # --- Important: Clear existing handlers to prevent duplicate logs ---
        # This is crucial if this function might be called multiple times for the same logger name
        if logger.handlers:
            logger.handlers.clear()

        # Set the logging level
        logger.setLevel(logging.INFO)
        # Prevent logs from propagating to the root logger if it has handlers
        logger.propagate = False

        # Define the log file path within the app-specific directory
        # Uses the logger_name to create a specific file (e.g., test_views.log, playwright_homepage.log)
        log_file = os.path.join(app_log_dir, f"{logger_name}.log")

        # Create File Handler (overwrite mode 'w')
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setLevel(logging.INFO)

        # Create Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO) # Or match logger level

        # Create Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add Handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.info(f"Test logging initialized for '{logger_name}' in app '{app_name}'. Log file: {log_file}")

        return logger

    ```

**2. Custom Django Test Runner:**

*   **Purpose:** Shows the pattern for creating a main log file during `manage.py test` runs. The current implementation logs to an app-specific directory, but the *pattern* is the key takeaway. A project might have one global runner log or multiple app-specific ones.
*   **Location:** `src/multi_choice_quiz/test_runner.py` (as an example)
*   **Code:**
    ```python
    # src/multi_choice_quiz/test_runner.py
    import os
    import sys
    import logging
    from django.test.runner import DiscoverRunner
    from django.conf import settings

    class LoggingTestRunner(DiscoverRunner):
        """Custom test runner that logs Django test results to an app-specific file."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # --- Define the specific app this runner is logging for ---
            # NOTE: For a truly unified system, this might check which app is being tested
            # or log to a single global file. For now, it demonstrates the pattern.
            app_name = "multi_choice_quiz" # Hardcoded for this example runner
            app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)
            os.makedirs(app_log_dir, exist_ok=True)

            # Use fixed filename within the app-specific directory
            log_file_path = os.path.join(app_log_dir, "django_tests.log")

            # --- Configure Logging ---
            # Get a specific logger for the test runner itself
            self.runner_logger = logging.getLogger("django.test.runner")
            self.runner_logger.setLevel(logging.INFO)
            self.runner_logger.propagate = False # Don't send to root

            # Clear handlers if re-initializing
            if self.runner_logger.handlers:
                self.runner_logger.handlers.clear()

            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            # File Handler (overwrite)
            file_handler = logging.FileHandler(log_file_path, mode="w")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.runner_logger.addHandler(file_handler)

            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.runner_logger.addHandler(console_handler)
            # --- End Logging Config ---

            self.runner_logger.info(
                f"Django Test Runner logging initialized for app '{app_name}'. Output directed to: {log_file_path}"
            )

        def run_tests(self, test_labels, extra_tests=None, **kwargs):
            """Run tests with logging."""
            self.runner_logger.info(f"Starting test run: {test_labels}")
            result = super().run_tests(test_labels, extra_tests=extra_tests, **kwargs)
            failure_count = len(result.failures) + len(result.errors)
            self.runner_logger.info(f"Test run completed. Failures/Errors: {failure_count}")
            # Log failures/errors (implementation omitted for brevity, but exists in original)
            return result

        # run_suite can also be overridden for more granular logging if needed
    ```
*   **Activation:** Remember this is activated in `settings.py`:
    ```python
    # core/settings.py
    TEST_RUNNER = "multi_choice_quiz.test_runner.LoggingTestRunner" # Or path to the relevant runner
    ```

**3. Playwright Screenshot Handling on Failure:**

*   **Purpose:** Demonstrates how to correctly save failure screenshots within the specific app's log directory.
*   **Location:** Inside the `try...except Exception:` block within Playwright test functions (e.g., in `src/multi_choice_quiz/tests/test_quiz_e2e.py`).
*   **Code Snippet:**
    ```python
        # Inside a Playwright test function, e.g., test_feature(...)
        try:
            # ... test steps ...

        except Exception as e:
            # Define the app name for logging/screenshots
            app_name = "[AppName]" # <-- LLM MUST REPLACE THIS

            # Define the app-specific log directory for screenshots
            app_log_dir = os.path.join(settings.BASE_DIR, "logs", app_name)

            # Create the app-specific directory if it doesn't exist
            os.makedirs(app_log_dir, exist_ok=True)

            # Define the full path for the screenshot
            # Consider adding a timestamp or test name for unique screenshot files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"failure_{timestamp}.png"
            screenshot_path = os.path.join(app_log_dir, screenshot_filename)

            # Take screenshot using the new path
            # Ensure 'page' is the Playwright Page object
            try:
                 if 'page' in locals() and hasattr(page, 'screenshot'):
                     page.screenshot(path=screenshot_path)
                     logger.error(f"Screenshot saved to: {screenshot_path}")
                 else:
                     logger.error("Could not save screenshot: 'page' object not available or invalid.")
            except Exception as ss_error:
                 logger.error(f"Failed to save screenshot to {screenshot_path}: {ss_error}")


            # Log the primary error
            # Ensure 'logger' is the logger instance obtained from setup_test_logging
            if 'logger' in locals() and hasattr(logger, 'error'):
                 logger.error(f"Test failed: {str(e)}", exc_info=True) # Include traceback
            else:
                 print(f"Test failed (logger not available): {str(e)}") # Fallback print

            raise # Re-raise the original exception
    ```
    *(Note: Added timestamp to screenshot filename and improved error handling)*

---

**Instructions for Generating Tests for `[AppName]`:**

**A. Core Requirements:**

1.  **Implement Tests:** Create necessary test files (e.g., `test_views.py`, `test_models.py`, Playwright tests like `test_feature_e2e.py`) inside `src/[AppName]/tests/`.
2.  **Use Logging Utility:** At the beginning of each test file (or test class `setUpClass`), import and call the `setup_test_logging` function (shown in Context #1 above). Pass the appropriate logger name (e.g., `__name__` for module-level logging, or a specific test name) and the **correct `app_name`**: `'[AppName]'`. Assign the returned logger instance to a variable (e.g., `logger`).
    ```python
    # Example at top of src/[AppName]/tests/test_views.py
    from ..utils.test_logging import setup_test_logging # Adjust path if centralized
    # ... other imports ...

    logger = setup_test_logging(__name__, '[AppName]') # Pass correct app name

    class ViewTests(TestCase):
        # ... tests using logger.info(), logger.error() etc ...
    ```
3.  **Log Generation:** Ensure all logs generated by these tests (using the `logger` instance) appear *only* within the `src/logs/[AppName]/` directory, in files named after the logger name provided (e.g., `test_views.log`). Logs should overwrite on subsequent runs.
4.  **Django Test Runner:** No specific action needed unless you want a dedicated runner log for `[AppName]`. The global runner (if configured like the example) will likely handle the overall summary.

**B. Playwright/E2E Test Specifics:**

5.  **Implement E2E Tests:** Create Playwright test files in `src/[AppName]/tests/`.
6.  **Screenshot on Failure:** Implement the `try...except` block exactly as shown in Context #3 above within each relevant Playwright test function. **Crucially, replace `app_name = "[AppName]"`** with the actual name of the app you are generating tests for.
7.  **Create E2E Runner Script:** Create a *new script* `src/run_[AppName]_e2e_tests.py`. This script must:
    *   Check if the Django server is running (port 8000) and start it if needed (reuse logic from other runners).
    *   Run any app-specific setup commands for `[AppName]` (e.g., migrations, data loading).
    *   Set environment variables: `RUN_E2E_TESTS=1`, `SERVER_URL='http://localhost:8000'`.
    *   Execute `pytest` targeting *only* the Playwright test file(s) within `src/[AppName]/tests/`. Example: `pytest [AppName]/tests/test_feature_e2e.py -v`.

**C. Documentation:**

8.  **Update `TESTING_GUIDE.md`:** Add/modify sections to explain:
    *   The log location for the new app: `src/logs/[AppName]/`.
    *   How to run the Django tests for the app: `python manage.py test [AppName]`.
    *   How to run the E2E tests for the app: `python src/run_[AppName]_e2e_tests.py`.

**Final Goal:** The testing setup for `[AppName]` should mirror the functionality and logging structure demonstrated in the context files, ensuring isolated and informative logs are generated within `src/logs/[AppName]/`.