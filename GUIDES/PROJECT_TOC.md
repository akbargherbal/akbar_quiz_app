**QuizMaster Project: Table of Contents**

**Module 1: Project Setup & Configuration**
1.1. Introduction: Django Project Structure (`core/`, `manage.py`)
1.2. Core Settings (`core/settings.py`):
_ Installed Apps (`INSTALLED_APPS`) - Identifying Your Apps and Django Apps
_ Middleware (`MIDDLEWARE`) - Understanding Request/Response Processing Flow (briefly)
_ Database Configuration (`DATABASES`) - SQLite (Local) vs. PostgreSQL (Production)
_ Template Engine Configuration (`TEMPLATES`)
_ Static File Handling (`STATIC_URL`, `STATIC_ROOT`, `STATICFILES_DIRS`, `Whitenoise`)
_ Root URL Configuration (`ROOT_URLCONF`)
1.3. Environment Management (`django-environ`, `.env`)
1.4. Local Development Overrides (`core/settings_local.py`, Debug Toolbar)
1.5. Main URL Routing (`core/urls.py`):
_ Including App URLs (`include()`)
_ Admin Site URL (`admin.site.urls`) \* Authentication URLs (`django.contrib.auth.urls`)

**Module 2: Data Modeling - The Quiz Structure**
2.1. Introduction to Django Models & ORM
2.2. Defining Topics (`multi_choice_quiz.models.Topic`)
2.3. Defining Quizzes (`multi_choice_quiz.models.Quiz`):
_ Fields (title, description, etc.)
_ Many-to-Many Relationship with `Topic`
_ Model Methods (`question_count`, `get_topics_display`)
2.4. Defining Questions (`multi_choice_quiz.models.Question`):
_ Fields (text, position, tag, etc.)
_ Foreign Key Relationship with `Quiz` and `Topic`
_ Model Methods (`correct_option`, `correct_option_index`, `options_list`)
_ The `to_dict()` Method: Bridging Backend and Frontend
2.5. Defining Options (`multi_choice_quiz.models.Option`):
_ Fields (text, position, is_correct)
_ Foreign Key Relationship with `Question`
2.6. Tracking User Progress (`multi_choice_quiz.models.QuizAttempt`):
_ Fields (score, total_questions, percentage, start/end times) \* Foreign Key Relationship with `Quiz` and `User` (Handling Anonymous Users)
2.7. Database Migrations (Concept and `manage.py makemigrations/migrate`)

**Module 3: Handling Requests & Rendering Pages**
3.1. Introduction to Django Views (Function-Based Views) and the Request-Response Cycle
3.2. The `pages` App: Structure and Purpose
_ `pages/views.py`: Home, Quizzes, About
_ `pages/urls.py`: Defining App-Specific URLs
_ `pages/templates/pages/`: Template Structure
_ Base Template (`base.html`): Structure, Tailwind Config, Alpine.js Inclusion, PWA Tags, Header/Footer
_ Child Templates (`home.html`, `quizzes.html`, `about.html`): Extending Base, Using Context Data (`{{ }}`), Template Tags (`{% %}`)
3.3. The `multi_choice_quiz` App: Views & Templates
_ `multi_choice_quiz/views.py`:
_ `quiz_detail`: Fetching specific quiz, using `models_to_frontend`, passing JSON data via context, `mark_safe`.
_ `multi_choice_quiz/templates/multi_choice_quiz/`: \* `index.html`: The Quiz Interface Template

**Module 4: Frontend Interactivity - Alpine.js & Static Files**
4.1. Role of Static Files (CSS, JS)
4.2. Integrating Alpine.js (`x-data`, `x-init`, `x-cloak`)
4.3. The `quizApp` Component (`multi_choice_quiz/static/multi_choice_quiz/app.js`):
_ Reading Initial Data (`#quiz-data`, `data-quiz-id`)
_ State Management (Variables: `questions`, `currentQuestionIndex`, `score`, etc.)
_ Computed Properties (Getters: `currentQuestion`, `starRatingDisplay`)
_ Core Methods (`init`, `selectOption`, `nextQuestion`, `restartQuiz`)
_ Handling User Answers and Feedback
_ Calculating Results (`calculatePercentage`, `calculateQuizTime`)
_ Dynamic Styling (`getOptionClass`, `style.css` feedback classes)
_ Timers (`setTimeout`) for Feedback Duration
4.4. Styling the Quiz (`multi_choice_quiz/static/multi_choice_quiz/style.css`): \* Basic Styles, Responsive Design (`@media`), Code Block Styling (`code`, `pre`), Animations.
4.5. Device Detection Script (`pages/base.html`)

**Module 5: User Authentication & Management**
5.1. Django's Built-in Authentication System Overview
5.2. Integrating Auth URLs (`core/urls.py`)
5.3. Customizing Auth Templates (`templates/registration/`):
_ Login (`login.html`)
_ Logout (`logged_out.html`)
_ Password Change (`password_change_form.html`, `password_change_done.html`)
_ Password Reset Flow (form, done, email, confirm, complete templates)
5.4. User Signup (`pages/forms.SignUpForm`, `pages/views.signup_view`):
_ Extending `UserCreationForm`
_ Handling GET vs. POST Requests
_ Form Validation (`is_valid()`)
_ Saving the User (`form.save()`)
_ Automatic Login (`login()`)
_ Displaying Form Errors in Templates
5.5. User Profile (`pages/views.profile_view`, `pages/templates/pages/profile.html`):
_ Requiring Login (`@login_required`)
_ Accessing the Logged-in User (`request.user`) \* Displaying User Information and Quiz History (`QuizAttempt`)

**Module 6: Interacting with the Frontend - API Endpoint**
6.1. Concept: Backend API for Frontend Data Submission
6.2. The `submit_quiz_attempt` View (`multi_choice_quiz/views.py`):
_ Expecting POST Requests (`@require_POST`)
_ Parsing JSON Data (`json.loads`)
_ Data Validation
_ Creating `QuizAttempt` Records
_ Returning `JsonResponse`
6.3. Connecting Frontend and Backend (`app.js:submitResults`):
_ Using the `fetch` API
_ Sending POST Request with JSON Payload
_ Handling Success and Errors
6.4. CSRF Considerations (`@csrf_exempt` and its implications)

**Module 7: Data Import & Utilities**
7.1. Management Commands (`multi_choice_quiz/management/commands/`):
_ Adding Sample Data (`add_sample_quizzes.py`, `add_code_test_questions.py`)
_ Importing from Files (`import_quiz_bank.py`, `import_chapter_quizzes.py`)
_ Using Pandas (`pd.read\__`)
            *   Data Processing Logic (Sampling, Splitting)
    7.2. Transformation Logic (`multi_choice_quiz/transform.py`):
        *   `quiz_bank_to_models`(Handling 1-based index input)
        *  `models_to_frontend` (Creating JSON structure, 0-based index output)
    7.3. Utility Functions (`multi_choice_quiz/utils.py`):
        *   `import_from_dataframe`         *   `curate_data`

**Module 8: Testing Your Application**
8.1. Introduction to Testing in Django/Python
8.2. Pytest Basics (`pytest.ini`)
8.3. Pytest Fixtures (`conftest.py`):
_ Understanding Fixture Scope (`session`, `function`)
_ The `django_server` Fixture: Purpose, How it Starts/Stops `runserver`, `yield`
_ The `capture_console_errors` Fixture: Purpose, Playwright Interaction (`page.on`), Failing Tests
8.4. End-to-End Testing with Playwright:
_ Simulating User Interactions (`page.goto`, `page.click`, `expect`)
_ Using the `django_server` and `capture_console_errors` Fixtures in Tests
8.5. Test Runners (`run\__.py`Scripts):
        *   Purpose: Automating Test Suite Execution
        *   Ensuring Server and Data Prerequisites
    8.6. Interpreting Test Results (Passing vs. Failing, Error Output)
    8.7.`pytest-django`Integration (Mention`django_db`marker if used in backend tests, even if not explicitly shown in`conftest.py` example)

**Module 9: Progressive Web App (PWA) Features**
9.1. Overview of `django-pwa`
9.2. Configuration in `settings.py` (`PWA_APP_*` settings)
9.3. Manifest File (`pwa/urls.py`, `/manifest.json`)
9.4. Service Worker (`static/js/serviceworker.js`, PWA template tags)
9.5. PWA Meta Tags in Base Templates (`{% progressive_web_app_meta %}`)
