# src/pages/views.py (Existing - Confirmed for Step 5.4)

from django.shortcuts import render, redirect  # Added redirect
from django.contrib.auth import login  # Added login
from django.contrib import messages  # Added messages
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required  # <<< Already imported
from multi_choice_quiz.models import (
    Quiz,
    Topic,
    QuizAttempt,  # <<< Already imported
)

# --- Add form import ---
from .forms import SignUpForm


def home(request):
    # ... (home view code - unchanged) ...
    featured_quizzes = Quiz.objects.filter(is_active=True).order_by("-created_at")[:3]
    topics = Topic.objects.all()[:5]
    context = {
        "featured_quizzes": featured_quizzes,
        "topics": topics,
    }
    return render(request, "pages/home.html", context)


def quizzes(request):
    # ... (quizzes view code - unchanged) ...
    all_quizzes = Quiz.objects.filter(is_active=True).order_by("-created_at")
    topics = Topic.objects.all()
    topic_id = request.GET.get("topic")
    if topic_id:
        try:
            topic_id = int(topic_id)
            all_quizzes = all_quizzes.filter(topics__id=topic_id)
            selected_topic = Topic.objects.get(id=topic_id)
        except (ValueError, Topic.DoesNotExist):
            selected_topic = None
    else:
        selected_topic = None
    context = {
        "quizzes": all_quizzes,
        "topics": topics,
        "selected_topic": selected_topic,
    }
    return render(request, "pages/quizzes.html", context)


def about(request):
    # ... (about view code - unchanged) ...
    return render(request, "pages/about.html")


# --- Corrected signup_view ---
def signup_view(request):
    # ... (signup_view code - unchanged) ...
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in automatically
            messages.success(request, "Registration successful! Welcome.")
            return redirect("pages:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()
    return render(request, "pages/signup.html", {"form": form})


# --- Profile View (Verification for Step 5.4) ---
@login_required  # <<< Decorator exists
def profile_view(request):
    """User profile page, showing quiz attempt history."""
    # Get quiz attempts for the logged-in user
    # Order by the end time, most recent first
    user_attempts = QuizAttempt.objects.filter(user=request.user).order_by(
        "-end_time"
    )  # <<< Fetches attempts for user, orders correctly

    # Pass the attempts to the template context
    context = {"quiz_attempts": user_attempts}  # <<< Passes with correct key
    return render(request, "pages/profile.html", context)
