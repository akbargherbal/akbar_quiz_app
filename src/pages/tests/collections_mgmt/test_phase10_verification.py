# src/pages/tests/collections_mgmt/test_phase10_verification.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages

from pages.models import UserCollection
from multi_choice_quiz.models import Quiz, Question
from multi_choice_quiz.tests.test_logging import setup_test_logging # Re-use existing

logger = setup_test_logging(__name__, "pages_phase10_verification") # Log under 'pages'
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

        cls.quiz1 = Quiz.objects.create(title="Collection Test Quiz 1", is_active=True)
        Question.objects.create(quiz=cls.quiz1, text="Q1 from CTQ1")
        cls.quiz2 = Quiz.objects.create(title="Collection Test Quiz 2", is_active=True)
        Question.objects.create(quiz=cls.quiz2, text="Q1 from CTQ2")
        cls.quiz3 = Quiz.objects.create(title="Collection Test Quiz 3", is_active=True) # For adding later
        Question.objects.create(quiz=cls.quiz3, text="Q1 from CTQ3")


        # URLs
        cls.profile_url = reverse("pages:profile")
        cls.create_collection_url = reverse("pages:create_collection")
        cls.quizzes_list_url = reverse("pages:quizzes") # For "Add to Collection" button presence

        # Collections for user1
        cls.collection1_user1 = UserCollection.objects.create(user=cls.user1, name="User1 Alpha Collection")
        cls.collection1_user1.quizzes.add(cls.quiz1)

        cls.collection2_user1 = UserCollection.objects.create(user=cls.user1, name="User1 Beta Collection (Empty)")

        # Collection for user2 (for permission tests)
        cls.collection1_user2 = UserCollection.objects.create(user=cls.user2, name="User2 Gamma Collection")
        cls.collection1_user2.quizzes.add(cls.quiz2)

    def setUp(self):
        self.client = Client()
        # Log in user1 by default for most tests
        self.client.login(username="coll_user1", password="password123")
        logger.debug(f"Client logged in as {self.user1.username} for test: {self._testMethodName}")

    # --- Create Collection Tests ---
    def test_create_collection_page_loads_get(self):
        """Test GET request to create_collection page loads form."""
        logger.info("Testing GET on create_collection page")
        response = self.client.get(self.create_collection_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/create_collection.html")
        self.assertIn("form", response.context)

    def test_create_collection_successful_post(self):
        """Test POSTing valid data creates a collection and redirects."""
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
        
        self.assertEqual(UserCollection.objects.filter(user=self.user1).count(), initial_coll_count + 1)
        new_collection = UserCollection.objects.get(user=self.user1, name=collection_name)
        self.assertEqual(new_collection.description, collection_description)

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any(f"Collection '{collection_name}' created successfully!" in str(m) for m in messages_list))

    def test_create_collection_duplicate_name_for_same_user_fails(self):
        """Test POSTing a duplicate collection name for the same user shows an error."""
        logger.info("Testing duplicate collection name for same user")
        existing_name = self.collection1_user1.name # "User1 Alpha Collection"
        
        response = self.client.post(
            self.create_collection_url,
            {"name": existing_name, "description": "Trying to duplicate"},
        )
        self.assertEqual(response.status_code, 200, "Should re-render form with error")
        self.assertTemplateUsed(response, "pages/create_collection.html")
        self.assertContains(response, "You already have a collection with this name") # Error message from form's clean or view
        
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any("collection name already exists" in str(m).lower() for m in messages_list))


    # --- Add Quiz to Collection (from public list flow) ---
    def test_select_collection_for_quiz_page_loads(self):
        """Test the select_collection_for_quiz page loads with user's collections."""
        logger.info(f"Testing select_collection_for_quiz page for quiz ID {self.quiz3.id}")
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
        """Test POST to add_quiz_to_selected_collection adds quiz."""
        logger.info(f"Testing adding quiz {self.quiz3.id} to collection {self.collection2_user1.id}")
        self.assertNotIn(self.quiz3, self.collection2_user1.quizzes.all())

        add_url = reverse("pages:add_quiz_to_selected_collection", args=[self.quiz3.id, self.collection2_user1.id])
        response = self.client.post(add_url) # POST request

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        
        self.collection2_user1.refresh_from_db()
        self.assertIn(self.quiz3, self.collection2_user1.quizzes.all())
        
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any(f"Quiz '{self.quiz3.title}' added to collection '{self.collection2_user1.name}'" in str(m) for m in messages_list))

    def test_add_quiz_already_in_collection_shows_info(self):
        """Test adding a quiz that's already in the collection shows an info message."""
        logger.info(f"Testing adding quiz {self.quiz1.id} (already in) to collection {self.collection1_user1.id}")
        self.assertIn(self.quiz1, self.collection1_user1.quizzes.all()) # Pre-condition

        add_url = reverse("pages:add_quiz_to_selected_collection", args=[self.quiz1.id, self.collection1_user1.id])
        response = self.client.post(add_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any(f"Quiz '{self.quiz1.title}' is already in collection '{self.collection1_user1.name}'" in str(m) for m in messages_list))


    # --- Remove Quiz from Collection (from profile page) ---
    def test_remove_quiz_from_collection_on_profile_successful_post(self):
        """Test POST to remove_quiz_from_collection removes the quiz."""
        logger.info(f"Testing removing quiz {self.quiz1.id} from collection {self.collection1_user1.id}")
        self.assertIn(self.quiz1, self.collection1_user1.quizzes.all()) # Pre-condition

        remove_url = reverse("pages:remove_quiz_from_collection", args=[self.collection1_user1.id, self.quiz1.id])
        response = self.client.post(remove_url) # POST request

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)

        self.collection1_user1.refresh_from_db()
        self.assertNotIn(self.quiz1, self.collection1_user1.quizzes.all())

        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any(f"Quiz '{self.quiz1.title}' removed from collection '{self.collection1_user1.name}'" in str(m) for m in messages_list))

    def test_remove_quiz_from_collection_permission_denied_for_other_user(self):
        """Test user cannot remove quiz from another user's collection."""
        logger.info(f"Testing permission denied for removing quiz {self.quiz2.id} from other user's collection {self.collection1_user2.id}")
        # self.user1 is logged in
        remove_url = reverse("pages:remove_quiz_from_collection", args=[self.collection1_user2.id, self.quiz2.id])
        response = self.client.post(remove_url)
        
        self.assertEqual(response.status_code, 404) # View raises 404 if collection not found for user
        self.collection1_user2.refresh_from_db()
        self.assertIn(self.quiz2, self.collection1_user2.quizzes.all()) # Quiz should still be there

    def test_add_to_collection_button_on_quiz_pages_for_auth_user(self):
        """Test 'Add to Collection' button appears on quiz list pages for authenticated users."""
        logger.info("Testing 'Add to Collection' button visibility for authenticated user")
        
        # Check on general quizzes page
        response_quizzes = self.client.get(self.quizzes_list_url)
        self.assertEqual(response_quizzes.status_code, 200)
        # Look for the link structure that goes to select_collection_for_quiz
        # Example for quiz1
        expected_add_link_quiz1 = reverse("pages:select_collection_for_quiz", args=[self.quiz1.id])
        self.assertContains(response_quizzes, f'href="{expected_add_link_quiz1}"', msg_prefix="Quizzes page missing add link for quiz1")

        # Check on home page (featured quizzes)
        response_home = self.client.get(reverse("pages:home"))
        self.assertEqual(response_home.status_code, 200)
        # Assuming quiz3 might be featured (or any quiz that would be on home)
        # We need to ensure at least one quiz is featured for this check
        # For simplicity, let's just check if the general pattern of the link exists for *any* quiz shown
        self.assertContains(response_home, 'title="Add to Collection"', count=None, msg_prefix="Homepage missing 'Add to Collection' button pattern")


    def test_add_to_collection_button_not_on_quiz_pages_for_anonymous_user(self):
        """Test 'Add to Collection' button does NOT appear for anonymous users."""
        self.client.logout()
        logger.info("Testing 'Add to Collection' button absence for anonymous user")

        response_quizzes = self.client.get(self.quizzes_list_url)
        self.assertEqual(response_quizzes.status_code, 200)
        expected_add_link_quiz1 = reverse("pages:select_collection_for_quiz", args=[self.quiz1.id])
        self.assertNotContains(response_quizzes, f'href="{expected_add_link_quiz1}"')
        self.assertNotContains(response_quizzes, 'title="Add to Collection"')
        
        response_home = self.client.get(reverse("pages:home"))
        self.assertEqual(response_home.status_code, 200)
        self.assertNotContains(response_home, 'title="Add to Collection"')


    def test_select_collection_redirects_to_create_if_user_has_no_collections(self):
        """Test user is redirected to create collection if they have none when trying to add a quiz."""
        # Log in as user2 who currently has one collection (collection1_user2).
        # We'll delete it for this test case.
        self.client.login(username="coll_user2", password="password123")
        UserCollection.objects.filter(user=self.user2).delete()
        self.assertEqual(UserCollection.objects.filter(user=self.user2).count(), 0)
        logger.info(f"User {self.user2.username} now has no collections.")

        select_url = reverse("pages:select_collection_for_quiz", args=[self.quiz3.id])
        response = self.client.get(select_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("pages:create_collection"))
        
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any("You don't have any collections yet." in str(m) for m in messages_list))