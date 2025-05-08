# src/multi_choice_quiz/tests/mistake_tracking/test_phase6_verification.py

import json
from datetime import datetime, timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from multi_choice_quiz.models import Quiz, Question, Option, QuizAttempt
# Import the standardized logging setup
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging for this verification test
logger = setup_test_logging(__name__, "multi_choice_quiz") # Log under the app

User = get_user_model()

class Phase6MistakeCaptureVerificationTests(TestCase):
    """Verify end-to-end mistake data capture and storage (Phase 6)."""

    @classmethod
    def setUpTestData(cls):
        logger.info("Setting up data for Phase 6 Verification")
        # Create a quiz with known questions and answers
        cls.quiz = Quiz.objects.create(title="Phase 6 Test Quiz")
        cls.q1 = Question.objects.create(quiz=cls.quiz, text="Q1 Text", position=1)
        Option.objects.create(question=cls.q1, text="Q1 Opt A (Correct)", position=1, is_correct=True) # Correct Index: 0
        Option.objects.create(question=cls.q1, text="Q1 Opt B", position=2)

        cls.q2 = Question.objects.create(quiz=cls.quiz, text="Q2 Text", position=2)
        Option.objects.create(question=cls.q2, text="Q2 Opt X", position=1)
        Option.objects.create(question=cls.q2, text="Q2 Opt Y (Correct)", position=2, is_correct=True) # Correct Index: 1

        cls.q3 = Question.objects.create(quiz=cls.quiz, text="Q3 Text", position=3)
        Option.objects.create(question=cls.q3, text="Q3 Opt 1", position=1)
        Option.objects.create(question=cls.q3, text="Q3 Opt 2", position=2)
        Option.objects.create(question=cls.q3, text="Q3 Opt 3 (Correct)", position=3, is_correct=True) # Correct Index: 2

        cls.submit_url = reverse("multi_choice_quiz:submit_quiz_attempt")
        cls.test_user = User.objects.create_user(username="phase6tester", password="password")

    def test_mistake_details_saved_correctly(self):
        """
        Simulate a submission with mixed correct/incorrect answers and verify
        only mistakes are stored in attempt_details.
        """
        logger.info("Testing mistake details storage")
        self.client.login(username="phase6tester", password="password")

        # Simulate answers:
        # Q1: User chose index 1 (Opt B) - Incorrect (Correct is 0)
        # Q2: User chose index 1 (Opt Y) - Correct
        # Q3: User chose index 0 (Opt 1) - Incorrect (Correct is 2)
        simulated_detailed_answers = {
            str(self.q1.id): 1, # Incorrect
            str(self.q2.id): 1, # Correct
            str(self.q3.id): 0, # Incorrect
        }

        payload = {
            "quiz_id": self.quiz.id,
            "score": 1, # Only Q2 was correct
            "total_questions": 3,
            "percentage": round((1/3)*100),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "attempt_details": simulated_detailed_answers
        }

        response = self.client.post(
            self.submit_url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        # --- Assertions ---
        self.assertEqual(response.status_code, 200, f"Expected status 200, got {response.status_code}. Response: {response.content.decode()}")
        response_data = response.json()
        self.assertEqual(response_data.get("status"), "success")
        self.assertTrue("attempt_id" in response_data)

        # Verify the created QuizAttempt in the database
        attempt = QuizAttempt.objects.get(id=response_data["attempt_id"])
        self.assertIsNotNone(attempt.attempt_details, "attempt_details should not be None")
        self.assertIsInstance(attempt.attempt_details, dict, "attempt_details should be a dict")

        # Define the expected mistakes structure
        expected_mistakes = {
            str(self.q1.id): {'user_answer_idx': 1, 'correct_answer_idx': 0}, # Q1 was wrong
            str(self.q3.id): {'user_answer_idx': 0, 'correct_answer_idx': 2}, # Q3 was wrong
        }

        self.assertEqual(attempt.attempt_details, expected_mistakes, "Stored mistake details do not match expected mistakes.")
        logger.info("Mistake details storage verified successfully.")

    def test_no_mistakes_saves_null_details(self):
        """
        Simulate a submission with all correct answers and verify
        attempt_details is None or empty.
        """
        logger.info("Testing submission with no mistakes")
        self.client.login(username="phase6tester", password="password")

        # Simulate all correct answers:
        simulated_detailed_answers = {
            str(self.q1.id): 0, # Correct
            str(self.q2.id): 1, # Correct
            str(self.q3.id): 2, # Correct
        }

        payload = {
            "quiz_id": self.quiz.id,
            "score": 3,
            "total_questions": 3,
            "percentage": 100,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "attempt_details": simulated_detailed_answers
        }

        response = self.client.post(
            self.submit_url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        # --- Assertions ---
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data.get("status"), "success")
        self.assertTrue("attempt_id" in response_data)

        attempt = QuizAttempt.objects.get(id=response_data["attempt_id"])
        # Allow either None or an empty dict, as both indicate no mistakes
        self.assertIn(attempt.attempt_details, [None, {}], "attempt_details should be None or empty for a perfect score")
        logger.info("No mistake details storage verified successfully for perfect score.")

    def test_submission_without_attempt_details(self):
        """
        Simulate a submission from an older JS version without attempt_details
        and verify it still saves basic data and attempt_details is None.
        """
        logger.info("Testing submission without attempt_details field")
        self.client.login(username="phase6tester", password="password")

        payload = {
            "quiz_id": self.quiz.id,
            "score": 2, # Example score
            "total_questions": 3,
            "percentage": 67,
            "end_time": datetime.now(timezone.utc).isoformat(),
            # 'attempt_details' is missing
        }

        response = self.client.post(
            self.submit_url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        # --- Assertions ---
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data.get("status"), "success")
        self.assertTrue("attempt_id" in response_data)

        attempt = QuizAttempt.objects.get(id=response_data["attempt_id"])
        self.assertIsNone(attempt.attempt_details, "attempt_details should be None when not provided in payload")
        # Verify basic data was still saved
        self.assertEqual(attempt.score, 2)
        self.assertEqual(attempt.total_questions, 3)
        logger.info("Submission without attempt_details handled gracefully.")