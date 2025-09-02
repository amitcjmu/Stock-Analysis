#!/usr/bin/env python3
"""
Analyze Alembic migrations to understand the dependency chain and identify issues.

This script will:
1. Extract revision IDs and dependencies from all migration files
2. Identify duplicates and hash-named files
3. Generate a proper migration sequence
4. Check for missing downgrade() functions
5. Validate the dependency chain

CC: Critical migration chain analysis tool
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class MigrationInfo:
    filename: str
    revision: str
    down_revision: Optional[str]
    down_revisions: Optional[List[str]]  # For merge migrations
    has_downgrade: bool
    is_numbered: bool
    is_hash_named: bool
    number: Optional[str] = None
    description: Optional[str] = None


def extract_migration_info(file_path: Path) -> Optional[MigrationInfo]:
    """Extract migration information from a migration file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the AST to extract variables safely
        tree = ast.parse(content)

        revision = None
        down_revision = None
        down_revisions = None
        has_downgrade = False

        # Extract revision and down_revision
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "revision":
                            if isinstance(node.value, ast.Constant):
                                revision = node.value.value
                            elif isinstance(
                                node.value, ast.Str
                            ):  # Python < 3.8 compatibility
                                revision = node.value.s
                        elif target.id == "down_revision":
                            if isinstance(node.value, ast.Constant):
                                down_revision = node.value.value
                            elif isinstance(node.value, ast.Str):
                                down_revision = node.value.s
                            elif isinstance(node.value, ast.Tuple):
                                # Handle merge migrations with multiple parents
                                down_revisions = []
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        down_revisions.append(elt.value)
                                    elif isinstance(elt, ast.Str):
                                        down_revisions.append(elt.s)

        # Check if downgrade function exists and is not just 'pass'
        downgrade_pattern = (
            r"def\s+downgrade\s*\(\s*\)\s*->\s*None:\s*\n(.*?)(?=\n\ndef|\nclass|\Z)"
        )
        downgrade_match = re.search(downgrade_pattern, content, re.DOTALL)
        if downgrade_match:
            downgrade_body = downgrade_match.group(1).strip()
            # Consider it a real downgrade if it has more than just comments and pass
            has_real_downgrade = bool(
                re.search(r"(op\.|execute|create|drop|add|alter)", downgrade_body)
            )
            has_downgrade = has_real_downgrade

        # Determine if it's numbered or hash-named
        filename = file_path.name
        numbered_pattern = r"^(\d+[a-z]?)_"
        hash_pattern = r"^[a-f0-9]+_"

        is_numbered = bool(re.match(numbered_pattern, filename))
        is_hash_named = bool(re.match(hash_pattern, filename)) and not is_numbered

        number = None
        description = None
        if is_numbered:
            match = re.match(numbered_pattern, filename)
            if match:
                number = match.group(1)
                description = (
                    filename[len(match.group(0)) :].replace(".py", "").replace("_", " ")
                )

        return MigrationInfo(
            filename=filename,
            revision=revision,
            down_revision=down_revision,
            down_revisions=down_revisions,
            has_downgrade=has_downgrade,
            is_numbered=is_numbered,
            is_hash_named=is_hash_named,
            number=number,
            description=description,
        )

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None


def analyze_migrations(versions_dir: Path) -> Dict[str, MigrationInfo]:
    """Analyze all migration files in the versions directory."""
    migrations = {}

    for file_path in versions_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue

        migration_info = extract_migration_info(file_path)
        if migration_info:
            migrations[migration_info.revision] = migration_info

    return migrations


def find_duplicates(migrations: Dict[str, MigrationInfo]) -> Dict[str, List[str]]:
    """Find duplicate numbered migrations."""
    number_to_files = {}

    for migration in migrations.values():
        if migration.is_numbered and migration.number:
            number = migration.number.rstrip(
                "abcdefghijklmnopqrstuvwxyz"
            )  # Remove letter suffixes
            if number not in number_to_files:
                number_to_files[number] = []
            number_to_files[number].append(migration.filename)

    # Return only duplicates
    return {num: files for num, files in number_to_files.items() if len(files) > 1}


def build_dependency_chain(migrations: Dict[str, MigrationInfo]) -> List[str]:
    """Build the dependency chain from migrations."""
    # Find the root migration (no down_revision)
    roots = [
        rev
        for rev, info in migrations.items()
        if info.down_revision is None
        and (not info.down_revisions or not any(info.down_revisions))
        and rev is not None
    ]

    if not roots:
        print("Warning: No root migration found!")
        return []

    if len(roots) > 1:
        print(f"Warning: Multiple root migrations found: {roots}")

    # Build chain starting from root
    chain = []
    visited = set()

    def build_chain_recursive(revision: str):
        if revision in visited or revision not in migrations:
            return
        visited.add(revision)
        chain.append(revision)

        # Find all migrations that depend on this one
        dependents = [
            rev
            for rev, info in migrations.items()
            if (
                info.down_revision == revision
                or (info.down_revisions and revision in info.down_revisions)
            )
        ]

        for dependent in sorted(
            d for d in dependents if d is not None
        ):  # Sort for consistent ordering
            build_chain_recursive(dependent)

    if roots:
        build_chain_recursive(roots[0])

    return chain


def generate_report(migrations: Dict[str, MigrationInfo]) -> str:
    """Generate a comprehensive migration analysis report."""
    report = []
    report.append("# Alembic Migration Analysis Report")
    report.append("=" * 50)
    report.append("")

    # Summary statistics
    total = len(migrations)
    numbered = sum(1 for m in migrations.values() if m.is_numbered)
    hash_named = sum(1 for m in migrations.values() if m.is_hash_named)
    no_downgrade = sum(1 for m in migrations.values() if not m.has_downgrade)

    report.append(f"## Summary")
    report.append(f"- Total migrations: {total}")
    report.append(f"- Numbered migrations: {numbered}")
    report.append(f"- Hash-named migrations: {hash_named}")
    report.append(f"- Missing proper downgrade: {no_downgrade}")
    report.append("")

    # Find duplicates
    duplicates = find_duplicates(migrations)
    if duplicates:
        report.append("## CRITICAL: Duplicate Numbered Migrations")
        for number, files in duplicates.items():
            report.append(f"- Number {number}:")
            for filename in files:
                migration = next(
                    m for m in migrations.values() if m.filename == filename
                )
                report.append(f"  * {filename} (revision: {migration.revision})")
        report.append("")

    # Hash-named files that need renumbering
    hash_named_migrations = [m for m in migrations.values() if m.is_hash_named]
    if hash_named_migrations:
        report.append("## Hash-Named Migrations (Need Renumbering)")
        for migration in sorted(hash_named_migrations, key=lambda x: x.filename):
            report.append(f"- {migration.filename} (revision: {migration.revision})")
        report.append("")

    # Missing downgrade functions
    no_downgrade_migrations = [m for m in migrations.values() if not m.has_downgrade]
    if no_downgrade_migrations:
        report.append("## Missing Proper Downgrade Functions")
        for migration in sorted(no_downgrade_migrations, key=lambda x: x.filename):
            report.append(f"- {migration.filename}")
        report.append("")

    # Dependency chain
    chain = build_dependency_chain(migrations)
    report.append("## Migration Dependency Chain")
    for i, revision in enumerate(chain):
        migration = migrations.get(revision)
        if migration:
            report.append(f"{i+1:3d}. {migration.filename} ({revision})")
        else:
            report.append(f"{i+1:3d}. Unknown revision: {revision}")

    if len(chain) != len(migrations):
        orphaned = set(migrations.keys()) - set(chain)
        report.append("")
        report.append("## Orphaned Migrations (Not in Chain)")
        for revision in orphaned:
            migration = migrations[revision]
            report.append(f"- {migration.filename} ({revision})")

    report.append("")

    # Detailed migration list
    report.append("## All Migrations (Detailed)")
    for migration in sorted(migrations.values(), key=lambda x: x.filename):
        report.append(f"### {migration.filename}")
        report.append(f"- Revision: {migration.revision}")
        report.append(f"- Down revision: {migration.down_revision}")
        if migration.down_revisions:
            report.append(f"- Down revisions: {migration.down_revisions}")
        report.append(f"- Has downgrade: {'✓' if migration.has_downgrade else '✗'}")
        report.append(
            f"- Type: {'Numbered' if migration.is_numbered else 'Hash-named' if migration.is_hash_named else 'Other'}"
        )
        if migration.number:
            report.append(f"- Number: {migration.number}")
        report.append("")

    return "\n".join(report)


def main():
    """Main analysis function."""
    versions_dir = Path("alembic/versions")

    if not versions_dir.exists():
        print(f"Error: {versions_dir} does not exist!")
        return

    print("Analyzing migration files...")
    migrations = analyze_migrations(versions_dir)

    if not migrations:
        print("No migration files found!")
        return

    print(f"Found {len(migrations)} migration files")

    # Generate and save report
    report = generate_report(migrations)

    report_file = Path("migration_analysis_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Analysis complete! Report saved to {report_file}")

    # Print critical issues to console
    duplicates = find_duplicates(migrations)
    hash_named = [m for m in migrations.values() if m.is_hash_named]
    no_downgrade = [m for m in migrations.values() if not m.has_downgrade]

    if duplicates or hash_named or no_downgrade:
        print("\n🚨 CRITICAL ISSUES FOUND:")
        if duplicates:
            print(f"- {len(duplicates)} duplicate numbered migrations")
        if hash_named:
            print(f"- {len(hash_named)} hash-named migrations need renumbering")
        if no_downgrade:
            print(
                f"- {len(no_downgrade)} migrations missing proper downgrade functions"
            )
    else:
        print("\n✅ No critical issues found!")


if __name__ == "__main__":
    main()
