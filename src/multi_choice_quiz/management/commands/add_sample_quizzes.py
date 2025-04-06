import json
import os
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from multi_choice_quiz.models import Quiz, Question, Option, Topic
from multi_choice_quiz.transform import quiz_bank_to_models


class Command(BaseCommand):
    help = "Add sample quiz data to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to a JSON file containing quiz data (optional)",
        )

    def handle(self, *args, **options):
        if options["file"]:
            self.import_from_file(options["file"])
        else:
            self.add_sample_quizzes()

    def import_from_file(self, file_path):
        """Import quiz data from a JSON file."""
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            quiz_title = data.get("title", "Imported Quiz")
            topic_name = data.get("topic")
            questions = data.get("questions", [])

            if not questions:
                self.stderr.write(self.style.ERROR("No questions found in the file"))
                return

            # Create the quiz using our transform function
            quiz = quiz_bank_to_models(questions, quiz_title, topic_name)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported quiz "{quiz.title}" with {quiz.question_count()} questions'
                )
            )

        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR("Invalid JSON format"))
        except ValidationError as e:
            self.stderr.write(self.style.ERROR(f"Validation error: {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error importing quiz: {str(e)}"))

    def add_sample_quizzes(self):
        """Add predefined sample quizzes to the database."""
        # Check if we already have sample quizzes
        if Quiz.objects.filter(title__startswith="Sample Quiz").exists():
            self.stdout.write(
                self.style.WARNING("Sample quizzes already exist in the database")
            )
            return

        # Create sample topics
        topics = {
            "general": Topic.objects.create(
                name="General Knowledge", description="Basic knowledge questions"
            ),
            "science": Topic.objects.create(
                name="Science", description="Scientific concepts and discoveries"
            ),
            "programming": Topic.objects.create(
                name="Programming", description="Software development concepts"
            ),
        }

        # Sample Quiz 1: General Knowledge
        general_questions = [
            {
                "text": "What is the capital of France?",
                "options": ["London", "Paris", "Berlin", "Madrid", "Rome"],
                "answerIndex": 2,  # 1-based index
            },
            {
                "text": "Which river is the longest in the world?",
                "options": ["Amazon", "Nile", "Mississippi", "Yangtze", "Congo"],
                "answerIndex": 2,  # 1-based index
            },
            {
                "text": "What is the highest mountain peak in the world?",
                "options": ["K2", "Kangchenjunga", "Makalu", "Mount Everest", "Lhotse"],
                "answerIndex": 4,  # 1-based index
            },
        ]

        # Sample Quiz 2: Programming
        programming_questions = [
            {
                "text": "How can you pass initial state from your Django view context to an Alpine.js x-data directive?",
                "options": [
                    "Store the context in browser cookies for Alpine to read.",
                    "Fetch the data using HTMX and then pass it to Alpine.",
                    "Alpine automatically detects Django context variables.",
                    "Use a special `x-django-context` directive.",
                    "Embed the Django context variable (often JSON-serialized) directly into the `x-data` attribute string within the template.",
                ],
                "answerIndex": 5,  # 1-based index
            },
            {
                "text": "In a multi-step wizard form driven by HTMX, where is the state (data from previous steps) typically stored between steps?",
                "options": [
                    "Directly in the browser's URL using `hx-push-url`.",
                    "Entirely within the client-side JavaScript variables.",
                    "Often stored in the Django session on the server-side or passed via hidden fields in subsequent forms.",
                    "HTMX automatically manages multi-step form state.",
                    "In HTML5 `localStorage` exclusively.",
                ],
                "answerIndex": 3,  # 1-based index
            },
            {
                "text": "What does the Django ORM provide?",
                "options": [
                    "A way to write HTML templates",
                    "A database-abstraction API that lets you create, retrieve, update and delete objects",
                    "A front-end JavaScript framework",
                    "A deployment platform for Django applications",
                    "A testing framework for Django views",
                ],
                "answerIndex": 2,  # 1-based index
            },
        ]

        # Sample Quiz 3: Science
        science_questions = [
            {
                "text": "What is the chemical symbol for gold?",
                "options": ["Go", "Ag", "Au", "Gd", "Fe"],
                "answerIndex": 3,  # 1-based index
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "options": ["Venus", "Jupiter", "Mars", "Saturn", "Mercury"],
                "answerIndex": 3,  # 1-based index
            },
            {
                "text": "What is the formula for water?",
                "options": ["H2O2", "CO2", "H2O", "NaCl", "CH4"],
                "answerIndex": 3,  # 1-based index
            },
        ]

        # Create the quizzes using our transform function
        quiz1 = quiz_bank_to_models(
            general_questions, "Sample Quiz: General Knowledge", "General Knowledge"
        )
        quiz2 = quiz_bank_to_models(
            programming_questions, "Sample Quiz: Programming", "Programming"
        )
        quiz3 = quiz_bank_to_models(
            science_questions, "Sample Quiz: Science", "Science"
        )

        self.stdout.write(self.style.SUCCESS("Successfully added sample quizzes:"))
        self.stdout.write(f"1. {quiz1.title} - {quiz1.question_count()} questions")
        self.stdout.write(f"2. {quiz2.title} - {quiz2.question_count()} questions")
        self.stdout.write(f"3. {quiz3.title} - {quiz3.question_count()} questions")
