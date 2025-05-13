# Iteration Guide: Profile & Core Features (Phases 5-13)

**Project:** QuizMaster
**Date Updated:** 2025-05-12
**Corresponding Requirements Doc:** `Project_Requirements.md` v2.6

## Overview

This guide outlines the development steps for enhancing the user profile and implementing core features like mistake tracking, review, and collection management, corresponding to Phases 5 through 13 of the project requirements.

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
*   **Status:** Completed in Session 5. Verification script: `src/multi_choice_quiz/tests/mistake_tracking/test_phase6_verification.py`. Branch `feature/phase6-mistake-capture` merged to main.
*   **Key Outcomes:**
    *   Frontend (`app.js`) collects detailed answer map (`{questionId: selectedOptionIndex}`).
    *   Frontend sends this map as `attempt_details` in the submission payload.
    *   Backend (`submit_quiz_attempt`) processes received details, compares with correct answers, and stores only the mistakes in the `QuizAttempt.attempt_details` JSONField.
    *   Verification tests confirm correct storage and handling of edge cases (perfect score, missing details).

### Phase 7: Basic Mistake Review Interface (High Priority) - COMPLETE

*   **Objective:** Allow the user to review the specific mistakes made in a past attempt.
*   **Status:** Completed in Session 6. Verification script: `src/multi_choice_quiz/tests/mistake_tracking/test_phase7_verification.py`. Branch `feature/phase7-mistake-review` merged to main.
*   **Key Outcomes:**
    *   `attempt_mistake_review` view implemented with ownership checks and data preparation.
    *   `mistake_review.html` template created to display mistakes.
    *   Conditional "Review Mistakes" link added to profile history.
    *   Verification script confirms end-to-end flow.

### Phase 8: Password Management - COMPLETE

*   **Objective:** Implement standard Django password change and reset functionality.
*   **Status:** Completed in Session 7. Verification script: `src/pages/tests/auth/test_phase8_verification.py`. Changes merged to main.
*   **Key Outcomes:**
    *   All necessary password management templates (`password_*.html`, `password_reset_email.html`) verified.
    *   `EMAIL_BACKEND` confirmed for console output.
    *   Password change and reset flows manually E2E tested and confirmed functional.
    *   Verification script for URL resolution and template rendering passed.

### Phase 9: Collection Models, Profile Population & Public Browsing (Revised) - COMPLETE

*   **Objective:** Implement models for `SystemCategory` and `UserCollection`. Populate profile with dynamic stats/collections. Update public quiz browsing. Implement basic profile editing.
*   **Status:** Completed in Session 9. Verification script: `src/pages/tests/user_profile/test_phase9_verification.py`. Branch `feature/phase9-collections-profile` merged to main.
*   **Key Outcomes:**
    *   `SystemCategory` and `UserCollection` models defined and migrated. Admin interfaces implemented.
    *   `profile_view` updated to fetch/calculate dynamic data; `profile.html` populated.
    *   `quizzes` view and template updated for `SystemCategory` filtering.
    *   `home` view and template updated for featured `SystemCategory` instances.
    *   Basic Edit Profile (email) functionality implemented and linked.
    *   HTMX/AJAX evaluation for Collections tab documented (deferred).

### Phase 10: User Collection Management & Import Integration (Revised) - COMPLETE

*   **Objective:** Allow users to create/manage private `UserCollection`s. Implement UI for adding global quizzes to private collections. Implement `SystemCategory` assignment during import.
*   **Status:** Completed in Session 11 (Req 10.c completed in Session 13 as part of refactoring). Verification script: `src/pages/tests/collections_mgmt/test_phase10_verification.py`. Branch `feature/phase10-collection-mgmt` merged.
*   **Key Outcomes:**
    *   `UserCollection` creation implemented (form, view, URL, UI on profile).
    *   Quiz removal from `UserCollection` (from profile) implemented.
    *   Adding quizzes to `UserCollection` from public lists implemented (select collection page, add view).
    *   UX Decisions for collection management (full page reloads) documented.
    *   Req 10.c (SystemCategory in import scripts) completed.

### Performance Refactoring: Bulk Create for Imports - COMPLETE

*   **Objective:** Refactor quiz import logic to use `bulk_create` for `Question` and `Option` objects to improve performance, especially with PostgreSQL.
*   **Status:** Completed in Session 16. Branch `feature/refactor-bulk-import` merged to main.
*   **Key Outcomes:**
    *   `quiz_bank_to_models` in `multi_choice_quiz/utils.py` refactored.
    *   All relevant unit tests for import scripts and utilities passed, confirming functional correctness.
    *   Qualitative performance verification (Step PERF.2) discussed; improvement expected.

---
---

## Phase 11: Post-Phase 10 UI/UX Tweaking (NEW)

**Version:** 1.0
**Date:** 2025-05-12
**Phase Objective:** Enhance the user interface and user experience based on observations and priorities identified after the completion of core collection management features. These are primarily template and view modifications without DB schema changes.
**Related Requirements:** 11.a, 11.b, 11.c, 11.d, 11.e (from Project_Requirements.md v2.6)
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 11.1: Navbar Enhancement - Profile Link Text & Avatar Placeholder

*   **Objective:** Clean up navbar and improve visual identity (Req 11.a; UI/UX Ref #1, #7).
*   **Key Tasks:**
    1.  Modify `pages/templates/pages/base.html`:
        *   Change the "Profile (username)" link text to just display the username (e.g., `({{ user.username }})`) or an alternative concise format.
        *   Add markup for a circular avatar placeholder (e.g., a `div` with user's initial) next to the username link. Apply Tailwind CSS for styling.
*   **Deliverables:** Updated `pages/templates/pages/base.html`.
*   **Verification Checklist:**
    *   `[ ]` **Manual E2E Check:** Verify navbar shows concise username and avatar placeholder for logged-in users on desktop and mobile.
    *   `[ ]` **Playwright (Optional):** Update snapshot tests or add specific locators if existing E2E tests for navigation are affected.
*   **Status:** To Do ⏳

#### Step 11.2: Fix Quiz Collection Redirection

*   **Objective:** Improve user flow when adding quizzes to collections by redirecting to the previous page (Req 11.b; UI/UX Ref #3).
*   **Key Tasks:**
    1.  Modify `pages/views.py::add_quiz_to_selected_collection_view`:
        *   Update the view to accept a `next` URL parameter.
        *   If `next` is provided and safe, redirect to it. Otherwise, fall back to `pages:profile`.
    2.  Modify `pages/templates/pages/select_collection_for_quiz.html`:
        *   Ensure the "Add to this Collection" forms pass the current page's path (or a desired `next` path) as a hidden input or query parameter to `add_quiz_to_selected_collection_view`.
    3.  Modify `pages/templates/pages/quizzes.html` and `pages/templates/pages/home.html`:
        *   When generating the link to `select_collection_for_quiz_view`, include the current page's path as a `next` query parameter (e.g., `?next={{ request.get_full_path|urlencode }}`).
*   **Deliverables:** Updated `pages/views.py`, `select_collection_for_quiz.html`, `quizzes.html`, `home.html`.
*   **Verification Checklist:**
    *   `[ ]` **Unit Tests:** For `add_quiz_to_selected_collection_view` to check `next` parameter handling.
    *   `[ ]` **Manual E2E Check:**
        *   Add quiz from `/quizzes/` -> verify redirect back to `/quizzes/` (with filters if any).
        *   Add quiz from `/` (homepage) -> verify redirect back to `/`.
        *   If `next` is invalid/missing, verify redirect to profile.
*   **Status:** To Do ⏳

#### Step 11.3: Reorder Attempted Quizzes & Refine Featured Quizzes

*   **Objective:** Improve content discovery by reordering attempted quizzes and refining featured quiz logic (Req 11.c; UI/UX Ref #4, #8).
*   **Key Tasks:**
    1.  Modify `pages/views.py::quizzes` view:
        *   If user is authenticated, fetch IDs of quizzes they've attempted.
        *   Annotate the main quiz queryset with a boolean indicating if it's been attempted.
        *   Adjust `order_by` to sort by `attempted` (False first), then by existing criteria (e.g., `-created_at`).
    2.  Modify `pages/views.py::home` view (for featured quizzes):
        *   If user is authenticated, fetch IDs of quizzes they've attempted.
        *   Exclude attempted quizzes from the initial pool for featured quizzes, or heavily down-rank them. Ensure enough non-attempted quizzes are available to feature.
*   **Deliverables:** Updated `pages/views.py`.
*   **Verification Checklist:**
    *   `[ ]` **Unit Tests:** For view logic changes verifying correct ordering and exclusion.
    *   `[ ]` **Manual E2E Check:**
        *   As a logged-in user, take a quiz. Verify it moves to the end of the list on `/quizzes/`.
        *   Verify featured quizzes on homepage prioritize unattempted ones.
*   **Status:** To Do ⏳

#### Step 11.4: Make Profile Collections Collapsible/Expandable

*   **Objective:** Improve organization on the profile page for users with many collections (Req 11.d; UI/UX Ref #4).
*   **Key Tasks:**
    1.  Modify `pages/templates/pages/profile.html`:
        *   For each collection in the "Collections" tab, add Alpine.js `x-data="{ open: false }"`.
        *   Add a button/clickable header to toggle `open`.
        *   Wrap the list of quizzes within that collection in an element with `x-show="open"`.
        *   Style the toggle and collapsed/expanded states.
*   **Deliverables:** Updated `pages/templates/pages/profile.html`.
*   **Verification Checklist:**
    *   `[ ]` **Manual E2E Check:** Verify collections are collapsible/expandable. Test with multiple collections and quizzes.
    *   `[ ]` **Playwright (Optional):** Add tests to `test_profile_responsive_layout` in `pages/tests/test_responsive.py` to check collapse/expand functionality.
*   **Status:** To Do ⏳

#### Step 11.5: Profile Page Polish (Stat Placeholders & Attempt Counts)

*   **Objective:** Enhance profile page clarity and information (Req 11.e; UI/UX Ref #8, #2).
*   **Key Tasks:**
    1.  Modify `pages/templates/pages/profile.html`:
        *   Update placeholder text for "Strongest Topic" and "Needs Review" stats (e.g., "Analysis Coming Soon!").
    2.  Modify `pages/views.py::profile_view`:
        *   Annotate `QuizAttempt` records (or perform separate queries) to count attempts per unique quiz for the current user.
        *   Pass this attempt count data to the template context.
    3.  Modify `pages/templates/pages/profile.html`:
        *   In the "Quiz History" tab, display the attempt count next to each quiz title (e.g., "History Quiz 1 (Taken 3 times)").
*   **Deliverables:** Updated `pages/views.py`, `pages/templates/pages/profile.html`.
*   **Verification Checklist:**
    *   `[ ]` **Unit Tests:** For `profile_view` to verify new context data (attempt counts).
    *   `[ ]` **Manual E2E Check:** Verify updated stat placeholders and attempt counts in history.
*   **Status:** To Do ⏳

#### Step 11.6: Phase 11 Verification

*   **Objective:** Verify all UI/UX tweaks are implemented correctly and improve usability.
*   **Key Tasks:** Create/update verification scripts or perform targeted E2E/manual checks for each implemented step.
*   **Deliverables:** Potentially updated test scripts (`test_responsive.py`, `test_templates.py`, new phase-specific verification if needed).
*   **Verification Checklist:** `[ ]` All targeted UI/UX improvements confirmed via tests or manual checks.
*   **Status:** To Do ⏳

---
---

## Phase 12: Advanced Mistake Analysis & Quiz Suggestion (Future) (Previously Phase 11)

**Version:** 1.0
**Date:** 2025-05-12 (Renumbered)
**Phase Objective:** Analyze mistakes and suggest quizzes/topics for review.
**Related Requirements:** 12.a, 12.b, 12.c, 12.d (from Project_Requirements.md v2.6)
**Phase Status:** Planned 📝

---

### Implementation Steps

#### Step 12.1: Backend Analysis Logic (Previously 11.1)

*   **Objective:** Develop logic to query and analyze `attempt_details` (Req 12.a, 12.b).
*   **Key Tasks:** Implement functions/methods to aggregate mistake data.
*   **Deliverables:** New analysis utilities/methods.
*   **Verification Checklist:** `[ ]` Unit tests for analysis logic.
*   **Status:** To Do ⏳

#### Step 12.2: Suggestion Generation Logic (Previously 11.2)

*   **Objective:** Implement logic to suggest quizzes/categories based on analysis (Req 12.c).
*   **Key Tasks:** Implement functions/methods to identify relevant quizzes/`SystemCategory` instances.
*   **Deliverables:** New suggestion utilities/methods.
*   **Verification Checklist:** `[ ]` Unit tests for suggestion logic.
*   **Status:** To Do ⏳

#### Step 12.3: Frontend Presentation (Previously 11.3)

*   **Objective:** Design and implement UI for suggestions (Req 12.d).
*   **Key Tasks:** Update profile view/template or create new dashboard.
*   **Deliverables:** Updated views/templates.
*   **Verification Checklist:** `[ ]` E2E tests / Manual check of suggestions display.
*   **Status:** To Do ⏳

#### Step 12.4: Phase 12 Verification (Previously 11.4)

*   **Objective:** Verify analysis and suggestions work correctly end-to-end.
*   **Key Tasks:** Create dedicated verification script. Add integration tests.
*   **Deliverables:** New verification script.
*   **Verification Checklist:** `[ ]` Phase Verification Script Passes. `[ ]` All relevant unit/E2E tests pass.
*   **Status:** To Do ⏳

---