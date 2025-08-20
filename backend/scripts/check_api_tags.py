#!/usr/bin/env python3
"""
Script to check for API tag violations and optionally fix them.

This script ensures:
1. No APIRouter(..., tags=...) in endpoint files
2. Tags are only applied at include_router level
3. All tags match the canonical list

Usage:
    python check_api_tags.py [--fix] [--dry-run] [file1 file2 ...]

    --fix: Automatically remove tags from routers
    --dry-run: Show what would be changed without modifying files
    file1 file2: Specific files to check (default: all .py files in app/)
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.api.v1.api_tags import APITags
except ImportError:
    print("Warning: Could not import APITags. Tag validation disabled.")
    APITags = None


def find_router_with_tags(content: str) -> List[Tuple[int, str]]:
    """Find all APIRouter instances with tags parameter."""
    violations = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        if "APIRouter" in line and "tags=" in line:
            violations.append((i, line.strip()))

    return violations


def remove_tags_from_router(content: str) -> str:
    """Remove tags parameter from APIRouter instantiations."""
    # Pattern 1: tags as the only parameter
    content = re.sub(
        r"(router\s*=\s*APIRouter\s*\(\s*)tags\s*=\s*\[[^\]]*\](\s*\))",
        r"\1\2",
        content,
    )

    # Pattern 2: tags with other parameters (before)
    content = re.sub(
        r"(router\s*=\s*APIRouter\s*\([^)]*?),?\s*tags\s*=\s*\[[^\]]*\],?\s*",
        r"\1",
        content,
    )

    # Pattern 3: tags with other parameters (after)
    content = re.sub(
        r"(router\s*=\s*APIRouter\s*\(\s*)tags\s*=\s*\[[^\]]*\],?\s*", r"\1", content
    )

    # Clean up any double commas or trailing commas
    content = re.sub(r",\s*,", ",", content)
    content = re.sub(r",\s*\)", ")", content)

    return content


def check_file(filepath: Path, fix: bool = False, dry_run: bool = False) -> bool:
    """
    Check a single file for violations.

    Returns True if violations were found (or fixed).
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

    violations = find_router_with_tags(content)

    if not violations:
        return False

    print(f"\n{filepath}:")
    for line_no, line in violations:
        print(f"  Line {line_no}: {line}")

    if fix:
        new_content = remove_tags_from_router(content)

        if dry_run:
            print(f"  [DRY RUN] Would remove tags from {len(violations)} router(s)")
        else:
            try:
                with open(filepath, "w") as f:
                    f.write(new_content)
                print(f"  ✓ Fixed {len(violations)} violation(s)")
            except Exception as e:
                print(f"  ✗ Error writing file: {e}")
                return False

    return True


def validate_include_router_tags(filepath: Path) -> List[str]:
    """Check if include_router tags are in the canonical list."""
    if not APITags:
        return []

    invalid_tags = []

    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception:
        return []

    # Find all include_router calls with tags
    pattern = re.compile(r"include_router\([^)]*tags\s*=\s*\[([^\]]*)\]", re.MULTILINE)

    for match in pattern.finditer(content):
        tags_str = match.group(1)
        # Extract individual tags
        tags = re.findall(r'"([^"]*)"', tags_str) + re.findall(r"'([^']*)'", tags_str)

        for tag in tags:
            if not APITags.validate_tag(tag):
                invalid_tags.append(tag)

    return invalid_tags


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix violations"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying",
    )
    parser.add_argument("files", nargs="*", help="Specific files to check")

    args = parser.parse_args()

    # Determine files to check
    if args.files:
        files = [Path(f) for f in args.files if Path(f).exists()]
    else:
        # Default: all Python files in app/api/v1/endpoints
        base_dir = Path(__file__).parent.parent / "app" / "api" / "v1" / "endpoints"
        files = list(base_dir.rglob("*.py"))

    if not files:
        print("No files to check")
        return 1

    print(f"Checking {len(files)} file(s) for API tag violations...")

    violations_found = False
    invalid_tags_found = []

    for filepath in files:
        # Skip __pycache__ directories
        if "__pycache__" in str(filepath):
            continue

        # Check for router tags
        if check_file(filepath, fix=args.fix, dry_run=args.dry_run):
            violations_found = True

        # Validate include_router tags
        invalid = validate_include_router_tags(filepath)
        if invalid:
            invalid_tags_found.extend(invalid)
            print(f"\n{filepath}: Invalid tags found: {', '.join(set(invalid))}")

    # Summary
    print("\n" + "=" * 60)

    if violations_found:
        if args.fix and not args.dry_run:
            print("✓ Violations fixed")
        else:
            print("✗ Violations found. Use --fix to automatically resolve.")
    else:
        print("✓ No APIRouter tag violations found")

    if invalid_tags_found:
        print(f"\n✗ Invalid tags found: {', '.join(set(invalid_tags_found))}")
        print("  These tags are not in the canonical list (api_tags.py)")

    return 1 if (violations_found and not args.fix) or invalid_tags_found else 0


if __name__ == "__main__":
    sys.exit(main())
