# src/multi_choice_quiz/views.py (Modified for Step 6.3)

from django.shortcuts import render, get_object_or_404
from django.contrib import messages  # <<< THIS LINE MUST BE PRESENT
from django.shortcuts import redirect

from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    Http404,
    HttpResponseForbidden,
)  # Added Http404, HttpResponseForbidden

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required  # Added login_required
from django.utils.safestring import mark_safe

import json
import logging
from datetime import datetime

from .models import Quiz, Question, QuizAttempt  # Added Question
from .transform import models_to_frontend

logger = logging.getLogger(__name__)


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
        # log view and name of file:
        logger.info(f"View: home, File: {__file__}")

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
            received_attempt_details = data.get("attempt_details", {})
            if not isinstance(received_attempt_details, dict):
                logger.warning(
                    f"Received non-dict attempt_details: {type(received_attempt_details)}. Ignoring."
                )
                received_attempt_details = {}  # Treat as empty if invalid type
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid data type or format received: {e}. Data: {data}")
            return HttpResponseBadRequest(f"Invalid data type or format for field: {e}")

        try:
            quiz = Quiz.objects.get(id=quiz_id)
            correct_answers = {
                q.id: q.correct_option_index()
                for q in Question.objects.filter(quiz=quiz)
            }
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


# <<< START NEW VIEW FUNCTION (Step 7.1) >>>
@login_required
def attempt_mistake_review(request, attempt_id):
    """
    Displays the mistakes made in a specific quiz attempt for the logged-in user.
    """
    logger.info(f"User {request.user.id} requesting review for attempt ID {attempt_id}")
    try:
        attempt = get_object_or_404(QuizAttempt, id=attempt_id)

        # --- Security Check: Ensure the user owns this attempt ---
        if attempt.user != request.user:
            logger.warning(
                f"User {request.user.id} attempted to access attempt {attempt_id} owned by user {attempt.user_id}."
            )
            # Option 1: Return 404 (as if it doesn't exist for them)
            raise Http404("Quiz attempt not found.")

        # --- Check if there are mistakes to review ---
        if not attempt.attempt_details or not isinstance(attempt.attempt_details, dict):
            logger.info(
                f"Attempt {attempt_id} has no mistake details to review. Redirecting user {request.user.id} to profile."
            )
            messages.info(
                request, "There are no mistakes to review for this attempt."
            )  # Optional message
            return redirect("pages:profile")  # Redirect to profile page

        mistake_details = attempt.attempt_details
        question_ids = [int(qid) for qid in mistake_details.keys()]

        # Fetch all relevant questions and their options in bulk to optimize DB access
        questions = (
            Question.objects.filter(id__in=question_ids)
            .prefetch_related("options")
            .order_by("position")
        )

        # Prepare context for the template
        mistakes_context = []
        for question in questions:
            q_id_str = str(question.id)
            if q_id_str in mistake_details:
                detail = mistake_details[q_id_str]
                user_idx = detail.get("user_answer_idx")
                correct_idx = detail.get("correct_answer_idx")

                options_list = list(question.options.order_by("position"))
                user_answer_text = "N/A"
                correct_answer_text = "N/A"

                # Get user answer text (0-based index from JSON -> 1-based position)
                if user_idx is not None and 0 <= user_idx < len(options_list):
                    user_answer_text = options_list[user_idx].text
                elif user_idx is not None:
                    logger.warning(
                        f"User answer index {user_idx} out of bounds for QID {question.id} options."
                    )

                # Get correct answer text (0-based index from JSON -> 1-based position)
                if correct_idx is not None and 0 <= correct_idx < len(options_list):
                    correct_answer_text = options_list[correct_idx].text
                elif correct_idx is not None:
                    logger.warning(
                        f"Correct answer index {correct_idx} out of bounds for QID {question.id} options."
                    )
                elif (
                    question.correct_option()
                ):  # Fallback if index missing but model has it
                    correct_answer_text = question.correct_option().text
                    logger.warning(
                        f"Used fallback correct option text for QID {question.id}."
                    )

                mistakes_context.append(
                    {
                        "question_id": question.id,
                        "question_text": question.text,
                        "user_answer": user_answer_text,
                        "correct_answer": correct_answer_text,
                        "question_tag": question.tag,  # Include tag if needed
                    }
                )
            else:
                logger.warning(
                    f"Question ID {question.id} was fetched but not found in mistake_details keys for attempt {attempt_id}."
                )

        context = {
            "attempt": attempt,
            "quiz": attempt.quiz,
            "mistakes": mistakes_context,
        }
        return render(request, "multi_choice_quiz/mistake_review.html", context)

    except Http404 as e:
        # Log the 404 explicitly if needed, then re-raise or handle
        logger.warning(f"Caught Http404 in attempt_mistake_review: {e}")
        raise  # Let Django handle the 404 page rendering

    except Exception as e:
        logger.error(
            f"Error generating mistake review for attempt {attempt_id} for user {request.user.id}: {e}",
            exc_info=True,
        )
        # Consider redirecting to an error page or profile page with a message
        messages.error(
            request, "An error occurred while trying to load the mistake review."
        )
        return redirect("pages:profile")


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
