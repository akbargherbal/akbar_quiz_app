import pandas as pd
# import regex as re # Note: regex module is imported but not used in this script. Retained for consistency if it was intended for future use.
import os
import subprocess
import logging

# Configure basic logging for the main script itself
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
logger = logging.getLogger(__name__)


def run_command(command_str_or_list):
    """
    Run a shell command and return True on success, False on failure.
    Logs command execution details.
    Accepts command as a string (for shell=True) or list of args (for shell=False).
    """
    is_shell_command = isinstance(command_str_or_list, str)
    command_display = command_str_or_list if is_shell_command else ' '.join(command_str_or_list)
    
    logger.info(f"Executing command: {command_display}")
    try:
        result = subprocess.run(
            command_str_or_list, 
            shell=is_shell_command, # Set shell based on input type
            check=True, 
            capture_output=True, # Capture output
            text=True, 
            encoding='utf-8'
        )
        if result.stdout:
            # Limit logging of potentially very long stdout from Python scripts
            # For external tools like gcloud, full stdout might be more useful.
            # Here, we assume python scripts might print a lot.
            stdout_log = result.stdout
            if command_display.startswith("python"):
                 stdout_log_lines = result.stdout.splitlines()
                 if len(stdout_log_lines) > 50: # Log only first 50 lines for python scripts
                     stdout_log = "\n".join(stdout_log_lines[:50]) + "\n... (stdout truncated)"
            logger.info(f"Stdout from '{command_display}':\n{stdout_log}")
        
        # stderr from successful commands (e.g., progress info)
        if result.stderr:
            logger.info(f"Stderr from '{command_display}' (command was successful):\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{command_display}' failed with return code {e.returncode}.")
        if e.stdout:
            logger.error(f"Stdout from failed '{command_display}':\n{e.stdout}")
        if e.stderr:
            logger.error(f"Stderr from failed '{command_display}':\n{e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(f"Command not found (FileNotFoundError) for '{command_display}'. Ensure the program/script and Python (if applicable) are in your PATH or specified correctly.")
        return False
    except Exception as e_gen:
        logger.error(f"An unexpected error occurred while trying to run '{command_display}': {e_gen}")
        return False


if __name__ == "__main__":
    logger.info("--- Main Orchestration Script Started ---")
    
    # Define the commands to run.
    # Each command should be a list of arguments for better security and control,
    # unless shell=True is strictly necessary for that command string.
    # For python scripts, using a list like ['python', './script.py'] is preferred.
    commands = [
        ['python', './manage_sql_dump.py'],            # New first step
        ['python', './convert_sql_to_pkl.py'],
        ['python', './sanity_check_psql_to_pkl.py'],
        ['python', './extract_revision_questions.py']
    ]

    all_successful = True
    for command_args in commands:
        command_display_name = ' '.join(command_args) 
        print(f"\n>>> Running: {command_display_name}") # Also print to console for immediate feedback
        
        if not run_command(command_args):
            print(f"!!! Command {command_display_name} FAILED or did not execute. !!!")
            logger.error(f"Command {command_display_name} failed. Subsequent steps might be affected or skipped.")
            all_successful = False
            # Decide if to break or continue. Let's break on first failure for critical pipeline.
            break 
        else:
            print(f"<<< Command {command_display_name} completed successfully.")


    if all_successful:
        logger.info("--- All commands executed successfully ---")
        print("\n--- All commands executed successfully ---")
    else:
        logger.error("--- One or more commands failed during execution. Pipeline halted. ---")
        print("\n--- One or more commands failed during execution. Pipeline halted. ---")
        exit(1) # Exit with a non-zero code to indicate failure