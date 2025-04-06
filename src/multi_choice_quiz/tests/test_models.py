from django.test import TestCase
from multi_choice_quiz.models import Quiz, Question, Option, Topic
from multi_choice_quiz.transform import (
    quiz_bank_to_models,
    models_to_frontend,
    frontend_to_models,
)


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


class QuestionModelTests(TestCase):
    """Tests for the Question model and its methods."""

    def setUp(self):
        """Set up test data."""
        self.topic = Topic.objects.create(name="Test Topic")
        self.quiz = Quiz.objects.create(title="Test Quiz")
        self.quiz.topics.add(self.topic)

        self.question = Question.objects.create(
            quiz=self.quiz, topic=self.topic, text="Test question?", position=1
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

    def test_question_string_representation(self):
        """Test string representation of questions."""
        self.assertEqual(str(self.question), "Test question?")

        # Test long question truncation in __str__
        long_question = Question.objects.create(
            quiz=self.quiz,
            text="This is a very long question that should be truncated in the string representation to ensure it doesn't get too long",
            position=2,
        )
        self.assertTrue(len(str(long_question)) < len(long_question.text))
        self.assertTrue(str(long_question).endswith("..."))

    def test_correct_option(self):
        """Test the correct_option method."""
        correct = self.question.correct_option()
        self.assertEqual(correct, self.option2)
        self.assertEqual(correct.text, "Option B")

    def test_multiple_correct_options(self):
        """Test behavior when multiple options are marked correct."""
        # Mark another option as correct
        self.option3.is_correct = True
        self.option3.save()

        # Should return the first correct option
        self.assertEqual(self.question.correct_option().position, 2)

    def test_correct_option_index(self):
        """Test the correct_option_index method (0-based conversion)."""
        # option2 is position 2 (1-based) so index should be 1 (0-based)
        self.assertEqual(self.question.correct_option_index(), 1)

    def test_options_list(self):
        """Test the options_list method."""
        options = self.question.options_list()
        self.assertEqual(len(options), 3)
        self.assertEqual(options[0], "Option A")
        self.assertEqual(options[1], "Option B")
        self.assertEqual(options[2], "Option C")

    def test_to_dict(self):
        """Test the to_dict method converting to frontend format."""
        question_dict = self.question.to_dict()

        self.assertEqual(question_dict["id"], self.question.id)
        self.assertEqual(question_dict["text"], "Test question?")
        self.assertEqual(len(question_dict["options"]), 3)
        self.assertEqual(question_dict["answerIndex"], 1)  # 0-based


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

        # Creating another option with the same position should raise an error
        with self.assertRaises(Exception):
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

        # Verify options
        self.assertEqual(question.options.count(), 4)
        correct_option = question.correct_option()
        self.assertIsNotNone(correct_option)
        self.assertEqual(correct_option.position, 2)  # 1-based position

    def test_models_to_frontend(self):
        """Test converting models to frontend format (0-based indexing)."""
        # Create test data
        test_data = [
            {
                "text": "Test question?",
                "options": ["A", "B", "C", "D"],
                "answerIndex": 2,  # 1-based index
            }
        ]

        quiz = quiz_bank_to_models(test_data, "Test Quiz")
        question = quiz.questions.first()

        # Convert to frontend format
        frontend_data = models_to_frontend([question])

        # Verify conversion
        self.assertEqual(len(frontend_data), 1)
        self.assertEqual(frontend_data[0]["text"], "Test question?")
        self.assertEqual(len(frontend_data[0]["options"]), 4)
        self.assertEqual(frontend_data[0]["answerIndex"], 1)  # 0-based index

    def test_frontend_to_models(self):
        """Test converting frontend format (0-based) to models (1-based)."""
        frontend_test = [
            {
                "text": "Frontend test?",
                "options": ["X", "Y", "Z"],
                "answerIndex": 1,  # 0-based index (second option)
            }
        ]

        quiz = frontend_to_models(frontend_test, "Frontend Test Quiz")

        # Verify question
        question = quiz.questions.first()
        self.assertEqual(question.text, "Frontend test?")

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
            }
        ]

        # First transformation: quiz bank → models
        quiz1 = quiz_bank_to_models(quiz_bank_data, "First Quiz")
        question1 = quiz1.questions.first()

        # Second transformation: models → frontend
        frontend_data = models_to_frontend([question1])

        # Verify frontend data has 0-based index
        self.assertEqual(frontend_data[0]["answerIndex"], 2)  # 0-based index

        # Third transformation: frontend → models
        quiz2 = frontend_to_models(frontend_data, "Second Quiz")
        question2 = quiz2.questions.first()

        # Verify final result matches original
        self.assertEqual(question1.text, question2.text)
        self.assertEqual(
            question1.correct_option().position, question2.correct_option().position
        )
        self.assertEqual(question1.options.count(), question2.options.count())
