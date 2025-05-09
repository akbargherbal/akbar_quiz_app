# src/pages/tests/test_models.py (Revised UserCollectionModelTests)

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.text import slugify

# Import models from the app being tested
from pages.models import SystemCategory, UserCollection

# Import models from related apps
from multi_choice_quiz.models import Quiz

# --- Replace existing logger setup with this ---
from multi_choice_quiz.tests.test_logging import (
    setup_test_logging,
)  # Reuse existing logger setup

logger = setup_test_logging(__name__, "pages")  # Log under 'pages' app
# --- End Replacement ---


User = get_user_model()


# --- SystemCategoryModelTests remains unchanged above ---
class SystemCategoryModelTests(TestCase):
    """Tests for the SystemCategory model."""

    @classmethod
    def setUpTestData(cls):
        # Create a quiz to associate later
        cls.quiz1 = Quiz.objects.create(title="Test Quiz for Category")

    def test_category_creation_and_str(self):
        """Test creating a category and its string representation."""
        category = SystemCategory.objects.create(
            name="Science Fiction", description="Quizzes about Sci-Fi."
        )
        self.assertEqual(category.name, "Science Fiction")
        self.assertEqual(category.description, "Quizzes about Sci-Fi.")
        self.assertEqual(str(category), "Science Fiction")
        logger.info(f"Successfully created category: {category}")

    def test_slug_auto_generation_on_create(self):
        """Test that the slug is auto-generated correctly when creating."""
        # Test with a simple name
        cat1 = SystemCategory.objects.create(name="Simple Name")
        self.assertEqual(cat1.slug, "simple-name")
        logger.info(f"Auto-generated slug for '{cat1.name}': {cat1.slug}")

        # Test with a name needing more slugify work
        cat2 = SystemCategory.objects.create(name="Quantum Physics 101!")
        self.assertEqual(cat2.slug, "quantum-physics-101")
        logger.info(f"Auto-generated slug for '{cat2.name}': {cat2.slug}")

    def test_slug_suffix_generation_on_save(self):
        """Test that slugs get suffixes if a collision *would* occur (even if name is different)."""
        # Create the first category
        cat1 = SystemCategory.objects.create(name="Collision Test")
        self.assertEqual(cat1.slug, "collision-test")

        # Create a *different* category whose name slugifies to the same thing
        cat2 = SystemCategory.objects.create(name="Collision Test!?")  # Different name
        self.assertEqual(cat2.slug, "collision-test-1")  # Should get suffix
        logger.info(
            f"Created categories with unique slugs from similar names: {cat1.slug}, {cat2.slug}"
        )

        # Create a third one
        cat3 = SystemCategory.objects.create(
            name="Collision Test..."
        )  # Different name again
        self.assertEqual(cat3.slug, "collision-test-2")  # Should get next suffix
        logger.info(f"Created third category with unique slug: {cat3.slug}")

    def test_name_uniqueness(self):
        """Test that the unique=True constraint on 'name' works."""
        name = "Unique Name Test"
        SystemCategory.objects.create(name=name)
        # Trying to create another with the same name should raise IntegrityError
        with self.assertRaises(IntegrityError):
            SystemCategory.objects.create(name=name)
        logger.info(f"Verified UNIQUE constraint failed for duplicate name '{name}'.")

    def test_quiz_m2m_relationship(self):
        """Test adding quizzes to a category."""
        category = SystemCategory.objects.create(name="History")
        self.assertEqual(category.quizzes.count(), 0)

        category.quizzes.add(self.quiz1)
        self.assertEqual(category.quizzes.count(), 1)
        self.assertEqual(category.quizzes.first(), self.quiz1)

        # Check reverse relationship
        self.assertEqual(self.quiz1.system_categories.count(), 1)
        self.assertEqual(self.quiz1.system_categories.first(), category)
        logger.info(f"Tested M2M relationship for SystemCategory '{category.name}'")


# --- START REVISED UserCollectionModelTests ---
class UserCollectionModelTests(TestCase):
    """Tests for the UserCollection model."""

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username="coll_user1", password="pw1")
        cls.user2 = User.objects.create_user(username="coll_user2", password="pw2")
        cls.quiz1 = Quiz.objects.create(title="Test Quiz for Collection 1")
        cls.quiz2 = Quiz.objects.create(title="Test Quiz for Collection 2")

    def test_collection_creation_and_str(self):
        """Test creating a collection and its string representation."""
        collection = UserCollection.objects.create(
            user=self.user1,
            name="My Study Set",
            description="Quizzes for the midterm.",
        )
        self.assertEqual(collection.user, self.user1)
        self.assertEqual(collection.name, "My Study Set")
        self.assertEqual(collection.description, "Quizzes for the midterm.")
        expected_str = f"{self.user1.username}'s Collection: My Study Set"
        self.assertEqual(str(collection), expected_str)
        logger.info(f"Successfully created collection: {collection}")

    def test_unique_together_constraint_same_user(self):  # <<< RENAMED TEST
        """Test that a user cannot have two collections with the same name."""
        collection_name = "Duplicate Name Test"
        UserCollection.objects.create(user=self.user1, name=collection_name)
        # Trying to create another with the same name for the same user should fail
        with self.assertRaises(IntegrityError):
            UserCollection.objects.create(user=self.user1, name=collection_name)
        logger.info(
            f"Verified unique_together constraint fails for same user, name='{collection_name}'."
        )

    def test_unique_together_constraint_different_user(self):  # <<< NEW TEST
        """Test that different users can have collections with the same name."""
        collection_name = "Shared Name Test"
        UserCollection.objects.create(user=self.user1, name=collection_name)
        # Creating with the same name for a *different* user should be fine
        try:
            UserCollection.objects.create(user=self.user2, name=collection_name)
        except IntegrityError:
            self.fail(
                "Should be able to create collection with same name for different user."
            )
        logger.info(
            f"Verified same collection name '{collection_name}' allowed for different users."
        )

    def test_quiz_m2m_relationship(self):
        """Test adding quizzes to a user collection."""
        collection = UserCollection.objects.create(user=self.user1, name="M2M Test")
        self.assertEqual(collection.quizzes.count(), 0)

        collection.quizzes.add(self.quiz1)
        self.assertEqual(collection.quizzes.count(), 1)
        self.assertEqual(collection.quizzes.first(), self.quiz1)

        collection.quizzes.add(self.quiz2)
        self.assertEqual(collection.quizzes.count(), 2)

        # Check reverse relationship
        self.assertEqual(self.quiz1.user_collections.count(), 1)
        self.assertEqual(self.quiz1.user_collections.first(), collection)
        logger.info(f"Tested M2M relationship for UserCollection '{collection.name}'")

    def test_cascade_delete_user(self):
        """Test that deleting a user cascades to delete their collections."""
        # Create a user specifically for this test to avoid conflicts
        user_to_delete = User.objects.create_user(username="deleteme", password="pw")
        collection = UserCollection.objects.create(
            user=user_to_delete, name="To Be Deleted"
        )
        collection_id = collection.id
        self.assertTrue(UserCollection.objects.filter(id=collection_id).exists())

        # Delete the user
        user_to_delete.delete()

        # Verify the collection associated with the user is also deleted
        self.assertFalse(UserCollection.objects.filter(id=collection_id).exists())
        logger.info("Verified cascade delete for UserCollection.")


# --- END REVISED UserCollectionModelTests ---
