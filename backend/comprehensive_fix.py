#!/usr/bin/env python3
"""Comprehensive fix for all Python syntax errors.
This addresses indentation issues introduced by previous fixes.
"""

import ast
import os
import re

try:
    import autopep8
except ImportError:
    autopep8 = None


def fix_python_file(filepath) -> bool | None:
    """Fix Python syntax errors in a file using autopep8."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # First, try to parse to see if it's already valid
        try:
            ast.parse(content)
            return False  # Already valid, no fix needed
        except SyntaxError:
            pass

        # Use autopep8 to fix syntax and style issues
        if not autopep8:
            return None  # autopep8 not available
        fixed_content = autopep8.fix_code(
            content,
            options={
                "aggressive": 2,  # More aggressive fixes
                "max_line_length": 120,
                "indent_size": 4,
            },
        )

        # Verify the fixed content is valid
        try:
            ast.parse(fixed_content)
        except SyntaxError:
            # If autopep8 didn't fix it, try manual fixes
            fixed_content = manual_fix(content)
            try:
                ast.parse(fixed_content)
            except SyntaxError:
                return False  # Still broken

        # Write back if different
        if fixed_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            return True

        return False

    except Exception:
        return False


def manual_fix(content):
    """Manual fixes for common patterns autopep8 might miss."""
    lines = content.split("\n")
    fixed_lines = []

    for _i, line in enumerate(lines):
        # Fix lines that have statements on the same line without proper separation
        # Pattern: some_var = value another_var = value
        if re.match(r"^(\s*)(\w+\s*=\s*[^=]+?)(\w+\s*=)", line):
            match = re.match(r"^(\s*)(\w+\s*=\s*[^=]+?)(\w+\s*=.*)", line)
            if match:
                indent = match.group(1)
                first_part = match.group(2).rstrip()
                second_part = match.group(3)
                fixed_lines.append(indent + first_part)
                fixed_lines.append(indent + second_part)
                continue

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def main() -> None:
    """Process all Python files."""
    # First install autopep8 if not available
    # autopep8 was removed as it's not used in this script

    fixed_count = 0

    for root, dirs, files in os.walk("."):
        # Skip directories
        dirs[:] = [
            d
            for d in dirs
            if d not in ["venv", "__pycache__", ".git", ".pytest_cache", "node_modules"]
        ]

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)

                if fix_python_file(filepath):
                    fixed_count += 1


if __name__ == "__main__":
    main()
