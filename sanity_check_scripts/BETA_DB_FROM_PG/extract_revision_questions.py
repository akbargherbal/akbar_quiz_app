# extract_revision_questions.py
import pandas as pd
import json
import os
import logging
from itertools import chain

# --- Configuration ---
BASE_INPUT_DIR = "database_pkl_export_from_sql_parse" # Directory where stage 1 .pkl files are
# Updated filenames to match the output of convert_sql_to_pkl.py which includes the schema
USER_AUTH_FILE = "public_auth_user.pkl"
ATTEMPTS_FILE = "public_multi_choice_quiz_quizattempt.pkl"
QUESTIONS_FILE = "public_multi_choice_quiz_question.pkl"

TARGET_USER_NAME = 'akbar' # Configurable user name

OUTPUT_PKL_FILENAME = "USER_FEEDBACK.pkl" # Output file in the current working directory
LOG_FILE_NAME = "extract_revision_questions.log" # Log file in the current working directory

# Columns to select from the questions_df
# From notebook: 'id text chapter_no tag quiz_id topic_id created_at'.split()
# which correctly becomes: ['id', 'text', 'chapter_no', 'tag', 'quiz_id', 'topic_id', 'created_at']
FINAL_QUESTION_COLUMNS = ['id', 'text', 'chapter_no', 'tag', 'quiz_id', 'topic_id', 'created_at']


def setup_logger(log_file_name):
    """Sets up a logger that logs to a file and to the console."""
    logger = logging.getLogger('RevisionExtractor')
    logger.setLevel(logging.INFO)

    # Remove existing handlers to prevent duplicate logging
    if logger.hasHandlers():
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File Handler
    fh = logging.FileHandler(log_file_name, mode='w')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console Handler
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO) # Adjust as needed, e.g., logging.WARNING for less console output
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    return logger

def main():
    logger = setup_logger(LOG_FILE_NAME)
    logger.info("--- Extract Revision Questions Script Started ---")
    logger.info(f"Base input directory: {BASE_INPUT_DIR}")
    logger.info(f"Target user name: {TARGET_USER_NAME}")
    logger.info(f"Output file: {OUTPUT_PKL_FILENAME}")

    try:
        # --- 1. Load user data and find target user ID ---
        user_df_path = os.path.join(BASE_INPUT_DIR, USER_AUTH_FILE)
        logger.info(f"Loading user data from: {user_df_path}")
        if not os.path.exists(user_df_path):
            logger.error(f"User data file not found: {user_df_path}")
            return

        user_df = pd.read_pickle(user_df_path)
        user_df = user_df.dropna(subset=['username']).reset_index(drop=True)
        
        user_series = user_df[user_df['username'] == TARGET_USER_NAME]['id']
        if user_series.empty:
            logger.error(f"User '{TARGET_USER_NAME}' not found in {USER_AUTH_FILE}.")
            target_user_id = None
            logger.warning(f"Proceeding without a specific user_id for '{TARGET_USER_NAME}'. All attempts will be processed.")
        else:
            target_user_id = int(user_series.values[0])
            logger.info(f"Found user_id for '{TARGET_USER_NAME}': {target_user_id}")

        # --- 2. Load attempt data ---
        attempt_df_path = os.path.join(BASE_INPUT_DIR, ATTEMPTS_FILE)
        logger.info(f"Loading attempt data from: {attempt_df_path}")
        if not os.path.exists(attempt_df_path):
            logger.error(f"Attempt data file not found: {attempt_df_path}")
            return
            
        attempt_df = pd.read_pickle(attempt_df_path)
        attempt_df = attempt_df.dropna(subset=['attempt_details']).reset_index(drop=True)
        attempt_df['user_id'] = attempt_df['user_id'].fillna(0).astype(int)
        logger.info(f"Loaded {len(attempt_df)} attempts after dropping NaNs in 'attempt_details'.")

        # --- 3. Extract question IDs from all attempts ---
        if 'attempt_details' not in attempt_df.columns:
            logger.error("'attempt_details' column not found in attempt_df.")
            return

        def get_question_keys(details_json_str):
            try:
                return list(json.loads(details_json_str).keys())
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Could not parse JSON in attempt_details: {str(details_json_str)[:100]}... Error: {e}")
                return []

        attempt_df['questions_keys'] = attempt_df['attempt_details'].apply(get_question_keys)
        list_q_ids_str = list(chain(*attempt_df['questions_keys']))
        
        list_q_ids = []
        for q_id_str in list_q_ids_str:
            try:
                list_q_ids.append(int(q_id_str))
            except ValueError:
                logger.warning(f"Could not convert question ID '{q_id_str}' to int. Skipping.")
        
        if not list_q_ids:
            logger.warning("No question IDs found from any attempts. Output will be empty.")
            questions_df = pd.DataFrame(columns=FINAL_QUESTION_COLUMNS)
        else:
            logger.info(f"Extracted {len(list_q_ids_str)} question ID references from attempts.")
            list_q_ids = sorted(list(set(list_q_ids))) # Get unique IDs
            logger.info(f"Unique question IDs to fetch: {len(list_q_ids)}")

            # --- 4. Load questions data and filter ---
            questions_df_path = os.path.join(BASE_INPUT_DIR, QUESTIONS_FILE)
            logger.info(f"Loading questions data from: {questions_df_path}")
            if not os.path.exists(questions_df_path):
                logger.error(f"Questions data file not found: {questions_df_path}")
                return

            all_questions_df = pd.read_pickle(questions_df_path)
            logger.info(f"Loaded {len(all_questions_df)} total questions.")

            questions_df = all_questions_df[all_questions_df['id'].isin(list_q_ids)].reset_index(drop=True)
            logger.info(f"Found {len(questions_df)} questions matching the IDs from attempts.")

            missing_cols = [col for col in FINAL_QUESTION_COLUMNS if col not in questions_df.columns]
            if missing_cols:
                logger.error(f"Missing expected columns in questions_df: {missing_cols}. Cannot proceed with column selection.")
                logger.info(f"Available columns: {questions_df.columns.tolist()}")
                return
            
            questions_df = questions_df[FINAL_QUESTION_COLUMNS]
            logger.info(f"Selected final columns: {FINAL_QUESTION_COLUMNS}")


        # --- 5. Save the final DataFrame ---
        logger.info(f"Saving final {len(questions_df)} questions to: {OUTPUT_PKL_FILENAME}")
        questions_df.to_pickle(OUTPUT_PKL_FILENAME, protocol=4)
        logger.info("Successfully saved USER_FEEDBACK.pkl.")

    except FileNotFoundError as e:
        logger.error(f"A required pickle file was not found: {e}")
    except KeyError as e:
        logger.error(f"A required column was not found in a DataFrame: {e}")
    except Exception as e:
        logger.exception("An unexpected error occurred during the script execution:")
    finally:
        logger.info("--- Extract Revision Questions Script Finished ---")
        # Close and remove handlers to allow for re-running in same session if needed (e.g. in a notebook)
        # or to ensure logs are flushed.
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)

if __name__ == "__main__":
    main()