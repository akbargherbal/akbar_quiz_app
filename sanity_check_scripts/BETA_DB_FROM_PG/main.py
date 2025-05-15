import pandas as pd
import regex as re # Note: regex module is imported but not used in this script. Retained for consistency if it was intended for future use.
import os
import subprocess
import logging

# Configure basic logging for the main script itself
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command):
    """
    Run a shell command and return the output.
    Logs command execution details.
    """
    logging.info(f"Executing command: {command}")
    try:
        # Using list of arguments for Popen/run is generally safer
        # For shell=True, command is a string.
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        if result.stdout:
            logging.info(f"Stdout from '{command}':\n{result.stdout}")
        if result.stderr: # Some tools might output info to stderr
            logging.info(f"Stderr from '{command}':\n{result.stderr}") # Log stderr as info as it might not always be an error
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{command}' failed with return code {e.returncode}.")
        if e.stdout:
            logging.error(f"Stdout from failed '{command}':\n{e.stdout}")
        if e.stderr:
            logging.error(f"Stderr from failed '{command}':\n{e.stderr}")
        return None
    except FileNotFoundError:
        logging.error(f"Command not found (FileNotFoundError) for '{command}'. Ensure Python and the script path are correct.")
        return None


if __name__ == "__main__":
    logging.info("--- Main script started ---")
    
    # Define the commands to run
    # convert_sql_to_pkl.py is now the primary script for SQL COPY to PKL.
    # parse_pkl.py has been removed from this sequence.
    commands = [
        'python ./convert_sql_to_pkl.py',
        # 'python ./parse_pkl.py', # Removed as per alignment strategy
        'python ./sanity_check_psql_to_pkl.py',
        'python ./extract_revision_questions.py'
    ]

    all_successful = True
    for command in commands:
        print(f"\nRunning command: {command}") # Also print to console for immediate feedback
        output = run_command(command)
        if output is None: # run_command now returns None on failure
            print(f"Command {command} failed or did not execute.")
            logging.warning(f"Command {command} failed or did not execute. Subsequent steps might be affected.")
            all_successful = False
            # Decide if to break or continue: For now, let's try to run all.
            # break 
        # Output is already logged by run_command, no need to print it again here unless desired for verbosity.
        # else:
        #     print(f"Output of {command} processed.")

    if all_successful:
        logging.info("--- All commands executed successfully ---")
    else:
        logging.error("--- One or more commands failed during execution ---")