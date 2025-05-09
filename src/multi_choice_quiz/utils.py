# src/multi_choice_quiz/utils.py

import json
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
import os

from django.db import transaction, IntegrityError

# --- SystemCategory IMPORT ---
from pages.models import SystemCategory  # <<< CORRECTED: Import from pages.models
from .models import Quiz, Question, Option, Topic  # Keep these from .models

# --- END SystemCategory IMPORT ---

from .transform import quiz_bank_to_models

logger = logging.getLogger(__name__)


def import_from_dataframe(
    df: pd.DataFrame,
    quiz_title: str,
    topic_name: Optional[str] = None,
    sample_size: Optional[int] = None,
    system_category_name: Optional[str] = None,
) -> Quiz:
    df = df.copy()
    required_columns = ["text", "options", "answerIndex"]
    for col in required_columns:
        if col not in df.columns:
            if col == "text" and "question_text" in df.columns:
                df = df.rename(columns={"question_text": "text"})
            elif col == "answerIndex" and "correct_answer" in df.columns:
                df = df.rename(columns={"correct_answer": "answerIndex"})
            else:
                raise ValueError(f"DataFrame is missing required column: {col}")

    if sample_size and sample_size < len(df):
        df = df.sample(sample_size)

    quiz_data = df.to_dict("records")
    for item in quiz_data:
        if isinstance(item["options"], str):
            try:
                item["options"] = json.loads(item["options"])
            except json.JSONDecodeError:
                item["options"] = [opt.strip() for opt in item["options"].split(",")]

    quiz = quiz_bank_to_models(quiz_data, quiz_title, topic_name)

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
    if "question_text" in df.columns and "text" not in df.columns:
        df = df.rename(columns={"question_text": "text"})
    if "correct_answer" in df.columns and "answerIndex" not in df.columns:
        df = df.rename(columns={"correct_answer": "answerIndex"})
    base_columns = ["text", "options", "answerIndex"]
    extra_columns = ["tag", "chapter_no", "topic", "CHAPTER_TITLE", "system_category"]

    available_base_columns = [col for col in base_columns if col in df.columns]
    available_extra_columns = [col for col in extra_columns if col in df.columns]
    if len(available_base_columns) < len(base_columns):
        missing = set(base_columns) - set(available_base_columns)
        raise ValueError(f"DataFrame is missing required columns: {missing}")
    columns_to_use = available_base_columns + available_extra_columns
    result = df[columns_to_use].sample(min(no_questions, len(df))).to_dict("records")
    return result


def load_quiz_bank(file_path: str) -> Optional[pd.DataFrame]:
    try:
        logger.info(f"Loading quiz bank from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Quiz bank file not found: {file_path}")
        df = pd.read_pickle(file_path)
        required_columns = ["chapter_no", "question_text", "options", "answerIndex"]
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
        elif "chapter_title" in df.columns:
            chapter_titles = df.groupby("chapter_no")["chapter_title"].first().to_dict()
            logger.info(f"Chapter titles (from chapter_title): {chapter_titles}")

        if "topic" in df.columns:
            topics = df["topic"].unique().tolist()
            logger.info(f"Topics: {len(topics)} unique topics")
            if len(topics) <= 10:
                logger.info(f"Topic values: {topics}")

        if "system_category" in df.columns:
            sc_values = df["system_category"].dropna().unique().tolist()
            logger.info(
                f"Detected 'system_category' column with {len(sc_values)} unique values."
            )
            if len(sc_values) <= 10:
                logger.info(f"System Category values found: {sc_values}")

        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except ValueError as ve:
        logger.error(f"Validation error loading quiz bank: {str(ve)}")
        raise
    except Exception as e:
        logger.error(
            f"Failed to load quiz bank due to an unexpected error: {str(e)}",
            exc_info=True,
        )
        return None


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
    cli_system_category_name: Optional[str] = None,
) -> tuple[int, int]:
    if df is None:
        logger.error("Cannot import questions: DataFrame is None.")
        return 0, 0

    total_quizzes_created = 0
    total_questions_imported = 0

    try:
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
            chapter_df = df[df["chapter_no"] == chapter].copy()
            num_chapter_questions = len(chapter_df)
            logger.info(
                f"\n--- Chapter {chapter}: {num_chapter_questions} questions available ---"
            )

            if num_chapter_questions == 0:
                logger.warning(f"Chapter {chapter}: No questions. Skipping.")
                continue

            if num_chapter_questions < questions_per_quiz * single_quiz_threshold:
                actual_quizzes_for_chapter = 1
                actual_questions_per_quiz = num_chapter_questions
                logger.info(
                    f"Chapter {chapter}: Low question count ({num_chapter_questions}). Creating 1 quiz with all {actual_questions_per_quiz} questions."
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
                        f"Chapter {chapter}: Default {actual_quizzes_for_chapter} quizzes insufficient for {min_coverage_percentage}% coverage ({min_questions_to_cover} questions). Adjusting to {new_quiz_count} quizzes (required: {required_quizzes_for_coverage}, max: {max_quizzes_per_chapter})."
                    )
                    actual_quizzes_for_chapter = new_quiz_count
                else:
                    logger.info(
                        f"Chapter {chapter}: Default {actual_quizzes_for_chapter} quizzes sufficient for {min_coverage_percentage}% coverage. (Min needed: {min_questions_to_cover} questions)."
                    )
                actual_quizzes_for_chapter = min(
                    max_quizzes_per_chapter, actual_quizzes_for_chapter
                )
                logger.info(
                    f"Chapter {chapter}: Final plan: {actual_quizzes_for_chapter} quizzes, aiming for {actual_questions_per_quiz} questions each."
                )

            chapter_prefix_str = ""
            if use_chapter_prefix:
                try:
                    chapter_prefix_str = str(int(chapter)).zfill(chapter_zfill) + " "
                except (ValueError, TypeError):
                    chapter_prefix_str = str(chapter) + " "
            chapter_title_base = f"Chapter {chapter}"
            if "CHAPTER_TITLE" in chapter_df.columns:
                chapter_title_base = chapter_df["CHAPTER_TITLE"].value_counts().index[0]
            elif "chapter_title" in chapter_df.columns:
                chapter_title_base = chapter_df["chapter_title"].value_counts().index[0]
            primary_topic_name = chapter_title_base
            if "topic" in chapter_df.columns:
                topic_counts = chapter_df["topic"].value_counts()
                if not topic_counts.empty:
                    primary_topic_name = topic_counts.index[0]

            system_category_for_this_chapter = cli_system_category_name
            if (
                not system_category_for_this_chapter
                and "system_category" in chapter_df.columns
            ):
                sc_counts = chapter_df["system_category"].dropna().value_counts()
                if not sc_counts.empty:
                    system_category_for_this_chapter = sc_counts.index[0]
                    logger.info(
                        f"Chapter {chapter}: Using SystemCategory '{system_category_for_this_chapter}' from DataFrame."
                    )
            elif system_category_for_this_chapter:
                logger.info(
                    f"Chapter {chapter}: Using SystemCategory '{system_category_for_this_chapter}' from CLI override."
                )
            else:
                logger.info(
                    f"Chapter {chapter}: No SystemCategory specified via CLI or found in DataFrame."
                )

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
                        f"Chapter {chapter}, Quiz {quiz_num}: Only {current_sample_size} unique questions left. Expected {actual_questions_per_quiz}."
                    )
                quiz_sample_df = available_for_sampling_df.sample(n=current_sample_size)
                original_indices_for_sample = chapter_df.index.get_indexer(
                    quiz_sample_df.index
                )
                used_question_indices.update(original_indices_for_sample)

                if use_descriptive_titles and "topic" in chapter_df.columns:
                    quiz_final_title = f"{chapter_prefix_str}{chapter_title_base}: {primary_topic_name} - Quiz {quiz_num}"
                    quiz_topic_name_for_import = primary_topic_name
                else:
                    quiz_final_title = (
                        f"{chapter_prefix_str}{chapter_title_base} - Quiz {quiz_num}"
                    )
                    quiz_topic_name_for_import = primary_topic_name

                try:
                    with transaction.atomic():
                        if Quiz.objects.filter(title=quiz_final_title).exists():
                            logger.warning(
                                f"Quiz '{quiz_final_title}' already exists. Skipping."
                            )
                            continue

                        logger.info(
                            f"Creating quiz '{quiz_final_title}' with {current_sample_size} questions "
                            f"(Topic: {quiz_topic_name_for_import}, "
                            f"SysCat: {system_category_for_this_chapter or 'None'})."
                        )
                        quiz = import_from_dataframe(
                            quiz_sample_df,
                            quiz_final_title,
                            topic_name=quiz_topic_name_for_import,
                            system_category_name=system_category_for_this_chapter,
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
