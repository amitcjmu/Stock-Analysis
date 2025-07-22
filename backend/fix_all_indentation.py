#!/usr/bin/env python3
"""Fix all indentation issues in Python files.
This handles cases where the previous syntax fix script broke indentation.
"""

import ast
import os


def fix_file_indentation(filepath) -> bool | None:
    """Fix indentation issues in a Python file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Fix pattern: unindented lines that should be indented
        # This happens when we have lines starting at column 0 that should be indented
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # Check if this line is unindented but should be indented
            if (i > 0 and
                line and
                not line.startswith(" ") and
                not line.startswith("#") and
                "=" in line and
                not line.startswith("class ") and
                not line.startswith("def ") and
                not line.startswith("if ") and
                not line.startswith("for ") and
                not line.startswith("while ") and
                not line.startswith("try:") and
                not line.startswith("except") and
                not line.startswith("finally:") and
                not line.startswith("with ") and
                not line.startswith("from ") and
                not line.startswith("import ") and
                not line.startswith("@")):

                # Look at previous non-empty line
                prev_line_idx = i - 1
                while prev_line_idx >= 0 and not lines[prev_line_idx].strip():
                    prev_line_idx -= 1

                if prev_line_idx >= 0:
                    prev_line = lines[prev_line_idx]
                    prev_indent = len(prev_line) - len(prev_line.lstrip())

                    # If previous line was indented, this line should probably be indented too
                    if prev_indent > 0:
                        # Use the same indentation as the previous line
                        fixed_line = " " * prev_indent + line
                        fixed_lines.append(fixed_line)
                        continue

            fixed_lines.append(line)

        fixed_content = "\n".join(fixed_lines)

        # Check if the fixed content is valid Python
        try:
            ast.parse(fixed_content)
            # Only write if content changed
            if fixed_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                return True
        except SyntaxError:
            # If still has syntax errors, don't write
            pass

        return False

    except Exception:
        return False


def main() -> None:
    """Process all Python files."""
    fixed_count = 0
    error_count = 0

    for root, dirs, files in os.walk("."):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in ["venv", "__pycache__", ".git", ".pytest_cache", "node_modules"]]

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)

                # Check if file has syntax errors
                try:
                    with open(filepath, encoding="utf-8") as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError:
                    # Try to fix it
                    if fix_file_indentation(filepath):
                        fixed_count += 1
                    else:
                        error_count += 1
                except Exception:
                    pass



if __name__ == "__main__":
    main()
