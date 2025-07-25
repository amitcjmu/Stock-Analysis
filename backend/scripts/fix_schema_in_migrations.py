#!/usr/bin/env python3
"""
Fix all migration files to use migration schema in their idempotent checks
"""

import re
from pathlib import Path


def fix_schema_in_file(file_path: Path):
    """Fix schema references in a single migration file"""

    content = file_path.read_text()
    original_content = content

    # Pattern to find information_schema queries without schema specification
    pattern = r"(FROM information_schema\.\w+\s+WHERE\s+)(?!table_schema)"

    # Replace with schema-aware version
    def replacement(match):
        return match.group(1) + "table_schema = 'migration'\n            AND "

    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # Also fix pg_indexes queries
    pg_pattern = r"(FROM pg_indexes\s+WHERE\s+)(?!schemaname)"

    def pg_replacement(match):
        return match.group(1) + "schemaname = 'migration'\n            AND "

    content = re.sub(pg_pattern, pg_replacement, content, flags=re.IGNORECASE)

    # Only write if changed
    if content != original_content:
        file_path.write_text(content)
        print(f"  ✓ Fixed schema references in {file_path.name}")
        return True
    return False


def main():
    """Main function"""
    migrations_dir = Path(__file__).parent.parent / "alembic" / "versions"

    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        return

    # Get all Python migration files
    migration_files = list(migrations_dir.glob("*.py"))
    migration_files.sort()

    print(f"Fixing schema references in {len(migration_files)} migration files")
    print("-" * 50)

    fixed_count = 0
    for file_path in migration_files:
        if file_path.name == "__init__.py":
            continue
        if fix_schema_in_file(file_path):
            fixed_count += 1

    print("-" * 50)
    print(f"✅ Fixed {fixed_count} migration files")


if __name__ == "__main__":
    main()
