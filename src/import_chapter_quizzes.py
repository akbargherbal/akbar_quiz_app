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
    max_quizzes_per_chapter=5,  # New parameter for upper limit (NEED TO TEST)
    min_coverage_percentage=40,  # New parameter for minimum question coverage (NEED TO TEST)
    single_quiz_threshold=1.5,  # New parameter - if questions < threshold*questions_per_quiz, just make one quiz (NEED TO TEST)
    use_descriptive_titles=True,
    use_chapter_prefix=True,
    chapter_zfill=2,
):
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
            f"Creating quizzes with {questions_per_quiz} questions each, adapting quiz count based on available questions"
        )
        logger.info(f"Found {len(chapters)} chapters: {chapters}")

        # Process each chapter
        for chapter in chapters:
            try:
                # Filter to this chapter's questions
                chapter_df = df[df["chapter_no"] == chapter].copy()
                total_chapter_questions = len(chapter_df)
                logger.info(
                    f"Chapter {chapter}: {total_chapter_questions} questions available"
                )

                if total_chapter_questions == 0:
                    logger.warning(f"Chapter {chapter} has no questions, skipping")
                    continue

                # Determine dynamic quiz count based on available questions
                if total_chapter_questions < questions_per_quiz * single_quiz_threshold:
                    # Too few questions or just slightly more than needed for one quiz
                    # Create just one quiz with all available questions
                    chapter_quiz_count = 1
                    logger.info(
                        f"Chapter {chapter} has only {total_chapter_questions} questions "
                        + f"(less than {questions_per_quiz * single_quiz_threshold}). "
                        + "Creating a single quiz with all available questions."
                    )
                elif total_chapter_questions > questions_per_quiz * quizzes_per_chapter:
                    # Many questions - calculate how many quizzes needed for good coverage
                    min_questions_to_cover = int(
                        total_chapter_questions * (min_coverage_percentage / 100)
                    )
                    chapter_quiz_count = min(
                        max_quizzes_per_chapter,
                        (min_questions_to_cover + questions_per_quiz - 1)
                        // questions_per_quiz,
                    )
                    logger.info(
                        f"Chapter {chapter} has {total_chapter_questions} questions. Creating {chapter_quiz_count} quizzes to cover approximately {min_coverage_percentage}% of content."
                    )
                else:
                    # Default case - use standard number of quizzes
                    chapter_quiz_count = quizzes_per_chapter
                    logger.info(
                        f"Chapter {chapter} has {total_chapter_questions} questions. Creating standard {chapter_quiz_count} quizzes."
                    )

                # Create chapter prefix if enabled
                chapter_prefix = ""
                if use_chapter_prefix:
                    try:
                        # Try to convert chapter to integer for zfill
                        chapter_num = int(chapter)
                        chapter_prefix = str(chapter_num).zfill(chapter_zfill) + " "
                    except (ValueError, TypeError):
                        # If chapter is not a simple number, use as is
                        chapter_prefix = str(chapter) + " "
                    logger.info(f"Using chapter prefix: '{chapter_prefix}'")

                # Extract key metadata from DataFrame
                chapter_metadata = {}

                # Look for chapter title in either CHAPTER_TITLE or chapter_title columns
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

                logger.info(f"Chapter {chapter} title: {chapter_metadata['title']}")

                # Extract topic information if available
                if "topic" in chapter_df.columns:
                    # Get the most common topic(s) for this chapter
                    topic_counts = chapter_df["topic"].value_counts()
                    chapter_metadata["primary_topic"] = topic_counts.index[0]
                    if len(topic_counts) > 1:
                        chapter_metadata["secondary_topics"] = topic_counts.index[
                            1:3
                        ].tolist()
                    else:
                        chapter_metadata["secondary_topics"] = []

                    logger.info(f"Primary topic: {chapter_metadata['primary_topic']}")
                    if chapter_metadata["secondary_topics"]:
                        logger.info(
                            f"Secondary topics: {chapter_metadata['secondary_topics']}"
                        )

                # Extract tags if available
                if "tag" in chapter_df.columns:
                    chapter_metadata["tags"] = chapter_df["tag"].unique().tolist()
                    logger.info(f"Tags: {chapter_metadata['tags'][:5]}...")

                # Create a set to track which questions have been used
                used_question_indices = set()
                total_questions_used = 0

                # Process each quiz for this chapter
                for quiz_num in range(1, chapter_quiz_count + 1):
                    try:
                        # Create descriptive title and topic based on available metadata
                        if use_descriptive_titles and chapter_metadata.get(
                            "primary_topic"
                        ):
                            # Use chapter title and primary topic for a more descriptive title
                            title = f"{chapter_prefix}{chapter_metadata['title']}: {chapter_metadata['primary_topic']} - Quiz {quiz_num}"
                            topic_name = chapter_metadata["primary_topic"]
                        else:
                            # Fallback to simpler naming
                            title = f"{chapter_prefix}{chapter_metadata['title']} - Quiz {quiz_num}"
                            topic_name = chapter_metadata["title"]

                        # Sample questions for this quiz, avoiding already used questions if possible
                        available_df = chapter_df

                        # If we have more than enough questions, filter out previously used ones
                        if (
                            total_chapter_questions - total_questions_used
                            >= questions_per_quiz
                        ):
                            if used_question_indices:
                                available_df = chapter_df.iloc[
                                    list(
                                        set(range(len(chapter_df)))
                                        - used_question_indices
                                    )
                                ]

                        # Sample questions
                        sample_size = min(questions_per_quiz, len(available_df))
                        if sample_size < questions_per_quiz:
                            logger.warning(
                                f"Only {sample_size} unique questions available for {title}. Using all available."
                            )

                        quiz_sample = available_df.sample(sample_size)

                        # Track which questions we've used
                        used_indices = chapter_df.index.get_indexer(quiz_sample.index)
                        used_question_indices.update(used_indices)
                        total_questions_used += sample_size

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
