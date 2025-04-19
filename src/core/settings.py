# src/core/settings.py

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Custom test runner to generate log files (Keep this if you use it)
TEST_RUNNER = "multi_choice_quiz.test_runner.LoggingTestRunner"

# --- Basic Security Settings ---
# Fetch the SECRET_KEY from an environment variable. Fallback for local dev ONLY.
# Ensure DJANGO_SECRET_KEY is set in your production environment (e.g., via gcloud deploy or Console)
DEBUG_TEMP_KEY = "django-insecure-m2*xxptb5lol_-d+nls$*n0p%1co9k5*vjm2h+to9ko#=q3a_s"  # Fallback ONLY for local
SECRET_KEY = os.getenv("SECRET_KEY", DEBUG_TEMP_KEY)  # Use SECRET_KEY consistently

# Fetch the DEBUG setting from an environment variable. Default to False (production).
# Ensure DEBUG is set to 'False' in your production environment
DEBUG = os.environ.get("DEBUG", "False") == "True"

# ALLOWED_HOSTS defines which domains this Django site can serve.
ALLOWED_HOSTS = []

# Automatically add App Engine domain and localhost/127.0.0.1 if in DEBUG mode
if DEBUG:
    ALLOWED_HOSTS.append("localhost")
    ALLOWED_HOSTS.append("127.0.0.1")

# Add App Engine URL structure. Replace YOUR_PROJECT_ID or fetch dynamically if needed.
# Alternatively, set ALLOWED_HOSTS via an environment variable in production.
# Example using project ID directly (replace with yours):
# ALLOWED_HOSTS.append("quiz-app-april-2025.appspot.com")
# ALLOWED_HOSTS.append("quiz-app-april-2025.uc.r.appspot.com") # Check your specific region URL if needed

# Better approach: Read from environment variable in production
# Ensure ALLOWED_HOSTS_PROD is set in your production env (e.g., "host1.com,host2.appspot.com")
allowed_hosts_prod = os.environ.get("ALLOWED_HOSTS_PROD")
if allowed_hosts_prod:
    ALLOWED_HOSTS.extend([host.strip() for host in allowed_hosts_prod.split(",")])

# If still empty in production (fallback, less secure), allow App Engine domains
if not DEBUG and not allowed_hosts_prod:
    ALLOWED_HOSTS.append(
        ".appspot.com"
    )  # Allows any appspot domain - refine if possible

# --- Application definition ---

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Whitenoise - Place BEFORE django.contrib.staticfiles
    "whitenoise.runserver_nostatic",  # Only effective when DEBUG=True
    "django.contrib.staticfiles",
    # Your apps
    "multi_choice_quiz",
    "pages",
    "pwa",  # Django-PWA app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise Middleware: Placed after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Project-level templates dir
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

WSGI_APPLICATION = "core.wsgi.application"


# --- Database Configuration ---
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Default to SQLite if DB env vars aren't set (suitable for local dev)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # Use Path object directly
    }
}

# Read database settings from environment variables for production
# Ensure these are set in your production environment (e.g., via gcloud deploy or Console)
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get(
    "DB_HOST"
)  # For App Engine + Cloud SQL, this is typically the socket path
DB_PORT = os.environ.get("DB_PORT", "5432")  # Default PostgreSQL port

# If running on App Engine or DB_HOST is set (indicating PostgreSQL config)
# The check for GAE_INSTANCE is a common way to detect App Engine environment
if os.getenv("GAE_INSTANCE") or DB_HOST:
    # App Engine uses a Unix socket for Cloud SQL connection via beta_settings
    # The DB_HOST environment variable should be set to the socket path:
    # e.g., '/cloudsql/YOUR_PROJECT_ID:YOUR_REGION:YOUR_INSTANCE_NAME'
    # Ensure this path matches the instance connection name in app.yaml's beta_settings
    if not DB_HOST or not DB_HOST.startswith("/cloudsql/"):
        # If DB_HOST isn't set correctly for App Engine, try to construct it
        # This requires knowing the project ID, region, and instance name
        # It's better to set DB_HOST explicitly in the environment
        print(
            "WARNING: DB_HOST environment variable not set or invalid for Cloud SQL socket. Database connection might fail."
        )
        # Example construction (replace placeholders):
        # project_id = "quiz-app-april-2025"
        # region = "us-central1" # Example region
        # instance = "quiz-app-db" # Example instance name
        # DB_HOST = f'/cloudsql/{project_id}:{region}:{instance}'

    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,  # Socket path for App Engine
        "PORT": DB_PORT,  # Usually ignored when using Unix socket, but set anyway
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
# https://whitenoise.readthedocs.io/

STATIC_URL = "static/"

# Directory where collectstatic gathers files for deployment
# This MUST match the 'static_dir' in app.yaml's handler
STATIC_ROOT = BASE_DIR / "staticfiles"

# Optional: Directory for project-level static files (not inside an app)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Whitenoise storage backend for optimized static file handling (compression, caching headers)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login redirect behavior
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "login"  # Assuming you have a URL named 'login'
LOGOUT_REDIRECT_URL = "/"


# --- Production Security Settings ---
# Apply these when DEBUG is False (i.e., in production)
if not DEBUG:
    CSRF_COOKIE_SECURE = True  # Use HTTPS only for CSRF cookie
    SESSION_COOKIE_SECURE = True  # Use HTTPS only for session cookie
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = True  # Redirect HTTP requests to HTTPS

    # HTTP Strict Transport Security (HSTS) - uncomment and configure if needed
    # SECURE_HSTS_SECONDS = 31536000 # 1 year
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True # Optional: requires submission to preload list


# --- PWA Settings (django-pwa) ---
# (Keep your existing PWA settings here)
PWA_APP_NAME = "QuizMaster"
PWA_APP_SHORT_NAME = "QuizMaster"
PWA_APP_DESCRIPTION = "An interactive quiz application built with Django and Alpine.js"
PWA_APP_THEME_COLOR = "#7C3AED"
PWA_APP_BACKGROUND_COLOR = "#0F172A"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_START_URL = "/"
PWA_APP_ICONS = [
    {
        "src": "/static/images/icons/icon-192x192.png",  # Ensure this path is correct relative to STATIC_URL
        "sizes": "192x192",
        "type": "image/png",
        "purpose": "any maskable",
    },
    {
        "src": "/static/images/icons/icon-512x512.png",  # Ensure this path is correct relative to STATIC_URL
        "sizes": "512x512",
        "type": "image/png",
        "purpose": "any maskable",
    },
]
# Add other PWA settings as needed
