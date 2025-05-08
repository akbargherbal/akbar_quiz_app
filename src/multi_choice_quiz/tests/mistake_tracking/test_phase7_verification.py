# src/multi_choice_quiz/tests/mistake_tracking/test_phase7_verification.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from multi_choice_quiz.models import Quiz, Question, Option, QuizAttempt

# Import the standardized logging setup
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging for this verification test
logger = setup_test_logging(__name__, "multi_choice_quiz")  # Log under the app

User = get_user_model()


class Phase7MistakeReviewVerificationTests(TestCase):
    """
    Verify the end-to-end mistake review functionality (Phase 7).
    Checks link visibility on profile and rendering of the review page.
    """

    @classmethod
    def setUpTestData(cls):
        logger.info("Setting up data for Phase 7 Verification")
        cls.user = User.objects.create_user(
            username="phase7tester", password="password"
        )
        cls.quiz = Quiz.objects.create(title="Phase 7 Review Quiz")

        # Q1: Mistake (Correct=A[0], User=B[1])
        cls.q1 = Question.objects.create(quiz=cls.quiz, text="Phase 7 - Q1", position=1)
        Option.objects.create(
            question=cls.q1, text="P7 Q1 Opt A (Correct)", position=1, is_correct=True
        )
        Option.objects.create(question=cls.q1, text="P7 Q1 Opt B", position=2)

        # Q2: Correct (Correct=Y[1], User=Y[1]) - Not in details
        cls.q2 = Question.objects.create(quiz=cls.quiz, text="Phase 7 - Q2", position=2)
        Option.objects.create(question=cls.q2, text="P7 Q2 Opt X", position=1)
        Option.objects.create(
            question=cls.q2, text="P7 Q2 Opt Y (Correct)", position=2, is_correct=True
        )

        # Attempt WITH mistake details
        cls.attempt_with_mistakes = QuizAttempt.objects.create(
            user=cls.user,
            quiz=cls.quiz,
            score=1,
            total_questions=2,
            percentage=50.0,
            attempt_details={
                str(cls.q1.id): {
                    "user_answer_idx": 1,
                    "correct_answer_idx": 0,
                }  # Only Q1 mistake
            },
        )

        # Attempt WITHOUT mistake details (e.g., perfect score or older attempt)
        cls.attempt_no_mistakes = QuizAttempt.objects.create(
            user=cls.user,
            quiz=cls.quiz,
            score=2,
            total_questions=2,
            percentage=100.0,
            attempt_details=None,  # Explicitly None
        )

        # Attempt with EMPTY mistake details dict
        cls.attempt_empty_details = QuizAttempt.objects.create(
            user=cls.user,
            quiz=cls.quiz,
            score=2,
            total_questions=2,
            percentage=100.0,
            attempt_details={},  # Empty dict
        )

        cls.profile_url = reverse("pages:profile")
        cls.review_url_with_mistakes = reverse(
            "multi_choice_quiz:attempt_mistake_review",
            args=[cls.attempt_with_mistakes.id],
        )
        cls.review_url_no_mistakes = reverse(
            "multi_choice_quiz:attempt_mistake_review",
            args=[cls.attempt_no_mistakes.id],
        )
        cls.review_url_empty_details = reverse(
            "multi_choice_quiz:attempt_mistake_review",
            args=[cls.attempt_empty_details.id],
        )

    def test_review_link_visibility_on_profile(self):
        """Verify the 'Review Mistakes' link appears only for attempts with details."""
        logger.info("Testing Review Mistakes link visibility on profile")
        self.client.login(username="phase7tester", password="password")
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/profile.html")

        # Check link IS present for the attempt WITH details
        logger.debug(f"Checking for link: {self.review_url_with_mistakes}")
        self.assertContains(
            response,
            f'href="{self.review_url_with_mistakes}"',
            msg_prefix="Link for attempt with mistakes should be present",
        )

        # Check link is NOT present for the attempt with NO details (None)
        logger.debug(
            f"Checking absence of link for attempt ID: {self.attempt_no_mistakes.id}"
        )
        self.assertNotContains(
            response,
            f'href="{self.review_url_no_mistakes}"',
            msg_prefix="Link for attempt with no mistakes (None details) should NOT be present",
        )

        # Check link is NOT present for the attempt with EMPTY details ({})
        logger.debug(
            f"Checking absence of link for attempt ID: {self.attempt_empty_details.id}"
        )
        self.assertNotContains(
            response,
            f'href="{self.review_url_empty_details}"',
            msg_prefix="Link for attempt with empty details ({}) should NOT be present",
        )
        logger.info("Link visibility checks passed.")

    def test_mistake_review_page_renders_correctly(self):
        """Verify the mistake review page loads and displays correct mistake details."""
        logger.info(
            f"Testing rendering of mistake review page: {self.review_url_with_mistakes}"
        )
        self.client.login(username="phase7tester", password="password")
        response = self.client.get(self.review_url_with_mistakes)

        self.assertEqual(response.status_code, 200, "Expected status code 200")
        self.assertTemplateUsed(
            response,
            "multi_choice_quiz/mistake_review.html",
            "Correct template should be used",
        )

        # Check for key elements in the rendered HTML
        self.assertContains(response, "Mistake Review", msg_prefix="Page title missing")
        self.assertContains(response, self.quiz.title, msg_prefix="Quiz title missing")
        self.assertContains(
            response,
            "Questions Answered Incorrectly",
            msg_prefix="Mistakes section heading missing",
        )

        # Check specific mistake details for Q1
        self.assertContains(
            response, "Phase 7 - Q1", msg_prefix="Mistake Q1 text missing"
        )
        self.assertContains(
            response,
            "Your Answer:",
            msg_prefix="Mistake Q1 'Your Answer' label missing",
        )
        self.assertContains(
            response, "P7 Q1 Opt B", msg_prefix="Mistake Q1 user answer text missing"
        )  # User chose B (idx 1)
        self.assertContains(
            response,
            "Correct Answer:",
            msg_prefix="Mistake Q1 'Correct Answer' label missing",
        )
        self.assertContains(
            response,
            "P7 Q1 Opt A (Correct)",
            msg_prefix="Mistake Q1 correct answer text missing",
        )  # Correct is A (idx 0)

        # Ensure Q2 (which was correct) is NOT listed as a mistake
        self.assertNotContains(
            response,
            "Phase 7 - Q2",
            msg_prefix="Correctly answered Q2 should not be listed",
        )

        self.assertContains(
            response, "Back to Profile", msg_prefix="Back button missing"
        )
        logger.info("Mistake review page rendering checks passed.")

    def test_review_page_redirects_if_no_mistakes(self):
        """Verify accessing review URL for an attempt without details redirects."""
        logger.info(
            f"Testing redirect for attempt with no mistakes: {self.review_url_no_mistakes}"
        )
        self.client.login(username="phase7tester", password="password")
        response = self.client.get(self.review_url_no_mistakes)
        self.assertRedirects(
            response,
            self.profile_url,
            msg_prefix="Should redirect to profile if details are None",
        )
        logger.info("Redirect for None details passed.")

        logger.info(
            f"Testing redirect for attempt with empty details: {self.review_url_empty_details}"
        )
        response_empty = self.client.get(self.review_url_empty_details)
        self.assertRedirects(
            response_empty,
            self.profile_url,
            msg_prefix="Should redirect to profile if details are {}",
        )
        logger.info("Redirect for empty {} details passed.")
