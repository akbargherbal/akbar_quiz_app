# src/core/tests/test_phase3_verification.py
# Corrected version 2

import pytest
from django.core.exceptions import FieldDoesNotExist
from django.contrib.auth import get_user_model
from django.urls import reverse, resolve
from django.db.models.deletion import SET_NULL
from django.test import TestCase

from multi_choice_quiz.models import QuizAttempt
from multi_choice_quiz.views import submit_quiz_attempt

User = get_user_model()

# Mark all tests in this module as needing database access if necessary
pytestmark = pytest.mark.django_db


# Use TestCase since the original structure used it
class TestPhase3Verification(TestCase):
    """
    Verifies the specific configuration and setup outcomes of Phase 3:
    Optional Linking of Quiz Attempts to Users.
    """

    def test_quiz_attempt_model_has_optional_user_field(self):
        """
        Verify that the QuizAttempt model has a 'user' field configured correctly
        to be optional and handle user deletion gracefully.
        """
        try:
            field = QuizAttempt._meta.get_field("user")
        except FieldDoesNotExist:
            self.fail("QuizAttempt model does not have a 'user' field.")

        self.assertIsNotNone(field, "'user' field not found in QuizAttempt model.")
        self.assertEqual(
            field.remote_field.model,
            User,
            "User field does not link to the correct User model.",
        )
        self.assertTrue(field.null, "User field should allow NULL values (null=True).")
        self.assertTrue(
            field.blank, "User field should allow blank values (blank=True)."
        )
        self.assertEqual(
            field.remote_field.on_delete,
            SET_NULL,
            "User field on_delete should be SET_NULL.",
        )
        # --- START CORRECTION ---
        self.assertEqual(
            field.remote_field.related_name,  # Use remote_field.related_name
            "quiz_attempts",
            "User field related_name should be 'quiz_attempts'.",
        )
        # --- END CORRECTION ---
        self.assertTrue(field.is_relation, "User field should be a relation.")
        self.assertFalse(field.one_to_one, "User field should not be OneToOne.")
        self.assertFalse(field.many_to_many, "User field should not be ManyToMany.")

    def test_submit_quiz_attempt_url_resolves(self):
        """
        Verify that the URL name for the quiz submission view resolves correctly.
        This implicitly checks if the view is mapped in the URLconf.
        """
        try:
            url = reverse("multi_choice_quiz:submit_quiz_attempt")
            self.assertEqual(
                url,
                "/quiz/submit_attempt/",
                f"Expected URL '/quiz/submit_attempt/' but got '{url}'",
            )
            resolved_func = resolve(url).func
            self.assertEqual(resolved_func, submit_quiz_attempt)
        except Exception as e:
            self.fail(
                f"Could not resolve URL name 'multi_choice_quiz:submit_quiz_attempt'. Error: {e}"
            )

    def test_view_logic_handles_authenticated_user(self):
        """
        Check if the submit_quiz_attempt view logic is present in the code.
        NOTE: Detailed logic testing (correct user assignment) should be in
        multi_choice_quiz/tests/test_views.py, but we check basic presence here.
        """
        self.assertTrue(
            hasattr(submit_quiz_attempt, "__call__"),
            "submit_quiz_attempt view function not found or not callable.",
        )
