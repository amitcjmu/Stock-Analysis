#!/usr/bin/env python3
"""
Fix syntax errors where '[] for' appears on the same line.
This script finds and fixes patterns like:
    errors = [] for error in exc.errors():
And converts them to:
    errors = []
    for error in exc.errors():
"""

import re
from pathlib import Path


def fix_list_comprehension_syntax(file_path):
    """Fix list comprehension syntax errors in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to find '[] for' on the same line
        # This will match lines like: variable = [] for item in iterable:
        pattern = r'^(\s*)([\w_]+)\s*=\s*\[\]\s+for\s+'
        
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                indent = match.group(1)
                var_name = match.group(2)
                # Extract the rest of the for statement
                rest_of_line = line[match.end():]
                
                # Create two lines: one for the empty list, one for the for loop
                fixed_lines.append(f"{indent}{var_name} = []")
                fixed_lines.append(f"{indent}for {rest_of_line}")
                print(f"Fixed in {file_path} at line {i+1}")
            else:
                fixed_lines.append(line)
        
        new_content = '\n'.join(fixed_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Process all Python files in the backend directory"""
    backend_dir = Path(__file__).parent
    fixed_count = 0
    
    # Find all Python files
    python_files = list(backend_dir.rglob("*.py"))
    
    print(f"Scanning {len(python_files)} Python files...")
    
    for file_path in python_files:
        # Skip this script itself
        if file_path.name == "fix_list_comprehension_syntax.py":
            continue
            
        if fix_list_comprehension_syntax(file_path):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files with list comprehension syntax errors")

if __name__ == "__main__":
    main()