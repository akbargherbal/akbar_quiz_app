# src/pages/tests/test_views.py

import re
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q, Exists, OuterRef

from multi_choice_quiz.models import Quiz, QuizAttempt, Question
from pages.models import UserCollection, SystemCategory
from multi_choice_quiz.tests.test_logging import setup_test_logging

logger = setup_test_logging(__name__, "pages")
User = get_user_model()


class PagesViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # --- Users ---
        cls.user_with_data = User.objects.create_user(
            username="profiletester",
            password="password123",
            email="profile@example.com",
        )
        cls.user_no_data = User.objects.create_user(
            username="nodataprofile", password="password123"
        )
        cls.user_for_ordering_tests = User.objects.create_user(
            username="ordering_tester", password="password123"
        )

        # --- System Categories ---
        cls.cat_tech = SystemCategory.objects.create(
            name="Technology", slug="technology"
        )
        cls.cat_hist = SystemCategory.objects.create(name="History", slug="history")
        cls.cat_sci = SystemCategory.objects.create(name="Science", slug="science")
        cls.cat_art = SystemCategory.objects.create(name="Art", slug="art")
        cls.cat_math = SystemCategory.objects.create(name="Math", slug="math")
        cls.cat_geo = SystemCategory.objects.create(name="Geography", slug="geo")

        # --- Quizzes - IMPORTANT: Define created_at with clear differences ---
        cls.quiz_t1 = Quiz.objects.create(
            title="Tech Quiz 1",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=10),
        )
        Question.objects.create(quiz=cls.quiz_t1, text="TQ1")
        cls.quiz_t2 = Quiz.objects.create(
            title="Tech Quiz 2",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=9),
        )
        Question.objects.create(quiz=cls.quiz_t2, text="TQ2")
        cls.quiz_t3 = Quiz.objects.create(
            title="Tech Quiz 3 (Newest Tech)",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=8),
        )
        Question.objects.create(quiz=cls.quiz_t3, text="TQ3")

        cls.quiz_h1 = Quiz.objects.create(
            title="History Quiz 1",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=7),
        )
        Question.objects.create(quiz=cls.quiz_h1, text="HQ1")

        cls.quiz_s1 = Quiz.objects.create(
            title="Science Quiz 1",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=6),
        )
        Question.objects.create(quiz=cls.quiz_s1, text="SQ1")
        cls.quiz_s2 = Quiz.objects.create(
            title="Science Quiz 2 (Newest Sci)",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=5),
        )
        Question.objects.create(quiz=cls.quiz_s2, text="SQ2")

        cls.quiz_m1 = Quiz.objects.create(
            title="Math Quiz 1",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=4),
        )
        Question.objects.create(quiz=cls.quiz_m1, text="MQ1")

        cls.quiz_g1 = Quiz.objects.create(
            title="Geography Quiz 1",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=3),
        )
        Question.objects.create(quiz=cls.quiz_g1, text="GQ1")

        cls.quiz_nocat = Quiz.objects.create(
            title="No Category Quiz (Newest Overall)",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=2),
        )
        Question.objects.create(quiz=cls.quiz_nocat, text="NoCatQ")

        # This was incorrectly creating a SystemCategory instead of a Quiz.
        # cls.quiz_art_no_q = SystemCategory.objects.create(name="Art Quiz No Questions", slug="art-quiz-no-questions")
        # Corrected:
        cls.quiz_a1_no_questions = Quiz.objects.create(
            title="Art Quiz 1 (No Qs)",
            is_active=True,
            created_at=timezone.now() - timezone.timedelta(days=20),
        )
        cls.quiz_a1_no_questions.system_categories.add(cls.cat_art)

        cls.quiz_inactive = Quiz.objects.create(
            title="Inactive Quiz",
            is_active=False,
            created_at=timezone.now() - timezone.timedelta(days=1),
        )
        Question.objects.create(quiz=cls.quiz_inactive, text="InactiveQ")
        cls.quiz_inactive.system_categories.add(cls.cat_sci)

        # Attempts for user_for_ordering_tests
        # Remove the 'created_at' argument here
        cls.user_for_ordering_tests_attempt1 = QuizAttempt.objects.create(
            user=cls.user_for_ordering_tests,
            quiz=cls.quiz_s1,
            score=1,
            total_questions=1,
            percentage=100,
        )
        cls.user_for_ordering_tests_attempt2 = QuizAttempt.objects.create(
            user=cls.user_for_ordering_tests,
            quiz=cls.quiz_g1,
            score=1,
            total_questions=1,
            percentage=100,
        )

        cls.quiz_t1.system_categories.add(cls.cat_tech)
        cls.quiz_t2.system_categories.add(cls.cat_tech)
        cls.quiz_t3.system_categories.add(cls.cat_tech)
        cls.quiz_h1.system_categories.add(cls.cat_hist)
        cls.quiz_s1.system_categories.add(cls.cat_sci)
        cls.quiz_s2.system_categories.add(cls.cat_sci)
        cls.quiz_m1.system_categories.add(cls.cat_math)
        cls.quiz_g1.system_categories.add(cls.cat_geo)

        cls.attempt1_user_with_data = QuizAttempt.objects.create(
            user=cls.user_with_data,
            quiz=cls.quiz_t1,
            score=8,
            total_questions=10,
            percentage=80.0,
            end_time=timezone.now()
            - timezone.timedelta(days=1),  # end_time is fine to set
        )
        cls.attempt2_user_with_data = QuizAttempt.objects.create(
            user=cls.user_with_data,
            quiz=cls.quiz_h1,
            score=5,
            total_questions=5,
            percentage=100.0,
            end_time=timezone.now(),  # end_time is fine to set
        )

        cls.collection1 = UserCollection.objects.create(
            user=cls.user_with_data, name="Collection A"
        )
        cls.collection1.quizzes.add(cls.quiz_t1, cls.quiz_h1)
        cls.collection2 = UserCollection.objects.create(
            user=cls.user_with_data, name="Collection B (Empty)"
        )

        cls.nodata_user_collection = UserCollection.objects.create(
            user=cls.user_no_data, name="No Data User Coll"
        )

    def setUp(self):
        self.client = Client()

    # ... (rest of the test methods remain unchanged from the previous full file you provided) ...
    # Make sure all test methods from the previous (long) test_views.py file are included below this line.
    # I will just show a placeholder for brevity here.
    def test_home_page_loads(self):
        """Verify homepage loads and includes featured quizzes and popular categories (anonymous)."""
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")

        self.assertIn("featured_quizzes", response.context)
        featured_in_context = response.context["featured_quizzes"]
        self.assertEqual(len(featured_in_context), 3)

        expected_featured_titles_anon = [
            self.quiz_nocat.title,
            self.quiz_g1.title,
            self.quiz_m1.title,
        ]
        self.assertEqual(
            [q.title for q in featured_in_context], expected_featured_titles_anon
        )

        self.assertIn("popular_categories", response.context)
        popular = response.context["popular_categories"]

        expected_popular_cat_names = [
            "Technology",
            "Science",
            "Geography",
            "History",
            "Math",
        ]
        self.assertEqual(len(popular), 5)
        self.assertEqual([cat.name for cat in popular], expected_popular_cat_names)
        self.assertEqual(popular[0].num_active_quizzes, 3)
        self.assertEqual(popular[1].num_active_quizzes, 2)
        self.assertEqual(popular[2].num_active_quizzes, 1)
        self.assertEqual(popular[3].num_active_quizzes, 1)
        self.assertEqual(popular[4].num_active_quizzes, 1)

        content = response.content.decode()
        for title in expected_featured_titles_anon:
            self.assertIn(title, content)
        self.assertIn("Popular Categories", content)
        self.assertIn(self.cat_tech.name, content)
        self.assertIn(f">{popular[0].num_active_quizzes} quizs</p>", content)
        self.assertIn(f">{popular[1].num_active_quizzes} quizs</p>", content)
        self.assertIn(f">{popular[2].num_active_quizzes} quiz</p>", content)
        self.assertNotIn(self.cat_art.name, content)

    def test_home_page_featured_quizzes_authenticated_user(self):
        """Test featured quizzes for an authenticated user with some attempts."""
        self.client.login(username="ordering_tester", password="password123")
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        featured_in_context = response.context["featured_quizzes"]

        expected_featured_titles = [
            self.quiz_nocat.title,
            self.quiz_m1.title,
            self.quiz_s2.title,
        ]
        self.assertEqual(
            [q.title for q in featured_in_context], expected_featured_titles
        )

    def test_home_page_featured_quizzes_not_enough_unattempted(self):
        """Test featured quizzes when not enough unattempted quizzes are available for the user."""
        user_highly_active = User.objects.create_user(
            username="highly_active", password="password"
        )
        QuizAttempt.objects.create(
            user=user_highly_active,
            quiz=self.quiz_nocat,
            score=1,
            total_questions=1,
            percentage=100,
        )
        QuizAttempt.objects.create(
            user=user_highly_active,
            quiz=self.quiz_g1,
            score=1,
            total_questions=1,
            percentage=100,
        )

        self.client.login(username="highly_active", password="password")
        response = self.client.get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        featured_in_context = response.context["featured_quizzes"]

        expected_titles = [
            self.quiz_m1.title,  # Unattempted
            self.quiz_s2.title,  # Unattempted
            self.quiz_s1.title,  # Unattempted
        ]
        self.assertEqual([q.title for q in featured_in_context], expected_titles)

    def test_quizzes_page_loads_and_filters_by_category(self):
        """Test the quizzes page for anonymous user: count, pagination, filtering."""
        all_quizzes_url = reverse("pages:quizzes")
        response_all = self.client.get(all_quizzes_url)
        self.assertEqual(response_all.status_code, 200)
        self.assertTemplateUsed(response_all, "pages/quizzes.html")

        self.assertIn("categories", response_all.context)
        self.assertEqual(len(response_all.context["categories"]), 6)
        self.assertIsNone(response_all.context["selected_category"])

        quizzes_page = response_all.context["quizzes"]
        self.assertEqual(quizzes_page.paginator.count, 9)
        self.assertEqual(len(quizzes_page.object_list), 9)

        expected_titles_page1_anon = [
            self.quiz_nocat.title,
            self.quiz_g1.title,
            self.quiz_m1.title,
            self.quiz_s2.title,
            self.quiz_s1.title,
            self.quiz_h1.title,
            self.quiz_t3.title,
            self.quiz_t2.title,
            self.quiz_t1.title,
        ]
        self.assertEqual(
            [q.title for q in quizzes_page.object_list], expected_titles_page1_anon
        )

        tech_quizzes_url = f"{all_quizzes_url}?category={self.cat_tech.slug}"
        response_tech = self.client.get(tech_quizzes_url)
        self.assertEqual(response_tech.context["selected_category"], self.cat_tech)
        tech_quizzes_on_page = response_tech.context["quizzes"]
        self.assertEqual(tech_quizzes_on_page.paginator.count, 3)
        expected_tech_titles = [
            self.quiz_t3.title,
            self.quiz_t2.title,
            self.quiz_t1.title,
        ]
        self.assertEqual(
            [q.title for q in tech_quizzes_on_page.object_list], expected_tech_titles
        )

        art_quizzes_url = f"{all_quizzes_url}?category={self.cat_art.slug}"
        response_art = self.client.get(art_quizzes_url)
        self.assertEqual(response_art.context["selected_category"], self.cat_art)
        art_quizzes_on_page = response_art.context["quizzes"]
        self.assertEqual(art_quizzes_on_page.paginator.count, 0)
        self.assertIn("No quizzes found for category", response_art.content.decode())

    def test_quizzes_page_ordering_for_authenticated_user(self):
        """Test quiz ordering on the quizzes page for ordering_tester."""
        self.client.login(username="ordering_tester", password="password123")
        response = self.client.get(reverse("pages:quizzes"))
        self.assertEqual(response.status_code, 200)

        quizzes_on_page = response.context["quizzes"].object_list

        expected_ordered_titles_page1 = [
            self.quiz_nocat.title,  # Unattempted, -2d
            self.quiz_m1.title,  # Unattempted, -4d
            self.quiz_s2.title,  # Unattempted, -5d
            self.quiz_h1.title,  # Unattempted, -7d
            self.quiz_t3.title,  # Unattempted, -8d
            self.quiz_t2.title,  # Unattempted, -9d
            self.quiz_t1.title,  # Unattempted, -10d
            self.quiz_g1.title,  # Attempted,   -3d
            self.quiz_s1.title,  # Attempted,   -6d
        ]

        self.assertEqual(
            [q.title for q in quizzes_on_page], expected_ordered_titles_page1
        )

        for quiz_obj in quizzes_on_page:
            is_attempted_in_test_data = quiz_obj.title in [
                self.quiz_s1.title,
                self.quiz_g1.title,
            ]
            self.assertEqual(
                quiz_obj.has_attempted,
                is_attempted_in_test_data,
                f"Quiz {quiz_obj.title} has_attempted mismatch",
            )

    def test_about_page_loads(self):  # Duplicated from previous for brevity
        response = self.client.get(reverse("pages:about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/about.html")

    def test_login_page_loads(self):  # Duplicated
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_signup_page_loads(self):  # Duplicated
        response = self.client.get(reverse("pages:signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/signup.html")

    def test_profile_page_redirects_when_not_logged_in(self):  # Duplicated
        response = self.client.get(reverse("pages:profile"))
        self.assertEqual(response.status_code, 302)
        expected_redirect_url = f"{reverse('login')}?next={reverse('pages:profile')}"
        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )

    def test_profile_page_loads_when_logged_in(self):  # Duplicated
        login_successful = self.client.login(
            username="profiletester", password="password123"
        )
        self.assertTrue(login_successful, "Test user login failed")
        response = self.client.get(reverse("pages:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/profile.html")
        self.assertEqual(response.context["user"], self.user_with_data)

    def test_profile_page_context_with_data(self):  # Duplicated
        self.client.login(username="profiletester", password="password123")
        response = self.client.get(reverse("pages:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("quiz_attempts", response.context)
        attempts_in_context = response.context["quiz_attempts"]
        self.assertEqual(attempts_in_context.count(), 2)
        self.assertIn("user_collections", response.context)
        collections_in_context = response.context["user_collections"]
        self.assertEqual(collections_in_context.count(), 2)
        self.assertNotIn(self.nodata_user_collection, collections_in_context)
        self.assertIn("stats", response.context)
        stats_in_context = response.context["stats"]
        self.assertEqual(stats_in_context.get("total_taken"), 2)
        self.assertEqual(stats_in_context.get("avg_score_percent"), 90)

    def test_profile_page_context_no_data(self):  # Duplicated
        self.client.login(username="nodataprofile", password="password123")
        response = self.client.get(reverse("pages:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("quiz_attempts", response.context)
        self.assertEqual(response.context["quiz_attempts"].count(), 0)
        self.assertIn("user_collections", response.context)
        self.assertEqual(response.context["user_collections"].count(), 1)
        self.assertEqual(
            response.context["user_collections"].first(), self.nodata_user_collection
        )
        self.assertIn("stats", response.context)
        stats_in_context = response.context["stats"]
        self.assertEqual(stats_in_context.get("total_taken"), 0)
        self.assertEqual(stats_in_context.get("avg_score_percent"), 0)

    def test_select_collection_for_quiz_view_context_with_next_param(
        self,
    ):  # Duplicated
        self.client.login(username="profiletester", password="password123")
        quiz_id = self.quiz_t1.id
        next_path = "/some/previous/path/"
        url = f"{reverse('pages:select_collection_for_quiz', args=[quiz_id])}?next={next_path}"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("next_url", response.context)
        self.assertEqual(response.context["next_url"], next_path)
        logger.info(f"Context 'next_url' verified: {response.context['next_url']}")

    def test_select_collection_for_quiz_view_context_without_next_param(
        self,
    ):  # Duplicated
        self.client.login(username="profiletester", password="password123")
        quiz_id = self.quiz_t1.id
        url = reverse("pages:select_collection_for_quiz", args=[quiz_id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("next_url", response.context)
        self.assertIsNone(response.context["next_url"])
        logger.info("Context 'next_url' correctly None when no GET param.")

    def test_add_quiz_to_selected_collection_redirects_to_next_param(
        self,
    ):  # Duplicated
        self.client.login(username="profiletester", password="password123")
        quiz_id = self.quiz_t2.id
        collection_id = self.collection2.id

        self.assertNotIn(self.quiz_t2, self.collection2.quizzes.all())

        next_path = reverse("pages:quizzes") + "?category=technology"
        url = reverse(
            "pages:add_quiz_to_selected_collection", args=[quiz_id, collection_id]
        )

        post_data = {"next": next_path}
        response = self.client.post(url, post_data)

        self.assertEqual(
            response.status_code,
            302,
            f"Expected redirect, got {response.status_code}. Errors: {response.context.get('form', {}).errors if response.context else 'No context'}",
        )
        self.assertRedirects(
            response, next_path, msg_prefix=f"Should redirect to '{next_path}'"
        )

        self.collection2.refresh_from_db()
        self.assertIn(self.quiz_t2, self.collection2.quizzes.all())
        logger.info(f"Successfully redirected to 'next' path: {next_path}")

    def test_add_quiz_to_selected_collection_redirects_to_profile_if_next_invalid(
        self,
    ):  # Duplicated
        self.client.login(username="profiletester", password="password123")
        quiz_id = self.quiz_t2.id
        collection_id = self.collection2.id

        next_path_invalid = "http://external.com/bad"
        url = reverse(
            "pages:add_quiz_to_selected_collection", args=[quiz_id, collection_id]
        )

        post_data = {"next": next_path_invalid}
        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("pages:profile"),
            msg_prefix="Should redirect to profile for invalid 'next'",
        )
        logger.info("Correctly redirected to profile for invalid 'next' path.")

    def test_add_quiz_to_selected_collection_redirects_to_profile_if_next_missing(
        self,
    ):  # Duplicated
        self.client.login(username="profiletester", password="password123")
        quiz_id = self.quiz_t3.id
        collection_id = self.collection2.id

        self.assertNotIn(self.quiz_t3, self.collection2.quizzes.all())

        url = reverse(
            "pages:add_quiz_to_selected_collection", args=[quiz_id, collection_id]
        )

        post_data = {}
        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("pages:profile"),
            msg_prefix="Should redirect to profile if 'next' is missing",
        )

        self.collection2.refresh_from_db()
        self.assertIn(self.quiz_t3, self.collection2.quizzes.all())
        logger.info("Correctly redirected to profile when 'next' path was missing.")
