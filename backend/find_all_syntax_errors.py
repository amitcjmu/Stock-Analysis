#!/usr/bin/env python3
"""Find all syntax errors in Python files."""

import ast
import os
import sys


def check_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"{filepath}:{e.lineno}: {e.msg}"
    except Exception:
        return None


def main():
    errors = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [
            d
            for d in dirs
            if d not in ["venv", "__pycache__", ".git", ".pytest_cache", "node_modules"]
        ]
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                error = check_file(filepath)
                if error:
                    errors.append(error)

    if errors:
        print(f"Found {len(errors)} syntax errors:\n")
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("No syntax errors found!")
        sys.exit(0)


if __name__ == "__main__":
    main()
