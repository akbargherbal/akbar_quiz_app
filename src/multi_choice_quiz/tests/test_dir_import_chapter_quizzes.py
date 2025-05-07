# src/multi_choice_quiz/tests/test_dir_import_chapter_quizzes.py

import sys
import tempfile
import shutil
import pandas as pd
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock
import logging  # Import logging

from django.test import TestCase
from django.core.management import call_command

import dir_import_chapter_quizzes  # Import the module

from multi_choice_quiz.models import Quiz, Question, Topic
from multi_choice_quiz.tests.test_logging import setup_test_logging

logger = setup_test_logging(__name__, "multi_choice_quiz_dir_import_script")


class TestDirImportChapterQuizzesScript(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("migrate", verbosity=0)
        logger.info("Database schema ensured via migrate.")

    def setUp(self):
        self.test_temp_root = Path(tempfile.mkdtemp())
        logger.info(f"Created temporary root for test: {self.test_temp_root}")
        self.mock_quiz_collections_target_in_temp = (
            self.test_temp_root / "QUIZ_COLLECTIONS_MOCKED"
        )
        self.mock_quiz_collections_target_in_temp.mkdir()
        logger.info(
            f"Created mock quiz collections dir for script to target: {self.mock_quiz_collections_target_in_temp}"
        )

        src_path = Path(dir_import_chapter_quizzes.__file__).resolve().parent
        project_root_path_real = src_path.parent
        self.real_path_script_targets = (
            project_root_path_real
            / Path(dir_import_chapter_quizzes.DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH)
        ).resolve()
        logger.info(
            f"Script will try to resolve its QUIZ_COLLECTIONS to: {self.real_path_script_targets}"
        )

        # Store original Path methods carefully before any patching occurs per test method
        self.original_path_is_dir = Path.is_dir
        self.original_path_glob = Path.glob

        Quiz.objects.all().delete()
        Question.objects.all().delete()
        Topic.objects.all().delete()
        logger.info("Cleared Quiz, Question, Topic tables for fresh test method.")

    def tearDown(self):
        if self.test_temp_root.exists():
            shutil.rmtree(self.test_temp_root)
            logger.info(f"Removed temporary root: {self.test_temp_root}")
        else:
            logger.warning(
                f"Temporary root {self.test_temp_root} did not exist at teardown."
            )

    def _create_dummy_pkl_file(
        self,
        filename_stem,
        num_questions=1,
        chapter_no=1,
        topic="Dummy Topic",
        chapter_title="Dummy Chapter Title",
    ):
        data = {
            "chapter_no": [chapter_no] * num_questions,
            "question_text": [
                f"Q{i+1} from {filename_stem}.pkl" for i in range(num_questions)
            ],
            "options": [[f"Opt A", f"Opt B", f"Opt C"]] * num_questions,
            "answerIndex": [(i % 3) + 1 for i in range(num_questions)],
            "topic": [topic] * num_questions,
            "CHAPTER_TITLE": [f"{chapter_title} {chapter_no}"] * num_questions,
        }
        df = pd.DataFrame(data)
        file_path = self.mock_quiz_collections_target_in_temp / f"{filename_stem}.pkl"
        df.to_pickle(file_path)
        logger.info(
            f"Created dummy pkl file: {file_path} with {num_questions} questions."
        )
        return file_path

    def run_script_main(self, cli_args):
        """Helper to run the script's main() function, capturing its log output."""
        # Patch sys.argv for the script
        with patch.object(sys, "argv", ["dir_import_chapter_quizzes.py"] + cli_args):
            # Use self.assertLogs to capture logs from the script's logger
            # The script's logger is named "quiz_import"
            with self.assertLogs(logger="quiz_import", level="INFO") as log_cm:
                logger.info(f"Running script main with args: {cli_args}")
                try:
                    exit_code = dir_import_chapter_quizzes.main()
                except (
                    Exception
                ) as e:  # Catch exceptions from main to ensure logs are processed
                    logger.error(f"Exception during script main: {e}", exc_info=True)
                    exit_code = 1  # Assume error exit code

                output_text = "\n".join(log_cm.output)

            logger.info(f"Script exit code: {exit_code}")
            # logger.debug(f"Script output captured by assertLogs:\n{output_text}") # For debugging test
            return exit_code, output_text

    def path_side_effect_for_target_dir(
        self, original_path_method, path_instance, *method_args
    ):
        """
        A side_effect function for Path methods (is_dir, glob).
        If the Path instance being operated on is the one the script calculated
        for QUIZ_COLLECTIONS, it redirects the call to our
        self.mock_quiz_collections_target_in_temp. Otherwise, it calls the original method.
        `path_instance` is the Path object the method was called on.
        `method_args` are any other args for the method (e.g., 'pattern' for glob).
        """
        # This debug logging can be very verbose, enable if needed
        # logger.debug(f"SIDE_EFFECT: original_method={original_path_method.__name__}, path_instance='{path_instance}', method_args={method_args}")

        if path_instance.resolve() == self.real_path_script_targets:
            logger.info(
                f"Redirecting Path.{original_path_method.__name__} for '{path_instance}' to operate on '{self.mock_quiz_collections_target_in_temp}'"
            )
            return getattr(
                self.mock_quiz_collections_target_in_temp, original_path_method.__name__
            )(*method_args)
        else:
            # logger.debug(f"Calling original Path.{original_path_method.__name__} for '{path_instance}'")
            # Call the original unbound method, passing the instance and other args
            return original_path_method(path_instance, *method_args)

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.glob", autospec=True)
    def test_import_from_directory_success_one_file(self, mock_glob, mock_is_dir):
        logger.info("--- Test: test_import_from_directory_success_one_file ---")
        self._create_dummy_pkl_file("test_quiz_01", num_questions=2, chapter_no=1)

        mock_is_dir.side_effect = lambda p_inst: self.path_side_effect_for_target_dir(
            self.original_path_is_dir, p_inst
        )
        mock_glob.side_effect = (
            lambda p_inst, pattern: self.path_side_effect_for_target_dir(
                self.original_path_glob, p_inst, pattern
            )
        )

        exit_code, output = self.run_script_main(["--import-dir"])

        self.assertEqual(
            exit_code, 0, f"Script should exit successfully. Output:\n{output}"
        )
        self.assertIn("Directory import mode. Processing .pkl files from", output)
        # Check that the script logged the *actual path it believes it's using for QUIZ_COLLECTIONS*
        self.assertIn(
            str(self.real_path_script_targets.resolve()),
            output,
            "Log should show the script's calculated QUIZ_COLLECTIONS path",
        )
        self.assertIn(
            "Successfully created '01 Dummy Chapter Title 1: Dummy Topic - Quiz 1'",
            output,
        )

        self.assertEqual(Quiz.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 2)
        quiz = Quiz.objects.first()
        self.assertEqual(quiz.title, "01 Dummy Chapter Title 1: Dummy Topic - Quiz 1")
        self.assertEqual(quiz.question_count(), 2)

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.glob", autospec=True)
    def test_import_from_directory_success_multiple_files(self, mock_glob, mock_is_dir):
        logger.info("--- Test: test_import_from_directory_success_multiple_files ---")
        self._create_dummy_pkl_file(
            "test_quiz_A", num_questions=3, chapter_no=10, topic="Topic A"
        )
        self._create_dummy_pkl_file(
            "test_quiz_B", num_questions=1, chapter_no=11, topic="Topic B"
        )

        mock_is_dir.side_effect = lambda p_inst: self.path_side_effect_for_target_dir(
            self.original_path_is_dir, p_inst
        )
        mock_glob.side_effect = (
            lambda p_inst, pattern: self.path_side_effect_for_target_dir(
                self.original_path_glob, p_inst, pattern
            )
        )

        exit_code, output = self.run_script_main(["--import-dir"])
        self.assertEqual(
            exit_code, 0, f"Script should exit successfully. Output:\n{output}"
        )

        self.assertEqual(Quiz.objects.count(), 2)
        self.assertEqual(Question.objects.count(), 3 + 1)
        self.assertTrue(
            Quiz.objects.filter(
                title__contains="10 Dummy Chapter Title 10: Topic A - Quiz 1"
            ).exists()
        )
        self.assertTrue(
            Quiz.objects.filter(
                title__contains="11 Dummy Chapter Title 11: Topic B - Quiz 1"
            ).exists()
        )
        self.assertEqual(Topic.objects.count(), 2)

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.glob", autospec=True)
    def test_import_from_directory_not_found_by_script(self, mock_glob, mock_is_dir):
        logger.info("--- Test: test_import_from_directory_not_found_by_script ---")

        def is_dir_returns_false_for_target(path_instance_being_called_on):
            # path_instance_being_called_on is the Path object .is_dir() was called on.
            if path_instance_being_called_on.resolve() == self.real_path_script_targets:
                logger.info(
                    f"Mocking Path.is_dir for '{path_instance_being_called_on}' to return False."
                )
                return False
            # For any other Path.is_dir call, use original behavior
            return self.original_path_is_dir(path_instance_being_called_on)

        mock_is_dir.side_effect = is_dir_returns_false_for_target
        mock_glob.return_value = (
            []
        )  # Should not be called if is_dir is False for target

        exit_code, output = self.run_script_main(["--import-dir"])

        self.assertEqual(
            exit_code,
            1,
            f"Script should exit with 1 for dir not found. Output:\n{output}",
        )
        self.assertIn(
            f"Default import directory '{self.real_path_script_targets}' not found",
            output,
        )
        self.assertEqual(Quiz.objects.count(), 0)

    @patch("pathlib.Path.is_dir", autospec=True)
    @patch("pathlib.Path.glob", autospec=True)
    def test_import_from_directory_empty(self, mock_glob, mock_is_dir):
        logger.info("--- Test: test_import_from_directory_empty ---")

        mock_is_dir.side_effect = lambda p_inst: self.path_side_effect_for_target_dir(
            self.original_path_is_dir, p_inst
        )
        mock_glob.side_effect = (
            lambda p_inst, pattern: self.path_side_effect_for_target_dir(
                self.original_path_glob, p_inst, pattern
            )
        )

        exit_code, output = self.run_script_main(["--import-dir"])
        self.assertEqual(
            exit_code,
            0,
            f"Script should exit successfully even with empty dir. Output:\n{output}",
        )
        self.assertIn("Scanned 0 .pkl files", output)
        self.assertEqual(Quiz.objects.count(), 0)

    def test_test_mode_creates_sample_data(self):
        logger.info("--- Test: test_test_mode_creates_sample_data ---")
        exit_code, output = self.run_script_main(["--test"])
        self.assertEqual(
            exit_code,
            0,
            f"Script --test mode should exit successfully. Output:\n{output}",
        )
        self.assertIn("Running in test mode with generated data.", output)
        self.assertEqual(Quiz.objects.count(), 3)
        self.assertEqual(Question.objects.count(), 6)
        self.assertTrue(
            Quiz.objects.filter(
                title__contains="01 Introduction to Testing: Test Topic A - Quiz 1"
            ).exists()
        )

    @patch(
        "os.path.exists", autospec=True
    )  # Patch os.path.exists used by load_quiz_bank
    def test_test_file_mode_success(self, mock_os_path_exists):
        logger.info("--- Test: test_test_file_mode_success ---")
        dummy_file_path_obj = self.test_temp_root / "specific_test_file.pkl"
        dummy_file_path_str = str(dummy_file_path_obj)
        data = {
            "chapter_no": [1] * 2,
            "question_text": ["TF Q1", "TF Q2"],
            "options": [["A", "B", "C"]] * 2,
            "answerIndex": [1] * 2,
            "topic": ["FileTopic"] * 2,
            "CHAPTER_TITLE": ["FileChapter 1"] * 2,
        }
        pd.DataFrame(data).to_pickle(dummy_file_path_obj)
        logger.info(f"Created dummy file for --test-file: {dummy_file_path_str}")

        # load_quiz_bank calls os.path.exists(file_path)
        mock_os_path_exists.return_value = True

        exit_code, output = self.run_script_main(["--test-file", dummy_file_path_str])

        self.assertEqual(
            exit_code,
            0,
            f"Script --test-file mode should exit successfully. Output:\n{output}",
        )
        # Ensure os.path.exists was called with the correct path
        mock_os_path_exists.assert_called_with(dummy_file_path_str)
        self.assertIn(
            f"Running in test mode with provided file: {dummy_file_path_str}", output
        )
        self.assertEqual(Quiz.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 2)
        self.assertTrue(
            Quiz.objects.filter(
                title__contains="01 FileChapter 1: FileTopic - Quiz 1"
            ).exists()
        )

    @patch("os.path.exists", autospec=True)
    def test_test_file_mode_file_not_found(self, mock_os_path_exists):
        logger.info("--- Test: test_test_file_mode_file_not_found ---")
        non_existent_file_str = str(self.test_temp_root / "not_real.pkl")
        mock_os_path_exists.return_value = False

        exit_code, output = self.run_script_main(["--test-file", non_existent_file_str])

        self.assertEqual(
            exit_code,
            1,
            f"Script --test-file mode should exit with 1 if file not found. Output:\n{output}",
        )
        mock_os_path_exists.assert_called_with(non_existent_file_str)
        self.assertIn(f"Quiz bank file not found: {non_existent_file_str}", output)
        self.assertEqual(Quiz.objects.count(), 0)

    @patch("builtins.input", return_value="non_existent_file.pkl")
    @patch("os.path.exists", return_value=False, autospec=True)
    def test_interactive_mode_file_not_found(self, mock_os_exists, mock_input):
        logger.info("--- Test: test_interactive_mode_file_not_found ---")
        exit_code, output = self.run_script_main([])

        self.assertEqual(
            exit_code,
            1,
            f"Script interactive mode should exit with 1 if file not found. Output:\n{output}",
        )
        self.assertIn("Entering interactive mode.", output)
        mock_input.assert_called_once()  # Verify input was called
        mock_os_exists.assert_called_with(
            "non_existent_file.pkl"
        )  # Verify os.path.exists was called with user input
        self.assertIn("Quiz bank file not found: non_existent_file.pkl", output)
        self.assertEqual(Quiz.objects.count(), 0)
