# src/multi_choice_quiz/tests/test_views.py

import json
from datetime import datetime, timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from unittest.mock import patch  # Import patch

from multi_choice_quiz.models import (
    Quiz,
    Question,
    Option,
    Topic,
    QuizAttempt,
)  # Add QuizAttempt

User = get_user_model()


class QuizViewTests(TestCase):
    """Tests for the quiz views."""

    @classmethod
    def setUpTestData(cls):
        """Set up data for the whole TestCase."""
        cls.topic1 = Topic.objects.create(name="General")
        cls.quiz1 = Quiz.objects.create(title="Quiz 1", description="First Quiz")
        cls.quiz1.topics.add(cls.topic1)

        cls.q1 = Question.objects.create(quiz=cls.quiz1, text="Question 1?", position=1)
        cls.o1_1 = Option.objects.create(
            question=cls.q1, text="Q1 Opt1", position=1, is_correct=True
        )
        cls.o1_2 = Option.objects.create(question=cls.q1, text="Q1 Opt2", position=2)

        cls.q2 = Question.objects.create(quiz=cls.quiz1, text="Question 2?", position=2)
        cls.o2_1 = Option.objects.create(question=cls.q2, text="Q2 Opt1", position=1)
        cls.o2_2 = Option.objects.create(
            question=cls.q2, text="Q2 Opt2", position=2, is_correct=True
        )

        cls.test_user = User.objects.create_user(
            username="testuser", password="password123"
        )

    # Test for quiz_detail view (can be expanded)
    def test_quiz_detail_view_loads(self):
        """Test that the quiz detail page loads correctly."""
        url = reverse("multi_choice_quiz:quiz_detail", args=[self.quiz1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "multi_choice_quiz/index.html")
        self.assertContains(response, self.quiz1.title)
        self.assertContains(response, "Question 1?")
        self.assertIn("quiz_id", response.context)
        self.assertEqual(response.context["quiz_id"], self.quiz1.id)
        self.assertIn("quiz_data", response.context)
        # Check if quiz_data is correctly formatted JSON in the context
        try:
            quiz_data_json = json.loads(response.context["quiz_data"])
            self.assertIsInstance(quiz_data_json, list)
            self.assertEqual(len(quiz_data_json), 2)  # Should have 2 questions
            self.assertEqual(quiz_data_json[0]["text"], "Question 1?")
            self.assertEqual(
                quiz_data_json[0]["answerIndex"], 0
            )  # Correct option is position 1 -> index 0
            self.assertEqual(quiz_data_json[1]["text"], "Question 2?")
            self.assertEqual(
                quiz_data_json[1]["answerIndex"], 1
            )  # Correct option is position 2 -> index 1
        except json.JSONDecodeError:
            self.fail("quiz_data in context is not valid JSON")
        except TypeError:
            # Handle if context['quiz_data'] is not a string (e.g., already decoded)
            # This might happen if mark_safe is not used or if tests bypass template rendering aspects
            if isinstance(response.context["quiz_data"], list):
                quiz_data_json = response.context["quiz_data"]
                self.assertIsInstance(quiz_data_json, list)
                self.assertEqual(len(quiz_data_json), 2)
            else:
                self.fail("quiz_data context variable is not a list or JSON string")


# === Tests for submit_quiz_attempt view ===


class SubmitQuizAttemptViewTests(TestCase):
    """Tests specifically for the submit_quiz_attempt API endpoint."""

    @classmethod
    def setUpTestData(cls):
        """Set up data for these specific tests."""
        cls.quiz = Quiz.objects.create(title="Submission Test Quiz")
        # Add at least one question so total_questions makes sense
        q = Question.objects.create(quiz=cls.quiz, text="Submit Q1", position=1)
        Option.objects.create(question=q, text="Opt A", position=1, is_correct=True)
        Option.objects.create(question=q, text="Opt B", position=2)

        cls.user = User.objects.create_user(
            username="submitter", password="password123"
        )
        cls.submit_url = reverse("multi_choice_quiz:submit_quiz_attempt")

        # Use a fixed datetime for predictable testing
        cls.fixed_end_time = datetime(2024, 5, 15, 10, 30, 0, tzinfo=timezone.utc)
        cls.valid_payload = {
            "quiz_id": cls.quiz.id,
            "score": 1,
            "total_questions": 1,
            "percentage": 100.0,
            "end_time": cls.fixed_end_time.isoformat(),  # Use fixed time
        }

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
        # Compare datetimes carefully, considering potential microsecond differences if not controlled
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
        self.assertEqual(attempt.user, self.user)  # Check user association
        self.assertEqual(attempt.quiz, self.quiz)
        self.assertEqual(attempt.score, self.valid_payload["score"])
        self.assertEqual(attempt.end_time, self.fixed_end_time)
        response_data = response.json()
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["attempt_id"], attempt.id)
        self.client.logout()  # Clean up login state

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
        del payload["score"]  # Remove a required field
        response = self.client.post(
            self.submit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields: score", response.content.decode())
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_invalid_data_type(self):
        """Test submission with an invalid data type for a field."""
        payload = self.valid_payload.copy()
        payload["score"] = "not-a-number"  # Invalid type
        response = self.client.post(
            self.submit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Invalid data type", response.content.decode()
        )  # Check for generic error message
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_invalid_end_time_format(self):
        """Test submission with an invalid end_time format."""
        payload = self.valid_payload.copy()
        payload["end_time"] = "15-05-2024 10:30:00"  # Wrong format
        response = self.client.post(
            self.submit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid end_time format", response.content.decode())
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_non_existent_quiz(self):
        """Test submission with a quiz_id that does not exist."""
        payload = self.valid_payload.copy()
        payload["quiz_id"] = 99999  # Non-existent ID
        response = self.client.post(
            self.submit_url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Quiz not found", response.content.decode())
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_submit_get_request_not_allowed(self):
        """Test that GET requests to the submit endpoint are not allowed."""
        response = self.client.get(self.submit_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
        self.assertEqual(QuizAttempt.objects.count(), 0)

    # Optional: Test CSRF protection if @csrf_exempt is removed
    # def test_submit_csrf_protection(self):
    #     """Test CSRF protection if @csrf_exempt is removed."""
    #     # This test assumes @csrf_exempt is removed from the view
    #     # You might need to adjust settings or client setup for CSRF tests
    #     client_no_csrf = Client(enforce_csrf_checks=True)
    #     response = client_no_csrf.post(
    #         self.submit_url,
    #         data=json.dumps(self.valid_payload),
    #         content_type='application/json'
    #     )
    #     self.assertEqual(response.status_code, 403) # Forbidden due to CSRF
    #     self.assertEqual(QuizAttempt.objects.count(), 0)
