# src/core/settings.py
import os
from pathlib import Path
import environ
import socket  # <-- Added import

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize django-environ
env = environ.Env(
    # Set defaults for key configuration values
    DEBUG=(bool, False),
    DJANGO_ENVIRONMENT=(str, "development"),
    SECRET_KEY=(str, "django-insecure-key-for-dev-only"),
)

# Read .env file ONLY in development environment
# (Assuming .env is in BASE_DIR (src/), adjust if needed)
if env("DJANGO_ENVIRONMENT") == "development":
    dotenv_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(dotenv_path):
        environ.Env.read_env(dotenv_path)

# --- SECURITY SETTINGS ---
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

# --- HOSTING SETTINGS (Option 2: Wildcard ALLOWED_HOSTS) ---
# Get Cloud Run specific variables if they exist
K_REVISION = env("K_REVISION", default=None)

# Use a wildcard for Cloud Run's domain, plus localhost/127.0.0.1
ALLOWED_HOSTS = [
    ".run.app",  # Allows any *.run.app domain (Note the leading dot)
    "localhost",
    "127.0.0.1",
]

# Add internal IP for potential health checks when on Cloud Run
if K_REVISION:
    try:
        ALLOWED_HOSTS.append(socket.gethostbyname(socket.gethostname()))
    except socket.gaierror:
        # Handle case where hostname might not be resolvable initially
        pass

# CSRF_TRUSTED_ORIGINS requires the specific URL scheme + hostname
# Use the exact URL from your deployment output
CSRF_TRUSTED_ORIGINS = ["https://quiz-app-service-62863504143.us-central1.run.app"]

# Determine environment based on DEBUG for simplicity now
if DEBUG:
    DJANGO_ENVIRONMENT = "development"
    # Add local origins for development CSRF checks
    CSRF_TRUSTED_ORIGINS.extend(["http://localhost:8000", "http://127.0.0.1:8000"])
else:
    # Assume non-DEBUG is production-like on Cloud Run
    DJANGO_ENVIRONMENT = "production"
    # Optional: Add production security settings here if desired
    # SECURE_SSL_REDIRECT = True
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True
    # etc.

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Whitenoise added BEFORE staticfiles
    "whitenoise.runserver_nostatic",  # Only if using runserver with whitenoise in DEV
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
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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
# Keep the logic to differentiate database based on environment
# Using K_REVISION is a simple way to check if running on Cloud Run here
if K_REVISION:
    # Running on Cloud Run - build config using secrets/env vars
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            # Use the standard Cloud SQL socket path
            # *** Confirm this matches your instance connection name ***
            "HOST": "/cloudsql/quiz-app-april-2025:us-central1:quiz-app-db",
            "PORT": "5432",
        }
    }
else:
    # Local development - use DATABASE_URL or fallback to SQLite
    DATABASES = {
        "default": env.db_url(
            "DATABASE_URL",
            default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        )
    }
    # Optional: Proxy config for local testing (keep commented unless needed)
    # if env('USE_PROXY_DB', cast=bool, default=False):
    #     DATABASES = { ... proxy config ... }

# --- AUTHENTICATION ---
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


# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# --- STATIC FILES ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Use Whitenoise storage for efficient serving in production
# Make sure 'whitenoise.storage.CompressedManifestStaticFilesStorage' is used
# If you want whitenoise to work with runserver in DEV, ensure middleware is configured correctly
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# --- DEFAULTS ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "/"


# --- TESTING ---
# Use the DJANGO_ENVIRONMENT variable set near the top
if DJANGO_ENVIRONMENT == "development":
    TEST_RUNNER = "multi_choice_quiz.test_runner.LoggingTestRunner"


# --- PWA ---
PWA_APP_ICONS = [
    {
        "src": "/static/images/icons/icon-192x192.png",
        "sizes": "192x192",
    },
    {
        "src": "/static/images/icons/icon-512x512.png",
        "sizes": "512x512",
    },
]
PWA_APP_NAME = "QuizMaster"
PWA_APP_SHORT_NAME = "QuizMaster"
PWA_APP_DESCRIPTION = "An interactive quiz application"
PWA_APP_THEME_COLOR = "#7C3AED"
PWA_APP_BACKGROUND_COLOR = "#0F172A"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_START_URL = "/"


# --- LOGGING ---
# Keep your existing logging configuration which outputs to console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": (
                "{levelname} {asctime} {module} {message}"
                if DEBUG
                else "{levelname} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "multi_choice_quiz": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "pages": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        # 'gunicorn.error': { ... },
        # 'gunicorn.access': { ... },
    },
}
