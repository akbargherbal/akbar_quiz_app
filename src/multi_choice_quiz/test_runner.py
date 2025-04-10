# src/multi_choice_quiz/test_runner.py

import os
import sys
import logging
from django.test.runner import DiscoverRunner
from django.conf import settings


class LoggingTestRunner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define the app-specific log directory
        app_log_dir = os.path.join(settings.BASE_DIR, "logs", "multi_choice_quiz")

        # Create the app-specific directory if it doesn't exist
        os.makedirs(app_log_dir, exist_ok=True)

        # Use fixed filename within the app-specific directory
        log_file_path = os.path.join(app_log_dir, "django_tests.log")  # Changed path

        # Configure root logger to write to the file
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file_path, mode="w"),  # Overwrite previous log
                logging.StreamHandler(sys.stdout),  # Keep console output too
            ],
        )

        self.logger = logging.getLogger("django.tests")
        self.logger.info(
            f"Test logging initialized. Output directed to: {log_file_path}"
        )

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Run tests with logging."""
        self.logger.info(f"Starting test run: {test_labels}")
        result = super().run_tests(test_labels, extra_tests=extra_tests, **kwargs)
        self.logger.info(f"Test run completed. Number of failures: {result}")
        return result

    def run_suite(self, suite, **kwargs):
        """Log the beginning and end of each test suite."""
        self.logger.info(f"Running test suite with {suite.countTestCases()} test cases")
        result = super().run_suite(suite, **kwargs)
        self.logger.info(
            f"Test suite complete. Errors: {len(result.errors)}, Failures: {len(result.failures)}"
        )

        # Log errors and failures
        if result.errors:
            self.logger.error("--- ERRORS ---")
            for test, error in result.errors:
                # Ensure test representation is string
                test_repr = getattr(test, "id", lambda: str(test))()
                self.logger.error(f"\nTest: {test_repr}\nError:\n{error}")

        if result.failures:
            self.logger.error("--- FAILURES ---")
            for test, failure in result.failures:
                # Ensure test representation is string
                test_repr = getattr(test, "id", lambda: str(test))()
                self.logger.error(f"\nTest: {test_repr}\nFailure:\n{failure}")

        return result
