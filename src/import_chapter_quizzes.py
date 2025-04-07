#!/usr/bin/env python
import os
import sys
import pandas as pd
import django
import traceback
import logging
from datetime import datetime

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

logger = logging.getLogger("quiz_import")

try:
    # Set up Django
    logger.info("Initializing Django...")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    from multi_choice_quiz.utils import import_from_dataframe
    from multi_choice_quiz.models import Quiz, Question, Option, Topic
    from django.db import transaction, DatabaseError, IntegrityError

    logger.info("Django initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Django: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)


def load_quiz_bank(file_path):
    """Load the quiz bank DataFrame with error handling."""
    try:
        logger.info(f"Loading quiz bank from: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Quiz bank file not found: {file_path}")

        df = pd.read_pickle(file_path)

        # Validate DataFrame structure
        required_columns = [
            "chapter_no",
            "topic",
            "question_text",
            "options",
            "answerIndex",
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(
                f"Missing required columns in quiz bank: {', '.join(missing_columns)}"
            )

        logger.info(f"Quiz bank loaded successfully with {len(df)} questions")
        logger.info(f"Topics: {df['topic'].nunique()} unique topics")
        logger.info(f"Chapters: {df['chapter_no'].nunique()} unique chapters")

        return df
    except Exception as e:
        logger.error(f"Failed to load quiz bank: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def import_questions_by_chapter(df, questions_per_quiz=20, quizzes_per_chapter=2):
    """Import questions organized by chapter with comprehensive error handling."""
    if df is None:
        logger.error("Cannot import questions: DataFrame is None")
        return

    try:
        quiz_count = 0
        question_count = 0

        # Get unique chapters
        chapters = sorted(df["chapter_no"].unique())
        logger.info(
            f"Creating {quizzes_per_chapter} quizzes per chapter, {questions_per_quiz} questions each"
        )
        logger.info(f"Found {len(chapters)} chapters: {chapters}")

        # Process each chapter
        for chapter in chapters:
            try:
                # Filter to this chapter's questions
                chapter_df = df[df["chapter_no"] == chapter].copy()
                logger.info(f"Chapter {chapter}: {len(chapter_df)} questions available")

                if len(chapter_df) == 0:
                    logger.warning(f"Chapter {chapter} has no questions, skipping")
                    continue

                # Process each quiz for this chapter
                for quiz_num in range(1, quizzes_per_chapter + 1):
                    try:
                        # Generate quiz title and topic
                        title = f"Chapter {chapter} - Quiz {quiz_num}"
                        topic_name = f"Chapter {chapter}"

                        # Sample questions for this quiz
                        sample_size = min(questions_per_quiz, len(chapter_df))
                        if sample_size < questions_per_quiz:
                            logger.warning(
                                f"Chapter {chapter} has fewer than {questions_per_quiz} questions. Using all {sample_size} available."
                            )

                        quiz_sample = chapter_df.sample(sample_size)

                        # Import using transaction to ensure atomicity
                        with transaction.atomic():
                            # Check if quiz already exists
                            if Quiz.objects.filter(title=title).exists():
                                logger.warning(
                                    f"Quiz '{title}' already exists, skipping"
                                )
                                continue

                            # Import the quiz
                            logger.info(
                                f"Creating {title} with {sample_size} questions"
                            )
                            quiz = import_from_dataframe(quiz_sample, title, topic_name)

                            if quiz:
                                # Verify the import
                                actual_count = quiz.question_count()
                                logger.info(
                                    f"Successfully created {title} with {actual_count} questions"
                                )

                                if actual_count != sample_size:
                                    logger.warning(
                                        f"Question count mismatch for {title}: Expected {sample_size}, got {actual_count}"
                                    )

                                quiz_count += 1
                                question_count += actual_count
                            else:
                                logger.error(
                                    f"Failed to create quiz {title} - import_from_dataframe returned None"
                                )

                    except IntegrityError as e:
                        logger.error(
                            f"Database integrity error creating quiz {title}: {str(e)}"
                        )
                        logger.error(traceback.format_exc())

                    except Exception as e:
                        logger.error(f"Error creating quiz {title}: {str(e)}")
                        logger.error(traceback.format_exc())

            except Exception as e:
                logger.error(f"Error processing Chapter {chapter}: {str(e)}")
                logger.error(traceback.format_exc())

        return quiz_count, question_count

    except Exception as e:
        logger.error(f"Global error in import process: {str(e)}")
        logger.error(traceback.format_exc())
        return 0, 0


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
        logger.info("Starting quiz import process...")

        # print current working directory
        logger.info(f"Current working directory: {os.getcwd()}")
        print(f"Current working directory: {os.getcwd()}")

        # Check for test mode arguments
        test_mode = "--test" in sys.argv
        test_file = None

        for i, arg in enumerate(sys.argv):
            if arg == "--test-file" and i + 1 < len(sys.argv):
                test_file = sys.argv[i + 1]

        # Determine quiz bank path
        if test_file:
            # Use provided test file
            quiz_bank_path = test_file
            logger.info(f"Running in test mode with provided file: {quiz_bank_path}")
        elif test_mode:
            # Create test data in memory
            logger.info("Running in test mode with generated data")
            df = pd.DataFrame(
                {
                    "chapter_no": [1, 1, 2, 2],
                    "topic": [
                        "Test Topic A",
                        "Test Topic B",
                        "Test Topic C",
                        "Test Topic D",
                    ],
                    "question_text": [
                        "Test question 1?",
                        "Test question 2?",
                        "Test question 3?",
                        "Test question 4?",
                    ],
                    "options": [
                        ["Option A", "Option B", "Option C"],
                        ["Option D", "Option E", "Option F"],
                        ["Option G", "Option H", "Option I"],
                        ["Option J", "Option K", "Option L"],
                    ],
                    "answerIndex": [1, 2, 3, 1],
                }
            )

            # Skip the load_quiz_bank call
            quiz_count, question_count = import_questions_by_chapter(
                df, questions_per_quiz=2, quizzes_per_chapter=1
            )

            # Print summary and exit
            logger.info("\nTest import completed")
            logger.info(
                f"Created {quiz_count} test quizzes with a total of {question_count} questions"
            )
            print_database_summary()
            logger.info(f"Log file saved to: {log_file}")
            return 0
        else:
            # Interactive mode - prompt user for path
            quiz_bank_path = input(
                "Enter the path to the quiz bank file (e.g., 'data/quiz_bank.pkl'): "
            )

        # Load the quiz bank
        df = load_quiz_bank(quiz_bank_path)
        if df is None:
            logger.error("Cannot proceed: Failed to load quiz bank")
            return 1

        # Import questions by chapter
        quiz_count, question_count = import_questions_by_chapter(
            df, questions_per_quiz=20, quizzes_per_chapter=2
        )

        # Print summary
        logger.info("\nImport process completed")
        logger.info(
            f"Created {quiz_count} quizzes with a total of {question_count} questions"
        )

        # Show database summary
        print_database_summary()

        logger.info(f"Log file saved to: {log_file}")
        return 0

    except Exception as e:
        logger.critical(f"Critical error in main process: {str(e)}")
        logger.critical(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
