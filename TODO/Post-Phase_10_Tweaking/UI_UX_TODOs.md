# UI/UX Refinement Plan

**Date:** 2025-05-10

This document outlines planned UI/UX improvements for the QuizMaster application. These tasks primarily involve changes to templates and views, without requiring database schema modifications. They will be tackled as part of the new **Phase 11: UI/UX Refinements**.

## Categorization & Ranking

Tasks are categorized by priority. Within each priority, they are roughly ordered by estimated effort (lowest to highest), considering their potential impact on user experience.

---

### ✅ High Priority

These items significantly improve core usability or address prominent visual/functional quirks.

1.  **Navbar Enhancement: Profile Link Text**

    - **Description:** If the user is logged in, remove the word "Profile" from the "Profile (username)" link in the navbar (e.g., just show "(username)" or "akbar").
    - **Effort:** Very Low
    - **Impact:** Medium (Cleaner navbar, more space)
    - **Files Likely Affected:** `pages/templates/pages/base.html`
    - **TODO Ref:** #1 (partial)

2.  **Navbar Enhancement: Avatar Placeholder**

    - **Description:** Add a placeholder for an avatar (e.g., user's initial in a circle, or a generic icon) next to the username in the navbar.
    - **Effort:** Low
    - **Impact:** Medium (Improved visual identity)
    - **Files Likely Affected:** `pages/templates/pages/base.html` (template + Tailwind CSS)
    - **TODO Ref:** #7 (partial)

3.  **Fix Quiz Collection Redirection**

    - **Description:** When a quiz is added to a collection, redirect the user back to the page they were on (e.g., `/quizzes/` or quiz detail page), not to their profile.
    - **Effort:** Medium
    - **Impact:** High (Reduced context switching, better flow)
    - **Files Likely Affected:** `pages/views.py` (view logic), `pages/templates/pages/quizzes.html`, `pages/templates/pages/home.html` (to pass `next` URL).
    - **TODO Ref:** #3

4.  **Reorder Taken Quizzes in Lists**

    - **Description:** On public quiz listing pages (e.g., `/quizzes/`, homepage featured quizzes), quizzes already attempted by the logged-in user should appear at the end of the list.
    - **Effort:** Medium
    - **Impact:** High (Better discovery of new content for returning users)
    - **Files Likely Affected:** `pages/views.py` (logic in `quizzes` and `home` views).
    - **TODO Ref:** #1

5.  **Make Profile Collections Collapsible/Expandable**
    - **Description:** In the "Collections" tab on the profile page, make each individual collection item (which lists its quizzes) collapsible and expandable.
    - **Effort:** Medium-High
    - **Impact:** High (Improved organization and scannability for users with many collections or many quizzes within collections)
    - **Files Likely Affected:** `pages/templates/pages/profile.html` (Alpine.js logic and structure).
    - **TODO Ref:** #4 (from your verbal update)

---

### 🟠 Medium Priority

These items enhance the user experience and provide more clarity or useful information.

6.  **Implement "Strongest Topic" / "Needs Review" Placeholders on Profile**

    - **Description:** Update the placeholder text (`--`) for "Strongest Topic" and "Needs Review" on the profile page to something more informative like "Analysis Coming Soon!" or "More data needed."
    - **Effort:** Very Low
    - **Impact:** Low-Medium (Manages expectations, looks more polished than `--`)
    - **Files Likely Affected:** `pages/templates/pages/profile.html`
    - **TODO Ref:** #8 / #1 (from your verbal update)

7.  **Track Quiz Attempts per Quiz on Profile**

    - **Description:** In the user's "Quiz History" tab on the profile page, display how many times each listed quiz has been taken by that user.
    - **Effort:** Medium
    - **Impact:** Medium (Provides useful context about user's engagement with specific quizzes)
    - **Files Likely Affected:** `pages/views.py` (`profile_view` logic), `pages/templates/pages/profile.html`.
    - **TODO Ref:** #2

8.  **Improve Featured Quizzes Logic (Avoid Attempted)**
    - **Description:** The "Featured Quizzes" section on the homepage should prioritize displaying quizzes that the logged-in user has not yet attempted.
    - **Effort:** Medium
    - **Impact:** Medium (Improved discovery of new content for returning users, complements item #4)
    - **Files Likely Affected:** `pages/views.py` (`home` view logic).
    - **TODO Ref:** #4

---

### ⚪ Low Priority / Exploratory

These items are valuable but can be addressed after higher priority refinements, or require more significant effort/design.

9.  **Deleting Quiz from Collection - Use Modal**

    - **Description:** When removing a quiz from a collection (on the profile page), use a styled modal confirmation dialog instead of the default browser `confirm()` prompt.
    - **Effort:** Medium
    - **Impact:** Low-Medium (More polished UX, consistent styling)
    - **Files Likely Affected:** `pages/templates/pages/profile.html` (Alpine.js for modal, form submission logic might need slight adjustment if modal handles submit).
    - **TODO Ref:** #9 (from your verbal update)

10. **Consider Search Utility for Quizzes**

    - **Description:** Implement a search bar/functionality to allow users to search for quizzes by title or keywords.
    - **Effort:** Medium-High
    - **Impact:** Medium (Very useful for larger quiz libraries)
    - **Files Likely Affected:** `pages/views.py` (new search view/updated `quizzes` view), new form, template updates.
    - **TODO Ref:** #8

11. **Enhance Collections Visibility on Home Page**

    - **Description:** Make user's private collections (if any) more prominent on the homepage for logged-in users.
    - **Effort:** Medium
    - **Impact:** Medium (Personalizes homepage, quick access)
    - **Files Likely Affected:** `pages/views.py` (`home` view logic), `pages/templates/pages/home.html`.
    - **TODO Ref:** #5

12. **Visualize Time Spent on Quizzes per Day (Exploratory)**
    - **Description:** Explore adding a simple visualization (e.g., date-based heatmap) to show daily quiz activity. Could be on the profile page or a dedicated "Activity" page.
    - **Effort:** High
    - **Impact:** Medium (Potentially engaging for users, promotes reflection)
    - **Files Likely Affected:** Likely `pages/views.py`, new template, potentially JS for visualization. _This might eventually require DB changes to store more granular attempt timing if not already available._ For now, assume we use existing `QuizAttempt` timestamps.
    - **TODO Ref:** #6

---
