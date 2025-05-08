# src/multi_choice_quiz/tests/test_views.py
# UPDATED (v3) based on Session 4 evaluation & test interference fix

import json
from datetime import datetime, timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.contrib.messages import get_messages  # <<< ADDED for checking messages
from django.contrib import messages  # <<< ADD THIS LINE

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
        self.assertIn(
            "Invalid data type or format for field", response.content.decode()
        )

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


# === Tests for attempt_mistake_review view ===
class AttemptMistakeReviewViewTests(TestCase):
    """Tests for the attempt_mistake_review view."""

    @classmethod
    def setUpTestData(cls):
        """Set up data for mistake review tests."""
        cls.user1 = User.objects.create_user(username="reviewer1", password="password")
        cls.user2 = User.objects.create_user(username="reviewer2", password="password")
        cls.quiz = Quiz.objects.create(title="Mistake Review Test Quiz")

        # Question 1: Correct=A(idx 0), User chose B(idx 1) -> MISTAKE
        cls.q1 = Question.objects.create(quiz=cls.quiz, text="Q1 Text", position=1)
        Option.objects.create(
            question=cls.q1, text="Q1 Opt A (Correct)", position=1, is_correct=True
        )
        Option.objects.create(question=cls.q1, text="Q1 Opt B", position=2)

        # Question 2: Correct=Y(idx 1), User chose Y(idx 1) -> CORRECT
        cls.q2 = Question.objects.create(quiz=cls.quiz, text="Q2 Text", position=2)
        Option.objects.create(question=cls.q2, text="Q2 Opt X", position=1)
        Option.objects.create(
            question=cls.q2, text="Q2 Opt Y (Correct)", position=2, is_correct=True
        )

        # Question 3: Correct=3(idx 2), User chose 1(idx 0) -> MISTAKE
        cls.q3 = Question.objects.create(quiz=cls.quiz, text="Q3 Text", position=3)
        Option.objects.create(question=cls.q3, text="Q3 Opt 1", position=1)
        Option.objects.create(question=cls.q3, text="Q3 Opt 2", position=2)
        Option.objects.create(
            question=cls.q3, text="Q3 Opt 3 (Correct)", position=3, is_correct=True
        )

        # Attempt WITH mistakes for user1
        cls.attempt_with_mistakes = QuizAttempt.objects.create(
            user=cls.user1,
            quiz=cls.quiz,
            score=1,  # Only Q2 correct
            total_questions=3,
            percentage=33.33,
            attempt_details={
                str(cls.q1.id): {
                    "user_answer_idx": 1,
                    "correct_answer_idx": 0,
                },  # Mistake
                str(cls.q3.id): {
                    "user_answer_idx": 0,
                    "correct_answer_idx": 2,
                },  # Mistake
            },
        )

        # Attempt with NO mistakes (perfect score, details=None) for user1
        cls.attempt_no_mistakes = QuizAttempt.objects.create(
            user=cls.user1,
            quiz=cls.quiz,
            score=3,
            total_questions=3,
            percentage=100.0,
            attempt_details=None,  # Or {} - view should handle both
        )

        # Attempt belonging to user2 (for permission testing)
        cls.attempt_other_user = QuizAttempt.objects.create(
            user=cls.user2,
            quiz=cls.quiz,
            score=2,
            total_questions=3,
            percentage=66.67,
            attempt_details={
                str(cls.q1.id): {"user_answer_idx": 1, "correct_answer_idx": 0}
            },
        )

        cls.review_url_valid = reverse(
            "multi_choice_quiz:attempt_mistake_review",
            args=[cls.attempt_with_mistakes.id],
        )
        cls.review_url_no_mistakes = reverse(
            "multi_choice_quiz:attempt_mistake_review",
            args=[cls.attempt_no_mistakes.id],
        )
        cls.review_url_other_user = reverse(
            "multi_choice_quiz:attempt_mistake_review", args=[cls.attempt_other_user.id]
        )
        cls.review_url_non_existent = reverse(
            "multi_choice_quiz:attempt_mistake_review", args=[9999]
        )

    def test_anonymous_user_redirected_to_login(self):
        """Verify anonymous users are redirected from the review page."""
        response = self.client.get(self.review_url_valid)
        self.assertEqual(response.status_code, 302)
        expected_redirect = f"{reverse('login')}?next={self.review_url_valid}"
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)

    def test_user_cannot_review_other_user_attempt(self):
        """Verify a logged-in user gets 404 trying to access another user's review."""
        self.client.login(username="reviewer1", password="password")
        response = self.client.get(self.review_url_other_user)
        self.assertEqual(response.status_code, 404)  # View raises Http404

    def test_non_existent_attempt_returns_404(self):
        """Verify accessing a non-existent attempt ID returns 404."""
        self.client.login(username="reviewer1", password="password")
        response = self.client.get(self.review_url_non_existent)
        self.assertEqual(response.status_code, 404)

    def test_attempt_with_no_mistakes_redirects_to_profile(self):
        """Verify accessing review for an attempt with no mistake details redirects."""
        self.client.login(username="reviewer1", password="password")
        response = self.client.get(self.review_url_no_mistakes)
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertRedirects(
            response, reverse("pages:profile"), fetch_redirect_response=False
        )

        # Check for optional message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "There are no mistakes to review for this attempt."
        )

    def test_successful_review_page_load_and_context(self):
        """Verify the review page loads correctly with expected context data."""
        self.client.login(username="reviewer1", password="password")
        response = self.client.get(self.review_url_valid)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "multi_choice_quiz/mistake_review.html")

        # Check main context objects
        self.assertEqual(response.context["attempt"], self.attempt_with_mistakes)
        self.assertEqual(response.context["quiz"], self.quiz)

        # Check mistakes context data
        mistakes_context = response.context["mistakes"]
        self.assertIsInstance(mistakes_context, list)
        self.assertEqual(len(mistakes_context), 2)  # q1 and q3 were mistakes

        # Verify details for the first mistake (Q1)
        mistake1 = next(
            (m for m in mistakes_context if m["question_id"] == self.q1.id), None
        )
        self.assertIsNotNone(mistake1)
        self.assertEqual(mistake1["question_text"], "Q1 Text")
        self.assertEqual(mistake1["user_answer"], "Q1 Opt B")  # User chose index 1
        self.assertEqual(
            mistake1["correct_answer"], "Q1 Opt A (Correct)"
        )  # Correct is index 0

        # Verify details for the second mistake (Q3)
        mistake3 = next(
            (m for m in mistakes_context if m["question_id"] == self.q3.id), None
        )
        self.assertIsNotNone(mistake3)
        self.assertEqual(mistake3["question_text"], "Q3 Text")
        self.assertEqual(mistake3["user_answer"], "Q3 Opt 1")  # User chose index 0
        self.assertEqual(
            mistake3["correct_answer"], "Q3 Opt 3 (Correct)"
        )  # Correct is index 2
