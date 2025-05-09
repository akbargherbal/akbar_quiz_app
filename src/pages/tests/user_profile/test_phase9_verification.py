# src/pages/tests/user_profile/test_phase9_verification.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages

from pages.models import (
    SystemCategory,
    UserCollection,
)  # Assuming models are in pages.models
from multi_choice_quiz.models import (
    Quiz,
    Question,
    QuizAttempt,
)  # For creating test data
from multi_choice_quiz.tests.test_logging import setup_test_logging

logger = setup_test_logging(__name__, "pages_phase9_verification")
User = get_user_model()


class Phase9ProfileAndCollectionsVerificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="phase9user", password="password123", email="initial@example.com"
        )
        cls.other_user = User.objects.create_user(
            username="otheruser", password="password123", email="other@example.com"
        )

        # Data for profile stats and collections (can be expanded)
        cls.quiz1 = Quiz.objects.create(title="P9 Quiz 1")
        Question.objects.create(
            quiz=cls.quiz1, text="Q1"
        )  # Add a question to make it "active" for some views

        QuizAttempt.objects.create(
            user=cls.user, quiz=cls.quiz1, score=1, total_questions=1, percentage=100.0
        )
        UserCollection.objects.create(user=cls.user, name="My P9 Collection")

        # Data for category browsing
        cls.cat1 = SystemCategory.objects.create(name="P9 Category 1", slug="p9-cat-1")
        cls.cat1.quizzes.add(cls.quiz1)

    def setUp(self):
        self.client = Client()
        self.client.login(username="phase9user", password="password123")
        self.edit_profile_url = reverse("pages:edit_profile")
        self.profile_url = reverse("pages:profile")

    # --- Tests for Step 9.7: Basic Edit Profile ---
    def test_edit_profile_page_loads_get(self):
        """Test that the edit profile page loads correctly with a GET request."""
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/edit_profile.html")
        self.assertIn("form", response.context)
        # Check if form is pre-filled with user's current email
        self.assertEqual(
            response.context["form"]["email"].value(), "initial@example.com"
        )

    def test_edit_profile_requires_login(self):
        """Test that accessing edit profile page requires login."""
        self.client.logout()
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        self.assertIn(reverse("login"), response.url)

    def test_edit_profile_successful_post(self):
        """Test successful profile update (email change)."""
        new_email = "updated@example.com"
        post_data = {"email": new_email}

        response = self.client.post(self.edit_profile_url, post_data)

        self.assertEqual(response.status_code, 302)  # Should redirect on success
        self.assertRedirects(response, self.profile_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)

        # Check for success message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(
            str(messages_list[0]), "Your profile has been updated successfully!"
        )

    def test_edit_profile_post_invalid_email(self):
        """Test profile update with an invalid email."""
        invalid_email = "not-an-email"
        post_data = {"email": invalid_email}

        response = self.client.post(self.edit_profile_url, post_data)

        self.assertEqual(response.status_code, 200)  # Should re-render form with errors
        self.assertTemplateUsed(response, "pages/edit_profile.html")
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)
        self.assertIn(
            "email", response.context["form"].errors
        )  # Check email field has errors

        # Ensure email was not changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "initial@example.com")

        # Check for error message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Please correct the errors below.")

    # --- Placeholder for tests for dynamic stats/collections on profile (Req 9.c, 9.d) ---
    def test_profile_displays_dynamic_stats_and_collections(self):
        # This test would verify that self.user's stats (1 attempt, 100% avg)
        # and "My P9 Collection" are displayed correctly on the profile page.
        # It can be more detailed than the ones in test_views.py if needed.
        # For now, let's ensure it runs without error.
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quizzes Taken")
        self.assertContains(response, "1")  # Based on setUpTestData
        self.assertContains(response, "Average Score")
        self.assertContains(response, "100%")  # Based on setUpTestData
        self.assertContains(response, "My P9 Collection")

    # --- Placeholder for tests for SystemCategory filtering (Req 9.e, 9.f) ---
    def test_quizzes_page_filters_by_system_category(self):
        # This test would verify that navigating to /quizzes/?category=p9-cat-1
        # correctly filters and shows only self.quiz1.
        # For now, let's ensure it runs without error.
        quizzes_url = reverse("pages:quizzes")
        response = self.client.get(f"{quizzes_url}?category={self.cat1.slug}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.quiz1.title)
        self.assertIn(
            self.cat1.name, response.content.decode()
        )  # Check category filter display

    # --- Placeholder for tests for homepage SystemCategory display (Req 9.g) ---
    def test_homepage_displays_popular_system_categories(self):
        # This test would verify that self.cat1 (P9 Category 1) appears on the homepage
        # if it meets the criteria for "popular".
        # For now, let's ensure it runs without error.
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        # Check if "P9 Category 1" is displayed (it has 1 active quiz with questions)
        # The view orders by -num_active_quizzes, name. So it should be among the top 5 if there aren't 5 others with more quizzes.
        self.assertContains(response, self.cat1.name)
