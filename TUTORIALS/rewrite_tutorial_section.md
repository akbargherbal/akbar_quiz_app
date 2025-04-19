Okay, here are the updated sections for your `Django_Deployment_App_Engine.txt` tutorial, incorporating the `secret_env_variables` parsing error and workaround.

**Instructions:** Replace or insert the following blocks into your original document at the specified locations.

---

**1. Update for Phase 1 - `requirements.txt`**

* **Location:** Find the subsection "Essential Production Dependencies" within "Phase 1: Preparing Your Django Project for Production". Specifically, locate the list item explaining `google-cloud-secret-manager` [cite: 60] and the example `requirements.txt` code block[cite: 63].

* **Action:**
    * Modify the explanation for `google-cloud-secret-manager`.
    * Update the example `requirements.txt` code block.

* **Modified Text:**

    **(Modify the list item explaining `google-cloud-secret-manager`)**
    ```markdown
    - **`google-cloud-secret-manager`**: Needed if you intend to access secrets programmatically within your Django application code. This is primarily used as a workaround if you encounter issues with App Engine parsing the `secret_env_variables` block in `app.yaml` (see Phase 7 Troubleshooting). Otherwise, using `secret_env_variables` is generally simpler.
    ```

    **(Replace the example `requirements.txt` code block)**
    ```
    # requirements.txt (example additions)
    Django>=4.2,<5.0        # Or your specific Django version
    gunicorn>=21.2.0,<22.0
    psycopg2-binary>=2.9.9,<3.0 # For PostgreSQL
    # mysqlclient>=2.2.0,<2.3  # For MySQL
    whitenoise[brotli]>=6.6.0,<7.0 # Brotli support is optional but efficient
    # django-environ>=0.11.0,<0.12.0 # If using django-environ
    google-cloud-secret-manager>=2.16.0,<3.0 # Required for programmatic secret fetching workaround
    # ... other dependencies
    ```

---

**2. Update for Phase 1 - `settings.py`**

* **Location:** Find the subsection "Configuring `settings.py` for Production" within "Phase 1". Locate the main Python code block example for `settings.py`.

* **Action:** Integrate the necessary imports, the helper function, and the conditional logic for fetching secrets programmatically.

* **Modified Text:**

    **(Add these imports near the top of the `settings.py` example, modifying existing ones if necessary)**
    ```python
    # myproject/settings.py

    import os
    import io
    import logging # Add logging import
    # import environ # If using django-environ
    from google.cloud import secretmanager # Keep or add this import
    ```

    **(Insert this helper function definition somewhere before the main settings logic, e.g., after imports)**
    ```python

    # --- Helper function for programmatic secret fetching (Workaround) ---
    # Only needed if bypassing app.yaml's secret_env_variables due to parsing errors.
    logger = logging.getLogger(__name__)

    def get_secret(secret_id, version_id="latest"):
        """Retrieves a secret version from Google Secret Manager."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                # On App Engine, GOOGLE_CLOUD_PROJECT should be automatically set.
                # Try to get it from metadata server as a fallback if needed.
                # Note: This might require additional permissions/setup.
                # import google.auth.compute_engine.credentials
                # import google.auth
                # credentials, project_id = google.auth.default()

                # For simplicity, raise error if not directly available via env var.
                logger.error("GOOGLE_CLOUD_PROJECT environment variable not set.")
                raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set.")

            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Error accessing secret: {secret_id}. Reason: {e}")
            # Decide how to handle failure: raise error, return None, use fallback?
            # Returning None here, let calling code handle it.
            return None

    ```

    **(Modify the `SECRET_KEY` and `DATABASES` sections within the `settings.py` example to integrate the programmatic fetching logic)**

    ```python
    # --- Option 1: Using os.environ (Standard Library) ---
    # Default SECRET_KEY using os.environ - will be overridden below if using workaround
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-for-local-dev-only-change-me')
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = os.environ.get('DEBUG', 'False') == 'True' # Environment variables are strings

    # ... (Keep ALLOWED_HOSTS section as is) ... [cite: 70]


    # --- Database Configuration ---
    # Default to SQLite for local development if DB variables aren't set
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

    # --- Environment Variable Handling for DB & Secrets ---
    # Prioritize App Engine standard integration (via app.yaml secret_env_variables)
    # These os.environ.get calls serve as fallbacks for local dev (e.g., with proxy)
    # OR if the programmatic fetching workaround below fails.
    DB_NAME_ENV = os.environ.get('DB_NAME')
    DB_USER_ENV = os.environ.get('DB_USER')
    DB_PASSWORD_ENV = os.environ.get('DB_PASSWORD')
    DB_HOST_ENV = os.environ.get('DB_HOST') # For Cloud SQL Proxy (local), Private IP, or App Engine Socket path
    DB_PORT_ENV = os.environ.get('DB_PORT', '5432') # Default PostgreSQL port

    # Check if running on App Engine
    IS_GAE = os.getenv('GAE_INSTANCE')

    # --- Programmatic Secret Fetching Workaround ---
    # Apply this logic ONLY if running on App Engine AND intending to use this workaround
    # Set an env variable like USE_PROGRAMMATIC_SECRETS=True in app.yaml to enable this,
    # OR simply rely on IS_GAE if this is your *only* way of getting secrets in prod.
    # For clarity, let's assume USE_PROGRAMMATIC_SECRETS controls this block.
    USE_PROGRAMMATIC_SECRETS = os.environ.get('USE_PROGRAMMATIC_SECRETS', 'False') == 'True'

    if IS_GAE and USE_PROGRAMMATIC_SECRETS:
        logger.info("Running on App Engine and USE_PROGRAMMATIC_SECRETS is True. Attempting to fetch secrets programmatically.")
        # Fetch secrets using the helper function
        SECRET_KEY_FETCHED = get_secret('django-secret-key') # Use your Secret Manager secret name
        DB_NAME_FETCHED = get_secret('db-name')
        DB_USER_FETCHED = get_secret('db-user')
        DB_PASSWORD_FETCHED = get_secret('db-password')
        # Fetch other secrets as needed...

        # Override settings if secrets were fetched successfully
        if SECRET_KEY_FETCHED:
            SECRET_KEY = SECRET_KEY_FETCHED
        else:
            logger.error("Failed to fetch SECRET_KEY from Secret Manager.")
            # Decide handling: raise error or rely on potentially insecure fallback?
            # Raising error is safer:
            raise ImproperlyConfigured("Could not fetch SECRET_KEY from Secret Manager.")

        # Use fetched DB creds if available, otherwise log error but potentially fallback to ENV?
        DB_NAME_PROD = DB_NAME_FETCHED if DB_NAME_FETCHED else DB_NAME_ENV
        DB_USER_PROD = DB_USER_FETCHED if DB_USER_FETCHED else DB_USER_ENV
        DB_PASSWORD_PROD = DB_PASSWORD_FETCHED if DB_PASSWORD_FETCHED else DB_PASSWORD_ENV

        if not all([DB_NAME_PROD, DB_USER_PROD, DB_PASSWORD_PROD]):
             logger.error("One or more DB secrets could not be fetched programmatically and no env fallback exists.")
             # Decide handling: raise error or proceed with potentially missing creds?
             raise ImproperlyConfigured("Missing required DB credentials.")

    else:
        # Not using programmatic fetching in prod OR running locally
        logger.info("Not fetching secrets programmatically (either local dev or USE_PROGRAMMATIC_SECRETS is False). Using environment variables.")
        DB_NAME_PROD = DB_NAME_ENV
        DB_USER_PROD = DB_USER_ENV
        DB_PASSWORD_PROD = DB_PASSWORD_ENV
        # SECRET_KEY already set from os.environ.get earlier

    # --- Final Database Config Logic ---
    # Use the determined prod credentials if running on App Engine OR connecting via local proxy (DB_HOST_ENV is set)
    # The DB_HOST_ENV will be '/cloudsql/...' on App Engine via app.yaml integration,
    # or '127.0.0.1' when using the proxy locally.
    if IS_GAE or DB_HOST_ENV:
        DATABASES['default'] = {
            'ENGINE': 'django.db.backends.postgresql', # Or mysql
            'NAME': DB_NAME_PROD,
            'USER': DB_USER_PROD,
            'PASSWORD': DB_PASSWORD_PROD,
            'HOST': DB_HOST_ENV, # Critical: Use the env var potentially set by App Engine or proxy
            'PORT': DB_PORT_ENV,
        }
        logger.info(f"Configured PostgreSQL database connection for host: {DB_HOST_ENV}")
    else:
         logger.info("Using default SQLite database for local development.")


    # ... (Remove the old "Option 3: Fetching Secrets Directly" example block if present) ...

    # ... (Keep Static Files, Middleware, Security Settings, Logging sections as they are) ...

    ```
    **(Optional but recommended): Add `USE_PROGRAMMATIC_SECRETS: 'True'` to the `env_variables` section in your `app.yaml` if you want to explicitly enable this workaround.** Otherwise, remove the `USE_PROGRAMMATIC_SECRETS` check in `settings.py` and rely solely on `IS_GAE`.

---

**3. Update for Phase 3 - `app.yaml` Explanation**

* **Location:** Find the "Code Breakdown & Why" subsection within "Phase 3: Configuring App Engine". Locate list item #6 explaining `secret_env_variables`.
* **Action:** Add a cautionary note at the end of the explanation for this key.
* **Modified Text:**

    **(Add this note to the end of the explanation for `secret_env_variables`)**
    ```markdown
    [...] It leverages Secret Manager's security and avoids exposing secrets in `app.yaml`. The App Engine service account needs the `Secret Manager Secret Accessor` role we granted earlier.

    > **Note:** Some users have reported encountering a parsing error like `Unexpected attribute 'secret_env_variables' for object of type AppInfoExternal` during `gcloud app deploy`, even with correct syntax. If you face this issue and standard troubleshooting (like `gcloud components update`) fails, please refer to the dedicated entry in the "Troubleshooting Common Issues" section (Phase 7) for a potential workaround involving programmatic secret fetching.
    ```

---

**4. Update for Phase 7 - Troubleshooting Common Issues**

* **Location:** Find the main heading "Troubleshooting Common Issues" (Phase 7)[cite: 381].
* **Action:** Add a new subsection detailing the `secret_env_variables` parsing error and workaround. It can be placed before or after other specific error types like "Deployment Failures".

* **New Subsection Text:**

    ```markdown
    ### `Unexpected attribute 'secret_env_variables'` Parsing Error

    **Symptom:**
    During `gcloud app deploy`, the deployment fails early in the process with an error similar to:
    ```
    ERROR: (gcloud.app.deploy) An error occurred while parsing file: [/path/to/your/app.yaml]
    Unexpected attribute 'secret_env_variables' for object of type AppInfoExternal.
     in "/path/to/your/app.yaml", line [XX]
    ```

    **Cause:**
    This indicates that the version of the App Engine deployment tools being used by `gcloud` does not recognize the `secret_env_variables:` key, despite it being standard documented configuration for App Engine Standard. This can sometimes happen even if `gcloud` and components seem up-to-date.

    **Standard Troubleshooting (Attempted but May Fail):**
    Users encountering this have reported that the following steps often *do not* resolve the issue:
    * Verifying `app.yaml` syntax and indentation are correct.
    * Updating `gcloud` and components: `gcloud components update` (including `app-engine-python`, `app-engine-python-extras`).
    * Trying different supported Python runtimes (e.g., `python311`, `python312`) in `app.yaml`.
    * Testing with a minimal `app.yaml` containing only `runtime`, `entrypoint`, and the `secret_env_variables` block.
    * Confirming that commenting out the *entire* `secret_env_variables` block allows parsing to proceed (though the app will fail later due to missing variables).

    **Resolution Path:**
    1.  **Check Google Cloud Issue Tracker / Support:** This appears to be an intermittent issue potentially related to specific tool versions or backend configurations. Check the public Google Cloud Issue Tracker for similar reports or open a support case with Google Cloud if you have a support plan. This is the best path to address the root cause.
    2.  **Workaround: Programmatic Secret Fetching:** If you need to deploy urgently and cannot resolve the parsing issue, you can use the following workaround:
        * **Remove `secret_env_variables`:** Comment out or completely remove the `secret_env_variables:` block from your `app.yaml`.
        * **Add Library:** Ensure `google-cloud-secret-manager` is included in your `requirements.txt` (see Phase 1).
        * **Modify `settings.py`:** Implement logic in your `settings.py` to fetch the necessary secrets directly from Secret Manager *at runtime* when running on App Engine. This typically involves:
            * Importing `google.cloud.secretmanager`, `os`, and `logging`.
            * Adding a helper function (like `get_secret()` shown in the Phase 1 `settings.py` example) to retrieve secrets by name.
            * Using conditional logic (e.g., `if os.getenv('GAE_INSTANCE'):`) to execute this fetching logic only when deployed on App Engine.
            * Assigning the fetched secrets to your Django settings variables (`SECRET_KEY`, `DATABASES['default']['PASSWORD']`, etc.).
            * Ensure your `settings.py` still provides fallbacks (e.g., using `os.getenv()` for proxy variables) for local development.
            * *(Optional but Recommended):* Add an environment variable like `USE_PROGRAMMATIC_SECRETS: 'True'` in the `env_variables:` section of `app.yaml` and check for it in `settings.py` to explicitly enable the workaround code path.
        * **Grant Permissions:** Double-check the App Engine service account (`YOUR_PROJECT_ID@appspot.gserviceaccount.com`) still has the `Secret Manager Secret Accessor` role for the required secrets.
        * **Deploy:** Run `gcloud app deploy` again. Since `app.yaml` no longer contains the problematic key, parsing should succeed. Your application code will now fetch secrets when it starts.

    **Important:** Remember that programmatic fetching is a **workaround** for the parsing issue. The standard `secret_env_variables` approach in `app.yaml` is generally preferred for its simplicity when it works correctly. Monitor the issue tracker or support channels for a permanent fix.

    ```

---

Remember to save the changes to your `Django_Deployment_App_Engine.txt` file after applying these updates.