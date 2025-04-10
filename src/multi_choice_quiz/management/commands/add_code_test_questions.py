# src/multi_choice_quiz/management/commands/add_code_test_questions.py

import os
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from multi_choice_quiz.models import Quiz, Question, Option, Topic
from multi_choice_quiz.transform import quiz_bank_to_models


class Command(BaseCommand):
    help = "Add sample quiz questions with code elements for testing CSS display"

    def handle(self, *args, **options):
        """Add questions with different code display patterns."""
        # Check if we already have a test quiz
        if Quiz.objects.filter(title="Code Display Test Quiz").exists():
            self.stdout.write(
                self.style.WARNING("Code Display Test Quiz already exists. Skipping creation.")
            )
            return

        # Create the test questions
        test_questions = [
            {
                "text": "What does the <code>print()</code> function do in Python?",
                "options": [
                    "Outputs text to the console",
                    "Creates a printable document",
                    "Imports a Python module",
                    "Defines a new function"
                ],
                "answerIndex": 1,  # 1-based index
            },
            {
                "text": "Which HTML element is used to define inline code?",
                "options": [
                    "The <code>&lt;pre&gt;</code> element",
                    "The <code>&lt;code&gt;</code> element",
                    "The <code>&lt;script&gt;</code> element",
                    "The <code>&lt;span class=\"code\"&gt;</code> element"
                ],
                "answerIndex": 2,  # 1-based index
            },
            {
                "text": "What is wrong with this Python code?",
                "options": [
                    "<code>for i in range(10): print(i) # This code works properly and follows PEP 8 guidelines, so there's nothing wrong with it.</code>",
                    "<code>for i in range(10) print(i) # Missing colon after the range definition</code>",
                    "<code>for i in range[10]: print(i) # Using square brackets instead of parentheses</code>",
                    "<code>for(i = 0; i < 10; i++) { console.log(i); } # This is JavaScript syntax, not Python</code>"
                ],
                "answerIndex": 2,  # 1-based index
            },
            {
                "text": "What is the correct way to define a Python function that adds two numbers?",
                "options": [
                    "<pre><code>def add_numbers(a, b):\n    return a + b</code></pre>",
                    "<pre><code>function add_numbers(a, b) {\n    return a + b;\n}</code></pre>",
                    "<pre><code>def add_numbers(a, b)\n    return a + b</code></pre>",
                    "<pre><code>add_numbers = lambda a, b: a + b</code></pre>"
                ],
                "answerIndex": 1,  # 1-based index
            },
            {
                "text": "What will <code>len(\"Hello, World!\")</code> return in Python?",
                "options": [
                    "<code>12</code>",
                    "<code>13</code>",
                    "<code>11</code>",
                    "<code>14</code>"
                ],
                "answerIndex": 2,  # 1-based index
            },
            {
                "text": "Which JavaScript method is used to add a new element at the end of an array?",
                "options": [
                    "<code>array.append(element)</code>",
                    "<code>array.push(element)</code>",
                    "<code>array.add(element)</code>",
                    "<code>array[array.length] = element</code>"
                ],
                "answerIndex": 2,  # 1-based index
            },
            {
                "text": "Which code snippet correctly handles exceptions in Python?",
                "options": [
                    "<pre><code>try:\n    result = 10 / 0\nexcept ZeroDivisionError:\n    print(\"Cannot divide by zero\")</code></pre>",
                    "<pre><code>try {\n    result = 10 / 0;\n} catch (ZeroDivisionError) {\n    console.log(\"Cannot divide by zero\");\n}</code></pre>",
                    "<pre><code>begin\n    result = 10 / 0\nrescue ZeroDivisionError\n    puts \"Cannot divide by zero\"\nend</code></pre>",
                    "<pre><code>if (10 / 0 == error) {\n    print(\"Cannot divide by zero\");\n}</code></pre>"
                ],
                "answerIndex": 1,  # 1-based index
            },
            {
                "text": "In HTML, which tag is used for creating a hyperlink?",
                "options": [
                    "The <code>&lt;a href=\"url\"&gt;link text&lt;/a&gt;</code> tag",
                    "The <code>&lt;link href=\"url\"&gt;link text&lt;/link&gt;</code> tag",
                    "The <code>&lt;url href=\"url\"&gt;link text&lt;/url&gt;</code> tag",
                    "The <code>&lt;hyperlink href=\"url\"&gt;link text&lt;/hyperlink&gt;</code> tag"
                ],
                "answerIndex": 1,  # 1-based index
            }
        ]

        try:
            # Create a topic for the test quiz
            topic, created = Topic.objects.get_or_create(
                name="Code Display Testing",
                defaults={"description": "Questions for testing code element display"}
            )

            # Create the quiz with the test questions
            quiz = quiz_bank_to_models(
                test_questions, 
                "Code Display Test Quiz", 
                "Code Display Testing"
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created quiz "{quiz.title}" with {quiz.question_count()} questions'
                )
            )

        except ValidationError as e:
            self.stderr.write(self.style.ERROR(f"Validation error: {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating test quiz: {str(e)}"))
