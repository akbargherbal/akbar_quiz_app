#!/usr/bin/env python3
import subprocess
import sys
import os
import json
from dotenv import load_dotenv

print(
    """
This script is be run in production migrations; especially on GCP Cloud Shell.
"""
)

# --- Configuration Loading ---
load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
CLOUD_RUN_SERVICE_NAME = os.getenv("CLOUD_RUN_SERVICE_NAME")
CLOUD_RUN_REGION = os.getenv("CLOUD_RUN_REGION")
CLOUD_SQL_INSTANCE_CONNECTION_NAME = os.getenv("CLOUD_SQL_INSTANCE_CONNECTION_NAME")

SECRET_NAMES = {
    "DB_NAME_SECRET": os.getenv("SECRET_NAME_DB_NAME"),
    "DB_USER_SECRET": os.getenv("SECRET_NAME_DB_USER"),
    "DB_PASSWORD_SECRET": os.getenv("SECRET_NAME_DB_PASSWORD"),
    "DJANGO_SECRET_KEY_SECRET": os.getenv("SECRET_NAME_DJANGO_SECRET_KEY"),
}

EXPECTED_ENV_VARS_FROM_SECRETS = {
    "DB_NAME_ENV": os.getenv("ENV_VAR_DB_NAME"),
    "DB_USER_ENV": os.getenv("ENV_VAR_DB_USER"),
    "DB_PASSWORD_ENV": os.getenv("ENV_VAR_DB_PASSWORD"),
    "DJANGO_SECRET_KEY_ENV": os.getenv("ENV_VAR_DJANGO_SECRET_KEY"),
}

EXPECTED_CSRF_ORIGIN_URL = os.getenv("EXPECTED_CSRF_ORIGIN_URL")


# --- Pre-run Checks for Script Configuration ---
def check_script_config():
    errors = []
    if not GCP_PROJECT_ID:
        errors.append("GCP_PROJECT_ID")
    if not CLOUD_RUN_SERVICE_NAME:
        errors.append("CLOUD_RUN_SERVICE_NAME")
    if not CLOUD_RUN_REGION:
        errors.append("CLOUD_RUN_REGION")
    if not CLOUD_SQL_INSTANCE_CONNECTION_NAME:
        errors.append("CLOUD_SQL_INSTANCE_CONNECTION_NAME")
    if not all(SECRET_NAMES.values()):
        errors.append("One or more SECRET_NAME_* variables")
    if not all(EXPECTED_ENV_VARS_FROM_SECRETS.values()):
        errors.append("One or more ENV_VAR_* variables")
    if (
        not EXPECTED_CSRF_ORIGIN_URL
        or EXPECTED_CSRF_ORIGIN_URL
        == "https://your-current-active-service-url.a.run.app"
    ):
        errors.append(
            "EXPECTED_CSRF_ORIGIN_URL is not set or is still the placeholder value."
        )

    if errors:
        print(
            "❌ Script Configuration Error: Missing values in .env file for:",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print(
            "\nPlease create or update the '.env' file next to this script.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("✅ Script configuration loaded successfully from .env")
    return True


# --- Helper Function ---
def run_gcloud_command(command_list, json_output=False, ignore_errors=False):
    print(f"   M Running: {' '.join(command_list)}")
    try:
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=not ignore_errors,
            encoding="utf-8",
        )
        if result.returncode != 0 and not ignore_errors:
            # This case should be caught by check=True, but as a fallback
            print(
                f"  ❌ Error running command (unexpected): {' '.join(command_list)}",
                file=sys.stderr,
            )
            if result.stderr.strip():
                print(f"     GCloud Stderr: {result.stderr.strip()}", file=sys.stderr)
            return None

        output = result.stdout.strip()
        if json_output:
            if not output:  # Handle empty output for JSON
                if ignore_errors:
                    return {}  # or appropriate default
                print(
                    f"  ❌ Error: Command produced no output for JSON parsing: {' '.join(command_list)}",
                    file=sys.stderr,
                )
                return None
            return json.loads(output)
        return output
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip()
        print(f"  ❌ Error running command: {' '.join(e.cmd)}", file=sys.stderr)
        if error_message:
            print(f"     GCloud Error: {error_message}", file=sys.stderr)
        else:
            print(f"     Command failed with exit code {e.returncode}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("  ❌ Error: 'gcloud' command not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(
            f"  ❌ Error: Failed to decode JSON output from command: {' '.join(command_list)}",
            file=sys.stderr,
        )
        print(f"     Error: {e}", file=sys.stderr)
        print(
            f"     Raw output: {result.stdout.strip()[:200]}...", file=sys.stderr
        )  # Print start of raw output
        return None
    except Exception as e:
        print(f"  ❌ An unexpected error occurred: {e}", file=sys.stderr)
        return None


# --- Check Functions ---
def check_cloud_run_service_config():
    print("\n--- 1. Cloud Run Service Configuration ---")
    service_data = run_gcloud_command(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            CLOUD_RUN_SERVICE_NAME,
            f"--project={GCP_PROJECT_ID}",
            f"--region={CLOUD_RUN_REGION}",
            "--format=json",
        ],
        json_output=True,
    )

    if not service_data:
        return False, None  # Indicate failure and no service account

    service_account = (
        service_data.get("spec", {})
        .get("template", {})
        .get("spec", {})
        .get("serviceAccountName")
    )
    print(f"  ✅ Fetched service data for '{CLOUD_RUN_SERVICE_NAME}'.")
    if service_account:
        print(f"  ℹ️ Service Account Used: {service_account}")
    else:
        print(
            f"  ⚠️ Could not determine service account from service description. Assuming default."
        )
        # Fallback to default Compute Engine service account format if needed for later checks
        project_number = run_gcloud_command(
            [
                "gcloud",
                "projects",
                "describe",
                GCP_PROJECT_ID,
                "--format=value(projectNumber)",
            ]
        )
        if project_number:
            service_account = f"{project_number}-compute@developer.gserviceaccount.com"
            print(f"  ℹ️ Assuming default service account: {service_account}")
        else:
            print(
                f"  ❌ Could not determine project number to construct default service account."
            )
            service_account = None

    # Check Cloud SQL Instance Connection
    connections = (
        service_data.get("spec", {})
        .get("template", {})
        .get("metadata", {})
        .get("annotations", {})
        .get("run.googleapis.com/cloudsql-instances")
    )
    sql_ok = False
    if connections and CLOUD_SQL_INSTANCE_CONNECTION_NAME in connections:
        print(
            f"  ✅ Cloud SQL Instance '{CLOUD_SQL_INSTANCE_CONNECTION_NAME}' is correctly connected to the service."
        )
        sql_ok = True
    else:
        print(
            f"  ❌ Cloud SQL Instance '{CLOUD_SQL_INSTANCE_CONNECTION_NAME}' NOT found in service connections."
        )
        print(f"     Current connections: {connections}")
        print(
            f"     (Check --add-cloudsql-instances in your 'gcloud run deploy' command - Step 7)"
        )

    # Check Secrets Mapping
    env_vars_from_secrets_mapping = {}
    containers = (
        service_data.get("spec", {})
        .get("template", {})
        .get("spec", {})
        .get("containers", [])
    )
    if containers:
        env_from = containers[0].get("envFrom", [])
        for env_source in env_from:
            secret_ref = env_source.get("secretRef")
            if secret_ref:
                # This structure might vary based on how secrets are mounted.
                # The provided guide uses --update-secrets which maps directly to env vars.
                # This check is more for 'envFrom.secretRef'.
                # We will check specific env vars that *should* be populated by --update-secrets directly.
                pass  # Not directly checking secretRef, as --update-secrets implies direct env var mapping.

        # Check for environment variables expected to be set from secrets (Step 7)
        envs = containers[0].get("env", [])
        actual_env_vars_from_secrets = {}
        for env_var in envs:
            if env_var.get("valueFrom", {}).get("secretKeyRef"):
                actual_env_vars_from_secrets[env_var["name"]] = env_var["valueFrom"][
                    "secretKeyRef"
                ]["name"]

        secrets_ok = True
        print("  ℹ️ Checking environment variables mapped from secrets:")
        expected_mapping = {
            EXPECTED_ENV_VARS_FROM_SECRETS["DB_NAME_ENV"]: SECRET_NAMES[
                "DB_NAME_SECRET"
            ],
            EXPECTED_ENV_VARS_FROM_SECRETS["DB_USER_ENV"]: SECRET_NAMES[
                "DB_USER_SECRET"
            ],
            EXPECTED_ENV_VARS_FROM_SECRETS["DB_PASSWORD_ENV"]: SECRET_NAMES[
                "DB_PASSWORD_SECRET"
            ],
            EXPECTED_ENV_VARS_FROM_SECRETS["DJANGO_SECRET_KEY_ENV"]: SECRET_NAMES[
                "DJANGO_SECRET_KEY_SECRET"
            ],
        }

        for env_name, secret_name_expected in expected_mapping.items():
            if env_name in actual_env_vars_from_secrets:
                secret_name_actual = actual_env_vars_from_secrets[env_name]
                if secret_name_actual == secret_name_expected:
                    print(
                        f"    ✅ Env Var '{env_name}' correctly mapped from Secret '{secret_name_actual}'."
                    )
                else:
                    print(
                        f"    ❌ Env Var '{env_name}' mapped from Secret '{secret_name_actual}', expected '{secret_name_expected}'."
                    )
                    secrets_ok = False
            else:
                print(
                    f"    ❌ Env Var '{env_name}' (expected from Secret '{secret_name_expected}') is NOT defined as a secret mapping."
                )
                secrets_ok = False
        if not actual_env_vars_from_secrets and expected_mapping:
            print(
                f"    ❌ No environment variables appear to be mapped from secrets. Check --update-secrets in Step 7."
            )
            secrets_ok = False

    # Check actual service URL for CSRF
    service_url = service_data.get("status", {}).get("url")
    csrf_ok = False
    if service_url:
        print(f"  ℹ️ Actual Deployed Service URL: {service_url}")
        if service_url == EXPECTED_CSRF_ORIGIN_URL:
            print(f"  ✅ EXPECTED_CSRF_ORIGIN_URL in .env matches actual service URL.")
            csrf_ok = True
        else:
            print(
                f"  ❌ EXPECTED_CSRF_ORIGIN_URL ('{EXPECTED_CSRF_ORIGIN_URL}') in .env does NOT match actual service URL ('{service_url}')."
            )
            print(
                f"     Update .env or your settings.py's CSRF_TRUSTED_ORIGINS (Step 4)."
            )
    else:
        print(
            f"  ❌ Could not determine actual deployed service URL from service description."
        )

    return all([sql_ok, secrets_ok, csrf_ok]), service_account


def check_secret_manager_permissions(service_account_email):
    print("\n--- 2. Secret Manager Permissions ---")
    if not service_account_email:
        print(
            "  ❌ Cannot check Secret Manager permissions: Service Account not determined."
        )
        return False

    all_permissions_ok = True
    for key_name, secret_name in SECRET_NAMES.items():
        if not secret_name:
            print(
                f"  ⚠️ Secret name for {key_name} not configured in .env, skipping permission check."
            )
            continue
        print(
            f"  ℹ️ Checking permissions for Secret '{secret_name}' for Service Account '{service_account_email}'..."
        )
        policy = run_gcloud_command(
            [
                "gcloud",
                "secrets",
                "get-iam-policy",
                secret_name,
                f"--project={GCP_PROJECT_ID}",
                "--format=json",
            ],
            json_output=True,
        )

        if not policy or "bindings" not in policy:
            print(
                f"  ❌ Could not retrieve IAM policy for Secret '{secret_name}' or no bindings found."
            )
            all_permissions_ok = False
            continue

        accessor_role = "roles/secretmanager.secretAccessor"
        has_permission = False
        for binding in policy["bindings"]:
            if binding.get("role") == accessor_role:
                # Normalize member format (serviceAccount: prefix)
                normalized_sa_email = f"serviceAccount:{service_account_email}"
                if service_account_email in binding.get(
                    "members", []
                ) or normalized_sa_email in binding.get("members", []):
                    has_permission = True
                    break

        if has_permission:
            print(
                f"  ✅ Service Account HAS '{accessor_role}' permission for Secret '{secret_name}'."
            )
        else:
            print(
                f"  ❌ Service Account does NOT have '{accessor_role}' for Secret '{secret_name}'. (Step 3, Part 3)"
            )
            all_permissions_ok = False
            # You can optionally print the full binding list for debugging if needed
            # print(f"     Current bindings: {json.dumps(policy['bindings'], indent=2)}")

    return all_permissions_ok


def check_secret_values_exist():
    print("\n--- 3. Secret Manager Values (Existence Check) ---")
    all_values_exist = True
    for key_name, secret_name in SECRET_NAMES.items():
        if not secret_name:
            print(
                f"  ⚠️ Secret name for {key_name} not configured in .env, skipping value check."
            )
            continue
        # We are just checking if *a* value can be accessed, not what the value is.
        # Accessing 'latest' version.
        value_output = run_gcloud_command(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                f"--secret={secret_name}",
                f"--project={GCP_PROJECT_ID}",
            ],
            ignore_errors=True,
        )  # Ignore errors because we just want to see if it returns something

        if (
            value_output is not None and value_output.strip() != ""
        ):  # Check if output is not None and not empty
            print(
                f"  ✅ Secret '{secret_name}' has a value accessible for version 'latest'."
            )
        elif value_output is None:  # Command failed
            print(
                f"  ❌ Failed to access Secret '{secret_name}' (version 'latest'). (Check secret name, permissions, or if versions exist - Step 3)"
            )
            all_values_exist = False
        else:  # Command succeeded but returned empty string
            print(
                f"  ⚠️ Secret '{secret_name}' (version 'latest') appears to be empty or could not be read properly."
            )
            # This could be an issue depending on if an empty value is valid for the secret
            all_values_exist = (
                False  # Treat empty as a potential issue for required secrets
            )

    return all_values_exist


# --- Main Execution ---
if __name__ == "__main__":
    if not check_script_config():
        sys.exit(1)

    print(f"\nRunning GCP Cloud Run Sanity Checks for Django Deployment")
    print(f"Target Project: {GCP_PROJECT_ID}")
    print(f"Target Service: {CLOUD_RUN_SERVICE_NAME} in {CLOUD_RUN_REGION}")
    print("========================================================")

    results = {}
    service_config_ok, sa_email = check_cloud_run_service_config()
    results["cloud_run_service_config"] = service_config_ok

    if sa_email:  # Only check permissions if we could determine the service account
        results["secret_manager_permissions"] = check_secret_manager_permissions(
            sa_email
        )
    else:
        results["secret_manager_permissions"] = (
            False  # Mark as failed if SA couldn't be found
        )
        print(
            "  SKIPPING Secret Manager permission checks as Service Account could not be determined."
        )

    results["secret_values_exist"] = check_secret_values_exist()

    print("\n========================================================")
    print("Cloud Run Deployment Sanity Check Summary:")

    all_ok_final = True
    for check_name, status in results.items():
        status_text = "✅ OK" if status else "❌ FAILED / WARNING"
        # Simple title case for readability
        readable_check_name = " ".join(
            word.capitalize() for word in check_name.split("_")
        )
        print(f"- {readable_check_name}: {status_text}")
        if not status:
            all_ok_final = False

    if all_ok_final:
        print("\n✅ All critical Cloud Run configurations seem OK based on checks.")
        print(
            "   If issues persist, check application-level logic, Django settings details,"
        )
        print("   and specific error messages in Cloud Run logs during request time.")
    else:
        print("\n⚠️ Some Cloud Run configuration checks FAILED or have warnings.")
        print(
            "   Please review the output above carefully and address the identified issues."
        )
        print("   These are likely contributing to your deployment problems.")

    print("========================================================")
