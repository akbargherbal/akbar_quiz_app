# src/run_e2e_tests.py

import os
import subprocess
import sys


def main():
    """Run the Playwright E2E tests."""
    # Make sure the server is running - could use django-livereload-server
    # or subprocess to start it, but for now we'll assume it's already running

    # Set environment variables
    os.environ["RUN_E2E_TESTS"] = "1"
    os.environ["SERVER_URL"] = "http://localhost:8000"

    # Call pytest with the E2E test file
    test_file = "multi_choice_quiz/tests/test_quiz_e2e.py"
    subprocess.run([sys.executable, "-m", "pytest", test_file, "-v"])


if __name__ == "__main__":
    main()
