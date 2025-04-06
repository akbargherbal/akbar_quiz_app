# Simplified Testing Guide for Django Quiz App

This guide provides clear instructions on how to test the Django Quiz App, with a simplified approach that avoids confusion.

## Types of Tests

The project uses two main testing approaches:

1. **Django Backend Tests**: Tests for models, views, utilities, and transformations
2. **Playwright Tests**: End-to-end browser tests for the user interface

## Running Backend Tests

We use Django's built-in test runner for all backend tests.

### Prerequisites

1. Ensure you have a virtual environment set up and activated
2. Make sure you're in the `src` directory

### Running the Tests

Simply run:

```bash
python manage.py test
```

This will:

- Run all tests found in the project
- Display results in the terminal
- Generate a log file at `src/logs/django_tests.log`

### Viewing Test Results

1. **Terminal Output**: The most immediate way to see if tests passed or failed
2. **Log Files**: For detailed inspection, all logs are stored in the `src/logs/` directory:
   - `django_tests.log` - Main Django test runner log
   - `test_views.log` - View-specific test logs
   - `test_models.log` - Model-specific test logs
   - Other test files have their own respective logs

### Targeting Specific Tests

To run only tests for a specific app or module:

```bash
# Run only multi_choice_quiz app tests
python manage.py test multi_choice_quiz

# Run tests for a specific file
python manage.py test multi_choice_quiz.tests.test_models

# Run a specific test class
python manage.py test multi_choice_quiz.tests.test_models.QuizModelTests

# Run a specific test method
python manage.py test multi_choice_quiz.tests.test_models.QuizModelTests.test_quiz_creation
```

## Running End-to-End Tests

The project includes Playwright end-to-end tests for testing the frontend.

### Prerequisites

1. Make sure you have installed the required dependencies:

   ```bash
   pip install -r testing_requirements.txt
   playwright install
   ```

2. The Django server must be running:
   ```bash
   python manage.py runserver
   ```

### Running the Tests

Run the E2E tests using:

```bash
python run_e2e_tests.py
```

This will:

- Run the Playwright tests against the running Django server
- Display results in the terminal
- Generate a log file at `src/logs/playwright_tests.log`

## Understanding the Test Output

When tests run successfully, you'll see output similar to:

```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.........................
----------------------------------------------------------------------
Ran 27 tests in 0.047s

OK
Destroying test database for alias 'default'...
```

Key things to look for:

- A dot `.` for each passing test
- `OK` at the end shows all tests passed
- `FAILED` appears if tests fail, with details of what went wrong

## Troubleshooting

If you encounter test failures:

1. Read the error messages in the terminal
2. Check the specific log file for the failing test in the `src/logs/` directory
3. Fix the issues in your code and run the tests again

If you're running the end-to-end tests and they fail:

1. Make sure the Django server is running on the default port (8000)
2. Check `src/logs/playwright_tests.log` for detailed error information
3. Verify that sample quiz data has been loaded into the database
