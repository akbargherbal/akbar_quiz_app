# src/pages/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from multi_choice_quiz.models import Quiz, Question, QuizAttempt
from .models import UserCollection, SystemCategory
from .forms import SignUpForm, EditProfileForm

from multi_choice_quiz.tests.test_logging import setup_test_logging

logger = setup_test_logging(__name__, "pages")


def home(request):
    """Displays the homepage with featured quizzes and popular categories."""
    featured_quizzes = (
        Quiz.objects.filter(is_active=True, questions__isnull=False)
        .distinct()
        .order_by("-created_at", "-id")[:3]  # <<< MODIFIED
    )
    popular_categories = (
        SystemCategory.objects.annotate(
            num_active_quizzes=Count(
                "quizzes",
                filter=Q(quizzes__is_active=True, quizzes__questions__isnull=False),
            )
        )
        .filter(num_active_quizzes__gt=0)
        .order_by("-num_active_quizzes", "name")[:5]
    )
    context = {
        "featured_quizzes": featured_quizzes,
        "popular_categories": popular_categories,
    }
    return render(request, "pages/home.html", context)


def about(request):
    return render(request, "pages/about.html")


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome.")
            return redirect("pages:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()
    return render(request, "pages/signup.html", {"form": form})


def quizzes(request):
    quiz_list = (
        Quiz.objects.filter(is_active=True)
        .select_related()
        .prefetch_related("system_categories")
        .order_by("-created_at", "-id")  # <<< MODIFIED
    )
    categories = SystemCategory.objects.all().order_by("name")
    selected_category = None
    category_slug = request.GET.get("category")
    if category_slug:
        try:
            selected_category = SystemCategory.objects.get(slug=category_slug)
            quiz_list = quiz_list.filter(system_categories=selected_category)
        except SystemCategory.DoesNotExist:
            selected_category = None

    paginator = Paginator(quiz_list, 9)
    page_number = request.GET.get("page")
    try:
        quizzes_page = paginator.page(page_number)
    except PageNotAnInteger:
        quizzes_page = paginator.page(1)
    except EmptyPage:
        quizzes_page = paginator.page(paginator.num_pages)

    context = {
        "quizzes": quizzes_page,
        "categories": categories,
        "selected_category": selected_category,
    }
    return render(request, "pages/quizzes.html", context)


@login_required
def profile_view(request):
    user = request.user
    user_attempts = (
        QuizAttempt.objects.filter(user=user)
        .order_by("-end_time")
        .select_related("quiz")
    )
    user_collections = (
        UserCollection.objects.filter(user=user)
        .prefetch_related("quizzes")
        .order_by("name")
    )
    stats = user_attempts.aggregate(
        total_attempts=Count("id"), average_score=Avg("percentage")
    )
    average_score = stats.get("average_score")
    if average_score is None:
        average_score = 0
    context = {
        "quiz_attempts": user_attempts,
        "user_collections": user_collections,
        "stats": {
            "total_taken": stats.get("total_attempts", 0),
            "avg_score_percent": round(average_score),
        },
    }
    return render(request, "pages/profile.html", context)


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("pages:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EditProfileForm(instance=request.user)

    return render(request, "pages/edit_profile.html", {"form": form})
