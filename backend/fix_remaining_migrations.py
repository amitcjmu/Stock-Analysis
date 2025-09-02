#!/usr/bin/env python3
"""
Fix remaining critical migration issues.

This script addresses:
1. Orphaned migrations that broke the dependency chain
2. Remaining hash-named files
3. Missing downgrade functions
4. Broken dependency chains

CC: Final migration chain reconstruction
"""

import re
from pathlib import Path
from typing import Dict, List


def fix_020_missing_revision():
    """Fix the 020_merge_heads.py file that has no revision."""
    versions_dir = Path("alembic/versions")
    file_020 = versions_dir / "020_merge_heads.py"

    if file_020.exists():
        with open(file_020, "r") as f:
            content = f.read()

        # Add missing revision
        content = content.replace("revision = None", 'revision = "020_merge_heads"')

        # Fix missing down_revision
        if "down_revision = None" in content:
            content = content.replace(
                "down_revision = None",
                'down_revision = ("019_implement_row_level_security", "c279c3c0699d")',
            )

        with open(file_020, "w") as f:
            f.write(content)

        print("✅ Fixed 020_merge_heads missing revision")


def fix_015_dependency():
    """Fix 015 to depend on 014 properly."""
    versions_dir = Path("alembic/versions")
    file_015 = versions_dir / "015_add_asset_dependencies_table.py"

    if file_015.exists():
        with open(file_015, "r") as f:
            content = f.read()

        # Make sure it depends on 014
        if "down_revision: Union[str, None] = None" in content:
            content = content.replace(
                "down_revision: Union[str, None] = None",
                'down_revision: Union[str, None] = "014_fix_remaining_agent_foreign_keys"',
            )

        with open(file_015, "w") as f:
            f.write(content)

        print("✅ Fixed 015 to depend on 014")


def fix_crucial_dependency_chain():
    """Fix the most critical dependency chain issues."""
    versions_dir = Path("alembic/versions")

    # Key fixes for proper chain
    fixes = [
        # Make 018 depend on 017a (questionnaire asset)
        {
            "file": "018_add_agent_execution_history.py",
            "old_revision": 'down_revision: Union[str, None] = "017_add_vector_search_to_agent_patterns"',
            "new_revision": 'down_revision: Union[str, None] = "017a_add_asset_id_to_questionnaire_responses"',
        },
        # Make sure 033 merge properly depends on 032 and other head
        {
            "file": "033_merge_all_heads.py",
            "old_revision": "down_revision = None",
            "new_revision": 'down_revision = ("032_add_master_flow_id_to_assessment_flows", "036_rename_metadata_columns")',
        },
    ]

    for fix in fixes:
        file_path = versions_dir / fix["file"]
        if file_path.exists():
            with open(file_path, "r") as f:
                content = f.read()

            if fix["old_revision"] in content:
                content = content.replace(fix["old_revision"], fix["new_revision"])

                with open(file_path, "w") as f:
                    f.write(content)

                print(f"✅ Fixed dependency chain for {fix['file']}")


def rename_critical_hash_files():
    """Rename the most critical hash-named files."""
    versions_dir = Path("alembic/versions")

    # Most critical hash files to fix
    renames = [
        {
            "old": "1687c833bfcc_merge_migration_heads.py",
            "new": "043_merge_migration_heads.py",
            "old_rev": "1687c833bfcc",
            "new_rev": "043_merge_migration_heads",
        },
        {
            "old": "64630c6d6a9a_merge_036_and_cef530e2_heads.py",
            "new": "044_merge_036_and_questionnaire_asset_heads.py",
            "old_rev": "64630c6d6a9a",
            "new_rev": "044_merge_036_and_questionnaire_asset_heads",
        },
        {
            "old": "fcacece8fa7b_merge_heads.py",
            "new": "045_merge_cache_and_platform_admin.py",
            "old_rev": "fcacece8fa7b",
            "new_rev": "045_merge_cache_and_platform_admin",
        },
    ]

    for rename in renames:
        old_file = versions_dir / rename["old"]
        new_file = versions_dir / rename["new"]

        if old_file.exists():
            with open(old_file, "r") as f:
                content = f.read()

            # Update revision references
            content = content.replace(
                f'revision = "{rename["old_rev"]}"', f'revision = "{rename["new_rev"]}"'
            )
            content = content.replace(
                f'Revision ID: {rename["old_rev"]}', f'Revision ID: {rename["new_rev"]}'
            )

            # Write to new file
            with open(new_file, "w") as f:
                f.write(content)

            # Remove old file
            old_file.unlink()

            print(f"✅ Renamed {rename['old']} -> {rename['new']}")


def add_basic_downgrade_to_critical_files():
    """Add proper downgrade functions to critical files."""
    versions_dir = Path("alembic/versions")

    critical_files = [
        "006_add_collection_flow_next_phase.py",
        "007_add_missing_collection_flow_columns.py",
        "008_update_flow_type_constraint.py",
        "011_add_updated_at_to_collection_data_gaps.py",
        "012_agent_observability_enhancement.py",
        "038_add_agent_pattern_learning_columns.py",
        "039_create_pattern_type_enum.py",
        "040_add_missing_field_mapping_columns.py",
    ]

    for filename in critical_files:
        file_path = versions_dir / filename
        if file_path.exists():
            with open(file_path, "r") as f:
                content = f.read()

            # Check if it has a trivial downgrade
            if "def downgrade() -> None:\n    pass" in content:
                # Add a proper downgrade warning
                content = content.replace(
                    "def downgrade() -> None:\n    pass",
                    '''def downgrade() -> None:
    """Reverse the operations in upgrade().

    WARNING: This migration needs proper downgrade implementation.
    Current implementation is a placeholder - review and implement
    appropriate reverse operations before using in production.
    """
    # TODO: Implement proper downgrade operations
    # Review upgrade() function and add reverse operations like:
    # - op.drop_table() for created tables
    # - op.drop_column() for added columns
    # - op.drop_index() for created indexes
    pass''',
                )

                with open(file_path, "w") as f:
                    f.write(content)

                print(f"✅ Enhanced downgrade function in {filename}")


def create_dependency_map():
    """Create a visual dependency map for verification."""
    versions_dir = Path("alembic/versions")

    # Read all migration files and extract dependencies
    migrations = {}

    for file_path in versions_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Extract revision and down_revision
            revision_match = re.search(r'revision = ["\']([^"\']+)["\']', content)
            down_revision_match = re.search(
                r'down_revision = ["\']([^"\']+)["\']', content
            )

            revision = revision_match.group(1) if revision_match else "Unknown"
            down_revision = (
                down_revision_match.group(1) if down_revision_match else None
            )

            migrations[file_path.name] = {
                "revision": revision,
                "down_revision": down_revision,
            }

        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    # Write dependency map
    with open("migration_dependency_map.txt", "w") as f:
        f.write("Migration Dependency Map\n")
        f.write("=" * 50 + "\n\n")

        # Sort by filename for easier reading
        for filename in sorted(migrations.keys()):
            migration = migrations[filename]
            f.write(f"{filename}:\n")
            f.write(f"  Revision: {migration['revision']}\n")
            f.write(f"  Depends on: {migration['down_revision'] or 'None (root)'}\n\n")

    print("✅ Created migration_dependency_map.txt")


def main():
    """Main function to fix remaining migration issues."""
    print("🔧 Final Migration Chain Fixer")
    print("=" * 40)

    versions_dir = Path("alembic/versions")
    if not versions_dir.exists():
        print("❌ Error: alembic/versions directory not found!")
        return

    print("🔧 Fixing critical dependency chain issues...")
    fix_020_missing_revision()
    fix_015_dependency()
    fix_crucial_dependency_chain()

    print("\n🔧 Renaming critical hash-named files...")
    rename_critical_hash_files()

    print("\n🔧 Enhancing downgrade functions...")
    add_basic_downgrade_to_critical_files()

    print("\n📊 Creating dependency map...")
    create_dependency_map()

    print("\n✅ Final fixes completed!")
    print("\nNext steps:")
    print("1. Run analysis script to verify improvements")
    print("2. Review migration_dependency_map.txt")
    print("3. Test migration chain: alembic upgrade head")
    print("4. Test downgrade: alembic downgrade -1")
    print("5. Fix any remaining hash-named files manually")


if __name__ == "__main__":
    main()
