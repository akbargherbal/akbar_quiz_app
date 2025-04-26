from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json
import logging
from django.utils.safestring import mark_safe

from .models import Quiz, Question
from .transform import models_to_frontend

# Set up logging
logger = logging.getLogger(__name__)


def home(request):
    """
    Display the home page with the first quiz found in the database.
    If no quizzes exist, fall back to hardcoded demo questions.
    """
    try:
        # Try to get the first active quiz from the database
        quiz = Quiz.objects.filter(is_active=True).first()

        if quiz and quiz.questions.exists():
            # Get all questions for this quiz, ordered by position
            questions = quiz.questions.filter(is_active=True).order_by("position")

            # Transform questions to frontend format (handling the index conversion)
            quiz_data = models_to_frontend(questions)

            logger.info(f"Loaded quiz '{quiz.title}' with {len(quiz_data)} questions")

        else:
            # Fallback to hardcoded demo questions if no quiz is found
            logger.warning("No active quizzes found in database, using demo questions")
            quiz_data = get_demo_questions()

    except Exception as e:
        # Log the error and fall back to demo questions
        logger.error(f"Error loading quiz from database: {str(e)}")
        quiz_data = get_demo_questions()

    # Mark the JSON as safe to prevent double-escaping of HTML entities
    context = {"quiz_data": mark_safe(json.dumps(quiz_data))}

    return render(request, "multi_choice_quiz/index.html", context)


def quiz_detail(request, quiz_id):
    """
    Display a specific quiz by ID.
    """
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
        questions = quiz.questions.filter(is_active=True).order_by("position")

        # Transform questions to frontend format
        quiz_data = models_to_frontend(questions)

        logger.info(
            f"""
jjj quiz_data; TYPE: {type(quiz_data)}

"""
        )

        logger.info(
            f"""
jjj quiz_data len: {len(quiz_data)}

"""
        )

        logger.info(
            f"""
jjj quiz_data[0]: {quiz_data[0]}

"""
        )

        # Mark the JSON as safe to prevent double-escaping of HTML entities
        context = {"quiz": quiz, "quiz_data": mark_safe(json.dumps(quiz_data))}

        return render(request, "multi_choice_quiz/index.html", context)

    except Exception as e:
        logger.error(f"Error loading quiz {quiz_id}: {str(e)}")

        # Simplified context to avoid potential errors
        context = {
            "error_message": f"The requested quiz (ID: {quiz_id}) could not be loaded."
        }

        return render(request, "multi_choice_quiz/error.html", context)


def get_demo_questions():
    """
    Return a set of demo questions for use when no database content exists.
    These are the same questions that were previously hardcoded.
    """
    return [
        {
            "text": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin", "Madrid", "Rome"],
            "answerIndex": 1,  # 0-based index for frontend
        },
        {
            "text": "Which river is the longest in the world?",
            "options": ["Amazon", "Nile", "Mississippi", "Yangtze", "Congo"],
            "answerIndex": 1,  # 0-based index for frontend
        },
        {
            "text": "What is the highest mountain peak in the world?",
            "options": ["K2", "Kangchenjunga", "Makalu", "Mount Everest", "Lhotse"],
            "answerIndex": 3,  # 0-based index for frontend
        },
    ]
