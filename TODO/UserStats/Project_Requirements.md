# Project Requirements: QuizMaster

**Version:** 2.4
**Date:** 2025-05-06 (Revised NFRs for Verification & Testing approach)

## 1. Vision & Scope

QuizMaster is a personalized learning tool designed primarily for efficient self-study. Its core value lies in:

1.  **Rapid Quiz Content Creation:** Enabling the bulk import of hundreds of quiz questions from structured data sources within minutes using provided scripts.
2.  **Targeted Learning Feedback:** Allowing the user (initially, the developer) to take these imported quizzes and, most importantly, **tracking specific mistakes** made during attempts.
3.  **Personalized Review:** Utilizing the mistake data to identify weak areas (by question, topic, or chapter) and potentially suggest targeted quizzes or review sessions.

Organization of quizzes into **Collections** is a key supporting feature. General user features (complex profiles, social aspects, quiz creation UI) are secondary unless they directly support the core learning feedback loop or are easily implemented "quick wins". Functionality enabling the mistake analysis loop takes precedence over aesthetics.

## 2. Core Architecture

- **Backend:** Django (Python Web Framework)
- **Database:** PostgreSQL (Production), SQLite (Development/Testing) - Must efficiently store attempt details.
- **Frontend:** Standard HTML, CSS, JavaScript.
  - **Styling:** Tailwind CSS (via CDN initially)
  - **Interactivity:** Alpine.js (for quiz player and profile tabs)
- **Content Import:** Python scripts (`dir_import_chapter_quizzes.py`) processing Pandas DataFrames (Pickle format).
- **Authentication:** Django's built-in authentication system.

## 3. Phased Development Plan

_(Phases 1-4: Existing Foundational Components)_

### Phase 1: Core Django Auth Backend & Basic Templates (Existing Foundation)

- **Objective:** Establish foundational Django authentication and basic site structure.
- **Requirements:**
  - `1.a`: Integrate `django.contrib.auth` and `django.contrib.sessions` apps.
  - `1.b`: Configure necessary authentication middleware (`SessionMiddleware`, `AuthenticationMiddleware`).
  - `1.c`: Include default Django auth URLs under `/accounts/`.
  - `1.d`: Configure `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` settings.
  - `1.e`: Apply necessary authentication-related database migrations.
  - `1.f`: Create a base template (`pages/base.html`) providing consistent site structure and navigation.
  - `1.g`: Create basic templates for core auth views (`registration/login.html`, `registration/logged_out.html`) extending the base template.

### Phase 2: User Registration (Signup) (Existing Foundation)

- **Objective:** Allow the primary user to register.
- **Requirements:**
  - `2.a`: Create a `SignUpForm` inheriting from `UserCreationForm`, including an `email` field.
  - `2.b`: Implement a `signup_view` (GET/POST) using the `SignUpForm`.
  - `2.c`: Add a URL pattern `/signup/` mapped to the `signup_view` (e.g., `pages:signup`).
  - `2.d`: Create a `pages/signup.html` template extending `base.html` to render the signup form.
  - `2.e`: Upon successful registration, automatically log the user in and redirect them (e.g., to the profile page).

### Phase 3: Basic Quiz Models & Data Import (Existing Core)

- **Objective:** Define the database structure for quizzes and implement **core** data loading capabilities.
- **Requirements:**
  - `3.a`: Define `Topic`, `Quiz`, `Question`, `Option` models.
  - `3.b`: Implement `transform.py` utilities.
  - `3.c`: Implement `import_quiz_bank.py` management command (useful fallback/alternative).
  - `3.d`: Implement **`dir_import_chapter_quizzes.py`** script as the primary method for bulk, structured import from a directory of `.pkl` files, supporting chapter/topic organization. **(High Importance)**
  - `3.e`: Apply database migrations.

### Phase 4: Core Quiz Taking Functionality (Existing Core)

- **Objective:** Enable users to view and take imported quizzes.
- **Requirements:**
  - `4.a`: Implement `quiz_detail` view.
  - `4.b`: Pass quiz data to `multi_choice_quiz/index.html`.
  - `4.c`: Implement Alpine.js quiz player (`app.js`).
  - `4.d`: Implement basic CSS (`style.css`).
  - `4.e`: Implement fallback `home` view (can show latest quiz or demo).

---

## _(Core Functionality & Profile Foundation)_

### Phase 5: Foundational Attempt Tracking & Profile Page Structure (Revised)

- **Objective:** Store overall quiz attempt results and establish the **final, responsive profile page structure based on Mockup 1 (Stats Above Tabs)**, including the initial display of quiz history.
- **Requirements:**
  - `5.a`: Define `QuizAttempt` model with FK to User (**Mandatory**), FK to Quiz, `score`, `total_questions`, `percentage`, `start_time`, `end_time`. **Add a `JSONField` named `attempt_details` (nullable/blank initially) intended to store detailed mistake data in Phase 6.** Apply migrations.
  - `5.b`: Implement `submit_quiz_attempt` API endpoint. Must save basic attempt data, associate with user. Initially ignores detailed answer data.
  - `5.c`: Ensure frontend (`app.js`) sends basic results to `submit_quiz_attempt`.
  - `5.d`: Implement `profile_view` (`@login_required`).
  - `5.e`: `profile_view` fetches user's `QuizAttempt` records (most recent first).
  - `5.f`: **(Revised)** Create `pages/profile.html` template extending `base.html`. **Implement the HTML structure, Tailwind classes, and Alpine.js tab setup matching Mockup 1 (Stats Above Tabs).** Include sections for Stats (using static placeholders initially) and Tabs for "History" and "Collections". **Ensure the "Favorites" tab is omitted entirely.**
  - `5.g`: **(Revised)** Populate the "History" tab within the new structure (`5.f`) using the fetched `QuizAttempt` records from `5.e`.
  - `5.h`: **(New - Verification)** Verify the profile page structure (`5.f`) is reasonably responsive across defined breakpoints.

### Phase 6: Detailed Mistake Data Capture (NEW CORE - High Priority)

- **Objective:** Capture _exactly_ which questions were answered incorrectly during a quiz attempt.
- **Requirements:**
  - `6.a`: Modify frontend (`app.js`) to collect detailed answer data (e.g., `{question_id: user_selected_option_index}`).
  - `6.b`: Modify frontend (`app.js`) to include detailed answer data in the payload sent to `submit_quiz_attempt`.
  - `6.c`: Modify `submit_quiz_attempt` view to receive details, compare user/correct answers, generate mistake structure, and store it in the `attempt_details` JSONField of the `QuizAttempt`.

### Phase 7: Basic Mistake Review Interface (NEW CORE - High Priority)

- **Objective:** Allow the user to review the specific mistakes made in a past attempt.
- **Requirements:**
  - `7.a`: Create `attempt_mistake_review` view taking a `QuizAttempt` ID, retrieving the attempt and `attempt_details`.
  - `7.b`: The view fetches relevant `Question` objects for the mistakes.
  - `7.c`: Create `multi_choice_quiz/mistake_review.html` template to display Question text, User's incorrect answer, and Correct answer for each mistake.
  - `7.d`: Add a "Review Mistakes" link/button on the `profile.html` history list for attempts with recorded mistakes.

### Phase 8: Password Management (Necessary Utility)

- **Objective:** Implement standard Django password change and reset functionality.
- **Requirements:**
  - `8.a`: Ensure default Django `password_change`, `password_reset`, etc., URLs are included (via `accounts/`).
  - `8.b`: Create necessary templates (`registration/password_*.html`) extending `base.html`.
  - `8.c`: Create `registration/password_reset_email.html` template.
  - `8.d`: Configure `EMAIL_BACKEND` (e.g., console for development).

### Phase 9: Profile Enhancement - Dynamic Data & Quick Wins (Medium Priority - Revised)

- **Objective:** Populate the existing profile structure with dynamic collections and stats, and add basic profile editing.
- **Requirements:**
  - `9.a`: **Model:** Define `QuizCollection` model (`pages/models.py`) with `user` (FK), `name`, `description` (opt), timestamps. Add M2M `quizzes` to `QuizCollection`. Apply migrations.
  - `9.b`: **Admin:** Implement basic Django Admin for `QuizCollection`.
  - `9.c`: **Profile View Logic (`pages/views.py`):** Fetch user's `QuizCollection` objects (ordered, prefetch quizzes), fetch uncategorized `Quiz` objects, calculate simple stats (Total Taken, Avg Score), pass all to context.
  - `9.d`: **(Removed)** _This requirement is now integrated into Phase 5.f._
  - `9.e`: **(Revised)** **Profile Template Population (`profile.html`):** Populate the **existing** profile template structure (from Phase 5.f):
    - Display the calculated simple stats (Total Taken, Avg Score) in the designated areas (replacing static placeholders).
    - Under the "Collections" tab, display the fetched collections and their associated quizzes, plus the "Uncategorized" quizzes list (replacing static placeholders). Ensure quizzes link to their detail pages.
  - `9.f`: **Basic Edit Profile (Quick Win):** Implement `EditProfileForm` (email only), `edit_profile_view` (GET/POST), URL pattern in `pages/urls.py`, and `pages/edit_profile.html` template.
  - `9.g`: **Update Edit Link:** Update the "Edit Profile" link/button in the `profile.html` template to point to the new `edit_profile_view`.
  - `9.h`: **(Removed/Covered)** _Responsiveness check moved to Phase 5.h._
  - `9.i`: **UX Evaluation:** During implementation of collection display (Req 9.e), **evaluate the feasibility and benefit of using HTMX or AJAX** to dynamically load the content of the "Collections" tab only when it becomes active, especially if collection lists become large. Document the decision.

### Phase 10: Collection Management & Import Integration (Medium Priority)

- **Objective:** Allow users to create/manage collections and optionally integrate the import script.
- **Requirements:**
  - `10.a`: Implement view/form to _create_ new collections from the profile page. **Evaluate using HTMX/AJAX** for form submission and list update.
  - `10.b`: Implement view/logic to _move_ quizzes between collections. **Evaluate using HTMX/AJAX** for dynamic actions on the profile page. Add UI controls.
  - `10.c`: (Optional Enhancement) Modify `dir_import_chapter_quizzes.py` to optionally create/assign quizzes to a collection for the specified user during import.
  - `10.d`: Add controls (e.g., button/modal) to `pages/quizzes.html` and `multi_choice_quiz/index.html` allowing adding a quiz to an _existing_ collection. **Evaluate using HTMX/AJAX**.

---

## _(Future Core Goal)_

### Phase 11: Advanced Mistake Analysis & Quiz Suggestion (Future - High Importance)

*   **Objective:** Analyze aggregated mistake patterns and suggest relevant quizzes/topics for review.
*   **Requirements:**
    *   `11.a`: Develop backend logic to query `QuizAttempt.attempt_details` across multiple attempts.
    *   `11.b`: Identify patterns (frequently missed questions, weak topics/chapters/tags).
    *   `11.c`: Implement logic to suggest Quizzes or Topics based on analysis.
    *   `11.d`: Design and implement UI on the profile page (or dedicated dashboard) to present personalized suggestions.

---
*(Lowest Priority / Future)*
---

### Phase 12: Favorites (Future - Low Priority)

*   **Objective:** Allow users to mark quizzes as favorites.
*   **Requirements:**
    *   `12.a`: Add M2M `favorited_by` field to `Quiz` model.
    *   `12.b`: Implement toggle logic (view/AJAX/HTMX).
    *   `12.c`: Implement "Favorites" display (potentially re-adding the tab to `profile.html` if desired).
    *   `12.d`: Add toggle controls to quiz lists/detail pages.

---

## 4. Non-Functional Requirements

- **Verification & Testing:** Automated tests must cover the primary workflow (bulk import -> quiz taking -> mistake data capture -> mistake review display). **Each development phase will undergo specific verification, potentially utilizing dedicated test modules organized by feature/phase within the relevant app's test suite, to ensure phase objectives are met before proceeding.** Detailed testing strategies, including component and end-to-end testing approaches, are outlined in the `docs/TESTING_GUIDE.md`.
- **Responsiveness:** Application must be usable on common device sizes (mobile, tablet, desktop). Functionality over perfect aesthetics.
- **Code Quality:** Adhere to PEP 8 and standard Django practices.
- **Security:** Securely manage credentials; implement standard Django security measures.