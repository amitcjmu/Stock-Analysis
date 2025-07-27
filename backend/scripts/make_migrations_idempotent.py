#!/usr/bin/env python3
"""
Make all migration files idempotent to handle existing columns/tables
"""

import re
from pathlib import Path


def make_add_column_idempotent(content: str) -> str:
    """Replace op.add_column calls with idempotent versions"""

    # Pattern to match op.add_column calls
    pattern = (
        r'([\s]*)op\.add_column\(\s*"([^"]+)",\s*sa\.Column\("([^"]+)"[^)]+\)\s*\)'
    )

    def replacement(match):
        indent = match.group(1)
        table_name = match.group(2)
        column_name = match.group(3)
        original = match.group(0)

        # Create idempotent version
        idempotent = f'''{indent}# Check if column already exists
{indent}conn = op.get_bind()
{indent}result = conn.execute(
{indent}    sa.text("""
{indent}        SELECT column_name
{indent}        FROM information_schema.columns
{indent}        WHERE table_name = '{table_name}'
{indent}        AND column_name = '{column_name}'
{indent}    """)
{indent})
{indent}if not result.fetchone():
{indent}    {original.strip()}'''

        return idempotent

    return re.sub(pattern, replacement, content)


def make_create_table_idempotent(content: str) -> str:
    """Replace op.create_table calls with idempotent versions"""

    # This is more complex, so for now we'll skip it
    # Tables are less likely to have duplicate issues
    return content


def process_migration_file(file_path: Path):
    """Process a single migration file to make it idempotent"""

    print(f"Processing: {file_path.name}")

    content = file_path.read_text()
    original_content = content

    # Skip if already has idempotent checks
    if "information_schema.columns" in content:
        print("  ✓ Already idempotent (skipping)")
        return

    # Make modifications
    content = make_add_column_idempotent(content)

    # Only write if changed
    if content != original_content:
        file_path.write_text(content)
        print("  ✓ Made idempotent")
    else:
        print("  ✓ No changes needed")


def main():
    """Main function"""
    migrations_dir = Path(__file__).parent.parent / "alembic" / "versions"

    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        return

    # Get all Python migration files
    migration_files = list(migrations_dir.glob("*.py"))
    migration_files.sort()

    print(f"Found {len(migration_files)} migration files")
    print("-" * 50)

    for file_path in migration_files:
        if file_path.name == "__init__.py":
            continue
        process_migration_file(file_path)

    print("-" * 50)
    print("✅ Migration files processed")


if __name__ == "__main__":
    main()
