# src/core/settings_local.py
from .settings import *  # Imports settings from core/settings.py

# Overrides the database to always use SQLite
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
