# src/multi_choice_quiz/tests/test_import_chapter_script.py

import pandas as pd
from django.test import TestCase
from django.core.management import call_command  # Needed to ensure models are ready

# Import the function directly from the utils module now
try:
    from multi_choice_quiz.utils import import_questions_by_chapter
except ImportError as e:
    raise ImportError(
        "Could not import 'import_questions_by_chapter' from 'multi_choice_quiz.utils'. "
        "Ensure the utils.py file is correct and accessible. "
        f"Original error: {e}"
    )

# --- ADD SystemCategory import ---
from multi_choice_quiz.models import Quiz, Question, Topic
from pages.models import SystemCategory  # <<< CORRECTED IMPORT for SystemCategory


# --- END SystemCategory import ---

# Import our standardized test logging
from multi_choice_quiz.tests.test_logging import setup_test_logging

# Set up logging for this specific test file
logger = setup_test_logging(
    __name__, "multi_choice_quiz"
)  # Use app_name 'multi_choice_quiz'

# --- Test Constants ---
# These match the defaults in your function signature but are explicit here
DEFAULT_Q_PER_QUIZ = 20
DEFAULT_QUIZZES_PER_CHAPTER = 2
DEFAULT_MAX_QUIZZES = 5
DEFAULT_MIN_COVERAGE = 40
DEFAULT_SINGLE_QUIZ_THRESHOLD = (
    1.5  # Note: In utils.py, it's 1.3. Let's use 1.3 to match utils.
)
# Or update utils to use 1.5 if that's the actual intent.
# For now, assuming test should match utils' default if not overridden in call.
# Let's use 1.3 to match default for now.
SINGLE_QUIZ_THRESHOLD_FROM_UTILS = 1.3  # Default from utils.py

DEFAULT_USE_DESCRIPTIVE_TITLES = True
DEFAULT_USE_CHAPTER_PREFIX = True
DEFAULT_CHAPTER_ZFILL = 2


class ImportQuestionsByChapterTests(TestCase):
    """Tests for the import_questions_by_chapter function."""

    @classmethod
    def setUpClass(cls):
        """Ensure the database schema is set up."""
        super().setUpClass()
        call_command("migrate", verbosity=0)

    def setUp(self):
        # Clean up relevant models before each test to ensure isolation
        Quiz.objects.all().delete()
        Question.objects.all().delete()
        Topic.objects.all().delete()
        SystemCategory.objects.all().delete()  # Clear SystemCategory as well

    def _create_test_dataframe(
        self,
        chapter_no,
        num_questions,
        topic="Test Topic",
        chapter_title="Test Chapter",
        system_category=None,
    ):  # Added system_category
        """Helper to create a sample DataFrame for testing."""
        data = {
            "chapter_no": [chapter_no] * num_questions,
            # Use "question_text" as per utils.py load_quiz_bank expectations
            "question_text": [f"Q{i+1} Ch{chapter_no}" for i in range(num_questions)],
            "options": [
                [f"Opt A{i}", f"Opt B{i}", f"Opt C{i}"] for i in range(num_questions)
            ],
            "answerIndex": [(i % 3) + 1 for i in range(num_questions)],  # 1-based index
            "topic": [topic] * num_questions,
            "CHAPTER_TITLE": [f"{chapter_title} {chapter_no}"] * num_questions,
        }
        if system_category:  # Add system_category column if provided
            data["system_category"] = [system_category] * num_questions
        return pd.DataFrame(data)

    def test_very_few_questions_creates_single_quiz(self):
        """
        Test Scenario 1: If total questions < questions_per_quiz * single_quiz_threshold,
        only one quiz should be created, capped at questions_per_quiz.
        """
        logger.info("Testing scenario: Very few questions -> single quiz")
        q_per_quiz = 10
        # Use the default threshold from utils.py if not overriding in the call, or be explicit.
        # The import_questions_by_chapter function uses 1.3 as its default.
        # The test call below doesn't override single_quiz_threshold, so it will use 1.3
        # num_questions = int(q_per_quiz * 1.5) - 1 # OLD: 14, with 1.5
        num_questions = (
            int(q_per_quiz * SINGLE_QUIZ_THRESHOLD_FROM_UTILS) - 1
        )  # Example: 10 * 1.3 = 13 -> 12 questions
        if num_questions <= 0:
            num_questions = 1  # ensure at least 1 question for the test's purpose

        # Let's set num_questions to be between q_per_quiz and q_per_quiz * threshold
        # e.g. q_per_quiz=10, threshold=1.3. questions_per_quiz * threshold = 13.
        # So, if num_questions is 12, it should create 1 quiz with 10 questions.
        # If num_questions is 7, it should create 1 quiz with 7 questions.

        num_questions = 12  # Specifically set to test capping behavior

        df = self._create_test_dataframe(chapter_no=1, num_questions=num_questions)

        quiz_count, question_count = import_questions_by_chapter(
            df,
            questions_per_quiz=q_per_quiz,
            # single_quiz_threshold parameter is NOT passed, so utils default of 1.3 is used.
            # Test setup has num_questions (12) < q_per_quiz (10) * 1.3 (utils default) -> 12 < 13, condition met.
            quizzes_per_chapter=2,
            use_descriptive_titles=False,
            use_chapter_prefix=False,
        )

        self.assertEqual(quiz_count, 1, "Should create only 1 quiz")

        # MODIFIED ASSERTION:
        # In this scenario, the single quiz should contain min(num_chapter_questions, questions_per_quiz)
        expected_questions_in_single_quiz = min(num_questions, q_per_quiz)
        self.assertEqual(
            question_count,
            expected_questions_in_single_quiz,
            f"Should use min({num_questions}, {q_per_quiz}) which is {expected_questions_in_single_quiz} questions for the single quiz",
        )
        self.assertEqual(Quiz.objects.count(), 1, "Database should contain 1 quiz")
        quiz = Quiz.objects.first()
        self.assertEqual(quiz.question_count(), expected_questions_in_single_quiz)
        # END MODIFIED ASSERTION

        self.assertEqual(quiz.title, "Test Chapter 1 - Quiz 1")
        self.assertEqual(quiz.system_categories.count(), 0)

    def test_standard_question_count_creates_default_quizzes(self):
        """
        Test Scenario 2: Enough questions for the default number of quizzes, but not
        enough to trigger coverage/threshold logic.
        """
        logger.info("Testing scenario: Standard question count -> default quizzes")
        q_per_quiz = 10
        quizzes_per_chapter = 2
        num_questions = q_per_quiz * quizzes_per_chapter + 5  # e.g., 25 questions

        df = self._create_test_dataframe(chapter_no=2, num_questions=num_questions)

        quiz_count, question_count = import_questions_by_chapter(
            df,
            questions_per_quiz=q_per_quiz,
            quizzes_per_chapter=quizzes_per_chapter,
            # single_quiz_threshold=1.5, # Using default from utils.py (1.3)
            min_coverage_percentage=40,
            max_quizzes_per_chapter=5,
            use_descriptive_titles=False,
            use_chapter_prefix=False,
        )

        self.assertEqual(
            quiz_count,
            quizzes_per_chapter,
            f"Should create default {quizzes_per_chapter} quizzes",
        )
        self.assertEqual(question_count, quizzes_per_chapter * q_per_quiz)
        self.assertEqual(Quiz.objects.count(), quizzes_per_chapter)
        self.assertTrue(Quiz.objects.filter(title="Test Chapter 2 - Quiz 1").exists())
        self.assertTrue(Quiz.objects.filter(title="Test Chapter 2 - Quiz 2").exists())
        for quiz in Quiz.objects.all():
            self.assertEqual(quiz.system_categories.count(), 0)

    def test_many_questions_triggers_coverage_calculation(self):
        """
        Test Scenario 3: Many questions, triggering the coverage percentage calculation,
        but staying below the max_quizzes_per_chapter cap.
        """
        logger.info("Testing scenario: Many questions -> coverage calculation")
        q_per_quiz = 10
        quizzes_per_chapter = 2  # Default starting point for calculation
        num_questions = 80
        min_coverage = 50  # Wants to cover 40 questions
        max_quizzes = 5  # Cap
        # Expected: ceil(40 / 10) = 4 quizzes. 4 <= max_quizzes (5). So, 4.
        expected_quiz_count = 4

        df = self._create_test_dataframe(chapter_no=3, num_questions=num_questions)

        quiz_count, question_count = import_questions_by_chapter(
            df,
            questions_per_quiz=q_per_quiz,
            quizzes_per_chapter=quizzes_per_chapter,
            # single_quiz_threshold=1.5, # Using default from utils.py (1.3)
            min_coverage_percentage=min_coverage,
            max_quizzes_per_chapter=max_quizzes,
            use_descriptive_titles=False,
            use_chapter_prefix=False,
        )

        self.assertEqual(
            quiz_count,
            expected_quiz_count,
            f"Should calculate {expected_quiz_count} quizzes based on coverage",
        )
        self.assertEqual(question_count, expected_quiz_count * q_per_quiz)
        self.assertEqual(Quiz.objects.count(), expected_quiz_count)
        for i in range(1, expected_quiz_count + 1):
            quiz = Quiz.objects.get(title=f"Test Chapter 3 - Quiz {i}")
            self.assertEqual(quiz.system_categories.count(), 0)

    def test_many_questions_hits_max_quiz_cap(self):
        """
        Test Scenario 4: Very many questions, where coverage calculation would exceed
        max_quizzes_per_chapter. Should be capped.
        """
        logger.info("Testing scenario: Very many questions -> hits max quiz cap")
        q_per_quiz = 10
        quizzes_per_chapter = 2
        num_questions = (
            150  # wants to cover 75 questions (50% coverage) -> 8 quizzes needed
        )
        min_coverage = 50
        max_quizzes = 5  # Cap at 5
        expected_quiz_count = max_quizzes

        df = self._create_test_dataframe(chapter_no=4, num_questions=num_questions)

        quiz_count, question_count = import_questions_by_chapter(
            df,
            questions_per_quiz=q_per_quiz,
            quizzes_per_chapter=quizzes_per_chapter,
            # single_quiz_threshold=1.5, # Using default from utils.py (1.3)
            min_coverage_percentage=min_coverage,
            max_quizzes_per_chapter=max_quizzes,
            use_descriptive_titles=False,
            use_chapter_prefix=False,
        )

        self.assertEqual(
            quiz_count,
            expected_quiz_count,
            f"Should be capped at {expected_quiz_count} quizzes",
        )
        self.assertEqual(question_count, expected_quiz_count * q_per_quiz)
        self.assertEqual(Quiz.objects.count(), expected_quiz_count)
        for i in range(1, expected_quiz_count + 1):
            quiz = Quiz.objects.get(title=f"Test Chapter 4 - Quiz {i}")
            self.assertEqual(quiz.system_categories.count(), 0)

    def test_zero_questions_skips_chapter(self):
        """
        Test Scenario 5: Chapter exists in DataFrame but has no questions.
        """
        logger.info("Testing scenario: Zero questions -> skips chapter")
        # Create an empty DataFrame with the expected columns
        df = pd.DataFrame(
            columns=[
                "chapter_no",
                "question_text",
                "options",
                "answerIndex",
                "topic",
                "CHAPTER_TITLE",
            ]
        )
        # Add a row that would imply chapter 5 exists, but will be filtered out if num_questions = 0 for it.
        # Better: create a df for chapter 5 with 0 questions.
        df_ch5_no_q = self._create_test_dataframe(chapter_no=5, num_questions=0)

        quiz_count, question_count = import_questions_by_chapter(df_ch5_no_q)

        self.assertEqual(quiz_count, 0, "Should create 0 quizzes")
        self.assertEqual(question_count, 0, "Should import 0 questions")
        self.assertEqual(Quiz.objects.count(), 0, "Database should contain 0 quizzes")

    def test_chapter_prefix_and_zfill(self):
        """
        Test Scenario 6: Verify chapter prefix and zfill work correctly.
        """
        logger.info("Testing scenario: Chapter prefix and zfill")
        df = self._create_test_dataframe(chapter_no=7, num_questions=5)

        # Test with prefix enabled (default zfill=2 from utils.py)
        Quiz.objects.all().delete()
        SystemCategory.objects.all().delete()
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            # single_quiz_threshold=1.5, # Using default from utils.py (1.3)
            use_descriptive_titles=False,
            use_chapter_prefix=True,
            # chapter_zfill=2, # Using default from utils.py
        )
        quiz1 = Quiz.objects.get(title__startswith="07 ")
        self.assertEqual(quiz1.title, "07 Test Chapter 7 - Quiz 1")
        self.assertEqual(quiz1.system_categories.count(), 0)

        # Test with prefix enabled (zfill=3)
        Quiz.objects.all().delete()
        SystemCategory.objects.all().delete()
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            # single_quiz_threshold=1.5, # Using default from utils.py (1.3)
            use_descriptive_titles=False,
            use_chapter_prefix=True,
            chapter_zfill=3,
        )
        quiz2 = Quiz.objects.get(title__startswith="007 ")
        self.assertEqual(quiz2.title, "007 Test Chapter 7 - Quiz 1")
        self.assertEqual(quiz2.system_categories.count(), 0)

        # Test with prefix disabled
        Quiz.objects.all().delete()
        SystemCategory.objects.all().delete()
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            # single_quiz_threshold=1.5, # Using default from utils.py (1.3)
            use_descriptive_titles=False,
            use_chapter_prefix=False,
        )
        quiz3 = Quiz.objects.first()
        self.assertEqual(quiz3.title, "Test Chapter 7 - Quiz 1")
        self.assertEqual(quiz3.system_categories.count(), 0)

    def test_descriptive_titles(self):
        """
        Test Scenario 6b: Verify descriptive titles are used when enabled.
        """
        logger.info("Testing scenario: Descriptive titles")
        df = self._create_test_dataframe(
            chapter_no=8,
            num_questions=5,
            topic="Specific Topic",
            chapter_title="Specific Chapter",
        )
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            # single_quiz_threshold=1.5, # Using default from utils.py (1.3)
            use_descriptive_titles=True,  # Explicitly True
            use_chapter_prefix=False,  # Disable prefix to isolate title check
        )
        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        self.assertEqual(quiz.title, "Specific Chapter 8: Specific Topic - Quiz 1")
        self.assertTrue(Topic.objects.filter(name="Specific Topic").exists())
        self.assertEqual(quiz.topics.first().name, "Specific Topic")
        self.assertEqual(quiz.questions.first().topic.name, "Specific Topic")
        self.assertEqual(quiz.system_categories.count(), 0)

    def test_non_numeric_chapter_handling(self):
        """
        Test Scenario 7: Handle chapter_no that isn't purely numeric.
        """
        logger.info("Testing scenario: Non-numeric chapter_no")
        chapter_id_str = "Appendix A"
        df = self._create_test_dataframe(chapter_no=chapter_id_str, num_questions=5)
        import_questions_by_chapter(
            df,
            questions_per_quiz=10,
            # single_quiz_threshold=1.5, # Using default from utils.py (1.3)
            use_descriptive_titles=False,
            use_chapter_prefix=True,  # Prefix enabled
            # chapter_zfill=2, # Using default from utils.py
        )
        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        # When chapter is not numeric, zfill won't apply, it's just "chapter_id_str "
        self.assertTrue(quiz.title.startswith(f"{chapter_id_str} "))
        self.assertEqual(
            quiz.title, f"{chapter_id_str} Test Chapter {chapter_id_str} - Quiz 1"
        )
        self.assertEqual(quiz.system_categories.count(), 0)

    # --- NEW TEST CASES for SystemCategory ---

    def test_system_category_assignment_via_cli_parameter(self):
        """Test assigning a SystemCategory via the cli_system_category_name parameter."""
        logger.info("Testing SystemCategory assignment via CLI parameter")
        category_name = "CLI Biology Category"
        df = self._create_test_dataframe(
            chapter_no=1, num_questions=3
        )  # No 'system_category' column

        import_questions_by_chapter(
            df, questions_per_quiz=5, cli_system_category_name=category_name
        )

        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        self.assertIsNotNone(quiz)

        self.assertTrue(SystemCategory.objects.filter(name=category_name).exists())
        category_obj = SystemCategory.objects.get(name=category_name)

        self.assertIn(category_obj, quiz.system_categories.all())
        self.assertEqual(quiz.system_categories.count(), 1)

    def test_system_category_assignment_from_dataframe_column(self):
        """Test assigning a SystemCategory based on a column in the DataFrame."""
        logger.info("Testing SystemCategory assignment from DataFrame column")
        category_name_df = "DataFrame Physics Category"
        df = self._create_test_dataframe(
            chapter_no=2, num_questions=4, system_category=category_name_df
        )

        import_questions_by_chapter(
            df, questions_per_quiz=5, cli_system_category_name=None
        )

        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        self.assertIsNotNone(quiz)

        self.assertTrue(SystemCategory.objects.filter(name=category_name_df).exists())
        category_obj = SystemCategory.objects.get(name=category_name_df)

        self.assertIn(category_obj, quiz.system_categories.all())
        self.assertEqual(quiz.system_categories.count(), 1)

    def test_cli_system_category_overrides_dataframe_column(self):
        """Test that cli_system_category_name overrides the DataFrame's system_category column."""
        logger.info("Testing CLI SystemCategory override of DataFrame column")
        category_name_df = "DF Internal Category"
        category_name_cli = "CLI Override Main Category"

        df = self._create_test_dataframe(
            chapter_no=3, num_questions=2, system_category=category_name_df
        )

        import_questions_by_chapter(
            df, questions_per_quiz=5, cli_system_category_name=category_name_cli
        )

        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        self.assertIsNotNone(quiz)

        self.assertTrue(SystemCategory.objects.filter(name=category_name_cli).exists())
        cli_category_obj = SystemCategory.objects.get(name=category_name_cli)
        self.assertIn(cli_category_obj, quiz.system_categories.all())

        # The DF category might or might not be created depending on whether other quizzes used it.
        # The key is that THIS quiz is NOT associated with it.
        if SystemCategory.objects.filter(name=category_name_df).exists():
            df_category_obj = SystemCategory.objects.get(name=category_name_df)
            self.assertNotIn(df_category_obj, quiz.system_categories.all())

        self.assertEqual(quiz.system_categories.count(), 1)
        self.assertEqual(quiz.system_categories.first().name, category_name_cli)

    def test_no_system_category_assigned_when_none_provided(self):
        """Test no SystemCategory is assigned if not in DF and not in CLI param."""
        logger.info("Testing no SystemCategory assignment")
        df = self._create_test_dataframe(chapter_no=4, num_questions=1)

        import_questions_by_chapter(
            df, questions_per_quiz=5, cli_system_category_name=None
        )

        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.system_categories.count(), 0)

    def test_system_category_from_df_most_common_value(self):
        """Test that the most common system_category from chapter_df is used."""
        logger.info("Testing most common system_category from DataFrame for a chapter")
        data = {
            "chapter_no": [1, 1, 1, 1, 1],  # All same chapter
            "question_text": [f"Q{i}" for i in range(5)],  # Corrected from "text"
            "options": [["A", "B"]] * 5,
            "answerIndex": [1] * 5,
            "topic": ["Mixed"] * 5,
            "CHAPTER_TITLE": ["Mixed Chapter"] * 5,
            "system_category": [
                "Alpha",
                "Beta",
                "Alpha",
                "Gamma",
                "Alpha",
            ],  # Alpha is most common
        }
        df = pd.DataFrame(data)

        import_questions_by_chapter(
            df, questions_per_quiz=5, cli_system_category_name=None
        )

        self.assertEqual(Quiz.objects.count(), 1)
        quiz = Quiz.objects.first()
        self.assertIsNotNone(quiz)
        self.assertEqual(quiz.system_categories.count(), 1)
        self.assertEqual(quiz.system_categories.first().name, "Alpha")
