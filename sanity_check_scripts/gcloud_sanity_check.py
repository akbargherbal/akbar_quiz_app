#!/usr/bin/env python3
import subprocess
import sys
import os
from dotenv import load_dotenv

# --- Configuration Loading ---
load_dotenv()  # Load environment variables from .env file

# Load configuration from environment variables
# Provide default None values and check later for better error handling
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
INSTANCE_NAME = os.getenv("CLOUD_SQL_INSTANCE_NAME")


# --- Pre-run Checks ---
def check_config():
    """Verify that required configuration variables were loaded."""
    errors = []
    if not PROJECT_ID:
        errors.append("  - GCP_PROJECT_ID is not set in the .env file or environment.")
    if not INSTANCE_NAME:
        errors.append(
            "  - CLOUD_SQL_INSTANCE_NAME is not set in the .env file or environment."
        )

    if errors:
        print("❌ Configuration Error:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        print(
            "\nPlease create or update the '.env' file in the script's directory with:",
            file=sys.stderr,
        )
        print('GCP_PROJECT_ID="your-project-id"', file=sys.stderr)
        print('CLOUD_SQL_INSTANCE_NAME="your-instance-name"', file=sys.stderr)
        sys.exit(1)  # Exit if configuration is missing
    return True


# --- Helper Function (Unchanged) ---
def run_gcloud_command(command_list):
    """
    Runs a gcloud command provided as a list and returns its stdout.
    Handles common errors and prints messages to stderr.
    Returns None if the command fails.
    """
    try:
        # Run command without shell=True for better security/control
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=True,  # Raise CalledProcessError on non-zero exit code
            encoding="utf-8",  # Explicitly set encoding
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Print specific gcloud error if available
        error_message = e.stderr.strip()
        print(f"  ❌ Error running command: {' '.join(e.cmd)}", file=sys.stderr)
        if error_message:
            print(f"     GCloud Error: {error_message}", file=sys.stderr)
        else:
            print(f"     Command failed with exit code {e.returncode}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("  ❌ Error: 'gcloud' command not found.", file=sys.stderr)
        print(
            "     Is the Google Cloud SDK installed and configured in your PATH?",
            file=sys.stderr,
        )
        sys.exit(1)  # Exit if gcloud isn't available
    except Exception as e:
        # Catch other potential exceptions
        print(f"  ❌ An unexpected error occurred: {e}", file=sys.stderr)
        return None


# --- Check Functions (Updated to use loaded config) ---
def check_account_project():
    """Checks and prints the active gcloud account and project."""
    print("--- 1. Active Account & Project ---")
    account_cmd_list = [
        "gcloud",
        "config",
        "list",
        "account",
        "--format=value(core.account)",
    ]
    project_cmd_list = [
        "gcloud",
        "config",
        "list",
        "project",
        "--format=value(core.project)",
    ]

    account = run_gcloud_command(account_cmd_list)
    project = run_gcloud_command(project_cmd_list)

    account_ok = False
    project_ok = False

    if account:
        print(f"  ✅ Account: {account}")
        account_ok = True
    else:
        print("  ❌ Could not determine active account. (Run 'gcloud auth login'?)")

    if project:
        print(f"  ✅ Configured Project: {project}")
        if project == PROJECT_ID:  # Compare with loaded PROJECT_ID
            print(f"     Matches expected project from .env file.")
            project_ok = True
        else:
            print(
                f"  ⚠️ Warning: Active project '{project}' differs from expected '{PROJECT_ID}' (from .env)."
            )
            print(
                f"     (Run 'gcloud config set project {PROJECT_ID}' to align if needed)"
            )
    else:
        print(
            f"  ❌ Could not determine active project. (Run 'gcloud config set project {PROJECT_ID}'?)"
        )

    # Return the account name for the IAM check, even if project mismatches
    return account if account_ok else None


def check_sql_admin_api():
    """Checks if the Cloud SQL Admin API is enabled."""
    print("\n--- 2. Cloud SQL Admin API Status ---")
    command_list = [
        "gcloud",
        "services",
        "list",
        "--enabled",
        "--filter=NAME:sqladmin.googleapis.com",
        f"--project={PROJECT_ID}",  # Use loaded PROJECT_ID
    ]
    output = run_gcloud_command(command_list)

    if output is not None:
        if "sqladmin.googleapis.com" in output:
            print(f"  ✅ Cloud SQL Admin API is ENABLED for project '{PROJECT_ID}'.")
            return True
        else:
            # Command succeeded but API wasn't listed among enabled ones
            print(
                f"  ❌ Cloud SQL Admin API is NOT ENABLED for project '{PROJECT_ID}'."
            )
            print(
                f"     (Enable it via GCP Console or 'gcloud services enable sqladmin.googleapis.com --project={PROJECT_ID}')"
            )
            return False
    return False  # Indicate failure if command failed


def check_sql_instance():
    """Checks the status of the Cloud SQL instance."""
    print("\n--- 3. Cloud SQL Instance Status ---")
    command_list = [
        "gcloud",
        "sql",
        "instances",
        "describe",
        INSTANCE_NAME,  # Use loaded INSTANCE_NAME
        f"--project={PROJECT_ID}",  # Use loaded PROJECT_ID
        "--format=value(state)",
    ]
    state = run_gcloud_command(command_list)

    if state:
        print(f"  ✅ Instance '{INSTANCE_NAME}' found. State: {state}")
        if state == "RUNNABLE":
            print("     Instance is RUNNABLE.")
            return True
        else:
            print(f"  ⚠️ Warning: Instance is '{state}', not RUNNABLE.")
            return False
    else:
        print(
            f"  ❌ Failed to get status for instance '{INSTANCE_NAME}' in project '{PROJECT_ID}'."
        )
        print(
            f"     (Check instance name in .env, project ID in .env, or permissions?)"
        )
        return False  # Indicate failure


def check_iam_roles(account):
    """Checks the IAM roles for the active account."""
    print("\n--- 4. IAM Roles for Active User ---")
    if not account:
        print("  ❌ Cannot check roles: Active account not determined in Step 1.")
        return False

    print(f"  ℹ️ Checking roles for account: {account}")
    # Construct the filter carefully - assumes a standard user account login
    # For service accounts, the prefix is 'serviceAccount:'
    iam_filter = f'bindings.members:"user:{account}"'

    # Build command as a list for subprocess.run
    command_list = [
        "gcloud",
        "projects",
        "get-iam-policy",
        PROJECT_ID,  # Use loaded PROJECT_ID
        "--flatten=bindings[].members",
        "--format=table(bindings.role)",  # Format specification
        f"--filter={iam_filter}",  # Filter specification
    ]

    roles_output = run_gcloud_command(command_list)

    if roles_output is not None:
        # Handle case where no roles are found (command succeeds but output is just headers)
        if (
            roles_output.strip() == "ROLE"
        ):  # Only header printed means no matching roles
            print(f"  ⚠️ No specific roles found directly assigned to 'user:{account}'")
            print(
                f"     (Permissions might be inherited via groups - cannot check here)"
            )
            print(
                f"     Ensure 'user:{account}' or a group it belongs to has 'roles/owner' or 'roles/cloudsql.client'"
            )
            return False  # Treat as warning/failure for script purposes

        print(f"  Roles found:\n---\n{roles_output}\n---")
        # Check for specific necessary roles
        has_owner = "roles/owner" in roles_output
        has_sql_client = "roles/cloudsql.client" in roles_output

        if has_owner:
            print("  ✅ Found 'roles/owner' (Provides sufficient permissions).")
            return True
        elif has_sql_client:
            print(
                "  ✅ Found 'roles/cloudsql.client' (Provides necessary connection permission)."
            )
            # Add checks here if other specific roles are needed by the application itself
            return True
        else:
            print(
                "  ⚠️ Warning: Did not find 'roles/owner' or 'roles/cloudsql.client' directly assigned."
            )
            print(
                "     The Cloud SQL Proxy may fail to connect if permissions aren't inherited."
            )
            print(
                f"     (Grant required roles via GCP Console IAM page for '{account}')"
            )
            return False
    else:
        print(
            f"  ❌ Failed to retrieve IAM roles for '{account}' on project '{PROJECT_ID}'."
        )
        return False  # Indicate failure


# --- Main Execution ---
if __name__ == "__main__":
    # First, check if config loaded successfully
    if not check_config():
        # Error message already printed by check_config()
        pass  # sys.exit(1) was already called inside check_config()

    print(f"Running Google Cloud Sanity Checks (using config from .env)")
    print(f"Target Project: {PROJECT_ID}")
    print(f"Target SQL Instance: {INSTANCE_NAME}")
    print("=========================================")

    results = {}
    active_account = check_account_project()
    # We need the active account for the IAM check later
    results["account_project"] = bool(active_account)  # True if account determined

    results["sql_api"] = check_sql_admin_api()
    results["sql_instance"] = check_sql_instance()
    results["iam_roles"] = check_iam_roles(active_account)  # Pass account name

    print("\n=========================================")
    print("Sanity Check Summary:")

    all_ok = True
    for check, status in results.items():
        status_text = "✅ OK" if status else "❌ FAILED / WARNING"
        print(f"- {check.replace('_', ' ').title()}: {status_text}")
        if not status:
            all_ok = False

    if all_ok:
        print("\n✅ All checks passed.")
    else:
        print(
            "\n⚠️ Some checks failed or have warnings. Please review the output above."
        )

    print("=========================================")
