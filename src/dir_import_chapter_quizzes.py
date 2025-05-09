#!/usr/bin/env python
# src/dir_import_chapter_quizzes.py
import os
import sys
import pandas as pd
import django
import traceback
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(
    log_dir,
    f'dir_quiz_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',  # Different log file name
)

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)

# This logger is for this script's main() function and direct logging.
logger = logging.getLogger("dir_quiz_import_script")  # Renamed logger

# Constants for formatting
CHAPTER_PREFIX_ENABLED = True
CHAPTER_PREFIX_ZFILL = 2
DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH = "QUIZ_COLLECTIONS"

try:
    # Set up Django
    logger.info("Initializing Django for dir_import_chapter_quizzes.py script...")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    # --- Import the refactored utility functions ---
    from multi_choice_quiz.utils import load_quiz_bank, import_questions_by_chapter

    # Models are used by print_database_summary
    from multi_choice_quiz.models import Quiz, Question, Option, Topic

    # transaction, IntegrityError are used by the utility function

    logger.info(
        "Django initialized successfully for dir_import_chapter_quizzes.py script."
    )
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


def main():
    """Main function to run the import process."""
    try:
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent

        logger.info(
            "Starting directory quiz import process (via dir_import_chapter_quizzes.py)..."
        )
        # ... (other logging) ...

        use_descriptive_titles = True
        use_chapter_prefix = CHAPTER_PREFIX_ENABLED
        chapter_zfill_val = CHAPTER_PREFIX_ZFILL
        test_mode = "--test" in sys.argv
        test_file_path = None
        import_dir_flag = "--import-dir" in sys.argv

        # --- NEW: For System Category ---
        cli_system_category_arg = None
        # --- END NEW ---

        # Parse all arguments
        i = 0
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--test-file" and i + 1 < len(sys.argv):
                test_file_path = sys.argv[i + 1]
                i += 1  # consume value
            elif arg == "--simple-titles":
                use_descriptive_titles = False
            elif arg == "--no-chapter-prefix":
                use_chapter_prefix = False
            elif arg == "--zfill" and i + 1 < len(sys.argv):
                try:
                    chapter_zfill_val = int(sys.argv[i + 1])
                    i += 1  # consume value
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
                i += 1  # consume value
            # --- END NEW ---
            i += 1

        if test_mode:
            logger.info("Running in test mode with generated data.")
            df = pd.DataFrame(  # Sample data for testing
                {  # ... (sample data as before) ...
                    "chapter_no": [1, 1, 2, 2, 10, 10],
                    "topic": [
                        "Test Topic A",
                        "Test Topic B",
                        "Test Topic C",
                        "Test Topic D",
                        "Advanced Testing",
                        "Advanced Testing",
                    ],
                    "question_text": [
                        "Test question 1?",
                        "Test question 2?",
                        "Test question 3?",
                        "Test question 4?",
                        "Test question 5?",
                        "Test question 6?",
                    ],
                    "options": [
                        ["Option A", "Option B", "Option C"],
                        ["Option D", "Option E", "Option F"],
                        ["Option G", "Option H", "Option I"],
                        ["Option J", "Option K", "Option L"],
                        ["Option M", "Option N", "Option O"],
                        ["Option P", "Option Q", "Option R"],
                    ],
                    "answerIndex": [1, 2, 3, 1, 2, 3],
                    "CHAPTER_TITLE": [
                        "Introduction to Testing",
                        "Introduction to Testing",
                        "Advanced Testing",
                        "Advanced Testing",
                        "Expert Testing",
                        "Expert Testing",
                    ],
                    # Optionally add system_category here for test mode if desired
                    # "system_category": ["Test SysCat"] * 6
                }
            )
            quiz_count, question_count = import_questions_by_chapter(
                df,
                questions_per_quiz=2,
                quizzes_per_chapter=1,
                use_descriptive_titles=use_descriptive_titles,
                use_chapter_prefix=use_chapter_prefix,
                chapter_zfill=chapter_zfill_val,
                cli_system_category_name=cli_system_category_arg,  # Pass CLI arg
            )
            logger.info(
                f"\nTest import completed. Created {quiz_count} test quizzes, {question_count} questions."
            )
            print_database_summary()
            return 0

        if test_file_path:
            logger.info(f"Running in test mode with provided file: {test_file_path}")
            df = load_quiz_bank(test_file_path)
            if df is None:
                return 1
            quiz_count, question_count = import_questions_by_chapter(
                df,
                use_descriptive_titles=use_descriptive_titles,
                use_chapter_prefix=use_chapter_prefix,
                chapter_zfill=chapter_zfill_val,
                cli_system_category_name=cli_system_category_arg,  # Pass CLI arg
            )
            logger.info(
                f"\nTest file import completed. Created {quiz_count} quizzes, {question_count} questions."
            )
            print_database_summary()
            return 0

        if import_dir_flag:
            default_import_dir_absolute = (
                project_root / DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH
            ).resolve()
            logger.info(
                f"Directory import mode. Processing .pkl files from: {default_import_dir_absolute}"
            )
            if not default_import_dir_absolute.is_dir():
                logger.error(
                    f"Default import directory '{default_import_dir_absolute}' not found or is not a directory."
                )
                return 1

            overall_quiz_count = 0
            overall_question_count = 0
            scanned_files_count = 0  # <<< ADD
            successful_files_count = 0  # <<< ADD
            failed_files_count = 0  # <<< ADD

            # Collect all pkl files first to count them
            pkl_files = list(
                default_import_dir_absolute.glob("*.pkl")
            )  # <<< CHANGE: Collect first
            scanned_files_count = len(pkl_files)  # <<< ADD
            logger.info(
                f"Scanned {scanned_files_count} .pkl files in the directory."
            )  # <<< ADD

            for pkl_file_path in pkl_files:  # <<< Use the collected list
                logger.info(f"Processing file: {pkl_file_path.name}")
                try:
                    df = load_quiz_bank(str(pkl_file_path))
                    if df is None:
                        logger.warning(
                            f"Skipping file {pkl_file_path.name} as it could not be loaded or was empty."
                        )
                        failed_files_count += 1  # <<< ADD
                        continue

                    quiz_count, question_count = import_questions_by_chapter(
                        df,
                        use_descriptive_titles=use_descriptive_titles,
                        use_chapter_prefix=use_chapter_prefix,
                        chapter_zfill=chapter_zfill_val,
                        cli_system_category_name=cli_system_category_arg,
                    )
                    overall_quiz_count += quiz_count  # <<< ADD
                    overall_question_count += question_count  # <<< ADD
                    if (
                        quiz_count > 0 or question_count > 0
                    ):  # Consider it successful if it resulted in quizzes/questions
                        successful_files_count += 1  # <<< ADD
                    logger.info(
                        f"Successfully processed {pkl_file_path.name}: Created {quiz_count} quizzes, {question_count} questions."
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to process file {pkl_file_path.name}: {e}",
                        exc_info=True,
                    )
                    failed_files_count += 1  # <<< ADD

            # --- Log summary ---
            logger.info("\n--- Directory Import Summary ---")  # <<< ADD
            logger.info(f"Total .pkl files scanned: {scanned_files_count}")  # <<< ADD
            logger.info(
                f"Successfully imported data from {successful_files_count} files."
            )  # <<< ADD
            if failed_files_count > 0:  # <<< ADD
                logger.warning(
                    f"Failed to process or skipped {failed_files_count} files."
                )  # <<< ADD
            logger.info(
                f"Total quizzes created from directory: {overall_quiz_count}"
            )  # <<< ADD
            logger.info(
                f"Total questions imported from directory: {overall_question_count}"
            )  # <<< ADD
            logger.info("---------------------------------")  # <<< ADD

            print_database_summary()
            return 0

        # Interactive mode (less common for this script)
        logger.info(
            "No --import-dir or --test flags. Entering interactive mode for a single file."
        )
        quiz_bank_path_input = input("Enter path to a single quiz bank .pkl file: ")
        df = load_quiz_bank(quiz_bank_path_input)
        if df is None:
            return 1
        quiz_count, question_count = import_questions_by_chapter(
            df,
            use_descriptive_titles=use_descriptive_titles,
            use_chapter_prefix=use_chapter_prefix,
            chapter_zfill=chapter_zfill_val,
            cli_system_category_name=cli_system_category_arg,  # Pass CLI arg
        )
        # ... (log summary for interactive) ...
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
