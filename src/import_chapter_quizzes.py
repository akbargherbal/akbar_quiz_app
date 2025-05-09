#!/usr/bin/env python
# src/import_chapter_quizzes.py
import os
import sys
import pandas as pd
import django
import traceback
import logging
from datetime import datetime
from pathlib import Path  # Keep Path if main() uses it, though it doesn't seem to here.

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir, f'quiz_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)

# This logger is for this script's main() function and direct logging.
# The utility functions will use their own logger from utils.py.
logger = logging.getLogger(
    "quiz_import_script"
)  # Renamed to avoid conflict if utils logger was also "quiz_import"

# Constants for formatting (used by main to pass to utility function)
CHAPTER_PREFIX_ENABLED = True
CHAPTER_PREFIX_ZFILL = 2

try:
    # Set up Django
    logger.info("Initializing Django for import_chapter_quizzes.py script...")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    # --- Import the refactored utility functions ---
    from multi_choice_quiz.utils import load_quiz_bank, import_questions_by_chapter

    # Models are used by print_database_summary and potentially by type hints if you add them.
    # The utility functions themselves handle their model imports.
    from multi_choice_quiz.models import Quiz, Question, Option, Topic

    # transaction, IntegrityError are used by the utility function, no need to import here unless main uses them.

    logger.info("Django initialized successfully for import_chapter_quizzes.py script.")
except Exception as e:
    logger.error(f"Failed to initialize Django: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)


# load_quiz_bank and import_questions_by_chapter are now imported from utils


def print_database_summary():
    """Display a summary of the database contents."""
    try:
        logger.info("\nDatabase Summary:")
        logger.info(f"Total Quizzes: {Quiz.objects.count()}")
        logger.info(f"Total Questions: {Question.objects.count()}")
        logger.info(f"Total Options: {Option.objects.count()}")
        logger.info(f"Total Topics: {Topic.objects.count()}")

        logger.info("\nQuizzes by chapter:")
        for quiz in Quiz.objects.all().order_by("title"):
            logger.info(f"- {quiz.title}: {quiz.question_count()} questions")

    except Exception as e:
        logger.error(f"Error generating database summary: {str(e)}")
        logger.error(traceback.format_exc())


def main():
    """Main function to run the import process."""
    try:
        logger.info("Starting quiz import process (via import_chapter_quizzes.py)...")
        # ... (other logging) ...

        use_descriptive_titles = True
        use_chapter_prefix = CHAPTER_PREFIX_ENABLED
        chapter_zfill_val = CHAPTER_PREFIX_ZFILL
        test_mode = "--test" in sys.argv
        test_file = None
        # --- NEW: For System Category ---
        cli_system_category_arg = None
        # --- END NEW ---

        # Parse arguments
        i = 0
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--test-file" and i + 1 < len(sys.argv):
                test_file = sys.argv[i + 1]
                i += 1
            elif arg == "--simple-titles":
                use_descriptive_titles = False
            elif arg == "--no-chapter-prefix":
                use_chapter_prefix = False
            elif arg == "--zfill" and i + 1 < len(sys.argv):
                try:
                    chapter_zfill_val = int(sys.argv[i + 1])
                    i += 1
                except ValueError:
                    logger.warning(
                        f"Invalid zfill value: {sys.argv[i+1]}. Using default {chapter_zfill_val}."
                    )
            # --- NEW: Parse --system-category ---
            elif arg == "--system-category" and i + 1 < len(sys.argv):
                cli_system_category_arg = sys.argv[i + 1]
                logger.info(
                    f"CLI System Category specified: '{cli_system_category_arg}'"
                )
                i += 1
            # --- END NEW ---
            i += 1

        if test_file:
            quiz_bank_path = test_file
            logger.info(f"Running in test mode with provided file: {quiz_bank_path}")
        elif test_mode:
            logger.info("Running in test mode with generated data.")
            df = pd.DataFrame({})  # ... (sample data as before) ...
            quiz_count, question_count = import_questions_by_chapter(
                df,
                questions_per_quiz=2,
                quizzes_per_chapter=1,
                use_descriptive_titles=use_descriptive_titles,
                use_chapter_prefix=use_chapter_prefix,
                chapter_zfill=chapter_zfill_val,
                cli_system_category_name=cli_system_category_arg,  # Pass CLI arg
            )
            # ... (log summary and return) ...
            logger.info(
                f"\nTest import completed. Created {quiz_count} test quizzes, {question_count} questions."
            )
            print_database_summary()
            return 0
        else:
            quiz_bank_path = input(
                "Enter the path to the quiz bank file (e.g., 'data/quiz_bank.pkl'): "
            )

        df = load_quiz_bank(quiz_bank_path)
        if df is None:
            logger.error("Cannot proceed: Failed to load quiz bank (returned None).")
            return 1

        quiz_count, question_count = import_questions_by_chapter(
            df,
            use_descriptive_titles=use_descriptive_titles,
            use_chapter_prefix=use_chapter_prefix,
            chapter_zfill=chapter_zfill_val,
            cli_system_category_name=cli_system_category_arg,  # Pass CLI arg
        )
        # ... (log summary and return) ...
        logger.info(
            f"\nImport process completed. Created {quiz_count} quizzes with a total of {question_count} questions."
        )
        print_database_summary()
        return 0
    # ... (exception handling and finally block) ...
    except FileNotFoundError as fnf_error:
        logger.error(f"File not found error in main: {str(fnf_error)}")
        return 1
    except ValueError as val_error:
        logger.error(f"Value error in main (e.g. missing columns): {str(val_error)}")
        return 1
    except Exception as e:
        logger.critical(f"Critical error in main process: {str(e)}", exc_info=True)
        return 1
    finally:
        logger.info(f"Log file saved to: {log_file}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
