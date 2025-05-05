# src/pages/tests/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from multi_choice_quiz.models import Quiz, QuizAttempt  # Import models
from django.utils import timezone  # To set end_time

# --- Replace existing logger setup with this ---
from multi_choice_quiz.tests.test_logging import setup_test_logging  # CORRECT

logger = setup_test_logging(__name__, "pages")
# --- End Replacement ---

# Get the User model
User = get_user_model()


class PagesViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create users for testing
        cls.test_user = User.objects.create_user(
            username="testuser_views", password="password123", email="test@example.com"
        )
        # Create another user for testing empty state
        cls.no_attempts_user = User.objects.create_user(
            username="noattempts_user", password="password123"
        )

        # Create some quizzes
        cls.quiz1 = Quiz.objects.create(title="History Quiz")
        cls.quiz2 = Quiz.objects.create(title="Science Quiz")

        # Create some attempts for test_user
        cls.attempt1 = QuizAttempt.objects.create(
            user=cls.test_user,
            quiz=cls.quiz1,
            score=8,
            total_questions=10,
            percentage=80.0,
            end_time=timezone.now() - timezone.timedelta(days=1),  # Set past end time
        )
        cls.attempt2 = QuizAttempt.objects.create(
            user=cls.test_user,
            quiz=cls.quiz2,
            score=5,
            total_questions=5,
            percentage=100.0,
            end_time=timezone.now(),  # Set recent end time
        )

    def setUp(self):
        # Create a new client for each test
        self.client = Client()

    def test_home_page_loads(self):
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertTemplateUsed(response, "pages/base.html")

    def test_quizzes_page_loads(self):
        response = self.client.get(reverse("pages:quizzes"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/quizzes.html")

    def test_about_page_loads(self):
        response = self.client.get(reverse("pages:about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/about.html")

    # --- START CORRECTION 1 ---
    # def test_login_page_loads(self):
    #     # This test is no longer relevant as pages:login doesn't exist.
    #     # The actual login page is at reverse('login') -> /accounts/login/
    #     # We can test that directly if needed, but it's testing Django's view.
    #     # It's better to test the *template* rendering if we customize it.
    #     # Let's test that accessing the built-in login URL works.
    #     response = self.client.get(reverse("login"))
    #     self.assertEqual(response.status_code, 200)
    #     # Check if it uses the correct template (adjust path if necessary)
    #     self.assertTemplateUsed(response, "registration/login.html")
    # --- END CORRECTION 1 ---

    def test_signup_page_loads(self):
        response = self.client.get(reverse("pages:signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/signup.html")

    # --- Test Profile Page Access ---
    def test_profile_page_redirects_when_not_logged_in(self):
        response = self.client.get(reverse("pages:profile"))
        self.assertEqual(response.status_code, 302)  # Should redirect

        # --- START CORRECTION 2 ---
        # Check if it redirects to the correct built-in login page
        expected_redirect_url = f"{reverse('login')}?next={reverse('pages:profile')}"
        # --- END CORRECTION 2 ---

        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )

    def test_profile_page_loads_when_logged_in(self):
        # Log in the test user
        login_successful = self.client.login(
            username="testuser_views", password="password123"
        )
        self.assertTrue(login_successful, "Test user login failed")

        response = self.client.get(reverse("pages:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/profile.html")
        # Check that the user object in context matches the logged-in user
        self.assertEqual(response.context["user"], self.test_user)

    # --- START NEW/MODIFIED TESTS for Step 3.3 ---
    def test_profile_page_displays_user_history(self):
        """Verify quiz attempts are passed to context and rendered."""
        # Log in the user who has attempts
        self.client.login(username="testuser_views", password="password123")
        response = self.client.get(reverse("pages:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/profile.html")

        # Check context contains the attempts, ordered correctly (most recent first)
        self.assertIn("quiz_attempts", response.context)
        attempts_in_context = response.context["quiz_attempts"]
        self.assertEqual(len(attempts_in_context), 2)
        self.assertEqual(attempts_in_context[0], self.attempt2)  # Most recent
        self.assertEqual(attempts_in_context[1], self.attempt1)

        # Check rendered HTML contains info from the attempts
        content = response.content.decode()
        self.assertIn(self.quiz1.title, content)  # History Quiz title
        self.assertIn(f"{self.attempt1.percentage:.0f}%", content)  # 80%
        self.assertIn(self.quiz2.title, content)  # Science Quiz title
        self.assertIn(f"{self.attempt2.percentage:.0f}%", content)  # 100%
        self.assertNotIn("You haven't completed any quizzes yet.", content)

        # Check the "Take Again" link URL for one of the attempts
        take_again_url_quiz1 = reverse(
            "multi_choice_quiz:quiz_detail", args=[self.quiz1.id]
        )
        self.assertIn(f'href="{take_again_url_quiz1}"', content)

    def test_profile_page_empty_history_message(self):
        """Verify the empty state message is shown for users with no attempts."""
        # Log in the user who has NO attempts
        self.client.login(username="noattempts_user", password="password123")
        response = self.client.get(reverse("pages:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/profile.html")

        # Check context contains an empty queryset for attempts
        self.assertIn("quiz_attempts", response.context)
        self.assertEqual(len(response.context["quiz_attempts"]), 0)

        # Check rendered HTML contains the empty message
        content = response.content.decode()
        self.assertIn("You haven't completed any quizzes yet.", content)
        self.assertNotIn(
            self.quiz1.title, content
        )  # Ensure no attempt details are shown

    # --- END NEW/MODIFIED TESTS for Step 3.3 ---
