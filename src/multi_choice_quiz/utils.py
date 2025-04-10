"""
Utility functions for the multi_choice_quiz app.
"""

import json
import pandas as pd
from typing import List, Dict, Any, Optional

from .transform import quiz_bank_to_models
from .models import Quiz


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
