# src/pages/tests/user_profile/test_phase5_verification.py

import pytest
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.core.exceptions import FieldDoesNotExist
import re
from multi_choice_quiz.models import QuizAttempt, Quiz  # Import necessary models

# Import the view function to check URL resolution (optional but good for confirmation)
from multi_choice_quiz.views import submit_quiz_attempt
from django.urls import reverse, NoReverseMatch, resolve  # <<< ADD resolve HERE

User = get_user_model()


# TestCase handles DB setup automatically
class Phase5VerificationTests(TestCase):
    """
    Verify the specific setup and outcomes of the revised Phase 5:
    Foundational Attempt Tracking & Profile Page Structure.
    """

    @classmethod
    def setUpTestData(cls):
        # Create a user needed for testing the logged-in profile view
        cls.test_user = User.objects.create_user(
            username="phase5verifier", password="password123"
        )
        # Create a quiz needed for attempt creation test (though not strictly necessary for field check)
        cls.quiz = Quiz.objects.create(title="Phase 5 Verification Quiz")

    def setUp(self):
        # Create a fresh client for each test
        self.client = Client()

    # --- Verification for Req 5.a ---
    def test_quiz_attempt_model_has_attempt_details_field(self):
        """Verify QuizAttempt model has attempt_details JSONField configured correctly."""
        try:
            field = QuizAttempt._meta.get_field("attempt_details")
        except FieldDoesNotExist:
            self.fail(
                "QuizAttempt model does not have a field named 'attempt_details'."
            )

        self.assertIsInstance(
            field,
            JSONField,
            "'attempt_details' field should be an instance of JSONField.",
        )
        self.assertTrue(
            field.null, "'attempt_details' field should allow NULL values (null=True)."
        )
        self.assertTrue(
            field.blank,
            "'attempt_details' field should allow blank values (blank=True).",
        )
        # Optional: Check help_text if you want to be very specific
        # self.assertIn("Stores detailed mistake data", field.help_text)

    # --- Verification for Req 5.b (URL Mapping) ---
    def test_submit_quiz_attempt_url_resolves(self):
        """Verify the URL for the quiz submission endpoint resolves correctly."""
        try:
            url = reverse("multi_choice_quiz:submit_quiz_attempt")
            # Check the path resolves as expected
            self.assertEqual(url, "/quiz/submit_attempt/")
            # Check it resolves to the correct view function
            resolved_func = resolve(url).func
            self.assertEqual(resolved_func, submit_quiz_attempt)
        except NoReverseMatch:
            self.fail(
                "Could not reverse URL name 'multi_choice_quiz:submit_quiz_attempt'. Check multi_choice_quiz/urls.py."
            )
        except Exception as e:
            self.fail(f"Error resolving 'multi_choice_quiz:submit_quiz_attempt': {e}")

    # --- Verification for Req 5.d (Login Required for Profile) ---
    def test_profile_view_requires_login(self):
        """Verify accessing profile page redirects anonymous users to login."""
        profile_url = reverse("pages:profile")
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 302, "Expected redirect status code")
        # Check the redirect points to the correct login URL with the 'next' parameter
        login_url = reverse("login")
        expected_redirect = f"{login_url}?next={profile_url}"
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

    # --- Verification for Req 5.f, 5.g (Basic Mockup 1 Structure) ---

    def test_profile_view_renders_mockup1_structure(self):
        """Verify profile page renders the basic Mockup 1 structure for logged-in users."""
        self.client.login(username="phase5verifier", password="password123")
        profile_url = reverse("pages:profile")
        response = self.client.get(profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/profile.html")

        content = response.content.decode()

        # 1. Stats section presence
        self.assertIn(
            "Quizzes Taken", content, "Stats section heading 'Quizzes Taken' not found."
        )

        # 2. Alpine tabs container
        self.assertIn(
            "x-data=\"{ activeTab: 'history' }\"",
            content,
            "Alpine tabs container (x-data) not found.",
        )

        # 3. Tab Buttons (History & Collections)
        self.assertRegex(
            content,
            r"<button[^>]*>\s*Quiz History\s*</button>",
            "'Quiz History' tab button not found or formatted unexpectedly.",
        )
        self.assertRegex(
            content,
            r"<button[^>]*>\s*Collections\s*</button>",
            "'Collections' tab button not found or formatted unexpectedly.",
        )

        # 4. Ensure removed tabs are NOT present
        self.assertNotIn(
            ">Favorites</button>",
            content,
            "'Favorites' tab button should not be present.",
        )
        self.assertNotIn(
            ">Created Quizzes</button>",
            content,
            "'Created Quizzes' tab button should not be present.",
        )

        # --- START MODIFIED ASSERTIONS for Tab Content ---
        # 5. Tab Content Area Headings - Check presence within the correct div
        # Use re.DOTALL to make '.' match newlines
        history_div_match = re.search(
            r'<div [^>]*x-show="activeTab === \'history\'"[^>]*>.*?</div>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(
            history_div_match, "History content div (x-show='history') not found."
        )
        if history_div_match:
            self.assertIn(
                "<h2",
                history_div_match.group(0),
                "No h2 tag found within history content div.",
            )
            self.assertIn(
                "Your Quiz History",
                history_div_match.group(0),
                "'Your Quiz History' heading text not found within history content div.",
            )

        collections_div_match = re.search(
            r'<div [^>]*x-show="activeTab === \'collections\'"[^>]*>.*?</div>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(
            collections_div_match,
            "Collections content div (x-show='collections') not found.",
        )
        if collections_div_match:
            self.assertIn(
                "<h2",
                collections_div_match.group(0),
                "No h2 tag found within collections content div.",
            )
            self.assertIn(
                "Your Collections",
                collections_div_match.group(0),
                "'Your Collections' heading text not found within collections content div.",
            )
        # --- END MODIFIED ASSERTIONS ---

    # ... (other tests remain the same) ...
