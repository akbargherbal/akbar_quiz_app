# Django Quiz App - Models and Transformation Guide

## Overview

This document explains how our Django Quiz App handles quiz data and the transformation between different formats. Understanding this is crucial for avoiding issues with question indexing.

## Data Format Comparison

### Quiz Bank Format (Source Data)
- Uses **1-based indexing** for correct answers
- Example:
  ```python
  {
      'text': 'How can you pass initial state from your Django view context to an Alpine.js x-data directive?',
      'options': [
          'Store the context in browser cookies for Alpine to read.',
          'Fetch the data using HTMX and then pass it to Alpine.',
          'Alpine automatically detects Django context variables.',
          'Use a special `x-django-context` directive.',
          'Embed the Django context variable (often JSON-serialized) directly into the `x-data` attribute string within the template.'
      ],
      'answerIndex': 5  # 1-based index! The fifth option (index 5) is correct
  }
  ```

### Database Model Format
- Uses **1-based indexing** for option positions
- Stores correct answer with a boolean flag rather than an index
- Example:
  ```python
  question = Question.objects.create(
      text='How can you pass initial state from your Django view context to an Alpine.js x-data directive?',
      # other fields...
  )

  Option.objects.create(question=question, text='Store the context in browser cookies...', position=1, is_correct=False)
  Option.objects.create(question=question, text='Fetch the data using HTMX...', position=2, is_correct=False)
  Option.objects.create(question=question, text='Alpine automatically detects...', position=3, is_correct=False)
  Option.objects.create(question=question, text='Use a special `x-django-context`...', position=4, is_correct=False)
  Option.objects.create(question=question, text='Embed the Django context variable...', position=5, is_correct=True)
  ```

### Frontend Format (Alpine.js JSON)
- Uses **0-based indexing** for answerIndex (JavaScript standard)
- Example:
  ```javascript
  {
      "text": "How can you pass initial state from your Django view context to an Alpine.js x-data directive?",
      "options": [
          "Store the context in browser cookies for Alpine to read.",
          "Fetch the data using HTMX and then pass it to Alpine.",
          "Alpine automatically detects Django context variables.",
          "Use a special `x-django-context` directive.",
          "Embed the Django context variable (often JSON-serialized) directly into the `x-data` attribute string within the template."
      ],
      "answerIndex": 4  // 0-based index! The fifth option (index 4) is correct
  }
  ```

## Transformation Process

### From Quiz Bank to Database
When importing quiz data from the quiz bank format:

1. We create a `Question` instance with the question text
2. We create `Option` instances with:
   - position (1-based) matching the original order
   - is_correct=True for the option where position matches answerIndex

```python
from multi_choice_quiz.transform import quiz_bank_to_models

# Quiz bank data (with 1-based indexing)
quiz_data = [
    {
        'text': 'Sample question?',
        'options': ['Option A', 'Option B', 'Option C'],
        'answerIndex': 2  # 1-based index
    }
]

# Transform and save to database
quiz = quiz_bank_to_models(quiz_data, "My Quiz", "My Topic")
```

### From Database to Frontend
When sending data to the frontend:

1. We retrieve all question and option data from the database
2. We transform it to the frontend format, converting the 1-based position of the correct option to a 0-based index

```python
from multi_choice_quiz.transform import models_to_frontend

# Get questions from the database
questions = Quiz.objects.get(id=1).questions.all()

# Transform to frontend format (0-based indexing)
frontend_data = models_to_frontend(questions)
```

### From Frontend to Database
When receiving data from the frontend:

1. We convert the 0-based answerIndex back to a 1-based position
2. We then use the standard quiz bank import process

```python
from multi_choice_quiz.transform import frontend_to_models

# Frontend data (with 0-based indexing)
frontend_data = [
    {
        'text': 'Sample question?',
        'options': ['Option A', 'Option B', 'Option C'],
        'answerIndex': 1  # 0-based index
    }
]

# Transform and save to database (handling conversion to 1-based)
quiz = frontend_to_models(frontend_data, "User Created Quiz", "User Topic")
```

## Key Points to Remember

1. **Always use the transformation functions** - Never manually convert between formats
2. **Quiz Bank Format uses 1-based indexing** - This is our source data format
3. **Database Models use 1-based positioning** - Position 1 is the first option
4. **Frontend Format uses 0-based indexing** - Index 0 is the first option
5. **Use the Question.to_dict() method** - For consistent transformation to frontend format

## Common Pitfalls to Avoid

1. **Direct index assignment** - Always use transformation functions to handle indexing differences
2. **Manual JSON serialization** - Use the provided functions to ensure correct indexing
3. **Forgetting to order options** - Always ensure options are ordered by position when retrieving from database
4. **Multiple correct answers** - The database model allows multiple correct answers, but the frontend expects only one

## DataFrame Import Guide

When importing from pandas DataFrames:

1. Ensure your DataFrame has the required columns:
   - `text` or `question_text`
   - `options` (as a list or JSON-serialized string)
   - `answerIndex` or `correct_answer` (1-based)

2. Use the import_from_dataframe utility:

```python
import pandas as pd
from multi_choice_quiz.utils import import_from_dataframe

# Load your dataframe
df = pd.read_csv('quiz_data.csv')

# Import data (handles column mapping and conversion)
quiz = import_from_dataframe(df, "CSV Imported Quiz", "CSV Topic")
```

## Running Tests

This project includes unit tests to verify the functionality, especially the data transformations.

### Standard Test Execution

The primary way to run the entire test suite is using Django's built-in `manage.py` command from the `src/` directory:

```bash
# Navigate to the directory containing manage.py
cd src/

# Run all tests discovered in the project
python manage.py test
```

This project uses a custom test runner (`LoggingTestRunner`) specified in `core/settings.py`. When you run the tests using the command above:
1.  Test results (including standard output and errors) will be displayed on the console.
2.  A detailed log file will be created inside the `src/multi_choice_quiz/` directory.
    *   **Log File Name Pattern:** `django_tests_YYYYMMDD-HHMMSS.log` (e.g., `django_tests_20231027-153000.log`)
    *   **Log File Location:** `src/multi_choice_quiz/django_tests_YYYYMMDD-HHMMSS.log`
    This log contains timestamps and detailed information about the test execution, including any errors or failures.

### Running Tests for a Specific App

To run tests only for the `multi_choice_quiz` application:

```bash
# Ensure you are in the src/ directory
python manage.py test multi_choice_quiz
```
This is useful for focusing on the tests relevant to the quiz logic and models. A log file specific to this run will still be created in the location mentioned above.

### Using Pytest (Optional)

If you have `pytest` and `pytest-django` installed in your Python environment, you can often leverage `pytest` for running tests. It typically offers more detailed output and integrates well with other testing tools like coverage reporters. From the `src/` directory:

```bash
# Ensure you are in the src/ directory
pytest
```
Pytest should automatically discover and run the Django tests using your project's settings. **Note:** When using `pytest` directly, it might not utilize the custom `LoggingTestRunner` unless specifically configured, so the log file might not be generated in the same way. Running via `python manage.py test` ensures the custom runner is used.

### Checking Test Output

Regardless of the method used, carefully review the console output for any reported `FAILURES` or `ERRORS`. If you used `python manage.py test`, the custom log file in `src/multi_choice_quiz/` provides a persistent record of the test run, which can be helpful for debugging.
