# src/run_e2e_tests.py

import os
import subprocess
import sys
import time
import socket


def is_port_in_use(port, host="localhost"):
    """Check if a port is in use on the specified host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def ensure_server_running():
    """Ensure the Django development server is running."""
    server_port = 8000
    server_host = "localhost"

    # Check if the server is already running
    if is_port_in_use(server_port, server_host):
        print(f"Server already running at http://{server_host}:{server_port}")
        return True

    # If not, start the server
    print(f"Starting Django server at http://{server_host}:{server_port}")

    # Start the server in a separate process
    server_process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"{server_host}:{server_port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to start
    max_wait_time = 10  # seconds
    start_time = time.time()
    server_started = False

    while time.time() - start_time < max_wait_time:
        if is_port_in_use(server_port, server_host):
            server_started = True
            break
        time.sleep(0.5)

    if not server_started:
        stdout, stderr = server_process.communicate(timeout=1)
        print(f"ERROR: Django server failed to start in {max_wait_time} seconds.")
        print(f"STDOUT: {stdout.decode('utf-8')}")
        print(f"STDERR: {stderr.decode('utf-8')}")
        server_process.terminate()
        return False

    print("Django server started successfully")
    return True


def ensure_sample_data():
    """Ensure sample quiz data is loaded."""
    print("Checking/adding sample quiz data...")
    try:
        # Call the management command to add sample quizzes
        # This is safe to run multiple times as it checks if data exists first
        subprocess.run([sys.executable, "manage.py", "add_sample_quizzes"], check=True)
        print("Sample data check completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to add sample quizzes: {e}")
        return False


def main():
    """Run the Playwright E2E tests."""
    # Ensure we're in the src directory
    if not os.path.exists("manage.py"):
        print("ERROR: This script must be run from the src directory")
        return 1

    # First ensure sample data is available
    if not ensure_sample_data():
        return 1

    # Make sure the server is running
    if not ensure_server_running():
        return 1

    # Set environment variables
    os.environ["RUN_E2E_TESTS"] = "1"
    os.environ["SERVER_URL"] = "http://localhost:8000"

    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Call pytest with the E2E test file
    test_file = "multi_choice_quiz/tests/test_quiz_e2e.py"
    subprocess.run([sys.executable, "-m", "pytest", test_file, "-v"])


if __name__ == "__main__":
    sys.exit(main())
