## **LLM Guide: Modifying UI & Styles in the Django Quiz App (Post-Auth Implementation)**

**1. Purpose:**

This guide provides context for making UI and styling changes (CSS, Tailwind classes, icons, layout adjustments) to the Django Quiz App. The primary goal is to **enhance the visual presentation without breaking existing application functionality**, particularly the quiz-taking logic (Alpine.js) and the user authentication system (Django Auth).

**2. Core Technologies:**

- **Backend:** Django (Python)
- **Frontend Logic:** Alpine.js (v3.x) for quiz interactivity.
- **Styling:** Tailwind CSS (v4 Browser Build via CDN), supplemented by static CSS files.
- **Templating:** Django Template Language (DTL).

**3. Current Application State & Key Areas:**

- **Authentication (Phase 3 Complete):**
  - Uses `django.contrib.auth` for backend user management.
  - Login/Logout uses default Django views, potentially customized templates (e.g., `registration/logged_out.html` might exist, but `LOGOUT_REDIRECT_URL='/'` is active).
  - Placeholder `/login/` and `/signup/` pages exist (`pages` app), currently non-functional for user creation/login via UI.
  - A login-required `/profile/` page exists (`pages` app), displaying the logged-in user's details and their quiz attempt history (`QuizAttempt` model).
  - The main navigation bar (`pages/base.html`) conditionally displays "Login/Sign Up" links (anonymous) or "Profile/Logout" links (authenticated).
  - The "Logout" link is implemented as a POST form for security.
  - Quiz attempts (`QuizAttempt` model) are optionally linked to the `User` model if a user is logged in during submission. Anonymous submissions still work correctly.
- **Quiz Taking (`multi_choice_quiz` app):**
  - Main interface is `multi_choice_quiz/index.html`.
  - Relies heavily on the Alpine.js component defined in `multi_choice_quiz/static/multi_choice_quiz/app.js` (`quizApp`).
  - Quiz data (questions, options, answers) is loaded via a JSON script tag (`id="quiz-data"`).
  - The Alpine component manages state (`currentQuestionIndex`, `score`, `isAnswered`, `quizCompleted`, etc.).
  - Options are displayed using `x-for` and handle clicks via `@click="selectOption(index)"`.
  - Dynamic styling for options (colors, feedback effects) is controlled by `:class="getOptionClass(index)"` in the template, referencing logic in `app.js`.
  - Quiz results are submitted asynchronously via `fetch` in the `submitResults` function in `app.js` to the `/quiz/submit_attempt/` endpoint.
  - The quiz title (`{{ quiz.title }}`) is displayed only on the results panel.
- **General Pages (`pages` app):**
  - Provides Home, About, Quizzes, Login (placeholder), Signup (placeholder), Profile pages.
  - Uses `pages/base.html` as the main layout template.
  - `pages/home.html` displays featured quizzes and topics.
  - `pages/quizzes.html` allows browsing all quizzes, with optional topic filtering via URL parameters.

**4. Current Styling Approach:**

- **Primary:** Tailwind CSS utility classes applied directly in HTML templates (`.html` files). Configuration is done via CDN script in `pages/base.html`.
- **Supplementary:** A static CSS file (`multi_choice_quiz/static/multi_choice_quiz/style.css`) contains:
  - Base styles for specific elements (e.g., `.option-button`).
  - Overrides for specific scenarios (e.g., `code`, `pre` tag styling within options/mistakes).
  - Media queries for responsive adjustments.
  - Keyframe animations (`@keyframes pulse-glow-scale`).
  - The `.option-hidden-immediately` class for instant hiding.
- **Dynamic Styling:** Alpine.js `:class` bindings are used in `multi_choice_quiz/index.html` for quiz option feedback. The logic determining these classes resides in `app.js` (`getOptionClass`).

**5. Critical Elements & Constraints (DO NOT BREAK):**

- **HTML Structure for Alpine:**
  - The root element with `x-data="quizApp()"` and `x-init="init()"` (`id="quiz-app-container"`).
  - Elements controlled by `x-if` or `x-show` (Quiz vs. Results panels).
  - The `template` tags using `x-for` to loop through questions/options/mistakes.
  - The `<button>` elements for options must retain `@click="selectOption(index)"` and `:class="getOptionClass(index)"`.
  - The "Play Again" button must retain `@click="restartQuiz"`.
  - Any element using `x-text` or `x-html` to display dynamic data (score, counter, question text, option text, results stats).
- **Data Loading:**
  - The `<script id="quiz-data" type="application/json">` tag must remain intact and correctly contain the JSON data passed from the Django view.
  - The `data-quiz-id` attribute on `#quiz-app-container` must remain if present.
- **Authentication Elements:**
  - The `{% if user.is_authenticated %}` / `{% else %}` / `{% endif %}` blocks in `pages/base.html` controlling navigation link visibility.
  - The Logout `<form>` structure (`method="post"`, `action="{% url 'logout' %}"`, `{% csrf_token %}`, and the submit button) must remain functional.
  - The structure used to display user info (`user.username`, etc.) and loop through `quiz_attempts` in `pages/profile.html`.
- **URLs and Static Files:**
  - `{% url '...' %}` tags must point to valid URL names.
  - `{% static '...' %}` tags must correctly load necessary JS and CSS files.
- **CSS:**
  - Do not remove or drastically alter the functionality of core classes defined in `style.css` that are used by Alpine bindings (e.g., `.option-button` base styles, `.option-hidden-immediately`, animation keyframes), unless specifically requested and the impact is understood.
- **JavaScript (`app.js`):** Avoid changes that require modifications to the Alpine component logic unless that is the specific task. Styling changes should ideally be achievable via HTML/CSS/Tailwind.

**6. Safe Modification Zones:**

- **Purely Visual Tailwind Classes:** Applying utility classes for color, padding, margin, font size/weight, borders, shadows, flex/grid layout _on container elements_ (`div`, `section`, `header`, `footer`, etc.) that are _not_ directly targeted by critical `:class` bindings or specific `id` selectors used by JS.
- **Static CSS (`style.css`):** Adding _new_ CSS rules targeting _new_ classes you introduce in the HTML, or modifying existing rules that _only_ affect visual presentation (e.g., changing color values, font families) without altering layout properties relied upon by JS (like `display`).
- **Icons:** Replacing text (like the home emoji 🏠) or placeholder icons with SVG or font icons, ensuring they are placed correctly within the existing layout structure.
- **Text Content:** Modifying static text content (e.g., headings, paragraphs in About page, placeholder text) that isn't part of functional elements like buttons or dynamic data display.
- **Adding Decorative Elements:** Adding purely visual elements (e.g., background patterns, dividers) that don't interfere with the layout or functionality of existing components.

**7. Testing and Verification:**

- **ALL** UI changes must be manually tested in a browser across different states (anonymous, authenticated, during quiz, quiz results).
- Run the relevant automated tests after making changes:
  - `python manage.py test` (Full Django suite)
  - `python run_pages_e2e_tests.py` (Pages app E2E)
  - `python run_multi_choice_quiz_e2e_tests.py` (Quiz app E2E)
- **No changes should be considered complete if any tests fail.**

**8. Example Prompt Structure:**

```text
Objective: Change the background color of the header.

File(s) to Modify: src/pages/templates/pages/base.html

Current State: The header currently uses `bg-bg-secondary/80`.

Desired Change: Change the header background to use the primary accent color (`bg-accent-primary`) and remove the opacity/blur effect.

Constraints: Do not change the navigation links, logo, or mobile menu functionality within the header. Ensure the change applies correctly on all screen sizes. Refer to the LLM Guide regarding safe modifications.

Verification: I will manually check the appearance and run automated tests afterward.
