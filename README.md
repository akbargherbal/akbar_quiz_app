# Multiple Choice Quiz App

A web application built with Django and Alpine.js that allows users to take multiple-choice quizzes interactively.

## Features

- Displays quizzes fetched from a database.
- Interactive quiz-taking interface powered by Alpine.js.
- Provides immediate feedback ("Correct" / "Incorrect") after each answer.
- Shows the correct answer if the user's selection was incorrect.
- Displays the final score and a summary of answers at the end of the quiz.
- Includes a Django Admin interface for managing Quizzes, Questions, Options, and Topics.
- Comes with a management command to populate the database with sample quizzes.
- Handles differences between data source indexing (1-based) and frontend indexing (0-based) via dedicated transformation functions.
- Provides a utility function to import quiz data from Pandas DataFrames.
- Includes a comprehensive suite of unit tests.
- Features a custom test runner that logs detailed test execution information to a file.

## Technology Stack

- **Backend:** Django (Python)
- **Frontend:** Alpine.js, HTML, CSS
- **Database:** SQLite (default, easily configurable in `core/settings.py`)

## Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

- Python 3.x
- Git
- Pip (Python package installer)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

    _(Replace `<repository-url>` with the actual URL of your Git repository)_

2.  **Create and activate a virtual environment (Recommended):**

    ```bash
    # Navigate to the project root directory (e.g., akbar_quiz_app)
    python -m venv venv

    # Activate the environment:
    # Windows (Git Bash/Command Prompt/PowerShell)
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

    Your terminal prompt should now start with `(venv)`.

3.  **Navigate to the `src` directory:**

    ```bash
    cd src
    ```

4.  **Install dependencies:**
    _(Assuming necessary packages like Django are the main requirement. If you have a `requirements.txt` file in `src/`, use `pip install -r requirements.txt` instead)_

    ```bash
    pip install django
    # Add other dependencies if needed, e.g., pip install pandas
    ```

    _(It's good practice to create a `requirements.txt` file: `pip freeze > requirements.txt`)_

5.  **Apply database migrations:**

    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser account (for accessing the admin panel):**
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to set up a username, email, and password.

## Running the Application

1.  **Ensure you are in the `src` directory** and your virtual environment is active.

2.  **Start the Django development server:**

    ```bash
    python manage.py runserver
    ```

3.  **Access the application:** Open your web browser and navigate to:
    - **Main Quiz Page:** `http://127.0.0.1:8000/` or `http://127.0.0.1:8000/quiz/`
      _(This will likely load the first available quiz or demo data)_
    - **Admin Interface:** `http://127.0.0.1:8000/admin/`

## Usage

### Taking a Quiz

- Navigate to the main URL (`/` or `/quiz/`). The application will load a quiz.
- Answer the questions one by one. Feedback is provided immediately.
- Your final score and a summary will be shown upon completion.
- You can restart the quiz using the "Play Again?" button.

### Adding Sample Data

If the database is empty or you want to add predefined examples:

1.  Make sure the server is **stopped**.
2.  Run the management command from the `src` directory:
    ```bash
    python manage.py add_sample_quizzes
    ```
    This will populate the database with sample Quizzes, Questions, Options, and Topics unless they already exist.
3.  You can also import from a specific JSON file using the `--file` argument:
    ```bash
    python manage.py add_sample_quizzes --file path/to/your/quiz_data.json
    ```

### Admin Interface

- Navigate to `/admin/`.
- Log in using the superuser credentials you created earlier.
- Here you can:
  - Create, view, update, and delete **Topics**.
  - Create, view, update, and delete **Quizzes**.
  - Create, view, update, and delete **Questions** (including adding/modifying their **Options** inline).

## Data Formats and Transformation

This application carefully manages different indexing conventions for quiz answers:

- **Quiz Bank Format (Source/Import):** Uses **1-based** indexing (`answerIndex: 1` means the first option).
- **Database Model:** Uses **1-based** positioning for `Option` objects and marks the correct one with `is_correct=True`.
- **Frontend Format (Alpine.js):** Uses **0-based** indexing (`answerIndex: 0` means the first option).

**Crucially, always use the provided transformation functions in `multi_choice_quiz/transform.py` when moving data between these formats.**

See **[QUIZ_MODELS_GUIDE.md](src/QUIZ_MODELS_GUIDE.md)** for a detailed explanation and examples.

## Running Tests

The project includes automated tests to verify functionality.

1.  **Ensure you are in the `src` directory** and your virtual environment is active.
2.  **Run the tests:**
    ```bash
    python manage.py test
    ```
3.  **Interpreting Output:**
    - Look for `OK` at the end, indicating all tests passed.
    - `.` indicates a passing test.
    - `F` indicates a failure (an assertion failed).
    - `E` indicates an error (an unexpected exception occurred).
    - Detailed tracebacks are provided for failures and errors.
4.  **Log File:** A detailed log of the test run is generated by the custom test runner:
    - **Location:** `src/multi_choice_quiz/`
    - **Name Pattern:** `django_tests_YYYYMMDD-HHMMSS.log`

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs or feature suggestions. (Add specific contribution guidelines if desired).
