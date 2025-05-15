# src/pages/tests/collections_mgmt/test_phase10_verification.py

from django.test import TestCase, Client
from django.urls import reverse, reverse_lazy  # Add reverse_lazy if needed
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.http import urlencode  # Import urlencode

from pages.models import UserCollection
from multi_choice_quiz.models import Quiz, Question
from multi_choice_quiz.tests.test_logging import setup_test_logging

logger = setup_test_logging(__name__, "pages_phase10_verification")
User = get_user_model()


class CollectionManagementVerificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        logger.info("Setting up test data for Phase 10 Verification")
        cls.user1 = User.objects.create_user(
            username="coll_user1", password="password123", email="user1@example.com"
        )
        cls.user2 = User.objects.create_user(
            username="coll_user2", password="password123", email="user2@example.com"
        )

        # Ensure quiz IDs are stable and known for tests
        # Using explicit IDs can help if tests rely on specific quiz IDs.
        # However, if they are just being created, relying on cls.quizX.id is usually fine.
        cls.quiz1, _ = Quiz.objects.get_or_create(
            id=1, defaults={"title": "Collection Test Quiz 1", "is_active": True}
        )
        if not cls.quiz1.questions.exists():
            Question.objects.create(quiz=cls.quiz1, text="Q1 from CTQ1")

        cls.quiz2, _ = Quiz.objects.get_or_create(
            id=2, defaults={"title": "Collection Test Quiz 2", "is_active": True}
        )
        if not cls.quiz2.questions.exists():
            Question.objects.create(quiz=cls.quiz2, text="Q1 from CTQ2")

        cls.quiz3, _ = Quiz.objects.get_or_create(
            id=3, defaults={"title": "Collection Test Quiz 3", "is_active": True}
        )
        if not cls.quiz3.questions.exists():
            Question.objects.create(quiz=cls.quiz3, text="Q1 from CTQ3")

        # URLs
        cls.profile_url = reverse("pages:profile")
        cls.create_collection_url = reverse("pages:create_collection")
        cls.quizzes_list_url = reverse("pages:quizzes")
        cls.home_url = reverse("pages:home")  # Added for consistency

        # Collections for user1
        cls.collection1_user1 = UserCollection.objects.create(
            user=cls.user1, name="User1 Alpha Collection"
        )
        cls.collection1_user1.quizzes.add(cls.quiz1)

        cls.collection2_user1 = UserCollection.objects.create(
            user=cls.user1, name="User1 Beta Collection (Empty)"
        )

        # Collection for user2 (for permission tests)
        cls.collection1_user2 = UserCollection.objects.create(
            user=cls.user2, name="User2 Gamma Collection"
        )
        cls.collection1_user2.quizzes.add(cls.quiz2)

    def setUp(self):
        self.client = Client()
        self.client.login(username="coll_user1", password="password123")
        logger.debug(
            f"Client logged in as {self.user1.username} for test: {self._testMethodName}"
        )

    # --- Create Collection Tests ---
    def test_create_collection_page_loads_get(self):
        logger.info("Testing GET on create_collection page")
        response = self.client.get(self.create_collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/create_collection.html")
        self.assertIn("form", response.context)

    def test_create_collection_successful_post(self):
        logger.info("Testing successful POST to create_collection")
        collection_name = "My New Test Collection"
        collection_description = "A description for it."
        initial_coll_count = UserCollection.objects.filter(user=self.user1).count()

        response = self.client.post(
            self.create_collection_url,
            {"name": collection_name, "description": collection_description},
        )

        self.assertEqual(response.status_code, 302, "Expected redirect on success")
        self.assertRedirects(response, self.profile_url)

        self.assertEqual(
            UserCollection.objects.filter(user=self.user1).count(),
            initial_coll_count + 1,
        )
        new_collection = UserCollection.objects.get(
            user=self.user1, name=collection_name
        )
        self.assertEqual(new_collection.description, collection_description)

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                f"Collection '{collection_name}' created successfully!" in str(m)
                for m in messages_list
            )
        )

    def test_create_collection_duplicate_name_for_same_user_fails(self):
        logger.info("Testing duplicate collection name for same user")
        existing_name = self.collection1_user1.name

        response = self.client.post(
            self.create_collection_url,
            {"name": existing_name, "description": "Trying to duplicate"},
        )
        self.assertEqual(response.status_code, 200, "Should re-render form with error")
        self.assertTemplateUsed(response, "pages/create_collection.html")
        self.assertContains(response, "You already have a collection with this name")

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "collection name already exists" in str(m).lower()
                for m in messages_list
            )
        )

    def test_select_collection_for_quiz_page_loads(self):
        logger.info(
            f"Testing select_collection_for_quiz page for quiz ID {self.quiz3.id}"
        )
        select_url = reverse("pages:select_collection_for_quiz", args=[self.quiz3.id])
        response = self.client.get(select_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/select_collection_for_quiz.html")
        self.assertEqual(response.context["quiz"], self.quiz3)
        self.assertIn(self.collection1_user1, response.context["collections"])
        self.assertIn(self.collection2_user1, response.context["collections"])
        self.assertContains(response, self.collection1_user1.name)
        self.assertContains(response, self.collection2_user1.name)

    def test_add_quiz_to_selected_collection_successful_post(self):
        logger.info(
            f"Testing adding quiz {self.quiz3.id} to collection {self.collection2_user1.id}"
        )
        self.assertNotIn(self.quiz3, self.collection2_user1.quizzes.all())

        add_url = reverse(
            "pages:add_quiz_to_selected_collection",
            args=[self.quiz3.id, self.collection2_user1.id],
        )
        response = self.client.post(add_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)

        self.collection2_user1.refresh_from_db()
        self.assertIn(self.quiz3, self.collection2_user1.quizzes.all())

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                f"Quiz '{self.quiz3.title}' added to collection '{self.collection2_user1.name}'"
                in str(m)
                for m in messages_list
            )
        )

    def test_add_quiz_already_in_collection_shows_info(self):
        logger.info(
            f"Testing adding quiz {self.quiz1.id} (already in) to collection {self.collection1_user1.id}"
        )
        self.assertIn(self.quiz1, self.collection1_user1.quizzes.all())

        add_url = reverse(
            "pages:add_quiz_to_selected_collection",
            args=[self.quiz1.id, self.collection1_user1.id],
        )
        response = self.client.post(add_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                f"Quiz '{self.quiz1.title}' is already in collection '{self.collection1_user1.name}'"
                in str(m)
                for m in messages_list
            )
        )

    def test_remove_quiz_from_collection_on_profile_successful_post(self):
        logger.info(
            f"Testing removing quiz {self.quiz1.id} from collection {self.collection1_user1.id}"
        )
        self.assertIn(self.quiz1, self.collection1_user1.quizzes.all())

        remove_url = reverse(
            "pages:remove_quiz_from_collection",
            args=[self.collection1_user1.id, self.quiz1.id],
        )
        response = self.client.post(remove_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)

        self.collection1_user1.refresh_from_db()
        self.assertNotIn(self.quiz1, self.collection1_user1.quizzes.all())

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                f"Quiz '{self.quiz1.title}' removed from collection '{self.collection1_user1.name}'"
                in str(m)
                for m in messages_list
            )
        )

    def test_remove_quiz_from_collection_permission_denied_for_other_user(self):
        logger.info(
            f"Testing permission denied for removing quiz {self.quiz2.id} from other user's collection {self.collection1_user2.id}"
        )
        remove_url = reverse(
            "pages:remove_quiz_from_collection",
            args=[self.collection1_user2.id, self.quiz2.id],
        )
        response = self.client.post(remove_url)

        self.assertEqual(response.status_code, 404)
        self.collection1_user2.refresh_from_db()
        self.assertIn(self.quiz2, self.collection1_user2.quizzes.all())

    def test_add_to_collection_button_on_quiz_pages_for_auth_user(self):
        logger.info(
            "Testing 'Add to Collection' button visibility for authenticated user"
        )

        response_quizzes = self.client.get(self.quizzes_list_url)
        self.assertEqual(response_quizzes.status_code, 200)

        # --- START MODIFIED ASSERTION for /quizzes/ page ---
        base_add_link_quiz1 = reverse(
            "pages:select_collection_for_quiz", args=[self.quiz1.id]
        )
        # We expect the href to START WITH this base_add_link_quiz1 and include "?next="
        self.assertContains(
            response_quizzes,
            f'href="{base_add_link_quiz1}?next=',
            msg_prefix="Quizzes page missing add link for quiz1 (or next param missing)",
        )
        # --- END MODIFIED ASSERTION ---

        response_home = self.client.get(self.home_url)
        self.assertEqual(response_home.status_code, 200)
        # For the home page, it's harder to predict which quiz will be featured and thus its exact ID.
        # The original assertion `self.assertContains(response_home, 'title="Add to Collection"')`
        # is good enough if at least one featured quiz makes it to the template.
        # We need to ensure that the setUpTestData creates quizzes that will be featured.
        # If Quiz.objects.all() are listed, then we can check one of them:
        # For quiz1 (ID=1):
        base_add_link_home_quiz1 = reverse(
            "pages:select_collection_for_quiz", args=[self.quiz1.id]
        )
        # This check assumes quiz1 will be rendered on the homepage. If not, it might fail.
        # A more robust check if homepage content is dynamic:
        # self.assertRegex(response_home.content.decode(), r'href="/quiz/\d+/add-to-collection/\?next=')
        # For now, let's keep the title check as it's less likely to break due to quiz ID ordering on home page.
        self.assertContains(
            response_home,
            'title="Add to Collection"',
            count=None,
            msg_prefix="Homepage missing 'Add to Collection' button pattern",
        )

    def test_add_to_collection_button_not_on_quiz_pages_for_anonymous_user(self):
        self.client.logout()
        logger.info("Testing 'Add to Collection' button absence for anonymous user")

        response_quizzes = self.client.get(self.quizzes_list_url)
        self.assertEqual(response_quizzes.status_code, 200)
        expected_add_link_quiz1_base = reverse(
            "pages:select_collection_for_quiz", args=[self.quiz1.id]
        )
        self.assertNotContains(
            response_quizzes, f'href="{expected_add_link_quiz1_base}"'
        )  # Check base part
        self.assertNotContains(response_quizzes, 'title="Add to Collection"')

        response_home = self.client.get(self.home_url)
        self.assertEqual(response_home.status_code, 200)
        self.assertNotContains(response_home, 'title="Add to Collection"')

    def test_select_collection_redirects_to_create_if_user_has_no_collections(self):
        self.client.login(username="coll_user2", password="password123")
        UserCollection.objects.filter(user=self.user2).delete()
        self.assertEqual(UserCollection.objects.filter(user=self.user2).count(), 0)
        logger.info(f"User {self.user2.username} now has no collections.")

        select_url = reverse("pages:select_collection_for_quiz", args=[self.quiz3.id])
        response = self.client.get(select_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pages:create_collection"))

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(
            any("You don't have any collections yet." in str(m) for m in messages_list)
        )
