#!/usr/bin/env python3
"""
Check all Alembic migrations for idempotency and proper error handling.
This script analyzes migration files to ensure they can be run multiple times safely.
"""

import re
from pathlib import Path
from typing import List, Dict


def check_migration_file(filepath: Path) -> Dict[str, List[str]]:
    """Check a single migration file for idempotency issues."""
    issues = {
        "missing_checks": [],
        "missing_error_handling": [],
        "sequencing_issues": [],
        "other_issues": [],
    }

    with open(filepath, "r") as f:
        content = f.read()

    filename = filepath.name

    # Check for common non-idempotent patterns
    patterns_to_check = [
        # Column operations
        (r"op\.add_column\([^)]+\)", "add_column", "column existence check"),
        (r"op\.drop_column\([^)]+\)", "drop_column", "error handling"),
        # Index operations
        (
            r"op\.create_index\([^)]+\)",
            "create_index",
            "IF NOT EXISTS or existence check",
        ),
        (r"op\.drop_index\([^)]+\)", "drop_index", "IF EXISTS or error handling"),
        # Constraint operations
        (
            r"op\.create_check_constraint\([^)]+\)",
            "create_check_constraint",
            "constraint existence check",
        ),
        (
            r"op\.create_foreign_key\([^)]+\)",
            "create_foreign_key",
            "constraint existence check",
        ),
        (r"op\.drop_constraint\([^)]+\)", "drop_constraint", "error handling"),
        # Table operations
        (
            r"op\.create_table\([^)]+\)",
            "create_table",
            "IF NOT EXISTS or existence check",
        ),
        (r"op\.drop_table\([^)]+\)", "drop_table", "IF EXISTS or error handling"),
    ]

    for pattern, operation, required_check in patterns_to_check:
        matches = re.findall(pattern, content)
        for match in matches:
            # Check if there's appropriate error handling or existence check nearby
            # Look for common idempotency patterns
            idempotent_patterns = [
                r"if\s+not\s+result\.fetchone\(",
                r"if\s+result\.fetchone\(",
                r"try:",
                r"except",
                r"IF\s+NOT\s+EXISTS",
                r"IF\s+EXISTS",
                r"DROP\s+.*\s+IF\s+EXISTS",
                r"CREATE\s+.*\s+IF\s+NOT\s+EXISTS",
                r"information_schema",
                r"pg_constraint",
                r"pg_indexes",
            ]

            # Get context around the match (500 chars before and after)
            match_pos = content.find(match)
            context_start = max(0, match_pos - 500)
            context_end = min(len(content), match_pos + len(match) + 500)
            context = content[context_start:context_end]

            has_check = any(
                re.search(p, context, re.IGNORECASE) for p in idempotent_patterns
            )

            if not has_check:
                issues["missing_checks"].append(
                    f"{filename}: {operation} without {required_check} - {match[:50]}..."
                )

    # Check for proper revision chain
    revision_match = re.search(r'revision\s*=\s*["\']([^"\']+)["\']', content)
    down_revision_match = re.search(r'down_revision\s*=\s*["\']([^"\']+)["\']', content)

    if revision_match and down_revision_match:
        revision = revision_match.group(1)
        # down_revision = down_revision_match.group(1)  # Not currently used

        # Check if revision number matches filename
        if not filename.startswith(revision.split("_")[0]):
            issues["sequencing_issues"].append(
                f"{filename}: Revision ID mismatch - file starts with {filename[:3]} but revision is {revision}"
            )

    return issues


def main():
    """Check all migration files for idempotency."""
    migrations_dir = Path("backend/alembic/versions")

    # Get all migration files from 040 onwards
    migration_files = sorted(
        [
            f
            for f in migrations_dir.glob("0[4-5]*.py")
            if f.name[0:3].isdigit() and int(f.name[0:3]) >= 40
        ]
    )

    print("=" * 80)
    print("ALEMBIC MIGRATION IDEMPOTENCY CHECK")
    print("=" * 80)
    print(f"\nChecking {len(migration_files)} migration files...\n")

    all_issues = {}

    for filepath in migration_files:
        issues = check_migration_file(filepath)
        if any(issues.values()):
            all_issues[filepath.name] = issues

    # Report findings
    if not all_issues:
        print("✅ All migrations appear to have idempotency checks!")
        return 0

    print("⚠️  POTENTIAL IDEMPOTENCY ISSUES FOUND:\n")

    for filename, issues in all_issues.items():
        print(f"\n📄 {filename}:")
        for issue_type, issue_list in issues.items():
            if issue_list:
                print(f"  {issue_type}:")
                for issue in issue_list:
                    print(f"    - {issue}")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("1. Add existence checks before creating database objects")
    print("2. Add error handling for dropping objects that may not exist")
    print("3. Use IF NOT EXISTS / IF EXISTS clauses where possible")
    print("4. Wrap operations in try/except blocks for graceful handling")
    print("=" * 80)

    return 1 if all_issues else 0


if __name__ == "__main__":
    exit(main())
