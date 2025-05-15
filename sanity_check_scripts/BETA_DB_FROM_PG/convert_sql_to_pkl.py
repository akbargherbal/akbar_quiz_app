import os
import re
import pandas as pd
import logging
import csv
from io import StringIO

# --- Configuration ---
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
# Define states for the parsing state machine
STATE_SCANNING_FOR_COPY = 0
STATE_READING_COPY_DATA = 1

def setup_logger(log_file_path):
    """Sets up a logger that writes to a file and (optionally) to the console."""
    logger = logging.getLogger('SQLDumpParser')
    logger.setLevel(logging.INFO) # Set base level for the logger

    # Prevent duplicate handlers if this function is called multiple times
    if logger.hasHandlers():
        for handler in logger.handlers[:]: # Iterate over a copy
            handler.close()
            logger.removeHandler(handler)
            
    # File Handler - always INFO level
    fh = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console Handler - you can set a higher level for less console noise if desired
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO) # e.g., logging.WARNING to see only warnings and errors on console
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def sanitize_identifier(identifier):
    """Removes surrounding quotes from an SQL identifier."""
    return identifier.strip().strip('"')

def generate_safe_filename(full_table_name_str):
    """
    Generates a safe filename from a potentially schema-qualified and quoted table name.
    Example: 'public."My Table"' -> 'public_My_Table.pkl'
             '"My_Table"' -> 'My_Table.pkl'
             'mytable' -> 'mytable.pkl'
    """
    # This regex finds words or quoted strings (handles escaped quotes inside if any)
    parts = re.findall(r'"(?:[^"\\]|\\.)+"|\w+', full_table_name_str)
    sanitized_parts = [sanitize_identifier(p) for p in parts]
    base_name = "_".join(sanitized_parts)
    if not base_name: # Handle empty or very odd names
        base_name = "unknown_table"
    return f"{base_name}.pkl"

def parse_copy_column_list(columns_str, logger):
    """
    Parses the column list string from a COPY statement.
    Handles quoted column names that might contain commas.
    """
    if not columns_str.strip():
        logger.debug("Empty column string received for parsing by parse_copy_column_list.") # Changed to debug from warning
        return []
    sio = StringIO(columns_str)
    # Use csv.reader to handle quotes correctly
    reader = csv.reader(sio, skipinitialspace=True)
    try:
        parsed_cols = next(reader) # The column list is one "row"
        return [sanitize_identifier(col) for col in parsed_cols]
    except StopIteration:
        logger.warning(f"Unexpected StopIteration (empty content?) parsing column string: '{columns_str}'")
        return []
    except Exception as e:
        logger.error(f"Error parsing column string '{columns_str}': {e}. Falling back to simple split.")
        # Fallback to simple split, though it may be incorrect for complex names
        return [sanitize_identifier(c.strip()) for c in columns_str.split(',')]

def _process_and_save_df(rows, table_name_sql, columns_from_copy_header, output_dir, logger, current_processed_count):
    """
    Helper function to process rows into a DataFrame, perform type conversions, and save to pickle.
    Manages generic column name generation if columns_from_copy_header is empty.
    Returns the updated processed_table_count.
    """
    if not rows:
        logger.info(f"  No data rows found for table '{table_name_sql}' in this COPY block.")
        return current_processed_count

    df_columns = columns_from_copy_header
    if not df_columns:  # True if COPY statement had no explicit columns, or columns_from_copy_header was []
        # Infer from first data row
        first_row_col_count = len(rows[0]) if rows and rows[0] else 0
        if first_row_col_count > 0:
            df_columns = [f"column_{i}" for i in range(first_row_col_count)]
            logger.warning(
                f"  Table '{table_name_sql}' data read from COPY statement without explicit column list or with an empty one. "
                f"Generated {first_row_col_count} generic column names: {df_columns[:5]}..."
            )
        else:
            logger.warning(
                f"  Table '{table_name_sql}' from COPY statement without explicit/valid columns, "
                f"and no data or empty first row to infer column count. Skipping DataFrame creation."
            )
            return current_processed_count

    if not df_columns: # Should be caught by above logic if rows exist. Defensive.
        logger.error(f"  Critical error: Could not determine columns for table '{table_name_sql}' with {len(rows)} rows. Skipping save.")
        return current_processed_count

    try:
        df = pd.DataFrame(rows, columns=df_columns)
        logger.info(f"  Created DataFrame for '{table_name_sql}' with shape {df.shape}")

        # Type conversion heuristics
        for col_name in df.columns:
            original_non_nulls = df[col_name].notna().sum()
            if original_non_nulls == 0: # Skip if all null
                continue

            # Attempt numeric conversion
            try:
                numeric_series = pd.to_numeric(df[col_name], errors='coerce')
                # Convert if a significant portion (e.g., >80%) of original non-nulls can be numeric
                if numeric_series.notna().sum() > 0.8 * original_non_nulls:
                    df[col_name] = numeric_series
                    logger.debug(f"    Converted column '{col_name}' to numeric.")
                    continue 
            except Exception as e_num:
                logger.debug(f"    Numeric conversion attempt failed for column '{col_name}': {e_num}")
            
            # Attempt datetime conversion (if not successfully numeric)
            if df[col_name].dtype == 'object': # Only for object types
                try:
                    sample_size = min(100, len(df[col_name]))
                    # Ensure sample can be taken from non-NA values
                    non_na_series = df[col_name].dropna()
                    if len(non_na_series) == 0: continue

                    sample_for_dt_check = non_na_series.sample(n=min(sample_size, len(non_na_series)), random_state=1)
                    
                    if not sample_for_dt_check.empty and \
                       sample_for_dt_check.astype(str).str.contains(r'\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[AP]M', regex=True, na=False).mean() > 0.5:
                        datetime_series = pd.to_datetime(df[col_name], errors='coerce')
                        if datetime_series.notna().sum() > 0.8 * original_non_nulls:
                            df[col_name] = datetime_series
                            logger.debug(f"    Converted column '{col_name}' to datetime.")
                except Exception as e_dt:
                    logger.debug(f"    Datetime conversion attempt failed for column '{col_name}': {e_dt}")
        
        pkl_filename = generate_safe_filename(table_name_sql)
        pkl_file_path = os.path.join(output_dir, pkl_filename)
        df.to_pickle(pkl_file_path)
        logger.info(f"  Saved {pkl_filename} ({len(df)} rows, {len(df.columns)} cols) to {output_dir}")
        current_processed_count += 1
    except Exception as e:
        logger.error(f"  Error processing DataFrame for table '{table_name_sql}': {e}", exc_info=True)
    
    return current_processed_count

def sql_dump_to_pickle_improved(sql_path, output_dir="database_pkl_export_from_sql_parse"):
    """
    Improved extraction of table data from PostgreSQL SQL dump file to pickle files.
    Processes COPY statements line by line with better parsing and logging.
    Handles COPY with and without explicit column lists.
    """
    os.makedirs(output_dir, exist_ok=True)
    log_file_path = os.path.join(output_dir, "parser.log")
    logger = setup_logger(log_file_path)

    logger.info(f"Starting processing of PostgreSQL dump: {sql_path}")
    logger.info(f"Output directory: {output_dir}")

    # Regex to find the start of a COPY statement with an explicit column list
    # Group 1: Full table name (possibly schema.table, possibly quoted)
    # Group 2: Column list string
    copy_header_with_cols_pattern = re.compile(
        r"COPY\s+((?:\"(?:[^\"\\]|\\.)+\"|[\w\.]+)+)\s*\((.*?)\)\s+FROM\s+stdin;",
        re.IGNORECASE
    )
    # Regex for COPY statement without an explicit column list
    # Group 1: Full table name
    copy_header_no_cols_pattern = re.compile(
        r"COPY\s+((?:\"(?:[^\"\\]|\\.)+\"|[\w\.]+)+)\s+FROM\s+stdin;",
        re.IGNORECASE
    )

    current_state = STATE_SCANNING_FOR_COPY
    current_table_name_sql = None
    current_columns = [] # Parsed from COPY (cols...) or remains [] for generic
    current_rows = []
    processed_table_count = 0
    line_num = 0

    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_num += 1
                stripped_line = line.strip()

                if current_state == STATE_SCANNING_FOR_COPY:
                    match_with_cols = copy_header_with_cols_pattern.match(stripped_line)
                    match_no_cols = None
                    if not match_with_cols:
                        match_no_cols = copy_header_no_cols_pattern.match(stripped_line)

                    if match_with_cols:
                        current_table_name_sql = match_with_cols.group(1)
                        columns_str = match_with_cols.group(2)
                        logger.info(f"Found COPY statement (with columns spec) for table '{current_table_name_sql}' on line {line_num}")
                        current_columns = parse_copy_column_list(columns_str, logger)
                        
                        if not current_columns:
                            # This implies an empty list like "COPY table () FROM stdin;" or a parsing error
                            if not columns_str.strip():
                                logger.warning(f"Empty column list specified in COPY statement for table '{current_table_name_sql}'. "
                                               "This block will be processed, and generic column names might be used if data exists.")
                                # current_columns remains [], generic names will be applied if data exists.
                            else: # Non-empty columns_str but parsing failed
                                logger.warning(f"Could not parse columns from COPY (with columns) statement for table '{current_table_name_sql}'. "
                                               f"Columns string: '{columns_str}'. Skipping this COPY block.")
                                current_table_name_sql = None # Reset
                                continue # to next line
                    
                    elif match_no_cols:
                        current_table_name_sql = match_no_cols.group(1)
                        logger.info(f"Found COPY statement (no columns specified) for table '{current_table_name_sql}' on line {line_num}")
                        current_columns = [] # Signifies no explicit columns / use generic

                    # If either matched and set up current_table_name_sql:
                    if current_table_name_sql: # Check if table name was set (i.e., a COPY statement was found and not skipped)
                        current_rows = []
                        current_state = STATE_READING_COPY_DATA
                        if current_columns: 
                             logger.debug(f"  Columns specified: {current_columns}")
                        else:
                             logger.debug(f"  No columns specified in COPY statement or an empty list was provided; will attempt to use generic column names if data exists.")
                        logger.debug(f"  Switching to state STATE_READING_COPY_DATA")

                elif current_state == STATE_READING_COPY_DATA:
                    if stripped_line == "\\.":
                        logger.info(f"  End of data for table '{current_table_name_sql}' on line {line_num}.")
                        
                        processed_table_count = _process_and_save_df(
                            current_rows, current_table_name_sql, current_columns, 
                            output_dir, logger, processed_table_count
                        )
                        
                        current_state = STATE_SCANNING_FOR_COPY
                        current_table_name_sql = None
                        current_columns = [] 
                        current_rows = [] # Clear for next table
                    else:
                        # This is a data line for the current table
                        try:
                            raw_values = line.rstrip('\n\r').split('\t')
                            values = [None if val == '\\N' else val for val in raw_values]
                            
                            # Column count validation
                            if not current_columns and not current_rows: # First data row for a COPY w/o explicit cols
                                # No validation yet, this row sets the standard for subsequent rows.
                                pass
                            elif not current_columns and current_rows: # Subsequent data row for COPY w/o explicit cols
                                expected_len = len(current_rows[0])
                                if len(values) != expected_len:
                                    logger.warning(f"    Line {line_num}: Data row column count mismatch for table '{current_table_name_sql}' (COPY w/o explicit columns). "
                                                   f"Expected {expected_len} (based on first data row), got {len(values)}. "
                                                   f"Line content (first 100 chars): '{line[:100]}...' Skipping this row.")
                                    continue
                            elif current_columns and len(values) != len(current_columns): # COPY w/ explicit cols
                                logger.warning(f"    Line {line_num}: Column count mismatch for table '{current_table_name_sql}'. "
                                               f"Expected {len(current_columns)} ('{','.join(current_columns)}'), got {len(values)}. "
                                               f"Line content (first 100 chars): '{line[:100]}...' Skipping this row.")
                                continue
                            current_rows.append(values)
                        except Exception as e:
                             logger.warning(f"    Error parsing data line {line_num} for table '{current_table_name_sql}': {e}. Line: '{stripped_line[:100]}...'")

        if current_state == STATE_READING_COPY_DATA and current_table_name_sql:
            logger.warning(f"SQL file ended unexpectedly while reading data for table '{current_table_name_sql}'. "
                           "Data for this table might be incomplete. Attempting to process buffered rows.")
            processed_table_count = _process_and_save_df(
                current_rows, current_table_name_sql, current_columns, 
                output_dir, logger, processed_table_count
            )

        if processed_table_count > 0:
            logger.info(f"\nSuccessfully processed and saved {processed_table_count} tables.")
        else:
            logger.warning("\nNo tables were processed or saved. Check if the SQL file contains 'COPY ... FROM stdin;' statements and corresponding data.")
        
        logger.info("Processing complete!")

    except FileNotFoundError:
        logger.error(f"SQL dump file not found: {sql_path}")
    except Exception as e:
        logger.error(f"An unexpected critical error occurred: {e}", exc_info=True)

    return processed_table_count

# Example usage:
if __name__ == "__main__":
    # Create a dummy SQL file for testing if needed
    # with open("dummy_test.sql", "w", encoding='utf-8') as f:
    #     f.write("-- Test with explicit columns\n")
    #     f.write("COPY public.users (id, name, email) FROM stdin;\n")
    #     f.write("1\tAlice\t\\N\n")
    #     f.write("2\tBob\tbob@example.com\n")
    #     f.write("3\t\"Charlie, Jr.\"\tcharlie@test.com\n")
    #     f.write("\\.\n")
    #     f.write("\n-- Test without explicit columns\n")
    #     f.write("COPY public.products FROM stdin;\n")
    #     f.write("P1\tLaptop\t1200.00\n")
    #     f.write("P2\tMouse\t25.50\n")
    #     f.write("\\.\n")
    #     f.write("\n-- Test with schema and quoted table name, no columns\n")
    #     f.write("COPY \"another_Schema\".\"Quoted Table\" FROM stdin;\n")
    #     f.write("val1\tval2\n")
    #     f.write("\\.\n")
    #     f.write("\n-- Test with empty column list (should use generic names or skip based on data)\n")
    #     f.write("COPY public.emptylist_test () FROM stdin;\n")
    #     f.write("data1\tdata2\n") # This data would lead to generic names if processed
    #     f.write("\\.\n")
    #     f.write("\n-- Test with empty column list and no data (should skip df creation)\n")
    #     f.write("COPY public.emptylist_nodata_test () FROM stdin;\n")
    #     f.write("\\.\n")

    # sql_dump_to_pickle_improved("dummy_test.sql", output_dir="dummy_output")
    
    sql_file = "Cloud_SQL_Export_2025-05-15.sql" 
    if os.path.exists(sql_file):
        sql_dump_to_pickle_improved(sql_file)
    else:
        # Fallback for testing if main file not present
        dummy_sql_file = "dummy_test_main.sql"
        print(f"Test SQL file '{sql_file}' not found. Creating and using '{dummy_sql_file}' for demonstration.")
        with open(dummy_sql_file, "w", encoding='utf-8') as f:
            f.write("COPY public.users (id, name, email) FROM stdin;\n")
            f.write("1\tAlice\t\\N\n")
            f.write("2\tBob\tbob@example.com\n")
            f.write("\\.\n")
            f.write("COPY public.items FROM stdin;\n")
            f.write("itemA\t10\n")
            f.write("itemB\t20\n")
            f.write("\\.\n")
        sql_dump_to_pickle_improved(dummy_sql_file, output_dir="dummy_output_main")