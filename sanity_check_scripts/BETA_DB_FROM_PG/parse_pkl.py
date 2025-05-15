# parse_sql_to_pkl.py
import os
import re
import pandas as pd
import csv
from io import StringIO
import logging # Import logging

# --- Configuration ---
SQL_FILE_PATH = "Cloud_SQL_Export_2025-05-15.sql"  # <--- SET YOUR SQL FILE PATH HERE
OUTPUT_DIR = "database_pkl_export_from_sql_parse"
SCHEMA_NAME = "public" # Assuming tables are in the 'public' schema
LOG_FILE_NAME = "parser.log" # Name of the log file

# --- Regex Patterns (same as before) ---
create_table_pattern = re.compile(
    r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(?:\"?(?:[a-zA-Z0-9_]+)\"?\.)?\"?([a-zA-Z0-9_]+)\"?\s*\((.*?)\)\s*;",
    re.IGNORECASE | re.DOTALL
)
copy_from_stdin_pattern = re.compile(
    r"COPY\s+(?:\"?(?:[a-zA-Z0-9_]+)\"?\.)?\"?([a-zA-Z0-9_]+)\"?\s*\((.*?)\)\s+FROM\s+stdin;",
    re.IGNORECASE
)
copy_no_cols_from_stdin_pattern = re.compile(
    r"COPY\s+(?:\"?(?:[a-zA-Z0-9_]+)\"?\.)?\"?([a-zA-Z0-9_]+)\"?\s+FROM\s+stdin;",
    re.IGNORECASE
)
insert_into_pattern = re.compile(
    r"INSERT INTO\s+(?:\"?{}\"?\.)?\"?([a-zA-Z0-9_]+)\"?\s*(?:\((.*?)\))?\s*VALUES".format(re.escape(SCHEMA_NAME)),
    re.IGNORECASE
)
values_pattern = re.compile(r"\((.*?)\)(?:,\s*\(.*?\))?;", re.DOTALL)


def parse_value(value_str): # Same as before
    value_str = str(value_str).strip()
    if value_str.upper() == "NULL": return None
    if value_str == "\\N": return None
    if value_str.startswith("'") and value_str.endswith("'"):
        return value_str[1:-1].replace("''", "'")
    if value_str.lower() in ('true', 't'): return True
    if value_str.lower() in ('false', 'f'): return False
    try: return int(value_str)
    except ValueError:
        try: return float(value_str)
        except ValueError: return value_str

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_file_path = os.path.join(OUTPUT_DIR, LOG_FILE_NAME)
    
    logger = logging.getLogger('SQLParser')
    logger.setLevel(logging.INFO)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    fh = logging.FileHandler(log_file_path, mode='w')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Add StreamHandler for console output
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO) # You can set this to logging.WARNING to only see warnings/errors on console
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    logger.info("--- SQL Parser Script Started ---")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"SQL file to process: {SQL_FILE_PATH}")

    if not os.path.exists(SQL_FILE_PATH):
        logger.error(f"SQL file not found at {SQL_FILE_PATH}")
        return

    tables_data = {}
    current_copy_table_name = None
    current_copy_columns_from_header = None
    parsing_copy_data = False

    logger.info(f"Processing SQL file: {SQL_FILE_PATH}...")

    try:
        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            sql_content_chunk = ""
            for line_number, line in enumerate(f, 1):
                line_strip = line.strip()

                if parsing_copy_data:
                    if line_strip == "\\.":
                        logger.info(f"  Finished COPY data for table: {current_copy_table_name}")
                        parsing_copy_data = False
                        current_copy_table_name = None
                        current_copy_columns_from_header = None
                    else:
                        try:
                            row_data_str = line.rstrip('\n')
                            # Use csv.reader for robust parsing of tab-delimited data, handling quotes
                            row_values_str = next(csv.reader(StringIO(row_data_str), delimiter='\t', quotechar='"'))
                            # Convert "\\N" to None, other values are kept as strings for now
                            row_values = [None if val_str == "\\N" else val_str for val_str in row_values_str]
                            tables_data[current_copy_table_name]["rows"].append(row_values)
                        except Exception as e:
                            logger.warning(f"  Could not parse COPY data line {line_number} for table {current_copy_table_name}: {e} - Line: '{line_strip[:100]}...'")
                    continue

                sql_content_chunk += line
                if not line_strip.endswith(';'):
                    if len(sql_content_chunk) > 1000000: # Safety break for very long non-statements
                        logger.warning(f"Resetting long SQL chunk at line {line_number} not ending with ';'")
                        sql_content_chunk = ""
                    continue

                statement_to_process = sql_content_chunk.strip()
                sql_content_chunk = "" # Reset for next statement

                create_match = create_table_pattern.search(statement_to_process)
                if create_match:
                    table_name = create_match.group(1).strip('"')
                    columns_block_content = create_match.group(2).strip()
                    
                    # Improved column parsing from CREATE TABLE statement
                    cols = []
                    # Remove comments
                    temp_block = re.sub(r"/\*.*?\*/", "", columns_block_content, flags=re.DOTALL) # multiline comments
                    temp_block = re.sub(r"--.*?(\n|$)", "\n", temp_block) # single line comments
                    temp_block = temp_block.replace('\n', ' ').strip() # Normalize whitespace

                    # Split by comma, respecting parentheses for constraints/types
                    potential_defs = []
                    balance = 0
                    current_def = ""
                    for char in temp_block:
                        current_def += char
                        if char == '(': balance += 1
                        elif char == ')': balance -= 1
                        elif char == ',' and balance == 0:
                            potential_defs.append(current_def[:-1].strip())
                            current_def = ""
                    if current_def: # Add the last definition
                        potential_defs.append(current_def.strip())
                    
                    for p_def in potential_defs:
                        p_def_stripped = p_def.strip()
                        # Skip if it's likely a constraint definition or other non-column def
                        if not p_def_stripped or \
                           p_def_stripped.upper().startswith(("CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK", "LIKE")): # Added LIKE for table inheritance
                            continue
                        
                        # Extract column name (first word, handling quotes)
                        name_match = re.match(r"^\s*(?:\"([^\"]+)\"|([a-zA-Z_][a-zA-Z0-9_]*))", p_def_stripped)
                        if name_match:
                            col_name = name_match.group(1) or name_match.group(2) # group(1) for quoted, group(2) for unquoted
                            cols.append(col_name)
                    
                    if cols:
                        if table_name not in tables_data:
                            tables_data[table_name] = {"columns": cols, "rows": []}
                        else: # Table might have been created by COPY first, or to update columns
                            # Prioritize CREATE TABLE columns if more comprehensive
                            if len(cols) > len(tables_data[table_name]["columns"]):
                                 tables_data[table_name]["columns"] = cols
                        logger.info(f"  Found/Updated schema for table: {table_name} with {len(cols)} columns: {cols[:5]}...")
                    else:
                        logger.warning(f"  Could not parse columns for table {table_name} from CREATE statement.")
                    continue

                copy_match = copy_from_stdin_pattern.search(statement_to_process)
                if not copy_match: # Try pattern without explicit column list
                    copy_match = copy_no_cols_from_stdin_pattern.search(statement_to_process)

                if copy_match:
                    current_copy_table_name = copy_match.group(1).strip('"')
                    current_copy_columns_from_header = []
                    if len(copy_match.groups()) > 1 and copy_match.group(2): # If columns are listed in COPY
                        cols_str_from_copy = copy_match.group(2)
                        try:
                            # Use csv.reader to handle quoted column names properly
                            reader = csv.reader(StringIO(cols_str_from_copy), skipinitialspace=True)
                            parsed_cols = next(reader)
                            current_copy_columns_from_header = [col.strip().strip('"') for col in parsed_cols]
                        except Exception as e:
                            logger.warning(f"  Could not parse column list from COPY statement for {current_copy_table_name}: '{cols_str_from_copy}' - {e}")
                    
                    if current_copy_table_name not in tables_data:
                        tables_data[current_copy_table_name] = {"columns": current_copy_columns_from_header, "rows": []}
                        logger.info(f"  Starting COPY for new table: {current_copy_table_name} (cols from COPY: {current_copy_columns_from_header[:5]}...)")
                    else:
                        # If table exists but columns weren't parsed from CREATE, use COPY columns
                        if not tables_data[current_copy_table_name]["columns"] and current_copy_columns_from_header:
                            tables_data[current_copy_table_name]["columns"] = current_copy_columns_from_header
                            logger.info(f"  Starting COPY for table: {current_copy_table_name}, using columns from COPY header: {current_copy_columns_from_header[:5]}...")
                        else:
                            logger.info(f"  Starting COPY for existing table: {current_copy_table_name} (cols from CREATE: {tables_data[current_copy_table_name]['columns'][:5]}...)")
                    parsing_copy_data = True
                    continue

                insert_match = insert_into_pattern.search(statement_to_process)
                if insert_match:
                    table_name = insert_match.group(1).strip('"')
                    if table_name in tables_data: # Only process if we know the table
                        values_data_match = values_pattern.search(statement_to_process[insert_match.end():])
                        if values_data_match:
                            values_str = values_data_match.group(1) # Get content inside the first (...)
                            try:
                                # Use csv.reader to handle commas within quoted strings, etc.
                                parsed_values_str = next(csv.reader(StringIO(values_str), skipinitialspace=True))
                                row_values = [parse_value(v) for v in parsed_values_str]
                                tables_data[table_name]["rows"].append(row_values)
                            except Exception as e:
                                logger.warning(f"  Could not parse INSERT VALUES for table {table_name} on line {line_number}: {e} - Values: '{values_str[:100]}...'")
                    continue
        logger.info("Finished processing SQL file. Converting to DataFrames and pickling...")

        for table_name, data in tables_data.items():
            table_cols = data["columns"]
            table_rows = data["rows"]

            if not table_rows and not table_cols: # Completely empty definition and data
                logger.info(f"  Skipping table {table_name}: No columns and no data rows.")
                continue
            
            logger.info(f"Processing DataFrame for table: {table_name} ({len(table_rows)} rows)")

            if table_rows: # Only check column consistency if there's data
                num_data_cols = len(table_rows[0]) if table_rows else 0
                if not table_cols: # No schema columns found (CREATE/COPY)
                    logger.warning(f"  No schema columns defined for {table_name}. Generating {num_data_cols} generic column names based on first data row.")
                    table_cols = [f"column_{i}" for i in range(num_data_cols)]
                elif len(table_cols) != num_data_cols:
                    logger.warning(f"  Column count mismatch for table {table_name}!")
                    logger.warning(f"    Parsed schema/COPY columns ({len(table_cols)}): {table_cols[:10]}...")
                    logger.warning(f"    Actual data columns in first row ({num_data_cols}): {str(table_rows[0][:10] if table_rows else 'N/A')}...")
                    
                    # Heuristic: if schema has more, trust schema. If data has more, something is wrong.
                    # For now, let's try to be robust: if counts mismatch, and schema cols exist, try with schema cols.
                    # Pandas will raise error if counts don't match data rows, which is a good indicator.
                    # If schema is shorter, we might lose data. If longer, there will be NaNs.
                    # The safest is to use generic names if mismatch to avoid data loss from wrong schema.
                    logger.warning(f"    ADJUSTING: Using generic column names based on actual data column count ({num_data_cols}) due to mismatch.")
                    table_cols = [f"column_{i}" for i in range(num_data_cols)]
            
            # If after all checks, still no columns but there are rows
            if not table_cols and table_rows : # Should be rare if above logic works
                # This can happen if table_rows is not empty, but all its elements are empty lists
                if any(table_rows) : # Check if there's any actual data
                     # Determine max columns from actual data, robustly
                     num_data_cols_from_any_row = max(len(r) for r in table_rows if r) if any(r for r in table_rows) else 0
                     if num_data_cols_from_any_row > 0:
                        logger.warning(f"  No schema columns, but non-empty data rows found for {table_name}. Generating {num_data_cols_from_any_row} generic names.")
                        table_cols = [f"column_{i}" for i in range(num_data_cols_from_any_row)]
                     else: # Empty rows like [[]]
                        logger.info(f"  Skipping table {table_name}: Data rows detected but they appear empty or malformed, and no columns defined.")
                        continue
            
            if not table_cols and not table_rows: # Final check, e.g. after empty rows were skipped
                 logger.info(f"  Skipping table {table_name}: Still no columns and no data rows after checks.")
                 continue


            try:
                # df_columns will be None if no cols and no rows, pandas handles this by creating empty DF.
                # If rows exist but no cols, pandas needs columns=None or explicit col list.
                df_columns = table_cols if table_cols else (None if not table_rows else [])


                # Ensure all rows have the same number of columns as df_columns, pad if necessary
                # This is crucial if some COPY lines had fewer fields.
                expected_col_count = len(df_columns) if df_columns is not None else 0
                if table_rows and expected_col_count > 0:
                    processed_rows = []
                    for i, r in enumerate(table_rows):
                        if len(r) < expected_col_count:
                            # logger.debug(f"  Padding row {i} for table {table_name}. Has {len(r)}, expected {expected_col_count}")
                            processed_rows.append(r + [None] * (expected_col_count - len(r)))
                        elif len(r) > expected_col_count:
                            # logger.debug(f"  Truncating row {i} for table {table_name}. Has {len(r)}, expected {expected_col_count}")
                            processed_rows.append(r[:expected_col_count])
                        else:
                            processed_rows.append(r)
                    table_rows_for_df = processed_rows
                else:
                    table_rows_for_df = table_rows


                df = pd.DataFrame(table_rows_for_df, columns=df_columns)
                
                # Attempt type conversion and NULL value standardization
                for col in df.columns:
                    # First, standardize various null representations to None (np.nan for Pandas)
                    if df[col].dtype == 'object':
                        # Replace common string nulls before numeric conversion
                        df[col] = df[col].replace({'': None, 'NULL': None, '\\N': None, 'null':None})
                    
                    # Attempt numeric conversion for non-object or fully None columns
                    try:
                        # pd.to_numeric will convert to float if NaNs are present, or int if possible
                        df[col] = pd.to_numeric(df[col], errors='raise')
                    except (ValueError, TypeError):
                        # If conversion to numeric fails, it's likely a string, datetime, or mixed type.
                        # Keep as object, further specific conversions (like datetime) could be added if needed.
                        pass # Keep as object or original type
                
                pkl_file_path = os.path.join(OUTPUT_DIR, f"{table_name}.pkl")
                df.to_pickle(pkl_file_path, protocol=4)
                logger.info(f"  Saved {table_name} ({len(df)} rows, {len(df.columns)} cols) to {pkl_file_path}")

            except Exception as e:
                logger.error(f"  Error creating DataFrame or pickling for table {table_name}: {e}")
                logger.error(f"    Final columns used: {str(df_columns)[:200]}...")
                if table_rows: logger.error(f"    First data row example: {str(table_rows[0][:10])[:200] if table_rows[0] else 'N/A'}...")
                logger.error(f"    Number of rows: {len(table_rows)}, Number of columns defined: {len(df_columns) if df_columns is not None else 'None'}")


        logger.info("SQL parsing to .pkl files attempt complete.")
        logger.info("IMPORTANT: Review the .pkl files and parser.log carefully. This direct parsing method may have inaccuracies.")
        logger.info("If 'WARNING: Column count mismatch' or 'generic column names' occurred, original column names might be lost for those tables.")

    except Exception as e:
        logger.exception("An unexpected error occurred during the parsing process:")
    finally:
        # Ensure all handlers are closed
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

if __name__ == "__main__":
    main()