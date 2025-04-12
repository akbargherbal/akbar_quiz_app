# src/multi_choice_quiz/tests/test_import_chapter_script.py

import pandas as pd
from django.test import TestCase
from django.core.management import call_command # Needed to ensure models are ready

# Import the function directly from the script file
# This assumes 'src' is in the python path when tests run, which manage.py test usually handles
try:
    from import_chapter_quizzes import import_questions_by_chapter
except ImportError as e:
    raise ImportError(
        "Could not import 'import_questions_by_chapter' from 'import_chapter_quizzes.py'. "
        "Ensure the script is in the 'src' directory and the test runner includes 'src' in PYTHONPATH. "
        f"Original error: {e}"
    )

from multi_choice_quiz.models import Quiz, Question, Topic

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging for this specific test file
logger = setup_test_logging(__name__, "multi_choice_quiz") # Use app_name 'multi_choice_quiz'

# --- Test Constants ---
# These match the defaults in your function signature but are explicit here
DEFAULT_Q_PER_QUIZ = 20
DEFAULT_QUIZZES_PER_CHAPTER = 2
DEFAULT_MAX_QUIZZES = 5
DEFAULT_MIN_COVERAGE = 40
DEFAULT_SINGLE_QUIZ_THRESHOLD = 1.5
DEFAULT_USE_DESCRIPTIVE_TITLES = True
DEFAULT_USE_CHAPTER_PREFIX = True
DEFAULT_CHAPTER_ZFILL = 2

class ImportQuestionsByChapterTests(TestCase):
    """Tests for the import_questions_by_chapter function."""

    @classmethod
    def setUpClass(cls):
        """Ensure the database schema is set up."""
        super().setUpClass()
        # Running migrate ensures the test DB is set up correctly before model access
        # Use verbosity 0 to silence the output during tests
        call_command('migrate', verbosity=0)

    def _create_test_dataframe(self, chapter_no, num_questions, topic="Test Topic", chapter_title="Test Chapter"):
        """Helper to create a sample DataFrame for testing."""
        data = {
            "chapter_no": [chapter_no] * num_questions,
            "question_text": [f"Q{i+1} Ch{chapter_no}" for i in range(num_questions)],
            "options": [[f"Opt A{i}", f"Opt B{i}", f"Opt C{i}"] for i in range(num_questions)],
            "answerIndex": [(i % 3) + 1 for i in range(num_questions)], # 1-based index
            "topic": [topic] * num_questions,
            "CHAPTER_TITLE": [f"{chapter_title} {chapter_no}"] * num_questions,
        }
        return pd.DataFrame(data)

    def test_very_few_questions_creates_single_quiz(self):
        """
        Test Scenario 1: If total questions < questions_per_quiz * single_quiz_threshold,
        only one quiz should be created with all available questions.
        """
        logger.info("Testing scenario: Very few questions -> single quiz")
        q_per_quiz = 10
        threshold_factor = 1.5
        num_questions = int(q_per_quiz * threshold_factor) - 1 # e.g., 14 questions if q_per_quiz=10

        df = self._create_test_dataframe(chapter_no=1, num_questions=num_questions)

        quiz_count, question_count = import_questions_by_chapter(
            df,
            questions_per_quiz=q_per_quiz,
            single_quiz_threshold=threshold_factor,
            quizzes_per_chapter=2, # Default, should be overridden by threshold logic
            use_descriptive_titles=False, # Simplify title checking
            use_chapter_prefix=False,
        )

        # Assertions
        self.assertEqual(quiz_count, 1, "Should create only 1 quiz")
        self.assertEqual(question_count, num_questions, "Should use all available questions")
        self.assertEqual(Quiz.objects.count(), 1, "Database should contain 1 quiz")
        quiz = Quiz.objects.first()
        self.assertEqual(quiz.question_count(), num_questions)
        self.assertEqual(quiz.title, "Test Chapter 1 - Quiz 1")

    def test_standard_question_count_creates_default_quizzes(self):
        """
        Test Scenario 2: Enough questions for the default number of quizzes, but not
        enough to trigger coverage/threshold logic.
        """
        logger.info("Testing scenario: Standard question count -> default quizzes")
        q_per_quiz = 10
        quizzes_per_chapter = 2
        num_questions = q_per_quiz * quizzes_per_chapter + 5 # e.g., 25 questions

        df = self._create_test_dataframe(chapter_no=2, num_questions=num_questions)

        quiz_count, question_count = import_questions_by_chapter(
            df,
            questions_per_quiz=q_per_quiz,
            quizzes_per_chapter=quizzes_per_chapter,
            single_quiz_threshold=1.5, # Should not be triggered
            min_coverage_percentage=40, # Should not be triggered
            max_quizzes_per_chapter=5,
            use_descriptive_titles=False,
            use_chapter_prefix=False,
        )

        # Assertions
        self.assertEqual(quiz_count, quizzes_per_chapter, f"Should create default {quizzes_per_chapter} quizzes")
        # Total questions imported might be less than num_questions if sampled,
        # but should be quizzes_per_chapter * q_per_quiz
        self.assertEqual(question_count, quizzes_per_chapter * q_per_quiz)
        self.assertEqual(Quiz.objects.count(), quizzes_per_chapter)
        # Check titles
        self.assertTrue(Quiz.objects.filter(title="Test Chapter 2 - Quiz 1").exists())
        self.assertTrue(Quiz.objects.filter(title="Test Chapter 2 - Quiz 2").exists())

    def test_many_questions_triggers_coverage_calculation(self):
        """
        Test Scenario 3: Many questions, triggering the coverage percentage calculation,
        but staying below the max_quizzes_per_chapter cap.
        """
        logger.info("Testing scenario: Many questions -> coverage calculation")
        q_per_quiz = 10
        quizzes_per_chapter = 2 # Default, should be overridden
        num_questions = 80 # Plenty of questions
        min_coverage = 50 # Require 50% coverage = 40 questions
        max_quizzes = 5

        # Expected quizzes: ceil(40 questions / 10 q_per_quiz) = 4 quizzes
        expected_quiz_count = 4

        df = self._create_test_dataframe(chapter_no=3, num_questions=num_questions)

        quiz_count, question_count = import_questions_by_chapter(
            df,
            questions_per_quiz=q_per_quiz,
            quizzes_per_chapter=quizzes_per_chapter,
            single_quiz_threshold=1.5,
            min_coverage_percentage=min_coverage,
            max_quizzes_per_chapter=max_quizzes,
            use_descriptive_titles=False,
            use_chapter_prefix=False,
        )

        # Assertions
        self.assertEqual(quiz_count, expected_quiz_count, f"Should calculate {expected_quiz_count} quizzes based on coverage")
        # Each quiz should ideally have q_per_quiz questions
        self.assertEqual(question_count, expected_quiz_count * q_per_quiz)
        self.assertEqual(Quiz.objects.count(), expected_quiz_count)
        # Check titles
        for i in range(1, expected_quiz_count + 1):
            self.assertTrue(Quiz.objects.filter(title=f"Test Chapter 3 - Quiz {i}").exists())

    def test_many_questions_hits_max_quiz_cap(self):
        """
        Test Scenario 4: Very many questions, where coverage calculation would exceed
        max_quizzes_per_chapter. Should be capped.
        """
        logger.info("Testing scenario: Very many questions -> hits max quiz cap")
        q_per_quiz = 10
        quizzes_per_chapter = 2 # Default, should be overridden
        num_questions = 150 # Very many questions
        min_coverage = 50 # Require 50% coverage = 75 questions
        max_quizzes = 5 # Cap

        # Coverage would suggest ceil(75 / 10) = 8 quizzes, but capped at 5
        expected_quiz_count = max_quizzes

        df = self._create_test_dataframe(chapter_no=4, num_questions=num_questions)

        quiz_count, question_count = import_questions_by_chapter(
            df,
            questions_per_quiz=q_per_quiz,
            quizzes_per_chapter=quizzes_per_chapter,
            single_quiz_threshold=1.5,
            min_coverage_percentage=min_coverage,
            max_quizzes_per_chapter=max_quizzes,
            use_descriptive_titles=False,
            use_chapter_prefix=False,
        )

        # Assertions
        self.assertEqual(quiz_count, expected_quiz_count, f"Should be capped at {expected_quiz_count} quizzes")
        self.assertEqual(question_count, expected_quiz_count * q_per_quiz)
        self.assertEqual(Quiz.objects.count(), expected_quiz_count)
        # Check titles
        for i in range(1, expected_quiz_count + 1):
            self.assertTrue(Quiz.objects.filter(title=f"Test Chapter 4 - Quiz {i}").exists())

    def test_zero_questions_skips_chapter(self):
        """
        Test Scenario 5: Chapter exists in DataFrame but has no questions.
        """
        logger.info("Testing scenario: Zero questions -> skips chapter")
        df = self._create_test_dataframe(chapter_no=5, num_questions=0) # No questions

        quiz_count, question_count = import_questions_by_chapter(df)

        # Assertions
        self.assertEqual(quiz_count, 0, "Should create 0 quizzes")
        self.assertEqual(question_count, 0, "Should import 0 questions")
        self.assertEqual(Quiz.objects.count(), 0, "Database should contain 0 quizzes")

    def test_chapter_prefix_and_zfill(self):
        """
        Test Scenario 6: Verify chapter prefix and zfill work correctly.
        """
        logger.info("Testing scenario: Chapter prefix and zfill")
        df = self._create_test_dataframe(chapter_no=7, num_questions=5) # Few questions -> 1 quiz

        # Test with prefix enabled (default zfill=2)
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            single_quiz_threshold=1.5,
            use_descriptive_titles=False,
            use_chapter_prefix=True, # ENABLED
            chapter_zfill=2,
        )
        self.assertTrue(Quiz.objects.filter(title__startswith="07 ").exists())
        quiz1 = Quiz.objects.get(title__startswith="07 ")
        self.assertEqual(quiz1.title, "07 Test Chapter 7 - Quiz 1")
        Quiz.objects.all().delete() # Clean up for next part

        # Test with prefix enabled (zfill=3)
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            single_quiz_threshold=1.5,
            use_descriptive_titles=False,
            use_chapter_prefix=True, # ENABLED
            chapter_zfill=3,
        )
        self.assertTrue(Quiz.objects.filter(title__startswith="007 ").exists())
        quiz2 = Quiz.objects.get(title__startswith="007 ")
        self.assertEqual(quiz2.title, "007 Test Chapter 7 - Quiz 1")
        Quiz.objects.all().delete() # Clean up

        # Test with prefix disabled
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            single_quiz_threshold=1.5,
            use_descriptive_titles=False,
            use_chapter_prefix=False, # DISABLED
        )
        self.assertFalse(Quiz.objects.filter(title__startswith="07 ").exists())
        quiz3 = Quiz.objects.first()
        self.assertEqual(quiz3.title, "Test Chapter 7 - Quiz 1")

    def test_descriptive_titles(self):
        """
        Test Scenario 6b: Verify descriptive titles are used when enabled.
        """
        logger.info("Testing scenario: Descriptive titles")
        df = self._create_test_dataframe(
            chapter_no=8,
            num_questions=5,
            topic="Specific Topic",
            chapter_title="Specific Chapter"
        )

        # Test with descriptive titles enabled
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            single_quiz_threshold=1.5,
            use_descriptive_titles=True, # ENABLED
            use_chapter_prefix=False, # Disabled for simplicity
        )
        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        # Expected: Chapter Title: Topic - Quiz Num
        self.assertEqual(quiz.title, "Specific Chapter 8: Specific Topic - Quiz 1")

        # Verify topic was created and linked
        self.assertTrue(Topic.objects.filter(name="Specific Topic").exists())
        self.assertEqual(quiz.topics.first().name, "Specific Topic")
        self.assertEqual(quiz.questions.first().topic.name, "Specific Topic")

    def test_non_numeric_chapter_handling(self):
        """
        Test Scenario 7: Handle chapter_no that isn't purely numeric.
        """
        logger.info("Testing scenario: Non-numeric chapter_no")
        chapter_id = "Appendix A"
        df = self._create_test_dataframe(chapter_no=chapter_id, num_questions=5)

        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            single_quiz_threshold=1.5,
            use_descriptive_titles=False,
            use_chapter_prefix=True, # Prefix enabled
            chapter_zfill=2, # zfill shouldn't apply here
        )
        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        # Expect prefix to use the string directly + space
        self.assertTrue(quiz.title.startswith(f"{chapter_id} "))
        self.assertEqual(quiz.title, f"{chapter_id} Test Chapter {chapter_id} - Quiz 1")


    # Note: Testing the exact sampling logic (question uniqueness across quizzes
    # within a chapter) is hard without mocking pandas `sample` or closely inspecting
    # the `used_question_indices` set. These tests focus on the *number* of quizzes
    # and total questions imported, which are the main things your new logic affects.