import subprocess
import os
import logging
from datetime import datetime

# --- Configuration ---
# Google Cloud Project and SQL Instance details
PROJECT_ID = "quiz-app-april-2025"
SQL_INSTANCE_NAME = "quiz-app-db"
DATABASE_NAME = "quiz_db"  # The specific database to export

# GCS Bucket details
GCS_BUCKET_NAME = "export-from-sql"
GCS_EXPORT_PATH = "DB_EXPORT"  # Path within the bucket

# Filename (fixed as per your example, ensure this matches convert_sql_to_pkl.py)
# If you want a dynamic date, uncomment the next two lines and adjust convert_sql_to_pkl.py
# TODAY_STR = datetime.now().strftime("%Y-%m-%d")
# SQL_FILENAME = f"Cloud_SQL_Export_{TODAY_STR}.sql"
SQL_FILENAME = "Cloud_SQL_Export_2025-05-15.sql" # Fixed filename from your example

# Local path where the SQL dump will be downloaded
# Defaults to the current directory where the script is run.
LOCAL_DOWNLOAD_PATH = "." # Or specify a sub-directory e.g., "sql_dumps"

# --- Logger Setup ---
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def run_gcloud_command(command_args, operation_name="gcloud operation"):
    """Runs a gcloud command using subprocess and logs the outcome."""
    logger.info(f"Starting: {operation_name}...")
    logger.info(f"Executing command: {' '.join(command_args)}")
    try:
        # Using shell=False is generally safer if command_args is a list
        result = subprocess.run(command_args, check=True, capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            logger.info(f"{operation_name} STDOUT:\n{result.stdout}")
        if result.stderr: # gcloud often uses stderr for progress/info
            logger.info(f"{operation_name} STDERR:\n{result.stderr}")
        logger.info(f"Successfully completed: {operation_name}.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during {operation_name}.")
        if e.stdout:
            logger.error(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            logger.error(f"STDERR:\n{e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(f"Command not found for {operation_name}. Is 'gcloud' or 'gsutil' in your PATH?")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during {operation_name}: {e}")
        return False

def export_sql_to_gcs():
    """Exports the Cloud SQL database to a GCS bucket."""
    gcs_uri = f"gs://{GCS_BUCKET_NAME}/{GCS_EXPORT_PATH}/{SQL_FILENAME}"
    
    command = [
    "gcloud.cmd", "sql", "export", "sql", # Changed "gcloud" to "gcloud.cmd"
    SQL_INSTANCE_NAME,
    gcs_uri,
    f"--database={DATABASE_NAME}",
    f"--project={PROJECT_ID}",
    "--quiet"
]
    return run_gcloud_command(command, operation_name=f"Export SQL dump to {gcs_uri}")

def download_sql_from_gcs():
    """Downloads the SQL dump from GCS to the local filesystem."""
    gcs_uri = f"gs://{GCS_BUCKET_NAME}/{GCS_EXPORT_PATH}/{SQL_FILENAME}"
    
    # Ensure local download directory exists
    if LOCAL_DOWNLOAD_PATH != "." and not os.path.exists(LOCAL_DOWNLOAD_PATH):
        os.makedirs(LOCAL_DOWNLOAD_PATH, exist_ok=True)
        logger.info(f"Created local directory: {LOCAL_DOWNLOAD_PATH}")

    local_file_destination = os.path.join(LOCAL_DOWNLOAD_PATH, SQL_FILENAME)
    
    command =[
    "gsutil.cmd", "cp", # Changed "gsutil" to "gsutil.cmd"
    gcs_uri,
    local_file_destination
]
    
    # Check if file already exists locally, gsutil cp will overwrite by default.
    if os.path.exists(local_file_destination):
        logger.info(f"Local file {local_file_destination} already exists. It will be overwritten by gsutil cp.")
        
    return run_gcloud_command(command, operation_name=f"Download SQL dump from {gcs_uri} to {local_file_destination}")

def main():
    logger.info("--- SQL Dump Management Script Started ---")
    
    logger.info(f"Target Project: {PROJECT_ID}")
    logger.info(f"Target SQL Instance: {SQL_INSTANCE_NAME}")
    logger.info(f"Target Database: {DATABASE_NAME}")
    logger.info(f"GCS Bucket: gs://{GCS_BUCKET_NAME}/{GCS_EXPORT_PATH}")
    logger.info(f"SQL Filename: {SQL_FILENAME}")
    logger.info(f"Local Download Directory: {os.path.abspath(LOCAL_DOWNLOAD_PATH)}")

    # Step 1: Export SQL to GCS
    if not export_sql_to_gcs():
        logger.error("Failed to export SQL dump to GCS. Aborting.")
        return False

    # Step 2: Download SQL from GCS
    if not download_sql_from_gcs():
        logger.error("Failed to download SQL dump from GCS. Aborting.")
        return False

    logger.info("--- SQL Dump Management Script Finished Successfully ---")
    return True

if __name__ == "__main__":
    if not main():
        # Indicate failure to any calling process
        exit(1)