# src/pages/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError

# Import the Quiz model from the other app
# Use a try-except block for robustness, although direct import is usually fine
# if apps are correctly installed.
try:
    from multi_choice_quiz.models import Quiz
except ImportError:
    # This fallback is unlikely to be fully functional but prevents server startup errors
    # if the app structure is temporarily broken during development.
    # A better approach is ensuring apps are correctly installed and configured.
    Quiz = None
    print(
        "WARNING: Could not import Quiz model from multi_choice_quiz. Ensure app is installed."
    )


User = get_user_model()


class SystemCategory(models.Model):
    """
    Represents a public, admin-managed category for organizing quizzes.
    e.g., "History", "Science - Biology", "Programming - Python".
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The display name of the category.",
    )
    slug = models.SlugField(
        max_length=110,  # Slightly longer than name to accommodate potential suffixes
        unique=True,
        blank=True,  # Allow blank initially, will be auto-populated
        help_text="A unique slug for URLs, typically auto-generated from the name.",
    )
    description = models.TextField(
        blank=True, help_text="A brief description of the category (optional)."
    )
    quizzes = models.ManyToManyField(
        "multi_choice_quiz.Quiz",  # Use string notation to avoid circular import issues
        related_name="system_categories",
        blank=True,  # A category might exist before quizzes are added
        help_text="Quizzes belonging to this public category.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "System Category"
        verbose_name_plural = "System Categories"

    def __str__(self):
        return self.name

    def clean(self):
        """Ensure Quiz model was imported."""
        if Quiz is None:
            raise ValidationError(
                "Cannot validate SystemCategory: Quiz model not found. Check multi_choice_quiz app installation."
            )
        super().clean()

    def save(self, *args, **kwargs):
        """Auto-populates the slug field if it's blank."""
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness if slug already exists
            original_slug = self.slug
            counter = 1
            while (
                SystemCategory.objects.filter(slug=self.slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)


class UserCollection(models.Model):
    """
    Represents a private, user-created collection for organizing quizzes.
    e.g., "My Python Study Set", "Review for Midterm", "Weak Areas - Networking".
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # If user is deleted, their collections are too
        related_name="user_collections",
        help_text="The user who owns this collection.",
    )
    name = models.CharField(
        max_length=100, help_text="The name of the user's private collection."
    )
    description = models.TextField(
        blank=True, help_text="A brief description of the collection (optional)."
    )
    quizzes = models.ManyToManyField(
        "multi_choice_quiz.Quiz",  # Use string notation
        related_name="user_collections",
        blank=True,  # A collection might be created before adding quizzes
        help_text="Quizzes the user has added to this collection.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensure a user cannot have two collections with the same name
        unique_together = [["user", "name"]]
        ordering = ["user", "name"]
        verbose_name = "User Collection"
        verbose_name_plural = "User Collections"

    def __str__(self):
        return f"{self.user.username}'s Collection: {self.name}"

    def clean(self):
        """Ensure Quiz model was imported."""
        if Quiz is None:
            raise ValidationError(
                "Cannot validate UserCollection: Quiz model not found. Check multi_choice_quiz app installation."
            )
        super().clean()


# --- Verification Steps ---
# 1. Replace the content of `src/pages/models.py` with the code above.
# 2. Run `python manage.py makemigrations pages`
# 3. Run `python manage.py migrate`
# 4. Run `python manage.py check` to ensure there are no model issues.
