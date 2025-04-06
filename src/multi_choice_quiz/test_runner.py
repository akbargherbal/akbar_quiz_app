# src/multi_choice_quiz/test_runner.py

import os
import sys
import time
import logging
from django.test.runner import DiscoverRunner


class LoggingTestRunner(DiscoverRunner):
    """Custom test runner that logs test results to a file."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up logging
        current_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_file_path = os.path.join(current_dir, f"django_tests_{timestamp}.log")

        # Configure root logger to write to the file
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file_path, mode="w"),
                logging.StreamHandler(sys.stdout),  # Keep console output too
            ],
            # Force=True might be needed if basicConfig was called elsewhere
            # force=True
        )

        self.logger = logging.getLogger("django.tests")
        self.logger.info(
            f"Test logging initialized. Output directed to: {log_file_path}"
        )

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Run tests with logging."""
        self.logger.info(f"Starting test run: {test_labels}")
        # Pass extra_tests as a keyword argument and forward **kwargs
        result = super().run_tests(
            test_labels, extra_tests=extra_tests, **kwargs
        )  # <-- CORRECTED LINE
        # Note: result is typically the number of failures (an integer)
        self.logger.info(f"Test run completed. Number of failures: {result}")
        return result

    def run_suite(self, suite, **kwargs):
        """Log the beginning and end of each test suite."""
        self.logger.info(f"Running test suite with {suite.countTestCases()} test cases")
        result = super().run_suite(
            suite, **kwargs
        )  # Pass kwargs here too for consistency
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
