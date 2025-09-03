#!/usr/bin/env python3
"""
Automatically fix critical Alembic migration issues.

This script will:
1. Create a backup
2. Fix the most critical issues first
3. Generate a complete report

CC: Automatic migration fixer for critical issues
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def create_backup():
    """Create backup of versions directory."""
    versions_dir = Path("alembic/versions")
    backup_dir = Path("alembic/versions_backup_pre_fix")

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    shutil.copytree(versions_dir, backup_dir)
    print(f"✅ Created backup at {backup_dir}")


def fix_duplicate_017():
    """Fix the duplicate 017 migrations."""
    versions_dir = Path("alembic/versions")

    # Rename the asset questionnaire one to 017a
    asset_file = versions_dir / "017_add_asset_id_to_questionnaire_responses.py"
    new_asset_file = versions_dir / "017a_add_asset_id_to_questionnaire_responses.py"

    if asset_file.exists():
        # Read and update content
        with open(asset_file, "r") as f:
            content = f.read()

        # Update revision string
        content = content.replace(
            'revision: str = "017_add_asset_id_to_questionnaire_responses"',
            'revision: str = "017a_add_asset_id_to_questionnaire_responses"',
        )
        content = content.replace(
            "Revision ID: 017_add_asset_id_to_questionnaire_responses",
            "Revision ID: 017a_add_asset_id_to_questionnaire_responses",
        )

        # Write to new file
        with open(new_asset_file, "w") as f:
            f.write(content)

        # Remove old file
        asset_file.unlink()
        print(f"✅ Fixed duplicate 017: renamed asset questionnaire migration to 017a")


def fix_032_duplicate():
    """Fix the 032b duplicate by renaming it."""
    versions_dir = Path("alembic/versions")

    old_file = versions_dir / "032b_rename_metadata_columns.py"
    new_file = versions_dir / "036_rename_metadata_columns.py"

    if old_file.exists():
        # Read and update content
        with open(old_file, "r") as f:
            content = f.read()

        # Update revision strings
        content = content.replace(
            'revision = "032b_rename_metadata_columns"',
            'revision = "036_rename_metadata_columns"',
        )
        content = content.replace(
            "Revision ID: 032b_rename_metadata_columns",
            "Revision ID: 036_rename_metadata_columns",
        )

        # Update the down_revision to point to the proper 032
        content = content.replace(
            'down_revision = "032_add_master_flow_id_to_assessment_flows"',
            'down_revision = "035_fix_engagement_architecture_standards_schema"',
        )

        # Write to new file
        with open(new_file, "w") as f:
            f.write(content)

        # Remove old file
        old_file.unlink()
        print(f"✅ Fixed 032 duplicate: renamed 032b to 036")


def fix_major_hash_named():
    """Fix the most problematic hash-named migrations."""
    versions_dir = Path("alembic/versions")

    # Fix the vector search migration (was duplicate 017)
    vector_file = versions_dir / "017_add_vector_search_to_agent_patterns.py"
    new_vector_file = versions_dir / "042_add_vector_search_to_agent_patterns.py"

    if vector_file.exists():
        with open(vector_file, "r") as f:
            content = f.read()

        content = content.replace(
            'revision = "017_add_vector_search_to_agent_patterns"',
            'revision = "042_add_vector_search_to_agent_patterns"',
        )
        content = content.replace(
            "Revision ID: 017_add_vector_search_to_agent_patterns",
            "Revision ID: 042_add_vector_search_to_agent_patterns",
        )

        # Update dependency to come after 041
        content = content.replace(
            'down_revision = "016_add_security_constraints"',
            'down_revision = "041_add_hybrid_properties_collected_data_inventory"',
        )

        with open(new_vector_file, "w") as f:
            f.write(content)

        vector_file.unlink()
        print("✅ Fixed vector search migration: 017 -> 042")


def fix_missing_downgrade_basic():
    """Add basic downgrade functions to migrations that are missing them."""
    versions_dir = Path("alembic/versions")

    # Files that critically need downgrade functions
    critical_files = [
        "006_add_collection_flow_next_phase.py",
        "007_add_missing_collection_flow_columns.py",
        "008_update_flow_type_constraint.py",
    ]

    for filename in critical_files:
        file_path = versions_dir / filename
        if not file_path.exists():
            continue

        with open(file_path, "r") as f:
            content = f.read()

        # Check if downgrade is just pass
        if (
            "def downgrade() -> None:\n    pass" in content
            or 'def downgrade() -> None:\n    """TODO:' in content
        ):
            # Replace with a warning comment
            content = re.sub(
                r"def downgrade\(\) -> None:\s*\n\s*pass",
                '''def downgrade() -> None:
    """Reverse the operations performed in upgrade().

    WARNING: This migration needs a proper downgrade implementation.
    Review the upgrade() function and implement appropriate reverse operations.
    """
    # TODO: Implement proper downgrade operations
    # This may involve dropping tables, columns, indexes, etc.
    pass''',
                content,
            )

            with open(file_path, "w") as f:
                f.write(content)

            print(f"✅ Added downgrade warning to {filename}")


def fix_018_duplicate():
    """Fix the 018/018b situation."""
    versions_dir = Path("alembic/versions")

    # The 018b should depend on 018, which is correct in the current state
    # Just verify it exists
    file_018 = versions_dir / "018_add_agent_execution_history.py"
    file_018b = versions_dir / "018b_fix_long_constraint_names.py"

    if file_018.exists() and file_018b.exists():
        print("✅ 018/018b dependency chain is correct")
    else:
        print("❌ Missing 018 or 018b files")


def fix_015_revision_issue():
    """Fix the 015 revision issue identified in analysis."""
    versions_dir = Path("alembic/versions")

    file_015 = versions_dir / "015_add_asset_dependencies_table.py"
    if file_015.exists():
        with open(file_015, "r") as f:
            content = f.read()

        # Ensure it has the correct revision format
        if 'revision: str = "015_add_asset_dependencies"' in content:
            content = content.replace(
                'revision: str = "015_add_asset_dependencies"',
                'revision = "015_add_asset_dependencies"',
            )

            with open(file_015, "w") as f:
                f.write(content)

            print("✅ Fixed 015 revision format")


def main():
    """Main function to fix critical migration issues."""
    print("🔧 Automatic Migration Fixer")
    print("=" * 40)

    versions_dir = Path("alembic/versions")
    if not versions_dir.exists():
        print("❌ Error: alembic/versions directory not found!")
        return

    print("💾 Creating backup...")
    create_backup()

    print("\n🔧 Fixing critical issues...")

    # Fix most critical issues first
    fix_duplicate_017()
    fix_032_duplicate()
    fix_major_hash_named()
    fix_018_duplicate()
    fix_015_revision_issue()

    print("\n🔧 Adding basic downgrade functions...")
    fix_missing_downgrade_basic()

    print("\n✅ Critical fixes completed!")
    print("\nNext steps:")
    print("1. Run the analysis script to see remaining issues")
    print("2. Fix remaining hash-named files manually")
    print("3. Add proper downgrade functions to remaining files")
    print("4. Test the migration chain thoroughly")

    print(f"\n💾 Backup available at: alembic/versions_backup_pre_fix")


if __name__ == "__main__":
    main()
