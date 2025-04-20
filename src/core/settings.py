import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Custom test runner to generate log files
TEST_RUNNER = "multi_choice_quiz.test_runner.LoggingTestRunner"
SECRET_KEY = (
    "django-insecure-4@#&*j3g1v2!$@8^5bqz0r6x7c3f1g3h4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z"
)

# Environment determination
DEBUG = True


ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Whitenoise - essential for serving static files efficiently in prod
    # Place it BEFORE django.contrib.staticfiles
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "multi_choice_quiz",
    "pages",
    "pwa",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise Middleware: Should be placed high up, right after SecurityMiddleware
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

WSGI_APPLICATION = "core.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
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
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"

# STATIC_ROOT: The directory where collectstatic will gather all static files
STATIC_ROOT = BASE_DIR / "staticfiles"

# STATICFILES_STORAGE: Use Whitenoise's specialized storage backend
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login redirect
LOGIN_REDIRECT_URL = "/"


# --- PWA Settings ---

# Define the icons for your PWA (create these files)
PWA_APP_ICONS = [
    {
        "src": "/static/images/icons/icon-192x192.png",  # Example path, adjust as needed
        "sizes": "192x192",
    },
    {
        "src": "/static/images/icons/icon-512x512.png",  # Example path, adjust as needed
        "sizes": "512x512",
    },
    # Add more sizes if needed (e.g., 144x144, etc.)
]

# Define the manifest settings
PWA_APP_NAME = "QuizMaster"
PWA_APP_SHORT_NAME = "QuizMaster"
PWA_APP_DESCRIPTION = "An interactive quiz application"
PWA_APP_THEME_COLOR = "#7C3AED"  # Your primary accent color (purple-600)
PWA_APP_BACKGROUND_COLOR = "#0F172A"  # Your primary background (slate-900)

# *** This is key for fullscreen/standalone ***
PWA_APP_DISPLAY = "standalone"  # Recommended: App-like feel without browser UI
# OR use 'fullscreen' for a more immersive experience (hides status bars)
# PWA_APP_DISPLAY = 'fullscreen'

# Define the scope and start URL
PWA_APP_SCOPE = "/"  # Scope of the PWA (usually the root)
PWA_APP_START_URL = "/"  # Where the app starts when launched from home screen (e.g., your home page URL)

# Optional: Service worker settings (default is usually fine initially)
# PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static/js', 'serviceworker.js') # Example custom path
