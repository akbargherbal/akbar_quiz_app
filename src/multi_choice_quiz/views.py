# src/multi_choice_quiz/views.py (Modified for Step 6.3)

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
import json
import logging
from datetime import datetime

from django.utils.safestring import mark_safe
from .models import Quiz, Question, QuizAttempt  # Added Question
from .transform import models_to_frontend

logger = logging.getLogger(__name__)


# --- home and quiz_detail views remain unchanged ---
def home(request):
    try:
        quiz = (
            Quiz.objects.filter(
                is_active=True,
                questions__isnull=False,
            )
            .distinct()
            .order_by("-created_at")
            .first()
        )
        quiz_id_to_pass = None
        quiz_data = []
        quiz_title_for_log = "Demo Quiz"

        if quiz:
            questions = quiz.questions.filter(is_active=True).order_by("position")
            quiz_data = models_to_frontend(questions)
            quiz_id_to_pass = quiz.id
            quiz_title_for_log = quiz.title
            logger.info(
                f"Loaded quiz '{quiz_title_for_log}' (ID: {quiz_id_to_pass}) with {len(quiz_data)} questions for generic home view."
            )
        else:
            logger.warning(
                "No active quizzes with questions found in database, using demo questions for generic home view."
            )
            quiz_data = get_demo_questions()

    except Exception as e:
        logger.error(
            f"Error loading quiz from database for generic home view: {str(e)}",
            exc_info=True,
        )
        quiz_data = get_demo_questions()
        quiz_id_to_pass = None
        quiz_title_for_log = "Demo Quiz (Error Fallback)"

    context = {
        "quiz_data": mark_safe(json.dumps(quiz_data)),
        "quiz_id": quiz_id_to_pass,
        "quiz_title": quiz_title_for_log,
    }
    return render(request, "multi_choice_quiz/index.html", context)


def quiz_detail(request, quiz_id):
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
        questions = quiz.questions.filter(is_active=True).order_by("position")
        if not questions.exists():
            logger.warning(
                f"Quiz ID {quiz_id} ('{quiz.title}') exists but has no active questions."
            )

        quiz_data = models_to_frontend(questions)
        context = {
            "quiz": quiz,
            "quiz_data": mark_safe(json.dumps(quiz_data)),
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
        }
        return render(request, "multi_choice_quiz/index.html", context)

    except ObjectDoesNotExist:
        logger.warning(f"Quiz with ID {quiz_id} not found or not active.")
        context = {
            "error_message": f"The requested quiz (ID: {quiz_id}) could not be found or is not active."
        }
        return render(request, "multi_choice_quiz/error.html", context, status=404)
    except Exception as e:
        logger.error(f"Error loading quiz {quiz_id}: {str(e)}", exc_info=True)
        context = {
            "error_message": f"An error occurred while trying to load quiz ID: {quiz_id}."
        }
        return render(request, "multi_choice_quiz/error.html", context, status=500)


# --- End unchanged views ---


@csrf_exempt
@require_POST
def submit_quiz_attempt(request):
    """
    API endpoint to receive and save quiz attempt results, including detailed mistakes.
    """
    try:
        try:
            data = json.loads(request.body)
            logger.debug(f"Received attempt data: {data}")
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON in submit_quiz_attempt.")
            return HttpResponseBadRequest("Invalid JSON data.")

        required_fields = [
            "quiz_id",
            "score",
            "total_questions",
            "percentage",
            "end_time",
        ]
        # attempt_details is now expected but handled if missing for compatibility
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(
                f"Missing fields in submit_quiz_attempt data: {missing_fields}"
            )
            return HttpResponseBadRequest(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        try:
            quiz_id = int(data["quiz_id"])
            score = int(data["score"])
            total_questions = int(data["total_questions"])
            percentage = float(data["percentage"])
            end_time_str = str(data["end_time"])
            end_time_dt = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            # --- START STEP 6.3: Extract attempt_details ---
            # Use .get() to handle cases where it might be missing (e.g., older JS)
            received_attempt_details = data.get("attempt_details", {})
            if not isinstance(received_attempt_details, dict):
                logger.warning(
                    f"Received non-dict attempt_details: {type(received_attempt_details)}. Ignoring."
                )
                received_attempt_details = {}  # Treat as empty if invalid type
            # --- END STEP 6.3: Extract attempt_details ---
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid data type or format received: {e}. Data: {data}")
            return HttpResponseBadRequest(f"Invalid data type or format for field: {e}")

        try:
            quiz = Quiz.objects.get(id=quiz_id)
            # --- START STEP 6.3: Fetch Correct Answers ---
            # Fetch all questions for this quiz and their correct answer index (0-based)
            correct_answers = {
                q.id: q.correct_option_index()
                for q in Question.objects.filter(quiz=quiz)
                # Ensure correct_option_index() handles cases with no correct option gracefully (returns None)
            }
            # --- END STEP 6.3: Fetch Correct Answers ---
        except ObjectDoesNotExist:
            logger.warning(f"Quiz with ID {quiz_id} not found during submission.")
            return HttpResponseBadRequest("Quiz not found.")

        attempt_user = request.user if request.user.is_authenticated else None
        user_log_str = (
            f"User ID: {attempt_user.id}" if attempt_user else "Anonymous User"
        )

        # --- START STEP 6.3: Process Mistakes ---
        mistakes_data = {}
        if received_attempt_details:  # Only process if we received details
            logger.debug(
                f"Processing received attempt_details for {len(received_attempt_details)} questions."
            )
            for q_id_str, user_answer_idx in received_attempt_details.items():
                try:
                    question_id = int(q_id_str)
                    correct_answer_idx = correct_answers.get(question_id)

                    # Check if the answer was incorrect
                    # Also handle cases where correct answer might be None (bad data) or user answer is None
                    if (
                        correct_answer_idx is not None
                        and user_answer_idx != correct_answer_idx
                    ):
                        mistakes_data[str(question_id)] = (
                            {  # Use string ID as key in JSON
                                "user_answer_idx": user_answer_idx,
                                "correct_answer_idx": correct_answer_idx,
                            }
                        )
                        logger.debug(
                            f"Mistake recorded for QID {question_id}: User={user_answer_idx}, Correct={correct_answer_idx}"
                        )
                    elif correct_answer_idx is None:
                        logger.warning(
                            f"Could not find correct answer for QID {question_id} while processing mistakes."
                        )

                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Error processing detail for QID string '{q_id_str}': {e}. Skipping."
                    )
                    continue  # Skip this detail entry
        else:
            logger.info(
                "No attempt_details received in payload or it was empty/invalid."
            )
        # --- END STEP 6.3: Process Mistakes ---

        # --- START STEP 6.3: Save Attempt with Processed Mistakes ---
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=attempt_user,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            end_time=end_time_dt,
            attempt_details=(
                mistakes_data if mistakes_data else None
            ),  # Save processed mistakes, or None if empty
        )
        # --- END STEP 6.3: Save Attempt ---

        logger.info(
            f"Saved QuizAttempt ID: {attempt.id} for Quiz ID: {quiz_id} by {user_log_str}. Score: {score}/{total_questions}. Mistakes recorded: {len(mistakes_data)}"
        )
        return JsonResponse({"status": "success", "attempt_id": attempt.id})

    except Exception as e:
        logger.error(f"Unexpected error in submit_quiz_attempt: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": "An internal server error occurred."},
            status=500,
        )


# --- get_demo_questions remains unchanged ---
def get_demo_questions():
    return [
        # ... demo questions ...
        {
            "text": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin", "Madrid", "Rome"],
            "answerIndex": 1,
        },
        {
            "text": "Which river is the longest in the world?",
            "options": ["Amazon", "Nile", "Mississippi", "Yangtze", "Congo"],
            "answerIndex": 1,
        },
        {
            "text": "What is the highest mountain peak in the world?",
            "options": ["K2", "Kangchenjunga", "Makalu", "Mount Everest", "Lhotse"],
            "answerIndex": 3,
        },
    ]
