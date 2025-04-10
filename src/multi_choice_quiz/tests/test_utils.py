"""
Tests for utility functions in the multi_choice_quiz app.
This covers functions in utils.py for importing and curating quiz data.
"""

import pytest
import pandas as pd
import json
from django.test import TestCase
from django.core.exceptions import ValidationError

from multi_choice_quiz.utils import import_from_dataframe, curate_data
from multi_choice_quiz.models import Quiz, Question, Option, Topic

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging
logger = setup_test_logging("test_utils")

# Only the test cases that need to be updated for the tag field:


class TestDataframeImport(TestCase):
    """Tests for the import_from_dataframe utility function."""

    def setUp(self):
        """Set up test data."""
        logger.info("Setting up TestDataframeImport test data")

        # Sample DataFrame with standard column names and tags
        self.standard_df = pd.DataFrame(
            {
                "text": [
                    "What is the capital of France?",
                    "Which planet is known as the Red Planet?",
                ],
                "options": [
                    ["London", "Paris", "Berlin", "Madrid", "Rome"],
                    ["Venus", "Jupiter", "Mars", "Saturn", "Mercury"],
                ],
                "answerIndex": [2, 3],  # 1-based index
                "tag": ["geography-capitals", "astronomy-planets"],  # Added tags
            }
        )

    def test_tag_field_import(self):
        """Test importing a DataFrame with tag field."""
        logger.info("Testing tag field import")
        quiz = import_from_dataframe(self.standard_df, "Test Quiz with Tags")

        # Verify tag was imported
        questions = quiz.questions.all()
        self.assertEqual(questions[0].tag, "geography-capitals")
        self.assertEqual(questions[1].tag, "astronomy-planets")


class TestCurateData(TestCase):
    """Tests for the curate_data utility function."""

    def setUp(self):
        """Set up test data."""
        logger.info("Setting up TestCurateData test data")
        # Sample DataFrame with standard column names and tags
        self.df = pd.DataFrame(
            {
                "text": [f"Question {i}" for i in range(1, 21)],
                "options": [[f"Option {j}" for j in range(1, 6)] for i in range(1, 21)],
                "answerIndex": [i % 5 + 1 for i in range(20)],  # 1-based indices
                "tag": [f"tag-{i}" for i in range(1, 21)],  # Added tags
                "CHAPTER_TITLE": [
                    "Test Chapter" for _ in range(20)
                ],  # Added chapter title
            }
        )

    def test_extra_columns_preservation(self):
        """Test that extra columns like tag and CHAPTER_TITLE are preserved."""
        logger.info("Testing preservation of extra columns")
        result = curate_data(self.df, no_questions=5)

        # Verify tag and CHAPTER_TITLE columns are included
        self.assertTrue(all("tag" in item for item in result))
        self.assertTrue(all("CHAPTER_TITLE" in item for item in result))


class TestCurateData(TestCase):
    """Tests for the curate_data utility function."""

    def setUp(self):
        """Set up test data."""
        logger.info("Setting up TestCurateData test data")
        # Sample DataFrame with standard column names
        self.df = pd.DataFrame(
            {
                "text": [f"Question {i}" for i in range(1, 21)],
                "options": [[f"Option {j}" for j in range(1, 6)] for i in range(1, 21)],
                "answerIndex": [i % 5 + 1 for i in range(20)],  # 1-based indices
            }
        )

    def test_default_curation(self):
        """Test default curation with 10 questions."""
        logger.info("Testing default curation (10 questions)")
        result = curate_data(self.df)

        # Verify we got 10 questions
        self.assertEqual(len(result), 10)

        # Verify structure of first item
        self.assertIn("text", result[0])
        self.assertIn("options", result[0])
        self.assertIn("answerIndex", result[0])

        # Verify options is a list
        self.assertIsInstance(result[0]["options"], list)

    def test_custom_question_count(self):
        """Test custom number of questions."""
        logger.info("Testing custom question count curation")
        result = curate_data(self.df, no_questions=5)

        # Verify we got exactly 5 questions
        self.assertEqual(len(result), 5)

    def test_max_available_questions(self):
        """Test requesting more questions than available."""
        logger.info("Testing requesting more questions than available")
        result = curate_data(self.df, no_questions=30)

        # Should return all available questions
        self.assertEqual(len(result), 20)

    def test_column_mapping(self):
        """Test automatic column mapping."""
        logger.info("Testing column mapping for curation")
        # DataFrame with alternative column names
        alt_df = pd.DataFrame(
            {
                "question_text": [f"Question {i}" for i in range(1, 6)],
                "options": [[f"Option {j}" for j in range(1, 6)] for i in range(1, 6)],
                "correct_answer": [i % 5 + 1 for i in range(5)],  # 1-based indices
            }
        )

        result = curate_data(alt_df, no_questions=3)

        # Verify column names were mapped correctly
        self.assertIn("text", result[0])
        self.assertIn("answerIndex", result[0])

    def test_missing_columns(self):
        """Test handling of missing required columns."""
        logger.info("Testing missing columns handling for curation")
        # DataFrame missing required columns
        invalid_df = pd.DataFrame(
            {
                "text": [f"Question {i}" for i in range(1, 6)],
                # Missing 'options' and 'answerIndex'
            }
        )

        # Should raise ValueError
        with self.assertRaises(ValueError):
            curate_data(invalid_df)
