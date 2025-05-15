# sanity_check_psql_to_pkl.py
import os
import pandas as pd
import glob
import logging # Import logging
import re # For GENERIC_COL_PATTERN

# --- Configuration ---
PICKLE_DIR = "database_pkl_export_from_sql_parse"  # Directory where .pkl files are stored
LOG_FILE_NAME = "sanity_check.log" # Name of the log file
GENERIC_COL_PATTERN = r"^column_\d+$"
ALL_NULL_THRESHOLD = 1.0
HIGH_CARDINALITY_THRESHOLD = 0.95
LOW_CARDINALITY_NON_BOOL_THRESHOLD = 5 # For non-boolean, non-id like columns
POTENTIAL_CONVERSION_SAMPLE_SIZE = 1000
POTENTIAL_CONVERSION_THRESHOLD = 0.90

# --- Logger Setup --- (Will be configured in main)

def check_dataframe(df_path, logger): # Pass logger instance
    """
    Performs sanity checks on a single DataFrame loaded from a pickle file.
    """
    file_name = os.path.basename(df_path)
    issues = []
    warnings = []
    info_notes = [] # For detailed info logging, not necessarily console clutter

    try:
        df = pd.read_pickle(df_path)
        file_size_mb = os.path.getsize(df_path) / (1024 * 1024)
        info_notes.append(f"File: {file_name}, Size: {file_size_mb:.2f} MB")
        info_notes.append(f"Shape: {df.shape} (rows, columns)")

        if df.empty:
            if df.columns.empty and df.index.empty: # No columns, no rows
                warnings.append("DataFrame is completely empty (no rows, no columns).")
            elif df.columns.empty: # Has rows (index) but no columns
                 warnings.append("DataFrame has rows but no columns defined.")
            else: # Has columns but no rows
                info_notes.append("DataFrame is empty (0 rows), but columns are defined.")
            
            # Log collected info before returning for empty DFs
            for note in info_notes: logger.info(f"  {note}")
            for warning in warnings: logger.warning(f"  [WARN] {file_name}: {warning}")
            return issues, warnings # info_notes already logged
        
        # Check for generic column names
        generic_cols_found = [col for col in df.columns if re.match(GENERIC_COL_PATTERN, str(col))]
        if generic_cols_found:
            issues.append(f"Contains generic column names: {generic_cols_found}. Original names might be lost.")

        if not df.empty: # Redundant check, but defensive
            null_summary = df.isnull().mean().sort_values(ascending=False)
            for col, null_percentage in null_summary.items():
                col_dtype = df[col].dtype
                if null_percentage >= ALL_NULL_THRESHOLD:
                    warnings.append(f"Column '{col}' (dtype: {col_dtype}) is entirely NULL/NaN.")
                elif null_percentage > 0:
                    info_notes.append(f"Column '{col}' (dtype: {col_dtype}) has {null_percentage*100:.2f}% NULL/NaN values.")
                
                # Cardinality checks
                num_unique = df[col].nunique(dropna=False) # Include NaNs in unique count for some checks
                total_rows = len(df)

                if total_rows > 0:
                    unique_ratio = num_unique / total_rows
                    # High cardinality (potential IDs, free text)
                    if unique_ratio >= HIGH_CARDINALITY_THRESHOLD and num_unique > 1 : # Avoid flagging single-value high-cardinality
                        # Heuristic to avoid flagging obvious ID columns as just "high cardinality text"
                        if not (str(col).lower().endswith(('_id', 'id', 'pk', 'uuid', 'key')) or df.index.name == col or pd.api.types.is_datetime64_any_dtype(df[col])):
                             info_notes.append(f"Column '{col}' (dtype: {col_dtype}) has high cardinality ({num_unique} unique / {total_rows} rows = {unique_ratio*100:.1f}%). Could be diverse text or specific identifier.")
                    
                    # Low cardinality (potential categorical, boolean-like)
                    # Check for non-boolean types specifically, as booleans naturally have low cardinality
                    is_likely_bool_stored_as_int_or_obj = False
                    if num_unique == 2 and (pd.api.types.is_numeric_dtype(col_dtype) or col_dtype == 'object'):
                        unique_vals = df[col].dropna().unique()
                        if len(unique_vals) == 2 and all(v in [0, 1, True, False, 't', 'f', 'true', 'false', 'yes', 'no', 'Y', 'N'] for v in unique_vals):
                            is_likely_bool_stored_as_int_or_obj = True
                            info_notes.append(f"Column '{col}' (dtype: {col_dtype}) has 2 unique values, potentially boolean-like: {unique_vals[:5]}.")


                    if not is_likely_bool_stored_as_int_or_obj and \
                       (col_dtype == 'object' or pd.api.types.is_numeric_dtype(col_dtype)) and \
                       not pd.api.types.is_bool_dtype(col_dtype) and \
                       num_unique <= LOW_CARDINALITY_NON_BOOL_THRESHOLD and num_unique > 1: # num_unique > 1 to avoid single-value columns
                             info_notes.append(f"Column '{col}' (dtype: {col_dtype}) has low cardinality ({num_unique} unique values). Potentially categorical.")
                
                # Potential type conversion checks for 'object' columns
                if col_dtype == 'object' and null_percentage < 1.0: # Only if not all null
                    # Take a sample for performance, ensure sample is not empty
                    non_null_series = df[col].dropna()
                    if not non_null_series.empty:
                        sample_df = non_null_series.sample(min(POTENTIAL_CONVERSION_SAMPLE_SIZE, len(non_null_series)), random_state=1)
                        
                        # Check for numeric
                        try:
                            numeric_converted = pd.to_numeric(sample_df, errors='coerce')
                            if numeric_converted.notnull().mean() >= POTENTIAL_CONVERSION_THRESHOLD:
                                warnings.append(f"Object column '{col}' might be numeric. {numeric_converted.notnull().mean()*100:.0f}% of a non-null sample converted successfully.")
                        except Exception: pass # Ignore errors during this speculative check
                        
                        # Check for datetime
                        try:
                            # Avoid overly aggressive datetime parsing for simple integers/floats
                            looks_like_date_strings = sample_df.astype(str).str.contains(r'[\-/: ]').sum() > (len(sample_df) * 0.1) # Heuristic: at least 10% have date-like chars
                            if looks_like_date_strings:
                                datetime_converted = pd.to_datetime(sample_df, errors='coerce')
                                if datetime_converted.notnull().mean() >= POTENTIAL_CONVERSION_THRESHOLD:
                                    warnings.append(f"Object column '{col}' might be datetime. {datetime_converted.notnull().mean()*100:.0f}% of a non-null sample converted successfully.")
                        except Exception: pass # Ignore errors

        info_notes.append(f"Data types summary:\n{df.dtypes.value_counts().to_string()}")

    except ModuleNotFoundError as e:
        issues.append(f"ERROR loading {file_name}: A module required by the pickled object was not found. Error: {e}")
    except EOFError:
        issues.append(f"ERROR loading {file_name}: File is corrupted or not a valid pickle file (EOFError).")
    except Exception as e:
        issues.append(f"ERROR loading or processing {file_name}: {e}")

    # Log collected info/warnings/issues from this function
    for note in info_notes: logger.info(f"  {note}")
    # Prefix warnings and issues with filename for clarity when multiple files are processed
    for warning in warnings: logger.warning(f"  [WARN] {file_name}: {warning}")
    for issue in issues: logger.error(f"  [ISSUE] {file_name}: {issue}")

    return issues, warnings # info_notes already logged

def main():
    # --- Logger Setup ---
    # Ensure PICKLE_DIR exists before trying to create log file in it
    if not os.path.exists(PICKLE_DIR):
        # If PICKLE_DIR doesn't exist, we might not be able to create it if script lacks permissions.
        # Log to current dir or print error and exit.
        print(f"Error: PICKLE_DIR '{PICKLE_DIR}' does not exist. Sanity check cannot run or log results there.")
        # Fallback: try to create it. If it fails, exit.
        try:
            os.makedirs(PICKLE_DIR, exist_ok=True)
            print(f"Info: PICKLE_DIR '{PICKLE_DIR}' was created.")
        except OSError as e:
            print(f"Error: Failed to create PICKLE_DIR '{PICKLE_DIR}': {e}. Exiting.")
            return

    log_file_path = os.path.join(PICKLE_DIR, LOG_FILE_NAME)
    
    logger = logging.getLogger('SanityChecker')
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]: # Remove any existing handlers
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    fh = logging.FileHandler(log_file_path, mode='w')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Add StreamHandler for console output
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO) # Or logging.WARNING to be less verbose on console
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    logger.info(f"--- Sanity Check for Pickle Files in '{PICKLE_DIR}' ---")
    
    pkl_files = glob.glob(os.path.join(PICKLE_DIR, "*.pkl"))

    if not pkl_files:
        logger.info(f"No .pkl files found in '{PICKLE_DIR}'.")
        return

    total_issues = 0
    total_warnings = 0

    for pkl_file_path in sorted(pkl_files):
        logger.info(f"\n--- Checking: {os.path.basename(pkl_file_path)} ---")
        # check_dataframe now logs its details directly
        issues_current, warnings_current = check_dataframe(pkl_file_path, logger) 
        
        total_warnings += len(warnings_current)
        total_issues += len(issues_current)
        
        if not issues_current and not warnings_current:
            logger.info(f"  [OK] {os.path.basename(pkl_file_path)}: No immediate issues or warnings detected based on checks.")

    logger.info("\n--- Sanity Check Summary ---")
    logger.info(f"Total files checked: {len(pkl_files)}")
    logger.info(f"Total ISSUES reported: {total_issues}")
    logger.info(f"Total WARNINGS reported: {total_warnings}")
    if total_issues > 0 or total_warnings > 0:
        logger.info("Review the [ISSUE] and [WARN] messages in the log and console output above carefully.")
    else:
        logger.info("All files passed basic sanity checks without raising specific issues or warnings.")
    
    # Ensure all handlers are closed
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

if __name__ == "__main__":
    main()