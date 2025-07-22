#!/usr/bin/env python3
"""Comprehensive script to fix all indentation errors in Python files."""

import ast
import os
import re


def fix_indentation_in_file(filepath):
    """Fix indentation issues in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file already has valid syntax
        try:
            ast.parse(content)
            return False  # File is already valid
        except SyntaxError:
            pass  # Continue with fixing
        
        lines = content.split('\n')
        fixed_lines = []
        
        # Track the expected indentation level
        expected_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            
            # Handle empty lines
            if not stripped:
                fixed_lines.append(line)
                continue
            
            # Handle comments
            if stripped.startswith('#'):
                # Comments should match current indentation level
                fixed_lines.append(' ' * expected_indent + stripped)
                continue
            
            # Check for lines that increase indentation
            if i > 0 and lines[i-1].strip().endswith(':'):
                expected_indent += 4
            
            # Check for lines that should decrease indentation
            if stripped.startswith(('return', 'raise', 'break', 'continue', 'pass')):
                # These usually end a block
                if i + 1 < len(lines) and lines[i+1].strip() and not lines[i+1].strip().startswith('#'):
                    next_line_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                    if next_line_indent < current_indent:
                        expected_indent = max(0, expected_indent - 4)
            
            # Handle dedent keywords
            if stripped.startswith(('else:', 'elif ', 'except ', 'except:', 'finally:', 'except:')):
                expected_indent = max(0, expected_indent - 4)
                fixed_lines.append(' ' * expected_indent + stripped)
                expected_indent += 4
                continue
            
            # Check for lines that are clearly mis-indented
            if current_indent != expected_indent:
                # Special case: lines that look like they should be indented
                if not stripped.startswith(('class ', 'def ', 'if ', 'for ', 'while ', 'try:', 'with ', 'async ', 'from ', 'import ', '@')):
                    # This line should probably use expected indentation
                    fixed_lines.append(' ' * expected_indent + stripped)
                    continue
                else:
                    # This is a new block at the wrong level
                    expected_indent = current_indent
            
            fixed_lines.append(line)
            
            # Update expected indentation for certain patterns
            if stripped.startswith(('class ', 'def ')):
                expected_indent = current_indent
        
        fixed_content = '\n'.join(fixed_lines)
        
        # Try to parse the fixed content
        try:
            ast.parse(fixed_content)
            # Success! Write the fixed content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
        except SyntaxError:
            # Still has errors - try a more aggressive fix
            return fix_aggressive(filepath)
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def fix_aggressive(filepath):
    """More aggressive fixing for stubborn files."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix specific patterns that cause indentation errors
        # Pattern 1: Unindented lines after except/try blocks
        content = re.sub(
            r'(except[^:]*:\n\s+[^\n]+\n)([A-Za-z_]\w*\s*=)',
            r'\1    \2',
            content,
            flags=re.MULTILINE
        )
        
        # Pattern 2: Unindented lines in class/function bodies
        content = re.sub(
            r'(\n    )([A-Za-z_]\w*\s*=)(?=\s*[^=])',
            r'\1    \2',
            content,
            flags=re.MULTILINE
        )
        
        # Pattern 3: Fix lines that start at column 0 but shouldn't
        lines = content.split('\n')
        fixed_lines = []
        indent_stack = [0]
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue
            
            # Determine proper indentation
            if i > 0:
                prev_line = lines[i-1].strip()
                if prev_line.endswith(':'):
                    # Should be indented more
                    indent_level = indent_stack[-1] + 4
                    indent_stack.append(indent_level)
                elif stripped.startswith(('return', 'raise', 'break', 'continue', 'pass')):
                    # Pop from indent stack
                    if len(indent_stack) > 1:
                        indent_stack.pop()
                    indent_level = indent_stack[-1]
                elif stripped.startswith(('else:', 'elif ', 'except ', 'except:', 'finally:')):
                    # Same level as matching if/try
                    if len(indent_stack) > 1:
                        indent_stack.pop()
                    indent_level = indent_stack[-1]
                    indent_stack.append(indent_level + 4)
                else:
                    # Use current indentation level
                    indent_level = indent_stack[-1]
                
                # Fix lines that have 0 indentation but shouldn't
                if len(line) > 0 and line[0] != ' ' and not stripped.startswith(('class ', 'def ', 'from ', 'import ', '@')):
                    if indent_level > 0:
                        line = ' ' * indent_level + stripped
            
            fixed_lines.append(line)
        
        fixed_content = '\n'.join(fixed_lines)
        
        # Try to parse
        try:
            ast.parse(fixed_content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
        except SyntaxError:
            return False
    
    except Exception:
        return False

def main():
    """Process all Python files."""
    fixed_count = 0
    error_count = 0
    
    # Only process app directory to focus on core functionality
    for root, dirs, files in os.walk('./app'):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                # Check if file has syntax errors
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast.parse(content)
                    continue  # File is already valid
                except SyntaxError:
                    # Try to fix it
                    if fix_indentation_in_file(filepath):
                        fixed_count += 1
                        print(f"Fixed: {filepath}")
                    else:
                        error_count += 1
                        print(f"Failed to fix: {filepath}")
                except Exception:
                    error_count += 1
    
    print(f"\nFixed {fixed_count} files")
    if error_count:
        print(f"Failed to fix {error_count} files")

if __name__ == "__main__":
    main()