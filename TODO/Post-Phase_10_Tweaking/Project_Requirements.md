# Project Requirements: QuizMaster

**Version:** 2.6
**Date:** 2025-05-12 (Reflects UI/UX Tweaking Phase Insertion)

## 1. Vision & Scope

QuizMaster is a personalized learning tool designed primarily for efficient self-study. Its core value lies in:

1.  **Rapid Quiz Content Creation:** Enabling the bulk import of hundreds of quiz questions from structured data sources within minutes using provided scripts.
2.  **Targeted Learning Feedback:** Allowing the user (initially, the developer) to take these imported quizzes and, most importantly, **tracking specific mistakes** made during attempts.
3.  **Personalized Review:** Utilizing the mistake data to identify weak areas (by question, topic, or chapter) and potentially suggest targeted quizzes or review sessions.

Organization of quizzes is crucial, facilitated through two mechanisms:
_ **Public Categories (`SystemCategory`):** Admin-managed categories (e.g., "History", "Science") for general browsing and discovery.
_ **Private Collections (`UserCollection`):** User-created groupings for personal organization (e.g., "Study Set", "Weak Areas").

General user features (complex profiles, social aspects, quiz creation UI) are secondary unless they directly support the core learning feedback loop or are easily implemented "quick wins". Functionality enabling the mistake analysis loop takes precedence over aesthetics.

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

### Phase 5: Foundational Attempt Tracking & Profile Page Structure (Revised) - COMPLETE

- **Objective:** Store overall quiz attempt results and establish the **final, responsive profile page structure based on Mockup 1 (Stats Above Tabs)**, including the initial display of quiz history.
- **Requirements:**
  - `5.a`: Define `QuizAttempt` model with FK to User (**Mandatory**), FK to Quiz, `score`, `total_questions`, `percentage`, `start_time`, `end_time`. **Add a `JSONField` named `attempt_details` (nullable/blank initially) intended to store detailed mistake data in Phase 6.** Apply migrations.
  - `5.b`: Implement `submit_quiz_attempt` API endpoint. Must save basic attempt data, associate with user. Initially ignores detailed answer data.
  - `5.c`: Ensure frontend (`app.js`) sends basic results to `submit_quiz_attempt`.
  - `5.d`: Implement `profile_view` (`@login_required`).
  - `5.e`: `profile_view` fetches user's `QuizAttempt` records (most recent first).
  - `5.f`: Create `pages/profile.html` template extending `base.html`. Implement the HTML structure, Tailwind classes, and Alpine.js tab setup matching Mockup 1 (Stats Above Tabs). Include sections for Stats (using static placeholders initially) and Tabs for "History" and "Collections". Ensure the "Favorites" tab is omitted entirely.
  - `5.g`: Populate the "History" tab within the new structure (`5.f`) using the fetched `QuizAttempt` records from `5.e`.
  - `5.h`: Verify the profile page structure (`5.f`) is reasonably responsive across defined breakpoints.

### Phase 6: Detailed Mistake Data Capture (NEW CORE - High Priority) - COMPLETE

- **Objective:** Capture _exactly_ which questions were answered incorrectly during a quiz attempt.
- **Requirements:**
  - `6.a`: Modify frontend (`app.js`) to collect detailed answer data (e.g., `{question_id: user_selected_option_index}`).
  - `6.b`: Modify frontend (`app.js`) to include detailed answer data in the payload sent to `submit_quiz_attempt`.
  - `6.c`: Modify `submit_quiz_attempt` view to receive details, compare user/correct answers, generate mistake structure, and store it in the `attempt_details` JSONField of the `QuizAttempt`.

### Phase 7: Basic Mistake Review Interface (NEW CORE - High Priority) - COMPLETE

- **Objective:** Allow the user to review the specific mistakes made in a past attempt.
- **Requirements:**
  - `7.a`: Create `attempt_mistake_review` view taking a `QuizAttempt` ID, retrieving the attempt and `attempt_details`.
  - `7.b`: The view fetches relevant `Question` objects for the mistakes.
  - `7.c`: Create `multi_choice_quiz/mistake_review.html` template to display Question text, User's incorrect answer, and Correct answer for each mistake.
  - `7.d`: Add a "Review Mistakes" link/button on the `profile.html` history list for attempts with recorded mistakes.

### Phase 8: Password Management (Necessary Utility) - COMPLETE

- **Objective:** Implement standard Django password change and reset functionality.
- **Requirements:**
  - `8.a`: Ensure default Django `password_change`, `password_reset`, etc., URLs are included (via `accounts/`).
  - `8.b`: Create necessary templates (`registration/password_*.html`) extending `base.html`.
  - `8.c`: Create `registration/password_reset_email.html` template.
  - `8.d`: Configure `EMAIL_BACKEND` (e.g., console for development).

---

## _(Collections, Profile Population & Management)_

### Phase 9: Collection Models, Profile Population & Public Browsing (Revised) - COMPLETE

- **Objective:** Implement models for both public categories (`SystemCategory`) and private user collections (`UserCollection`). Populate the profile page with dynamic stats and private collections. Update public quiz browsing to use categories.
- **Requirements:**
  - `9.a`: **Models:** Define `SystemCategory` model for public categories (name, slug, description, M2M->Quiz). Define `UserCollection` model for private collections (user FK, name, description, M2M->Quiz, timestamps). Apply migrations.
  - `9.b`: **Admin:** Implement basic Django Admin interfaces for `SystemCategory` and `UserCollection`.
  - `9.c`: **Profile View Logic (`pages/views.py::profile_view`):** Fetch user's `UserCollection`s, uncategorized quizzes, calculate simple stats (Total Taken, Avg Score), pass all to context.
  - `9.d`: **Profile Template Population (`profile.html`):** Populate template: display stats; display `UserCollection`s & uncategorized quizzes under "Collections" tab.
  - `9.e`: **Public Browsing View (`pages/views.py::quizzes`):** Update view to use `SystemCategory` for filtering. Pass categories to context.
  - `9.f`: **Public Browsing Template (`pages/quizzes.html`):** Update template to display `SystemCategory` filters.
  - `9.g`: **Homepage View (`pages/views.py::home`):** Optionally, update view to display featured `SystemCategory` instances.
  - `9.h`: **Basic Edit Profile (Quick Win):** Implement `EditProfileForm` (email only), `edit_profile_view` (GET/POST), URL pattern, and template.
  - `9.i`: **Update Edit Link:** Update profile template's "Edit Profile" link.
  - `9.j`: **UX Evaluation:** Evaluate HTMX/AJAX for loading "Collections" tab content; document decision. (Decision: Defer HTMX for now).

### Phase 10: User Collection Management & Import Integration (Revised) - COMPLETE

- **Objective:** Allow users to create/manage their private `UserCollection`s. Implement UI for adding global quizzes to private collections. (Req 10.c, enhancing import scripts for `SystemCategory`, has been completed).
- **Requirements:**
  - `10.a`: Implement ability to create `UserCollection`s (form, view, URL, UI trigger on profile). Evaluate HTMX/AJAX for this interaction. (Decision: Full page reload implemented).
  - `10.b`: Implement ability to remove quizzes from `UserCollection`s via the profile page. Evaluate HTMX/AJAX. (Decision: Full page reload implemented).
  - `10.c`: **(Completed)** Enhance import scripts (`dir_import_chapter_quizzes.py`, `import_questions_by_chapter` utility) to allow assigning imported quizzes to a specified `SystemCategory` via a CLI argument or based on a DataFrame column.
  - `10.d`: Implement UI controls on public quiz listing pages (e.g., `/quizzes/`, homepage featured quizzes) for authenticated users to add a quiz to one of their existing `UserCollection`s. This involves a selection mechanism if multiple collections exist. Evaluate HTMX/AJAX. (Decision: Full page redirect flow implemented).

---

## _(UI/UX Enhancement)_

### Phase 11: Post-Phase 10 UI/UX Tweaking (NEW)

- **Objective:** Enhance the user interface and user experience based on observations and priorities identified after the completion of core collection management features. These are primarily template and view modifications without DB schema changes.
- **Requirements:**
  - `11.a`: **Navbar Enhancements:**
    - Modify the profile link in the navbar for logged-in users to be more concise (e.g., "(username)" instead of "Profile (username)").
    - Add a placeholder avatar (e.g., user's initial in a circle) next to the username in the navbar.
  - `11.b`: **Improved Redirection for Collections:**
    - When adding a quiz to a collection, redirect the user back to the page they initiated the action from (e.g., `/quizzes/` or quiz detail page) instead of their profile.
  - `11.c`: **Refined Quiz List Presentation:**
    - On public quiz listing pages (`/quizzes/`, homepage featured quizzes), reorder quizzes so that those already attempted by the logged-in user appear at the end of the list.
    - For featured quizzes on the homepage, prioritize displaying quizzes the logged-in user has not yet attempted.
  - `11.d`: **Enhanced Profile Page Collections Tab:**
    - Make individual collection items (listing their quizzes) in the "Collections" tab on the profile page collapsible/expandable using Alpine.js.
  - `11.e`: **Profile Page Polish:**
    - Update placeholder text for "Strongest Topic" and "Needs Review" stats on the profile page to be more informative (e.g., "Analysis Coming Soon!").
    - In the "Quiz History" tab, display how many times each listed quiz has been taken by the user.

---

## _(Future Core Goal)_

### Phase 12: Advanced Mistake Analysis & Quiz Suggestion (Future - High Importance) (Previously Phase 11)

- **Objective:** Analyze aggregated mistake patterns and suggest relevant quizzes/topics for review.
- **Requirements:**
  - `12.a`: Develop backend logic to query `QuizAttempt.attempt_details`. (Previously 11.a)
  - `12.b`: Identify patterns (frequently missed questions, weak topics/`SystemCategory`/tags). (Previously 11.b)
  - `12.c`: Implement logic to suggest Quizzes or `SystemCategory` instances. (Previously 11.c)
  - `12.d`: Design and implement UI for suggestions. (Previously 11.d)

---

## _(Lowest Priority / Future)_

### Phase 13: Favorites (Future - Low Priority) (Previously Phase 12)

- **Objective:** Allow users to mark quizzes as favorites (alternative or supplementary to `UserCollection`).
- **Requirements:**
  - `13.a`: Add M2M `favorited_by` field to `Quiz` model. (Previously 12.a)
  - `13.b`: Implement toggle logic (view/AJAX/HTMX). (Previously 12.b)
  - `13.c`: Implement "Favorites" display. (Previously 12.c)
  - `13.d`: Add toggle controls to quiz lists/detail pages. (Previously 12.d)

---

## 4. Non-Functional Requirements

- **Verification & Testing:** Automated tests must cover the primary workflow (bulk import -> quiz taking -> mistake data capture -> mistake review display). **Each development phase will undergo specific verification, potentially utilizing dedicated test modules organized by feature/phase within the relevant app's test suite, to ensure phase objectives are met before proceeding.** Detailed testing strategies, including component and end-to-end testing approaches, are outlined in the `docs/TESTING_GUIDE.md`.
- **Responsiveness:** Application must be usable on common device sizes (mobile, tablet, desktop). Functionality over perfect aesthetics.
- **Code Quality:** Adhere to PEP 8 and standard Django practices.
- **Security:** Securely manage credentials; implement standard Django security measures.