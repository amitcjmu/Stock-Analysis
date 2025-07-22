#!/usr/bin/env python3
"""Fix common indentation patterns that are causing syntax errors."""

import os


def fix_file(filepath):
    """Fix common indentation issues in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                i += 1
                continue
            
            # Check if this line has incorrect indentation
            if i > 0 and not line.startswith(' ') and not line.startswith('\t'):
                # Check if it's a continuation line that should be indented
                prev_line_idx = i - 1
                while prev_line_idx >= 0 and (not lines[prev_line_idx].strip() or lines[prev_line_idx].strip().startswith('#')):
                    prev_line_idx -= 1
                
                if prev_line_idx >= 0:
                    prev_line = lines[prev_line_idx]
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    
                    # Common patterns that need indentation
                    needs_indent = False
                    
                    # Pattern 1: Variable assignment after a block
                    if (prev_line.strip().endswith(':') or 
                        prev_line.strip().startswith('except') or
                        prev_line.strip().startswith('finally')):
                        needs_indent = True
                        indent_level = prev_indent + 4
                    # Pattern 2: Continuation of previous line
                    elif (prev_indent > 0 and 
                          not stripped.startswith(('class ', 'def ', 'if ', 'for ', 'while ', 
                                                  'try:', 'except', 'finally:', 'with ', 
                                                  'from ', 'import ', '@', 'async '))):
                        needs_indent = True
                        indent_level = prev_indent
                    
                    if needs_indent:
                        fixed_lines.append(' ' * indent_level + stripped)
                        i += 1
                        continue
            
            fixed_lines.append(line)
            i += 1
        
        # Write back the fixed content
        fixed_content = ''.join(fixed_lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        return True
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    """Fix common indentation issues in all Python files."""
    fixed_count = 0
    error_count = 0
    
    # First, fix only the core app files
    app_dirs = ['./app']
    
    for app_dir in app_dirs:
        if not os.path.exists(app_dir):
            continue
            
        for root, dirs, files in os.walk(app_dir):
            # Skip test directories for now
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    if fix_file(filepath):
                        fixed_count += 1
                    else:
                        error_count += 1
    
    print(f"Fixed {fixed_count} files")
    if error_count:
        print(f"Failed to fix {error_count} files")

if __name__ == "__main__":
    main()