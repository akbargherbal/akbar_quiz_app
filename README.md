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

## Populating the Database with Quizzes

QuizMaster relies on Python scripts to efficiently bulk import quiz questions into the database. These scripts process structured data, primarily from Pandas DataFrames stored as Pickle files (`.pkl`).

There are two main scripts for importing quizzes:

1.  **`dir_import_chapter_quizzes.py`**: This is the **primary script** for bulk importing quizzes from a directory of `.pkl` files. It's designed to handle multiple files, typically organized by chapter or larger collections.
2.  **`import_chapter_quizzes.py`**: This script is generally used for importing questions from a **single `.pkl` file**. It shares much of its underlying logic with `dir_import_chapter_quizzes.py` but has a simpler command-line interface focused on one file at a time.

Both scripts need to be run from the `src/` directory of the project, with your Django virtual environment activated. The underlying import logic has been refactored to use `bulk_create` for improved performance, especially with PostgreSQL databases.

### 1. `dir_import_chapter_quizzes.py` (Bulk Import from Directory)

This script scans a specified directory (by default, `QUIZ_COLLECTIONS/` in the project root relative to `src/manage.py`) for `.pkl` files and imports the quiz data from each.

**Default Usage:**

```bash
(your_venv) $ python dir_import_chapter_quizzes.py --import-dir
```

This command will:

- Look for `.pkl` files in the `PROJECT_ROOT/QUIZ_COLLECTIONS/` directory (where `PROJECT_ROOT` is the directory containing `src/`).
- Process each file, creating quizzes and questions based on the data within.
- Log its progress and a summary to the console and to a timestamped log file in the `logs/` directory (relative to `src/`).

**Key Command-Line Arguments:**

- `--import-dir`: **Required** to run the directory import mode.
- `--test`: Runs the script in test mode using internally generated sample data. Useful for verifying the script and database connection without needing actual `.pkl` files. No quizzes are imported from files in this mode.
- `--test-file /path/to/your/test_file.pkl`: Runs the script in test mode but uses the specified `.pkl` file instead of generated data.
- `--system-category "Category Name"`: (Optional) Assigns all quizzes imported during this run to the specified `SystemCategory`. If the category doesn't exist, it will be created. This CLI argument overrides any `system_category` column present in the `.pkl` files.
- `--simple-titles`: (Optional) Uses a simpler format for quiz titles (e.g., "Chapter 1 - Quiz 1") instead of the more descriptive default (e.g., "01 Chapter Title: Topic Name - Quiz 1").
- `--no-chapter-prefix`: (Optional) Disables the automatic prefixing of quiz titles with the chapter number (e.g., "01 ").
- `--zfill <number>`: (Optional) Specifies the zero-padding for the chapter number prefix if `--no-chapter-prefix` is NOT used. Default is `2` (e.g., "01", "02", ..., "10"). Example: `--zfill 3` would produce "001".

**Expected `.pkl` File Structure:**

The script expects each `.pkl` file to be a Pandas DataFrame with at least the following columns:

- `chapter_no`: (e.g., 1, 2, "A1") The chapter identifier.
- `question_text`: The text of the question.
- `options`: A list of strings representing the answer options.
- `answerIndex`: An integer (1-based) indicating the correct option in the `options` list.
- `topic`: (Optional but Recommended) The topic of the question. Used for generating descriptive quiz titles.
- `CHAPTER_TITLE`: (Optional but Recommended) The title of the chapter. Used for generating descriptive quiz titles.
- `system_category`: (Optional) The name of a `SystemCategory` to associate the quiz with. This is overridden if `--system-category` is used on the command line.
- `tag`: (Optional) A tag for categorizing questions.

**Log Files:**

A detailed log file for each run will be created in the `src/logs/` directory, named like `dir_quiz_import_YYYYMMDD_HHMMSS.log`.

### 2. `import_chapter_quizzes.py` (Import from a Single File)

This script is for importing quiz data from a single `.pkl` file.

**Interactive Usage (Default):**

If run without specific file arguments, it will prompt you to enter the path to the `.pkl` file:

```bash
(your_venv) $ python import_chapter_quizzes.py
Enter the path to the quiz bank file (e.g., 'data/quiz_bank.pkl'): path/to/your/file.pkl
```

**Direct File Usage (using `--test-file`):**

```bash
(your_venv) $ python import_chapter_quizzes.py --test-file /path/to/your/file.pkl
```

(Note: `--test-file` here provides the file path directly. To run with internally generated data for script testing, use `--test`.)

**Key Command-Line Arguments:**

- `--test-file /path/to/your/file.pkl`: Specifies the path to the `.pkl` file to import directly, bypassing the interactive prompt.
- `--test`: Runs the script in test mode using internally generated sample data. This is for script testing and ignores any file paths.
- `--system-category "Category Name"`: (Optional) Assigns the imported quiz (or quizzes, if the file contains data for multiple auto-generated quizzes) to the specified `SystemCategory`.
- `--simple-titles`, `--no-chapter-prefix`, `--zfill <number>`: Same as for `dir_import_chapter_quizzes.py`.

**Expected `.pkl` File Structure:**

Same as for `dir_import_chapter_quizzes.py`.

**Log Files:**

A detailed log file for each run will be created in the `src/logs/` directory, named like `quiz_import_YYYYMMDD_HHMMSS.log`.

---

**General Notes for Both Scripts:**

- **Django Context:** Both scripts initialize the Django environment, so they must be run from within the `src/` directory where `manage.py` is located.
- **Virtual Environment:** Ensure your project's virtual environment is activated.
- **Dependencies:** Make sure all project dependencies, including `pandas`, are installed (e.g., from `requirements.txt`).
- **Data Integrity:** The scripts attempt to be robust, but malformed `.pkl` files or data not adhering to the expected column structure can lead to import errors. Check the log files for details if issues occur.
- **Idempotency:** If a quiz with the exact same auto-generated title already exists in the database, the scripts will typically log a warning and skip re-creating that specific quiz and its questions to avoid duplicates.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs or feature suggestions. (Add specific contribution guidelines if desired).
