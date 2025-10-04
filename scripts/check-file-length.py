#!/usr/bin/env python3
"""
Pre-commit hook to check Python file length and warn about files exceeding LOC limits.
Enforces modularization best practices by preventing excessively large files.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Configuration
MAX_LINES_ERROR = 400  # Hard limit - block commit
MAX_LINES_WARNING = 350  # Soft limit - show warning
IDEAL_MAX_LINES = 300  # Best practice recommendation

# Files to exclude from checks (legacy or generated files)
EXCLUDE_PATTERNS = [
    "*/migrations/*",
    "*/alembic/versions/*",  # Alembic migration files can be necessarily long
    "*/tests/*",  # Test files are EXEMPT from 400 line limit per CLAUDE.md
    "*/test_*.py",  # Test files are EXEMPT from 400 line limit per CLAUDE.md
    "*_test.py",  # Test files are EXEMPT from 400 line limit per CLAUDE.md
    "*/venv/*",
    "*/node_modules/*",
    "*/__pycache__/*",
    "*/build/*",
    "*/dist/*",
]


def get_staged_python_files() -> List[str]:
    """Get list of staged Python files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--staged", "--name-only", "--diff-filter=AMR"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return [f for f in files if f.endswith(".py") and Path(f).exists()]
    except subprocess.CalledProcessError:
        return []


def should_exclude(file_path: str) -> bool:
    """Check if file should be excluded from length check."""
    path_str = str(Path(file_path))
    for pattern in EXCLUDE_PATTERNS:
        # Use glob-style matching for patterns with wildcards
        if '*' in pattern:
            # Convert glob pattern to match anywhere in path
            import fnmatch
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Also try matching against path parts
            if fnmatch.fnmatch(path_str, '*/' + pattern):
                return True
        elif pattern in path_str:
            return True
    return False


def count_lines(file_path: str) -> int:
    """Count non-empty, non-comment lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Count actual code lines (excluding blank lines and pure comments)
            code_lines = 0
            for line in lines:
                stripped = line.strip()
                # Count line if it's not empty and not a pure comment
                if stripped and not stripped.startswith("#"):
                    code_lines += 1
                # Also count docstrings and multi-line comments
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    code_lines += 1
            return code_lines
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0


def check_file_lengths() -> Tuple[List[str], List[str], List[str]]:
    """Check lengths of all staged Python files."""
    errors = []
    warnings = []
    info = []

    staged_files = get_staged_python_files()

    if not staged_files:
        return errors, warnings, info

    for file_path in staged_files:
        if should_exclude(file_path):
            continue

        line_count = count_lines(file_path)

        if line_count > MAX_LINES_ERROR:
            errors.append(
                f"❌ {file_path}: {line_count} lines (exceeds {MAX_LINES_ERROR} line limit)"
            )
        elif line_count > MAX_LINES_WARNING:
            warnings.append(
                f"⚠️  {file_path}: {line_count} lines (exceeds recommended {MAX_LINES_WARNING} lines)"
            )
        elif line_count > IDEAL_MAX_LINES:
            info.append(
                f"ℹ️  {file_path}: {line_count} lines (consider keeping under {IDEAL_MAX_LINES} lines)"
            )

    return errors, warnings, info


def print_modularization_tips():
    """Print helpful tips for modularizing large files."""
    tips = """
📚 Modularization Tips:
-----------------------
1. Split by responsibility (queries, commands, handlers)
2. Extract utility functions to separate modules
3. Use mixins for shared functionality
4. Consider the facade pattern for backward compatibility
5. See backend/app/repositories/crewai_flow_state_extensions/ for a good example

Run '/modtest' to analyze all files needing modularization.
"""
    print(tips)


def main():
    """Main function to run the file length check."""
    errors, warnings, info = check_file_lengths()

    # Always show errors
    if errors:
        print("\n🚨 FILE LENGTH VIOLATIONS (Commit Blocked):")
        print("=" * 50)
        for error in errors:
            print(error)
        print("\nThese files must be modularized before committing.")
        print_modularization_tips()
        return 1  # Exit with error to block commit

    # Show warnings (don't block commit)
    if warnings:
        print("\n⚠️  FILE LENGTH WARNINGS (Consider Modularizing):")
        print("=" * 50)
        for warning in warnings:
            print(warning)
        print("\nConsider modularizing these files soon to maintain code quality.")

    # Optionally show info messages
    if info and len(info) <= 3:  # Only show a few info messages to avoid noise
        print("\nℹ️  Files approaching size limit:")
        for msg in info[:3]:
            print(msg)

    # Success message if all files are within limits
    if not errors and not warnings and not info:
        staged_count = len(get_staged_python_files())
        if staged_count > 0:
            print(f"✅ All {staged_count} staged Python files are within size limits.")

    return 0  # Success (warnings don't block commit)


if __name__ == "__main__":
    sys.exit(main())
