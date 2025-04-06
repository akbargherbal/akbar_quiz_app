## Comprehensive Testing Guide for the Django Quiz App

This guide provides step-by-step instructions on how to run the automated tests included in this repository. Running these tests helps ensure the application's core functionality, especially data transformations and views, works as expected.

This project uses Django's built-in testing framework along with a custom test runner (`LoggingTestRunner`) that generates detailed log files for each test run.

### Prerequisites

1.  **Git:** You need Git installed to clone the repository.
2.  **Python:** Ensure you have Python 3.x installed on your system.
3.  **Repository Cloned:** You should have already cloned this repository to your local machine.
    ```bash
    # If you haven't cloned it yet:
    # git clone <repository-url>
    # cd <repository-directory>
    ```
4.  **Virtual Environment (Highly Recommended):** To avoid conflicts with other Python projects, create and activate a virtual environment within the project directory.

    ```bash
    # Navigate to the root directory of the cloned repository
    cd path/to/akbar_quiz_app

    # Create a virtual environment (e.g., named 'venv')
    python -m venv venv

    # Activate the virtual environment:
    # On Windows (Git Bash or Cmd/PowerShell)
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

    You should see `(venv)` at the beginning of your terminal prompt.

5.  **Install Dependencies:** Install Django and any other required packages. Assuming dependencies are listed in a `requirements.txt` file (if not, you'll need to install Django manually: `pip install django`).
    ```bash
    # Ensure your virtual environment is active
    # Navigate to the directory containing requirements.txt (likely the root or src/)
    # If requirements.txt is in the root:
    # pip install -r requirements.txt
    # If it's in src/:
    # cd src
    # pip install -r requirements.txt
    # If no requirements.txt, install Django:
    # pip install django
    ```

### Running All Tests (Standard Method)

This is the recommended method as it guarantees the use of the custom logging test runner.

1.  **Navigate to the `src` Directory:** Open your terminal or command prompt, ensure your virtual environment is active, and change to the `src` directory where the `manage.py` file is located.

    ```bash
    # Example: If you are in the root 'akbar_quiz_app' directory
    cd src
    ```

2.  **Run the Test Command:** Execute the following command:
    ```bash
    python manage.py test
    ```

### Understanding the Output (Successful Run)

If all tests pass, you will see output similar to the example you provided:

```
# Custom runner starts and initializes logging
Test logging initialized. Output directed to: C:\...\akbar_quiz_app\src\multi_choice_quiz\django_tests_YYYYMMDD-HHMMSS.log
2025-04-06 16:40:13,457 - django.tests - INFO - Test logging initialized...

# Test run begins
Starting test run: ()
2025-04-06 16:40:13,458 - django.tests - INFO - Starting test run: ()

# (Optional) Logging from within specific test files might appear
# 2025-04-06 16:40:13,907 - test_views - INFO - Logging setup complete...

# Test discovery and setup
2025-04-06 16:40:13,908 - django.tests - INFO - Found 27 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).

# Test execution begins
2025-04-06 16:40:14,014 - django.tests - INFO - Running test suite with 27 test cases

# Progress indicators (one dot '.' per passing test)
...........................

----------------------------------------------------------------------
# Summary of results
Ran 27 tests in 0.047s

# Final Status: OK means all tests passed!
OK

# Custom runner logging completion
2025-04-06 16:40:14,061 - django.tests - INFO - Test suite complete. Errors: 0, Failures: 0

# Test database cleanup
Destroying test database for alias 'default'...

# Final message from runner
Test run completed. Number of failures: 0
2025-04-06 16:40:14,061 - django.tests - INFO - Test run completed. Number of failures: 0
```

**Key things to look for:**

- The final status line: `OK` indicates success.
- The number of tests run (`Ran 27 tests...` in the example).
- No `FAIL` or `ERROR` lines in the summary.

### Interpreting Failures or Errors

If a test fails (an assertion returns `False`) or encounters an error (an unexpected exception occurs), the output will change:

- Instead of dots (`.`), you might see `F` (Failure) or `E` (Error).
- The final status will be `FAILED (failures=X)` or `FAILED (errors=Y)` or a combination.
- Detailed tracebacks will be printed _before_ the summary, showing exactly where the failure or error occurred in the test code and the application code. Use these tracebacks to debug the issue.

### Checking the Log Files

The custom `LoggingTestRunner` provides detailed logs:

1.  **Main Test Log:**

    - **Location:** `src/multi_choice_quiz/`
    - **Name Pattern:** `django_tests_YYYYMMDD-HHMMSS.log` (e.g., `django_tests_20250406-164013.log`)
    - **Content:** Contains timestamped information about the test run initialization, start/end of suites, and detailed tracebacks for any errors or failures reported by the runner. This is very useful for post-mortem analysis.

2.  **Specific Test File Logs (Optional):**
    - As seen in your output, individual test files (like `test_views.py`) might implement their _own_ logging.
    - **Location:** Typically within the `src/multi_choice_quiz/tests/` directory.
    - **Name Pattern:** Varies depending on how it's set up in the test file (e.g., `test_views_YYYYMMDD-HHMMSS.log`).
    - **Content:** Contains log messages generated specifically by the code within that test file.

### Optional: Running Tests for a Specific App

If you only want to run tests for the `multi_choice_quiz` app (which is faster):

1.  Navigate to the `src` directory.
2.  Run:
    ```bash
    python manage.py test multi_choice_quiz
    ```
    The output and logging behaviour will be similar, but only tests within that specific app will be executed.
