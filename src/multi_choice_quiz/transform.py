"""
Transformation module for quiz data.

This module handles converting between different quiz data formats:
1. Quiz Bank Format (source data with 1-based indexing)
2. Database Models (using Django ORM)
3. Frontend Format (JSON with 0-based indexing for Alpine.js)
"""

from typing import List, Dict, Any, Optional, Union
import json

from django.db import transaction
from django.db.models import QuerySet

from .models import Quiz, Question, Option, Topic


def quiz_bank_to_models(
    quiz_data: List[Dict[str, Any]], quiz_title: str, topic_name: Optional[str] = None
) -> Quiz:
    """
    Transform quiz bank data into database models.
    Handles the 1-based to 0-based index conversion.

    Args:
        quiz_data: List of dictionaries with keys 'text', 'options', 'answerIndex'
        quiz_title: Title for the new quiz
        topic_name: Optional topic name to associate with the quiz

    Returns:
        The created Quiz instance
    """
    # Create or get the topic if provided
    topic = None
    if topic_name:
        topic, _ = Topic.objects.get_or_create(name=topic_name)

    # Create the quiz
    with transaction.atomic():
        quiz = Quiz.objects.create(title=quiz_title)

        if topic:
            quiz.topics.add(topic)

        # Create questions and options
        for i, item in enumerate(quiz_data):
            # Extract chapter_no if available
            chapter_no = item.get("chapter_no", "")

            question = Question.objects.create(
                quiz=quiz,
                topic=topic,
                text=item["text"],
                position=i + 1,  # 1-based position
                chapter_no=chapter_no,
            )

            # Get the correct answer index (1-based in quiz bank)
            correct_index = item["answerIndex"]

            # Create options
            options = item["options"]
            for j, option_text in enumerate(options, start=1):  # 1-based position
                Option.objects.create(
                    question=question,
                    text=option_text,
                    position=j,  # 1-based position
                    is_correct=(j == correct_index),  # Compare 1-based positions
                )

    return quiz


def models_to_frontend(
    questions: Union[QuerySet, List[Question]],
) -> List[Dict[str, Any]]:
    """
    Transform database models to frontend format.

    Args:
        questions: QuerySet or list of Question instances

    Returns:
        List of dictionaries in the format expected by the Alpine.js component
    """
    return [question.to_dict() for question in questions]


def frontend_to_models(
    frontend_data: List[Dict[str, Any]],
    quiz_title: str,
    topic_name: Optional[str] = None,
) -> Quiz:
    """
    Transform frontend format data back to database models.
    This handles the conversion from 0-based to 1-based indexing.

    Args:
        frontend_data: List of dictionaries with keys 'text', 'options', 'answerIndex' (0-based)
        quiz_title: Title for the new quiz
        topic_name: Optional topic name to associate with the quiz

    Returns:
        The created Quiz instance
    """
    # Convert 0-based answerIndex to 1-based for our models
    quiz_bank_format = []

    for item in frontend_data:
        # Create a copy to avoid modifying the original
        transformed_item = item.copy()

        # Convert 0-based answerIndex to 1-based
        if "answerIndex" in transformed_item:
            transformed_item["answerIndex"] = transformed_item["answerIndex"] + 1

        quiz_bank_format.append(transformed_item)

    return quiz_bank_to_models(quiz_bank_format, quiz_title, topic_name)
