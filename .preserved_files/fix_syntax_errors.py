#!/usr/bin/env python3
"""
Fix syntax errors in Python files where multiple statements are on the same line.
This script looks for patterns where statements are incorrectly placed on the same line
and splits them onto separate lines.
"""

import os
import re
import sys
from pathlib import Path


def fix_syntax_errors_in_file(filepath):
    """Fix syntax errors in a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
content = f.read()
        
        original_content = content
        
        # Pattern to find lines where a statement follows an assignment without proper newline
        # This matches patterns like: some_var = value  another_statement
        # Negative lookbehind to avoid matching inside strings or comments
        pattern = r'([^#\n]+?=\s*[^=\n]+?)(\s{2,})(\w+[\.\[\(]|\w+\s*=)'
        
        def replace_match(match):
            """Replace match with proper newline formatting."""
            assignment = match.group(1)
next_statement = match.group(3)
            # Preserve indentation by getting the leading whitespace of the line
            line_start = content.rfind('\n', 0, match.start()) + 1
line_prefix = content[line_start:match.start()]
            indent = re.match(r'^(\s*)', line_prefix).group(1) if line_prefix else ''
            
            return f"{assignment}\n{indent}{next_statement}"
        
        # Apply the fix
        content = re.sub(pattern, replace_match, content)
        
        # Additional pattern for list/dict comprehensions that got split incorrectly
        # Fix patterns like: ] for x in items
        pattern2 = r'(\])\s+(for\s+\w+\s+in)'
content = re.sub(pattern2, r'\1 \2', content)
        
        # Write back only if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    # Get all Python files in the current directory and subdirectories
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and cache directories
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', '.pytest_cache']] for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to check")
    
    fixed_count = 0
    for filepath in python_files:
        if fix_syntax_errors_in_file(filepath):
            print(f"Fixed: {filepath}")
            fixed_count += 1
print(f"\nFixed syntax errors in {fixed_count} files")


if __name__ == "__main__":
main()