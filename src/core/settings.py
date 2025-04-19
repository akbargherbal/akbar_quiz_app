# src/core/settings.py

from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Custom test runner to generate log files (Keep this if you use it)
TEST_RUNNER = "multi_choice_quiz.test_runner.LoggingTestRunner"

SECRET_KEY = "django-insecure-m2*xxptb5lol_-d+nls$*n0p%1co9k5*vjm2h+to9ko#=q3a_s"

DEBUG = True

ALLOWED_HOSTS = []

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
        "DIRS": [BASE_DIR / "templates"],  # Add project-level templates if needed
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


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

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
STATIC_ROOT = BASE_DIR / "staticfiles"  # Directory where collectstatic gathers files
STATICFILES_DIRS = [
    BASE_DIR / "static",
]  # Uncomment if you have project-level static files


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login redirect behavior
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "/"


# --- PWA Settings (django-pwa) ---
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
        "src": "/static/images/icons/icon-192x192.png",
        "sizes": "192x192",
        "type": "image/png",
        "purpose": "any maskable",
    },
    {
        "src": "/static/images/icons/icon-512x512.png",
        "sizes": "512x512",
        "type": "image/png",
        "purpose": "any maskable",
    },
]
# Add other PWA settings as needed
