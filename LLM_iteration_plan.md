# LLM-Led Development Plan for Django Quiz App

## Iteration 1: Move Quiz Data to Django Context

**User Inputs:**

1. Existing front-end code (HTML, CSS, JS files)
2. Description of development environment (Python version, preferred package manager)
3. Any preferences for project/app naming

**LLM Deliverables:**

1. Terminal commands to:
   - Create Django project and app
   - Install required dependencies
   - Set up initial structure
2. Complete Django files:
   - `settings.py` with necessary configurations
   - `urls.py` for both project and app
   - `views.py` with the quiz view function
   - Any template modifications needed for the index.html
3. Instructions for:
   - Where to place the existing files
   - Any modifications needed to the existing files
   - How to run the Django server

**Expected Results:**

- Working Django app serving the existing quiz with data coming from Django
- No database requirements yet (using static data in views)
- Identical user experience to the current version

**Verification:**

- Playwright test script that checks:
  - Quiz loads with correct questions
  - Quiz functions as expected
  - Test commands to run the verification

## Iteration 2: Models Aligned with Quiz Bank Format

**User Inputs:**

1. The completed code from Iteration 1
2. Sample of the quiz bank format (as previously shared)
3. Any admin customization preferences

**LLM Deliverables:**

1. Complete model definitions aligned with the quiz bank format:
   - `models.py` with models for:
     - Question (with fields: topic, question_text, chapter_no)
     - Option (with fields: text, is_correct)
     - Quiz (to group questions)
   - Migration commands
2. Django admin configuration:
   - `admin.py` with registered models and customizations
   - Admin interfaces optimized for the data structure
3. Updated view code:
   - Modified `views.py` to pull from database instead of static data
   - Data structure conversion to match what Alpine.js expects
4. Manual data entry script/instructions:
   - For adding a few sample quizzes without requiring full import yet
5. Instructions for:
   - Running migrations
   - Creating a superuser
   - Accessing the admin
   - Adding quiz content

**Expected Results:**

- Database structure that mirrors the quiz bank format
- Admin interface for managing quizzes, questions, and options
- Frontend pulling quiz data from the database

**Verification:**

- Playwright test script checking:
  - Admin login works
  - Quiz creation via admin works
  - Frontend correctly displays database-stored quiz
  - Test commands for running verification

# Updated Iteration 3: Quiz Results & UI Enhancement

## User Inputs:

1. Completed code from Iteration 2
2. Preferences for UI styling and layout
3. What result data should be captured (time taken, score, individual answers, etc.)

## LLM Deliverables:

### 1. Result Tracking Implementation:

- `models.py` additions for QuizAttempt and UserAnswer models
- Migration commands
- View functions for receiving and processing results

### 2. Basic UI Framework:

- Create a consistent UI layout with navigation elements
- Implement a homepage with quiz selection (even with limited functionality)
- Add placeholder pages for future features (login, signup, user dashboard)
- Design shared templates/components (header, footer, navigation)

### 3. HTMX Integration:

- Instructions for adding HTMX to the project
- Updated HTML with HTMX attributes for quiz submission
- Required JS bridges between Alpine.js and HTMX

### 4. Styling Improvements:

- Enhanced CSS for a more polished appearance
- Responsive design improvements for mobile users
- Transition effects for better user experience

### 5. Static Placeholder Pages:

- Login/Signup pages (non-functional but visually complete)
- User profile page mockup
- Quiz history view mockup
- Statistics dashboard mockup

### 6. Instructions for:

- Running migrations for the new models
- Testing the submission flow
- Navigating between the new UI pages

## Expected Results:

- Quiz results saved to database after completion
- Confirmation message shown to user
- Admin interface showing submitted results
- Cohesive application UI with consistent styling
- Static mockups of future functionality
- Improved user experience with better visual design

## Verification:

- Playwright test script checking:
  - Results correctly submitted to server
  - Confirmation displayed to user
  - Results appear in database/admin
  - Navigation works between implemented pages
  - Static pages load correctly
  - Test commands for running verification

## Iteration 4: Quiz Selection and User Features

**User Inputs:**

1. The completed code from Iteration 3
2. Authentication preferences (session-only, user accounts, etc.)
3. Desired statistics or history views
4. Any topic/chapter filtering requirements for the quiz bank

**LLM Deliverables:**

1. Quiz browsing and selection:
   - List view of quizzes categorized by topic/chapter
   - Search/filter functionality for finding specific quizzes
   - Templates for displaying quiz metadata
2. Authentication system (if needed):
   - User model customizations
   - Login/registration views and templates
   - Session handling configuration
3. History and statistics:
   - Views for user history
   - Templates for displaying statistics
   - Calculations for user performance by topic/chapter
4. Instructions for:
   - Setting up user accounts (if applicable)
   - Navigating the enhanced application
   - Testing the new features

**Expected Results:**

- Browsable interface for 700 quiz questions organized by topic/chapter
- User history and statistics tracking
- Complete end-to-end quiz application utilizing the entire quiz bank

**Verification:**

- Playwright test script covering:
  - Quiz selection flow
  - Topic/chapter filtering
  - User history views
  - Multiple quiz attempts tracking
  - Test commands for running verification

## Development Workflow for Each Iteration

1. **Preparation:**

   - Create a new branch/directory for the iteration
   - Have the existing code ready for reference

2. **Input Gathering:**

   - Prepare the information listed in "User Inputs" section for each iteration
   - Make decisions about any optional features

3. **LLM Interaction:**

   - Share the existing code and input information with the LLM
   - Request the deliverables for the current iteration
   - Ask for clarification on any instructions that aren't clear

4. **Implementation:**

   - Create files and directories as instructed
   - Copy generated code into appropriate files
   - Run commands as provided in the instructions

5. **Testing:**

   - Run the provided test scripts
   - Manually verify functionality works as expected
   - Report any issues to the LLM for troubleshooting

6. **Iteration Completion:**
   - Commit working code
   - Prepare for next iteration by gathering new inputs
