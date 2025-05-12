# src/multi_choice_quiz/utils.py

import json
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
import os

from django.db import transaction, IntegrityError

# --- SystemCategory IMPORT ---
from pages.models import SystemCategory
from .models import Quiz, Question, Option, Topic

# --- END SystemCategory IMPORT ---

from .transform import (
    quiz_bank_to_models,
)  # This line might seem circular now, but it's if other parts of transform.py were to call this file.

# Given the current structure, quiz_bank_to_models is defined below.
# If quiz_bank_to_models was *only* in transform.py previously,
# and we are moving its *definition* here, then this import in utils.py
# for itself is not needed. We'll define it fresh below.

logger = logging.getLogger(__name__)


# --- REFACTORED FUNCTION ---
def quiz_bank_to_models(
    quiz_data: List[Dict[str, Any]], quiz_title: str, topic_name: Optional[str] = None
) -> Quiz:
    """
    Transform quiz bank data into database models using bulk_create for efficiency.
    Handles the 1-based to 0-based index conversion internally for options.

    Args:
        quiz_data: List of dictionaries, each representing a question.
                   Expected keys: 'text' (or 'question_text'), 'options' (list of strings),
                                  'answerIndex' (1-based), optionally 'tag', 'chapter_no'.
        quiz_title: Title for the new quiz.
        topic_name: Optional topic name to associate with the quiz.

    Returns:
        The created Quiz instance.
    """
    topic_instance = None
    if topic_name:
        topic_instance, _ = Topic.objects.get_or_create(name=topic_name)

    quiz_instance = None  # Initialize quiz_instance

    with transaction.atomic():
        quiz_instance = Quiz.objects.create(title=quiz_title)
        if topic_instance:
            quiz_instance.topics.add(topic_instance)

        questions_to_create = []
        # Store a mapping: (original question text, original position in quiz_data) -> prepared Question object (before saving)
        # This helps map back to the original data structure when creating options.
        # We use a tuple of (text, index) as a key assuming question text within a single quiz_data batch is unique enough for this.
        # A more robust key might be needed if question texts can be identical within the same import batch.
        # For now, using original index in quiz_data for disambiguation if needed.
        prepared_questions_map = {}

        for i, item_data in enumerate(quiz_data):
            question_text = item_data.get("question_text", item_data.get("text", ""))
            prepared_q = Question(
                quiz=quiz_instance,  # Temporarily assign quiz_instance, will be set by bulk_create through quiz_id
                topic=topic_instance,
                text=question_text,
                position=i + 1,  # 1-based position in the quiz
                chapter_no=item_data.get("chapter_no", ""),
                tag=item_data.get("tag", ""),
            )
            questions_to_create.append(prepared_q)
            # Key by (text, original_index) to handle potential duplicate texts in the input batch
            prepared_questions_map[(question_text, i)] = prepared_q

        if not questions_to_create:
            logger.warning(
                f"No questions found in quiz_data for quiz '{quiz_title}'. Quiz created empty."
            )
            return quiz_instance  # Return the empty quiz

        # Bulk create questions.
        # For PostgreSQL, IDs will be set on instances. For SQLite, they might not be.
        Question.objects.bulk_create(questions_to_create)
        logger.info(
            f"Bulk created {len(questions_to_create)} question shells for quiz '{quiz_title}'."
        )

        # Re-fetch the questions to ensure we have their database IDs,
        # especially important for SQLite.
        # We order by position to attempt a stable order for matching.
        created_questions_from_db = list(
            Question.objects.filter(quiz=quiz_instance).order_by("position")
        )

        if len(created_questions_from_db) != len(questions_to_create):
            logger.error(
                f"Mismatch after bulk_create for quiz '{quiz_title}': "
                f"Expected {len(questions_to_create)} questions, "
                f"fetched {len(created_questions_from_db)} from DB. Aborting option creation for this quiz."
            )
            # This state is problematic, raising an error or returning early might be best.
            # For now, we'll log and continue, which means options might not be created correctly.
            # A more robust solution might raise an exception here.
            # raise Exception(f"Question count mismatch after bulk_create for quiz {quiz_title}")
            return quiz_instance  # Or handle error more gracefully

        options_to_create = []
        for i, original_item_data in enumerate(quiz_data):
            # Find the corresponding question from the database using its position.
            # This relies on 'position' being correctly set and unique within the quiz during creation.
            db_question = None
            for q_from_db in created_questions_from_db:
                if q_from_db.position == (i + 1):  # Match by 1-based position
                    db_question = q_from_db
                    break

            if not db_question:
                logger.warning(
                    f"Could not find matching DB question for item at original index {i} (position {i+1}) "
                    f"for quiz '{quiz_title}'. Skipping its options."
                )
                continue

            correct_answer_index_1_based = original_item_data[
                "answerIndex"
            ]  # This is 1-based from source

            options_data = original_item_data["options"]
            if not isinstance(options_data, list):
                logger.warning(
                    f"Options for question '{db_question.text}' are not a list, skipping. Data: {options_data}"
                )
                continue

            for opt_idx, option_text in enumerate(options_data):
                option_position_1_based = opt_idx + 1  # Option position is 1-based
                is_correct = option_position_1_based == correct_answer_index_1_based

                options_to_create.append(
                    Option(
                        question=db_question,  # Link to the question instance that has a DB ID
                        text=option_text,
                        position=option_position_1_based,
                        is_correct=is_correct,
                    )
                )

        if options_to_create:
            Option.objects.bulk_create(options_to_create)
            logger.info(
                f"Bulk created {len(options_to_create)} options for quiz '{quiz_title}'."
            )
        else:
            logger.info(
                f"No options to create for quiz '{quiz_title}' (either no questions or questions had no options)."
            )

    return quiz_instance


# --- END REFACTORED FUNCTION ---


# Keep other functions in utils.py as they are, they should call the refactored quiz_bank_to_models
# For example, import_from_dataframe, curate_data, load_quiz_bank, import_questions_by_chapter


def import_from_dataframe(
    df: pd.DataFrame,
    quiz_title: str,
    topic_name: Optional[str] = None,
    sample_size: Optional[int] = None,
    system_category_name: Optional[str] = None,
) -> Quiz:
    df = df.copy()
    required_columns = ["text", "options", "answerIndex"]
    # Try to map common alternative column names
    column_mapping = {
        "question_text": "text",
        "correct_answer": "answerIndex",
        # Add other potential mappings here
    }
    df.rename(columns=column_mapping, inplace=True)

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"DataFrame is missing required column: {col}")

    if sample_size and sample_size < len(df):
        logger.info(
            f"Sampling {sample_size} questions from DataFrame for quiz '{quiz_title}'."
        )
        df = df.sample(
            n=sample_size, random_state=1
        )  # Added random_state for reproducibility if needed

    quiz_data_records = df.to_dict("records")

    # Ensure options are lists (handle JSON strings or comma-separated strings)
    for item in quiz_data_records:
        if "options" in item and isinstance(item["options"], str):
            try:
                # Attempt to parse as JSON first
                parsed_options = json.loads(item["options"])
                if isinstance(parsed_options, list):
                    item["options"] = parsed_options
                else:
                    # If JSON parsed but not a list, fallback to comma-separated
                    logger.warning(
                        f"JSON options for '{item.get('text', 'Unknown Question')}' was not a list, trying comma split."
                    )
                    item["options"] = [
                        opt.strip() for opt in item["options"].split(",")
                    ]
            except json.JSONDecodeError:
                # If JSON parsing fails, assume comma-separated
                item["options"] = [opt.strip() for opt in item["options"].split(",")]
        elif "options" not in item or not isinstance(item["options"], list):
            logger.warning(
                f"Missing or invalid options for question '{item.get('text', 'Unknown Question')}'. Setting to empty list."
            )
            item["options"] = []  # Ensure options key exists and is a list

    # Call the (now refactored) quiz_bank_to_models
    quiz = quiz_bank_to_models(
        quiz_data_records, quiz_title, topic_name
    )  # This now uses bulk_create

    if quiz and system_category_name:
        try:
            category_obj, created = SystemCategory.objects.get_or_create(
                name=system_category_name
            )
            if created:
                logger.info(
                    f"Created new SystemCategory: '{system_category_name}' during import."
                )
            quiz.system_categories.add(category_obj)
            logger.info(
                f"Associated quiz '{quiz.title}' with SystemCategory '{category_obj.name}'."
            )
        except Exception as e:
            logger.error(
                f"Error associating quiz '{quiz.title}' with SystemCategory '{system_category_name}': {e}",
                exc_info=True,
            )
    return quiz


def curate_data(input_df, no_questions=10):
    df = input_df.copy()
    # Standardize column names for 'text' and 'answerIndex'
    if "question_text" in df.columns and "text" not in df.columns:
        df = df.rename(columns={"question_text": "text"})
    if "correct_answer" in df.columns and "answerIndex" not in df.columns:
        df = df.rename(columns={"correct_answer": "answerIndex"})

    # Define base required columns and optional columns to preserve
    base_columns = ["text", "options", "answerIndex"]
    extra_columns = ["tag", "chapter_no", "topic", "CHAPTER_TITLE", "system_category"]

    # Check for missing base columns
    missing_base_cols = [col for col in base_columns if col not in df.columns]
    if missing_base_cols:
        raise ValueError(
            f"DataFrame is missing required columns for curation: {', '.join(missing_base_cols)}"
        )

    # Determine which of the optional columns are actually present in the DataFrame
    available_extra_columns = [col for col in extra_columns if col in df.columns]

    columns_to_use = base_columns + available_extra_columns

    # Ensure we don't try to sample more than available rows
    sample_n = min(no_questions, len(df))
    if (
        sample_n == 0 and len(df) > 0
    ):  # If no_questions is 0, but df has rows, sample 0.
        return []
    if len(df) == 0:  # If df is empty, return empty list.
        return []

    result = df[columns_to_use].sample(n=sample_n, random_state=1).to_dict("records")
    return result


def load_quiz_bank(file_path: str) -> Optional[pd.DataFrame]:
    try:
        logger.info(f"Loading quiz bank from: {file_path}")
        if not os.path.exists(file_path):
            # Log and raise FileNotFoundError to be caught by calling scripts
            logger.error(f"Quiz bank file not found: {file_path}")
            raise FileNotFoundError(f"Quiz bank file not found: {file_path}")

        df = pd.read_pickle(file_path)

        # Define required columns for a quiz bank .pkl file
        # These are typically expected by import_questions_by_chapter
        required_columns = ["chapter_no", "question_text", "options", "answerIndex"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            err_msg = f"Missing required columns in quiz bank pickle file ('{file_path}'): {', '.join(missing_columns)}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        logger.info(f"Available columns in quiz bank: {', '.join(df.columns.tolist())}")
        logger.info(f"Quiz bank loaded successfully with {len(df)} questions")

        unique_chapters = df["chapter_no"].unique()
        logger.info(
            f"Chapters: {len(unique_chapters)} unique chapters. Values: {unique_chapters[:10]}{'...' if len(unique_chapters) > 10 else ''}"
        )

        # Log chapter titles if present
        # Prefer "CHAPTER_TITLE" then "chapter_title"
        chapter_title_col_name = None
        if "CHAPTER_TITLE" in df.columns:
            chapter_title_col_name = "CHAPTER_TITLE"
        elif "chapter_title" in df.columns:
            chapter_title_col_name = "chapter_title"

        if chapter_title_col_name:
            chapter_titles = (
                df.groupby("chapter_no")[chapter_title_col_name].first().to_dict()
            )
            logger.info(
                f"Chapter titles (from '{chapter_title_col_name}'): First 10 - {dict(list(chapter_titles.items())[:10])}{'...' if len(chapter_titles) > 10 else ''}"
            )

        # Log topics if present
        if "topic" in df.columns:
            topics = df["topic"].dropna().unique().tolist()
            logger.info(
                f"Topics: {len(topics)} unique topics. First 10 values: {topics[:10]}{'...' if len(topics) > 10 else ''}"
            )

        # Log system_category if present
        if "system_category" in df.columns:
            sc_values = df["system_category"].dropna().unique().tolist()
            logger.info(
                f"Detected 'system_category' column with {len(sc_values)} unique values. First 10: {sc_values[:10]}{'...' if len(sc_values) > 10 else ''}"
            )

        return df
    except FileNotFoundError:
        # This is already logged above, re-raise to be handled by caller
        raise
    except ValueError as ve:
        # This is already logged above, re-raise to be handled by caller
        raise
    except Exception as e:
        logger.error(
            f"Failed to load quiz bank from '{file_path}' due to an unexpected error: {str(e)}",
            exc_info=True,
        )
        return None  # Or re-raise, depending on desired strictness


def import_questions_by_chapter(
    df: pd.DataFrame,
    questions_per_quiz: int = 20,
    quizzes_per_chapter: int = 2,
    max_quizzes_per_chapter: int = 5,
    min_coverage_percentage: int = 40,
    single_quiz_threshold: float = 1.3,  # If questions < questions_per_quiz * threshold, create 1 quiz
    use_descriptive_titles: bool = True,
    use_chapter_prefix: bool = True,
    chapter_zfill: int = 2,
    cli_system_category_name: Optional[str] = None,  # For CLI override
) -> tuple[int, int]:
    """
    Imports questions from a DataFrame, organizing them into quizzes by chapter.
    This function now uses the refactored `quiz_bank_to_models` for actual DB insertion.
    """
    if df is None or df.empty:
        logger.error("Cannot import questions: DataFrame is None or empty.")
        return 0, 0

    total_quizzes_created = 0
    total_questions_imported = 0

    try:
        # Ensure 'question_text' exists, mapping from 'text' if necessary for this function's logic
        if "text" in df.columns and "question_text" not in df.columns:
            df = df.rename(columns={"text": "question_text"})

        # Validate required columns for this function's processing logic
        required_for_processing = [
            "chapter_no",
            "question_text",
            "options",
            "answerIndex",
        ]
        missing_for_processing = [
            col for col in required_for_processing if col not in df.columns
        ]
        if missing_for_processing:
            logger.error(
                f"DataFrame missing columns required for chapter processing: {missing_for_processing}"
            )
            return 0, 0

        chapters = sorted(df["chapter_no"].unique())
        log_message_parts = [
            f"Processing {len(chapters)} chapters.",
            f"Target: {questions_per_quiz}Q/quiz, {quizzes_per_chapter} quizzes/chapter.",
            f"Max quizzes: {max_quizzes_per_chapter}.",
            f"Min coverage: {min_coverage_percentage}%.",
            f"Single quiz factor: {single_quiz_threshold}.",
        ]
        if cli_system_category_name:
            log_message_parts.append(
                f"CLI System Category Override: '{cli_system_category_name}'."
            )
        logger.info(" ".join(log_message_parts))

        for chapter in chapters:
            chapter_df = df[
                df["chapter_no"] == chapter
            ].copy()  # Use .copy() to avoid SettingWithCopyWarning
            num_chapter_questions = len(chapter_df)

            chapter_display_name = str(chapter)  # For logging
            logger.info(
                f"\n--- Chapter {chapter_display_name}: {num_chapter_questions} questions available ---"
            )

            if num_chapter_questions == 0:
                logger.warning(
                    f"Chapter {chapter_display_name}: No questions. Skipping."
                )
                continue

            # Determine how many quizzes to create for this chapter
            if num_chapter_questions < questions_per_quiz * single_quiz_threshold:
                actual_quizzes_for_chapter = 1
                # For a single quiz, use all available questions up to questions_per_quiz.
                # If more than questions_per_quiz, it will be capped by questions_per_quiz.
                # If less, it will use all available.
                actual_questions_per_quiz_for_this_chapter_calc = min(
                    num_chapter_questions, questions_per_quiz
                )

                logger.info(
                    f"Chapter {chapter_display_name}: Low question count ({num_chapter_questions}). "
                    f"Creating 1 quiz with up to {actual_questions_per_quiz_for_this_chapter_calc} questions."
                )
            else:
                actual_quizzes_for_chapter = quizzes_per_chapter  # Start with default
                actual_questions_per_quiz_for_this_chapter_calc = questions_per_quiz

                # Adjust number of quizzes based on coverage percentage
                min_questions_to_cover = int(
                    num_chapter_questions * (min_coverage_percentage / 100)
                )
                required_quizzes_for_coverage = (
                    min_questions_to_cover
                    + actual_questions_per_quiz_for_this_chapter_calc
                    - 1
                ) // actual_questions_per_quiz_for_this_chapter_calc

                if required_quizzes_for_coverage > actual_quizzes_for_chapter:
                    new_quiz_count = min(
                        max_quizzes_per_chapter, required_quizzes_for_coverage
                    )
                    logger.info(
                        f"Chapter {chapter_display_name}: Default {actual_quizzes_for_chapter} quizzes insufficient for "
                        f"{min_coverage_percentage}% coverage ({min_questions_to_cover} questions). "
                        f"Adjusting to {new_quiz_count} quizzes (required: {required_quizzes_for_coverage}, max: {max_quizzes_per_chapter})."
                    )
                    actual_quizzes_for_chapter = new_quiz_count
                else:
                    logger.info(
                        f"Chapter {chapter_display_name}: Default {actual_quizzes_for_chapter} quizzes sufficient "
                        f"for {min_coverage_percentage}% coverage. (Min needed: {min_questions_to_cover} questions)."
                    )

            # Final cap by max_quizzes_per_chapter
            actual_quizzes_for_chapter = min(
                max_quizzes_per_chapter, actual_quizzes_for_chapter
            )
            logger.info(
                f"Chapter {chapter_display_name}: Final plan: {actual_quizzes_for_chapter} quizzes, "
                f"aiming for {actual_questions_per_quiz_for_this_chapter_calc} questions each."
            )

            # Determine Chapter Title and Primary Topic for naming quizzes
            chapter_prefix_str = ""
            if use_chapter_prefix:
                try:  # Attempt to zfill if chapter is numeric
                    chapter_prefix_str = str(int(chapter)).zfill(chapter_zfill) + " "
                except (ValueError, TypeError):  # Otherwise, use as is
                    chapter_prefix_str = str(chapter) + " "

            chapter_title_base = f"Chapter {chapter_display_name}"  # Default base title
            if (
                "CHAPTER_TITLE" in chapter_df.columns
                and not chapter_df["CHAPTER_TITLE"].empty
            ):
                # Use the most common CHAPTER_TITLE for this chapter
                chapter_title_base = (
                    chapter_df["CHAPTER_TITLE"].mode()[0]
                    if not chapter_df["CHAPTER_TITLE"].mode().empty
                    else chapter_title_base
                )
            elif (
                "chapter_title" in chapter_df.columns
                and not chapter_df["chapter_title"].empty
            ):
                # Fallback to 'chapter_title' if 'CHAPTER_TITLE' isn't there or all NaNs
                chapter_title_base = (
                    chapter_df["chapter_title"].mode()[0]
                    if not chapter_df["chapter_title"].mode().empty
                    else chapter_title_base
                )

            primary_topic_name_for_chapter = (
                chapter_title_base  # Default topic name if no 'topic' column
            )
            if "topic" in chapter_df.columns and not chapter_df["topic"].dropna().empty:
                # Use the most common topic for this chapter as the primary topic for quiz naming
                primary_topic_name_for_chapter = (
                    chapter_df["topic"].mode()[0]
                    if not chapter_df["topic"].mode().empty
                    else primary_topic_name_for_chapter
                )

            # Determine System Category for this chapter's quizzes
            system_category_for_this_chapter = (
                cli_system_category_name  # CLI override takes precedence
            )
            if (
                not system_category_for_this_chapter
                and "system_category" in chapter_df.columns
            ):
                # If no CLI override, try to get from DataFrame's 'system_category' column
                sc_counts = chapter_df["system_category"].dropna().value_counts()
                if not sc_counts.empty:
                    system_category_for_this_chapter = sc_counts.index[0]
                    logger.info(
                        f"Chapter {chapter_display_name}: Using SystemCategory '{system_category_for_this_chapter}' from DataFrame."
                    )
            elif system_category_for_this_chapter:  # Log if CLI override is used
                logger.info(
                    f"Chapter {chapter_display_name}: Using SystemCategory '{system_category_for_this_chapter}' from CLI override."
                )
            else:  # No category specified or found
                logger.info(
                    f"Chapter {chapter_display_name}: No SystemCategory specified via CLI or found in DataFrame."
                )

            # --- Create quizzes for the chapter ---
            used_question_indices_in_chapter_df = (
                set()
            )  # Track indices within the chapter_df
            chapter_questions_imported_count = 0

            for quiz_num in range(1, actual_quizzes_for_chapter + 1):
                # Get questions not yet used in this chapter
                available_indices_in_chapter_df = list(
                    set(range(num_chapter_questions))
                    - used_question_indices_in_chapter_df
                )

                if not available_indices_in_chapter_df:
                    logger.warning(
                        f"Chapter {chapter_display_name}, Quiz {quiz_num}: No more unique questions available from this chapter. Stopping quiz creation for this chapter."
                    )
                    break

                # DataFrame of questions still available in this chapter
                available_for_sampling_df = chapter_df.iloc[
                    available_indices_in_chapter_df
                ]

                # Determine sample size for current quiz
                # If it's a single quiz due to low question count, actual_questions_per_quiz_for_this_chapter_calc was already set to num_chapter_questions
                # Otherwise, it's the standard questions_per_quiz
                current_quiz_sample_size = min(
                    actual_questions_per_quiz_for_this_chapter_calc,
                    len(available_for_sampling_df),
                )

                if current_quiz_sample_size == 0:
                    logger.warning(
                        f"Chapter {chapter_display_name}, Quiz {quiz_num}: Calculated sample size is 0. Skipping this quiz."
                    )
                    continue

                if (
                    current_quiz_sample_size
                    < actual_questions_per_quiz_for_this_chapter_calc
                    and not (
                        actual_quizzes_for_chapter == 1
                        and num_chapter_questions
                        < questions_per_quiz * single_quiz_threshold
                    )
                ):  # Log if not enough questions, unless it's the single quiz scenario for low count
                    logger.warning(
                        f"Chapter {chapter_display_name}, Quiz {quiz_num}: Only {current_quiz_sample_size} unique questions left. "
                        f"Expected {actual_questions_per_quiz_for_this_chapter_calc}."
                    )

                # Sample questions for the current quiz
                quiz_sample_df = available_for_sampling_df.sample(
                    n=current_quiz_sample_size, random_state=quiz_num
                )  # random_state for some consistency

                # Record the chapter_df indices that were just sampled
                # Need to map quiz_sample_df.index back to the original chapter_df indices
                original_indices_for_sample = [
                    chapter_df.index.get_loc(idx) for idx in quiz_sample_df.index
                ]
                used_question_indices_in_chapter_df.update(original_indices_for_sample)

                # --- Determine quiz title and topic for quiz_bank_to_models ---
                # The topic_name passed to quiz_bank_to_models will associate all questions in *this specific quiz* to that one topic.
                # If quiz_sample_df has a 'topic' column, we might use its most common value for this quiz.
                # Otherwise, we use the primary_topic_name_for_chapter.

                topic_for_this_quiz = primary_topic_name_for_chapter  # Default
                if (
                    "topic" in quiz_sample_df.columns
                    and not quiz_sample_df["topic"].dropna().empty
                ):
                    current_quiz_topic_counts = quiz_sample_df["topic"].value_counts()
                    if not current_quiz_topic_counts.empty:
                        topic_for_this_quiz = current_quiz_topic_counts.index[0]

                if use_descriptive_titles:
                    quiz_final_title = f"{chapter_prefix_str}{chapter_title_base}: {topic_for_this_quiz} - Quiz {quiz_num}"
                else:  # Simple title
                    quiz_final_title = (
                        f"{chapter_prefix_str}{chapter_title_base} - Quiz {quiz_num}"
                    )

                # Now, call quiz_bank_to_models which uses bulk_create
                # It needs the raw data for questions (text, options, answerIndex, tag, chapter_no)
                # Ensure the quiz_sample_df has the 'text' column expected by quiz_bank_to_models
                if (
                    "question_text" in quiz_sample_df.columns
                    and "text" not in quiz_sample_df.columns
                ):
                    quiz_sample_df_for_import = quiz_sample_df.rename(
                        columns={"question_text": "text"}
                    )
                else:
                    quiz_sample_df_for_import = quiz_sample_df

                quiz_data_for_import = quiz_sample_df_for_import.to_dict("records")

                try:
                    # Atomic transaction for each quiz creation
                    with transaction.atomic():
                        if Quiz.objects.filter(title=quiz_final_title).exists():
                            logger.warning(
                                f"Quiz '{quiz_final_title}' already exists. Skipping."
                            )
                            # If skipping, we need to ensure used_question_indices are not re-used by mistake later.
                            # However, the current logic samples from *available*, so this should be okay.
                            continue

                        logger.info(
                            f"Creating quiz '{quiz_final_title}' with {len(quiz_data_for_import)} questions. "
                            f"(Topic: {topic_for_this_quiz}, "
                            f"SysCat: {system_category_for_this_chapter or 'None'})."
                        )

                        # --- Call the refactored quiz_bank_to_models ---
                        quiz = quiz_bank_to_models(
                            quiz_data_for_import,
                            quiz_final_title,
                            topic_name=topic_for_this_quiz,  # This sets the Topic for the Quiz and all its Questions
                        )
                        # --- End call ---

                        if quiz:
                            # Associate SystemCategory with the Quiz if specified
                            if system_category_for_this_chapter:
                                category_obj, created = (
                                    SystemCategory.objects.get_or_create(
                                        name=system_category_for_this_chapter
                                    )
                                )
                                if created:
                                    logger.info(
                                        f"Created new SystemCategory: '{system_category_for_this_chapter}'."
                                    )
                                quiz.system_categories.add(category_obj)
                                logger.info(
                                    f"Associated Quiz '{quiz.title}' with SystemCategory '{category_obj.name}'."
                                )

                            num_actually_imported = (
                                quiz.question_count()
                            )  # Verify count from DB
                            logger.info(
                                f"Successfully created '{quiz.title}' with {num_actually_imported} questions."
                            )
                            if num_actually_imported != len(quiz_data_for_import):
                                logger.warning(
                                    f"Mismatch for '{quiz.title}': Sampled {len(quiz_data_for_import)}, "
                                    f"actually imported {num_actually_imported} questions into DB."
                                )
                            total_quizzes_created += 1
                            total_questions_imported += num_actually_imported
                            chapter_questions_imported_count += num_actually_imported
                        else:
                            logger.error(
                                f"Failed to create quiz '{quiz_final_title}' (quiz_bank_to_models returned None)."
                            )

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
                f"--- Chapter {chapter_display_name} processing finished. Imported {chapter_questions_imported_count} questions "
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
