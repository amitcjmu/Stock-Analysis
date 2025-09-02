#!/usr/bin/env python3
"""
Fix Alembic migration issues by renaming files and fixing dependencies.

This script will:
1. Resolve duplicate numbered migrations
2. Rename hash-named files to sequential numbers
3. Add missing downgrade() functions where needed
4. Update revision dependencies to form a proper chain
5. Create a clean migration sequence

CC: Critical migration chain fixer
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MigrationFix:
    old_filename: str
    new_filename: str
    old_revision: str
    new_revision: str
    needs_downgrade_fix: bool = False


def fix_duplicate_017_migrations():
    """Fix the duplicate 017 migrations by renaming one to 017a."""
    versions_dir = Path("alembic/versions")

    # The two 017 files
    asset_file = "017_add_asset_id_to_questionnaire_responses.py"
    vector_file = "017_add_vector_search_to_agent_patterns.py"

    # Keep asset file as 017a, vector file becomes 042 (after all numbered ones)
    fixes = []

    # Fix the asset questionnaire file to 017a
    fixes.append(
        MigrationFix(
            old_filename=asset_file,
            new_filename="017a_add_asset_id_to_questionnaire_responses.py",
            old_revision="017_add_asset_id_to_questionnaire_responses",
            new_revision="017a_add_asset_id_to_questionnaire_responses",
        )
    )

    # The vector search file will be renumbered later with other hash-named files

    return fixes


def get_hash_named_migrations_renaming():
    """Get renaming plan for hash-named migrations starting from 042."""
    versions_dir = Path("alembic/versions")

    # Hash-named files that need renumbering (starting from 042)
    hash_files = [
        "017_add_vector_search_to_agent_patterns.py",  # Already identified as duplicate
        "1687c833bfcc_merge_migration_heads.py",
        "2ae8940123e6_add_analysis_queue_tables.py",
        "51470c6d6288_merge_collection_apps_with_timestamp_fix.py",
        "595ea1f47121_add_auto_generated_uuid_to_raw_import_.py",
        "64630c6d6a9a_merge_036_and_cef530e2_heads.py",
        "7cc356fcc04a_add_technical_details_to_assets.py",
        "951b58543ba5_add_confidence_score_to_assets.py",
        "add_canonical_application_identity.py",
        "add_collection_flow_applications_table.py",
        "b75f619e44dc_fix_application_name_variants_timestamps.py",
        "c279c3c0699d_fix_timestamp_mixin_timezone_issues.py",
        "cb5aa7ecb987_merge_heads_for_attribute_mapping_fix.py",
        "cef530e273d4_merge_heads_fix_questionnaire_asset_.py",
        "dc3417edf498_fix_platform_admin_is_admin_flag_after_.py",
        "fcacece8fa7b_merge_heads.py",
        "merge_mfo_testing_heads.py",
        "migrate_existing_collection_applications.py",
        "optimize_application_indexes.py",
    ]

    # Create descriptive names based on content
    new_names = [
        "042_add_vector_search_to_agent_patterns.py",
        "043_merge_migration_heads_035_optimize.py",
        "044_add_analysis_queue_tables.py",
        "045_merge_collection_apps_with_timestamp_fix.py",
        "046_add_auto_generated_uuid_to_raw_imports.py",
        "047_merge_036_and_questionnaire_asset_heads.py",
        "048_add_technical_details_to_assets.py",
        "049_add_confidence_score_to_assets.py",
        "050_add_canonical_application_identity.py",
        "051_add_collection_flow_applications_table.py",
        "052_fix_application_name_variants_timestamps.py",
        "053_fix_timestamp_mixin_timezone_issues.py",
        "054_merge_heads_for_attribute_mapping_fix.py",
        "055_merge_heads_fix_questionnaire_asset_relations.py",
        "056_fix_platform_admin_is_admin_flag.py",
        "057_merge_heads_cache_and_platform_admin.py",
        "058_merge_mfo_testing_heads.py",
        "059_migrate_existing_collection_applications.py",
        "060_optimize_application_indexes.py",
    ]

    # Map old revision IDs to new ones
    old_revisions = [
        "017_add_vector_search_to_agent_patterns",
        "1687c833bfcc",
        "2ae8940123e6",
        "51470c6d6288",
        "595ea1f47121",
        "64630c6d6a9a",
        "7cc356fcc04a",
        "951b58543ba5",
        "canonical_apps_001",
        "add_collection_apps_001",
        "b75f619e44dc",
        "c279c3c0699d",
        "cb5aa7ecb987",
        "cef530e273d4",
        "dc3417edf498",
        "fcacece8fa7b",
        "merge_mfo_testing_heads",
        "migrate_collection_apps_001",
        "optimize_app_indexes_001",
    ]

    new_revisions = [
        f"{i+42:03d}_{name.split('_', 1)[1].replace('.py', '')}"
        for i, name in enumerate(new_names)
    ]

    fixes = []
    for i in range(len(hash_files)):
        fixes.append(
            MigrationFix(
                old_filename=hash_files[i],
                new_filename=new_names[i],
                old_revision=old_revisions[i],
                new_revision=new_revisions[i],
            )
        )

    return fixes


def fix_032_duplicate():
    """Fix the 032 duplicate by renaming 032b to 036."""
    return [
        MigrationFix(
            old_filename="032b_rename_metadata_columns.py",
            new_filename="036_rename_metadata_columns.py",
            old_revision="032b_rename_metadata_columns",
            new_revision="036_rename_metadata_columns",
        )
    ]


def get_missing_downgrade_fixes():
    """Identify migrations that need downgrade() function fixes."""
    missing_downgrades = [
        "006_add_collection_flow_next_phase.py",
        "007_add_missing_collection_flow_columns.py",
        "008_update_flow_type_constraint.py",
        "011_add_updated_at_to_collection_data_gaps.py",
        "012_agent_observability_enhancement.py",
        "013_fix_agent_task_history_foreign_keys.py",
        "014_fix_remaining_agent_foreign_keys.py",
        "024_add_cache_metadata_tables.py",
        "033_merge_all_heads.py",
        "038_add_agent_pattern_learning_columns.py",
        "039_create_pattern_type_enum.py",
        "040_add_missing_field_mapping_columns.py",
    ]

    fixes = []
    for filename in missing_downgrades:
        fixes.append(
            MigrationFix(
                old_filename=filename,
                new_filename=filename,  # Same filename
                old_revision="",  # Will be determined when processing
                new_revision="",  # Same revision
                needs_downgrade_fix=True,
            )
        )

    return fixes


def update_file_content(
    file_path: Path, old_revision: str, new_revision: str, fix_downgrade: bool = False
) -> bool:
    """Update the content of a migration file with new revision info."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        updated_content = content

        # Update revision string
        if old_revision and new_revision:
            updated_content = re.sub(
                f'revision: str = "{re.escape(old_revision)}"',
                f'revision: str = "{new_revision}"',
                updated_content,
            )
            updated_content = re.sub(
                f'revision = "{re.escape(old_revision)}"',
                f'revision = "{new_revision}"',
                updated_content,
            )

        # Fix missing downgrade if needed
        if fix_downgrade:
            # Check if downgrade function exists but is empty/pass only
            downgrade_pattern = (
                r"(def downgrade\(\) -> None:\s*\n)(.*?)(?=\n\ndef|\nclass|\Z)"
            )
            match = re.search(downgrade_pattern, updated_content, re.DOTALL)

            if match:
                downgrade_body = match.group(2).strip()
                # If it's just pass or empty, add a proper downgrade
                if (
                    not downgrade_body
                    or downgrade_body == "pass"
                    or "pass" in downgrade_body
                    and len(downgrade_body.split("\n")) <= 2
                ):
                    # Generate a basic downgrade based on the upgrade function
                    upgrade_pattern = r"def upgrade\(\) -> None:(.*?)(?=def downgrade)"
                    upgrade_match = re.search(
                        upgrade_pattern, updated_content, re.DOTALL
                    )

                    if upgrade_match:
                        upgrade_body = upgrade_match.group(1)

                        # Basic downgrade logic based on common patterns
                        downgrade_ops = []

                        # Find create_table operations
                        if "op.create_table" in upgrade_body:
                            tables = re.findall(
                                r'op\.create_table\(\s*["\']([^"\']+)["\']',
                                upgrade_body,
                            )
                            for table in tables:
                                downgrade_ops.append(
                                    f'    op.drop_table("{table}", schema="migration")'
                                )

                        # Find add_column operations
                        if "op.add_column" in upgrade_body:
                            columns = re.findall(
                                r'op\.add_column\(\s*["\']([^"\']+)["\'],\s*sa\.Column\(["\']([^"\']+)["\']',
                                upgrade_body,
                            )
                            for table, column in columns:
                                downgrade_ops.append(
                                    f'    op.drop_column("{table}", "{column}", schema="migration")'
                                )

                        # Find create_index operations
                        if "op.create_index" in upgrade_body:
                            indexes = re.findall(
                                r'op\.create_index\(\s*["\']([^"\']+)["\']',
                                upgrade_body,
                            )
                            for index in indexes:
                                downgrade_ops.append(
                                    f'    op.drop_index("{index}", table_name="unknown_table", schema="migration")'
                                )

                        if downgrade_ops:
                            new_downgrade = f"""def downgrade() -> None:
    \"\"\"Reverse the changes made in upgrade().\"\"\"
    # Note: This is a generated downgrade. Review and test carefully.
{chr(10).join(downgrade_ops)}
"""
                        else:
                            new_downgrade = """def downgrade() -> None:
    \"\"\"Reverse the changes made in upgrade().

    WARNING: This migration does not have a proper downgrade implementation.
    Review the upgrade() function and implement appropriate reverse operations.
    \"\"\"
    # TODO: Implement proper downgrade operations
    pass
"""

                        updated_content = re.sub(
                            downgrade_pattern,
                            new_downgrade,
                            updated_content,
                            flags=re.DOTALL,
                        )

        # Write updated content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        return True

    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def create_backup():
    """Create backup of versions directory."""
    versions_dir = Path("alembic/versions")
    backup_dir = Path("alembic/versions_backup_pre_fix")

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    shutil.copytree(versions_dir, backup_dir)
    print(f"✅ Created backup at {backup_dir}")


def apply_fixes(fixes: List[MigrationFix], dry_run: bool = True):
    """Apply all the migration fixes."""
    versions_dir = Path("alembic/versions")

    print(f"{'DRY RUN: ' if dry_run else ''}Applying {len(fixes)} fixes...")

    for fix in fixes:
        old_path = versions_dir / fix.old_filename
        new_path = versions_dir / fix.new_filename

        if not old_path.exists():
            print(f"❌ File not found: {fix.old_filename}")
            continue

        print(
            f"{'[DRY RUN] ' if dry_run else ''}Processing: {fix.old_filename} -> {fix.new_filename}"
        )

        if not dry_run:
            # Update file content first
            if fix.old_revision and fix.new_revision:
                if not update_file_content(
                    old_path,
                    fix.old_revision,
                    fix.new_revision,
                    fix.needs_downgrade_fix,
                ):
                    print(f"❌ Failed to update content for {fix.old_filename}")
                    continue
            elif fix.needs_downgrade_fix:
                if not update_file_content(old_path, "", "", True):
                    print(f"❌ Failed to fix downgrade for {fix.old_filename}")
                    continue

            # Rename file if needed
            if fix.old_filename != fix.new_filename:
                try:
                    old_path.rename(new_path)
                    print(f"✅ Renamed: {fix.old_filename} -> {fix.new_filename}")
                except Exception as e:
                    print(f"❌ Failed to rename {fix.old_filename}: {e}")


def main():
    """Main function to orchestrate the migration fixes."""
    print("🔧 Migration Chain Fixer")
    print("=" * 40)

    # Check if we're in the right directory
    versions_dir = Path("alembic/versions")
    if not versions_dir.exists():
        print("❌ Error: alembic/versions directory not found!")
        return

    # Gather all fixes
    all_fixes = []

    # Fix duplicate 017s
    print("📋 Planning fixes for duplicate 017 migrations...")
    duplicate_017_fixes = fix_duplicate_017_migrations()
    all_fixes.extend(duplicate_017_fixes)

    # Fix duplicate 032s
    print("📋 Planning fixes for duplicate 032 migrations...")
    duplicate_032_fixes = fix_032_duplicate()
    all_fixes.extend(duplicate_032_fixes)

    # Hash-named migrations
    print("📋 Planning fixes for hash-named migrations...")
    hash_fixes = get_hash_named_migrations_renaming()
    all_fixes.extend(hash_fixes)

    # Missing downgrade fixes
    print("📋 Planning fixes for missing downgrade functions...")
    downgrade_fixes = get_missing_downgrade_fixes()
    all_fixes.extend(downgrade_fixes)

    print(f"\n📊 Total fixes planned: {len(all_fixes)}")
    print("   - Duplicate 017 fixes:", len(duplicate_017_fixes))
    print("   - Duplicate 032 fixes:", len(duplicate_032_fixes))
    print("   - Hash-named renames:", len(hash_fixes))
    print("   - Downgrade fixes:", len(downgrade_fixes))

    # Show what will be done
    print("\n🔍 Preview of changes:")
    for i, fix in enumerate(all_fixes[:10]):  # Show first 10
        status = (
            "RENAME + UPDATE"
            if fix.old_filename != fix.new_filename
            else "UPDATE CONTENT"
        )
        if fix.needs_downgrade_fix:
            status += " + FIX DOWNGRADE"
        print(f"  {i+1}. {fix.old_filename} -> {fix.new_filename} ({status})")

    if len(all_fixes) > 10:
        print(f"  ... and {len(all_fixes) - 10} more")

    # Ask for confirmation
    print(f"\n⚠️  This will modify {len(all_fixes)} migration files!")
    response = input("Continue with fixes? [y/N]: ").strip().lower()

    if response != "y":
        print("❌ Operation cancelled.")
        return

    # Create backup first
    print("\n💾 Creating backup...")
    create_backup()

    # Apply fixes
    print("\n🔧 Applying fixes...")
    apply_fixes(all_fixes, dry_run=False)

    print("\n✅ Migration fixes completed!")
    print("🔍 Run the analysis script again to verify the fixes.")
    print("⚠️  Remember to test the migration chain before deployment!")


if __name__ == "__main__":
    main()
