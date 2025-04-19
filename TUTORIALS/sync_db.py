#!/usr/bin/env python
import argparse
import getpass
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# --- Configuration ---
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 5432  # Default PostgreSQL port
DEFAULT_DUMP_FILENAME = f"temp_data_snapshot_{int(time.time())}.json"
MANAGE_PY_NAME = "manage.py"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# --- Helper Functions ---
def check_proxy(host: str, port: int) -> bool:
    """Checks if a TCP connection can be established to the host:port."""
    logging.info(f"Checking for Cloud SQL Auth Proxy on {host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set a short timeout to avoid long hangs if proxy is unresponsive
    sock.settimeout(2)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            logging.info("Proxy connection successful.")
            return True
        else:
            logging.error(f"Connection to {host}:{port} failed (Error code: {result}).")
            return False
    except socket.error as e:
        logging.error(f"Socket error connecting to proxy: {e}")
        return False
    finally:
        sock.close()

def print_proxy_instructions(instance_connection_name: str | None = None):
    """Prints instructions on how to run the Cloud SQL Auth Proxy."""
    instance_placeholder = instance_connection_name or "YOUR_PROJECT:YOUR_REGION:YOUR_INSTANCE"
    logging.error("-" * 60)
    logging.error("!! Cloud SQL Auth Proxy Not Detected or Not Reachable !!")
    logging.error("-" * 60)
    logging.error(f"This script requires the Cloud SQL Auth Proxy to be running and listening on {PROXY_HOST}:{PROXY_PORT}.")
    logging.error("Please start the proxy in a SEPARATE terminal window before running this script.")
    logging.error("\nExample commands (replace placeholders):")
    logging.error("\n--- On Linux/macOS/WSL (Windows Subsystem for Linux) ---")
    logging.error("   Download: https://cloud.google.com/sql/docs/postgres/connect-auth-proxy#install")
    logging.error(f"   Run: ./cloud-sql-proxy --private-ip {instance_placeholder} -p {PROXY_PORT}")
    logging.error("\n--- On Windows (Command Prompt / PowerShell) ---")
    logging.error("   Download: https://cloud.google.com/sql/docs/postgres/connect-auth-proxy#install")
    logging.error(f"   Run: cloud-sql-proxy.exe --private-ip {instance_placeholder} -p {PROXY_PORT}")
    logging.error("-" * 60)
    logging.error("Ensure the proxy starts successfully and shows 'Ready for new connections'.")
    logging.error("Then, re-run this script.")
    logging.error("-" * 60)


def run_manage_py(
    manage_py_path: Path,
    command: list[str],
    target_cloud_sql: bool = False,
    cloud_sql_creds: dict | None = None,
    settings_module: str | None = None,
    dump_file_path: Path | None = None,
) -> bool:
    """
    Runs a Django manage.py command using subprocess.

    Args:
        manage_py_path: Path to the manage.py script.
        command: A list containing the manage.py command and its arguments
                 (e.g., ['flush'], ['dumpdata', '--output', 'file.json']).
        target_cloud_sql: If True, set environment variables for Cloud SQL proxy.
        cloud_sql_creds: Dictionary with DB_NAME, DB_USER, DB_PASSWORD.
        settings_module: The DJANGO_SETTINGS_MODULE string.
        dump_file_path: Path object for output redirection (used by dumpdata).

    Returns:
        True if the command succeeded, False otherwise.
    """
    base_cmd = ["python", str(manage_py_path)] + command
    env = os.environ.copy()
    input_data = None
    stdout_dest = subprocess.PIPE
    stderr_dest = subprocess.PIPE

    if settings_module:
        env["DJANGO_SETTINGS_MODULE"] = settings_module
        logging.info(f"Using DJANGO_SETTINGS_MODULE: {settings_module}")
    else:
         logging.warning("DJANGO_SETTINGS_MODULE not specified. Assuming default behavior.")


    if target_cloud_sql:
        if not cloud_sql_creds:
            logging.error("Cloud SQL credentials missing for target_cloud_sql=True.")
            return False
        logging.info(f"Targeting Cloud SQL ({cloud_sql_creds.get('DB_NAME', 'N/A')}) via proxy {PROXY_HOST}:{PROXY_PORT}")
        env["DB_HOST"] = PROXY_HOST
        env["DB_PORT"] = str(PROXY_PORT)
        env["DB_NAME"] = cloud_sql_creds["DB_NAME"]
        env["DB_USER"] = cloud_sql_creds["DB_USER"]
        env["DB_PASSWORD"] = cloud_sql_creds["DB_PASSWORD"] # Critical!
        # Add other necessary env vars if your settings need them, e.g., SECRET_KEY
        # env["SECRET_KEY"] = os.environ.get("SECRET_KEY", "some-fallback-if-needed")

        # Handle 'flush' command confirmation
        if command and command[0] == "flush":
            input_data = "yes\n"
            logging.info("Automatically confirming 'yes' for flush command.")

    else:
        logging.info("Targeting local database (presumably SQLite).")
        # For dumpdata, redirect stdout to the file
        if command and command[0] == 'dumpdata' and dump_file_path:
             logging.info(f"Redirecting dumpdata output to {dump_file_path}")
             # We'll handle file writing outside subprocess for better control/error handling
             # but need to adjust args if --output is expected by manage.py itself
             if '--output' not in command :
                 base_cmd.extend(['--output', str(dump_file_path)])
             else:
                 # Find and replace if needed, though passing path directly is better
                 try:
                      idx = command.index('--output')
                      base_cmd[base_cmd.index(command[idx+1])] = str(dump_file_path)
                 except (ValueError, IndexError):
                      logging.error("Could not correctly set --output argument for dumpdata.")
                      return False


    cmd_display = list(base_cmd)
    # Mask password in displayed command
    if "DB_PASSWORD" in env:
        try:
            # Simple masking, might not cover all subprocess argument passing nuances
            idx = cmd_display.index(env["DB_PASSWORD"])
            cmd_display[idx] = "****"
        except ValueError:
            pass # Password not directly in command args, good.

    logging.info(f"Running command: {' '.join(cmd_display)}")

    try:
        process = subprocess.run(
            base_cmd,
            input=input_data,
            env=env,
            check=True,  # Raise CalledProcessError on non-zero exit code
            text=True,   # Work with text streams
            capture_output=True # Capture stdout/stderr unless redirected
        )
        logging.info(f"Command successful.")
        if process.stdout:
             logging.info(f"stdout:\n{process.stdout.strip()}")
        if process.stderr:
             logging.info(f"stderr:\n{process.stderr.strip()}") # Often has useful info even on success
        return True

    except FileNotFoundError:
        logging.exception(f"Error: 'python' or '{manage_py_path}' command not found. Is Python installed and in PATH? Is the script in the right directory?")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with exit code {e.returncode}: {' '.join(base_cmd)}")
        if e.stdout:
            logging.error(f"stdout:\n{e.stdout.strip()}")
        if e.stderr:
            logging.error(f"stderr:\n{e.stderr.strip()}")
        return False
    except Exception as e: # Catch other potential errors
        logging.exception(f"An unexpected error occurred running manage.py: {e}")
        return False


# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(
        description="Sync local Django SQLite data to Cloud SQL (PostgreSQL) via Cloud SQL Auth Proxy.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--settings",
        required=True,
        help="Django settings module path (e.g., 'myproject.settings')",
    )
    parser.add_argument(
        "--instance",
        required=True,
        help="Cloud SQL Instance Connection Name (e.g., 'my-project:us-central1:my-instance')",
    )
    parser.add_argument(
        "--db-name",
        required=True,
        help="Cloud SQL Database name.",
    )
    parser.add_argument(
        "--db-user",
        required=True,
        help="Cloud SQL Database user.",
    )
    parser.add_argument(
        "--dump-file",
        default=DEFAULT_DUMP_FILENAME,
        help=f"Temporary filename for the data dump (default: {DEFAULT_DUMP_FILENAME}).",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip the basic verification step using psycopg2.",
    )
    parser.add_argument(
        "--manage-py-path",
        default=MANAGE_PY_NAME,
        help=f"Path to your manage.py file (default: ./{MANAGE_PY_NAME})."
    )

    args = parser.parse_args()

    manage_py_path = Path(args.manage_py_path).resolve()
    dump_file_path = Path(args.dump_file).resolve()

    if not manage_py_path.is_file():
        logging.error(f"Error: manage.py not found at {manage_py_path}")
        sys.exit(1)

    logging.info("--- Starting Django DB Sync Script ---")

    # 1. Check for Cloud SQL Proxy
    if not check_proxy(PROXY_HOST, PROXY_PORT):
        print_proxy_instructions(args.instance)
        sys.exit(1)

    # 2. Get Cloud SQL Password Securely
    db_password = getpass.getpass(f"Enter password for Cloud SQL user '{args.db_user}': ")
    if not db_password:
        logging.error("Password cannot be empty.")
        sys.exit(1)

    cloud_sql_creds = {
        "DB_NAME": args.db_name,
        "DB_USER": args.db_user,
        "DB_PASSWORD": db_password,
    }

    sync_success = False
    try:
        # 3. Flush Cloud SQL Data
        logging.info("\n--- Step 1: Flushing Cloud SQL Database ---")
        if not run_manage_py(
            manage_py_path,
            ["flush", "--noinput"], # Pass --noinput for flush for non-interactive
            target_cloud_sql=True,
            cloud_sql_creds=cloud_sql_creds,
            settings_module=args.settings,
        ):
             # NOTE: Passing --noinput to flush means NO 'yes' prompt.
             # If you *want* the safety prompt, remove --noinput and adjust
             # run_manage_py to handle stdin piping 'yes\n' as shown previously.
             # For this script, --noinput is simpler. Assume user wants the flush.
             logging.error("Failed to flush Cloud SQL database.")
             raise Exception("Flush failed") # Use Exception to trigger finally block

        # 4. Dump Local SQLite Data
        logging.info("\n--- Step 2: Dumping Data from Local SQLite DB ---")
        # Note: dumpdata args might need adjustment based on your models (natural keys etc.)
        dump_command = [
            "dumpdata",
            "--exclude=contenttypes",
            "--exclude=auth.Permission",
            "--indent=2",
            # Output is handled by run_manage_py when dump_file_path is set
        ]
        if not run_manage_py(
            manage_py_path,
            dump_command,
            target_cloud_sql=False, # Target LOCAL DB
            settings_module=args.settings,
            dump_file_path=dump_file_path
        ):
            logging.error("Failed to dump data from local SQLite database.")
            raise Exception("Dump failed")

        # 5. Load Data into Cloud SQL
        logging.info("\n--- Step 3: Loading Data into Cloud SQL ---")
        if not run_manage_py(
            manage_py_path,
            ["loaddata", str(dump_file_path)],
            target_cloud_sql=True,
            cloud_sql_creds=cloud_sql_creds,
            settings_module=args.settings,
        ):
            logging.error("Failed to load data into Cloud SQL database.")
            raise Exception("Load failed")

        # 6. Optional: Basic Verification
        if not args.skip_verify:
            logging.info("\n--- Step 4: Basic Verification ---")
            try:
                import psycopg2
                logging.info("Attempting basic connection test using psycopg2...")
                conn = None
                try:
                    conn = psycopg2.connect(
                        dbname=args.db_name,
                        user=args.db_user,
                        password=db_password,
                        host=PROXY_HOST,
                        port=PROXY_PORT,
                        connect_timeout=5
                    )
                    cur = conn.cursor()
                    cur.execute("SELECT 1;") # Simple query to test connection
                    cur.fetchone()
                    cur.close()
                    logging.info("Verification successful: Able to connect and execute simple query.")
                except psycopg2.Error as e:
                    logging.warning(f"Verification failed: Could not connect or query via proxy using psycopg2. Error: {e}")
                    # Don't mark the whole sync as failed just for this
                finally:
                    if conn:
                        conn.close()
            except ImportError:
                logging.warning("psycopg2 not installed. Skipping verification step.")
                logging.warning("Install it (`pip install psycopg2-binary`) to enable verification.")

        # If we reached here, all core steps succeeded
        sync_success = True
        logging.info("\n--- Sync Process Completed Successfully! ---")

    except Exception as e:
        logging.error(f"\n--- Sync Process Failed: {e} ---")
        sync_success = False

    finally:
        # 7. Cleanup temporary dump file
        if dump_file_path.exists():
            logging.info(f"\n--- Step 5: Cleaning up temporary file {dump_file_path} ---")
            try:
                dump_file_path.unlink()
                logging.info("Temporary file deleted.")
            except OSError as e:
                logging.error(f"Error deleting temporary file {dump_file_path}: {e}")

        # 8. Final Reminder
        logging.info("\n--- Final Reminder ---")
        logging.info("Don't forget to stop the Cloud SQL Auth Proxy process running in the other terminal if you are finished.")
        logging.info("-" * 60)

        if not sync_success:
            sys.exit(1) # Exit with error code if sync failed

if __name__ == "__main__":
    main()