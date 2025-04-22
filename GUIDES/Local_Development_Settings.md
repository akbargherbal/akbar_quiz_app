# Strategy for Separate Django Development Settings

This document outlines a strategy for introducing development-specific settings into a Django project without modifying the existing production `core/settings.py` file. This approach prioritizes minimal intrusion and preserves the production configuration.

## Strategy: Using `local_settings.py`

The most common and minimally intrusive method for handling environment-specific settings in Django is to create a separate file (e.g., `local_settings.py`) that imports the base settings and then overrides specific values for the development environment.

### 1. Create `local_settings.py`

Place this new file inside the same directory as your main settings file (`src/core/`).

**Example `src/core/local_settings.py`:**

```python
# src/core/local_settings.py
# Import everything from the base settings file (which should not be modified)
from .settings import * # noqa F403 - Ignore "star import" warnings here

# --- Development-Specific Overrides ---

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow local development hosts
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# Use SQLite database for local development
# This overrides the PostgreSQL/Cloud SQL configuration from settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3", # BASE_DIR is imported from settings.py
    }
}

# Use console email backend for development (emails print to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Add development-only apps (e.g., Django Debug Toolbar)
# Make sure 'debug_toolbar' is installed (`pip install django-debug-toolbar`)
# INSTALLED_APPS += ["debug_toolbar"] # Uncomment if using debug_toolbar

# Add middleware for development-only apps
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"] # Uncomment if using debug_toolbar

# Required for Django Debug Toolbar
# INTERNAL_IPS = [
#     "127.0.0.1",
# ] # Uncomment if using debug_toolbar

# Optional: Override other settings like logging levels for development if needed
# For example, to see more detailed SQL queries:
# LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'

# --- End of Development Overrides ---

# Note: Any setting *not* defined here will retain its value from core.settings.py
```

### Explanation:

- `from .settings import *`: Imports all variables from the original `core/settings.py`.
- **Overrides**: Subsequent variable assignments (like `DEBUG = True`, `DATABASES = {...}`) replace the values imported from `core.settings.py` specifically for the environment using `local_settings.py`.
- **BASE_DIR**: This variable is available because it was imported from `core.settings.py`.
- **Development Apps**: The example includes commented-out lines for adding django-debug-toolbar. Remember to install it (`pip install django-debug-toolbar`) if you uncomment these lines.

### 2. Switching Between Environments (DJANGO_SETTINGS_MODULE)

The `DJANGO_SETTINGS_MODULE` environment variable tells Django which settings file to use.

#### For Production:

Set `DJANGO_SETTINGS_MODULE` to `core.settings`.

This is often handled by your deployment environment (e.g., Cloud Run environment variables) or defaults in `wsgi.py`/`asgi.py`. Ensure your production environment explicitly sets or defaults to `core.settings`.

#### For Development:

Set `DJANGO_SETTINGS_MODULE` to `core.local_settings` before running Django commands (`runserver`, `manage.py`, etc.).

**Methods:**

**.env File (Recommended)**: Add this line to your `src/.env` file (which django-environ reads):

```
# src/.env
DJANGO_SETTINGS_MODULE=core.local_settings
# Other dev vars (DEBUG, SECRET_KEY, DATABASE_URL) can also be here.
# Settings in local_settings.py override .env values if DJANGO_SETTINGS_MODULE points there.
DEBUG=True
SECRET_KEY=your-dev-secret-key # Use a distinct development key
# DATABASE_URL=sqlite:///db.sqlite3 # Alternative for django-environ
```

**Note:** It's best practice for `local_settings.py` to explicitly define `DEBUG` and `DATABASES` to ensure clarity and override any base settings logic.

**Shell Export (Temporary Session):**

- Linux/macOS: `export DJANGO_SETTINGS_MODULE=core.local_settings`
- Windows (CMD): `set DJANGO_SETTINGS_MODULE=core.local_settings`
- Windows (PowerShell): `$env:DJANGO_SETTINGS_MODULE = "core.local_settings"`

Then run your Django command (e.g., `python manage.py runserver`).

**IDE Launch Configuration:** Configure your IDE (VS Code, PyCharm) to set the `DJANGO_SETTINGS_MODULE` environment variable to `core.local_settings` for your Django run/debug configurations.

### 3. .gitignore

Ensure `local_settings.py` and `.env` files are not committed to version control. Add `core/local_settings.py` to your `src/.gitignore` file:

```
# src/.gitignore

# Environment-specific settings
core/local_settings.py

# Environment variables file (already likely covered)
.env
.env.*
*.env

# Other standard ignores...
```

## TL;DR: Steps Involved

1. Create `src/core/local_settings.py`.
2. **Import base settings**: Start `local_settings.py` with `from .settings import *`.
3. **Add overrides**: Define development-specific settings in `local_settings.py` (e.g., `DEBUG = True`, `DATABASES` for SQLite, `EMAIL_BACKEND`).
4. **Set Environment Variable for Dev**: Configure your development environment to use the new settings by setting `DJANGO_SETTINGS_MODULE=core.local_settings` (use `.env`, shell export, or IDE configuration).
5. **Ensure Production Uses Base Settings**: Verify your production deployment sets `DJANGO_SETTINGS_MODULE=core.settings`.
6. **Update .gitignore**: Add `core/local_settings.py` to prevent committing development settings.
