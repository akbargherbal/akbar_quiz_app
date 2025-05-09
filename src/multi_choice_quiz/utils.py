# src/multi_choice_quiz/utils.py

import json
import pandas as pd
from typing import List, Dict, Any, Optional
import logging  # <<< ADDED for utils logger
import os  # <<< ADDED for load_quiz_bank

# sys is not directly used by the functions here, but was in the scripts for their loggers

# Django specific imports needed by the new functions
from django.db import transaction, IntegrityError
from .models import Quiz, Question, Option, Topic
from .transform import (
    quiz_bank_to_models,
)  # Already present, used by import_from_dataframe

# --- Initialize a logger for this utils module ---
logger = logging.getLogger(__name__)


# --- Existing import_from_dataframe function (assumed to be here) ---
# This function is called by the new import_questions_by_chapter
def import_from_dataframe(
    df: pd.DataFrame,
    quiz_title: str,
    topic_name: Optional[str] = None,
    sample_size: Optional[int] = None,
) -> Quiz:
    """
    Import quiz data from a pandas DataFrame.

    Args:
        df: DataFrame containing quiz data
        quiz_title: Title for the new quiz
        topic_name: Optional topic name to associate with the quiz
        sample_size: Optional number of questions to sample from the DataFrame

    Returns:
        The created Quiz instance
    """
    # Make a copy to avoid modifying the original dataframe
    df = df.copy()

    # Check if the DataFrame has the required columns
    required_columns = ["text", "options", "answerIndex"]
    for col in required_columns:
        if col not in df.columns:
            # Try to map some common column names
            if col == "text" and "question_text" in df.columns:
                df = df.rename(columns={"question_text": "text"})
            elif col == "answerIndex" and "correct_answer" in df.columns:
                df = df.rename(columns={"correct_answer": "answerIndex"})
            else:
                raise ValueError(f"DataFrame is missing required column: {col}")

    # Sample the data if requested
    if sample_size and sample_size < len(df):
        df = df.sample(sample_size)

    # Convert DataFrame to list of dictionaries
    quiz_data = df.to_dict("records")

    # Ensure options is a list not a string (in case it was serialized)
    for item in quiz_data:
        if isinstance(item["options"], str):
            try:
                item["options"] = json.loads(item["options"])
            except json.JSONDecodeError:
                # Try to handle comma-separated options
                item["options"] = [opt.strip() for opt in item["options"].split(",")]

    # Create the quiz using our transform function
    return quiz_bank_to_models(quiz_data, quiz_title, topic_name)


# --- Existing curate_data function (assumed to be here) ---
def curate_data(input_df, no_questions=10):
    """
    Create a subset of questions from the input DataFrame in the format expected by the quiz bank.
    This matches the format shown in your example.

    Args:
        input_df: DataFrame containing quiz data
        no_questions: Number of questions to sample

    Returns:
        List of dictionaries in quiz bank format
    """
    # Make a copy to avoid modifying the original DataFrame
    df = input_df.copy()

    # Ensure the DataFrame has the required columns, rename if necessary
    if "question_text" in df.columns and "text" not in df.columns:
        df = df.rename(columns={"question_text": "text"})

    if "correct_answer" in df.columns and "answerIndex" not in df.columns:
        df = df.rename(columns={"correct_answer": "answerIndex"})

    # Select required columns - now including tag and chapter_no if available
    base_columns = ["text", "options", "answerIndex"]
    extra_columns = ["tag", "chapter_no", "topic", "CHAPTER_TITLE"]

    # Get available base columns (required)
    available_base_columns = [col for col in base_columns if col in df.columns]

    # Get available extra columns (optional)
    available_extra_columns = [col for col in extra_columns if col in df.columns]

    # Check for required columns
    if len(available_base_columns) < len(base_columns):
        missing = set(base_columns) - set(available_base_columns)
        raise ValueError(f"DataFrame is missing required columns: {missing}")

    # Combine all available columns
    columns_to_use = available_base_columns + available_extra_columns

    # Sample and convert to dict
    result = df[columns_to_use].sample(min(no_questions, len(df))).to_dict("records")
    return result


# --- NEW: Moved from import_chapter_quizzes.py / dir_import_chapter_quizzes.py ---
def load_quiz_bank(file_path: str) -> Optional[pd.DataFrame]:
    """
    Load the quiz bank DataFrame with error handling.
    Reads a .pkl file.
    """
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

        logger.info(f"Available columns in quiz bank: {', '.join(df.columns.tolist())}")
        logger.info(f"Quiz bank loaded successfully with {len(df)} questions")
        logger.info(f"Chapters: {df['chapter_no'].nunique()} unique chapters")

        if "CHAPTER_TITLE" in df.columns:
            chapter_titles = df.groupby("chapter_no")["CHAPTER_TITLE"].first().to_dict()
            logger.info(f"Chapter titles (from CHAPTER_TITLE): {chapter_titles}")
        elif "chapter_title" in df.columns:  # Check for lowercase alternative
            chapter_titles = df.groupby("chapter_no")["chapter_title"].first().to_dict()
            logger.info(f"Chapter titles (from chapter_title): {chapter_titles}")

        if "topic" in df.columns:
            topics = df["topic"].unique().tolist()
            logger.info(f"Topics: {len(topics)} unique topics")
            if len(topics) <= 10:
                logger.info(f"Topic values: {topics}")

        return df
    except FileNotFoundError:  # Specific exception first
        logger.error(f"File not found: {file_path}")
        raise  # Re-raise to be handled by caller script's main try-except if needed
    except ValueError as ve:  # For missing columns
        logger.error(f"Validation error loading quiz bank: {str(ve)}")
        raise  # Re-raise
    except Exception as e:
        logger.error(
            f"Failed to load quiz bank due to an unexpected error: {str(e)}",
            exc_info=True,
        )
        return None  # Or re-raise, depending on desired handling by caller


# --- NEW: Moved from import_chapter_quizzes.py (preferred version) ---
def import_questions_by_chapter(
    df: pd.DataFrame,
    questions_per_quiz: int = 20,
    quizzes_per_chapter: int = 2,
    max_quizzes_per_chapter: int = 5,
    min_coverage_percentage: int = 40,
    single_quiz_threshold: float = 1.3,
    use_descriptive_titles: bool = True,
    use_chapter_prefix: bool = True,
    chapter_zfill: int = 2,
) -> tuple[int, int]:
    """
    Import questions from a DataFrame, organized by chapter, into the database.

    Args:
        df: Pandas DataFrame containing the quiz questions.
            Required columns: 'chapter_no', 'question_text', 'options', 'answerIndex'.
            Optional columns: 'CHAPTER_TITLE' or 'chapter_title', 'topic'.
        questions_per_quiz: Target number of questions for each generated quiz.
        quizzes_per_chapter: Target number of quizzes to generate per chapter.
        max_quizzes_per_chapter: Maximum number of quizzes to generate for any single chapter.
        min_coverage_percentage: Minimum percentage of a chapter's questions to be included
                                 across all quizzes for that chapter.
        single_quiz_threshold: Factor based on 'questions_per_quiz'. If a chapter has
                               fewer questions than questions_per_quiz * single_quiz_threshold,
                               only one quiz will be made for that chapter.
        use_descriptive_titles: If True, include topic in quiz titles.
        use_chapter_prefix: If True, prefix quiz titles with chapter number.
        chapter_zfill: Padding for chapter number prefix.

    Returns:
        A tuple (total_quizzes_created, total_questions_imported).
    """
    if df is None:
        logger.error("Cannot import questions: DataFrame is None.")
        return 0, 0

    total_quizzes_created = 0
    total_questions_imported = 0

    # Ensure 'question_text' column exists, mapping from 'text' if necessary
    # This is handled by `import_from_dataframe`'s internal call to `quiz_bank_to_models`,
    # which expects 'text' or 'question_text'. The `load_quiz_bank` already validated 'question_text'.

    try:
        chapters = sorted(df["chapter_no"].unique())
        logger.info(
            f"Processing {len(chapters)} chapters. Target: {questions_per_quiz}Q/quiz, "
            f"{quizzes_per_chapter} quizzes/chapter. Max quizzes: {max_quizzes_per_chapter}. "
            f"Min coverage: {min_coverage_percentage}%. Single quiz factor: {single_quiz_threshold}."
        )

        for chapter in chapters:
            chapter_df = df[df["chapter_no"] == chapter].copy()
            num_chapter_questions = len(chapter_df)
            logger.info(
                f"\n--- Chapter {chapter}: {num_chapter_questions} questions available ---"
            )

            if num_chapter_questions == 0:
                logger.warning(f"Chapter {chapter}: No questions. Skipping.")
                continue

            # Determine quiz count and sample size for this chapter
            if num_chapter_questions < questions_per_quiz * single_quiz_threshold:
                actual_quizzes_for_chapter = 1
                actual_questions_per_quiz = num_chapter_questions
                logger.info(
                    f"Chapter {chapter}: Low question count ({num_chapter_questions}). "
                    f"Creating 1 quiz with all {actual_questions_per_quiz} questions."
                )
            else:
                actual_quizzes_for_chapter = quizzes_per_chapter
                actual_questions_per_quiz = questions_per_quiz

                min_questions_to_cover = int(
                    num_chapter_questions * (min_coverage_percentage / 100)
                )
                required_quizzes_for_coverage = (
                    min_questions_to_cover + actual_questions_per_quiz - 1
                ) // actual_questions_per_quiz

                if required_quizzes_for_coverage > actual_quizzes_for_chapter:
                    new_quiz_count = min(
                        max_quizzes_per_chapter, required_quizzes_for_coverage
                    )
                    logger.info(
                        f"Chapter {chapter}: Default {actual_quizzes_for_chapter} quizzes insufficient "
                        f"for {min_coverage_percentage}% coverage ({min_questions_to_cover} questions). "
                        f"Adjusting to {new_quiz_count} quizzes (required: {required_quizzes_for_coverage}, max: {max_quizzes_per_chapter})."
                    )
                    actual_quizzes_for_chapter = new_quiz_count
                else:
                    logger.info(
                        f"Chapter {chapter}: Default {actual_quizzes_for_chapter} quizzes sufficient "
                        f"for {min_coverage_percentage}% coverage. "
                        f"(Min needed: {min_questions_to_cover} questions)."
                    )
                actual_quizzes_for_chapter = min(
                    max_quizzes_per_chapter, actual_quizzes_for_chapter
                )
                logger.info(
                    f"Chapter {chapter}: Final plan: {actual_quizzes_for_chapter} quizzes, "
                    f"aiming for {actual_questions_per_quiz} questions each."
                )

            # Prepare chapter metadata
            chapter_prefix_str = ""
            if use_chapter_prefix:
                try:
                    chapter_prefix_str = str(int(chapter)).zfill(chapter_zfill) + " "
                except (ValueError, TypeError):
                    chapter_prefix_str = str(chapter) + " "
                logger.debug(f"Chapter {chapter}: Using prefix '{chapter_prefix_str}'.")

            chapter_title_base = f"Chapter {chapter}"
            if "CHAPTER_TITLE" in chapter_df.columns:
                chapter_title_base = chapter_df["CHAPTER_TITLE"].value_counts().index[0]
            elif "chapter_title" in chapter_df.columns:
                chapter_title_base = chapter_df["chapter_title"].value_counts().index[0]
            logger.debug(f"Chapter {chapter}: Base title '{chapter_title_base}'.")

            primary_topic_name = chapter_title_base  # Fallback topic
            if "topic" in chapter_df.columns:
                topic_counts = chapter_df["topic"].value_counts()
                if not topic_counts.empty:
                    primary_topic_name = topic_counts.index[0]
            logger.debug(f"Chapter {chapter}: Primary topic '{primary_topic_name}'.")

            # Create quizzes for this chapter
            used_question_indices = set()
            chapter_questions_imported_count = 0

            for quiz_num in range(1, actual_quizzes_for_chapter + 1):
                quiz_df_indices = list(
                    set(range(len(chapter_df))) - used_question_indices
                )
                if not quiz_df_indices:
                    logger.warning(
                        f"Chapter {chapter}, Quiz {quiz_num}: No more unique questions. Stopping."
                    )
                    break

                available_for_sampling_df = chapter_df.iloc[quiz_df_indices]
                current_sample_size = min(
                    actual_questions_per_quiz, len(available_for_sampling_df)
                )

                if current_sample_size < actual_questions_per_quiz and not (
                    actual_quizzes_for_chapter == 1
                    and num_chapter_questions
                    < questions_per_quiz * single_quiz_threshold
                ):
                    logger.warning(
                        f"Chapter {chapter}, Quiz {quiz_num}: Only {current_sample_size} unique "
                        f"questions left. Expected {actual_questions_per_quiz}."
                    )

                quiz_sample_df = available_for_sampling_df.sample(n=current_sample_size)

                # Get original DataFrame indices to mark as used
                original_indices_for_sample = chapter_df.index.get_indexer(
                    quiz_sample_df.index
                )
                used_question_indices.update(original_indices_for_sample)

                # Construct quiz title
                if (
                    use_descriptive_titles and "topic" in chapter_df.columns
                ):  # Use primary_topic_name already derived
                    quiz_final_title = f"{chapter_prefix_str}{chapter_title_base}: {primary_topic_name} - Quiz {quiz_num}"
                    quiz_topic_name_for_import = primary_topic_name
                else:
                    quiz_final_title = (
                        f"{chapter_prefix_str}{chapter_title_base} - Quiz {quiz_num}"
                    )
                    quiz_topic_name_for_import = primary_topic_name  # Fallback to chapter title or its derivative

                try:
                    with transaction.atomic():
                        if Quiz.objects.filter(title=quiz_final_title).exists():
                            logger.warning(
                                f"Quiz '{quiz_final_title}' already exists. Skipping."
                            )
                            continue

                        logger.info(
                            f"Creating quiz '{quiz_final_title}' with {current_sample_size} questions (Topic: {quiz_topic_name_for_import})."
                        )
                        # Call existing import_from_dataframe (which uses quiz_bank_to_models)
                        quiz = import_from_dataframe(
                            quiz_sample_df,
                            quiz_final_title,
                            topic_name=quiz_topic_name_for_import,
                            # No sample_size here, as we've already sampled
                        )
                        if quiz:
                            num_actually_imported = quiz.question_count()
                            logger.info(
                                f"Successfully created '{quiz_final_title}' with {num_actually_imported} questions."
                            )
                            if num_actually_imported != current_sample_size:
                                logger.warning(
                                    f"Mismatch for '{quiz_final_title}': Expected {current_sample_size}, got {num_actually_imported}."
                                )
                            total_quizzes_created += 1
                            total_questions_imported += num_actually_imported
                            chapter_questions_imported_count += num_actually_imported
                        else:
                            logger.error(f"Failed to create quiz '{quiz_final_title}'.")
                except IntegrityError as e:
                    logger.error(
                        f"DB integrity error for quiz '{quiz_final_title}': {e}",
                        exc_info=True,
                    )
                except Exception as e:
                    logger.error(
                        f"Error creating quiz '{quiz_final_title}': {e}", exc_info=True
                    )

            logger.info(
                f"--- Chapter {chapter} processing finished. Imported {chapter_questions_imported_count} questions "
                f"out of {num_chapter_questions} available into {actual_quizzes_for_chapter} planned quiz(zes). ---"
            )

        logger.info(f"\n=== Import Process Summary ===")
        logger.info(f"Total quizzes created: {total_quizzes_created}")
        logger.info(f"Total questions imported: {total_questions_imported}")
        logger.info(f"==============================")
        return total_quizzes_created, total_questions_imported

    except Exception as e:
        logger.error(
            f"Global error in import_questions_by_chapter: {str(e)}", exc_info=True
        )
        return 0, 0
