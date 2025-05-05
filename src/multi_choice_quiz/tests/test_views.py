# src/multi_choice_quiz/tests/test_views.py
# UPDATED (v3) based on Session 4 evaluation & test interference fix

import json
from datetime import datetime, timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from multi_choice_quiz.models import (
    Quiz,
    Question,
    Option,
    Topic,
    QuizAttempt,
)

# --- Replace existing logger setup with this ---
from .test_logging import setup_test_logging

logger = setup_test_logging(__name__, "multi_choice_quiz")
# --- End Replacement ---

User = get_user_model()


class QuizViewTests(TestCase):
    """Tests for the quiz views (home and detail)."""

    @classmethod
    def setUpTestData(cls):
        """Set up data needed by multiple tests (but avoid quiz creation here)."""
        # Only create data that won't be modified or deleted by individual tests
        cls.topic1 = Topic.objects.create(name="General Shared Topic")
        cls.test_user = User.objects.create_user(
            username="testuser_views_shared", password="password123"
        )

    def test_quiz_detail_view_loads(self):
        """Test that the quiz detail page loads correctly."""
        # --- ARRANGE: Create quiz and questions needed ONLY for this test ---
        # Use the shared topic from setUpTestData
        topic1 = Topic.objects.get(name="General Shared Topic")
        quiz1 = Quiz.objects.create(
            title="Detail Test Quiz 1", description="First Quiz"
        )
        quiz1.topics.add(topic1)
        q1 = Question.objects.create(quiz=quiz1, text="Detail Q1?", position=1)
        Option.objects.create(question=q1, text="DQ1 Opt1", position=1, is_correct=True)
        Option.objects.create(question=q1, text="DQ1 Opt2", position=2)
        q2 = Question.objects.create(quiz=quiz1, text="Detail Q2?", position=2)
        Option.objects.create(question=q2, text="DQ2 Opt1", position=1)
        Option.objects.create(question=q2, text="DQ2 Opt2", position=2, is_correct=True)
        # --- END ARRANGE ---

        # ACT
        url = reverse("multi_choice_quiz:quiz_detail", args=[quiz1.id])
        response = self.client.get(url)

        # ASSERT
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "multi_choice_quiz/index.html")
        self.assertContains(response, quiz1.title)
        self.assertContains(response, "Detail Q1?")
        self.assertIn("quiz_id", response.context)
        self.assertEqual(response.context["quiz_id"], quiz1.id)
        self.assertIn("quiz_data", response.context)
        try:
            raw_quiz_data = response.context["quiz_data"]
            if hasattr(raw_quiz_data, "__html__"):
                quiz_data_json = json.loads(str(raw_quiz_data))
            elif isinstance(raw_quiz_data, str):
                quiz_data_json = json.loads(raw_quiz_data)
            elif isinstance(raw_quiz_data, list):
                quiz_data_json = raw_quiz_data
            else:
                self.fail(f"quiz_data context type error: {type(raw_quiz_data)}")

            self.assertIsInstance(quiz_data_json, list)
            self.assertEqual(len(quiz_data_json), 2)
            self.assertEqual(quiz_data_json[0]["text"], "Detail Q1?")
            self.assertEqual(quiz_data_json[0]["answerIndex"], 0)
            self.assertEqual(quiz_data_json[1]["text"], "Detail Q2?")
            self.assertEqual(quiz_data_json[1]["answerIndex"], 1)
        except json.JSONDecodeError:
            self.fail("quiz_data in context is not valid JSON")
        except Exception as e:
            self.fail(f"Error checking quiz_data context: {e}")

    def test_home_view_loads_first_quiz(self):
        """Test that the home view loads the first available active quiz with questions."""
        # --- ARRANGE: Create quizzes/questions needed ONLY for this test ---
        # Use the shared topic
        topic1 = Topic.objects.get(name="General Shared Topic")
        # Create an older, active quiz *with no questions*
        quiz_no_questions = Quiz.objects.create(
            title="Home Test - No Qs", is_active=True
        )
        # Create an older, *inactive* quiz with questions (should be ignored)
        quiz_inactive = Quiz.objects.create(
            title="Home Test - Inactive", is_active=False
        )
        Question.objects.create(quiz=quiz_inactive, text="Inactive Q?", position=1)
        # Create the newest, *active* quiz *with questions* - THIS is the one we expect
        quiz_expected = Quiz.objects.create(
            title="Home Test - Expected", is_active=True
        )
        quiz_expected.topics.add(topic1)
        q_home = Question.objects.create(
            quiz=quiz_expected, text="Expected Q1?", position=1, is_active=True
        )
        Option.objects.create(
            question=q_home, text="ExQ1 Opt1", position=1, is_correct=True
        )
        # --- END ARRANGE ---

        # ACT
        url = reverse("multi_choice_quiz:home")
        response = self.client.get(url)

        # ASSERT
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "multi_choice_quiz/index.html")
        # It should load the latest *active* quiz that *has questions*
        self.assertEqual(response.context.get("quiz_id"), quiz_expected.id)
        self.assertContains(response, "Expected Q1?")
        self.assertNotContains(response, "Inactive Q?")
        self.assertNotContains(response, "What is the capital of France?")  # Demo check
        # Check that the quiz data loaded corresponds to the expected quiz
        try:
            raw_quiz_data = response.context["quiz_data"]
            if hasattr(raw_quiz_data, "__html__"):
                quiz_data_json = json.loads(str(raw_quiz_data))
            elif isinstance(raw_quiz_data, str):
                quiz_data_json = json.loads(raw_quiz_data)
            elif isinstance(raw_quiz_data, list):
                quiz_data_json = raw_quiz_data
            else:
                self.fail(f"quiz_data context type error: {type(raw_quiz_data)}")
            self.assertEqual(
                len(quiz_data_json), 1
            )  # Only one question in quiz_expected
            self.assertEqual(quiz_data_json[0]["text"], "Expected Q1?")
        except Exception as e:
            self.fail(f"Error checking quiz_data context for expected quiz: {e}")

    def test_home_view_loads_demo_when_no_quiz(self):
        """Test that the home view loads demo questions if no active quizzes with questions exist."""
        # --- ARRANGE: Ensure no suitable quizzes exist ---
        # Create an inactive quiz (should be ignored)
        quiz_inactive = Quiz.objects.create(
            title="Demo Test - Inactive", is_active=False
        )
        Question.objects.create(quiz=quiz_inactive, text="Inactive Q?", position=1)
        # Create an active quiz *with no questions* (should be ignored)
        Quiz.objects.create(title="Demo Test - No Qs", is_active=True)
        # Explicitly assert no *suitable* quizzes exist before acting
        self.assertFalse(
            Quiz.objects.filter(is_active=True, questions__isnull=False).exists()
        )
        # --- END ARRANGE ---

        # ACT
        url = reverse("multi_choice_quiz:home")
        response = self.client.get(url)

        # ASSERT
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "multi_choice_quiz/index.html")
        self.assertContains(response, "What is the capital of France?")  # Demo question
        self.assertIsNone(response.context.get("quiz_id"))
        try:
            raw_quiz_data = response.context["quiz_data"]
            if hasattr(raw_quiz_data, "__html__"):
                quiz_data_json = json.loads(str(raw_quiz_data))
            elif isinstance(raw_quiz_data, str):
                quiz_data_json = json.loads(raw_quiz_data)
            elif isinstance(raw_quiz_data, list):
                quiz_data_json = raw_quiz_data
            else:
                self.fail(f"quiz_data context type error (demo): {type(raw_quiz_data)}")

            self.assertIsInstance(quiz_data_json, list)
            self.assertEqual(len(quiz_data_json), 3)  # Demo questions count
            self.assertEqual(
                quiz_data_json[0]["text"], "What is the capital of France?"
            )
        except Exception as e:
            self.fail(f"Error checking demo quiz_data context: {e}")


# === Tests for submit_quiz_attempt view ===
# This class remains unchanged as its setup is self-contained and doesn't delete quizzes.
class SubmitQuizAttemptViewTests(TestCase):
    """Tests specifically for the submit_quiz_attempt API endpoint."""

    @classmethod
    def setUpTestData(cls):
        """Set up data for these specific tests."""
        cls.quiz = Quiz.objects.create(title="Submission Test Quiz")
        q = Question.objects.create(quiz=cls.quiz, text="Submit Q1", position=1)
        Option.objects.create(question=q, text="Opt A", position=1, is_correct=True)
        Option.objects.create(question=q, text="Opt B", position=2)

        cls.user = User.objects.create_user(
            username="submitter", password="password123"
        )
        cls.submit_url = reverse("multi_choice_quiz:submit_quiz_attempt")

        cls.fixed_end_time = datetime(2024, 5, 15, 10, 30, 0, tzinfo=timezone.utc)
        cls.valid_payload = {
            "quiz_id": cls.quiz.id,
            "score": 1,
            "total_questions": 1,
            "percentage": 100.0,
            "end_time": cls.fixed_end_time.isoformat(),
        }

    # Tests for submit_quiz_attempt remain unchanged...
    def test_submit_anonymous_success(self):
        """Test successful submission by an anonymous user."""
        self.assertEqual(QuizAttempt.objects.count(), 0)
        response = self.client.post(
            self.submit_url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuizAttempt.objects.count(), 1)
        attempt = QuizAttempt.objects.first()
        self.assertIsNone(attempt.user)
        self.assertEqual(attempt.quiz, self.quiz)
        self.assertEqual(attempt.score, self.valid_payload["score"])
        self.assertEqual(attempt.total_questions, self.valid_payload["total_questions"])
        self.assertEqual(attempt.percentage, self.valid_payload["percentage"])
        self.assertEqual(attempt.end_time, self.fixed_end_time)
        response_data = response.json()
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["attempt_id"], attempt.id)

    def test_submit_authenticated_success(self):
        """Test successful submission by an authenticated user."""
        self.client.force_login(self.user)
        self.assertEqual(QuizAttempt.objects.count(), 0)
        response = self.client.post(
            self.submit_url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuizAttempt.objects.count(), 1)
        attempt = QuizAttempt.objects.first()
        self.assertEqual(attempt.user, self.user)
        self.assertEqual(attempt.quiz, self.quiz)
        self.assertEqual(attempt.score, self.valid_payload["score"])
        self.assertEqual(attempt.end_time, self.fixed_end_time)
        response_data = response.json()
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["attempt_id"], attempt.id)
        self.client.logout()

    def test_submit_invalid_json(self):
        """Test submission with invalid JSON payload."""
        response = self.client.post(
            self.submit_url, data='{"invalid json",,}', content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid JSON data", response.content.decode())
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_missing_field(self):
        """Test submission with a missing required field."""
        payload = self.valid_payload.copy()
        del payload["score"]
        response = self.client.post(
            self.submit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields: score", response.content.decode())
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_invalid_data_type(self):
        """Test submission with an invalid data type for a field."""
        payload = self.valid_payload.copy()
        payload["score"] = "not-a-number"
        response = self.client.post(
            self.submit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid data type", response.content.decode())
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_invalid_end_time_format(self):
        """Test submission with an invalid end_time format."""
        payload = self.valid_payload.copy()
        payload["end_time"] = "15-05-2024 10:30:00"
        response = self.client.post(
            self.submit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid end_time format", response.content.decode())
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_non_existent_quiz(self):
        """Test submission with a quiz_id that does not exist."""
        payload = self.valid_payload.copy()
        payload["quiz_id"] = 99999
        response = self.client.post(
            self.submit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Quiz not found", response.content.decode())
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_get_request_not_allowed(self):
        """Test that GET requests to the submit endpoint are not allowed."""
        response = self.client.get(self.submit_url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(QuizAttempt.objects.count(), 0)
