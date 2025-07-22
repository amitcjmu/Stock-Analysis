#!/usr/bin/env python3
"""Fix indentation errors in Python files caused by the previous syntax fix script.
This script looks for lines that are improperly indented and fixes them.
"""

import ast
import os
import re


def check_syntax(content) -> bool | None:
    """Check if Python code has valid syntax."""
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def fix_indentation_in_file(filepath) -> bool | None:
    """Fix indentation errors in a single Python file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        prev_indent = 0

        for i, line in enumerate(lines):
            # Skip empty lines and comments
            if line.strip() == "" or line.strip().startswith("#"):
                fixed_lines.append(line)
                continue

            # Get current indentation
            current_indent = len(line) - len(line.lstrip())

            # Check if this is a continuation of a previous line
            if i > 0 and fixed_lines and fixed_lines[-1].rstrip().endswith(":"):
                # This line should be indented more than the previous line
                if current_indent <= prev_indent:
                    # Fix indentation
                    fixed_line = " " * (prev_indent + 4) + line.lstrip()
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
            elif i > 0 and current_indent > 0 and current_indent % 4 != 0:
                # Fix odd indentation to nearest multiple of 4
                new_indent = round(current_indent / 4) * 4
                fixed_line = " " * new_indent + line.lstrip()
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)

            # Update previous indent
            if line.strip():
                prev_indent = len(fixed_lines[-1]) - len(fixed_lines[-1].lstrip())

        # Join lines and check syntax
        fixed_content = "".join(fixed_lines)

        # Only write if syntax is valid and content changed
        if fixed_content != "".join(lines) and check_syntax(fixed_content):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            return True
        return False

    except Exception:
        return False


def fix_specific_patterns(filepath) -> bool | None:
    """Fix specific indentation patterns that are known to be wrong."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix pattern where statements are not properly indented after except/try blocks
        # Pattern: except block followed by unindented assignment
        pattern = r"(except\s+\w+.*:\n\s+[^\n]+\n)([A-Za-z_]\w*\s*=\s*[^\n]+\n)(\s+\w+)"

        def fix_except_block(match):
            except_block = match.group(1)
            assignment = match.group(2)
            next_line = match.group(3)
            # Get indentation of except block
            indent_match = re.search(r"\n(\s+)", except_block)
            if indent_match:
                indent = indent_match.group(1)
                # Fix the assignment to have same indentation
                fixed_assignment = indent + assignment.lstrip()
                return except_block + fixed_assignment + next_line
            return match.group(0)

        content = re.sub(pattern, fix_except_block, content, flags=re.MULTILINE)

        # Write back if changed and syntax is valid
        if content != original_content and check_syntax(content):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    except Exception:
        return False


def main() -> None:
    """Main function to process all Python files."""
    # Get all Python files in the current directory and subdirectories
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip virtual environments and cache directories
        dirs[:] = [d for d in dirs if d not in ["venv", "__pycache__", ".git", ".pytest_cache"]]

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))


    fixed_count = 0
    for filepath in python_files:
        # Try specific pattern fixes first
        if fix_specific_patterns(filepath) or fix_indentation_in_file(filepath):
            fixed_count += 1



if __name__ == "__main__":
    main()
