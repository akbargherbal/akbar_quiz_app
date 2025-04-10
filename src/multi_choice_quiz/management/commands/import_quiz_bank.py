# src/multi_choice_quiz/management/commands/import_quiz_bank.py

import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
import logging

from multi_choice_quiz.utils import import_from_dataframe, curate_data
from multi_choice_quiz.models import Quiz, Topic


class Command(BaseCommand):
    help = "Import quiz data from a quiz bank file (CSV, Excel)"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path", type=str, help="Path to the quiz bank file (CSV or Excel)"
        )
        parser.add_argument(
            "--quiz-title",
            type=str,
            default=None,
            help="Title for the imported quiz (defaults to chapter title from data)",
        )
        parser.add_argument(
            "--topic", type=str, help="Topic to associate with the imported questions"
        )
        parser.add_argument(
            "--max-questions",
            type=int,
            help="Maximum number of questions to import (will sample if dataset is larger)",
        )
        parser.add_argument(
            "--split-by-topic",
            action="store_true",
            help="Create separate quizzes for each topic in the data (requires a topic column)",
        )
        parser.add_argument(
            "--topic-column",
            type=str,
            default="topic",
            help="Column name containing topic information (use with --split-by-topic)",
        )
        parser.add_argument(
            "--chapter-column",
            type=str,
            default="chapter_no",
            help="Column name containing chapter information",
        )
        parser.add_argument(
            "--chapter-title-column",
            type=str,
            default="chapter_title",
            help="Column name containing chapter title information",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]
        provided_quiz_title = options["quiz_title"]
        topic_name = options["topic"]
        max_questions = options["max_questions"]
        split_by_topic = options["split_by_topic"]
        topic_column = options["topic_column"]
        chapter_column = options["chapter_column"]
        chapter_title_column = options["chapter_title_column"]

        # Configure logging
        logger = logging.getLogger(__name__)

        # Validate file path
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Load the data based on file extension
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            self.stdout.write(self.style.NOTICE(f"Loading data from {file_path}"))

            if file_ext == ".csv":
                df = pd.read_csv(file_path)
            elif file_ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            elif file_ext in [".pkl", ".pickle"]:
                df = pd.read_pickle(file_path)
            else:
                self.stderr.write(
                    self.style.ERROR(f"Unsupported file format: {file_ext}")
                )
                return

            self.stdout.write(
                self.style.SUCCESS(f"Loaded {len(df)} rows from {file_path}")
            )

            # Check if DataFrame has any data
            if len(df) == 0:
                self.stderr.write(self.style.ERROR("File contains no data"))
                return

            # Map chapter column if it exists
            if chapter_column in df.columns and chapter_column != "chapter_no":
                df["chapter_no"] = df[chapter_column]

            # Get chapter title if available
            chapter_title = None
            if chapter_title_column in df.columns:
                # Get the most common chapter title
                chapter_title = df[chapter_title_column].value_counts().index[0]
                self.stdout.write(
                    self.style.NOTICE(f"Found chapter title: {chapter_title}")
                )

            # Process the data based on the split option
            if split_by_topic and topic_column in df.columns:
                # Create separate quizzes for each topic
                self._import_by_topic(
                    df, topic_column, chapter_title_column, max_questions
                )
            else:
                # Create a single quiz with all questions
                # Use provided title, chapter title, or default
                quiz_title = provided_quiz_title
                if not quiz_title and chapter_title:
                    quiz_title = chapter_title
                elif not quiz_title:
                    quiz_title = "Quiz Bank Import"

                # Use actual topic from data if available
                actual_topic = None
                if topic_column in df.columns and not topic_name:
                    # Get the most common topic
                    actual_topic = df[topic_column].value_counts().index[0]

                self._import_as_single_quiz(
                    df, quiz_title, topic_name or actual_topic, max_questions
                )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error importing quiz data: {str(e)}"))
            logger.exception("Error in import_quiz_bank command")

    def _import_as_single_quiz(self, df, quiz_title, topic_name, max_questions):
        """Import all data as a single quiz"""
        try:
            if max_questions and max_questions < len(df):
                self.stdout.write(
                    self.style.NOTICE(
                        f"Sampling {max_questions} questions from {len(df)} total"
                    )
                )

            # Use import_from_dataframe to create the quiz
            quiz = import_from_dataframe(
                df=df,
                quiz_title=quiz_title,
                topic_name=topic_name,
                sample_size=max_questions,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully imported quiz '{quiz.title}' with {quiz.question_count()} questions"
                )
            )

            # If the quiz has topics, log them
            if quiz.topics.exists():
                topic_names = ", ".join(t.name for t in quiz.topics.all())
                self.stdout.write(f"Quiz topics: {topic_names}")

        except ValidationError as e:
            self.stderr.write(self.style.ERROR(f"Validation error: {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating quiz: {str(e)}"))

    def _import_by_topic(self, df, topic_column, chapter_title_column, max_questions):
        """Import data split into multiple quizzes by topic"""
        # Get unique topics
        if topic_column not in df.columns:
            self.stderr.write(
                self.style.ERROR(f"Topic column '{topic_column}' not found in data")
            )
            return

        topics = df[topic_column].dropna().unique()

        if len(topics) == 0:
            self.stderr.write(self.style.ERROR("No topics found in data"))
            return

        self.stdout.write(self.style.NOTICE(f"Found {len(topics)} unique topics"))

        # Create a quiz for each topic
        for topic in topics:
            self.stdout.write(f"Processing topic: {topic}")

            # Filter data for this topic
            topic_df = df[df[topic_column] == topic].copy()

            if len(topic_df) == 0:
                self.stdout.write(
                    self.style.WARNING(f"No questions found for topic: {topic}")
                )
                continue

            # Determine questions per topic
            topic_max = max_questions
            if topic_max and topic_max > len(topic_df):
                topic_max = None  # Use all available questions if less than max

            # Get chapter title if available
            chapter_title = None
            # Check for both upper and lowercase column names
            if chapter_title_column in topic_df.columns:
                # Get the most common chapter title for this topic
                chapter_title = topic_df[chapter_title_column].value_counts().index[0]
            elif "CHAPTER_TITLE" in topic_df.columns:  # Add this check
                # Get the most common chapter title for this topic
                chapter_title = topic_df["CHAPTER_TITLE"].value_counts().index[0]

            # Generate quiz title based on topic and chapter title
            if chapter_title:
                quiz_title = f"{chapter_title}: {topic} Quiz"
            else:
                quiz_title = f"Quiz: {topic}"

            try:
                # Import this topic's questions
                quiz = import_from_dataframe(
                    df=topic_df,
                    quiz_title=quiz_title,
                    topic_name=topic,  # Use the topic value as the topic name
                    sample_size=topic_max,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created quiz '{quiz.title}' with {quiz.question_count()} questions"
                    )
                )

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Error creating quiz for topic '{topic}': {str(e)}"
                    )
                )
