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

# Set up logging for this specific app
logger = setup_test_logging("test_utils", "multi_choice_quiz")  # Pass app_name


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
                "chapter_no": ["GEO101", "AST101"],  # Added chapter numbers
            }
        )

        # DataFrame with alternative column names
        self.alt_df = pd.DataFrame(
            {
                "question_text": ["Question 1?", "Question 2?"],
                "options": [["Opt A", "Opt B"], ["Opt X", "Opt Y"]],
                "correct_answer": [1, 2],  # 1-based index
                "tag": ["tag1", "tag2"],
                "chapter_no": ["CH1", "CH2"],
            }
        )

        # DataFrame with options as JSON string
        self.json_options_df = pd.DataFrame(
            {
                "text": ["JSON Options Question"],
                "options": [json.dumps(["Opt J1", "Opt J2", "Opt J3"])],
                "answerIndex": [3],  # 1-based index
                "tag": ["json-tag"],
                "chapter_no": ["JSON1"],
            }
        )

        # DataFrame with options as comma-separated string
        self.csv_options_df = pd.DataFrame(
            {
                "text": ["CSV Options Question"],
                "options": ["Opt C1, Opt C2, Opt C3"],
                "answerIndex": [1],  # 1-based index
                "tag": ["csv-tag"],
                "chapter_no": ["CSV1"],
            }
        )

        # DataFrame missing required columns
        self.invalid_df = pd.DataFrame({"text": ["Incomplete question"]})

    def test_standard_import(self):
        """Test importing a standard DataFrame."""
        logger.info("Testing standard DataFrame import")
        quiz = import_from_dataframe(self.standard_df, "Standard Import Quiz")
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.title, "Standard Import Quiz")
        self.assertEqual(quiz.questions.count(), 2)

        # Verify first question details
        q1 = quiz.questions.get(text="What is the capital of France?")
        self.assertEqual(q1.tag, "geography-capitals")
        self.assertEqual(q1.chapter_no, "GEO101")
        self.assertEqual(q1.options.count(), 5)
        self.assertEqual(q1.correct_option().text, "Paris")
        self.assertEqual(q1.correct_option().position, 2)

        # Verify second question details
        q2 = quiz.questions.get(text="Which planet is known as the Red Planet?")
        self.assertEqual(q2.tag, "astronomy-planets")
        self.assertEqual(q2.chapter_no, "AST101")
        self.assertEqual(q2.options.count(), 5)
        self.assertEqual(q2.correct_option().text, "Mars")
        self.assertEqual(q2.correct_option().position, 3)

    def test_alternative_column_names_import(self):
        """Test importing with alternative column names."""
        logger.info("Testing alternative column names import")
        quiz = import_from_dataframe(self.alt_df, "Alt Columns Quiz")
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.title, "Alt Columns Quiz")
        self.assertEqual(quiz.questions.count(), 2)

        # Verify question text and correct options were mapped
        q1 = quiz.questions.get(text="Question 1?")
        self.assertEqual(q1.correct_option().text, "Opt A")
        self.assertEqual(q1.correct_option().position, 1)
        self.assertEqual(q1.tag, "tag1")
        self.assertEqual(q1.chapter_no, "CH1")

        q2 = quiz.questions.get(text="Question 2?")
        self.assertEqual(q2.correct_option().text, "Opt Y")
        self.assertEqual(q2.correct_option().position, 2)
        self.assertEqual(q2.tag, "tag2")
        self.assertEqual(q2.chapter_no, "CH2")

    def test_json_options_import(self):
        """Test importing with options as a JSON string."""
        logger.info("Testing JSON options string import")
        quiz = import_from_dataframe(self.json_options_df, "JSON Options Quiz")
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.questions.count(), 1)
        q = quiz.questions.first()
        self.assertEqual(q.options.count(), 3)
        self.assertEqual(q.correct_option().text, "Opt J3")
        self.assertEqual(q.correct_option().position, 3)
        self.assertEqual(q.tag, "json-tag")
        self.assertEqual(q.chapter_no, "JSON1")

    def test_csv_options_import(self):
        """Test importing with options as a CSV string."""
        logger.info("Testing CSV options string import")
        quiz = import_from_dataframe(self.csv_options_df, "CSV Options Quiz")
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.questions.count(), 1)
        q = quiz.questions.first()
        self.assertEqual(q.options.count(), 3)
        self.assertEqual(q.correct_option().text, "Opt C1")
        self.assertEqual(q.correct_option().position, 1)
        self.assertEqual(q.tag, "csv-tag")
        self.assertEqual(q.chapter_no, "CSV1")

    def test_import_with_topic(self):
        """Test importing and associating with a topic."""
        logger.info("Testing import with topic association")
        topic_name = "Geography Topic"
        quiz = import_from_dataframe(
            self.standard_df, "Topic Quiz", topic_name=topic_name
        )
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.topics.count(), 1)
        self.assertEqual(quiz.topics.first().name, topic_name)
        # Check questions also have the topic
        self.assertEqual(quiz.questions.first().topic.name, topic_name)

    def test_import_with_sampling(self):
        """Test importing with sampling."""
        logger.info("Testing import with sampling (1 question)")
        quiz = import_from_dataframe(self.standard_df, "Sampled Quiz", sample_size=1)
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.questions.count(), 1)

    def test_missing_columns_raises_error(self):
        """Test that missing required columns raise ValueError."""
        logger.info("Testing import with missing columns")
        with self.assertRaises(ValueError) as cm:
            import_from_dataframe(self.invalid_df, "Invalid Quiz")
        self.assertIn("missing required column", str(cm.exception))

    def test_empty_dataframe(self):
        """Test importing an empty DataFrame."""
        logger.info("Testing import of empty DataFrame")
        empty_df = pd.DataFrame(columns=["text", "options", "answerIndex"])
        quiz = import_from_dataframe(empty_df, "Empty Quiz")
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.questions.count(), 0)


class TestCurateData(TestCase):
    """Tests for the curate_data utility function."""

    def setUp(self):
        """Set up test data."""
        logger.info("Setting up TestCurateData test data")
        # Sample DataFrame with standard column names and extra columns
        self.df = pd.DataFrame(
            {
                "text": [f"Question {i}" for i in range(1, 21)],
                "options": [[f"Option {j}" for j in range(1, 6)] for i in range(1, 21)],
                "answerIndex": [i % 5 + 1 for i in range(20)],  # 1-based indices
                "tag": [f"tag-{i}" for i in range(1, 21)],
                "chapter_no": [f"CH{i//5 + 1}" for i in range(20)],
                "topic": [f"Topic {(i%3)+1}" for i in range(20)],
                "CHAPTER_TITLE": [f"Chapter Title {(i//5)+1}" for i in range(20)],
                "extra_col": [f"extra_{i}" for i in range(20)],  # Column to be ignored
            }
        )

    def test_default_curation(self):
        """Test default curation with 10 questions."""
        logger.info("Testing default curation (10 questions)")
        result = curate_data(self.df)

        # Verify we got 10 questions
        self.assertEqual(len(result), 10)

        # Verify structure and required keys of first item
        item = result[0]
        self.assertIn("text", item)
        self.assertIn("options", item)
        self.assertIn("answerIndex", item)
        self.assertIsInstance(item["options"], list)

        # Verify optional keys are included if present in original DF
        self.assertIn("tag", item)
        self.assertIn("chapter_no", item)
        self.assertIn("topic", item)
        self.assertIn("CHAPTER_TITLE", item)

        # Verify extra columns not included
        self.assertNotIn("extra_col", item)

    def test_custom_question_count(self):
        """Test custom number of questions."""
        logger.info("Testing custom question count curation (5 questions)")
        result = curate_data(self.df, no_questions=5)
        self.assertEqual(len(result), 5)

    def test_max_available_questions(self):
        """Test requesting more questions than available."""
        logger.info("Testing requesting more questions than available")
        result = curate_data(self.df, no_questions=30)
        # Should return all available questions (20 in this case)
        self.assertEqual(len(result), 20)

    def test_column_mapping(self):
        """Test automatic column mapping."""
        logger.info("Testing column mapping for curation")
        # DataFrame with alternative column names
        alt_df = pd.DataFrame(
            {
                "question_text": [f"Q {i}" for i in range(1, 6)],
                "options": [[f"Opt {j}" for j in range(1, 6)] for i in range(1, 6)],
                "correct_answer": [i % 5 + 1 for i in range(5)],  # 1-based indices
                "tag": ["alt_tag"] * 5,
                "chapter_number": ["ALT_CH1"] * 5,  # Different name for chapter_no
            }
        )
        # Rename chapter_number to chapter_no for curate_data to pick it up
        alt_df_renamed = alt_df.rename(columns={"chapter_number": "chapter_no"})

        result = curate_data(alt_df_renamed, no_questions=3)

        # Verify standard keys are present after mapping
        self.assertIn("text", result[0])
        self.assertIn("answerIndex", result[0])
        self.assertIn("options", result[0])
        self.assertIn("tag", result[0])
        self.assertIn("chapter_no", result[0])  # Check renamed column is included

    def test_missing_required_columns(self):
        """Test handling of missing required columns."""
        logger.info("Testing missing required columns handling for curation")
        # DataFrame missing 'options' and 'answerIndex'
        invalid_df = pd.DataFrame({"text": ["Q1"], "tag": ["t1"]})
        with self.assertRaises(ValueError) as cm:
            curate_data(invalid_df)
        # MODIFIED ASSERTIONS
        self.assertIn("missing required columns for curation", str(cm.exception))
        self.assertIn("options", str(cm.exception))
        self.assertIn("answerIndex", str(cm.exception))
        # END MODIFIED ASSERTIONS

    def test_options_json_string_curation(self):
        """Test curating data where options are JSON strings."""
        logger.info("Testing curation with JSON string options")
        json_df = pd.DataFrame(
            {
                "text": ["Q1", "Q2"],
                "options": [json.dumps(["A", "B"]), json.dumps(["C", "D"])],
                "answerIndex": [1, 2],
            }
        )
        # Note: curate_data itself doesn't parse JSON options; it expects lists.
        # The import_from_dataframe function handles the parsing.
        # This test just verifies curate_data passes the string through.
        result = curate_data(json_df, no_questions=2)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0]["options"], str)  # Should still be string here
        self.assertIsInstance(result[1]["options"], str)

    def test_empty_dataframe_curation(self):
        """Test curating an empty DataFrame."""
        logger.info("Testing curation of empty DataFrame")
        empty_df = pd.DataFrame(columns=["text", "options", "answerIndex", "tag"])
        result = curate_data(empty_df, no_questions=10)
        self.assertEqual(len(result), 0)  # Should return empty list
