# src/pages/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.views.decorators.http import require_POST

from multi_choice_quiz.models import Quiz, Question, QuizAttempt
from .models import UserCollection, SystemCategory
from .forms import SignUpForm, EditProfileForm, UserCollectionForm


# Attempt to import test-specific logging, fall back if not found (e.g., in production)
try:
    from multi_choice_quiz.tests.test_logging import setup_test_logging
    # Assuming setup_test_logging returns a logger instance or configures the root logger.
    # If it configures a specific logger, you might want to get it by name here.
    # For example, if setup_test_logging configures a logger named 'pages.views':
    # setup_test_logging(__name__, "your_log_file_for_pages_views.log") # If it configures and you get it later
    logger = logging.getLogger(__name__) # Get the logger for the current module
    # If setup_test_logging directly returns the logger:
    # logger = setup_test_logging(__name__, "your_log_file_for_pages_views.log")
    logger.info("Successfully initialized test-specific logging for pages.views.")

except (ImportError, ModuleNotFoundError):
    # Fallback to standard logging if the test module isn't found
    logger = logging.getLogger(__name__)
    logger.info("Test logging module not found. Using standard logging for pages.views.")



logger = setup_test_logging(__name__, "pages")


# ... (home, about, signup_view, quizzes, profile_view, edit_profile_view, create_collection_view, remove_quiz_from_collection_view, select_collection_for_quiz_view views remain the same) ...
def home(request):
    # ... (home view remains the same) ...
    featured_quizzes = (
        Quiz.objects.filter(is_active=True, questions__isnull=False)
        .distinct()
        .order_by("-created_at", "-id")[:3]
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
    # ... (about view remains the same) ...
    return render(request, "pages/about.html")


def signup_view(request):
    # ... (signup_view remains the same) ...
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
    # ... (quizzes view remains the same) ...
    quiz_list = (
        Quiz.objects.filter(is_active=True)
        .select_related()
        .prefetch_related("system_categories")
        .order_by("-created_at", "-id")
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
    # ... (profile_view remains the same) ...
    user = request.user
    user_attempts = (
        QuizAttempt.objects.filter(user=user)
        .order_by("-end_time")
        .select_related("quiz")
    )
    user_collections = (
        UserCollection.objects.filter(user=user)
        .prefetch_related("quizzes__questions")
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
    # ... (edit_profile_view remains the same) ...
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
    # ... (create_collection_view remains the same) ...
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
    # ... (remove_quiz_from_collection_view remains the same) ...
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
    # ... (select_collection_for_quiz_view remains the same) ...
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    user_collections = UserCollection.objects.filter(user=request.user).order_by("name")

    if not user_collections.exists():
        messages.info(
            request,
            "You don't have any collections yet. Please create one first to add quizzes.",
        )
        return redirect("pages:create_collection")

    context = {
        "quiz": quiz,
        "collections": user_collections,
    }
    return render(request, "pages/select_collection_for_quiz.html", context)


# --- NEW VIEW for adding a quiz to a specific collection ---
@login_required
@require_POST  # This action modifies data, so it should be POST
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

    # Redirect back to the page where the user can select another collection for the same quiz,
    # or to their profile, or to the quiz page. Redirecting to profile is simple.
    # Redirecting back to select_collection_for_quiz_view might be good if they want to add to multiple.
    # For now, let's redirect to profile.
    return redirect("pages:profile")
