from django.db import models


class Topic(models.Model):
    """Model representing a topic or category for quiz questions."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Topic"
        verbose_name_plural = "Topics"


class Quiz(models.Model):
    """Model representing a quiz containing multiple questions."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    topics = models.ManyToManyField(Topic, related_name="quizzes", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def question_count(self):
        """Return the number of questions in this quiz."""
        return self.questions.count()

    def get_topics_display(self):
        """Return a comma-separated list of topic names."""
        return ", ".join(topic.name for topic in self.topics.all())

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"


class Question(models.Model):
    """Model representing a quiz question."""

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    text = models.TextField()
    chapter_no = models.CharField(max_length=20, blank=True)
    position = models.PositiveIntegerField(
        default=0, help_text="Position of this question within the quiz"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text

    def correct_option(self):
        """Return the correct option for this question."""
        try:
            return self.options.get(is_correct=True)
        except Option.DoesNotExist:
            return None
        except Option.MultipleObjectsReturned:
            # In case multiple options are marked as correct, return the first one
            return self.options.filter(is_correct=True).first()

    def correct_option_index(self):
        """
        Return the index of the correct option (0-based for JavaScript).
        This handles the conversion from database (1-based) to frontend (0-based).
        """
        correct = self.correct_option()
        if correct:
            return correct.position - 1  # Convert to 0-based for JS
        return None

    def options_list(self):
        """Return a list of option texts, ordered by position."""
        return list(self.options.order_by("position").values_list("text", flat=True))

    def to_dict(self):
        """
        Convert question to dictionary format expected by the frontend.
        This handles data transformation for the Alpine.js component.
        """
        return {
            "id": self.id,
            "text": self.text,
            "options": self.options_list(),
            "answerIndex": self.correct_option_index(),
        }

    class Meta:
        ordering = ["quiz", "position"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"


class Option(models.Model):
    """Model representing an answer option for a question."""

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.TextField()
    position = models.PositiveIntegerField(
        default=0, help_text="Position of this option (1-based)"
    )
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.text[:30]}... (Correct: {self.is_correct})"
            if len(self.text) > 30
            else f"{self.text} (Correct: {self.is_correct})"
        )

    class Meta:
        ordering = ["question", "position"]
        verbose_name = "Option"
        verbose_name_plural = "Options"
        # Ensure each option has a unique position within a question
        unique_together = ["question", "position"]
