**Overview: User Stats & Profile Features**

**I. Current State (Release 06):**

*   **Models:**
    *   `User`: Standard Django user model (username, email, password, date joined, etc.).
    *   `QuizAttempt`: Stores a *summary* of each completed quiz attempt (link to `User`, link to `Quiz`, final score, total questions, percentage, start/end times).
*   **Profile Page (`pages/profile.html`):**
    *   Displays basic user info (username, email, initial, member since) - **Dynamic**.
    *   Displays four "Stats Cards" (Quizzes Taken, Avg Score, Topics Explored, Perfect Scores) - **Currently Placeholders (Hardcoded)**.
    *   Has tabs for "Quiz History", "Favorites", "Created Quizzes".
    *   Displays the "Quiz History" list dynamically based on the logged-in user's `QuizAttempt` records - **Dynamic & Working**.
    *   "Favorites" and "Created Quizzes" tabs show placeholder content - **Placeholders**.
    *   "Edit Profile" button is present but non-functional (placeholder).
*   **Data Capture:** The frontend (`app.js`) calculates the score/percentage and sends this *summary* data to the backend (`submit_quiz_attempt`), which saves it as a `QuizAttempt`.

**II. What's Missing (for desired features):**

*   **Database Granularity for Mistakes:** There's no record of *which specific questions* a user answered correctly or incorrectly within a `QuizAttempt`.
*   **Database Relationship for Favorites:** No way to link a `User` to their favorite `Quiz` instances.
*   **Database Link for Quiz Creators:** No field on the `Quiz` model to indicate which `User` created it.
*   **Mechanism for Storing Custom Profile Info:** No dedicated `Profile` model or extended `User` model fields for things like bios, avatars, etc. (beyond basic auth fields).

**III. Roadmap for Enhancements:**

Here’s a phased approach, starting with the easiest wins:

**Phase 1: Implement Dynamic Stats Cards (No Model Changes Required)**

*   **Goal:** Replace the placeholder numbers in the four stats cards on the profile page with real data calculated from existing `QuizAttempt` records.
*   **Achievability:** **Easily Achievable.** Requires only backend view logic and template modifications.
*   **Steps:**
    1.  **Modify `pages.views.profile_view`:**
        *   Query the `QuizAttempt` model, filtering by `request.user`.
        *   Calculate:
            *   `quizzes_taken_count = user_attempts.count()`
            *   `average_score = user_attempts.aggregate(Avg('percentage'))['avg_percentage']` (handle potential `None` if no attempts)
            *   `topics_explored_count = Topic.objects.filter(quizzes__attempts__user=request.user).distinct().count()`
            *   `perfect_scores_count = user_attempts.filter(percentage=100.0).count()`
        *   Pass these calculated values into the template context dictionary.
    2.  **Modify `pages/templates/pages/profile.html`:**
        *   Replace the hardcoded numbers in the stats cards with the corresponding template variables (e.g., `{{ quizzes_taken_count }}`).
        *   Use Django template filters like `|floatformat:0` for the average score percentage if needed.

**Phase 2: Implement Mistake Tracking (Requires Model & Other Changes)**

*   **Goal:** Record which specific questions were answered incorrectly (and optionally, correctly) for each quiz attempt, allowing for detailed review and future features like flashcards.
*   **Achievability:** **Requires Adjustments.** This is the most significant change needed for deeper stats/revision features. Involves database, backend, frontend, and template changes.
*   **Steps (Conceptual):**
    1.  **Database (Model Change):**
        *   Create a new model (e.g., `UserAnswer` or `AttemptDetail`) in `multi_choice_quiz/models.py`.
        *   Fields: `attempt` (FK to `QuizAttempt`), `question` (FK to `Question`), `selected_option` (FK to `Option`, nullable), `is_correct` (BooleanField).
        *   Run `makemigrations` and `migrate`.
    2.  **Data Transformation (`transform.py` - Minor Change):**
        *   Ensure `models_to_frontend` includes `option.id` alongside `option.text` in the data sent to the frontend.
    3.  **Frontend (`app.js` - Moderate Change):**
        *   Modify the JS quiz logic to store `question_id` and selected `option_id` for each answer.
        *   Modify the `submitResults` function to send an enhanced payload including a list of these detailed answers (e.g., `[{question_id: X, selected_option_id: Y}, ...]`) along with the summary score.
    4.  **Backend (`multi_choice_quiz.views.submit_quiz_attempt` - Significant Change):**
        *   Modify the view to parse the new detailed `answers` list from the JSON payload.
        *   After creating the `QuizAttempt` summary record, iterate through the received answers.
        *   For each answer, create and save a corresponding `UserAnswer` record, linking it to the `QuizAttempt`, `Question`, `Option`, and calculating `is_correct`. Wrap this in a transaction.
    5.  **Profile Page (`pages.views.profile_view` & `profile.html` - Moderate Change):**
        *   Modify the view to fetch related `UserAnswer` objects when retrieving `QuizAttempt`s (use `prefetch_related`).
        *   Modify the template to display the mistake details (e.g., under each attempt in the history, or potentially in a separate detailed view per attempt).

**Phase 3: Future Enhancements (Building on Previous Phases):**

*   **Goal:** Leverage the improved data structure for more advanced features.
*   **Achievability:** Depends on completing Phase 1 & 2. Varies from moderate to complex.
*   **Ideas:**
    *   **Mistake-Based Flashcards/Revision:** (Requires Phase 2) Create a new view/app that queries `UserAnswer` records where `is_correct=False` for the logged-in user and presents them as flashcards.
    *   **Detailed Attempt Review Page:** (Requires Phase 2) Create a new view that takes an `attempt_id` and shows every question, the user's answer, and the correct answer for that specific attempt.
    *   **Topic Mastery Stats:** (Requires Phase 2) Analyze `UserAnswer` data grouped by `question.topic` to calculate performance per topic. Display this on the profile.
    *   **Functional Favorites:** (Requires Model Changes) Add ManyToManyField, update views to handle adding/removing favorites, update profile template to list them.
    *   **Functional Created Quizzes:** (Requires Model Changes) Add `creator` ForeignKey to `Quiz`, potentially build a simple quiz creation interface, update profile template to list them.
    *   **Functional Edit Profile:** (Requires Forms/Views, maybe Model changes for custom fields) Implement forms and views to handle profile updates, linking to Django's built-in views for password/email changes where possible.

**Summary:**

You can immediately make the profile stats *dynamic* by working within the existing `pages` app (views/templates) and querying the `multi_choice_quiz` models. This provides a good improvement with relatively low effort. Tracking *specific mistakes* is the next logical step for deeper analysis and features like flashcards, but requires database modifications (new model) and adjustments across the frontend/backend data flow. Features like Favorites and Created Quizzes are further out as they also require model changes.

---
Okay, here is a prioritized checklist for enhancing the user profile page, categorized from most obtainable (no database model changes needed) to farthest (requiring significant changes or new features).

**Phase 1: Immediate Wins (No Model Changes - View/Template Edits Only)**

*   `[ ]` **Implement Dynamic Stats Cards:**
    *   `[ ]` Calculate and display the correct "Quizzes Taken" count in `pages.views.profile_view` and `profile.html`.
    *   `[ ]` Calculate and display the correct "Average Score" percentage.
    *   `[ ]` Calculate and display the correct "Topics Explored" count.
    *   `[ ]` Calculate and display the correct "Perfect Scores" count.
*   `[ ]` **Refine Quiz History Display:**
    *   `[ ]` Verify the date/time format for completed attempts is clear and user-friendly.
    *   `[ ]` Ensure the "Take Again" links correctly point to the respective quiz detail pages.

**Phase 2: Core Enhancement - Mistake Tracking (Requires DB Model Change + Frontend/Backend Logic)**

*   `[ ]` **Implement Mistake Tracking Infrastructure:**
    *   `[ ]` **Database:** Define and add a new `UserAnswer` model (or similar name) in `multi_choice_quiz.models` with ForeignKeys to `QuizAttempt`, `Question`, `Option` (nullable), and an `is_correct` BooleanField.
    *   `[ ]` **Database:** Run `makemigrations` and `migrate` to apply the new model.
    *   `[ ]` **Frontend:** Modify `app.js` (and potentially `transform.py`) to capture `question_id`, `selected_option_id` during the quiz.
    *   `[ ]` **Frontend:** Modify `app.js` (`submitResults`) to send a payload containing the list of detailed answers along with the summary score.
    *   `[ ]` **Backend:** Modify `multi_choice_quiz.views.submit_quiz_attempt` to parse the detailed answers and create/save `UserAnswer` records for the submitted `QuizAttempt` (within a transaction).
*   `[ ]` **Display Basic Mistake Information:**
    *   `[ ]` **Backend:** Update `pages.views.profile_view` to fetch related `UserAnswer` data using `prefetch_related`.
    *   `[ ]` **Template:** Modify `pages/templates/pages/profile.html` to loop through the fetched answers for each attempt in the history and display basic info for incorrect answers (e.g., Question text, Correct answer text).

**Phase 3: Further Features (Often Require DB Model Changes or Build on Phase 2)**

*   `[ ]` **Implement Functional "Favorites" Tab:**
    *   `[ ]` **Database:** Add a ManyToManyField relationship between `User` and `Quiz`.
    *   `[ ]` **Database:** Run migrations.
    *   `[ ]` **Backend/Frontend:** Create views/URLs/template logic for users to add/remove quizzes from their favorites.
    *   `[ ]` **Profile:** Display the user's favorited quizzes in the "Favorites" tab.
*   `[ ]` **Implement Functional "Created Quizzes" Tab:**
    *   `[ ]` **Database:** Add a `creator` ForeignKey field (linking to `User`) on the `Quiz` model.
    *   `[ ]` **Database:** Run migrations.
    *   `[ ]` **Backend:** Update admin/import scripts (if applicable) to set the creator. Potentially build a user-facing quiz creation interface (much larger task).
    *   `[ ]` **Profile:** Display quizzes where `creator == request.user` in the "Created Quizzes" tab.
*   `[ ]` **Implement Basic "Edit Profile" Functionality:**
    *   `[ ]` **Backend:** Create a simple form and view to update basic, non-sensitive `User` fields (like `first_name`, `last_name`).
    *   `[ ]` **Template:** Link the "Edit Profile" button to this new view.
    *   `[ ]` **Template:** Add links to Django's built-in password change (`{% url 'password_change' %}`) and potentially email change views.

**Phase 4: Advanced/Future Ideas (Build on Previous Phases)**

*   `[ ]` **Create Mistake-Based Revision Feature (e.g., Flashcards):** (Depends on Phase 2)
    *   Build a new view/template that queries `UserAnswer` for incorrect answers and presents them in a study format.
*   `[ ]` **Create Detailed Attempt Review Page:** (Depends on Phase 2)
    *   Build a new view that takes a `QuizAttempt` ID and displays all questions, the user's selection, and the correct answer for that specific attempt.
*   `[ ]` **Add Advanced Profile Stats:** (Depends on Phase 2)
    *   Implement calculations and display for stats like performance per topic, weakest areas, etc., based on `UserAnswer` data.
*   `[ ]` **Implement Full "Edit Profile" (Custom Fields/Avatar):** (Requires new `Profile` Model)
    *   Define a separate `Profile` model linked OneToOne to `User` for custom fields (bio, avatar ImageField, etc.).
    *   Implement the necessary forms, views, and template updates, including handling image uploads.
*   `[ ]` **Implement Leaderboards or Social Features:** (Likely requires new models/app)
    *   Design and implement models and logic for comparing user scores, ranking, etc.

This checklist progresses from changes requiring only view/template modifications using existing data, through the core database change for mistake tracking, and finally to features requiring further model changes or building significantly upon the mistake data.