from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from multi_choice_quiz.models import Quiz, Topic


def home(request):
    """Home page view with featured quizzes."""
    # Get some featured quizzes to display
    featured_quizzes = Quiz.objects.filter(is_active=True).order_by("-created_at")[:3]

    # Get some popular topics
    topics = Topic.objects.all()[:5]

    context = {
        "featured_quizzes": featured_quizzes,
        "topics": topics,
    }
    return render(request, "pages/home.html", context)


def quizzes(request):
    """View for browsing all quizzes."""
    # Get all active quizzes
    all_quizzes = Quiz.objects.filter(is_active=True).order_by("-created_at")

    # Get all topics for filtering
    topics = Topic.objects.all()

    # Filter by topic if specified
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
    """About page view."""
    return render(request, "pages/about.html")


def login_view(request):
    """Placeholder login page."""
    return render(request, "pages/login.html")


def signup_view(request):
    """Placeholder signup page."""
    return render(request, "pages/signup.html")


def profile_view(request):
    """Placeholder user profile page."""
    return render(request, "pages/profile.html")


def privacy_view(request):
    """Privacy policy page."""
    return render(request, "pages/privacy.html")


def terms_view(request):
    """Terms of service page."""
    return render(request, "pages/terms.html")
