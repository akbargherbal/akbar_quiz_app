# Iteration Guide: Profile & Core Learning Features

**Scope:** Tracking implementation for user profile enhancements, mistake tracking/review, and quiz collections (Phases 5-11, as defined in Project Requirements v2.4).
**Template:** Standard Iteration Guide (LGID v3)
**Current Date:** 2025-05-06
**Overall Status:** Phase 5 Planned

---
---

## Phase 5: Foundational Attempt Tracking & Profile Page Structure (Revised)

**Version:** 1.0
**Date:** 2025-05-06
**Phase Objective:** Store overall quiz attempt results, establish the final responsive profile page structure (Mockup 1: Stats Above Tabs), display initial history, and add the `attempt_details` field for future use.
**Related Requirements:** 5.a, 5.b, 5.c, 5.d, 5.e, 5.f (Revised), 5.g (Revised), 5.h (New)
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 5.1: Add `attempt_details` JSONField to `QuizAttempt` Model

*   **Objective:** Add the database field for storing detailed mistake data (Req 5.a).
*   **Key Tasks:**
    1.  Modify `QuizAttempt` model in `multi_choice_quiz/models.py` to include a `JSONField` named `attempt_details` (nullable, blankable).
    2.  Generate and apply database migrations.
*   **Deliverables:**
    *   Updated `multi_choice_quiz/models.py`.
    *   New migration file(s) in `multi_choice_quiz/migrations/`.
*   **Verification Checklist:**
    *   `[ ]` `python manage.py check` passes.
    *   `[ ]` `python manage.py migrate` applies successfully.
    *   `[ ]` **Unit Test:** Add/run test in `test_models.py` confirming `attempt_details` field exists and accepts null/JSON.
*   **Status:** To Do ⏳

#### Step 5.2: Implement Basic `submit_quiz_attempt` API Endpoint

*   **Objective:** Create backend endpoint to save basic `QuizAttempt` data (Req 5.b).
*   **Key Tasks:**
    1.  Implement `submit_quiz_attempt` view in `multi_choice_quiz/views.py` (handle POST, parse JSON, validate basic payload, determine user, save `QuizAttempt` ignoring `attempt_details`, return JSON response).
    2.  Map URL in `multi_choice_quiz/urls.py`.
*   **Deliverables:**
    *   Updated `multi_choice_quiz/views.py`.
    *   Updated `multi_choice_quiz/urls.py`.
*   **Verification Checklist:**
    *   `[ ]` **Unit Tests:** Run relevant tests in `multi_choice_quiz/tests/test_views.py` verifying successful/failed submissions for anonymous and authenticated users.
*   **Status:** To Do ⏳

#### Step 5.3: Ensure Frontend Sends Basic Results

*   **Objective:** Update quiz player JS to POST basic results on completion (Req 5.c).
*   **Key Tasks:**
    1.  Modify `app.js` to gather required data (`quiz_id`, score, total, %, end_time) and POST to the `submit_quiz_attempt` endpoint using `fetch`.
    2.  Ensure `quiz_id` is passed from the template to the JS context.
*   **Deliverables:**
    *   Updated `multi_choice_quiz/static/multi_choice_quiz/app.js`.
    *   Updated `multi_choice_quiz/templates/multi_choice_quiz/index.html`.
*   **Verification Checklist:**
    *   `[ ]` **Manual E2E Check:** Take quiz (logged out/in), verify POST request in network tab & basic `QuizAttempt` saved in DB (with `user` correctly set/null).
*   **Status:** To Do ⏳

#### Step 5.4: Implement `profile_view` Logic

*   **Objective:** Create view to fetch user's quiz attempt history (Req 5.d, 5.e).
*   **Key Tasks:**
    1.  Implement `profile_view` in `pages/views.py`, decorated with `@login_required`.
    2.  Fetch user's `QuizAttempt` records (ordered).
    3.  Pass attempts to template context.
    4.  Map URL in `pages/urls.py`.
*   **Deliverables:**
    *   Updated `pages/views.py`.
    *   Updated `pages/urls.py`.
*   **Verification Checklist:**
    *   `[ ]` **Unit Tests:** Run relevant tests in `pages/tests/test_views.py` verifying login requirement and context data.
*   **Status:** To Do ⏳

#### Step 5.5: Restructure `profile.html` (Mockup 1 Layout) & Populate History

*   **Objective:** Implement Mockup 1 structure; display history (Req 5.f Rev, 5.g Rev).
*   **Key Tasks:**
    1.  Modify `pages/templates/pages/profile.html` to match Mockup 1 structure (Stats section above Alpine.js tabs for "History" & "Collections").
    2.  Remove "Favorites" tab elements.
    3.  Place existing history loop within the "History" tab content.
    4.  Use static placeholders for Stats and Collections content areas.
*   **Deliverables:**
    *   Updated `pages/templates/pages/profile.html`.
*   **Verification Checklist:**
    *   `[ ]` **Manual E2E Check:** Log in, view profile, check structure (Stats above tabs), check tab presence ("History", "Collections" only), check tab switching, confirm history list renders in correct tab.
*   **Status:** To Do ⏳

#### Step 5.6: Verify Profile Page Responsiveness

*   **Objective:** Ensure Mockup 1 structure is reasonably responsive (Req 5.h New).
*   **Key Tasks:**
    1.  Manually check profile page layout across breakpoints using browser dev tools.
    2.  **Update** `pages/tests/test_responsive.py::test_profile_responsive_layout` to assert key elements of the *new* structure are visible/positioned correctly at different breakpoints.
*   **Deliverables:**
    *   Updated `pages/tests/test_responsive.py`.
*   **Verification Checklist:**
    *   `[ ]` Manual inspection passes.
    *   `[ ]` **E2E Test:** `pytest src/pages/tests/test_responsive.py::test_profile_responsive_layout` passes with updated assertions.
*   **Status:** To Do ⏳

#### Step 5.7: Phase 5 Verification

*   **Objective:** Ensure all Phase 5 objectives are met integratively.
*   **Key Tasks:**
    1.  Create verification script `src/pages/tests/user_profile/test_phase5_verification.py`.
    2.  Add tests verifying: `attempt_details` field exists, `profile_view` requires login, basic Mockup 1 structure (stats section, correct tabs) renders.
*   **Deliverables:**
    *   New `src/pages/tests/user_profile/test_phase5_verification.py`.
*   **Verification Checklist:**
    *   `[ ]` All relevant unit tests pass (`pytest src/multi_choice_quiz/tests/`, `pytest src/pages/tests/ --ignore=src/pages/tests/user_profile/`).
    *   `[ ]` All relevant E2E tests pass (`pytest src/pages/tests/test_responsive.py src/pages/tests/test_templates.py`).
    *   `[ ]` **Phase Verification Script Passes:** `pytest src/pages/tests/user_profile/test_phase5_verification.py`.
*   **Status:** To Do ⏳

---
---

## Phase 6: Detailed Mistake Data Capture (High Priority)

**Version:** 1.0
**Date:** 2025-05-06
**Phase Objective:** Capture _exactly_ which questions were answered incorrectly during a quiz attempt and store this data.
**Related Requirements:** 6.a, 6.b, 6.c
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 6.1: Frontend Data Collection (`app.js`)

*   **Objective:** Collect detailed answer data during the quiz (Req 6.a).
*   **Key Tasks:** Modify `app.js` to store user's selected answer index for each question ID during the quiz.
*   **Deliverables:** Updated `multi_choice_quiz/static/multi_choice_quiz/app.js`.
*   **Verification Checklist:** `[ ]` Manual check (e.g., `console.log`) or JS unit test confirms data structure is populated correctly.
*   **Status:** To Do ⏳

#### Step 6.2: Frontend Payload Update (`app.js`)

*   **Objective:** Include collected answer details in the results payload (Req 6.b).
*   **Key Tasks:** Modify `app.js` `submitResults` function to add the collected detailed answers to the JSON payload sent via `fetch`.
*   **Deliverables:** Updated `multi_choice_quiz/static/multi_choice_quiz/app.js`.
*   **Verification Checklist:** `[ ]` Manual check (network tab) confirms detailed answer data is included in POST request.
*   **Status:** To Do ⏳

#### Step 6.3: Backend Processing & Storage (`submit_quiz_attempt`)

*   **Objective:** Process detailed answers and store mistake data in `attempt_details` (Req 6.c).
*   **Key Tasks:** Modify `submit_quiz_attempt` view in `multi_choice_quiz/views.py` to: extract detailed answers, compare with correct answers, generate mistake data JSON, save JSON to `QuizAttempt.attempt_details`.
*   **Deliverables:** Updated `multi_choice_quiz/views.py`.
*   **Verification Checklist:** `[ ]` **Unit Tests:** Add/run tests in `test_views.py` verifying `attempt_details` field is correctly populated based on submitted answers.
*   **Status:** To Do ⏳

#### Step 6.4: Phase 6 Verification

*   **Objective:** Ensure detailed mistake data is correctly captured and stored end-to-end.
*   **Key Tasks:** Create `src/multi_choice_quiz/tests/mistake_tracking/test_phase6_verification.py`. Add integration tests verifying DB state after submission.
*   **Deliverables:** New verification script `test_phase6_verification.py`.
*   **Verification Checklist:** `[ ]` Phase Verification Script Passes. `[ ]` All relevant unit/E2E tests pass.
*   **Status:** To Do ⏳

---
---

## Phase 7: Basic Mistake Review Interface (High Priority)

**Version:** 1.0
**Date:** 2025-05-06
**Phase Objective:** Allow the user to review the specific mistakes made in a past attempt.
**Related Requirements:** 7.a, 7.b, 7.c, 7.d
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 7.1: Create `attempt_mistake_review` View

*   **Objective:** Implement view to fetch attempt data and prepare context for review (Req 7.a, 7.b).
*   **Key Tasks:** Define view, fetch `QuizAttempt`, parse `attempt_details`, fetch relevant `Question` objects, prepare context. Map URL. Add `@login_required` and check user ownership of attempt.
*   **Deliverables:** New view function in `multi_choice_quiz/views.py`, updated `urls.py`.
*   **Verification Checklist:** `[ ]` **Unit Tests:** Add/run tests in `test_views.py` for the new view (context data, access control).
*   **Status:** To Do ⏳

#### Step 7.2: Create `mistake_review.html` Template

*   **Objective:** Create template to display mistake details (Req 7.c).
*   **Key Tasks:** Create `mistake_review.html` extending base. Loop through mistakes context, display question text, user answer, correct answer.
*   **Deliverables:** New `multi_choice_quiz/templates/multi_choice_quiz/mistake_review.html`.
*   **Verification Checklist:** `[ ]` **Manual E2E Check:** View the page for an attempt with mistakes, confirm correct display.
*   **Status:** To Do ⏳

#### Step 7.3: Add "Review Mistakes" Link to Profile

*   **Objective:** Add conditional link from profile history to review page (Req 7.d).
*   **Key Tasks:** Modify `profile.html` history loop to conditionally add a link to the `attempt_mistake_review` view if mistakes exist in `attempt.attempt_details`.
*   **Deliverables:** Updated `pages/templates/pages/profile.html`.
*   **Verification Checklist:** `[ ]` **Manual E2E Check:** View profile, confirm link appears only for attempts with mistakes and points to correct URL.
*   **Status:** To Do ⏳

#### Step 7.4: Phase 7 Verification

*   **Objective:** Verify the mistake review flow works end-to-end.
*   **Key Tasks:** Create `src/multi_choice_quiz/tests/mistake_tracking/test_phase7_verification.py`. Add integration tests.
*   **Deliverables:** New verification script `test_phase7_verification.py`.
*   **Verification Checklist:** `[ ]` Phase Verification Script Passes. `[ ]` All relevant unit/E2E tests pass.
*   **Status:** To Do ⏳

---
---

## Phase 8: Password Management

**Version:** 1.0
**Date:** 2025-05-06
**Phase Objective:** Implement standard Django password change and reset functionality.
**Related Requirements:** 8.a, 8.b, 8.c, 8.d
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 8.1: Create/Verify Password Mgmt Templates & Config

*   **Objective:** Ensure necessary templates exist and email backend is configured (Req 8.a-d).
*   **Key Tasks:** Create/verify templates (`password_*.html`, `password_reset_email.html`) extending base. Configure `EMAIL_BACKEND`.
*   **Deliverables:** Templates in `templates/registration/`, updated `settings.py`.
*   **Verification Checklist:** `[ ]` Run `core/tests/test_phase5_verification.py` (verifies templates/config). `[ ]` Manual E2E test of password reset flow using console email.
*   **Status:** To Do ⏳

#### Step 8.2: Phase 8 Verification

*   **Objective:** Confirm password management functionality is integrated.
*   **Key Tasks:** None beyond Step 8.1 verification.
*   **Deliverables:** Passing tests from Step 8.1.
*   **Verification Checklist:** `[ ]` Verification from Step 8.1 completed successfully.
*   **Status:** To Do ⏳

---
---

## Phase 9: Profile Enhancement - Dynamic Data & Quick Wins (Revised)

**Version:** 1.0
**Date:** 2025-05-06
**Phase Objective:** Populate profile with dynamic collections/stats, add basic profile editing.
**Related Requirements:** 9.a, 9.b, 9.c, 9.e (Revised), 9.f, 9.g, 9.i
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 9.1: Define & Migrate `QuizCollection` Model

*   **Objective:** Create DB model for quiz collections (Req 9.a).
*   **Key Tasks:** Define `QuizCollection` in `pages/models.py` (User FK, name, M2M quizzes). Generate/apply migrations.
*   **Deliverables:** Updated `pages/models.py`, migration file(s).
*   **Verification Checklist:** `[ ]` `check`, `migrate` pass. `[ ]` **Unit Test:** Add/run tests in `pages/tests/test_models.py`.
*   **Status:** To Do ⏳

#### Step 9.2: Implement `QuizCollection` Admin

*   **Objective:** Create basic Django Admin interface (Req 9.b).
*   **Key Tasks:** Register `QuizCollection` in `pages/admin.py`. Customize display/filtering if needed.
*   **Deliverables:** Updated `pages/admin.py`.
*   **Verification Checklist:** `[ ]` **Manual Check:** Access admin site, verify model is present and functional.
*   **Status:** To Do ⏳

#### Step 9.3: Update `profile_view` Logic (Stats & Collections)

*   **Objective:** Fetch collections data and calculate basic stats (Req 9.c).
*   **Key Tasks:** Modify `profile_view` in `pages/views.py` to fetch user's collections (prefetch quizzes), uncategorized quizzes, calculate stats (total attempts, avg score), add to context.
*   **Deliverables:** Updated `pages/views.py`.
*   **Verification Checklist:** `[ ]` **Unit Tests:** Add/run tests in `test_views.py` verifying correct data (collections, stats) in context.
*   **Status:** To Do ⏳

#### Step 9.4: Populate Profile Template (Stats & Collections)

*   **Objective:** Display dynamic stats and collections list (Req 9.e Rev). Evaluate HTMX/AJAX (Req 9.i).
*   **Key Tasks:** Modify `profile.html`. Replace placeholder stats with context variables. Implement collections display (looping through collections, quizzes) under "Collections" tab. Document HTMX/AJAX evaluation decision for tab loading.
*   **Deliverables:** Updated `pages/templates/pages/profile.html`.
*   **Verification Checklist:** `[ ]` **Manual E2E Check:** View profile, confirm dynamic stats and collections list render correctly. Check Collections tab loading behavior based on evaluation decision.
*   **Status:** To Do ⏳

#### Step 9.5: Implement Basic Edit Profile

*   **Objective:** Add simple profile editing (email) (Req 9.f, 9.g).
*   **Key Tasks:** Create form, view, URL, template for editing email. Update "Edit Profile" link on `profile.html`.
*   **Deliverables:** New `EditProfileForm`, `edit_profile_view`, URL pattern, `edit_profile.html`. Updated `profile.html`.
*   **Verification Checklist:** `[ ]` **Unit/E2E Tests:** Add/run tests for edit profile form, view, and E2E flow.
*   **Status:** To Do ⏳

#### Step 9.6: Phase 9 Verification

*   **Objective:** Verify dynamic data display and editing work.
*   **Key Tasks:** Create `src/pages/tests/user_profile/test_phase9_verification.py`. Add tests verifying dynamic stats/collections display and profile editing.
*   **Deliverables:** New verification script `test_phase9_verification.py`.
*   **Verification Checklist:** `[ ]` Phase Verification Script Passes. `[ ]` All relevant unit/E2E tests pass.
*   **Status:** To Do ⏳

---
---

## Phase 10: Collection Management & Import Integration

**Version:** 1.0
**Date:** 2025-05-06
**Phase Objective:** Allow users to create/manage collections; optionally enhance import script.
**Related Requirements:** 10.a, 10.b, 10.c, 10.d
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 10.1: Implement Collection Creation

*   **Objective:** Add ability to create collections from profile (Req 10.a). Evaluate HTMX/AJAX.
*   **Key Tasks:** Implement form, view, URL for creating collections. Add UI trigger (button/form) to profile. Document HTMX/AJAX decision.
*   **Deliverables:** Updated views, new form, updated templates.
*   **Verification Checklist:** `[ ]` **Unit/E2E Tests:** Add/run tests verifying creation flow.
*   **Status:** To Do ⏳

#### Step 10.2: Implement Moving Quizzes Between Collections

*   **Objective:** Add ability to move quizzes (Req 10.b). Evaluate HTMX/AJAX.
*   **Key Tasks:** Implement backend logic and UI controls (e.g., dropdown/modal) on profile page for moving quizzes. Document HTMX/AJAX decision.
*   **Deliverables:** Updated views, templates, possibly JS/HTMX snippets.
*   **Verification Checklist:** `[ ]` **Unit/E2E Tests:** Add/run tests verifying move functionality.
*   **Status:** To Do ⏳

#### Step 10.3: Implement Adding to Collection from Quiz Lists

*   **Objective:** Add controls to add quiz to existing collection (Req 10.d). Evaluate HTMX/AJAX.
*   **Key Tasks:** Add UI controls (e.g., button/modal) to `pages/quizzes.html` and `multi_choice_quiz/index.html`. Implement backend view/logic. Document HTMX/AJAX decision.
*   **Deliverables:** Updated templates, views, possibly JS/HTMX.
*   **Verification Checklist:** `[ ]` **Unit/E2E Tests:** Add/run tests verifying add-to-collection flow.
*   **Status:** To Do ⏳

#### Step 10.4: (Optional) Enhance Import Script

*   **Objective:** Allow assigning imported quizzes to a collection (Req 10.c).
*   **Key Tasks:** Modify `dir_import_chapter_quizzes.py` to accept optional user/collection args and assign imported quizzes.
*   **Deliverables:** Updated `dir_import_chapter_quizzes.py`.
*   **Verification Checklist:** `[ ]` **Script Tests:** Add/run tests for the import script verifying collection assignment.
*   **Status:** To Do ⏳

#### Step 10.5: Phase 10 Verification

*   **Objective:** Verify collection management works correctly.
*   **Key Tasks:** Create `src/pages/tests/collections_mgmt/test_phase10_verification.py` (or similar). Add integration tests.
*   **Deliverables:** New verification script.
*   **Verification Checklist:** `[ ]` Phase Verification Script Passes. `[ ]` All relevant unit/E2E tests pass.
*   **Status:** To Do ⏳

---
---

## Phase 11: Advanced Mistake Analysis & Quiz Suggestion (Future)

**Version:** 1.0
**Date:** 2025-05-06
**Phase Objective:** Analyze mistakes and suggest quizzes/topics for review.
**Related Requirements:** 11.a, 11.b, 11.c, 11.d
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 11.1: Backend Analysis Logic

*   **Objective:** Develop logic to query and analyze `attempt_details` (Req 11.a, 11.b).
*   **Key Tasks:** Implement functions/methods to aggregate mistake data across attempts.
*   **Deliverables:** New analysis utilities/methods.
*   **Verification Checklist:** `[ ]` Unit tests for analysis logic.
*   **Status:** To Do ⏳

#### Step 11.2: Suggestion Generation Logic

*   **Objective:** Implement logic to suggest quizzes/topics based on analysis (Req 11.c).
*   **Key Tasks:** Implement functions/methods to identify relevant quizzes/topics based on identified weaknesses.
*   **Deliverables:** New suggestion utilities/methods.
*   **Verification Checklist:** `[ ]` Unit tests for suggestion logic.
*   **Status:** To Do ⏳

#### Step 11.3: Frontend Presentation

*   **Objective:** Design and implement UI for suggestions (Req 11.d).
*   **Key Tasks:** Update profile view/template or create new dashboard to display suggestions.
*   **Deliverables:** Updated views/templates.
*   **Verification Checklist:** `[ ]` E2E tests / Manual check of suggestions display.
*   **Status:** To Do ⏳

#### Step 11.4: Phase 11 Verification

*   **Objective:** Verify analysis and suggestions work correctly end-to-end.
*   **Key Tasks:** Create dedicated verification script. Add integration tests.
*   **Deliverables:** New verification script.
*   **Verification Checklist:** `[ ]` Phase Verification Script Passes. `[ ]` All relevant unit/E2E tests pass.
*   **Status:** To Do ⏳

---
---

PS: Profile_and_CoreFeatures_Iteration_Guide.md often you'll be hearing me calling it the Iteration Guide.