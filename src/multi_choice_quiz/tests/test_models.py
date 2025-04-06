from django.test import TestCase
from django.core.exceptions import ValidationError
from multi_choice_quiz.models import Quiz, Question, Option, Topic
from multi_choice_quiz.transform import quiz_bank_to_models, models_to_frontend, frontend_to_models


class QuizModelTests(TestCase):
    def setUp(self):
        """Set up test data."""
        # Create a topic
        self.topic = Topic.objects.create(
            name="Test Topic",
            description="A topic for testing"
        )
        
        # Create a quiz
        self.quiz = Quiz.objects.create(
            title="Test Quiz",
            description="A quiz for testing"
        )
        self.quiz.topics.add(self.topic)
        
        # Create a question
        self.question = Question.objects.create(
            quiz=self.quiz,
            topic=self.topic,
            text="What is the answer to life, the universe, and everything?",
            position=1
        )
        
        # Create options
        self.options = [
            Option.objects.create(
                question=self.question,
                text="41",
                position=1,
                is_correct=False
            ),
            Option.objects.create(
                question=self.question,
                text="42",
                position=2,
                is_correct=True
            ),
            Option.objects.create(
                question=self.question,
                text="43",
                position=3,
                is_correct=False
            ),
            Option.objects.create(
                question=self.question,
                text="44",
                position=4,
                is_correct=False
            )
        ]
    
    def test_quiz_question_count(self):
        """Test the question_count method on Quiz."""
        self.assertEqual(self.quiz.question_count(), 1)
        
        # Add another question
        Question.objects.create(
            quiz=self.quiz,
            topic=self.topic,
            text="Second question",
            position=2
        )
        
        # Refresh from database
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.question_count(), 2)
    
    def test_quiz_get_topics_display(self):
        """Test the get_topics_display method on Quiz."""
        self.assertEqual(self.quiz.get_topics_display(), "Test Topic")
        
        # Add another topic
        topic2 = Topic.objects.create(
            name="Another Topic",
            description="A second topic for testing"
        )
        self.quiz.topics.add(topic2)
        
        # The method should return topics in alphabetical order
        self.assertEqual(self.quiz.get_topics_display(), "Another Topic, Test Topic")
    
    def test_question_correct_option(self):
        """Test the correct_option method on Question."""
        correct_option = self.question.correct_option()
        self.assertEqual(correct_option.text, "42")
        self.assertEqual(correct_option.position, 2)
        
        # Test with multiple correct answers (should return the first one)
        self.options[2].is_correct = True
        self.options[2].save()
        
        self.assertEqual(self.question.correct_option().text, "42")
    
    def test_question_correct_option_index(self):
        """Test the correct_option_index method on Question."""
        # The correct option is at position 2 (1-based), so index should be 1 (0-based)
        self.assertEqual(self.question.correct_option_index(), 1)
    
    def test_question_options_list(self):
        """Test the options_list method on Question."""
        options_list = self.question.options_list()
        self.assertEqual(options_list, ["41", "42", "43", "44"])
    
    def test_question_to_dict(self):
        """Test the to_dict method on Question."""
        question_dict = self.question.to_dict()
        
        self.assertEqual(question_dict["id"], self.question.id)
        self.assertEqual(question_dict["text"], "What is the answer to life, the universe, and everything?")
        self.assertEqual(question_dict["options"], ["41", "42", "43", "44"])
        self.assertEqual(question_dict["answerIndex"], 1)  # 0-based index for JavaScript


class TransformationTests(TestCase):
    def test_quiz_bank_to_models(self):
        """Test converting quiz bank format to models."""
        quiz_data = [
            {
                "text": "Question 1",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answerIndex": 2  # 1-based index
            },
            {
                "text": "Question 2",
                "options": ["Option W", "Option X", "Option Y", "Option Z"],
                "answerIndex": 3  # 1-based index
            }
        ]
        
        quiz = quiz_bank_to_models(quiz_data, "Test Quiz", "Test Topic")
        
        # Verify quiz
        self.assertEqual(quiz.title, "Test Quiz")
        self.assertEqual(quiz.topics.first().name, "Test Topic")
        self.assertEqual(quiz.question_count(), 2)
        
        # Verify questions
        questions = quiz.questions.order_by("position")
        self.assertEqual(questions[0].text, "Question 1")
        self.assertEqual(questions[1].text, "Question 2")
        
        # Verify options and correct answers
        self.assertEqual(questions[0].options.count(), 4)
        self.assertEqual(questions[0].correct_option().text, "Option B")
        self.assertEqual(questions[0].correct_option().position, 2)
        
        self.assertEqual(questions[1].options.count(), 4)
        self.assertEqual(questions[1].correct_option().text, "Option Y")
        self.assertEqual(questions[1].correct_option().position, 3)
    
    def test_models_to_frontend(self):
        """Test converting models to frontend format."""
        # Create test data
        topic = Topic.objects.create(name="Test Topic")
        quiz = Quiz.objects.create(title="Test Quiz")
        quiz.topics.add(topic)
        
        q1 = Question.objects.create(
            quiz=quiz,
            text="Question 1",
            position=1
        )
        Option.objects.create(question=q1, text="A", position=1, is_correct=False)
        Option.objects.create(question=q1, text="B", position=2, is_correct=True)
        
        q2 = Question.objects.create(
            quiz=quiz,
            text="Question 2",
            position=2
        )
        Option.objects.create(question=q2, text="X", position=1, is_correct=True)
        Option.objects.create(question=q2, text="Y", position=2, is_correct=False)
        
        # Convert to frontend format
        frontend_data = models_to_frontend([q1, q2])
        
        # Verify conversion
        self.assertEqual(len(frontend_data), 2)
        
        self.assertEqual(frontend_data[0]["text"], "Question 1")
        self.assertEqual(frontend_data[0]["options"], ["A", "B"])
        self.assertEqual(frontend_data[0]["answerIndex"], 1)  # 0-based
        
        self.assertEqual(frontend_data[1]["text"], "Question 2")
        self.assertEqual(frontend_data[1]["options"], ["X", "Y"])
        self.assertEqual(frontend_data[1]["answerIndex"], 0)  # 0-based
    
    def test_frontend_to_models(self):
        """Test converting frontend format to models."""
        frontend_data = [
            {
                "text": "Question 1",
                "options": ["Option A", "Option B"],
                "answerIndex": 1  # 0-based index
            },
            {
                "text": "Question 2",
                "options": ["Option X", "Option Y"],
                "answerIndex": 0  # 0-based index
            }
        ]
        
        quiz = frontend_to_models(frontend_data, "Test Quiz", "Test Topic")
        
        # Verify quiz
        self.assertEqual(quiz.title, "Test Quiz")
        self.assertEqual(quiz.topics.first().name, "Test Topic")
        self.assertEqual(quiz.question_count(), 2)
        
        # Verify questions
        questions = quiz.questions.order_by("position")
        self.assertEqual(questions[0].text, "Question 1")
        self.assertEqual(questions[1].text, "Question 2")
        
        # Verify options and correct answers
        self.assertEqual(questions[0].options.count(), 2)
        self.assertEqual(questions[0].correct_option().text, "Option B")
        self.assertEqual(questions[0].correct_option().position, 2)  # 1-based
        
        self.assertEqual(questions[1].options.count(), 2)
        self.assertEqual(questions[1].correct_option().text, "Option X")
        self.assertEqual(questions[1].correct_option().position, 1)  # 1-based
    
    def test_roundtrip_conversion(self):
        """Test a full roundtrip conversion between formats."""
        # Start with quiz bank format (1-based indexing)
        quiz_bank_data = [
            {
                "text": "Question X",
                "options": ["A", "B", "C", "D"],
                "answerIndex": 3  # 1-based index
            }
        ]
        
        # Convert to models
        quiz = quiz_bank_to_models(quiz_bank_data, "Roundtrip Quiz")
        
        # Get questions
        questions = quiz.questions.all()
        
        # Convert to frontend format (0-based indexing)
        frontend_data = models_to_frontend(questions)
        
        # Verify frontend data
        self.assertEqual(frontend_data[0]["text"], "Question X")
        self.assertEqual(frontend_data[0]["options"], ["A", "B", "C", "D"])
        self.assertEqual(frontend_data[0]["answerIndex"], 2)  # 0-based index
        
        # Convert back to models
        quiz2 = frontend_to_models(frontend_data, "Roundtrip Quiz 2")
        
        # Get questions
        questions2 = quiz2.questions.all()
        
        # Verify that the correct option is the same
        self.assertEqual(questions[0].correct_option().text, "C")
        self.assertEqual(questions2[0].correct_option().text, "C")
        
        # Verify that the correct option position is the same (1-based)
        self.assertEqual(questions[0].correct_option().position, 3)
        self.assertEqual(questions2[0].correct_option().position, 3)
