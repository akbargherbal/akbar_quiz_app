# src/multi_choice_quiz/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import (
    csrf_exempt,
)  # For simplicity now, handle CSRF properly later if needed
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import json
import logging
from django.utils.safestring import mark_safe
from datetime import datetime  # Keep this import

from .models import Quiz, Question, QuizAttempt  # Keep these imports
from .transform import models_to_frontend

# Set up logging
logger = logging.getLogger(__name__)


def home(request):
    """
    Display the home page with the first available active quiz that has questions.
    If no suitable quizzes exist, fall back to hardcoded demo questions.
    """
    try:
        # --- START CORRECTED QUERY ---
        # Try to get the latest active quiz that has questions from the database
        quiz = (
            Quiz.objects.filter(
                is_active=True,
                questions__isnull=False,  # Ensure it has related questions
            )
            .distinct()
            .order_by("-created_at")
            .first()
        )  # Order by latest and get the first one
        # --- END CORRECTED QUERY ---

        quiz_id_to_pass = None
        quiz_data = []
        quiz_title_for_log = "Demo Quiz"  # Default for logging

        if quiz:  # No need to check quiz.questions.exists() again, query ensures it
            # Get all active questions for this quiz, ordered by position
            questions = quiz.questions.filter(is_active=True).order_by("position")
            quiz_data = models_to_frontend(questions)
            quiz_id_to_pass = quiz.id  # Get the ID
            quiz_title_for_log = quiz.title  # Use actual title for logging
            logger.info(
                f"Loaded quiz '{quiz_title_for_log}' (ID: {quiz_id_to_pass}) with {len(quiz_data)} questions for generic home view."
            )
        else:
            # Fallback to hardcoded demo questions if no suitable quiz is found
            logger.warning(
                "No active quizzes with questions found in database, using demo questions for generic home view."
            )
            quiz_data = get_demo_questions()
            # No quiz_id in demo mode (quiz_id_to_pass remains None)

    except Exception as e:
        # Log the error and fall back to demo questions
        logger.error(
            f"Error loading quiz from database for generic home view: {str(e)}",
            exc_info=True,  # Include traceback in log
        )
        quiz_data = get_demo_questions()
        quiz_id_to_pass = None
        quiz_title_for_log = "Demo Quiz (Error Fallback)"

    # Mark the JSON as safe to prevent double-escaping of HTML entities
    context = {
        "quiz_data": mark_safe(json.dumps(quiz_data)),
        "quiz_id": quiz_id_to_pass,  # Pass quiz_id if available, else None
        "quiz_title": quiz_title_for_log,  # Pass title for potential template use
    }

    return render(request, "multi_choice_quiz/index.html", context)


def quiz_detail(request, quiz_id):
    """
    Display a specific quiz by ID.
    """
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
        questions = quiz.questions.filter(is_active=True).order_by("position")

        # Check if the quiz actually has questions (good practice)
        if not questions.exists():
            logger.warning(
                f"Quiz ID {quiz_id} ('{quiz.title}') exists but has no active questions."
            )
            # Optionally handle this differently, e.g., show a message
            # For now, it will render with an empty quiz_data list

        # Transform questions to frontend format
        quiz_data = models_to_frontend(questions)

        # Mark the JSON as safe to prevent double-escaping of HTML entities
        context = {
            "quiz": quiz,  # Pass the whole quiz object if needed by template
            "quiz_data": mark_safe(json.dumps(quiz_data)),
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,  # Pass title
        }

        return render(request, "multi_choice_quiz/index.html", context)

    except ObjectDoesNotExist:  # More specific exception
        logger.warning(f"Quiz with ID {quiz_id} not found or not active.")
        context = {
            "error_message": f"The requested quiz (ID: {quiz_id}) could not be found or is not active."
        }
        return render(
            request, "multi_choice_quiz/error.html", context, status=404
        )  # Return 404 status
    except Exception as e:
        logger.error(f"Error loading quiz {quiz_id}: {str(e)}", exc_info=True)
        context = {
            "error_message": f"An error occurred while trying to load quiz ID: {quiz_id}."
        }
        return render(
            request, "multi_choice_quiz/error.html", context, status=500
        )  # Return 500 status


@csrf_exempt  # Temporarily disable CSRF for API endpoint simplicity
@require_POST
def submit_quiz_attempt(request):
    """
    API endpoint to receive and save quiz attempt results from the frontend.
    """
    try:
        # Check if request body is valid JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON in submit_quiz_attempt.")
            return HttpResponseBadRequest("Invalid JSON data.")

        # Validate required fields
        required_fields = [
            "quiz_id",
            "score",
            "total_questions",
            "percentage",
            "end_time",
        ]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(
                f"Missing fields in submit_quiz_attempt data: {missing_fields}"
            )
            return HttpResponseBadRequest(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        # --- Validate data types early ---
        try:
            quiz_id = int(data["quiz_id"])
            score = int(data["score"])
            total_questions = int(data["total_questions"])
            percentage = float(data["percentage"])
            end_time_str = data["end_time"]  # Keep as string for format check
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Invalid data type received in submit_quiz_attempt: {e}. Data: {data}"
            )
            return HttpResponseBadRequest(f"Invalid data type for field: {e}")

        # Validate end_time format
        try:
            end_time_dt = datetime.fromisoformat(
                end_time_str.replace("Z", "+00:00")
            )  # Handle 'Z' for UTC
        except ValueError:
            logger.warning(f"Invalid end_time format received: {end_time_str}")
            return HttpResponseBadRequest("Invalid end_time format. Expected ISO 8601.")

        # Get the quiz object
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except ObjectDoesNotExist:
            logger.warning(
                f"Quiz with ID {quiz_id} not found during attempt submission."
            )
            return HttpResponseBadRequest("Quiz not found.")

        # Determine the user
        attempt_user = request.user if request.user.is_authenticated else None
        user_log_str = (
            f"User ID: {attempt_user.id}" if attempt_user else "Anonymous User"
        )

        # Create and save the QuizAttempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=attempt_user,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            # start_time is set automatically by auto_now_add
            end_time=end_time_dt,
        )

        logger.info(
            f"Saved QuizAttempt ID: {attempt.id} for Quiz ID: {quiz_id} by {user_log_str}. Score: {score}/{total_questions}"
        )
        return JsonResponse({"status": "success", "attempt_id": attempt.id})

    except Exception as e:
        logger.error(f"Unexpected error in submit_quiz_attempt: {e}", exc_info=True)
        # Consider what status code to return, 500 might be appropriate
        return JsonResponse(
            {"status": "error", "message": "An internal server error occurred."},
            status=500,
        )


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
