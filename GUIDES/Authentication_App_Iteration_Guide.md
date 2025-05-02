# Iterative Development Process: Modular Authentication App (v2 - With Phase Verification Scripts)

**Core Philosophy:**

This guide outlines the step-by-step process for implementing user authentication within the Django Quiz App project. We will prioritize:

1.  **Modularity:** The authentication features (using `django.contrib.auth`) should enhance the application _without_ creating hard dependencies. The core quiz functionality must remain fully operational for anonymous users even if authentication features are later disabled or removed.
2.  **Reusability:** While tailored to this project, the underlying approach using standard Django components and optional linking should be conceptually reusable.
3.  **Iteration:** Development will proceed in small, distinct phases and steps.
4.  **Verification:** Each step will conclude with specific, automated verification checks (unit tests, integration tests, E2E tests, **phase verification scripts**). **No progression to the next step occurs unless all verification checks for the current step pass.** We will also perform regression testing to ensure previous functionality remains intact.

**LLM Interaction Model:**

The LLM will be provided with the current state of the codebase before each step. It will be tasked with implementing _only_ the specific changes required for that step. The user will then run the verification checks. If checks pass, the LLM proceeds to the next step. If checks fail, the LLM will be asked to revise the implementation for the current step based on the failure feedback.

---

## Authentication Implementation Phases

### Phase 1: Enable Core Django Auth Backend & Basic Templates

- **Overall Objective:** Activate Django's built-in authentication system (`django.contrib.auth`), create necessary database tables, and ensure basic, styled auth pages (login, logout confirmation) are available using the site's theme.
- **Verification Focus:** System stability, migrations, non-regression, basic auth template rendering, **phase-specific configuration checks**.
- **UX/UI Feel After This Phase:**
  - **Anonymous User:** For a typical user navigating the site (homepage, quiz browser, taking a quiz), the experience will be **identical** to before this phase.
  - **What's New (Hidden/Manual Access):** The default Django auth URLs (e.g., `/accounts/login/`, `/accounts/logout/`) now exist. If a user manually navigates to `/accounts/login/`, they will see a login form styled according to `pages/base.html`. Logging out via `/accounts/logout/` will show a styled confirmation page. There is no way to create users via the UI yet, and logging in wouldn't grant access to any new features beyond what `django.contrib.auth` provides internally.
  - **What's Unchanged:** Anonymous quiz taking, quiz browsing, page navigation (About, Home) remain fully functional and visually unchanged. Result submission still happens anonymously.

**Step 1.1: Configure Auth Apps & Middleware**

- **Input:** Codebase state before starting authentication implementation.
- **Objective:** Add the necessary authentication apps and middleware to the Django settings.
- **Key Tasks (LLM):**
  1.  Modify `core/settings.py`: Ensure `django.contrib.auth` and `django.contrib.sessions` are present in `INSTALLED_APPS`.
  2.  Modify `core/settings.py`: Ensure `django.contrib.sessions.middleware.SessionMiddleware` and `django.contrib.auth.middleware.AuthenticationMiddleware` are present in `MIDDLEWARE` in the appropriate order (Session before Auth).
- **Deliverables:** Updated `core/settings.py`.
- **Verification Checklist:**
  - `[ ]` **Django Checks Pass:** `python manage.py check` runs without errors.
  - `[ ]` **Server Starts:** `python manage.py runserver` starts without crashing.

**Step 1.2: Include Default Auth URLs**

- **Input:** Code from Step 1.1.
- **Objective:** Make Django's default authentication views (login, logout, etc.) accessible via URLs under the `/accounts/` path.
- **Key Tasks (LLM):**
  1.  Modify `core/urls.py`: Add `path("accounts/", include("django.contrib.auth.urls")),`.
  2.  Modify `core/settings.py`: Set `LOGIN_URL = 'login'` and ensure `LOGIN_REDIRECT_URL` (e.g., `'/'`) and `LOGOUT_REDIRECT_URL` (e.g., `'/'`) are defined.
- **Deliverables:** Updated `core/urls.py`, updated `core/settings.py`.
- **Verification Checklist:**
  - `[ ]` **Default Login URL Resolves:** `python manage.py shell -c "from django.urls import reverse; print(reverse('login'))"` outputs `/accounts/login/`.

**Step 1.3: Apply Auth Migrations**

- **Input:** Code from Step 1.2.
- **Objective:** Create the necessary database tables for the authentication system.
- **Key Tasks (LLM):** None (User runs the command).
- **Deliverables:** Database schema updated.
- **Verification Checklist:**
  - `[ ]` **Migrations Apply:** `python manage.py migrate` runs successfully, applying migrations for `auth`, `contenttypes`, `sessions`.

**Step 1.4: Create/Customize Core Auth Templates**

- **Input:** Code from Step 1.3.
- **Objective:** Ensure essential auth pages use the site's base template and styling.
- **Key Tasks (LLM):**
  1.  Ensure the top-level `templates` directory exists (`src/templates/`).
  2.  Modify `core/settings.py`: Ensure `TEMPLATES[0]['DIRS']` includes `[BASE_DIR / 'templates']`.
  3.  Create `src/templates/registration/login.html`: Must extend `pages/base.html`, include `{% csrf_token %}` in the form, have `method="POST"`, include inputs named `username` and `password`, and display form errors using `{{ form.non_field_errors }}` and optionally `{{ form.<field_name>.errors }}`.
  4.  Create `src/templates/registration/logged_out.html`: A simple page extending `pages/base.html` confirming logout.
- **Deliverables:** New `templates/registration/login.html`, new `templates/registration/logged_out.html`, potentially updated `settings.py`.
- **Verification Checklist:**
  - `[ ]` **Styled Login Page Loads:** Accessing `/accounts/login/` shows your custom, styled login page (run server).
  - `[ ]` **Manual Login/Logout Test:** Create a superuser (`manage.py createsuperuser`). Log in via `/accounts/login/`. Access `/accounts/logout/`. Verify the styled `logged_out.html` page is shown.

**Step 1.5: Full Regression Test**

- **Input:** Code from Step 1.4.
- **Objective:** Confirm that enabling the auth backend and basic templates has not negatively impacted any existing functionality (excluding known URL name changes in tests).
- **Key Tasks (LLM):** None (User runs the tests).
- **Deliverables:** Test results.
- **Verification Checklist:**
  - `[ ]` **Existing Tests Pass (Non-Auth):** Existing unit and E2E tests for core quiz/pages functionality pass. _(Note: Some `pages` tests related to `pages:login` might fail here, to be fixed in Phase 4)_.

**Step 1.6: Run Phase 1 Verification Script**

- **Input:** Code from Step 1.5.
- **Objective:** Automatically verify the specific configuration and setup outcomes of Phase 1 using the dedicated script.
- **Key Tasks (LLM):** Ensure `src/core/tests/test_phase1_verification.py` exists and is up-to-date.
- **Deliverables:** Test result for the phase verification script.
- **Verification Checklist:**
  - `[ ]` **Phase 1 Script Passes:** `python manage.py test core.tests.test_phase1_verification` runs successfully with 0 errors/failures.

---

**Phase 2: User Registration (Signup)**

- **Overall Objective:** Allow new users to create accounts via the web interface.
- **Verification Focus:** Form validation, successful user creation, redirection after signup, correct template rendering, **phase-specific configuration checks**.
- **UX/UI Feel After This Phase:**
  - **Anonymous User:** Sees "Sign Up" link in navigation. Clicking it leads to a functional, styled registration form at `/signup/`.
  - **Authenticated User:** Sees navigation without "Sign Up".
  - **What's New:** Successful signup creates a user, logs them in automatically, and redirects (e.g., to profile or home), possibly showing a success message.
  - **What's Unchanged:** Login, logout, anonymous quiz flow, profile viewing (for previously created users).

**Step 2.1: Create Signup Form & View**

- **Input:** Code from Phase 1.
- **Objective:** Implement the logic for user registration using Django's standard form.
- **Key Tasks (LLM):**
  1.  Create `pages/forms.py`. Define a `SignUpForm` class inheriting from `django.contrib.auth.forms.UserCreationForm`.
  2.  Modify `pages/views.py`: Replace the placeholder `signup_view`. Import `SignUpForm`, `login`, `messages`, `redirect`. Handle GET (display form) and POST (process form, validate, save user, login user, add success message, redirect).
- **Deliverables:** New `pages/forms.py`, updated `pages/views.py`.
- **Verification Checklist:**
  - `[ ]` **View Unit Tests:** Write/run tests in `pages/tests/test_views.py` for `signup_view` (GET, invalid POST, valid POST).

**Step 2.2: Implement Signup Template**

- **Input:** Code from Step 2.1.
- **Objective:** Create the user-facing registration form using the Django form.
- **Key Tasks (LLM):**
  1.  Modify `pages/templates/pages/signup.html`: Ensure form has `method="POST"`, `{% csrf_token %}`. Render form fields (`{{ form.as_p }}`) and errors. Remove placeholder notice.
- **Deliverables:** Updated `pages/templates/pages/signup.html`.
- **Verification Checklist:**
  - `[ ]` **Signup Page Renders Form:** Accessing `/signup/` shows the actual form fields (run server).
  - `[ ]` **Form Validation UI Test:** Manual test: attempt signup with invalid data, verify errors appear.
  - `[ ]` **Successful Signup UI Test:** Manual test: complete signup, verify user created, logged in, redirected.

**Step 2.3: Run Phase 2 Verification Script** (Assuming you create one for this phase)

- **Input:** Code from Step 2.2.
- **Objective:** Automatically verify the specific configuration and setup outcomes of Phase 2.
- **Key Tasks (LLM):** Create `src/pages/tests/test_phase2_verification.py` (or similar) checking signup URL resolution, form availability in view context etc.
- **Deliverables:** Test result for the phase verification script.
- **Verification Checklist:**
  - `[ ]` **Phase 2 Script Passes:** `python manage.py test pages.tests.test_phase2_verification` runs successfully.

---

**Phase 3: Optional Linking of Quiz Attempts to Users**

- **Overall Objective:** Modify the quiz result submission process to associate attempts with logged-in users _if available_, while maintaining full functionality for anonymous users.
- **Verification Focus:** Correct database schema changes, conditional logic in views, distinct handling of anonymous vs. authenticated submissions confirmed via tests, **phase-specific configuration checks**.
- **UX/UI Feel After This Phase:**
  - **No visible changes** to the user interface or user experience compared to Phase 2. Backend links attempts if logged in.

**Step 3.1: Modify Models & Generate Migrations**

- **Input:** Code from Phase 2.
- **Objective:** Add an optional `user` foreign key to the `QuizAttempt` model.
- **Key Tasks (LLM):**
  1.  Modify `multi_choice_quiz/models.py`: Add `user` ForeignKey to `QuizAttempt` (null=True, blank=True, on_delete=models.SET_NULL, related_name='quiz_attempts'). Import `get_user_model`.
- **Deliverables:** Updated `multi_choice_quiz/models.py`.
- **Verification Checklist:**
  - `[ ]` **Makemigrations Runs:** `python manage.py makemigrations multi_choice_quiz` creates migration.
  - `[ ]` **Migration Applies:** `python manage.py migrate` runs successfully.

**Step 3.2: Update Submission View Logic**

- **Input:** Code from Step 3.1.
- **Objective:** Modify the `submit_quiz_attempt` view to assign `request.user` if authenticated.
- **Key Tasks (LLM):**
  1.  Modify `multi_choice_quiz/views.py`: In `submit_quiz_attempt`, set `attempt_user = request.user if request.user.is_authenticated else None`. Pass `user=attempt_user` when creating `QuizAttempt`.
- **Deliverables:** Updated `multi_choice_quiz/views.py`.
- **Verification Checklist:**
  - `[ ]` **Python Linting:** Code passes linter checks (`ruff`).

**Step 3.3: Write/Update Submission Tests**

- **Input:** Code from Step 3.2.
- **Objective:** Verify the `submit_quiz_attempt` view correctly handles both anonymous and authenticated submissions in the database.
- **Key Tasks (LLM):**
  1.  Update tests in `multi_choice_quiz/tests/test_views.py`: Ensure tests exist and pass for anonymous POST (user=None) and authenticated POST (user=correct user).
- **Deliverables:** Updated `multi_choice_quiz/tests/test_views.py`.
- **Verification Checklist:**
  - `[ ]` **View Unit/Integration Tests Pass:** All tests in `multi_choice_quiz/tests/test_views.py` pass.

**Step 3.4: Verify Anonymous E2E Flow & DB State**

- **Input:** Code from Step 3.3.
- **Objective:** Confirm end-to-end anonymous quiz completion still results in `user=None` attempt.
- **Key Tasks (LLM):** None (User runs/adapts E2E tests).
- **Deliverables:** Test results.
- **Verification Checklist:**
  - `[ ]` **Anonymous E2E Test Passes:** `run_multi_choice_quiz_e2e_tests.py` passes.
  - `[ ]` **Database Check (Anonymous):** Verify (programmatically or manually) the `QuizAttempt` created has `user_id = NULL`.

**Step 3.5: Run Phase 3 Verification Script** (Using `test_phase2_verification.py` which maps to this phase)

- **Input:** Code from Step 3.4.
- **Objective:** Automatically verify the specific model and view setup outcomes of Phase 3.
- **Key Tasks (LLM):** Ensure `src/core/tests/test_phase2_verification.py` exists and is up-to-date.
- **Deliverables:** Test result for the phase verification script.
- **Verification Checklist:**
  - `[ ]` **Phase 3 Script Passes:** `python manage.py test core.tests.test_phase2_verification` runs successfully.

---

**Phase 4: Basic User-Facing Profile & Navigation**

- **Overall Objective:** Introduce a simple profile page accessible only to logged-in users and update site navigation based on auth status.
- **Verification Focus:** Access control (`@login_required`), conditional template rendering, correct data display, URL name resolution, **phase-specific configuration checks**.
- **UX/UI Feel After This Phase:**
  - **Anonymous User:** Navigation shows "Login" (`/accounts/login/`) and "Sign Up". Accessing `/profile/` redirects to login.
  - **Authenticated User:** Navigation shows "Profile" (with username) and "Logout". Can access `/profile/`, which displays their info and quiz attempt history.

**Step 4.1: Create/Verify Profile View & URL (Login Required)**

- **Input:** Code from Phase 3.
- **Objective:** Ensure the profile URL/view exist and enforce login. Fix related test URL lookups.
- **Key Tasks (LLM):**
  1.  Verify `pages/views.py` has `profile_view` decorated with `@login_required`.
  2.  Verify `pages/urls.py` maps `/profile/` to `profile_view` with `name='profile'`.
  3.  Modify `pages/tests/test_views.py`: Update `test_profile_page_redirects_when_not_logged_in` to expect redirect to `reverse('login')`.
- **Deliverables:** Updated `pages/tests/test_views.py`, verified `pages/views.py`, `pages/urls.py`.
- **Verification Checklist:**
  - `[ ]` **Django Test Client - Profile Access:** Run tests in `pages/tests/test_views.py`. Verify `test_profile_page_redirects_when_not_logged_in` and `test_profile_page_loads_when_logged_in` pass.

**Step 4.2: Implement Conditional Navigation**

- **Input:** Code from Step 4.1.
- **Objective:** Update base template navigation to show correct links based on auth status, using correct URL names.
- **Key Tasks (LLM):**
  1.  Modify `pages/templates/pages/base.html`: Use `{% if user.is_authenticated %}`/`{% else %}`. Ensure links use `{% url 'login' %}`, `{% url 'logout' %}`, `{% url 'pages:profile' %}`, `{% url 'pages:signup' %}` correctly. Display username.
- **Deliverables:** Updated `pages/templates/pages/base.html`.
- **Verification Checklist:**
  - `[ ]` **Playwright - Conditional Nav:** Run E2E tests (`run_pages_e2e_tests.py`, `test_anonymous_user_navigation`, `test_authenticated_user_navigation`). Assert correct links/visibility.

**Step 4.3: Display User History on Profile**

- **Input:** Code from Step 4.2.
- **Objective:** Fetch and display the logged-in user's quiz attempts on their profile page.
- **Key Tasks (LLM):**
  1.  Modify `pages/views.py` (`profile_view`): Query `QuizAttempt.objects.filter(user=request.user).order_by('-end_time')` and pass as `quiz_attempts` to context.
  2.  Modify `pages/templates/pages/profile.html`: Loop through `quiz_attempts`, display info, include `{% empty %}` block. Remove placeholders.
- **Deliverables:** Updated `pages/views.py`, updated `pages/templates/pages/profile.html`.
- **Verification Checklist:**
  - `[ ]` **Django Test Client - Profile Context/Content:** Run tests in `pages/tests/test_views.py`. Verify `test_profile_page_displays_user_history` and `test_profile_page_empty_history_message` pass.
  - `[ ]` **Playwright - Profile History Display:** Run E2E tests (`run_pages_e2e_tests.py`). Verify history/empty message displays correctly.

**Step 4.4: Run Phase 4 Verification Script** (Using `test_phase3_verification.py` which maps to this phase)

- **Input:** Code from Step 4.3.
- **Objective:** Automatically verify the specific view setup, access control, and context data outcomes of Phase 4.
- **Key Tasks (LLM):** Ensure `src/core/tests/test_phase3_verification.py` exists, is up-to-date, and correctly tests profile access/context. _It might need updates to reflect the `reverse('login')` change._
- **Deliverables:** Test result for the phase verification script.
- **Verification Checklist:**
  - `[ ]` **Phase 4 Script Passes:** `python manage.py test core.tests.test_phase3_verification` runs successfully.

---

**Phase 5: Password Management**

- **Overall Objective:** Implement secure password change (for logged-in users) and password reset (for forgotten passwords) functionality using Django's built-in views and forms.
- **Verification Focus:** Correct template rendering, email sending via console (for reset), successful password updates, correct redirections, **phase-specific configuration checks**.
- **UX/UI Feel After This Phase:**
  - **Authenticated User:** Can access `/accounts/password_change/`, see a styled form, change their password, and see a styled confirmation.
  - **Any User:** Can access `/accounts/password_reset/`, enter email, receive a (console) email with a reset link, click link, access `/accounts/reset/<uidb64>/<token>/`, set a new password via a styled form, and see a styled confirmation.

**Step 5.1: Implement Password Change Templates**

- **Input:** Code from Phase 4.
- **Objective:** Allow logged-in users to change their password using styled forms.
- **Key Tasks (LLM):**
  1.  Create `src/templates/registration/password_change_form.html`: Extend `pages/base.html`, include CSRF, POST method, render `{{ form.as_p }}`, submit button.
  2.  Create `src/templates/registration/password_change_done.html`: Extend `pages/base.html`, display success message, link back.
- **Deliverables:** `templates/registration/password_change_form.html`, `templates/registration/password_change_done.html`.
- **Verification Checklist:**
  - `[ ]` **Password Change Pages Load:** Log in, access `/accounts/password_change/`, `/accounts/password_change/done/` - verify styled pages load (run server).
  - `[ ]` **Manual Test:** Change password via UI. Log out, log in with new password.

**Step 5.2: Implement Password Reset Templates**

- **Input:** Code from Step 5.1.
- **Objective:** Provide styled templates for the multi-step password reset flow.
- **Key Tasks (LLM):**
  1.  Create `templates/registration/password_reset_form.html` (Extend base, CSRF, POST, `{{ form.as_p }}`).
  2.  Create `templates/registration/password_reset_done.html` (Extend base, "Check email" message).
  3.  Create `templates/registration/password_reset_confirm.html` (Extend base, CSRF, POST, `{{ form.as_p }}`, check `validlink`).
  4.  Create `templates/registration/password_reset_complete.html` (Extend base, "Success" message, link to `{% url 'login' %}`).
  5.  Create `templates/registration/password_reset_email.html` (Plain text email body with reset link `{% url 'password_reset_confirm' ... %}`).
- **Deliverables:** The five new template files in `templates/registration/`.
- **Verification Checklist:**
  - `[ ]` **Password Reset Pages Load:** Access `/accounts/password_reset/`, `/accounts/password_reset/done/`, `/accounts/reset/done/` - verify styled pages load (run server).

**Step 5.3: Configure Email Backend (Console)**

- **Input:** Code from Step 5.2.
- **Objective:** Set up Django to "send" emails to the console for development testing.
- **Key Tasks (LLM):**
  1.  Modify `core/settings.py`: Add `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`.
- **Deliverables:** Updated `core/settings.py`.
- **Verification Checklist:**
  - `[ ]` **Password Reset Email Sent (Console):** Use `/accounts/password_reset/` form. Verify reset email content prints to `runserver` console.

**Step 5.4: Test Password Management Flows**

- **Input:** Code from Step 5.3.
- **Objective:** Verify the end-to-end password change and reset flows using console email.
- **Key Tasks (LLM):** None (User performs tests).
- **Deliverables:** Test results.
- **Verification Checklist:**
  - `[ ]` **Manual Test (Password Change):** Log in, change password via UI, log out, log in with new password.
  - `[ ]` **Manual Test (Password Reset):** Use reset form, copy link from console, set new password via link form, verify success, log in with new password.

**Step 5.5: Run Phase 5 Verification Script** (Requires creating a new script)

- **Input:** Code from Step 5.4.
- **Objective:** Automatically verify the specific template existence and email backend configuration for Phase 5.
- **Key Tasks (LLM):** Create `src/core/tests/test_phase5_verification.py` checking template loading for password mgmt URLs and `settings.EMAIL_BACKEND`.
- **Deliverables:** Test result for the phase verification script.
- **Verification Checklist:**
  - `[ ]` **Phase 5 Script Passes:** `python manage.py test core.tests.test_phase5_verification` runs successfully.

---

**Phase 6: Final Regression & Modularity Check**

- **Overall Objective:** Ensure all components work together correctly and that core anonymous functionality remains uncompromised.
- **Verification Focus:** Non-regression across the entire application.
- **UX/UI Feel After This Phase:**
  - The user experience is **identical to the end of Phase 5**. This phase involves no new features or UI changes. Full basic authentication functionality is in place and verified.

**Step 6.1: Full Test Suite Execution**

- **Input:** Code from Phase 5.
- **Objective:** Run all automated tests to confirm integration and check for regressions.
- **Key Tasks (LLM):** None (User runs tests).
- **Deliverables:** Final test suite results.
- **Verification Checklist:**
  - `[ ]` **All Backend Tests Pass:** `python manage.py test` runs successfully with 0 errors/failures (includes all unit tests and phase verification scripts).
  - `[ ]` **All E2E Tests Pass:** `run_multi_choice_quiz_e2e_tests.py` and `run_pages_e2e_tests.py` run successfully with 0 failures.
