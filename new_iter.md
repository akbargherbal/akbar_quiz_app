# LLM-Led Development Plan for Django Quiz App

## Iteration 1: Move Quiz Data to Django Context

**User Inputs:**

1. Existing front-end code (HTML, CSS, JS files)
2. Description of development environment (Python version, preferred package manager)
3. Any preferences for project/app naming

**LLM Deliverables:**

1. Terminal commands to:
   - Create Django project and app
   - Install required dependencies
   - Set up initial structure
2. Complete Django files:
   - `settings.py` with necessary configurations
   - `urls.py` for both project and app
   - `views.py` with the quiz view function
   - Any template modifications needed for the index.html
3. Instructions for:
   - Where to place the existing files
   - Any modifications needed to the existing files
   - How to run the Django server

**Expected Results:**

- Working Django app serving the existing quiz with data coming from Django
- No database requirements yet (using static data in views)
- Identical user experience to the current version

**Verification:**

- Playwright test script that checks:
  - Quiz loads with correct questions
  - Quiz functions as expected
  - Test commands to run the verification

## Iteration 2: Models Aligned with Quiz Bank Format

**User Inputs:**

1. The completed code from Iteration 1
2. Sample of the quiz bank format (as previously shared)
3. Any admin customization preferences

**LLM Deliverables:**

1. Complete model definitions aligned with the quiz bank format:
   - `models.py` with models for:
     - Question (with fields: topic, question_text, chapter_no)
     - Option (with fields: text, is_correct)
     - Quiz (to group questions)
   - Migration commands
2. Django admin configuration:
   - `admin.py` with registered models and customizations
   - Admin interfaces optimized for the data structure
3. Updated view code:
   - Modified `views.py` to pull from database instead of static data
   - Data structure conversion to match what Alpine.js expects
4. Manual data entry script/instructions:
   - For adding a few sample quizzes without requiring full import yet
5. Instructions for:
   - Running migrations
   - Creating a superuser
   - Accessing the admin
   - Adding quiz content

**Expected Results:**

- Database structure that mirrors the quiz bank format
- Admin interface for managing quizzes, questions, and options
- Frontend pulling quiz data from the database

**Verification:**

- Playwright test script checking:
  - Admin login works
  - Quiz creation via admin works
  - Frontend correctly displays database-stored quiz
  - Test commands for running verification

<!-- Iteration 1 and 2 have been completed -->

**Iteration 3: Backend - Persisting Quiz Results**

- **Overall Objective:** Implement the backend mechanism to store the results of a completed quiz attempt. Verification is primarily through the Django Admin and direct API testing. _No frontend UI changes required in this iteration._
- **Template Phase Alignment:** Phase 4.2 (Models), Phase 4.3 (Dynamic Views).

**Step 3.1: Define Result Models**

- **Input:** Code from Iteration 2.
- **Objective:** Create Django models to store quiz attempts and individual answers.
- **Key Tasks/LLM Responsibilities:**
  1.  Define `QuizAttempt` model (`multi_choice_quiz/models.py`) with fields like `quiz` (FK to Quiz), `score` (Int), `start_time` (DateTime), `end_time` (DateTime), `total_time_seconds` (Int, calculated). Add `user` (FK to `auth.User`, nullable=True, blank=True for now).
  2.  Define `UserAnswer` model (`multi_choice_quiz/models.py`) with fields like `attempt` (FK to QuizAttempt), `question` (FK to Question), `selected_option` (FK to Option, nullable=True - if user skipped?), `is_correct` (Boolean).
  3.  Generate migration files.
  4.  Write basic model unit tests (`tests/test_models.py`) confirming model creation and relationships.
- **Deliverables:** Updated `models.py`, new migration file(s), updated `tests/test_models.py`.
- **Verification Checklist:**
  - `[ ]` **Django Checks Pass:** `python manage.py check` runs without errors.
  - `[ ]` **Migrations Generated:** `python manage.py makemigrations multi_choice_quiz` generates new migration(s).
  - `[ ]` **Migrations Apply:** `python manage.py migrate` runs successfully.
  - `[ ]` **Model Unit Tests Pass:** `python manage.py test multi_choice_quiz.tests.test_models` passes for new model tests.

**Step 3.2: Expose Result Models in Admin**

- **Input:** Code from Step 3.1.
- **Objective:** Make the new `QuizAttempt` and `UserAnswer` models viewable and manageable via the Django Admin.
- **Key Tasks/LLM Responsibilities:**
  1.  Register `QuizAttempt` and `UserAnswer` in `multi_choice_quiz/admin.py`.
  2.  Configure basic `list_display` for both models in the admin (e.g., Attempt: quiz title, score, user, timestamp; Answer: attempt ID, question text, correctness).
- **Deliverables:** Updated `admin.py`.
- **Verification Checklist:**
  - `[ ]` **Admin Interface Loads:** Django server runs (`runserver`), `/admin/` page loads.
  - `[ ]` **Models Registered:** `QuizAttempts` and `UserAnswers` sections appear in the admin for the `multi_choice_quiz` app.
  - `[ ]` **Admin Views Work:** Can click into `QuizAttempts` and `UserAnswers` lists without errors (even if empty).

**Step 3.3: Create API Endpoint (View/URL)**

- **Input:** Code from Step 3.2.
- **Objective:** Create a Django view and URL that accepts POST requests containing quiz results data (expecting JSON). _This view will ONLY handle data intake and saving, returning a simple JSON confirmation._
- **Key Tasks/LLM Responsibilities:**
  1.  Create a new view function `submit_results` in `multi_choice_quiz/views.py`.
  2.  This view should:
      - Only accept POST requests.
      - Expect JSON data in the request body (e.g., `{'quizId': 1, 'score': 2, 'time': 120, 'answers': [{'questionId': 10, 'selectedOptionIndex': 1}, ...]}`).
      - Parse the JSON.
      - **Crucially:** Convert `selectedOptionIndex` (0-based from potential future JS) to `selected_option_id` (database PK, requires fetching Option based on Question and _position_).
      - Create a `QuizAttempt` record using the received data (calculate `total_time_seconds`).
      - Iterate through the `answers` array, creating `UserAnswer` records, linking them to the `QuizAttempt` and correctly determining `is_correct` and `selected_option`.
      - Return a `JsonResponse` indicating success (e.g., `{'status': 'success', 'attempt_id': attempt.id}`). Handle potential errors (bad JSON, missing data) gracefully with appropriate error JsonResponses.
  3.  Add a URL pattern in `multi_choice_quiz/urls.py` (e.g., `path('submit/', views.submit_results, name='submit_results')`).
  4.  Write Django Test Client tests (`tests/test_views.py`) that POST valid and invalid JSON data to this new URL and assert:
      - Correct HTTP status codes (200 for success, 400/405 for errors).
      - Expected JSON response content.
      - Correct `QuizAttempt` and `UserAnswer` records created/not created in the database.
- **Deliverables:** Updated `views.py`, updated `urls.py`, updated `tests/test_views.py`.
- **Verification Checklist:**
  - `[ ]` **Python Linting:** `ruff` passes for `views.py`, `urls.py`.
  - `[ ]` **View Unit/Integration Tests Pass:** `python manage.py test multi_choice_quiz.tests.test_views` passes for the new endpoint tests.
  - `[ ]` **Manual Test (Optional but Recommended):** Use `curl` or Postman to send sample JSON to the `/quiz/submit/` endpoint and verify database records via Admin.

**Step 3.4: Frontend JS Submission (Minimal)**

- **Input:** Code from Step 3.3, existing `multi_choice_quiz/static/multi_choice_quiz/app.js`.
- **Objective:** Modify the Alpine.js component to send the results to the backend endpoint _after_ the quiz is completed. _Do NOT change the existing results display logic yet._
- **Key Tasks/LLM Responsibilities:**
  1.  In `app.js`, locate the logic where `this.quizCompleted = true` is set (likely within `nextQuestion` or a similar method).
  2.  Immediately after setting `quizCompleted` to true:
      - Gather the necessary data: `quizId` (needs to be available, perhaps from the initial data load or URL), `score`, `quizTime`, and the `userAnswers` array (which stores the _index_ selected by the user).
      - **Important:** Ensure the `userAnswers` array is transformed into the format expected by the backend view (e.g., `[{'questionId': id, 'selectedOptionIndex': index}, ...]`). This requires access to the `question.id` for each answer.
      - Use the `fetch` API to send this data as a JSON POST request to the `/quiz/submit/` URL. Include the CSRF token header.
      - Add basic handling for the response (e.g., `console.log('Submission response:', response.json())`) or errors (`console.error('Submission failed:', error)`).
- **Deliverables:** Updated `multi_choice_quiz/static/multi_choice_quiz/app.js`.
- **Verification Checklist:**
  - `[ ]` **JS Linting:** `eslint` (if configured) passes for `app.js`.
  - `[ ]` **Playwright E2E Test - Submission:**
    - Create a new test (`tests/test_submission_e2e.py` or similar).
    - Test loads a quiz, answers all questions.
    - **Crucially:** Use `page.route` or `page.expect_request` to intercept/verify the POST request to `/quiz/submit/`. Assert the request method is POST, the URL is correct, and the payload contains expected keys (`quizId`, `score`, `answers`, etc.).
    - Check browser console for the success/error log message from the `fetch` call.
    - **(Optional but Recommended):** Query the database (using Django ORM within the test setup/teardown or via `call_command`) to verify `QuizAttempt` count increases after quiz completion in the test.

---

**Iteration 4: Basic Site Structure & Navigation (`pages` app)**

- **Overall Objective:** Establish the main site layout using the `pages` app and Tailwind CSS. Integrate the existing quiz application into this structure.
- **Template Phase Alignment:** Phase 2 (Static UI), Phase 4.1 (Template Integration).

**Step 4.1: Implement Base Layout (`pages` app)**

- **Input:** Code from Iteration 3, existing `pages` app structure and templates.
- **Objective:** Create a consistent site-wide base template with header, footer, and navigation using Tailwind CSS.
- **Key Tasks/LLM Responsibilities:**
  1.  Refine/Implement `pages/templates/pages/base.html`:
      - Include Tailwind CSS (CDN or build process).
      - Define the purple color theme as specified previously.
      - Create header (with site title/logo, links to Home, Quizzes, About, Login, Signup).
      - Define a `{% block content %}`.
      - Create a footer.
      - Ensure basic responsiveness.
  2.  Create simple views in `pages/views.py` for `home`, `about`, `login_view`, `signup_view`, `profile_view` that just render basic corresponding templates extending `pages/base.html`.
  3.  Create corresponding templates (`home.html`, `about.html`, `login.html`, `signup.html`, `profile.html`) in `pages/templates/pages/`. These should initially contain minimal placeholder content but extend the base.
  4.  Ensure `pages/urls.py` is set up correctly and included in the project's `core/urls.py` at the root (`""`).
- **Deliverables:** Updated `pages` app templates, views, and URLs.
- **Verification Checklist:**
  - `[ ]` **Template Linting:** `djlint` passes for all `pages` templates.
  - `[ ]` **Python Linting:** `ruff` passes for `pages/views.py`, `pages/urls.py`.
  - `[ ]` **Django Test Client - Page Rendering:** Tests confirm that `/`, `/about/`, `/login/`, `/signup/`, `/profile/` return 200 OK and use `pages/base.html`.
  - `[ ]` **Playwright - Static Page Checks:**
    - Test loads Home, About, Login, Signup, Profile pages.
    - Assert header and footer are present and consistent on all pages.
    - Assert basic responsiveness using viewport changes and visual checks/snapshots.
    - Run `axe-core` checks on these static pages.

**Step 4.2: Integrate Quiz App into Base Layout**

- **Input:** Code from Step 4.1, `multi_choice_quiz` app.
- **Objective:** Make the quiz interface (`multi_choice_quiz/index.html`) render within the main site layout provided by `pages/base.html`.
- **Key Tasks/LLM Responsibilities:**
  1.  Modify `multi_choice_quiz/templates/multi_choice_quiz/index.html` to `{% extends 'pages/base.html' %}`.
  2.  Wrap the existing quiz container div within `{% block content %}`.
  3.  Ensure the quiz's specific CSS (`multi_choice_quiz/static/multi_choice_quiz/style.css`) is still loaded (potentially via an `{% block extra_css %}` in `pages/base.html` that `multi_choice_quiz/index.html` populates).
  4.  Adjust quiz CSS if necessary to avoid major conflicts with Tailwind (minor layout tweaks might be needed).
- **Deliverables:** Updated `multi_choice_quiz/index.html`, potentially minor updates to `style.css` and `pages/base.html`.
- **Verification Checklist:**
  - `[ ]` **Playwright - Quiz Integration Check:**
    - Test loads a quiz page (e.g., `/quiz/1/`).
    - Assert the main site header and footer (from `pages/base.html`) are visible.
    - Assert the quiz container (`.quiz-container`) and its elements (question, options) are visible and functional _within_ the main layout.
    - Re-run the basic quiz interaction test (answer one question) to ensure functionality isn't broken by the layout change.

**Step 4.3: Implement Quiz Browsing Page (`pages` app)**

- **Input:** Code from Step 4.2.
- **Objective:** Create the `/quizzes/` page that lists available quizzes fetched from the database.
- **Key Tasks/LLM Responsibilities:**
  1.  Update the `quizzes` view in `pages/views.py` to:
      - Fetch all active `Quiz` objects from the database.
      - Fetch all `Topic` objects for potential filtering (defer filter logic implementation).
      - Pass the `quizzes` and `topics` to the template context.
  2.  Implement `pages/templates/pages/quizzes.html`:
      - Extend `pages/base.html`.
      - Display a title like "Browse Quizzes".
      - Include a section for topic filter buttons (linking to `?topic=<id>`, but filtering logic is not yet implemented in the view).
      - Loop through the `quizzes` context variable.
      - For each quiz, display its `title`, `description`, number of questions (`quiz.question_count`), associated `topics`, and a "Start Quiz" button linking to its `quiz_detail` URL (`{% url 'multi_choice_quiz:quiz_detail' quiz.id %}`).
      - Use Tailwind CSS for styling the quiz cards in a grid.
- **Deliverables:** Updated `pages/views.py`, new/updated `pages/templates/pages/quizzes.html`.
- **Verification Checklist:**
  - `[ ]` **Template Linting:** `djlint` passes for `quizzes.html`.
  - `[ ]` **Python Linting:** `ruff` passes for `pages/views.py`.
  - `[ ]` **Django Test Client - Quiz List:** Test fetches `/quizzes/`, asserts 200 OK, asserts quiz titles/topics from sample DB data are present in the response context/HTML.
  - `[ ]` **Playwright - Quiz List Page:** Test loads `/quizzes/`, asserts page title is visible, asserts quiz cards are displayed, clicks a "Start Quiz" button and verifies it navigates to the correct quiz detail URL.

---

**Iteration 5: Polishing and Frontend Refinements**

- **Overall Objective:** Improve the user experience by refining the results display and implementing filtering on the browse page.
- **Template Phase Alignment:** Phase 4.1 (Templates), Phase 3.1 (Alpine.js), potentially Phase 5 (HTMX for filtering).

**Step 5.1: Enhance Quiz Results Display**

- **Input:** Code from Iteration 4.
- **Objective:** Refine the visual presentation of the quiz results panel using the Tailwind CSS framework and ensure data shown is confirmed by the backend submission.
- **Key Tasks/LLM Responsibilities:**
  1.  Update the results panel section within `multi_choice_quiz/templates/multi_choice_quiz/index.html`. Use Tailwind classes for layout, stats display, mistake review list, and buttons, matching the design in `pages/templates/pages/profile.html` or similar refined style.
  2.  Modify `app.js`: In the `fetch` success handler for submission, update Alpine.js variables bound to the results panel elements (score, time, mistakes list) using the data from the server's JSON response. The client-side calculation should now primarily be a fallback or hidden.
- **Deliverables:** Updated `multi_choice_quiz/index.html`, updated `app.js`.
- **Verification Checklist:**
  - `[ ]` **Playwright - Results Panel:** Test completes a quiz, verifies the results panel uses Tailwind styles, displays score/time matching server response, and shows the "Mistakes Review" section correctly.
  - `[ ]` **Visual Regression:** Run visual regression test specifically on the results panel state.

**Step 5.2: Implement Quiz Filtering by Topic**

- **Input:** Code from Step 5.1.
- **Objective:** Make the topic buttons on the `/quizzes/` page functional, filtering the displayed quizzes.
- **Key Tasks/LLM Responsibilities:**
  1.  Modify the `quizzes` view in `pages/views.py`:
      - Read the `topic` GET parameter.
      - If a valid topic ID is provided, filter the `Quiz.objects.filter(is_active=True)` query by `topics__id=topic_id`.
      - Pass the `selected_topic` object (or None) to the context.
  2.  Update `pages/templates/pages/quizzes.html`:
      - Use the `selected_topic` context variable to highlight the active filter button.
      - Add a "Clear filter" link if a topic is selected.
      - Display a message like "Showing quizzes for topic: ..." if filtered.
  3.  **(Optional - Defer HTMX):** Implement this using standard page reloads first. HTMX could be added later in Iteration 6 to make filtering dynamic without reload.
- **Deliverables:** Updated `pages/views.py`, updated `pages/templates/pages/quizzes.html`.
- **Verification Checklist:**
  - `[ ]` **Django Test Client - Filtering:** Test fetches `/quizzes/?topic=<id>`, asserts only quizzes with that topic are in the response context. Test `/quizzes/` returns all quizzes.
  - `[ ]` **Playwright - Filtering Interaction:** Test loads `/quizzes/`, clicks a topic filter button, verifies the URL changes, verifies only quizzes with the corresponding topic are displayed, clicks "Clear filter", verifies all quizzes reappear.

---

**Iteration 6: Authentication & User-Specific History (Placeholder)**

- **Overall Objective:** Introduce user accounts and link quiz attempts to users. _Focus on backend logic and basic display, full UI integration later._
- **Template Phase Alignment:** Phase 4.2/4.3 (Models/Views), Phase 6 (Django Forms).

**Step 6.1: Basic Django Authentication Setup**

- **Input:** Code from Iteration 5.
- **Objective:** Set up Django's built-in authentication system. _Do not implement custom templates yet._
- **Key Tasks/LLM Responsibilities:**
  1.  Ensure `django.contrib.auth` and `django.contrib.sessions` are in `INSTALLED_APPS` and `MIDDLEWARE`.
  2.  Include Django's auth URLs (`django.contrib.auth.urls`) in the project's `core/urls.py`.
  3.  Run `migrate` to create necessary auth tables.
  4.  Create a superuser account (`createsuperuser`).
- **Deliverables:** Potentially updated `settings.py`, `core/urls.py`.
- **Verification Checklist:**
  - `[ ]` **Migrations Applied:** Auth tables exist in DB.
  - `[ ]` **Superuser Created:** Can log in via `/admin/` with superuser credentials.
  - `[ ]` **Default Auth URLs Work:** Can navigate to `/accounts/login/`, `/accounts/logout/` (using Django's default templates) without errors.

**Step 6.2: Link Quiz Attempts to Users**

- **Input:** Code from Step 6.1.
- **Objective:** Modify the quiz submission logic to associate attempts with the logged-in user (if any).
- **Key Tasks/LLM Responsibilities:**
  1.  Modify the `submit_results` view (`multi_choice_quiz/views.py`):
      - Check if `request.user.is_authenticated`.
      - If authenticated, assign `request.user` to the `user` field when creating the `QuizAttempt`.
  2.  Update the Django Test Client tests for `submit_results`:
      - Include tests simulating authenticated requests (using `client.force_login()`).
      - Assert the `user` field is correctly set on the created `QuizAttempt`.
- **Deliverables:** Updated `multi_choice_quiz/views.py`, updated `tests/test_views.py`.
- **Verification Checklist:**
  - `[ ]` **View Unit/Integration Tests Pass:** All tests for `submit_results`, including authenticated scenarios, pass.
  - `[ ]` **Manual Admin Check:** Log in as superuser, take a quiz, submit results, check the `QuizAttempt` in the admin – verify the `user` field is set to the superuser.

**Step 6.3: Basic Profile Page History (Read-Only)**

- **Input:** Code from Step 6.2.
- **Objective:** Display a simple list of the logged-in user's past quiz attempts on the placeholder profile page.
- **Key Tasks/LLM Responsibilities:**
  1.  Modify the `profile_view` in `pages/views.py`:
      - Require login (`@login_required` decorator).
      - Fetch `QuizAttempt` objects filtered by `user=request.user`, ordered by date.
      - Pass these attempts to the `pages/profile.html` context.
  2.  Update `pages/templates/pages/profile.html`:
      - Replace the static history list with a loop through the `quiz_attempts` context variable.
      - Display basic info for each attempt (quiz title, score, date).
- **Deliverables:** Updated `pages/views.py`, updated `pages/templates/pages/profile.html`.
- **Verification Checklist:**
  - `[ ]` **Django Test Client - Profile View:** Test authenticates a user, creates some `QuizAttempt` records for them, fetches `/profile/`, asserts 200 OK, asserts the attempt data is in the context/HTML. Test unauthenticated access redirects to login.
  - `[ ]` **Playwright - Profile History:** Test logs in (manual step or via admin cookie injection if simpler than building login UI test), navigates to `/profile/`, verifies the attempts created during manual testing (or test setup) are listed.

---

**Iteration 7: Deployment Preparation**

- **Overall Objective:** Prepare the application for deployment to a chosen platform (GCP App Engine or Cloud Run).
- **Template Phase Alignment:** Primarily configuration and environment setup.

**Step 7.1: Production Settings & Dependencies**

- **Input:** Full project code.
- **Objective:** Configure Django settings for production, finalize dependencies.
- **Key Tasks/LLM Responsibilities:**
  1.  Create/Refine production settings logic (e.g., using environment variables for `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`).
  2.  Configure database settings for production (e.g., Cloud SQL connection string via env var).
  3.  Configure static file handling for production (`whitenoise` or cloud storage).
  4.  Generate final `requirements.txt` (`pip freeze > requirements.txt`).
- **Deliverables:** Production-ready settings configuration, `requirements.txt`.
- **Verification Checklist:**
  - `[ ]` **Django Checks Pass (Prod Settings):** `python manage.py check --settings=core.settings.production` (assuming separate prod settings file) passes.
  - `[ ]` **Collect Static Works:** `python manage.py collectstatic --noinput` runs successfully.

**Step 7.2: Containerization (Dockerfile)**

- **Input:** Codebase, `requirements.txt`.
- **Objective:** Create a Dockerfile to containerize the application.
- **Key Tasks/LLM Responsibilities:**
  1.  Write a `Dockerfile`:
      - Use an appropriate Python base image.
      - Set up working directory, copy requirements, install dependencies.
      - Copy application code.
      - Run `collectstatic`.
      - Expose port (e.g., 8080).
      - Set entrypoint/command (e.g., using `gunicorn`).
- **Deliverables:** `Dockerfile`, potentially `.dockerignore`.
- **Verification Checklist:**
  - `[ ]` **Docker Build Succeeds:** `docker build . -t quizapp-test` completes successfully locally.
  - `[ ]` **Container Runs Locally:** `docker run -p 8080:8080 quizapp-test` starts, and the app is accessible locally via `http://localhost:8080`.

**Step 7.3: Platform Configuration (GCP)**

- **Input:** `Dockerfile`, Production Settings info.
- **Objective:** Create configuration files for the target GCP platform.
- **Key Tasks/LLM Responsibilities:**
  1.  **(If App Engine):** Create `app.yaml` specifying runtime, entrypoint, environment variables (secrets handled separately).
  2.  **(If Cloud Run):** Prepare `gcloud run deploy` command parameters or a service definition YAML, including environment variables.
  3.  Document steps for setting secrets (e.g., using Secret Manager).
- **Deliverables:** `app.yaml` or Cloud Run deployment script/config, documentation for secrets.
- **Verification Checklist:**
  - `[ ]` **Config Linting/Validation:** Use `gcloud` CLI to validate `app.yaml` or Cloud Run config if possible.
  - `[ ]` **Manual Review:** Human review of configuration files for correctness.

---

**Iteration 8: Deployment to GCP & Smoke Testing**

- **Overall Objective:** Deploy the containerized application to the chosen GCP platform and perform basic checks.
- **Template Phase Alignment:** Deployment.

**Step 8.1: Deploy Application**

- **Input:** Container image (e.g., pushed to Google Artifact Registry), platform configuration (`app.yaml` or Cloud Run settings).
- **Objective:** Deploy the application to the cloud environment.
- **Key Tasks/LLM Responsibilities:** Generate `gcloud` commands for deployment (`gcloud app deploy` or `gcloud run deploy`).
- **Deliverables:** Deployment commands/script.
- **Verification Checklist:**
  - `[ ]` **Deployment Command Succeeds:** `gcloud ... deploy` command completes without critical errors.
  - `[ ]` **Service Available:** GCP console shows the service/version as running/serving.

**Step 8.2: Post-Deployment Smoke Tests**

- **Input:** Deployed application URL.
- **Objective:** Run basic automated checks against the live deployment to ensure core functionality is working.
- **Key Tasks/LLM Responsibilities:**
  1.  Execute a small subset of critical Playwright E2E tests against the deployed URL:
      - Load home page.
      - Load quiz browse page.
      - Load and start a specific quiz (answer maybe 1 question).
      - (If auth deployed) Load login page.
- **Deliverables:** Playwright smoke test script/suite.
- **Verification Checklist:**
  - `[ ]` **Homepage Loads:** Playwright test confirms home page returns 200 OK and renders basic title/header.
  - `[ ]` **Quiz Page Loads:** Playwright test confirms a quiz page loads and shows question text.
  - `[ ]` **Smoke Test Suite Passes:** All tests in the designated smoke test suite pass against the deployed URL.
