# src/multi_choice_quiz/tests/test_models.py
# UPDATED based on Session 4 evaluation

from django.test import TestCase
from multi_choice_quiz.models import Quiz, Question, Option, Topic
from multi_choice_quiz.transform import (
    quiz_bank_to_models,
    models_to_frontend,
    frontend_to_models,
)
import json  # Needed for some tests
from django.db import IntegrityError  # <<< ADDED for test_unique_position


# --- Replace existing logger setup with this ---
from .test_logging import setup_test_logging

logger = setup_test_logging(__name__, "multi_choice_quiz")
# --- End Replacement ---


class TopicModelTests(TestCase):
    """Tests for the Topic model."""

    def test_topic_creation(self):
        """Test basic topic creation and string representation."""
        topic = Topic.objects.create(
            name="Test Topic", description="This is a test topic"
        )

        self.assertEqual(str(topic), "Test Topic")
        self.assertEqual(topic.description, "This is a test topic")


class QuizModelTests(TestCase):
    """Tests for the Quiz model and relationships."""

    def setUp(self):
        """Set up test data."""
        self.topic = Topic.objects.create(name="Test Topic")
        self.quiz = Quiz.objects.create(
            title="Test Quiz", description="This is a test quiz"
        )
        self.quiz.topics.add(self.topic)

    def test_quiz_creation(self):
        """Test basic quiz creation and properties."""
        self.assertEqual(str(self.quiz), "Test Quiz")
        self.assertEqual(self.quiz.description, "This is a test quiz")
        self.assertTrue(self.quiz.is_active)

        # Test topics relationship
        self.assertEqual(self.quiz.topics.count(), 1)
        self.assertEqual(self.quiz.topics.first().name, "Test Topic")

        # Test get_topics_display method
        self.assertEqual(self.quiz.get_topics_display(), "Test Topic")

    def test_question_count(self):
        """Test the question_count method."""
        # Initially no questions
        self.assertEqual(self.quiz.question_count(), 0)

        # Add questions
        Question.objects.create(
            quiz=self.quiz, topic=self.topic, text="Question 1", position=1
        )
        Question.objects.create(
            quiz=self.quiz, topic=self.topic, text="Question 2", position=2
        )

        # Now should have 2 questions
        self.assertEqual(self.quiz.question_count(), 2)


# Only the test cases that need to be updated for the tag field:


class QuestionModelTests(TestCase):
    """Tests for the Question model and its methods."""

    def setUp(self):
        """Set up test data."""
        self.topic = Topic.objects.create(name="Test Topic")
        self.quiz = Quiz.objects.create(title="Test Quiz")
        self.quiz.topics.add(self.topic)

        self.question = Question.objects.create(
            quiz=self.quiz,
            topic=self.topic,
            text="Test question?",
            position=1,
            tag="test-tag",  # Added tag field
        )

        # Create options
        self.option1 = Option.objects.create(
            question=self.question, text="Option A", position=1, is_correct=False
        )
        self.option2 = Option.objects.create(
            question=self.question, text="Option B", position=2, is_correct=True
        )
        self.option3 = Option.objects.create(
            question=self.question, text="Option C", position=3, is_correct=False
        )

    # Add test for tag field
    def test_tag_field(self):
        """Test the tag field."""
        self.assertEqual(self.question.tag, "test-tag")

        # Test blank tag is allowed
        question_no_tag = Question.objects.create(
            quiz=self.quiz, text="Question without tag", position=2
        )
        self.assertEqual(question_no_tag.tag, "")

    def test_to_dict(self):
        """Test the to_dict method converting to frontend format."""
        question_dict = self.question.to_dict()

        self.assertEqual(question_dict["id"], self.question.id)
        self.assertEqual(question_dict["text"], "Test question?")
        self.assertEqual(len(question_dict["options"]), 3)
        self.assertEqual(question_dict["answerIndex"], 1)  # 0-based
        self.assertEqual(question_dict["tag"], "test-tag")  # Check tag is included


class OptionModelTests(TestCase):
    """Tests for the Option model."""

    def setUp(self):
        """Set up test data."""
        self.quiz = Quiz.objects.create(title="Test Quiz")
        self.question = Question.objects.create(
            quiz=self.quiz, text="Test question?", position=1
        )

    def test_option_creation(self):
        """Test basic option creation."""
        option = Option.objects.create(
            question=self.question, text="Test option", position=1, is_correct=True
        )

        self.assertEqual(option.text, "Test option")
        self.assertEqual(option.position, 1)
        self.assertTrue(option.is_correct)

    def test_option_string_representation(self):
        """Test string representation of options."""
        option = Option.objects.create(
            question=self.question, text="Short option", position=1, is_correct=True
        )

        self.assertEqual(str(option), "Short option (Correct: True)")

        # Test long option truncation
        long_option = Option.objects.create(
            question=self.question,
            text="This is a very long option text that should be truncated in the string representation",
            position=2,
            is_correct=False,
        )

        self.assertTrue(len(str(long_option).split("...")[0]) <= 30)
        self.assertTrue("(Correct: False)" in str(long_option))

    def test_unique_position(self):
        """Test that options must have unique positions within a question."""
        Option.objects.create(question=self.question, text="Option 1", position=1)

        # Creating another option with the same position should raise an IntegrityError
        # <<< UPDATED EXCEPTION TYPE >>>
        with self.assertRaises(IntegrityError):
            Option.objects.create(question=self.question, text="Option 2", position=1)


class TransformationTests(TestCase):
    """Tests for the transformation functions."""

    def test_quiz_bank_to_models(self):
        """Test transforming quiz bank format (1-based) to database models."""
        test_data = [
            {
                "text": "Test question?",
                "options": ["A", "B", "C", "D"],
                "answerIndex": 2,  # 1-based index
                "tag": "q-tag",  # <<< ADDED tag to input >>>
                "chapter_no": "CH1",  # <<< ADDED chapter to input >>>
            }
        ]

        quiz = quiz_bank_to_models(test_data, "Test Quiz", "Test Topic")

        # Verify quiz
        self.assertIsNotNone(quiz.id)
        self.assertEqual(quiz.title, "Test Quiz")
        self.assertEqual(quiz.topics.count(), 1)
        self.assertEqual(quiz.topics.first().name, "Test Topic")

        # Verify question
        self.assertEqual(quiz.questions.count(), 1)
        question = quiz.questions.first()
        self.assertEqual(question.text, "Test question?")
        self.assertEqual(question.tag, "q-tag")  # <<< VERIFY tag saved >>>
        self.assertEqual(question.chapter_no, "CH1")  # <<< VERIFY chapter saved >>>
        self.assertEqual(
            question.topic.name, "Test Topic"
        )  # <<< VERIFY topic linked to question >>>

        # Verify options
        self.assertEqual(question.options.count(), 4)
        correct_option = question.correct_option()
        self.assertIsNotNone(correct_option)
        self.assertEqual(correct_option.position, 2)  # 1-based position
        self.assertEqual(
            correct_option.text, "B"
        )  # <<< VERIFY text of correct option >>>

    def test_models_to_frontend(self):
        """Test converting models to frontend format (0-based indexing)."""
        # Create test data
        test_data = [
            {
                "text": "Test question?",
                "options": ["A", "B", "C", "D"],
                "answerIndex": 2,  # 1-based index
                "tag": "model-tag",  # <<< ADDED tag >>>
                "chapter_no": "CH1",  # <<< ADDED chapter >>>
            }
        ]

        quiz = quiz_bank_to_models(test_data, "Test Quiz", "Test Topic")
        question = quiz.questions.first()

        # Convert to frontend format
        frontend_data = models_to_frontend([question])

        # Verify conversion
        self.assertEqual(len(frontend_data), 1)
        self.assertEqual(frontend_data[0]["text"], "Test question?")
        self.assertEqual(len(frontend_data[0]["options"]), 4)
        self.assertEqual(frontend_data[0]["answerIndex"], 1)  # 0-based index
        self.assertEqual(
            frontend_data[0]["tag"], "model-tag"
        )  # <<< VERIFY tag included >>>
        # Chapter_no is not part of the frontend format per `Question.to_dict()`, so no need to check here.

    def test_frontend_to_models(self):
        """Test converting frontend format (0-based) to models (1-based)."""
        frontend_test = [
            {
                "id": 99,  # Simulate potential ID from frontend (should be ignored)
                "text": "Frontend test?",
                "options": ["X", "Y", "Z"],
                "answerIndex": 1,  # 0-based index (second option)
                "tag": "frontend-tag",  # <<< ADDED tag >>>
                # chapter_no is not typically sent from frontend, so not included here
            }
        ]

        quiz = frontend_to_models(frontend_test, "Frontend Test Quiz", "Frontend Topic")

        # Verify question
        question = quiz.questions.first()
        self.assertEqual(question.text, "Frontend test?")
        self.assertEqual(question.tag, "frontend-tag")  # <<< VERIFY tag saved >>>
        self.assertEqual(
            question.chapter_no, ""
        )  # <<< VERIFY chapter is blank (not in input) >>>
        self.assertEqual(
            question.topic.name, "Frontend Topic"
        )  # <<< VERIFY topic linked >>>

        # Verify options
        options = list(question.options.order_by("position"))
        self.assertEqual(len(options), 3)

        # Verify correct answer is position 2 (1-based, second option)
        correct = question.correct_option()
        self.assertIsNotNone(correct)
        self.assertEqual(correct.position, 2)
        self.assertEqual(correct.text, "Y")

    def test_round_trip_transformation(self):
        """Test a round-trip transformation (quiz bank → models → frontend → models)."""
        # Start with quiz bank format
        quiz_bank_data = [
            {
                "text": "Round trip test?",
                "options": ["Option 1", "Option 2", "Option 3"],
                "answerIndex": 3,  # 1-based index (third option)
                "tag": "round-trip",  # <<< ADDED tag >>>
                "chapter_no": "RT1",  # <<< ADDED chapter >>>
            }
        ]

        # First transformation: quiz bank → models
        quiz1 = quiz_bank_to_models(quiz_bank_data, "First Quiz", "Round Trip Topic")
        question1 = quiz1.questions.first()
        # <<< ADDED asserts after first step >>>
        self.assertEqual(question1.tag, "round-trip")
        self.assertEqual(question1.chapter_no, "RT1")
        self.assertEqual(question1.topic.name, "Round Trip Topic")
        # <<< END Added asserts >>>

        # Second transformation: models → frontend
        frontend_data = models_to_frontend([question1])

        # Verify frontend data has 0-based index and tag
        self.assertEqual(frontend_data[0]["answerIndex"], 2)  # 0-based index
        self.assertEqual(
            frontend_data[0]["tag"], "round-trip"
        )  # <<< VERIFY tag included >>>

        # Third transformation: frontend → models
        quiz2 = frontend_to_models(
            frontend_data, "Second Quiz", "Round Trip Topic"
        )  # Topic name passed here
        question2 = quiz2.questions.first()

        # Verify final result matches original relevant fields
        self.assertEqual(question1.text, question2.text)
        self.assertEqual(
            question1.correct_option().position, question2.correct_option().position
        )
        self.assertEqual(question1.options.count(), question2.options.count())
        self.assertEqual(question1.tag, question2.tag)  # <<< VERIFY tag survived >>>
        # chapter_no won't survive round trip as it's not in frontend format
        self.assertEqual(question2.chapter_no, "")  # <<< VERIFY chapter blank >>>
        # Topic association will be based on the name provided to frontend_to_models
        self.assertEqual(
            question2.topic.name, "Round Trip Topic"
        )  # <<< VERIFY topic association >>>
