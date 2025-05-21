# src/pages/views.py

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Exists, OuterRef
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.views.decorators.http import require_POST

from multi_choice_quiz.models import Quiz, Question, QuizAttempt
from .models import UserCollection, SystemCategory
from .forms import SignUpForm, EditProfileForm, UserCollectionForm
from django.utils.http import (
    url_has_allowed_host_and_scheme,
)


try:
    from multi_choice_quiz.tests.test_logging import setup_test_logging

    logger = logging.getLogger(__name__)
except (ImportError, ModuleNotFoundError):
    logger = logging.getLogger(__name__)
    logger.info(
        "Test logging module not found. Using standard logging for pages.views."
    )


def home(request):
    base_quizzes_qs = (
        Quiz.objects.filter(is_active=True, questions__isnull=False)
        .distinct()
        .select_related()
        .prefetch_related("system_categories")
    )

    featured_quizzes_list = []

    # log view and name of file:
    logger.info(f"View: home, File: {__file__}")

    if request.user.is_authenticated:
        attempted_quiz_ids = list(
            QuizAttempt.objects.filter(user=request.user)
            .values_list("quiz_id", flat=True)
            .distinct()
        )

        unattempted_qs = base_quizzes_qs.exclude(id__in=attempted_quiz_ids)
        unattempted_featured = list(unattempted_qs.order_by("-created_at", "-id")[:3])
        featured_quizzes_list.extend(unattempted_featured)

        if len(featured_quizzes_list) < 3:
            num_needed = 3 - len(featured_quizzes_list)
            selected_ids = [q.id for q in featured_quizzes_list]
            additional_qs = base_quizzes_qs.exclude(id__in=selected_ids)
            additional_featured = list(
                additional_qs.order_by("-created_at", "-id")[:num_needed]
            )
            featured_quizzes_list.extend(additional_featured)
    else:
        featured_quizzes_list = list(base_quizzes_qs.order_by("-created_at", "-id")[:3])

    popular_categories = (
        SystemCategory.objects.annotate(
            num_active_quizzes=Count(
                "quizzes",
                filter=Q(quizzes__is_active=True, quizzes__questions__isnull=False),
            )
        )
        .filter(num_active_quizzes__gt=0)
        .order_by("-num_active_quizzes", "name")[:16]
    )
    context = {
        "featured_quizzes": featured_quizzes_list,
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
    quiz_list_query = (
        Quiz.objects.filter(is_active=True, questions__isnull=False)
        .distinct()
        .select_related()
        .prefetch_related("system_categories", "questions")
    )

    categories = SystemCategory.objects.all().order_by("name")
    selected_category = None
    category_slug = request.GET.get("category")

    if category_slug:
        try:
            selected_category = SystemCategory.objects.get(slug=category_slug)
            quiz_list_query = quiz_list_query.filter(
                system_categories=selected_category
            )
        except SystemCategory.DoesNotExist:
            selected_category = None

    if request.user.is_authenticated:
        quiz_list_annotated_and_ordered = quiz_list_query.annotate(
            has_attempted=Exists(
                QuizAttempt.objects.filter(quiz_id=OuterRef("pk"), user=request.user)
            )
        ).order_by("has_attempted", "-created_at", "-id")
        final_quiz_list_for_pagination = list(quiz_list_annotated_and_ordered)
    else:
        final_quiz_list_for_pagination = list(
            quiz_list_query.order_by("-created_at", "-id")
        )

    paginator = Paginator(final_quiz_list_for_pagination, 9)
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
    user_attempts_qs = (  # Changed variable name to indicate it's a queryset initially
        QuizAttempt.objects.filter(user=user)
        .order_by("-end_time")
        .select_related("quiz")
    )
    user_collections = (
        UserCollection.objects.filter(user=user)
        .prefetch_related("quizzes__questions")
        .order_by("name")
    )
    stats = user_attempts_qs.aggregate(  # Use the queryset for aggregate
        total_attempts=Count("id"), average_score=Avg("percentage")
    )
    average_score = stats.get("average_score")
    if average_score is None:
        average_score = 0

    # --- START: Calculate attempt counts per quiz for this user ---
    quiz_attempt_counts_raw = (
        QuizAttempt.objects.filter(user=user)
        .values("quiz_id")
        .annotate(count=Count("id"))
        .order_by("quiz_id")
    )

    quiz_attempt_counts_dict = {
        item["quiz_id"]: item["count"] for item in quiz_attempt_counts_raw
    }
    logger.debug(
        f"Quiz attempt counts for user {user.username}: {quiz_attempt_counts_dict}"
    )
    # --- END: Calculate attempt counts per quiz ---

    # Attach the count to each attempt object for easier template access
    # This is one way; another is to pass quiz_attempt_counts_dict directly
    # and look up in the template. For simplicity in the template, let's try attaching.
    # Note: This modifies the queryset results in memory.
    user_attempts_list = []
    for attempt in user_attempts_qs:  # Iterate over the original queryset
        attempt.individual_quiz_attempt_count = quiz_attempt_counts_dict.get(
            attempt.quiz.id, 0
        )
        user_attempts_list.append(attempt)

    context = {
        "quiz_attempts": user_attempts_list,  # Pass the modified list
        "user_collections": user_collections,
        "stats": {
            "total_taken": stats.get("total_attempts", 0),
            "avg_score_percent": round(average_score),
        },
        "quiz_attempt_counts": quiz_attempt_counts_dict,  # Also pass the dict for flexibility or alternative use
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


@login_required
def create_collection_view(request):
    if request.method == "POST":
        form = UserCollectionForm(request.POST)
        if form.is_valid():
            try:
                collection = form.save(commit=False)
                collection.user = request.user
                collection.save()
                messages.success(
                    request, f"Collection '{collection.name}' created successfully!"
                )
                return redirect("pages:profile")
            except IntegrityError:
                form.add_error(
                    "name",
                    "You already have a collection with this name. Please choose a different name.",
                )
                messages.error(
                    request,
                    "This collection name already exists for your account. Please choose a different name.",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCollectionForm()

    return render(request, "pages/create_collection.html", {"form": form})


@login_required
@require_POST
def remove_quiz_from_collection_view(request, collection_id, quiz_id):
    collection = get_object_or_404(UserCollection, id=collection_id, user=request.user)
    quiz_to_remove = get_object_or_404(Quiz, id=quiz_id)

    if quiz_to_remove in collection.quizzes.all():
        collection.quizzes.remove(quiz_to_remove)
        messages.success(
            request,
            f"Quiz '{quiz_to_remove.title}' removed from collection '{collection.name}'.",
        )
        logger.info(
            f"User {request.user.username} removed quiz '{quiz_to_remove.title}' (ID: {quiz_id}) from collection '{collection.name}' (ID: {collection_id})."
        )
    else:
        messages.warning(
            request,
            f"Quiz '{quiz_to_remove.title}' was not found in collection '{collection.name}'.",
        )
        logger.warning(
            f"User {request.user.username} tried to remove quiz ID {quiz_id} from collection ID {collection_id}, but quiz was not in it."
        )

    return redirect("pages:profile")


@login_required
def select_collection_for_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    user_collections = UserCollection.objects.filter(user=request.user).order_by("name")

    if not user_collections.exists():
        messages.info(
            request,
            "You don't have any collections yet. Please create one first to add quizzes.",
        )
        return redirect("pages:create_collection")

    next_url = request.GET.get("next")

    context = {
        "quiz": quiz,
        "collections": user_collections,
        "next_url": next_url,
    }
    return render(request, "pages/select_collection_for_quiz.html", context)


@login_required
@require_POST
def add_quiz_to_selected_collection_view(request, quiz_id, collection_id):
    quiz_to_add = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    collection = get_object_or_404(UserCollection, id=collection_id, user=request.user)

    if quiz_to_add not in collection.quizzes.all():
        collection.quizzes.add(quiz_to_add)
        messages.success(
            request,
            f"Quiz '{quiz_to_add.title}' added to collection '{collection.name}'.",
        )
        logger.info(
            f"User {request.user.username} added quiz '{quiz_to_add.title}' (ID: {quiz_id}) to collection '{collection.name}' (ID: {collection_id})."
        )
    else:
        messages.info(
            request,
            f"Quiz '{quiz_to_add.title}' is already in collection '{collection.name}'.",
        )
        logger.info(
            f"User {request.user.username} tried to add quiz ID {quiz_id} to collection ID {collection_id}, but it was already there."
        )

    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, request.get_host()):
        logger.info(f"Redirecting to 'next' URL: {next_url}")
        return redirect(next_url)
    elif next_url:
        logger.warning(
            f"Invalid 'next' URL provided: {next_url}. Defaulting to profile."
        )

    logger.info("No valid 'next' URL. Redirecting to profile page.")
    return redirect("pages:profile")
