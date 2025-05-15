#!/usr/bin/env python3
import os
import re
import glob

INLINE_COMMENT = r'(?<!["\'\\])#.*$'  # Match inline comments not part of strings
DOCSTRING_TRIPLE_SINGLE = r"'''(.*?)'''"  # Triple single quotes docstrings
DOCSTRING_TRIPLE_DOUBLE = r'"""(.*?)"""'  # Triple double quotes docstrings

def remove_comments(content):
    """Remove all types of comments from a Python file."""
    # Remove inline comments
    content = re.sub(INLINE_COMMENT, '', content, flags=re.MULTILINE)
    
    # Remove multi-line docstrings (both triple single and triple double quotes)
    content = re.sub(DOCSTRING_TRIPLE_SINGLE, '', content, flags=re.DOTALL)
    content = re.sub(DOCSTRING_TRIPLE_DOUBLE, '', content, flags=re.DOTALL)
    
    # Remove extra blank lines (2+ consecutive newlines -> 2 newlines)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content

def process_directory(directory):
    """Process all Python files in the given directory."""
    # Get all Python files
    python_files = glob.glob(f"{directory}/**/*.py", recursive=True)
    
    print(f"Found {len(python_files)} Python files in {directory}")
    
    for file_path in python_files:
        # Skip this script itself
        if file_path == __file__:
            continue
            
        print(f"Processing {file_path}...")
        
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove comments
            new_content = remove_comments(content)
            
            # Write the file if changes were made
            if content != new_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"  Removed comments from {file_path}")
            else:
                print(f"  No comments found in {file_path}")
                
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")

if __name__ == "__main__":
    # Process the info_videos directory
    process_directory("info_videos")
    print("Done processing files.") 