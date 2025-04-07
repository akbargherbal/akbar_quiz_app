"""
Example script to demonstrate importing a quiz bank using the management command.
This file should be placed in src/ directory.
"""

import os
import sys
import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser(description='Import quiz data from a CSV or Excel file')
    parser.add_argument('file_path', type=str, help='Path to the CSV or Excel file')
    parser.add_argument('--preview', action='store_true', help='Preview the data without importing')
    args = parser.parse_args()
    
    file_path = args.file_path
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return 1
        
    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Load data based on file extension
    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext in ['.pkl', '.pickle']:
            df = pd.read_pickle(file_path)
        else:
            print(f"Error: Unsupported file format {file_ext}. Please use CSV, Excel, or Pickle files.")
            return 1
            
        # Display preview of the data
        print(f"\nLoaded {len(df)} rows from {file_path}")
        print("\nColumn names:")
        for col in df.columns:
            print(f"  - {col}")
            
        print("\nFirst 5 rows sample:")
        print(df.head().to_string())
        
        # If preview only, stop here
        if args.preview:
            print("\nPreview completed. Use without --preview flag to perform the actual import.")
            return 0
            
        # Check for required columns
        required_columns = ['text', 'options', 'answerIndex']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            # Check for alternative column names
            if 'question_text' in df.columns and 'text' in missing_columns:
                missing_columns.remove('text')
            if 'correct_answer' in df.columns and 'answerIndex' in missing_columns:
                missing_columns.remove('answerIndex')
                
        if missing_columns:
            print(f"\nError: Missing required columns: {', '.join(missing_columns)}")
            print("Please ensure the file has the required columns or proper alternatives.")
            return 1
            
        # Check options format
        if 'options' in df.columns:
            sample_options = df['options'].iloc[0]
            print(f"\nOptions format sample: {sample_options}")
            
            if isinstance(sample_options, str):
                print("Note: Options appear to be in string format. The import will attempt to parse them.")
            
        # Look for topic column - this will help with import strategy
        has_topics = False
        topic_column = None
        for possible_column in ['topic', 'category', 'subject']:
            if possible_column in df.columns:
                has_topics = True
                topic_column = possible_column
                unique_topics = df[topic_column].dropna().unique()
                print(f"\nFound {len(unique_topics)} unique topics in column '{topic_column}':")
                for topic in unique_topics[:10]:  # Show first 10
                    print(f"  - {topic}")
                if len(unique_topics) > 10:
                    print(f"  ... and {len(unique_topics)-10} more")
                break
                
        # Look for chapter column
        chapter_column = None
        for possible_column in ['chapter', 'chapter_no', 'chapter_number', 'section']:
            if possible_column in df.columns:
                chapter_column = possible_column
                print(f"\nFound chapter information in column '{chapter_column}'")
                break
                
        # Suggest import strategy
        print("\n" + "="*50)
        print("RECOMMENDED IMPORT COMMAND:")
        
        # Base command
        command = f"python manage.py import_quiz_bank \"{file_path}\" --quiz-title=\"Quiz Bank Import\""
        
        # Add options based on data analysis
        if has_topics:
            print(f"\nOption 1 - Split into separate quizzes by topic:")
            print(f"{command} --split-by-topic --topic-column=\"{topic_column}\"")
            
            print(f"\nOption 2 - Import as single quiz:")
            print(f"{command}")
            
        else:
            print(command)
            
        if chapter_column and chapter_column != 'chapter_no':
            print(f"\nAdd this option to include chapter information:")
            print(f"--chapter-column=\"{chapter_column}\"")
            
        print("\n" + "="*50)
        
        # Prompt to run the recommended command
        print("\nDo you want to run the command now? (y/n)")
        choice = input().lower()
        
        if choice == 'y' or choice == 'yes':
            # Construct the command
            import_command = f"python manage.py import_quiz_bank \"{file_path}\" --quiz-title=\"Quiz Bank Import\""
            
            if has_topics:
                print("\nDo you want to split by topic? (y/n)")
                split_choice = input().lower()
                
                if split_choice == 'y' or split_choice == 'yes':
                    import_command += f" --split-by-topic --topic-column=\"{topic_column}\""
                    
            if chapter_column and chapter_column != 'chapter_no':
                import_command += f" --chapter-column=\"{chapter_column}\""
                
            print(f"\nRunning: {import_command}")
            os.system(import_command)
            
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
if __name__ == '__main__':
    sys.exit(main())
