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

# --- MODIFIED: Default directory for --import-dir ---
# This script (import_chapter_quizzes.py) is expected to be in 'src/'
# So, '../' from here goes to the project root (where manage.py is)
# Then, 'QUIZ_COLLECTIONS' is a directory at that project root level.
DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH = "../QUIZ_COLLECTIONS" 


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
                if total_chapter_questions < questions_per_quiz * single_quiz_threshold:
                    chapter_quiz_count = 1
                    sample_size_per_quiz = total_chapter_questions
                    logger.info(
                        f"Decision: Chapter {chapter} has only {total_chapter_questions} questions. Creating a single quiz."
                    )
                else:
                    chapter_quiz_count = quizzes_per_chapter
                    sample_size_per_quiz = questions_per_quiz
                    min_questions_to_cover = int(total_chapter_questions * (min_coverage_percentage / 100))
                    required_quizzes_for_coverage = (min_questions_to_cover + sample_size_per_quiz - 1) // sample_size_per_quiz
                    if required_quizzes_for_coverage > chapter_quiz_count:
                        new_quiz_count = min(max_quizzes_per_chapter, required_quizzes_for_coverage)
                        logger.info(f"Decision: Increasing quiz count for Chapter {chapter} to {new_quiz_count} for coverage.")
                        chapter_quiz_count = new_quiz_count
                    else:
                        logger.info(f"Decision: Using default {chapter_quiz_count} quizzes for Chapter {chapter}.")
                    chapter_quiz_count = min(max_quizzes_per_chapter, chapter_quiz_count)

                # --- Setup Chapter Metadata ---
                chapter_prefix = ""
                if use_chapter_prefix:
                    try:
                        chapter_prefix = str(int(chapter)).zfill(chapter_zfill) + " "
                    except (ValueError, TypeError):
                        chapter_prefix = str(chapter) + " "
                
                chapter_metadata = {}
                if "CHAPTER_TITLE" in chapter_df.columns:
                    chapter_metadata["title"] = chapter_df["CHAPTER_TITLE"].value_counts().index[0]
                elif "chapter_title" in chapter_df.columns:
                    chapter_metadata["title"] = chapter_df["chapter_title"].value_counts().index[0]
                else:
                    chapter_metadata["title"] = f"Chapter {chapter}"

                if "topic" in chapter_df.columns:
                    chapter_metadata["primary_topic"] = chapter_df["topic"].value_counts().index[0]

                # --- Create Quizzes for this Chapter ---
                used_question_indices = set()
                chapter_questions_used_count = 0

                for quiz_num in range(1, chapter_quiz_count + 1):
                    try:
                        if use_descriptive_titles and chapter_metadata.get("primary_topic"):
                            title = f"{chapter_prefix}{chapter_metadata['title']}: {chapter_metadata['primary_topic']} - Quiz {quiz_num}"
                            topic_name = chapter_metadata["primary_topic"]
                        else:
                            title = f"{chapter_prefix}{chapter_metadata['title']} - Quiz {quiz_num}"
                            topic_name = chapter_metadata["title"]

                        available_indices = list(set(range(len(chapter_df))) - used_question_indices)
                        if not available_indices:
                            logger.warning(f"No more unique questions in Chapter {chapter} for Quiz {quiz_num}.")
                            break
                        
                        available_df = chapter_df.iloc[available_indices]
                        current_sample_size = min(sample_size_per_quiz, len(available_df))
                        
                        if current_sample_size < sample_size_per_quiz and not (chapter_quiz_count == 1 and total_chapter_questions < questions_per_quiz * single_quiz_threshold):
                            logger.warning(f"Only {current_sample_size} unique questions left for '{title}'. Expected {sample_size_per_quiz}.")
                        
                        quiz_sample_df = available_df.sample(current_sample_size)
                        original_indices = chapter_df.index.get_indexer(quiz_sample_df.index)
                        used_question_indices.update(original_indices)
                        chapter_questions_used_count += current_sample_size

                        with transaction.atomic():
                            if Quiz.objects.filter(title=title).exists():
                                logger.warning(f"Quiz '{title}' already exists, skipping.")
                                continue
                            
                            quiz = import_from_dataframe(quiz_sample_df, title, topic_name)
                            if quiz:
                                actual_count = quiz.question_count()
                                logger.info(f"Successfully created '{title}' with {actual_count} questions.")
                                if actual_count != current_sample_size:
                                    logger.warning(f"Question count mismatch for '{title}': Expected {current_sample_size}, got {actual_count}.")
                                quiz_count_total += 1
                                question_count_total += actual_count
                            else:
                                logger.error(f"Failed to create quiz '{title}'.")
                    except IntegrityError as e:
                        logger.error(f"DB integrity error for quiz '{title}': {e}")
                    except Exception as e:
                        logger.error(f"Error creating quiz '{title}': {e}")
                logger.info(f"--- Finished Chapter {chapter}. Used {chapter_questions_used_count} questions. ---")
            except Exception as e:
                logger.error(f"Error processing Chapter {chapter}: {e}")
        
        logger.info(f"\n=== Import Process Summary (from current DataFrame) ===")
        logger.info(f"Total quizzes created: {quiz_count_total}")
        logger.info(f"Total questions imported: {question_count_total}")
        logger.info(f"======================================================")
        return quiz_count_total, question_count_total
    except Exception as e:
        logger.error(f"Global error in import process: {str(e)}")
        return 0,0


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
        script_dir = Path(__file__).resolve().parent # This is /path/to/project/src
        project_root = script_dir.parent # This is /path/to/project
        
        logger.info("Starting quiz import process...")
        logger.info(f"Script directory: {script_dir}")
        logger.info(f"Deduced project root: {project_root}")
        logger.info(f"Current working directory (os.getcwd()): {os.getcwd()}")

        use_descriptive_titles = True
        use_chapter_prefix = CHAPTER_PREFIX_ENABLED
        chapter_zfill = CHAPTER_PREFIX_ZFILL
        test_mode = "--test" in sys.argv
        test_file_path = None
        import_dir_flag = "--import-dir" in sys.argv

        for i, arg in enumerate(sys.argv):
            if arg == "--test-file" and i + 1 < len(sys.argv):
                test_file_path = sys.argv[i + 1]
            elif arg == "--simple-titles":
                use_descriptive_titles = False
            elif arg == "--no-chapter-prefix":
                use_chapter_prefix = False
            elif arg == "--zfill" and i + 1 < len(sys.argv):
                try:
                    chapter_zfill = int(sys.argv[i + 1])
                except ValueError:
                    logger.warning(f"Invalid zfill value: {sys.argv[i+1]}. Using default {chapter_zfill}.")
        
        if test_mode:
            logger.info("Running in test mode with generated data.")
            df = pd.DataFrame( # Sample data for testing
                {
                    "chapter_no": [1, 1, 2, 2, 10, 10],
                    "topic": ["Test Topic A", "Test Topic B", "Test Topic C", "Test Topic D", "Advanced Testing", "Advanced Testing"],
                    "question_text": ["Test question 1?", "Test question 2?", "Test question 3?", "Test question 4?", "Test question 5?", "Test question 6?"],
                    "options": [["Option A", "Option B", "Option C"], ["Option D", "Option E", "Option F"], ["Option G", "Option H", "Option I"], ["Option J", "Option K", "Option L"], ["Option M", "Option N", "Option O"], ["Option P", "Option Q", "Option R"]],
                    "answerIndex": [1, 2, 3, 1, 2, 3],
                    "CHAPTER_TITLE": ["Introduction to Testing", "Introduction to Testing", "Advanced Testing", "Advanced Testing", "Expert Testing", "Expert Testing"],
                    "tag": ["test-topic-a", "test-topic-b", "test-topic-c", "test-topic-d", "test-topic-e", "test-topic-f"],
                }
            )
            quiz_count, question_count = import_questions_by_chapter(
                df, questions_per_quiz=2, quizzes_per_chapter=1,
                use_descriptive_titles=use_descriptive_titles,
                use_chapter_prefix=use_chapter_prefix, chapter_zfill=chapter_zfill
            )
            logger.info(f"\nTest import completed. Created {quiz_count} test quizzes, {question_count} questions.")
            print_database_summary()
            return 0

        if test_file_path:
            logger.info(f"Running in test mode with provided file: {test_file_path}")
            df = load_quiz_bank(test_file_path)
            if df is None: return 1
            quiz_count, question_count = import_questions_by_chapter(
                df, use_descriptive_titles=use_descriptive_titles,
                use_chapter_prefix=use_chapter_prefix, chapter_zfill=chapter_zfill
            )
            logger.info(f"\nTest file import completed. Created {quiz_count} quizzes, {question_count} questions.")
            print_database_summary()
            return 0

        if import_dir_flag:
            # --- MODIFIED: Construct absolute path for the default import directory ---
            default_import_dir_absolute = (project_root / DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH).resolve()
            
            logger.info(f"Directory import mode. Processing .pkl files from: {default_import_dir_absolute}")

            if not default_import_dir_absolute.is_dir():
                logger.error(f"Default import directory '{default_import_dir_absolute}' not found or is not a directory. Please create it or check the path.")
                logger.error(f"Expected structure: Your project root should contain a folder named 'QUIZ_COLLECTIONS'.")
                logger.error(f"Project root detected as: {project_root}")
                return 1

            overall_quiz_count = 0
            overall_question_count = 0
            processed_files = 0
            successful_file_imports = 0

            for pkl_file_path in default_import_dir_absolute.glob("*.pkl"):
                logger.info(f"\n--- Processing file: {pkl_file_path.name} ---")
                processed_files += 1
                try:
                    df = load_quiz_bank(str(pkl_file_path))
                    if df is None:
                        logger.error(f"Skipping file {pkl_file_path.name} due to loading errors.")
                        continue
                    
                    quiz_count, question_count = import_questions_by_chapter(
                        df, use_descriptive_titles=use_descriptive_titles,
                        use_chapter_prefix=use_chapter_prefix, chapter_zfill=chapter_zfill
                    )
                    
                    overall_quiz_count += quiz_count
                    overall_question_count += question_count
                    if quiz_count > 0: successful_file_imports +=1
                except Exception as e:
                    logger.error(f"Failed to process file {pkl_file_path.name}: {e}")
            
            logger.info(f"\n--- Directory Import Overall Summary ---")
            logger.info(f"Scanned {processed_files} .pkl files in '{default_import_dir_absolute}'.")
            logger.info(f"Successfully imported data from {successful_file_imports} files.")
            logger.info(f"Total quizzes created from directory: {overall_quiz_count}")
            logger.info(f"Total questions imported from directory: {overall_question_count}")
            print_database_summary()
            return 0
            
        logger.info("Entering interactive mode.")
        quiz_bank_path_input = input("Enter the path to the quiz bank file (e.g., 'data/quiz_bank.pkl'): ")
        df = load_quiz_bank(quiz_bank_path_input)
        if df is None: return 1
        quiz_count, question_count = import_questions_by_chapter(
            df, use_descriptive_titles=use_descriptive_titles,
            use_chapter_prefix=use_chapter_prefix, chapter_zfill=chapter_zfill
        )
        logger.info(f"\nInteractive import completed. Created {quiz_count} quizzes, {question_count} questions.")
        print_database_summary()
        return 0
    except Exception as e:
        logger.critical(f"Critical error in main process: {str(e)}")
        return 1
    finally:
        logger.info(f"Log file saved to: {log_file}")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)