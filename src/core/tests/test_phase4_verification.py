# src/core/tests/test_phase4_verification.py

import pytest
from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet

from multi_choice_quiz.models import (
    Quiz,
    QuizAttempt,
    Topic,
)  # Import models needed for creating test data

# Mark all tests in this module as needing database access
# Keep this, it often helps pytest-django recognize the file needs DB setup
pytestmark = pytest.mark.django_db

User = get_user_model()


class TestPhase4Verification:
    """
    Verifies the successful completion of Phase 4:
    Basic User-Facing Profile & Navigation.
    Focuses on profile view access control and context data.
    """

    # --- START FIX: Change scope from 'class' to 'function' (default) ---
    @pytest.fixture
    def test_user(self, db):  # Add 'db' fixture from pytest-django
        """Fixture to create a standard test user for each test function."""
        # Use get_or_create to avoid potential issues if run multiple times within a session somehow
        user, created = User.objects.get_or_create(
            username="testuser_phase4", defaults={"email": "phase4@test.com"}
        )
        # Always set password in case user existed but password was different
        user.set_password("password123")
        user.save()
        print(f"\nEnsured user '{user.username}' exists for test.")
        return user

    @pytest.fixture
    def logged_in_client(self, test_user):
        """Fixture for a Django client logged in as the test user for each function."""
        client = Client()
        # Ensure login works, fail test if not
        logged_in = client.login(username=test_user.username, password="password123")
        assert logged_in, f"Client login failed for user '{test_user.username}'"
        print(f"Created logged-in client for user '{test_user.username}'.")
        return client

    # --- END FIX ---

    @pytest.fixture  # No scope needed, doesn't interact with DB
    def anonymous_client(self):
        """Fixture for an anonymous Django client."""
        return Client()

    # --- Step 4.1: Create/Verify Profile View & URL (Login Required) ---

    def test_profile_url_resolves(self):
        """Verify the '/profile/' URL resolves to the 'pages:profile' name."""
        expected_url_path = "/profile/"
        try:
            profile_url = reverse("pages:profile")
            assert (
                profile_url == expected_url_path
            ), f"reverse('pages:profile') resolved to '{profile_url}', expected '{expected_url_path}'"
        except NoReverseMatch:
            pytest.fail(
                "URL pattern named 'pages:profile' could not be reversed. Check pages/urls.py."
            )

    def test_profile_view_requires_login(self, anonymous_client):
        """Verify accessing profile page when not logged in redirects to login."""
        profile_url = reverse("pages:profile")
        response = anonymous_client.get(profile_url)

        assert (
            response.status_code == 302
        ), f"Expected status code 302 (redirect) for anonymous access to {profile_url}, but got {response.status_code}"

        login_url = reverse("login")
        # Check redirect URL using response.url (handles potential host/scheme)
        # The test client automatically follows redirects, so response.url is the final destination
        assert response.url.startswith(
            login_url
        ), f"Expected redirect URL to start with '{login_url}', but got '{response.url}'"
        assert (
            f"next={profile_url}" in response.url
        ), f"Redirect URL should contain '?next={profile_url}', but got '{response.url}'"

    def test_profile_view_loads_for_logged_in_user(self, logged_in_client):
        """Verify profile page loads successfully for an authenticated user."""
        profile_url = reverse("pages:profile")
        response = logged_in_client.get(profile_url)

        assert (
            response.status_code == 200
        ), f"Expected status code 200 for authenticated access to {profile_url}, but got {response.status_code}"

    # --- Step 4.3: Display User History on Profile ---

    def test_profile_view_context_has_quiz_attempts(self, logged_in_client):
        """Verify the profile view context includes 'quiz_attempts'."""
        profile_url = reverse("pages:profile")
        response = logged_in_client.get(profile_url)

        assert response.status_code == 200
        assert (
            "quiz_attempts" in response.context
        ), "Context dictionary for profile view is missing the 'quiz_attempts' key."

        assert isinstance(
            response.context["quiz_attempts"], (QuerySet, list)
        ), f"'quiz_attempts' in context should be a QuerySet or list, but got type {type(response.context['quiz_attempts'])}."

    def test_profile_view_context_shows_correct_attempts(
        self, logged_in_client, test_user
    ):
        """Verify 'quiz_attempts' in context contains attempts ONLY for the logged-in user."""
        # Create a dummy quiz
        quiz = Quiz.objects.create(title="Phase 4 Test Quiz")
        topic, _ = Topic.objects.get_or_create(name="Phase 4 Testing")
        quiz.topics.add(topic)

        # Create an attempt for the test user
        attempt1 = QuizAttempt.objects.create(
            quiz=quiz, user=test_user, score=8, total_questions=10, percentage=80.0
        )
        # Create an attempt for another user (should NOT appear)
        other_user = User.objects.create_user(
            username="otheruser_p4", password="password123"
        )  # Use unique username
        attempt2 = QuizAttempt.objects.create(
            quiz=quiz, user=other_user, score=5, total_questions=10, percentage=50.0
        )
        # Create an anonymous attempt (should NOT appear)
        attempt3 = QuizAttempt.objects.create(
            quiz=quiz, user=None, score=3, total_questions=10, percentage=30.0
        )

        profile_url = reverse("pages:profile")
        response = logged_in_client.get(profile_url)

        assert response.status_code == 200
        context_attempts = response.context.get("quiz_attempts")
        assert context_attempts is not None

        # Convert QuerySet to list for easier comparison if necessary, or use QuerySet methods
        context_attempts_list = list(context_attempts)

        assert (
            attempt1 in context_attempts_list
        ), "The test user's attempt was not found in the profile context."
        assert (
            len(context_attempts_list) == 1
        ), f"Expected exactly 1 attempt for the test user, but found {len(context_attempts_list)}."
        # Check IDs to be sure
        attempt_ids = [a.id for a in context_attempts_list]
        assert attempt1.id in attempt_ids
        assert (
            attempt2.id not in attempt_ids
        ), "Another user's attempt was incorrectly included in the profile context."
        assert (
            attempt3.id not in attempt_ids
        ), "An anonymous attempt was incorrectly included in the profile context."
