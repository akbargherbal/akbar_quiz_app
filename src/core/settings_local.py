# src/core/settings_local.py
from .settings import *  # Imports base settings from core/settings.py

# --- Development Overrides ---

# Use SQLite for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Dev-only Installed Apps ---
INSTALLED_APPS += [
    "django_extensions",      # Handy management commands and shell enhancements
    "debug_toolbar",          # Django Debug Toolbar for profiling and debugging
]

# --- Dev-only Middleware ---
# Insert Debug Toolbar middleware just after CommonMiddleware
COMMON_INDEX = MIDDLEWARE.index("django.middleware.common.CommonMiddleware")
MIDDLEWARE.insert(
    COMMON_INDEX + 1,
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

# --- Debug Toolbar Configuration ---
# Only show toolbar for these internal IPs
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

DEBUG_TOOLBAR_CONFIG = {
    # Collapse panels by default
    "SHOW_COLLAPSED": True,
    # Show toolbar when DEBUG is True
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# --- Shell Plus Configuration ---
SHELL_PLUS = "ipython"   # Use IPython for `manage.py shell_plus`
