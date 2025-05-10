"""Helper functions and utilities for testing."""
import logging
# Import the standardized logging function
# Attempt to import test-specific logging, fall back if not found (e.g., in production)
try:
    from multi_choice_quiz.tests.test_logging import setup_test_logging
    # Assuming setup_test_logging returns a logger instance or configures the root logger.
    # If it configures a specific logger, you might want to get it by name here.
    # For example, if setup_test_logging configures a logger named 'pages.views':
    # setup_test_logging(__name__, "your_log_file_for_pages_views.log") # If it configures and you get it later
    logger = logging.getLogger(__name__) # Get the logger for the current module
    # If setup_test_logging directly returns the logger:
    # logger = setup_test_logging(__name__, "your_log_file_for_pages_views.log")
    logger.info("Successfully initialized test-specific logging for pages.views.")

except (ImportError, ModuleNotFoundError):
    # Fallback to standard logging if the test module isn't found
    logger = logging.getLogger(__name__)
    logger.info("Test logging module not found. Using standard logging for pages.views.")


# All other helper functions can remain here
# Any code that used the old setup_test_logging should now use the imported version
