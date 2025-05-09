# Iteration Guide: Profile & Core Features (Phases 5-11)

**Project:** QuizMaster
**Date Updated:** 2025-05-09
**Corresponding Requirements Doc:** `Project_Requirements.md` v2.5

## Overview

This guide outlines the development steps for enhancing the user profile and implementing core features like mistake tracking, review, and collection management, corresponding to Phases 5 through 11 of the project requirements.

## Completed Phases

### Phase 5: Foundational Attempt Tracking & Profile Page Structure (Revised) - COMPLETE

*   **Objective:** Store overall quiz attempt results and establish the final, responsive profile page structure based on Mockup 1 (Stats Above Tabs), including the initial display of quiz history.
*   **Status:** Completed in Session 4. Verification script: `src/pages/tests/user_profile/test_phase5_verification.py`. Branch `feature/phase5-profile-foundation` merged to main.
*   **Key Outcomes:**
    *   `QuizAttempt` model includes `attempt_details` JSONField.
    *   `submit_quiz_attempt` endpoint saves basic attempt data.
    *   Frontend sends basic results.
    *   `profile_view` requires login and fetches attempt history.
    *   `profile.html` structure matches Mockup 1 (Stats above Tabs for History/Collections). History tab displays attempts.
    *   Profile page is responsive and verified.

### Phase 6: Detailed Mistake Data Capture - COMPLETE

*   **Objective:** Capture _exactly_ which questions were answered incorrectly during a quiz attempt and store this detailed data.
*   **Status:** Completed in Session 5. Verification script: `src/multi_choice_quiz/tests/mistake_tracking/test_phase6_verification.py`. Branch `feature/phase6-mistake-capture` ready for merge.
*   **Key Outcomes:**
    *   Frontend (`app.js`) collects detailed answer map (`{questionId: selectedOptionIndex}`).
    *   Frontend sends this map as `attempt_details` in the submission payload.
    *   Backend (`submit_quiz_attempt`) processes received details, compares with correct answers, and stores only the mistakes in the `QuizAttempt.attempt_details` JSONField.
    *   Verification tests confirm correct storage and handling of edge cases (perfect score, missing details).

## Planned Phases

### Phase 7: Basic Mistake Review Interface (High Priority)

**Version:** 1.0
**Date:** 2025-05-09
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
**Date:** 2025-05-09
**Phase Objective:** Implement standard Django password change and reset functionality.
**Related Requirements:** 8.a, 8.b, 8.c, 8.d
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 8.1: Create/Verify Password Mgmt Templates & Config

*   **Objective:** Ensure necessary templates exist and email backend is configured (Req 8.a-d).
*   **Key Tasks:** Create/verify templates (`password_*.html`, `password_reset_email.html`) extending base. Configure `EMAIL_BACKEND`.
*   **Deliverables:** Templates in `templates/registration/`, updated `settings.py`.
*   **Verification Checklist:** `[ ]` Run relevant verification tests (e.g., template rendering tests if created, potentially from a `test_phase8_verification.py`). `[ ]` Manual E2E test of password reset flow using console email.
*   **Status:** To Do ⏳

#### Step 8.2: Phase 8 Verification

*   **Objective:** Confirm password management functionality is integrated.
*   **Key Tasks:** None beyond Step 8.1 verification.
*   **Deliverables:** Passing tests from Step 8.1.
*   **Verification Checklist:** `[ ]` Verification from Step 8.1 completed successfully.
*   **Status:** To Do ⏳

---
---

## Phase 9: Collection Models, Profile Population & Public Browsing (Revised)

**Version:** 1.0
**Date:** 2025-05-09
**Phase Objective:** Implement models for both **public `SystemCategory`** (admin-managed, for browsing) and **private `UserCollection`** (user-managed). Populate the profile page dynamically with user stats and `UserCollection` data. Update public quiz browsing to use `SystemCategory`. Implement basic profile editing.
**Related Requirements:** 9.a, 9.b, 9.c, 9.d, 9.e, 9.f, 9.g, 9.h, 9.i, 9.j
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 9.1: Define & Migrate Collection Models

*   **Objective:** Create DB models for `SystemCategory` and `UserCollection` (Req 9.a).
*   **Key Tasks:** Define models in `pages/models.py` (or dedicated app). Generate/apply migrations.
*   **Deliverables:** Updated `models.py`, migration file(s).
*   **Verification Checklist:** `[ ]` `check`, `migrate` pass. `[ ]` **Unit Test:** Add/run tests for new models.
*   **Status:** To Do ⏳

#### Step 9.2: Implement Collection Admin Interfaces

*   **Objective:** Create Django Admin interfaces for both models (Req 9.b).
*   **Key Tasks:** Register models in `admin.py`. Customize if needed.
*   **Deliverables:** Updated `admin.py`.
*   **Verification Checklist:** `[ ]` **Manual Check:** Access admin site, verify models are present and functional.
*   **Status:** To Do ⏳

#### Step 9.3: Update `profile_view` Logic (Stats & `UserCollection`)

*   **Objective:** Fetch `UserCollection` data and calculate stats for profile (Req 9.c).
*   **Key Tasks:** Modify `profile_view` to fetch user's `UserCollection`s (prefetch quizzes), uncategorized quizzes, calculate stats (total attempts, avg score), add to context.
*   **Deliverables:** Updated `pages/views.py`.
*   **Verification Checklist:** `[ ]` **Unit Tests:** Add/run tests verifying correct data in context.
*   **Status:** To Do ⏳

#### Step 9.4: Populate Profile Template (Stats & `UserCollection`)

*   **Objective:** Display dynamic stats and `UserCollection` list (Req 9.d). Evaluate HTMX/AJAX (Req 9.j).
*   **Key Tasks:** Modify `profile.html`. Replace placeholder stats. Implement `UserCollection` display under "Collections" tab. Document HTMX/AJAX evaluation decision for tab loading.
*   **Deliverables:** Updated `pages/templates/pages/profile.html`.
*   **Verification Checklist:** `[ ]` **Manual E2E Check:** View profile, confirm dynamic stats and collections list render correctly. Check Collections tab loading behavior.
*   **Status:** To Do ⏳

#### Step 9.5: Update Public Browsing (`quizzes` View & Template)

*   **Objective:** Use `SystemCategory` for public quiz filtering (Req 9.e, 9.f).
*   **Key Tasks:** Update `quizzes` view to fetch/filter by `SystemCategory`. Update template to show `SystemCategory` filters.
*   **Deliverables:** Updated `pages/views.py`, `pages/templates/pages/quizzes.html`.
*   **Verification Checklist:** `[ ]` **Unit/E2E Tests:** Add/run tests verifying category filtering works.
*   **Status:** To Do ⏳

#### Step 9.6: Update Homepage View (Optional)

*   **Objective:** Optionally display featured `SystemCategory` instances (Req 9.g).
*   **Key Tasks:** Modify `home` view and template if implementing this feature.
*   **Deliverables:** Updated `pages/views.py`, `pages/templates/pages/home.html` (if changed).
*   **Verification Checklist:** `[ ]` **Manual/E2E Check:** Verify homepage displays categories correctly (if implemented).
*   **Status:** To Do ⏳

#### Step 9.7: Implement Basic Edit Profile

*   **Objective:** Add simple profile editing (email) (Req 9.h, 9.i).
*   **Key Tasks:** Create form, view, URL, template for editing email. Update "Edit Profile" link on `profile.html`.
*   **Deliverables:** New `EditProfileForm`, `edit_profile_view`, URL pattern, `edit_profile.html`. Updated `profile.html`.
*   **Verification Checklist:** `[ ]` **Unit/E2E Tests:** Add/run tests for edit profile flow.
*   **Status:** To Do ⏳

#### Step 9.8: Phase 9 Verification

*   **Objective:** Verify dynamic data display, category filtering, and editing work.
*   **Key Tasks:** Create `src/pages/tests/user_profile/test_phase9_verification.py`. Add tests verifying dynamic stats/collections display, category filtering, and profile editing.
*   **Deliverables:** New verification script `test_phase9_verification.py`.
*   **Verification Checklist:** `[ ]` Phase Verification Script Passes. `[ ]` All relevant unit/E2E tests pass.
*   **Status:** To Do ⏳

---
---
---
---

## Phase 10: User Collection Management & Import Integration (Revised)

**Version:** 1.0
**Date:** 2025-05-10
**Phase Objective:** Allow users to create/manage their private `UserCollection`s. Implement UI for adding global quizzes to private collections. (Req 10.c, enhancing import scripts, is deferred to post-refactoring).
**Related Requirements:** 10.a, 10.b, 10.d
**Phase Status:** COMPLETE ✅ (Step 10.4/Req 10.c Deferred)

---

### Implementation Steps

#### Step 10.1: Implement `UserCollection` Creation

*   **Objective:** Add ability to create `UserCollection`s from profile (Req 10.a). Evaluate HTMX/AJAX.
*   **Key Tasks:** Implement form, view, URL for creating collections. Add UI trigger to profile. **UX Decision: Full page reload implemented.**
*   **Deliverables:** Updated views, new form, updated templates.
*   **Verification Checklist:** `[✅]` **Unit/E2E Tests:** Add/run tests verifying creation flow. (Covered by Phase 10 Verification Script)
*   **Status:** Done ✅

#### Step 10.2: Implement Managing Quizzes in `UserCollection`s (Removal from Profile)

*   **Objective:** Add ability to remove quizzes from `UserCollection`s via the profile page (Req 10.b). Evaluate HTMX/AJAX.
*   **Key Tasks:** Implement backend logic and UI controls (form with POST button) on profile page for quiz removal. **UX Decision: Full page reload implemented.**
*   **Deliverables:** Updated views, templates.
*   **Verification Checklist:** `[✅]` **Unit/E2E Tests:** Add/run tests verifying remove functionality. (Covered by Phase 10 Verification Script)
*   **Status:** Done ✅

#### Step 10.3: Implement Adding to `UserCollection` from Quiz Lists

*   **Objective:** Add controls on public pages to add quiz to existing `UserCollection` (Req 10.d). Evaluate HTMX/AJAX.
*   **Key Tasks:** Add UI controls to `pages/quizzes.html` and homepage. Implement backend views/logic for selecting a collection and adding the quiz. **UX Decision: Full page redirect flow implemented.**
*   **Deliverables:** Updated templates, views.
*   **Verification Checklist:** `[✅]` **Unit/E2E Tests:** Add/run tests verifying add-to-collection flow from public pages. (Covered by Phase 10 Verification Script)
*   **Status:** Done ✅

#### Step 10.4: (Optional) Enhance Import Script for `SystemCategory`

*   **Objective:** Allow assigning imported quizzes to `SystemCategory` (Req 10.c).
*   **Key Tasks:** Modify `dir_import_chapter_quizzes.py` to accept optional category args and assign imported quizzes to `SystemCategory`.
*   **Deliverables:** Updated `dir_import_chapter_quizzes.py`.
*   **Verification Checklist:** `[ ]` **Script Tests:** Add/run tests for the import script verifying category assignment.
*   **Status:** Deferred ⏳ *(To be addressed after import script refactoring)*

#### Step 10.5: Phase 10 Verification

*   **Objective:** Verify collection management works correctly.
*   **Key Tasks:** Create `src/pages/tests/collections_mgmt/test_phase10_verification.py`. Add integration tests covering creation, removal from profile, and adding from public lists.
*   **Deliverables:** New verification script `test_phase10_verification.py`.
*   **Verification Checklist:** `[✅]` Phase Verification Script Passes. `[✅]` All relevant unit/E2E tests pass.
*   **Status:** Done ✅

---
---

## Phase 11: Advanced Mistake Analysis & Quiz Suggestion (Future)

**Version:** 1.0
**Date:** 2025-05-09
**Phase Objective:** Analyze mistakes and suggest quizzes/topics for review.
**Related Requirements:** 11.a, 11.b, 11.c, 11.d
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 11.1: Backend Analysis Logic

*   **Objective:** Develop logic to query and analyze `attempt_details` (Req 11.a, 11.b).
*   **Key Tasks:** Implement functions/methods to aggregate mistake data.
*   **Deliverables:** New analysis utilities/methods.
*   **Verification Checklist:** `[ ]` Unit tests for analysis logic.
*   **Status:** To Do ⏳

#### Step 11.2: Suggestion Generation Logic

*   **Objective:** Implement logic to suggest quizzes/categories based on analysis (Req 11.c).
*   **Key Tasks:** Implement functions/methods to identify relevant quizzes/`SystemCategory` instances.
*   **Deliverables:** New suggestion utilities/methods.
*   **Verification Checklist:** `[ ]` Unit tests for suggestion logic.
*   **Status:** To Do ⏳

#### Step 11.3: Frontend Presentation

*   **Objective:** Design and implement UI for suggestions (Req 11.d).
*   **Key Tasks:** Update profile view/template or create new dashboard.
*   **Deliverables:** Updated views/templates.
*   **Verification Checklist:** `[ ]` E2E tests / Manual check of suggestions display.
*   **Status:** To Do ⏳

#### Step 11.4: Phase 11 Verification

*   **Objective:** Verify analysis and suggestions work correctly end-to-end.
*   **Key Tasks:** Create dedicated verification script. Add integration tests.
*   **Deliverables:** New verification script.
*   **Verification Checklist:** `[ ]` Phase Verification Script Passes. `[ ]` All relevant unit/E2E tests pass.
*   **Status:** To Do ⏳