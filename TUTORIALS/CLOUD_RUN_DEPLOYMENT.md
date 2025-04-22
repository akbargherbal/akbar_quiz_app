# **REVISED** Guide: Deploying the Django Quiz App (`akbar_quiz_app`) to GCP Cloud Run

## 1. Introduction

_(This section remains largely the same as the original guide)_

**Goal:** Deploy your specific Django Quiz App (`akbar_quiz_app`) to Google Cloud Run, making it accessible on the web using Cloud SQL for the database[cite: 1].

**Why Cloud Run?** Cloud Run runs your containerized application (using Docker) in a serverless environment, managing infrastructure and scaling. It's a flexible alternative to App Engine[cite: 1].

**The Big Picture:** We will containerize your Django app using Docker, set up a Cloud SQL PostgreSQL database, securely manage credentials with Secret Manager, configure Django to connect correctly, deploy the container to Cloud Run, and run database migrations[cite: 1].

**Learning Objectives:**

- Understand why SQLite is unsuitable for Cloud Run[cite: 1].
- Set up and configure a Cloud SQL (PostgreSQL) instance[cite: 1].
- Securely store database credentials using Secret Manager[cite: 1].
- Configure your Django app (`settings.py`) for Cloud Run (PostgreSQL) vs. local development (SQLite)[cite: 1].
- Create a `Dockerfile` and `.dockerignore` for your application[cite: 1].
- Deploy your containerized application to Cloud Run using `gcloud`[cite: 1].
- Handle database migrations reliably using Cloud Shell[cite: 1].
- Understand how static files are served using WhiteNoise[cite: 1].

## 2. Prerequisites

_(This section remains largely the same, ensure APIs are enabled)_

1.  **GCP Account & Project:** Active account with billing enabled, and your Project ID noted[cite: 1].
2.  **`gcloud` CLI:** Installed, initialized (`gcloud init`), authenticated (`gcloud auth login`), and configured for your project (`gcloud config set project YOUR_PROJECT_ID`)[cite: 1].
3.  **Enabled APIs:** Ensure necessary APIs are enabled:
    ```bash
    gcloud services enable run.googleapis.com \
                           sqladmin.googleapis.com \
                           secretmanager.googleapis.com \
                           cloudbuild.googleapis.com \
                           artifactregistry.googleapis.com
    ```
    _(Run this command in your local terminal or Cloud Shell)_ [cite: 1]
4.  **Your Codebase:** Your `akbar_quiz_app` project code ready locally[cite: 1].
5.  **Code Editor**[cite: 1].
6.  **(Recommended) Verify Project Integrity:** Before starting, ensure your local Django project is complete and functional. Double-check `src/core/settings.py`[cite: 2].

## 3. Step-by-Step Deployment Guide

### Step 1: The Database Dilemma - From SQLite to Cloud SQL

Your app currently uses SQLite (`db.sqlite3`). Cloud Run's temporary filesystem requires a persistent, external database like Cloud SQL. We'll use PostgreSQL[cite: 1].

### Step 2: Set Up Cloud SQL (PostgreSQL)

_(This section remains largely the same, but clarifies Private IP implications)_

1.  **Navigate:** Go to the [GCP Console](https://console.cloud.google.com/) -> SQL[cite: 1].
2.  **Create Instance:** Click "Create Instance" -> "Choose PostgreSQL"[cite: 1].
3.  **Instance ID:** e.g., `quiz-app-db`[cite: 1].
4.  **Password:** Set a strong password for the default `postgres` user. **Save this securely**[cite: 1].
5.  **Version & Region:** Choose PostgreSQL 15 (or newer). Select your desired region (e.g., `us-central1`). **Remember this region**[cite: 1].
6.  **Configuration:** Choose "Development" edition initially for lower cost[cite: 1].
7.  **Network Access (Public vs. Private IP):**
    - Expand "Connections" -> "Networking"[cite: 1].
    - **Private IP:** This is generally **recommended for security**. Only allows connections from within the same VPC network (like Cloud Run). Requires selecting a VPC network (e.g., `default`)[cite: 1]. **Note:** If you choose Private IP _only_, the "Local Proxy Method" for running migrations (Step 8 Alternative) **will not work**. You **must** use Cloud Shell[cite: 1].
    - **Public IP:** Allows connections from anywhere (still requires authorization). Makes the "Local Proxy Method" in Step 8 possible but is less secure[cite: 1].
    - **Recommendation:** Start with **Private IP enabled**. You can temporarily enable Public IP later if absolutely needed for specific debugging, but aim to keep it off[cite: 1].
8.  **Create:** Click "Create Instance". Wait for provisioning[cite: 1].
9.  **Create Database:** Once ready, click instance name -> "Databases" tab -> "Create database". Name it `quiz_db`[cite: 1].
10. **Create Dedicated User (Recommended):** Go to "Users" tab -> "Create user account".
    - Username: `quiz_user`
    - Password: Set a **different strong password**. **Save this securely.**
    - Click "Create"[cite: 1].
11. **Get Connection Name:** Go to the instance "Overview" tab. Copy the **Instance connection name** (e.g., `YOUR_PROJECT_ID:REGION:INSTANCE_ID`, like `quiz-app-april-2025:us-central1:quiz-app-db`)[cite: 1].
12. **Verify Creation:** Double-check that the `quiz_db` database and the `quiz_user` user exist[cite: 1].

### Step 3: Secure Credentials with Secret Manager

_(This section remains the same)_

Store your database credentials securely.

1.  **Navigate:** Go to [GCP Console](https://console.cloud.google.com/) -> Security -> Secret Manager[cite: 1].
2.  **Create Secrets:** Click "Create Secret" for each:
    - `quiz-db-name`: Value = `quiz_db`
    - `quiz-db-user`: Value = `quiz_user` (or `postgres`)
    - `quiz-db-password`: Value = The password for the user specified above.
    - `django-secret-key`: Value = A _new_, strong, randomly generated Django secret key (do not reuse your development key). You can generate one locally using Django or an online tool[cite: 1].
3.  **Grant Access:** Cloud Run needs permission to read these secrets.
    - Find your Compute Engine default service account email (IAM & Admin -> Service Accounts, looks like `PROJECT_NUMBER-compute@developer.gserviceaccount.com`). Or, if you specified a different service account during deployment, use that one.
    - For **each** secret: Go to Secret Manager -> Click Secret Name -> Permissions tab -> "Grant Access".
    - Principals: Paste the service account email.
    - Role: Select "Secret Manager Secret Accessor".
    - Save[cite: 1].

### Step 4: Configure Django Settings (`settings.py`)

_(This section is significantly rewritten for clarity and uses the simpler, working configuration)_

Update `src/core/settings.py` to handle both Cloud Run (PostgreSQL) and local development (SQLite), fixing the `ALLOWED_HOSTS` issue encountered previously.

1.  **Install Packages:** Ensure `src/requirements.txt` includes `psycopg2-binary>=2.9`, `django-environ>=0.11`, `gunicorn>=20.0`, and `whitenoise>=6.0`. Install them locally if you haven't (`pip install -r src/requirements.txt`)[cite: 1].
2.  **Update `settings.py`:** Replace the _entire content_ of your `src/core/settings.py` with the version below. This version uses the simpler wildcard approach for `ALLOWED_HOSTS` that worked for you.

    ```python
    # src/core/settings.py
    import os
    from pathlib import Path
    import environ
    import socket # <-- Added import

    BASE_DIR = Path(__file__).resolve().parent.parent

    # Initialize django-environ
    env = environ.Env(
        # Set defaults for key configuration values
        DEBUG=(bool, False),
        DJANGO_ENVIRONMENT=(str, "development"),
        SECRET_KEY=(str, "django-insecure-key-for-dev-only"), # CHANGE IN PRODUCTION!
    )

    # Read .env file ONLY if it exists and we're in development
    # (Assuming .env is in BASE_DIR (src/), adjust if needed)
    dotenv_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(dotenv_path) and env("DJANGO_ENVIRONMENT") == "development":
        environ.Env.read_env(dotenv_path)

    # --- SECURITY SETTINGS ---
    SECRET_KEY = env("SECRET_KEY") # Reads from Secret Manager in Cloud Run
    DEBUG = env("DEBUG") # Reads from .env locally, defaults to False

    # --- HOSTING SETTINGS (Option 2: Wildcard ALLOWED_HOSTS) ---
    # Get Cloud Run specific variables if they exist
    K_REVISION = env("K_REVISION", default=None) # Used to detect Cloud Run env

    # Use a wildcard for Cloud Run's default domain, plus localhost/127.0.0.1
    # Allows any *.run.app hostname. Less secure but simpler for getting started.
    ALLOWED_HOSTS = [
        '.run.app', # Note the leading dot!
        'localhost',
        '127.0.0.1'
    ]

    # Add internal IP for potential health checks when on Cloud Run
    if K_REVISION:
        try:
            ALLOWED_HOSTS.append(socket.gethostbyname(socket.gethostname()))
        except socket.gaierror:
            pass # Ignore if hostname isn't resolvable

    # CSRF_TRUSTED_ORIGINS requires the specific URL scheme + hostname.
    # Replace with your *actual* Service URL after deployment!
    # Example: 'https://quiz-app-service-xxxxxxxxxx-uc.a.run.app'
    # You can get this from the 'gcloud run deploy' output.
    # For now, we add a placeholder - UPDATE THIS AFTER DEPLOYMENT
    # or retrieve dynamically if needed for more complex setups.
    CSRF_TRUSTED_ORIGINS = [
        # IMPORTANT: Replace with your exact service URL!
        'https://quiz-app-service-62863504143.us-central1.run.app'
    ]

    # Determine environment based on DEBUG for simplicity now
    if DEBUG:
         DJANGO_ENVIRONMENT = "development"
         # Add local origins for development CSRF checks
         CSRF_TRUSTED_ORIGINS.extend(['http://localhost:8000', 'http://127.0.0.1:8000'])
    else:
         # Assume non-DEBUG is production-like on Cloud Run
         DJANGO_ENVIRONMENT = "production"
         # Optional: Add production security settings here (recommended later)
         # SECURE_SSL_REDIRECT = True
         # SESSION_COOKIE_SECURE = True
         # CSRF_COOKIE_SECURE = True

    # --- APPLICATION DEFINITION ---
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        # Whitenoise MUST be before staticfiles
        "whitenoise.runserver_nostatic", # ONLY for runserver + whitenoise in DEV
        "django.contrib.staticfiles",
        # Your apps
        "multi_choice_quiz",
        "pages",
        "pwa",
    ]

    # --- MIDDLEWARE ---
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        # Whitenoise Middleware - place high up, right after SecurityMiddleware
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]

    # --- TEMPLATES ---
    TEMPLATES = [ # Ensure this section exists and is correct
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [], # Add project-level template dirs here if you have any
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    ]

    ROOT_URLCONF = "core.urls"
    WSGI_APPLICATION = "core.wsgi.application"

    # --- DATABASE ---
    # Differentiates DB based on Cloud Run environment detection
    if K_REVISION: # If K_REVISION env var exists, assume Cloud Run
        # Cloud Run: Use PostgreSQL via Cloud SQL Proxy socket and secrets
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": env("DB_NAME"), # From Secret Manager
                "USER": env("DB_USER"), # From Secret Manager
                "PASSWORD": env("DB_PASSWORD"), # From Secret Manager
                # *** IMPORTANT: Verify this matches your Cloud SQL Instance Connection Name ***
                "HOST": "/cloudsql/quiz-app-april-2025:us-central1:quiz-app-db",
                "PORT": "5432",
            }
        }
    else:
        # Local: Use DATABASE_URL from .env or default to SQLite
        DATABASES = {
            "default": env.db_url(
                "DATABASE_URL", # Check .env for DATABASE_URL=postgres://...
                default=f'sqlite:///{BASE_DIR / "db.sqlite3"}', # Fallback
            )
        }

    # --- AUTHENTICATION ---
    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    # --- INTERNATIONALIZATION ---
    LANGUAGE_CODE = "en-us"
    TIME_ZONE = "UTC"
    USE_I18N = True
    USE_TZ = True

    # --- STATIC FILES (Whitenoise) ---
    STATIC_URL = "static/"
    STATIC_ROOT = BASE_DIR / "staticfiles" # Directory where collectstatic gathers files
    # Recommended storage for Whitenoise efficiency
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

    # --- DEFAULTS ---
    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
    LOGIN_REDIRECT_URL = "/" # Or your desired redirect path

    # --- TESTING ---
    if DJANGO_ENVIRONMENT == "development":
        TEST_RUNNER = "multi_choice_quiz.test_runner.LoggingTestRunner"

    # --- PWA --- (Keep your existing PWA settings)
    PWA_APP_ICONS = [
        {"src": "/static/images/icons/icon-192x192.png", "sizes": "192x192"},
        {"src": "/static/images/icons/icon-512x512.png", "sizes": "512x512"},
    ]
    PWA_APP_NAME = "QuizMaster"
    # ... other PWA settings ...

    # --- LOGGING --- (Keep your existing logging config)
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": ("{levelname} {asctime} {module} {message}" if DEBUG else "{levelname} {message}"), "style": "{",},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "simple",},
        },
        "root": {"handlers": ["console"], "level": "INFO",},
        "loggers": {
            "django": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO"), "propagate": False,},
            # Add your app loggers if needed
        },
    }
    ```

3.  **Verify Settings:** Briefly check the `DATABASES` section's `HOST` value matches your Cloud SQL Instance Connection Name. Ensure your `CSRF_TRUSTED_ORIGINS` has the correct URL.

### Step 5: Create the `Dockerfile`

_(This section remains the same)_

Create `Dockerfile` (no extension) in your project **root** directory (the one containing `src/`).

```dockerfile
# Dockerfile (Use Python 3.11 or your project's version)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Optional: Install system dependencies if needed for psycopg2
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

# Run collectstatic DURING the build
RUN python manage.py collectstatic --noinput

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Use gunicorn to run the app
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--bind", "0.0.0.0:8080", "core.wsgi"]
```

### Step 6: Create `.dockerignore`

_(This section remains the same)_

Create `.dockerignore` in your project **root** directory. Ensure it includes entries like `venv/`, `.git/`, `db.sqlite3*`, `*.pyc`, `__pycache__/`, `logs/`, etc., to keep your container image small[cite: 17].

```
# .dockerignore (Example - use your existing comprehensive one)
.git
.gitignore
.dockerignore
Dockerfile
*.md
venv/
.venv/
env/
*.pyc
__pycache__/
db.sqlite3*
*.sqlite3*
staticfiles/ # Exclude local staticfiles dir
logs/
.env*
*.env
# Add other files/dirs specific to your local setup
```

### Step 7: Deploy to Cloud Run

_(This section remains largely the same)_

1.  Navigate to your project **root** directory (`akbar_quiz_app`) in your local terminal (with `venv` active).
2.  Run the deployment command (replace placeholders only if they differ from your setup):

    ```bash
    gcloud run deploy quiz-app-service ^
        --source . ^
        --region us-central1 ^
        --allow-unauthenticated ^
        --add-cloudsql-instances quiz-app-april-2025:us-central1:quiz-app-db ^
        --update-secrets=DB_PASSWORD=quiz-db-password:latest ^
        --update-secrets=DB_USER=quiz-db-user:latest ^
        --update-secrets=DB_NAME=quiz-db-name:latest ^
        --update-secrets=SECRET_KEY=django-secret-key:latest
    ```

    _(Use `\` instead of `^` for line continuation on Linux/macOS/PowerShell)_.

3.  **Note the Service URL:** Carefully copy the `Service URL` provided in the output after deployment finishes. You'll need it for testing and potentially updating `CSRF_TRUSTED_ORIGINS` if you didn't hardcode the correct one in Step 4.

### Step 8: Run Database Migrations (via Cloud Shell)

_(This section is rewritten to prioritize Cloud Shell)_

Your deployed application code is ready, but the Cloud SQL database is still empty. You need to create the tables using Django migrations. The **recommended way** is using Cloud Shell, as it avoids potential local connection issues, especially with Private IP databases.

1.  **Open Cloud Shell:** Go to the [Google Cloud Console](https://console.cloud.google.com/) and click the "Activate Cloud Shell" icon ( `>_` ).
2.  **Clone Your Repository:** If you haven't already, get your code into Cloud Shell:
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory> # e.g., cd akbar_quiz_app
    ```
3.  **Set up Python Environment:** Create and activate a virtual environment and install requirements:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r src/requirements.txt
    ```
4.  **Install Cloud SQL Auth Proxy:**
    ```bash
    wget https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.1/cloud-sql-proxy.linux.amd64 -O cloud-sql-proxy
    chmod +x cloud-sql-proxy
    ```
5.  **Run Proxy in Background:** Start the proxy connecting to your instance. The `&` runs it in the background.
    ```bash
    ./cloud-sql-proxy quiz-app-april-2025:us-central1:quiz-app-db --port 5433 &
    ```
    _(Wait a few seconds for the "ready for new connections" message)_
6.  **Set Environment Variables for Django:** Tell Django how to connect via the proxy by setting the `DATABASE_URL`. We fetch credentials directly from Secret Manager here:

    ```bash
    # Fetch secrets (ensure names match yours)
    export DB_NAME=$(gcloud secrets versions access latest --secret=quiz-db-name --project=quiz-app-april-2025)
    export DB_USER=$(gcloud secrets versions access latest --secret=quiz-db-user --project=quiz-app-april-2025)
    export DB_PASSWORD=$(gcloud secrets versions access latest --secret=quiz-db-password --project=quiz-app-april-2025)

    # Configure DATABASE_URL for proxy connection
    export DATABASE_URL="postgres://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5433/${DB_NAME}"

    # Tell Django which settings file to use
    export DJANGO_SETTINGS_MODULE=core.settings
    ```

7.  **Run Migrations:** Execute the migrate command from the directory containing `manage.py` (i.e., `src/`):
    ```bash
    cd src
    python manage.py migrate
    ```
8.  **(Optional) Create Superuser:** To access the `/admin/` interface:
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts.
9.  **Stop Proxy (Optional):** Find the proxy process ID (`ps aux | grep cloud-sql-proxy`) and stop it (`kill <pid>`).

### Step 9: Test the Deployed App

_(This section remains the same)_

Open the **Service URL** (e.g., `https://quiz-app-service-62863504143.us-central1.run.app`) you noted from the `gcloud run deploy` output in your browser. Check the main page and `/admin/` (if you created a superuser)[cite: 1].

## 4. Troubleshooting

_(This section is updated based on our findings)_

- **400 Bad Request / `DisallowedHost` Error:**
  - **Check Cloud Run Logs:** Go to Cloud Run -> Your Service -> Logs. Find the error entry. It will show the _exact_ `HTTP_HOST header` being rejected.
  - **Verify `settings.py`:** Ensure the rejected hostname is allowed by your `ALLOWED_HOSTS` setting. Using `'.run.app'` should cover standard Cloud Run URLs. Also, ensure the _full URL_ (including `https://`) is listed in `CSRF_TRUSTED_ORIGINS`.
  - **Redeploy:** If you change `settings.py`, you _must_ redeploy.
- **5xx Server Errors / Application Not Starting:**
  - **Check Cloud Run Logs:** Look for Python tracebacks, Gunicorn errors, or messages indicating issues connecting to the database or accessing secrets during startup.
  - **Secret Manager Permissions:** Double-check that the service account used by Cloud Run (usually `PROJECT_NUMBER-compute@developer.gserviceaccount.com` unless specified otherwise) has the "Secret Manager Secret Accessor" role for _all_ secrets used (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`).
  - **Database Connection:** Ensure the Cloud SQL Instance Connection Name in `settings.py` (`HOST: "/cloudsql/..."`) is correct and the Cloud SQL instance is running.
  - **Migrations:** Confirm that migrations (Step 8) were run successfully against the Cloud SQL database.
- **Static Files Not Loading (404s):** Ensure `whitenoise.middleware.WhiteNoiseMiddleware` is correctly placed in `settings.py` (high up), `STATICFILES_STORAGE` is set to `whitenoise.storage.CompressedManifestStaticFilesStorage`, and `RUN python manage.py collectstatic --noinput` ran successfully during the Docker build (check Cloud Build logs linked in deployment output)[cite: 1].
- **Local Proxy Error: 'instance does not have IP of type PUBLIC'**: This occurs when trying the _local_ proxy method (Step 8 Alternative) against a Cloud SQL instance with only a Private IP. Use the Cloud Shell method instead[cite: 1].

## 5. Next Steps

_(This section remains the same)_

- Custom Domain mapping.
- CI/CD automation (Cloud Build triggers).
- Configure Cloud Storage for user media uploads (if needed).
- Monitoring & Logging exploration[cite: 1].

## 6. Conclusion

_(This section remains largely the same)_

You've deployed your Django app to Cloud Run with Cloud SQL! This revised guide incorporates lessons learned to handle database configuration, secret management, `ALLOWED_HOSTS` settings, and database migrations more reliably for beginners[cite: 1].

---

## Appendix A: Bulk Importing Quiz Data

If you have existing quiz data (like in a Pandas DataFrame saved as a `.pkl` file) and want to import it into your _deployed_ Cloud SQL database, you can use your `src/import_chapter_quizzes.py` script via Cloud Shell.

**Prerequisites:**

- Your application is successfully deployed (Steps 1-7 completed).
- Database migrations have been run (Step 8 completed).
- Your `import_chapter_quizzes.py` script correctly uses Django's ORM to interact with the database[cite: 103].
- You have the quiz bank data file (e.g., `quiz_bank.pkl`) ready.

**Steps:**

1.  **Activate Cloud Shell:** Open Cloud Shell in the GCP Console.
2.  **Navigate & Activate Env:**
    ```bash
    cd <your-repository-directory> # e.g., cd akbar_quiz_app
    source venv/bin/activate
    ```
3.  **Ensure Data File is Present:**
    - If the data file (e.g., `data/quiz_bank.pkl`) is in your Git repo, it should be present after cloning. Verify with `ls data/`.
    - If not, upload it using the Cloud Shell menu (⋮ -> Upload) and note its path (e.g., `~/quiz_bank.pkl`).
4.  **Start Cloud SQL Auth Proxy:** Run the proxy in the background:
    ```bash
    ./cloud-sql-proxy quiz-app-april-2025:us-central1:quiz-app-db --port 5433 &
    ```
5.  **Set Environment Variables:** Configure the database connection for your script:

    ```bash
    # Fetch secrets
    export DB_NAME=$(gcloud secrets versions access latest --secret=quiz-db-name --project=quiz-app-april-2025)
    export DB_USER=$(gcloud secrets versions access latest --secret=quiz-db-user --project=quiz-app-april-2025)
    export DB_PASSWORD=$(gcloud secrets versions access latest --secret=quiz-db-password --project=quiz-app-april-2025)

    # Configure DATABASE_URL for Django settings
    export DATABASE_URL="postgres://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5433/${DB_NAME}"

    # Ensure Django settings are loaded
    export DJANGO_SETTINGS_MODULE=core.settings
    ```

6.  **Run the Import Script:** Execute your script (adjust path if needed):
    ```bash
    python src/import_chapter_quizzes.py
    ```
    - When prompted by the script, enter the correct path to your quiz bank file within Cloud Shell (e.g., `data/quiz_bank.pkl` or `~/quiz_bank.pkl`).
7.  **Monitor & Verify:** Check the script's console output and its log file (`src/logs/quiz_import_*.log`)[cite: 103]. Verify the data in the `/admin/` interface of your live application.
8.  **Stop Proxy (Optional):** Use `ps aux | grep cloud-sql-proxy` and `kill <pid>`.
