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


class TestDataframeImport(TestCase):
    """Tests for the import_from_dataframe utility function."""

    def setUp(self):
        """Set up test data."""
        logger.info("Setting up TestDataframeImport test data")

        # Sample DataFrame with standard column names
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
            }
        )

        # DataFrame with alternative column names
        self.alt_columns_df = pd.DataFrame(
            {
                "question_text": [
                    "What is the formula for water?",
                    "What is the chemical symbol for gold?",
                ],
                "options": [
                    ["H2O2", "CO2", "H2O", "NaCl", "CH4"],
                    ["Go", "Ag", "Au", "Gd", "Fe"],
                ],
                "correct_answer": [3, 3],  # 1-based index
            }
        )

        # DataFrame with string options (serialized JSON)
        self.string_options_df = pd.DataFrame(
            {
                "text": ["What is the capital of Germany?"],
                "options": ['["Hamburg", "Munich", "Berlin", "Frankfurt", "Cologne"]'],
                "answerIndex": [3],  # 1-based index
            }
        )

        # DataFrame with comma-separated options
        self.csv_options_df = pd.DataFrame(
            {
                "text": ["Which language is most widely spoken?"],
                "options": ["English, Mandarin, Spanish, Hindi, Arabic"],
                "answerIndex": [2],  # 1-based index
            }
        )

    def test_standard_import(self):
        """Test importing a standard DataFrame with correct column names."""
        logger.info("Testing standard DataFrame import")
        quiz = import_from_dataframe(self.standard_df, "Test Quiz", "Test Topic")

        # Verify quiz was created
        self.assertIsInstance(quiz, Quiz)
        self.assertEqual(quiz.title, "Test Quiz")

        # Verify topic was created
        self.assertEqual(quiz.topics.count(), 1)
        topic = quiz.topics.first()
        self.assertEqual(topic.name, "Test Topic")

        # Verify questions were created
        self.assertEqual(quiz.question_count(), 2)

        # Verify first question details
        question1 = quiz.questions.order_by("position").first()
        self.assertEqual(question1.text, "What is the capital of France?")

        # Verify options
        self.assertEqual(question1.options.count(), 5)

        # Verify correct answer
        correct_option = question1.correct_option()
        self.assertEqual(correct_option.text, "Paris")
        self.assertEqual(correct_option.position, 2)  # 1-based position

    def test_alternative_column_names(self):
        """Test importing a DataFrame with alternative column names."""
        logger.info("Testing DataFrame with alternative column names")
        quiz = import_from_dataframe(self.alt_columns_df, "Alternative Columns Quiz")

        # Verify quiz was created
        self.assertIsInstance(quiz, Quiz)

        # Verify questions were created with transformed column names
        self.assertEqual(quiz.question_count(), 2)

        # Verify first question details
        question1 = quiz.questions.order_by("position").first()
        self.assertEqual(question1.text, "What is the formula for water?")

        # Verify correct answer
        correct_option = question1.correct_option()
        self.assertEqual(correct_option.text, "H2O")
        self.assertEqual(correct_option.position, 3)  # 1-based position

    def test_json_string_options(self):
        """Test importing a DataFrame with JSON string options."""
        logger.info("Testing DataFrame with JSON string options")
        quiz = import_from_dataframe(self.string_options_df, "JSON Options Quiz")

        # Verify question and options were created
        question = quiz.questions.first()
        self.assertEqual(question.options.count(), 5)

        # Verify options were parsed correctly
        option_texts = list(
            question.options.order_by("position").values_list("text", flat=True)
        )
        self.assertEqual(
            option_texts, ["Hamburg", "Munich", "Berlin", "Frankfurt", "Cologne"]
        )

        # Verify correct answer
        correct_option = question.correct_option()
        self.assertEqual(correct_option.text, "Berlin")

    def test_csv_string_options(self):
        """Test importing a DataFrame with comma-separated string options."""
        logger.info("Testing DataFrame with comma-separated options")
        quiz = import_from_dataframe(self.csv_options_df, "CSV Options Quiz")

        # Verify question and options were created
        question = quiz.questions.first()
        self.assertEqual(question.options.count(), 5)

        # Verify options were parsed correctly
        option_texts = list(
            question.options.order_by("position").values_list("text", flat=True)
        )
        self.assertEqual(
            option_texts, ["English", "Mandarin", "Spanish", "Hindi", "Arabic"]
        )

        # Verify correct answer
        correct_option = question.correct_option()
        self.assertEqual(correct_option.text, "Mandarin")

    def test_sample_size_parameter(self):
        """Test the sample_size parameter to limit questions."""
        logger.info("Testing sample_size parameter")
        # Create a larger DataFrame
        larger_df = pd.concat(
            [self.standard_df, self.alt_columns_df], ignore_index=True
        )

        # Import with sample_size=1
        quiz = import_from_dataframe(larger_df, "Sampled Quiz", sample_size=1)

        # Verify only one question was imported
        self.assertEqual(quiz.question_count(), 1)

    def test_missing_required_columns(self):
        """Test handling of missing required columns."""
        logger.info("Testing missing required columns handling")
        # DataFrame missing 'options' column
        invalid_df = pd.DataFrame(
            {"text": ["What is the capital of France?"], "answerIndex": [2]}
        )

        # Should raise ValueError
        with self.assertRaises(ValueError):
            import_from_dataframe(invalid_df, "Invalid Quiz")


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
