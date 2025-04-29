# Iterative Development Process: Modular Authentication App

**Core Philosophy:**

This guide outlines the step-by-step process for implementing user authentication within the Django Quiz App project. We will prioritize:

1.  **Modularity:** The authentication features (using `django.contrib.auth`) should enhance the application _without_ creating hard dependencies. The core quiz functionality must remain fully operational for anonymous users even if authentication features are later disabled or removed.
2.  **Reusability:** While tailored to this project, the underlying approach using standard Django components and optional linking should be conceptually reusable.
3.  **Iteration:** Development will proceed in small, distinct phases and steps.
4.  **Verification:** Each step will conclude with specific, automated verification checks (unit tests, integration tests, E2E tests). **No progression to the next step occurs unless all verification checks for the current step pass.** We will also perform regression testing to ensure previous functionality remains intact.

**LLM Interaction Model:**

The LLM will be provided with the current state of the codebase before each step. It will be tasked with implementing _only_ the specific changes required for that step. The user will then run the verification checks. If checks pass, the LLM proceeds to the next step. If checks fail, the LLM will be asked to revise the implementation for the current step based on the failure feedback.

---

## Authentication Implementation Phases

_(Based on the structure of Iteration 6 from the original plan)_

### Phase 1: Enable Core Django Auth Backend

- **Overall Objective:** Activate Django's built-in authentication system (`django.contrib.auth`) and its dependencies, ensuring no impact on existing anonymous functionality.
- **Verification Focus:** System stability, application of auth migrations, non-regression of existing tests.

**Step 1.1: Configure Auth Apps & Middleware**

- **Input:** Codebase state before Iteration 6.
- **Objective:** Add the necessary authentication apps and middleware to the Django settings.
- **Key Tasks (LLM):**
  1.  Modify `core/settings.py`: Add `django.contrib.auth` and `django.contrib.sessions` to `INSTALLED_APPS`.
  2.  Modify `core/settings.py`: Add `django.contrib.sessions.middleware.SessionMiddleware` and `django.contrib.auth.middleware.AuthenticationMiddleware` to `MIDDLEWARE` in the appropriate order.
- **Deliverables:** Updated `core/settings.py`.
- **Verification Checklist:**
  - `[ ]` **Django Checks Pass:** `python manage.py check` runs without errors.
  - `[ ]` **Server Starts:** `python manage.py runserver` starts without crashing.

**Step 1.2: Include Default Auth URLs**

- **Input:** Code from Step 1.1.
- **Objective:** Make Django's default authentication views (login, logout, etc.) accessible via URLs.
- **Key Tasks (LLM):**
  1.  Modify `core/urls.py`: Include `django.contrib.auth.urls` under a suitable path (e.g., `accounts/`).
- **Deliverables:** Updated `core/urls.py`.
- **Verification Checklist:**
  - `[ ]` **Default Login Page Loads:** Accessing `/accounts/login/` in a browser displays Django's default (unstyled) login form. (Requires `runserver`).

**Step 1.3: Apply Auth Migrations**

- **Input:** Code from Step 1.2.
- **Objective:** Create the necessary database tables for the authentication system.
- **Key Tasks (LLM):** None (User runs the command).
- **Deliverables:** Database schema updated.
- **Verification Checklist:**
  - `[ ]` **Migrations Apply:** `python manage.py migrate` runs successfully, applying migrations for `auth`, `contenttypes`, `sessions`.

**Step 1.4: Full Regression Test**

- **Input:** Code from Step 1.3.
- **Objective:** Confirm that enabling the auth backend has not negatively impacted any existing functionality.
- **Key Tasks (LLM):** None (User runs the tests).
- **Deliverables:** Test results.
- **Verification Checklist:**
  - `[ ]` **Existing Tests Pass:** The complete existing test suite (unit, integration, E2E for `multi_choice_quiz` and `pages`) passes without any modifications.

---

### Phase 2: Optional Linking of Quiz Attempts to Users

- **Overall Objective:** Modify the quiz result submission process to associate attempts with logged-in users _if available_, while maintaining full functionality for anonymous users.
- **Verification Focus:** Correct database schema changes, conditional logic in views, distinct handling of anonymous vs. authenticated submissions confirmed via tests.

**Step 2.1: Modify Models & Generate Migrations**

- **Input:** Code from Phase 1.
- **Objective:** Add an optional `user` foreign key to the `QuizAttempt` model.
- **Key Tasks (LLM):**
  1.  Modify `multi_choice_quiz/models.py`: Add `user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='quiz_attempts')` to `QuizAttempt`.
- **Deliverables:** Updated `multi_choice_quiz/models.py`.
- **Verification Checklist:**
  - `[ ]` **Makemigrations Runs:** `python manage.py makemigrations multi_choice_quiz` creates a new migration file.
  - `[ ]` **Migration Applies:** `python manage.py migrate` runs successfully.

**Step 2.2: Update Submission View Logic**

- **Input:** Code from Step 2.1.
- **Objective:** Modify the `submit_results` view to check for an authenticated user and assign them to the `QuizAttempt` if present.
- **Key Tasks (LLM):**
  1.  Modify `multi_choice_quiz/views.py`: In `submit_results`, add logic `attempt_user = request.user if request.user.is_authenticated else None` and use `attempt_user` when creating `QuizAttempt`.
- **Deliverables:** Updated `multi_choice_quiz/views.py`.
- **Verification Checklist:**
  - `[ ]` **Python Linting:** Code passes linter checks (`ruff`).

**Step 2.3: Write/Update Submission Tests**

- **Input:** Code from Step 2.2.
- **Objective:** Verify the `submit_results` view correctly handles both anonymous and authenticated submissions at the database level.
- **Key Tasks (LLM):**
  1.  Write/Update Django Test Client tests in `multi_choice_quiz/tests/test_views.py` for the `submit_results` endpoint:
      - Include a test case for an unauthenticated POST, asserting the created `QuizAttempt.user` is `None`.
      - Include a test case using `client.force_login()` for an authenticated POST, asserting the created `QuizAttempt.user` matches the logged-in user.
- **Deliverables:** Updated `multi_choice_quiz/tests/test_views.py`.
- **Verification Checklist:**
  - `[ ]` **View Unit/Integration Tests Pass:** All tests in `test_views.py` pass.

**Step 2.4: Verify Anonymous E2E Flow & DB State**

- **Input:** Code from Step 2.3.
- **Objective:** Confirm that the end-to-end flow for an anonymous user completing a quiz still works and correctly results in an unassociated `QuizAttempt`.
- **Key Tasks (LLM):** None (User runs/adapts E2E tests).
- **Deliverables:** Test results, potentially adapted E2E test script.
- **Verification Checklist:**
  - `[ ]` **Anonymous E2E Test Passes:** Existing Playwright test for anonymous quiz completion runs successfully.
  - `[ ]` **Database Check (Anonymous):** Add verification (programmatic or manual via admin) confirming the `QuizAttempt` created during the anonymous E2E test has `user_id = NULL`.

---

### Phase 3: Basic User-Facing Profile & Navigation

- **Overall Objective:** Introduce a simple profile page accessible only to logged-in users and update the site navigation to reflect the user's authentication status.
- **Verification Focus:** Access control (`@login_required`), conditional template rendering, correct data display on profile page.

**Step 3.1: Create Profile View & URL (Login Required)**

- **Input:** Code from Phase 2.
- **Objective:** Set up the basic URL and view for the profile page, enforcing login.
- **Key Tasks (LLM):**
  1.  Create `profile_view` in `pages/views.py` decorated with `@login_required`. Initially, it should just render `pages/profile.html`.
  2.  Add a URL pattern for `/profile/` in `pages/urls.py` pointing to this view.
- **Deliverables:** Updated `pages/views.py`, updated `pages/urls.py`.
- **Verification Checklist:**
  - `[ ]` **Django Test Client - Profile Access:** Write tests verifying unauthenticated GET to `/profile/` redirects (302) to login, while authenticated GET returns 200 OK.

**Step 3.2: Implement Conditional Navigation**

- **Input:** Code from Step 3.1.
- **Objective:** Modify the base template's navigation bar to show appropriate links based on whether `user.is_authenticated`.
- **Key Tasks (LLM):**
  1.  Modify `pages/templates/pages/base.html`: Use `{% if user.is_authenticated %}` / `{% else %}` / `{% endif %}` template tags to conditionally display Login/Signup links vs. Profile/Logout links.
- **Deliverables:** Updated `pages/templates/pages/base.html`.
- **Verification Checklist:**
  - `[ ]` **Playwright - Conditional Nav:** Run E2E tests loading a page anonymously and authenticated, asserting the correct set of navigation links is visible in each case.

**Step 3.3: Display User History on Profile**

- **Input:** Code from Step 3.2.
- **Objective:** Fetch and display the logged-in user's quiz attempts on their profile page.
- **Key Tasks (LLM):**
  1.  Modify `profile_view` (`pages/views.py`): Query `QuizAttempt.objects.filter(user=request.user).order_by(...)` and pass the results to the template context (e.g., `{'quiz_attempts': ...}`).
  2.  Modify `pages/templates/pages/profile.html`: Replace static history content with a `{% for attempt in quiz_attempts %}` loop, displaying basic info (quiz title, score, date). Include an `{% empty %}` block.
- **Deliverables:** Updated `pages/views.py`, updated `pages/templates/pages/profile.html`.
- **Verification Checklist:**
  - `[ ]` **Django Test Client - Profile Context/Content:** Update authenticated profile test to create attempts for the test user, verify the attempts are passed in the context, and check for key details in the rendered HTML.
  - `[ ]` **Playwright - Profile History Display:** Run E2E test: log in, navigate to `/profile/`, verify previously submitted attempts for that user are displayed. Test the empty state.

---

### Phase 4: Final Regression & Modularity Check

- **Overall Objective:** Ensure all components work together correctly and that core anonymous functionality remains uncompromised.
- **Verification Focus:** Non-regression across the entire application.

**Step 4.1: Full Test Suite Execution**

- **Input:** Code from Phase 3.
- **Objective:** Run all automated tests to confirm integration and check for regressions.
- **Key Tasks (LLM):** None (User runs tests).
- **Deliverables:** Final test suite results.
- **Verification Checklist:**
  - `[ ]` **All Tests Pass:** The _entire_ test suite (all unit, integration, and E2E tests for all apps) passes. **Particular attention should be paid to tests simulating anonymous user flows.**

