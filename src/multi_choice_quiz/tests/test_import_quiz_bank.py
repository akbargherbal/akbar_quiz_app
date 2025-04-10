"""
Tests for the import_quiz_bank management command.
This file should be placed in multi_choice_quiz/tests/
"""

import os
import tempfile
import pandas as pd
from io import StringIO
from django.test import TestCase
from django.core.management import call_command

from multi_choice_quiz.models import Quiz, Question, Option, Topic


class ImportQuizBankCommandTest(TestCase):
    """Test the import_quiz_bank management command."""

    def setUp(self):
        """Set up test data."""
        # Create sample data as a pandas DataFrame
        self.data = {
            "text": [
                "What is the capital of France?",
                "Which planet is known as the Red Planet?",
                "What is the formula for water?",
                "What is 2+2?",
                "What is the symbol for Gold?",
            ],
            "options": [
                ["London", "Paris", "Berlin", "Madrid"],
                ["Venus", "Jupiter", "Mars", "Saturn"],
                ["H2O2", "CO2", "H2O", "NaCl"],
                ["3", "4", "5", "6"],
                ["Go", "Au", "Ag", "Gd"],
            ],
            "answerIndex": [2, 3, 3, 2, 2],  # 1-based indices
            "topic": [
                "Geography",
                "Astronomy",
                "Chemistry",
                "Mathematics",
                "Chemistry",
            ],
            "chapter_no": ["1", "2", "3", "1", "3"],
        }

        self.df = pd.DataFrame(self.data)

        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()

        # Save the data in different formats
        self.csv_path = os.path.join(self.temp_dir.name, "test_quiz_bank.csv")
        self.excel_path = os.path.join(self.temp_dir.name, "test_quiz_bank.xlsx")
        self.pickle_path = os.path.join(self.temp_dir.name, "test_quiz_bank.pkl")

        # Save as CSV
        self.df.to_csv(self.csv_path, index=False)

        # Save as Excel
        self.df.to_excel(self.excel_path, index=False)

        # Save as pickle
        self.df.to_pickle(self.pickle_path)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_import_csv(self):
        """Test importing from a CSV file."""
        # Clear any existing data
        Quiz.objects.all().delete()

        # Run the command with CSV
        out = StringIO()
        call_command(
            "import_quiz_bank", self.csv_path, quiz_title="CSV Test Quiz", stdout=out
        )

        # Verify command output indicates success
        output = out.getvalue()
        self.assertIn("Successfully imported quiz", output)

        # Verify quiz was created with all 5 questions
        quiz = Quiz.objects.get(title="CSV Test Quiz")
        self.assertEqual(quiz.question_count(), 5)

    def test_import_excel(self):
        """Test importing from an Excel file."""
        # Clear any existing data
        Quiz.objects.all().delete()

        # Run the command with Excel
        out = StringIO()
        call_command(
            "import_quiz_bank",
            self.excel_path,
            quiz_title="Excel Test Quiz",
            stdout=out,
        )

        # Verify command output indicates success
        output = out.getvalue()
        self.assertIn("Successfully imported quiz", output)

        # Verify quiz was created with all 5 questions
        quiz = Quiz.objects.get(title="Excel Test Quiz")
        self.assertEqual(quiz.question_count(), 5)

    def test_import_pickle(self):
        """Test importing from a pickle file."""
        # Clear any existing data
        Quiz.objects.all().delete()

        # Run the command with pickle
        out = StringIO()
        call_command(
            "import_quiz_bank",
            self.pickle_path,
            quiz_title="Pickle Test Quiz",
            stdout=out,
        )

        # Verify command output indicates success
        output = out.getvalue()
        self.assertIn("Successfully imported quiz", output)

        # Verify quiz was created with all 5 questions
        quiz = Quiz.objects.get(title="Pickle Test Quiz")
        self.assertEqual(quiz.question_count(), 5)

    def test_import_with_topic(self):
        """Test importing with a specified topic."""
        # Clear any existing data
        Quiz.objects.all().delete()

        # Run the command
        call_command(
            "import_quiz_bank",
            self.csv_path,
            quiz_title="Topic Quiz",
            topic="Quiz Bank",
        )

        # Verify topic was created and associated with the quiz
        topic = Topic.objects.get(name="Quiz Bank")
        self.assertIsNotNone(topic)

        quiz = Quiz.objects.get(title="Topic Quiz")
        self.assertTrue(quiz.topics.filter(name="Quiz Bank").exists())

    def test_import_with_max_questions(self):
        """Test importing with a maximum number of questions."""
        # Clear any existing data
        Quiz.objects.all().delete()

        # Run the command
        call_command(
            "import_quiz_bank",
            self.csv_path,
            quiz_title="Limited Quiz",
            max_questions=3,
        )

        # Verify only 3 questions were imported
        quiz = Quiz.objects.get(title="Limited Quiz")
        self.assertEqual(quiz.question_count(), 3)

    def test_import_split_by_topic(self):
        """Test splitting import by topic."""
        # Clear any existing data
        Quiz.objects.all().delete()
        Topic.objects.all().delete()

        # Run the command
        out = StringIO()
        call_command("import_quiz_bank", self.csv_path, split_by_topic=True, stdout=out)

        # Verify output indicates multiple quizzes created
        output = out.getvalue()
        self.assertIn("Found 4 unique topics", output)  # Updated to expect 4 topics

        # Verify correct number of quizzes created
        geography_quiz = Quiz.objects.filter(title="Quiz: Geography").first()
        chemistry_quiz = Quiz.objects.filter(title="Quiz: Chemistry").first()
        astronomy_quiz = Quiz.objects.filter(title="Quiz: Astronomy").first()
        mathematics_quiz = Quiz.objects.filter(title="Quiz: Mathematics").first()

        self.assertIsNotNone(geography_quiz)
        self.assertIsNotNone(chemistry_quiz)
        self.assertIsNotNone(astronomy_quiz)
        self.assertIsNotNone(mathematics_quiz)

        # Verify topic association
        self.assertTrue(Topic.objects.filter(name="Geography").exists())
        self.assertTrue(Topic.objects.filter(name="Chemistry").exists())
        self.assertTrue(Topic.objects.filter(name="Astronomy").exists())
        self.assertTrue(Topic.objects.filter(name="Mathematics").exists())

        # Verify correct question counts by topic
        self.assertEqual(geography_quiz.question_count(), 1)
        self.assertEqual(chemistry_quiz.question_count(), 2)
        self.assertEqual(astronomy_quiz.question_count(), 1)
        self.assertEqual(mathematics_quiz.question_count(), 1)

    def test_chapter_column_handling(self):
        """Test importing with chapter information."""
        # Clear any existing data
        Quiz.objects.all().delete()

        # Run the command
        call_command("import_quiz_bank", self.csv_path, quiz_title="Chapter Quiz")

        # Verify chapter information was imported
        chem_question = Question.objects.filter(
            text__contains="formula for water"
        ).first()
        self.assertEqual(chem_question.chapter_no, "3")

        math_question = Question.objects.filter(text__contains="2+2").first()
        self.assertEqual(math_question.chapter_no, "1")

    # Add this test to the ImportQuizBankCommandTest class:
    def test_improved_title_and_topic_names(self):
        """Test importing with chapter titles and better topic names."""
        # Clear any existing data
        Quiz.objects.all().delete()
        Topic.objects.all().delete()

        # Create test data with chapter titles
        data = self.data.copy()
        data["CHAPTER_TITLE"] = [
            "Earth Science",
            "Space Science",
            "Chemistry",
            "Mathematics",
            "Chemistry",
        ]
        df = pd.DataFrame(data)

        # Save as CSV
        csv_path = os.path.join(self.temp_dir.name, "test_with_titles.csv")
        df.to_csv(csv_path, index=False)

        # Run the command
        out = StringIO()
        call_command("import_quiz_bank", csv_path, split_by_topic=True, stdout=out)

        # Verify output indicates quizzes created with better titles
        output = out.getvalue()

        # Check Geography quiz
        geography_quiz = Quiz.objects.filter(title__contains="Earth Science").first()
        self.assertIsNotNone(geography_quiz)
        self.assertEqual(geography_quiz.title, "Earth Science: Geography Quiz")

        # Check Chemistry quiz
        chemistry_quiz = Quiz.objects.filter(title__contains="Chemistry").first()
        self.assertIsNotNone(chemistry_quiz)
        self.assertEqual(chemistry_quiz.title, "Chemistry: Chemistry Quiz")

        # Check that actual topic names were used
        self.assertTrue(Topic.objects.filter(name="Geography").exists())
        self.assertTrue(Topic.objects.filter(name="Chemistry").exists())
