# Pages App

The Pages app provides the public-facing pages for the Django Quiz App, including the home page, quiz browser, about page, and placeholder pages for user authentication.

## Features

- Modern, responsive UI using Tailwind CSS
- Purple color scheme based on the project's color palette
- Consistent layout with header and footer
- Placeholder pages for future functionality (login, signup, profile)

## Directory Structure

```
pages/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── static/
│   └── css/
│       └── base.css           # Legacy CSS (maintained for reference)
├── templates/
│   └── pages/
│       ├── about.html         # About us page
│       ├── base.html          # Main template with Tailwind CSS
│       ├── home.html          # Homepage with featured quizzes
│       ├── login.html         # Placeholder login page
│       ├── profile.html       # Placeholder user profile
│       ├── quizzes.html       # Quiz browser/catalog
│       └── signup.html        # Placeholder registration page
├── tests/
│   ├── __init__.py
│   └── test_templates.py      # Playwright tests for templates
├── urls.py                    # URL routing for pages app
└── views.py                   # View functions for all pages
```

## Setup

The Pages app is already included in the Django project's `INSTALLED_APPS` and should be ready to use without additional setup.

### Key URLs

- `/` - Home page
- `/quizzes/` - Browse and filter quizzes
- `/about/` - About page
- `/login/` - Placeholder login page (non-functional)
- `/signup/` - Placeholder signup page (non-functional)
- `/profile/` - Placeholder user profile (non-functional)

## Testing

### Running Backend Tests

```bash
# Run all tests in the Pages app
python manage.py test pages

# Run specific test file
python manage.py test pages.tests.test_views
```

### Running End-to-End Tests

The Pages app includes Playwright tests for validating the UI templates:

1. Make sure you're in the root directory (`src/`):
   ```bash
   cd src
   ```

2. Run the dedicated Pages E2E test runner:
   ```bash
   python run_pages_e2e_tests.py
   ```

### Test Logs

All test logs for the Pages app are stored in the app-specific log directory:
```
src/logs/pages/
```

Log files include:
- E2E test logs: `e2e_runner_*.log`
- Django test logs: `test_views.log` 
- Template test logs: `test_templates.log`
- Screenshots: `home_page.png`, `failure_*.png`, etc.

## Technology Stack

- **Django** - Backend framework
- **Tailwind CSS** - Utility-first CSS framework (via CDN)
- **Alpine.js** - JavaScript framework for enhancing interactivity

## Color Palette

The Pages app implements a custom purple color palette defined in the base template:

- **Background Primary**: `#0F172A` (slate-900)
- **Background Secondary**: `#1E293B` (slate-800)
- **Surface**: `#1E293B` (slate-800)
- **Text Primary**: `#D1D5DB` (gray-300)
- **Text Secondary**: `#E5E7EB` (gray-200)
- **Text Muted**: `#9CA3AF` (gray-400)
- **Accent Heading**: `#A78BFA` (purple-400)
- **Accent Primary**: `#7C3AED` (purple-600)
- **Accent Hover**: `#6D28D9` (purple-700)
- **Border**: `#475569` (slate-600)
- **Tag Background**: `#334155` (slate-700)
