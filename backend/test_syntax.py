#!/usr/bin/env python3
"""Test script to verify Python syntax in all files."""

import ast
import os
import sys


def check_file_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"{e.msg} at line {e.lineno}"
    except Exception as e:
        return False, str(e)


def main():
    """Check all Python files for syntax errors."""
    error_files = []
    total_files = 0

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
                total_files += 1

                valid, error = check_file_syntax(filepath)
                if not valid:
                    error_files.append((filepath, error))

    if error_files:
        for filepath, error in error_files[:10]:  # Show first 10
            pass

        if len(error_files) > 10:
            pass

        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
