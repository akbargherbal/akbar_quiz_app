# src/multi_choice_quiz/tests/test_dir_import_chapter_quizzes.py

import os
import sys
import pandas as pd
from pathlib import Path
from unittest import mock
from django.test import TestCase
from django.conf import settings

try:
    from dir_import_chapter_quizzes import main as dir_importer_main
    from dir_import_chapter_quizzes import DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH
except ImportError as e:
    raise ImportError(
        "Could not import 'main' from 'dir_import_chapter_quizzes.py'. "
        f"Original error: {e}"
    )

from multi_choice_quiz.models import Quiz
from .test_logging import setup_test_logging
logger = setup_test_logging(__name__, "multi_choice_quiz_dir_import")

def create_dummy_pkl_file(dir_path, filename, data_dict):
    file_path = dir_path / filename
    df = pd.DataFrame(data_dict)
    df.to_pickle(file_path)
    return file_path

class TestDirImportChapterQuizzesScript(TestCase):
    def setUp(self):
        self.mock_project_root = Path(settings.BASE_DIR)
        
        temp_dir_name_for_files = DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH.lstrip('../').lstrip('./')
        if DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH.startswith('../'):
            self.temp_quiz_collections_path_for_creating_files = self.mock_project_root / temp_dir_name_for_files
        else:
            self.temp_quiz_collections_path_for_creating_files = self.mock_project_root / 'src' / temp_dir_name_for_files
        self.temp_quiz_collections_path_for_creating_files.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"setUp: Temp dir for creating files: {self.temp_quiz_collections_path_for_creating_files}")

        self.sample_df_data1 = {
            "chapter_no": [1], "question_text": ["Q1 Ch1?"], "options": [["A", "B"]], 
            "answerIndex": [1], "CHAPTER_TITLE": ["Chapter 1 Title"], "topic": ["Topic A"], "tag": ["TagA"]
        }
        self.sample_df_data2 = {
            "chapter_no": [2], "question_text": ["Q1 Ch2?"], "options": [["C", "D"]], 
            "answerIndex": [2], "CHAPTER_TITLE": ["Chapter 2 Title"], "topic": ["Topic B"], "tag": ["TagB"]
        }

    def tearDown(self):
        import shutil
        if hasattr(self, 'temp_quiz_collections_path_for_creating_files') and self.temp_quiz_collections_path_for_creating_files.exists():
            shutil.rmtree(self.temp_quiz_collections_path_for_creating_files)

    # Test for directory not found - CORRECTED SIDE_EFFECTS
    @mock.patch('dir_import_chapter_quizzes.sys.exit')
    @mock.patch('dir_import_chapter_quizzes.import_questions_by_chapter')
    @mock.patch('dir_import_chapter_quizzes.load_quiz_bank')
    @mock.patch('pathlib.Path.is_dir') 
    @mock.patch('pathlib.Path.resolve') 
    @mock.patch('dir_import_chapter_quizzes.Path') 
    def test_import_dir_directory_not_found(
        self, mock_script_path_constructor, mock_path_resolve, mock_path_is_dir,
        mock_load_quiz_bank, mock_import_questions, mock_sys_exit
    ):
        logger.info("Testing --import-dir when directory not found (corrected side_effects)...")
        mock_sys_argv = ["dir_import_chapter_quizzes.py", "--import-dir"]

        mock_path_dunder_file_obj = mock.MagicMock(spec=Path, name="MockPathFor__file__")
        # Script calculates: script_dir = Path(__file__).resolve().parent
        # So, Path(__file__).resolve() should return something whose .parent is the script_dir.
        mock_path_dunder_file_obj.resolve.return_value = mock_path_dunder_file_obj 
        mock_path_dunder_file_obj.parent = Path(settings.BASE_DIR) / 'src' # script_dir

        def script_path_constructor_side_effect(arg_to_path_constructor):
            # This __file__ is the one from dir_import_chapter_quizzes.py context
            # For simplicity, we assume the test's __file__ location is close enough
            # or the script doesn't use __file__ for anything other than getting its dir.
            # A more robust way if the script's __file__ is crucial and different:
            # if arg_to_path_constructor == Path('dir_import_chapter_quizzes.py').resolve():
            if isinstance(arg_to_path_constructor, str) and 'dir_import_chapter_quizzes.py' in arg_to_path_constructor:
                 # This is a guess; depends on how the script refers to its own path if not __file__
                return mock_path_dunder_file_obj
            if arg_to_path_constructor == __file__: # Path(__file__) in the script
                return mock_path_dunder_file_obj
            return Path(arg_to_path_constructor) 
        mock_script_path_constructor.side_effect = script_path_constructor_side_effect
        
        # Path the script will try to check: (project_root / DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH)
        # project_root in script will be (Path(settings.BASE_DIR) / 'src').parent == Path(settings.BASE_DIR)
        path_obj_before_resolve_in_script = (Path(settings.BASE_DIR) / DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH)
        
        mock_resolved_target_dir_obj = mock.MagicMock(spec=Path, name="MockResolvedCollectionsDir")
        mock_resolved_target_dir_obj.__str__.return_value = "mocked/path/NON_EXISTENT_COLLECTIONS"

        # Store original methods to call them if needed
        _original_path_resolve = Path.resolve
        _original_path_is_dir = Path.is_dir

        # ***** CORRECTED selective_resolve *****
        def selective_resolve(instance_path_obj, strict=False): # Added 'instance_path_obj' for self
            if instance_path_obj == path_obj_before_resolve_in_script:
                return mock_resolved_target_dir_obj
            return _original_path_resolve(instance_path_obj, strict=strict)
        mock_path_resolve.side_effect = selective_resolve

        # ***** CORRECTED selective_is_dir_global *****
        def selective_is_dir_global(instance_path_obj): # Added 'instance_path_obj' for self
            if instance_path_obj == mock_resolved_target_dir_obj:
                return False # Directory does not exist
            return _original_path_is_dir(instance_path_obj)
        mock_path_is_dir.side_effect = selective_is_dir_global
        
        with mock.patch.object(sys, 'argv', mock_sys_argv):
            return_code = dir_importer_main()

        self.assertEqual(return_code, 1, "Main function should return 1 on directory not found.")
        mock_load_quiz_bank.assert_not_called()
        mock_import_questions.assert_not_called()
        # is_dir should be called on the object returned by resolve
        mock_path_is_dir.assert_any_call(mock_resolved_target_dir_obj)
        # resolve should be called on the path object before it's resolved
        mock_path_resolve.assert_any_call(path_obj_before_resolve_in_script, strict=False) # Check strict if Python version requires


    # Test for successful processing - CORRECTED SIDE_EFFECTS
    @mock.patch('dir_import_chapter_quizzes.sys.exit')
    @mock.patch('dir_import_chapter_quizzes.import_questions_by_chapter')
    @mock.patch('dir_import_chapter_quizzes.load_quiz_bank')
    @mock.patch('pathlib.Path.glob') 
    @mock.patch('pathlib.Path.is_dir')
    @mock.patch('pathlib.Path.resolve')
    @mock.patch('dir_import_chapter_quizzes.Path')
    def test_import_dir_flag_processes_pkl_files(
        self, mock_script_path_constructor, mock_path_resolve, mock_path_is_dir, mock_path_glob,
        mock_load_quiz_bank, mock_import_questions, mock_sys_exit
    ):
        logger.info("Testing --import-dir processes .pkl files (corrected side_effects)...")
        mock_sys_argv = ["dir_import_chapter_quizzes.py", "--import-dir"]

        pkl_file1 = create_dummy_pkl_file(self.temp_quiz_collections_path_for_creating_files, "quiz_data_01.pkl", self.sample_df_data1)
        pkl_file2 = create_dummy_pkl_file(self.temp_quiz_collections_path_for_creating_files, "quiz_data_02.pkl", self.sample_df_data2)

        mock_path_dunder_file_obj = mock.MagicMock(spec=Path, name="MockPathFor__file__Success")
        mock_path_dunder_file_obj.resolve.return_value = mock_path_dunder_file_obj
        mock_path_dunder_file_obj.parent = Path(settings.BASE_DIR) / 'src'
        def script_path_constructor_side_effect_success(arg):
            if arg == __file__: return mock_path_dunder_file_obj
            return Path(arg)
        mock_script_path_constructor.side_effect = script_path_constructor_side_effect_success
        
        path_obj_before_resolve_in_script = (Path(settings.BASE_DIR) / DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH)
        mock_resolved_target_dir_obj = mock.MagicMock(spec=Path, name="MockResolvedCollectionsDirSuccess")
        mock_resolved_target_dir_obj.__str__.return_value = str(self.temp_quiz_collections_path_for_creating_files)

        _original_path_resolve = Path.resolve
        def selective_resolve_success(instance_path_obj, strict=False):
            if instance_path_obj == path_obj_before_resolve_in_script: return mock_resolved_target_dir_obj
            return _original_path_resolve(instance_path_obj, strict=strict)
        mock_path_resolve.side_effect = selective_resolve_success

        _original_path_is_dir = Path.is_dir
        def selective_is_dir_success(instance_path_obj):
            if instance_path_obj == mock_resolved_target_dir_obj: return True
            return _original_path_is_dir(instance_path_obj)
        mock_path_is_dir.side_effect = selective_is_dir_success

        # mock_path_glob is now a global patch on Path.glob
        # It will be called with mock_resolved_target_dir_obj as its 'self'
        mock_path_glob.return_value = [pkl_file1, pkl_file2]

        mock_df1 = pd.DataFrame(self.sample_df_data1)
        mock_df2 = pd.DataFrame(self.sample_df_data2)
        mock_load_quiz_bank.side_effect = [mock_df1, mock_df2]
        mock_import_questions.side_effect = [(1, 10), (1, 15)]

        with mock.patch.object(sys, 'argv', mock_sys_argv):
            return_code = dir_importer_main()

        self.assertEqual(return_code, 0)
        mock_sys_exit.assert_not_called()
        self.assertEqual(mock_load_quiz_bank.call_count, 2)
        self.assertEqual(mock_import_questions.call_count, 2)
        mock_path_glob.assert_any_call(mock_resolved_target_dir_obj, "*.pkl")


    # Test for one file failing - CORRECTED SIDE_EFFECTS
    @mock.patch('dir_import_chapter_quizzes.sys.exit')
    @mock.patch('dir_import_chapter_quizzes.import_questions_by_chapter')
    @mock.patch('dir_import_chapter_quizzes.load_quiz_bank')
    @mock.patch('pathlib.Path.glob')
    @mock.patch('pathlib.Path.is_dir')
    @mock.patch('pathlib.Path.resolve')
    @mock.patch('dir_import_chapter_quizzes.Path')
    def test_import_dir_one_file_fails_to_load(
        self, mock_script_path_constructor, mock_path_resolve, mock_path_is_dir, mock_path_glob,
        mock_load_quiz_bank, mock_import_questions, mock_sys_exit
    ):
        logger.info("Testing --import-dir with one file load failure (corrected side_effects)...")
        mock_sys_argv = ["dir_import_chapter_quizzes.py", "--import-dir"]

        pkl_file_bad = create_dummy_pkl_file(self.temp_quiz_collections_path_for_creating_files, "bad_quiz.pkl", {"text": ["bad"]})
        pkl_file_good = create_dummy_pkl_file(self.temp_quiz_collections_path_for_creating_files, "good_quiz.pkl", self.sample_df_data2)
        
        mock_path_dunder_file_obj = mock.MagicMock(spec=Path, name="MockPathFor__file__OneFail")
        mock_path_dunder_file_obj.resolve.return_value = mock_path_dunder_file_obj
        mock_path_dunder_file_obj.parent = Path(settings.BASE_DIR) / 'src'
        def script_path_constructor_side_effect_one_fail(arg):
            if arg == __file__: return mock_path_dunder_file_obj
            return Path(arg)
        mock_script_path_constructor.side_effect = script_path_constructor_side_effect_one_fail

        path_obj_before_resolve_in_script = (Path(settings.BASE_DIR) / DEFAULT_IMPORT_DIRECTORY_RELATIVE_PATH)
        mock_resolved_target_dir_obj = mock.MagicMock(spec=Path, name="MockResolvedCollectionsDirOneFail")
        mock_resolved_target_dir_obj.__str__.return_value = str(self.temp_quiz_collections_path_for_creating_files)
        
        _original_path_resolve = Path.resolve
        def selective_resolve_one_fail(instance_path_obj, strict=False):
            if instance_path_obj == path_obj_before_resolve_in_script: return mock_resolved_target_dir_obj
            return _original_path_resolve(instance_path_obj, strict=strict)
        mock_path_resolve.side_effect = selective_resolve_one_fail
        
        _original_path_is_dir = Path.is_dir
        def selective_is_dir_one_fail(instance_path_obj):
            if instance_path_obj == mock_resolved_target_dir_obj: return True
            return _original_path_is_dir(instance_path_obj)
        mock_path_is_dir.side_effect = selective_is_dir_one_fail

        mock_path_glob.return_value = [pkl_file_bad, pkl_file_good]
        
        mock_df_good = pd.DataFrame(self.sample_df_data2)
        mock_load_quiz_bank.side_effect = [None, mock_df_good]
        mock_import_questions.return_value = (1, 10)

        with mock.patch.object(sys, 'argv', mock_sys_argv):
            return_code = dir_importer_main()
        
        self.assertEqual(return_code, 0)
        mock_sys_exit.assert_not_called()
        self.assertEqual(mock_load_quiz_bank.call_count, 2)
        self.assertEqual(mock_import_questions.call_count, 1)
        mock_path_glob.assert_any_call(mock_resolved_target_dir_obj, "*.pkl")