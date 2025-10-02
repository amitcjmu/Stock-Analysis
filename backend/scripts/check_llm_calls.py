#!/usr/bin/env python3
"""
Pre-commit hook to check LLM usage tracking via multi_model_service.

This script checks for direct LLM API calls that bypass automatic usage tracking.
All LLM calls SHOULD use multi_model_service.generate_response() for proper logging.

IMPORTANT: This is a WARNING-ONLY check (exit code 0) - does NOT block commits.
LLM tracking is an operational concern, not a code quality requirement.

Usage:
    python scripts/check_llm_calls.py [files...]

Exit codes:
    0: Always (warnings only, never blocks)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


# Patterns that indicate direct LLM calls (violations)
VIOLATION_PATTERNS = [
    (
        r"litellm\.completion\s*\(",
        "litellm.completion() - Use multi_model_service.generate_response() instead",
    ),
    (
        r"openai\.chat\.completions\.create\s*\(",
        "openai.chat.completions.create() - Use multi_model_service.generate_response() instead",
    ),
    (
        r"client\.chat\.completions\.create\s*\(",
        "client.chat.completions.create() - Use multi_model_service.generate_response() instead",
    ),
    (
        r"completion\s*\(\s*model\s*=",
        "completion(model=...) - Use multi_model_service.generate_response() instead",
    ),
]

# Files/directories to skip (allowed to have direct calls)
SKIP_PATTERNS = [
    "app/services/llm_usage_tracker.py",  # Tracker itself
    "app/services/multi_model_service.py",  # Service that wraps calls
    "app/services/deepinfra_completion_wrapper.py",  # Legacy wrapper
    "app/services/crews/base_crew.py",  # Legacy crew base (uses litellm directly)
    "tests/",  # Test files
    "alembic/",  # Database migrations
    "scripts/check_llm_calls.py",  # This script
]


def should_skip_file(file_path: str) -> bool:
    """Check if file should be skipped from LLM call validation."""
    for pattern in SKIP_PATTERNS:
        if pattern in file_path:
            return True
    return False


def check_file(file_path: str) -> List[Tuple[int, str, str]]:
    """
    Check a single file for direct LLM calls.

    Returns:
        List of (line_number, line_content, violation_message) tuples
    """
    violations = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                # Check each violation pattern
                for pattern, message in VIOLATION_PATTERNS:
                    if re.search(pattern, line):
                        violations.append((line_num, line.strip(), message))

    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return violations


def main(files: List[str] = None) -> int:
    """
    Main entry point for LLM call checking.

    Args:
        files: List of file paths to check. If None, checks all Python files in app/

    Returns:
        0 if no violations, 1 if violations found
    """
    if files is None:
        # Check all Python files in app directory
        app_dir = Path(__file__).parent.parent / "app"
        files = [str(f) for f in app_dir.rglob("*.py")]

    violations_found = False

    for file_path in files:
        # Skip non-Python files
        if not file_path.endswith(".py"):
            continue

        # Skip excluded files
        if should_skip_file(file_path):
            continue

        # Check for violations
        violations = check_file(file_path)

        if violations:
            violations_found = True
            print(f"\n❌ {file_path}:")
            for line_num, line_content, message in violations:
                print(f"   Line {line_num}: {message}")
                print(f"   > {line_content}")

    if violations_found:
        print("\n" + "=" * 80)
        print("⚠️  DIRECT LLM CALLS DETECTED (WARNING ONLY)")
        print("=" * 80)
        print(
            "\nAll LLM calls SHOULD use multi_model_service.generate_response() for tracking."
        )
        print("\nCorrect usage:")
        print("  from app.services.multi_model_service import multi_model_service")
        print("  response = await multi_model_service.generate_response(...)")
        print("\nSee CLAUDE.md for details.")
        print("\nNOTE: This is a warning only - commit will NOT be blocked.")
        print("=" * 80 + "\n")
        return 0  # Don't block commits
    else:
        print("✅ All LLM calls properly wrapped with tracking")
        return 0


if __name__ == "__main__":
    # Get files from command line args, or check all
    files = sys.argv[1:] if len(sys.argv) > 1 else None
    sys.exit(main(files))
