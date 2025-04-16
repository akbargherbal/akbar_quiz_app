**Overall Goal for Next Two Weeks:**

1.  **Reliably save quiz results to the database.** (Complete the core of the _new_ Iteration 3)
2.  **Establish the basic, navigable site structure using the `pages` app.** (Complete the core of the _new_ Iteration 4)

**Week 1 Focus: Backend Persistence & Verification (Iteration 3)**

- **Objective:** Get quiz results saved correctly. Verify thoroughly via Admin and automated tests. _Minimal focus on frontend UI changes this week._
- **Tasks (Following the Revised Plan):**
  1.  **Step 3.1: Define Result Models (`QuizAttempt`, `UserAnswer`):**
      - LLM generates model code, migration.
      - You run checks, `makemigrations`, `migrate`.
      - LLM generates basic model unit tests.
      - You run tests (`manage.py test ...test_models`). **Checklist Complete.**
  2.  **Step 3.2: Expose Result Models in Admin:**
      - LLM updates `admin.py`.
      - You run the server, manually check `/admin/` for the new models. **Checklist Complete.**
  3.  **Step 3.3: Create API Endpoint (View/URL):**
      - LLM generates `submit_results` view and URL pattern.
      - LLM generates Django Test Client tests for this endpoint (valid/invalid data).
      - You run linters (`ruff`).
      - You run tests (`manage.py test ...test_views`). **Checklist Complete.**
  4.  **Step 3.4: Frontend JS Submission (Minimal):**
      - LLM modifies `app.js` to add the `fetch` POST call on quiz completion.
      - LLM generates a Playwright test (`test_submission_e2e.py`) to verify the POST request is sent correctly (using `page.expect_request` or similar).
      - You run linters (`eslint`, if configured).
      - You run the Playwright test (`pytest ...test_submission_e2e.py`). **Checklist Complete.**
- **End-of-Week Goal:** You should be able to complete a quiz, and verify via the Django Admin and automated tests that a `QuizAttempt` and corresponding `UserAnswer` records are successfully created in the database. The frontend quiz experience should remain largely unchanged visually for now.

**Week 2 Focus: Basic Site Structure & Integration (Iteration 4)**

- **Objective:** Integrate the quiz app into a consistent site layout provided by the `pages` app. Implement the basic quiz browsing page.
- **Tasks (Following the Revised Plan):**
  1.  **Step 4.1: Implement Base Layout (`pages` app):**
      - LLM refines/implements `pages/base.html` (Tailwind, header, footer, content block).
      - LLM ensures basic views/templates exist for Home, About, Login, Signup, Profile (extending the base).
      - LLM ensures `pages/urls.py` and project `urls.py` are correct.
      - You run linters (`djlint`, `ruff`).
      - LLM generates/updates Django Test Client tests for basic page rendering.
      - LLM generates/updates Playwright tests for static page structure/navigation.
      - You run tests (Django & Playwright). **Checklist Complete.**
  2.  **Step 4.2: Integrate Quiz App into Base Layout:**
      - LLM modifies `multi_choice_quiz/index.html` to extend `pages/base.html`.
      - LLM ensures quiz CSS is still loaded correctly (e.g., via `extra_css` block).
      - You manually review potential CSS conflicts (minimal adjustments expected).
      - LLM generates/updates Playwright test to load a quiz page and verify header/footer presence alongside quiz elements.
      - You run the Playwright test. **Checklist Complete.**
  3.  **Step 4.3: Implement Quiz Browsing Page (`pages` app):**
      - LLM updates `pages/views.py` (`quizzes` view) to fetch active Quizzes and Topics.
      - LLM implements `pages/quizzes.html` to display the list of quizzes (cards, titles, topics, start button) using Tailwind. Include non-functional topic filter buttons.
      - You run linters (`djlint`, `ruff`).
      - LLM generates/updates Django Test Client test for `/quizzes/` rendering.
      - LLM generates/updates Playwright test to load `/quizzes/`, check cards, and test a "Start Quiz" link.
      - You run tests (Django & Playwright). **Checklist Complete.**
- **End-of-Week Goal:** The application should have a consistent look and feel across the Home, About, Quiz Browse, and individual Quiz pages. Users can navigate between these sections. The `/quizzes/` page should dynamically list quizzes from the database.

**Key Strategies for Success:**

- **Strict Adherence:** Follow the _revised_ plan steps sequentially. Do _not_ let the LLM jump ahead or combine steps.
- **Verification is MANDATORY:** Complete the verification checklist for each step before asking the LLM for the next one. If a check fails, the _immediate next task_ is to fix it, not move on.
- **Focused Prompts:** Give the LLM very specific instructions, referencing the step number and its objectives/deliverables from the revised plan (e.g., "Complete Step 3.1: Define Result Models. Generate the Python code for `QuizAttempt` and `UserAnswer` in `models.py` and the necessary migration file.").
- **Smaller Commits:** Commit your code to Git after each _verified_ step.
- **Defer Everything Else:** Do _not_ work on polishing the results display (Iteration 5), implementing filtering logic (Iteration 5), authentication (Iteration 6), deployment (Iteration 7+), or HTMX during these two weeks.

