# --- START OF MODIFIED SCRIPT ---

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import google.generativeai as genai

# User-defined constants (Keep these as they were)
# *** ENSURE this model supports Context Caching ***
GEMINI_MODEL = "gemini-2.5-pro-preview-03-25"
MAX_TOKENS = 65_000 # Max *output* tokens per API call. Context size is handled by caching.
PROMPT_INDEX_COLUMN = "PROMPT_ID"  # Name of the column containing prompt indices
# Name of the column containing the actual prompts (incl. Prompt 0 with shared context/instructions)
PROMPT_COLUMN = "PROMPT"
MAX_DELAY = 45  # Maximum delay between API calls in seconds

# Additional columns to include in results (Keep as needed)
ADDITIONAL_COLUMNS = []
# Time-stamped output directory (Same setup)
TIME_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
DIR_RESULT = f"results_{TIME_STAMP}"
LogFileName = "LOG.log"
PKL_FILE_NAME = "RESULTS.pkl"

# Create directory to save results if it doesn't exist (Same setup)
os.makedirs(DIR_RESULT, exist_ok=True)

# Set up logging (Same setup)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(DIR_RESULT, LogFileName)),
        logging.StreamHandler(),
    ],
)


def setup_gemini_api():
    """Set up the Gemini API key and model.
    *** NO CHANGE from original script ***
    This function initializes a SINGLE model instance which is key for context caching.
    """
    logging.info(
        "Google API key not found in environment variables. Please enter it now."
    )
    print("Google API key not found in environment variables. Please enter it now.")
    api_key = input("Paste your Google API key: ").strip()

    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": MAX_TOKENS,
    }
    safety_settings = [
        {"category": category, "threshold": "BLOCK_NONE"}
        for category in [
            "HARM_CATEGORY_HARASSMENT",
            "HARM_CATEGORY_HATE_SPEECH",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "HARM_CATEGORY_DANGEROUS_CONTENT",
        ]
    ]

    try:
        # *** CRITICAL: Initialize the model ONCE here. ***
        # This 'model' object will be reused across API calls in process_prompts,
        # which enables the context caching feature automatically for supported models.
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        # Test the model with a simple prompt (Good practice)
        model.generate_content("Hello")
        logging.info("Gemini API authentication and model setup successful.")
        logging.info(f"Using model: {GEMINI_MODEL} (Ensure it supports Context Caching)")
        print(f"Using model: {GEMINI_MODEL} (Ensure it supports Context Caching)")

    except Exception as e:
        logging.error(f"An error occurred while setting up the Gemini API: {str(e)}")
        sys.exit(1)

    # *** Return the SINGLE model instance ***
    return model


def generate_response(model, prompt_text, prompt_id):
    """Generate a response using Gemini API based on user input.
    *** ENHANCEMENT: Added optional logging for cache usage confirmation. ***
    *** CORE CHANGE: No change needed here for caching to work, as long as the SAME 'model' instance is passed in repeatedly. ***
    """
    try:
        logging.debug(f"Sending prompt (ID: {prompt_id}) to API. Length: {len(prompt_text)} chars.")
        # Log snippet for the potentially large first prompt (Prompt 0 containing the initial context)
        if len(prompt_text) > 1000 and prompt_id == 0: # Be specific to prompt 0 if desired
             logging.debug(f"Prompt 0 starts: {prompt_text[:200]}...")
             logging.debug(f"...Prompt 0 ends: {prompt_text[-200:]}")

        start_time = time.time()
        # *** This call uses the SAME 'model' instance passed from process_prompts. ***
        # *** On the first call (Prompt 0), it sends the full text and establishes the cache. ***
        # *** On subsequent calls (Prompts 1-N), the library detects the same model instance ***
        # *** and reuses the cache, sending only the new prompt text. ***
        response = model.generate_content(prompt_text)
        end_time = time.time()
        logging.info(f"API call for Prompt ID {prompt_id} took {end_time - start_time:.2f} seconds.")

        # --- [Optional Enhancement] Log Cache Usage Info ---
        try:
            usage_metadata = getattr(response, 'usage_metadata', None)
            if usage_metadata:
                # Check common attributes for cache info
                cached_tokens = getattr(usage_metadata, 'cached_content_token_count', 0)
                prompt_tokens = getattr(usage_metadata, 'prompt_token_count', 'N/A') # Tokens in *this* turn's prompt
                candidates_tokens = getattr(usage_metadata, 'candidates_token_count', 'N/A') # Tokens in the response
                total_tokens = getattr(usage_metadata, 'total_token_count', 'N/A') # Total billed for *this* turn

                if cached_tokens > 0:
                    # This indicates context caching was successfully used for this turn
                    logging.info(f"Prompt ID {prompt_id}: Context Cache HIT. Cached: {cached_tokens}, Turn Prompt: {prompt_tokens}, Turn Candidates: {candidates_tokens}, Turn Total: {total_tokens} tokens.")
                    print(f"Prompt ID {prompt_id}: Context Cache HIT. (Tokens Billed This Turn: {total_tokens})")
                else:
                    # This is expected for the first call (Prompt 0) which loads the context
                    logging.info(f"Prompt ID {prompt_id}: Context Cache MISS/First Call. Turn Prompt: {prompt_tokens}, Turn Candidates: {candidates_tokens}, Turn Total: {total_tokens} tokens.")
                    print(f"Prompt ID {prompt_id}: Context Cache MISS/First Call. (Tokens Billed This Turn: {total_tokens})")
            else:
                logging.warning(f"Prompt ID {prompt_id}: Could not retrieve usage_metadata from response to check cache status.")
        except Exception as meta_e:
             logging.warning(f"Prompt ID {prompt_id}: Error accessing usage_metadata - {str(meta_e)}")
        # --- [End Optional Enhancement] ---

        prefix = str(prompt_id).zfill(2) # Using original zero-padding logic
        result_content = response.text
        result_file_name = f"{prefix}_result.txt" # Using original file naming
        with open(
            os.path.join(DIR_RESULT, result_file_name), "w", encoding="utf-8"
        ) as f:
            f.write(result_content)

        # Return the text content and the full response object (as in original script)
        # Be mindful that the 'response' object for Prompt 0 might be large if it includes input details.
        return result_content, response
    except Exception as e:
        logging.error(f"Error generating response for prompt ID {prompt_id}: {str(e)}")
        # Specific check for potential issue with large initial context
        if "ResourceExhausted" in str(e) and prompt_id == 0:
             logging.error("ResourceExhausted error on Prompt 0 might indicate the initial context + instructions exceed the model's processing limit for caching.")
             print(f"ERROR on Prompt ID {prompt_id}: Initial shared context + instructions might be too large for the model's caching limit.")
        elif "MaxTokens" in str(e):
             logging.error(f"MaxTokens error on Prompt ID {prompt_id}: The requested 'max_output_tokens' ({MAX_TOKENS}) might be too large or the response generated was too long.")
             print(f"ERROR on Prompt ID {prompt_id}: Output token limit likely exceeded.")

        return None, None


def process_prompts(model, path_to_prompts):
    """Process prompts sequentially against a shared context and generate responses.
    *** NO CHANGE from original script's core logic ***
    The key is that this function receives the SINGLE 'model' instance from main()
    and uses it REPEATEDLY in the loop when calling generate_response().
    This implicitly enables context caching via the Gemini library.
    *** USER RESPONSIBILITY: Ensure the PKL file at 'path_to_prompts' has Prompt 0 formatted correctly (task instructions + full shared context). ***
    """
    try:
        df = pd.read_pickle(path_to_prompts)
        logging.info(f"Columns in the dataframe: {list(df.columns)}")
        print(f"Columns in the dataframe: {list(df.columns)}")

        if PROMPT_COLUMN not in df.columns:
            raise KeyError(f"'{PROMPT_COLUMN}' column not found in the input DataFrame")

        if PROMPT_INDEX_COLUMN not in df.columns:
            raise KeyError(
                f"'{PROMPT_INDEX_COLUMN}' column not found in the input DataFrame"
            )

    except FileNotFoundError:
        logging.error(f"Input file {path_to_prompts} not found.")
        return
    except KeyError as e:
        logging.error(f"Column error: {str(e)}")
        return
    except Exception as e:
        logging.error(f"Error reading input file: {str(e)}")
        return

    # Ensure processing happens in order based on PROMPT_ID (0, 1, 2...)
    # This is crucial for the caching strategy (Prompt 0 MUST come first to establish context).
    df = df.sort_values(by=PROMPT_INDEX_COLUMN).reset_index(drop=True)
    prompts_list = list(zip(df[PROMPT_INDEX_COLUMN], df[PROMPT_COLUMN]))

    results_list = [] # Using original results collection method

    total_prompts_count = len(prompts_list)

    # *** The loop iterates through prompts sequentially (0 to N) ***
    for index, (prompt_id, prompt_text) in enumerate(prompts_list, 1):
        # Skipping logic remains the same (useful for resuming within the *same run* if needed)
        if any(item["PROMPT_ID"] == prompt_id for item in results_list):
            logging.info(
                f"Skipping prompt {index} (ID: {prompt_id}) as it's already processed in this run."
            )
            continue

        logging.info(f"Processing prompt {index} of {total_prompts_count} (ID: {prompt_id})")
        print(f"Processing prompt {index} of {total_prompts_count} (ID: {prompt_id})")
        start = datetime.now()

        # *** Call generate_response with the SAME 'model' instance each time ***
        # This enables context caching after the first call (Prompt 0).
        result_content, response = generate_response(model, prompt_text, prompt_id)

        # Result handling and saving logic remains identical to the original script
        if result_content:
            result_dict = {
                "PROMPT_ID": prompt_id,
                "RESULT": result_content,
                "RESPONSE": response, # Storing full response object as before
            }
            # Add additional columns (same logic)
            for col in ADDITIONAL_COLUMNS:
                if col in df.columns:
                    # Ensure correct row selection based on prompt_id
                    row_index = df.index[df[PROMPT_INDEX_COLUMN] == prompt_id].tolist()
                    if row_index:
                        result_dict[col] = df.loc[row_index[0], col]
                    else:
                         logging.warning(f"Prompt ID {prompt_id} not found for additional column '{col}'")
                else:
                    logging.warning(f"Column '{col}' not found in the input DataFrame")

            results_list.append(result_dict)
            df_result = pd.DataFrame(results_list) # Create DataFrame from list
            try:
                # Save intermediate results (same logic)
                df_result.to_pickle(os.path.join(DIR_RESULT, PKL_FILE_NAME), protocol=4)
                logging.info(f"Intermediate results saved for prompt {index}")
            except Exception as e:
                logging.error(f"Error saving intermediate results: {str(e)}")
                print(f"Error saving intermediate results: {str(e)}")
        else:
            # Handle case where generate_response returned None (due to an error)
             logging.warning(f"No result content generated for prompt {index} (ID: {prompt_id}). Skipping result save for this prompt.")
             print(f"WARNING: No result content generated for prompt {index} (ID: {prompt_id}).")


        # Rate limiting logic remains identical
        end = datetime.now()
        sleep_time = max(MAX_DELAY - (end - start).total_seconds(), 0)
        if sleep_time > 0:
            logging.info(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)

    # Final summary message logic remains identical
    logging.info(
        f"Processing complete. {len(results_list)} out of {total_prompts_count} prompts processed successfully (results saved)."
    )
    logging.info(f"Results saved to {DIR_RESULT}")
    print(
        f"Processing complete. {len(results_list)} out of {total_prompts_count} prompts processed successfully (results saved)."
    )
    print(f"Results saved to {DIR_RESULT}")


def main():
    """ Main function to run the script.
    *** NO CHANGE from original script ***
    It sets up the model ONCE and passes that instance to process_prompts.
    """
    try:
        path_to_prompts = input(
            "Enter the path to the PKL file containing prompts (ensure Prompt 0 has initial context + instructions): "
        ).strip()
        # *** Model is set up ONCE here ***
        model = setup_gemini_api()
        # *** The SAME model instance is passed to process_prompts ***
        process_prompts(model, path_to_prompts)
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {str(e)}")
        print(
            f"An unexpected error occurred. Please check the log file in {DIR_RESULT} for details."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

# --- END OF MODIFIED SCRIPT ---