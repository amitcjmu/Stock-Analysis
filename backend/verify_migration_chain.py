#!/usr/bin/env python3
"""
Simple migration chain verification script
Checks if the revision references are correct without requiring a database connection
"""

import os
import re
from pathlib import Path


def extract_revision_info(file_path):
    """Extract revision and down_revision from a migration file"""
    with open(file_path, "r") as f:
        content = f.read()

    # Handle both formats: revision = "..." and revision: str = "..."
    revision_match = re.search(
        r'revision\s*:\s*str\s*=\s*["\']([^"\']+)["\']|'
        r'revision\s*[:=]\s*["\']([^"\']+)["\']',
        content,
    )
    down_revision_match = re.search(
        r'down_revision\s*:\s*Union\[str,\s*None\]\s*=\s*["\']([^"\']+)["\']|'
        r'down_revision\s*[:=]\s*["\']([^"\']+)["\']',
        content,
    )

    # Handle multiple groups from regex alternatives
    revision = None
    if revision_match:
        revision = revision_match.group(1) or revision_match.group(2)

    down_revision = None
    if down_revision_match:
        down_revision = down_revision_match.group(1) or down_revision_match.group(2)

    return revision, down_revision


def verify_migration_chain():
    """Verify the migration chain is consistent"""
    migrations_dir = Path("alembic/versions")

    if not migrations_dir.exists():
        print("❌ Alembic versions directory not found")
        return False

    # Get all migration files
    migration_files = sorted(
        [f for f in migrations_dir.glob("*.py") if f.name != "__pycache__"]
    )

    print(f"Found {len(migration_files)} migration files")

    # Build revision map
    revisions = {}
    dependencies = {}

    for file_path in migration_files:
        revision, down_revision = extract_revision_info(file_path)
        if revision:
            revisions[revision] = file_path.name
            dependencies[revision] = down_revision
            print(f"📄 {file_path.name}: {revision} <- {down_revision}")

    # Check for broken references
    broken_refs = []
    for revision, down_revision in dependencies.items():
        if down_revision and down_revision not in revisions:
            broken_refs.append((revision, down_revision))
            print(f"❌ BROKEN: {revision} references non-existent {down_revision}")

    if broken_refs:
        print(f"\n❌ Found {len(broken_refs)} broken references")
        return False
    else:
        print("\n✅ Migration chain appears to be valid")
        return True


if __name__ == "__main__":
    # Change to backend directory relative to script location
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    verify_migration_chain()
