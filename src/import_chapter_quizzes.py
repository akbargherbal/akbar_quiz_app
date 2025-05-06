#!/usr/bin/env python
# src/import_chapter_quizzes.py
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

# Constants for formatting
CHAPTER_PREFIX_ENABLED = (
    True  # Default value, can be overridden with --no-chapter-prefix
)
CHAPTER_PREFIX_ZFILL = (
    2  # Default padding for chapter numbers, can be changed here or via argument
)

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
            "question_text",
            "options",
            "answerIndex",
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(
                f"Missing required columns in quiz bank: {', '.join(missing_columns)}"
            )

        # Log all available columns for reference
        logger.info(f"Available columns in quiz bank: {', '.join(df.columns.tolist())}")
        logger.info(f"Quiz bank loaded successfully with {len(df)} questions")
        logger.info(f"Chapters: {df['chapter_no'].nunique()} unique chapters")

        # Log chapter titles if available
        if "CHAPTER_TITLE" in df.columns:
            chapter_titles = df.groupby("chapter_no")["CHAPTER_TITLE"].first().to_dict()
            logger.info(f"Chapter titles: {chapter_titles}")
        elif "chapter_title" in df.columns:
            chapter_titles = df.groupby("chapter_no")["chapter_title"].first().to_dict()
            logger.info(f"Chapter titles: {chapter_titles}")

        # Log topic information if available
        if "topic" in df.columns:
            topics = df["topic"].unique().tolist()
            logger.info(f"Topics: {len(topics)} unique topics")
            if len(topics) <= 10:  # Only show if not too many
                logger.info(f"Topic values: {topics}")

        return df
    except Exception as e:
        logger.error(f"Failed to load quiz bank: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def import_questions_by_chapter(
    df,
    questions_per_quiz=20,
    quizzes_per_chapter=2,
    max_quizzes_per_chapter=5,
    min_coverage_percentage=40,
    single_quiz_threshold=1.3,
    use_descriptive_titles=True,
    use_chapter_prefix=True,
    chapter_zfill=2,
):
    """Import questions organized by chapter with comprehensive error handling."""
    if df is None:
        logger.error("Cannot import questions: DataFrame is None")
        return 0, 0  # Return counts

    try:
        quiz_count_total = 0
        question_count_total = 0

        chapters = sorted(df["chapter_no"].unique())
        logger.info(
            f"Processing {len(chapters)} chapters. Default settings: "
            f"{questions_per_quiz} questions/quiz, {quizzes_per_chapter} quizzes/chapter (target). "
            f"Max quizzes: {max_quizzes_per_chapter}, Min coverage: {min_coverage_percentage}%, "
            f"Single quiz threshold factor: {single_quiz_threshold}."
        )

        for chapter in chapters:
            try:
                chapter_df = df[df["chapter_no"] == chapter].copy()
                total_chapter_questions = len(chapter_df)
                logger.info(
                    f"\n--- Processing Chapter {chapter}: {total_chapter_questions} questions available ---"
                )

                if total_chapter_questions == 0:
                    logger.warning(f"Chapter {chapter} has no questions, skipping.")
                    continue

                # --- Determine Quiz Count and Questions Per Quiz ---
                # This logic block determines the plan for this chapter *before* the loop

                if total_chapter_questions < questions_per_quiz * single_quiz_threshold:
                    # Scenario 1: Very few questions -> create just one quiz
                    chapter_quiz_count = 1
                    # Use all available questions for this single quiz
                    sample_size_per_quiz = total_chapter_questions
                    logger.info(
                        f"Decision: Chapter {chapter} has only {total_chapter_questions} questions "
                        f"(threshold: {questions_per_quiz * single_quiz_threshold}). "
                        f"Creating a single quiz with all {sample_size_per_quiz} questions."
                    )
                else:
                    # Scenario 2 & 3: Enough questions for standard or more
                    # Start with the default number of quizzes
                    chapter_quiz_count = quizzes_per_chapter
                    sample_size_per_quiz = (
                        questions_per_quiz  # Aim for this many per quiz
                    )

                    # Check if we need *more* quizzes to meet coverage
                    min_questions_to_cover = int(
                        total_chapter_questions * (min_coverage_percentage / 100)
                    )
                    # Calculate how many quizzes are needed based on target sample size
                    required_quizzes_for_coverage = (
                        min_questions_to_cover + sample_size_per_quiz - 1
                    ) // sample_size_per_quiz

                    if required_quizzes_for_coverage > chapter_quiz_count:
                        # Increase quiz count if coverage requires it, up to the max
                        new_quiz_count = min(
                            max_quizzes_per_chapter, required_quizzes_for_coverage
                        )
                        logger.info(
                            f"Decision: Default {chapter_quiz_count} quizzes insufficient for {min_coverage_percentage}% coverage ({min_questions_to_cover} questions). "
                            f"Increasing quiz count to {new_quiz_count} (required: {required_quizzes_for_coverage}, max: {max_quizzes_per_chapter})."
                        )
                        chapter_quiz_count = new_quiz_count
                    else:
                        logger.info(
                            f"Decision: Default {chapter_quiz_count} quizzes sufficient for {min_coverage_percentage}% coverage. "
                            f"(Min needed: {min_questions_to_cover} questions)."
                        )

                    # Final cap (safety check, should be handled by min above)
                    chapter_quiz_count = min(
                        max_quizzes_per_chapter, chapter_quiz_count
                    )
                    logger.info(
                        f"Final plan for Chapter {chapter}: Create {chapter_quiz_count} quizzes, aiming for {sample_size_per_quiz} questions each."
                    )

                # --- Setup Chapter Metadata (Prefix, Title, Topic, etc.) ---
                chapter_prefix = ""
                if use_chapter_prefix:
                    try:
                        chapter_num = int(chapter)
                        chapter_prefix = str(chapter_num).zfill(chapter_zfill) + " "
                    except (ValueError, TypeError):
                        chapter_prefix = str(chapter) + " "
                    logger.info(f"Using chapter prefix: '{chapter_prefix}'")

                chapter_metadata = {}
                # Look for chapter title
                if "CHAPTER_TITLE" in chapter_df.columns:
                    chapter_metadata["title"] = (
                        chapter_df["CHAPTER_TITLE"].value_counts().index[0]
                    )
                elif "chapter_title" in chapter_df.columns:
                    chapter_metadata["title"] = (
                        chapter_df["chapter_title"].value_counts().index[0]
                    )
                else:
                    chapter_metadata["title"] = f"Chapter {chapter}"
                logger.info(f"Chapter title: {chapter_metadata['title']}")

                # Extract topic
                if "topic" in chapter_df.columns:
                    topic_counts = chapter_df["topic"].value_counts()
                    chapter_metadata["primary_topic"] = topic_counts.index[0]
                    logger.info(f"Primary topic: {chapter_metadata['primary_topic']}")

                # --- Create Quizzes for this Chapter ---
                used_question_indices = set()  # Track indices relative to chapter_df
                chapter_questions_used_count = 0

                for quiz_num in range(1, chapter_quiz_count + 1):
                    try:
                        # Determine title and topic for this specific quiz
                        if use_descriptive_titles and chapter_metadata.get(
                            "primary_topic"
                        ):
                            title = f"{chapter_prefix}{chapter_metadata['title']}: {chapter_metadata['primary_topic']} - Quiz {quiz_num}"
                            topic_name = chapter_metadata["primary_topic"]
                        else:
                            title = f"{chapter_prefix}{chapter_metadata['title']} - Quiz {quiz_num}"
                            topic_name = chapter_metadata["title"]  # Fallback topic

                        # Get questions available for sampling (not already used in this chapter)
                        # Indices in chapter_df that haven't been used yet
                        available_indices = list(
                            set(range(len(chapter_df))) - used_question_indices
                        )
                        if not available_indices:
                            logger.warning(
                                f"No more unique questions available in Chapter {chapter} for Quiz {quiz_num}. Stopping quiz creation for this chapter."
                            )
                            break  # Exit loop if no more questions

                        available_df = chapter_df.iloc[available_indices]

                        # --- Use the Correct Sample Size ---
                        # Use the sample_size_per_quiz calculated earlier
                        current_sample_size = min(
                            sample_size_per_quiz, len(available_df)
                        )

                        if (
                            current_sample_size < sample_size_per_quiz
                            and chapter_quiz_count == 1
                            and total_chapter_questions
                            < questions_per_quiz * single_quiz_threshold
                        ):
                            # This case is expected (using all available in single quiz) - don't warn
                            pass
                        elif current_sample_size < sample_size_per_quiz:
                            # Warn if we aimed for more but ran out of unique questions
                            logger.warning(
                                f"Only {current_sample_size} unique questions left for '{title}'. Expected {sample_size_per_quiz}. Using available."
                            )

                        # Sample the questions
                        quiz_sample_df = available_df.sample(current_sample_size)

                        # Update used indices (relative to the original chapter_df)
                        # Get the original indices from chapter_df corresponding to the sample
                        original_indices = chapter_df.index.get_indexer(
                            quiz_sample_df.index
                        )
                        used_question_indices.update(original_indices)
                        chapter_questions_used_count += current_sample_size

                        # Import using transaction
                        with transaction.atomic():
                            if Quiz.objects.filter(title=title).exists():
                                logger.warning(
                                    f"Quiz '{title}' already exists, skipping."
                                )
                                continue

                            logger.info(
                                f"Creating quiz '{title}' with {current_sample_size} questions (Topic: {topic_name})"
                            )
                            quiz = import_from_dataframe(
                                quiz_sample_df, title, topic_name
                            )

                            if quiz:
                                actual_count = quiz.question_count()
                                logger.info(
                                    f"Successfully created '{title}' with {actual_count} questions."
                                )
                                if actual_count != current_sample_size:
                                    logger.warning(
                                        f"Question count mismatch for '{title}': Expected {current_sample_size}, got {actual_count}."
                                    )
                                quiz_count_total += 1
                                question_count_total += actual_count
                            else:
                                logger.error(
                                    f"Failed to create quiz '{title}' - import_from_dataframe returned None."
                                )

                    except IntegrityError as e:
                        logger.error(
                            f"Database integrity error creating quiz '{title}': {str(e)}"
                        )
                        logger.error(traceback.format_exc())
                    except Exception as e:
                        logger.error(f"Error creating quiz '{title}': {str(e)}")
                        logger.error(traceback.format_exc())

                logger.info(
                    f"--- Finished Chapter {chapter}. Used {chapter_questions_used_count} questions out of {total_chapter_questions} available. ---"
                )

            except Exception as e:
                logger.error(f"Error processing Chapter {chapter}: {str(e)}")
                logger.error(traceback.format_exc())

        logger.info(f"\n=== Import Process Summary ===")
        logger.info(f"Total quizzes created: {quiz_count_total}")
        logger.info(f"Total questions imported: {question_count_total}")
        logger.info(f"==============================")

        return quiz_count_total, question_count_total

    except Exception as e:
        logger.error(f"Global error in import process: {str(e)}")
        logger.error(traceback.format_exc())
        return 0, 0  # Return zero counts on global error


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

        # Get the global constants as initial values
        use_descriptive_titles = True  # Default to using descriptive titles
        use_chapter_prefix = CHAPTER_PREFIX_ENABLED
        chapter_zfill = CHAPTER_PREFIX_ZFILL

        # Parse command line arguments
        test_mode = "--test" in sys.argv
        test_file = None

        # Look for arguments
        for i, arg in enumerate(sys.argv):
            if arg == "--test-file" and i + 1 < len(sys.argv):
                test_file = sys.argv[i + 1]
            elif arg == "--simple-titles":
                use_descriptive_titles = False
                logger.info("Using simple title format (without topic information)")
            elif arg == "--no-chapter-prefix":
                use_chapter_prefix = False
                logger.info("Disabling chapter number prefix in titles")
            elif arg == "--zfill" and i + 1 < len(sys.argv):
                try:
                    chapter_zfill = int(sys.argv[i + 1])
                    logger.info(
                        f"Setting chapter number padding to {chapter_zfill} digits"
                    )
                except ValueError:
                    logger.warning(
                        f"Invalid zfill value: {sys.argv[i + 1]}, using default {chapter_zfill}"
                    )

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
                    "tag": [
                        "test-topic-a",
                        "test-topic-b",
                        "test-topic-c",
                        "test-topic-d",
                        "test-topic-e",
                        "test-topic-f",
                    ],
                }
            )

            # Skip the load_quiz_bank call
            quiz_count, question_count = import_questions_by_chapter(
                df,
                questions_per_quiz=2,
                quizzes_per_chapter=1,
                use_descriptive_titles=use_descriptive_titles,
                use_chapter_prefix=use_chapter_prefix,
                chapter_zfill=chapter_zfill,
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
            df,
            questions_per_quiz=20,
            quizzes_per_chapter=2,
            use_descriptive_titles=use_descriptive_titles,
            use_chapter_prefix=use_chapter_prefix,
            chapter_zfill=chapter_zfill,
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
