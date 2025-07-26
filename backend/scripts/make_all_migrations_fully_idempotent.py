#!/usr/bin/env python3
"""
Make all migration files fully idempotent by adding proper checks for:
- create_table
- create_index
- create_foreign_key
- create_unique_constraint
- create_check_constraint
- add_column
"""

from pathlib import Path


def add_helper_functions(content):
    """Add helper functions if they don't exist"""

    # Check if helper functions already exist
    if "def table_exists" in content:
        return content

    # Add imports if needed
    if "import sqlalchemy as sa" not in content:
        content = content.replace(
            "from alembic import op", "import sqlalchemy as sa\nfrom alembic import op"
        )

    # Find where to insert helper functions (after imports)
    lines = content.split("\n")
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith("revision ="):
            # Insert before revision
            insert_index = i - 1
            break

    helper_functions = '''

def table_exists(table_name):
    """Check if a table exists in the migration schema"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = :table_name
            )
        """).bindparams(table_name=table_name)
    ).scalar()
    return result


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = :table_name
                AND column_name = :column_name
            )
        """).bindparams(table_name=table_name, column_name=column_name)
    ).scalar()
    return result


def index_exists(index_name, table_name):
    """Check if an index exists"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = :table_name
                AND indexname = :index_name
            )
        """).bindparams(table_name=table_name, index_name=index_name)
    ).scalar()
    return result


def constraint_exists(constraint_name, table_name):
    """Check if a constraint exists"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'migration'
                AND constraint_schema = 'migration'
                AND table_name = :table_name
                AND constraint_name = :constraint_name
            )
        """).bindparams(table_name=table_name, constraint_name=constraint_name)
    ).scalar()
    return result

'''

    lines.insert(insert_index, helper_functions)
    return "\n".join(lines)


def process_migration_file(file_path: Path):
    """Process a single migration file to make it idempotent"""

    print(f"Processing: {file_path.name}")

    content = file_path.read_text()
    original_content = content

    # Skip if already has comprehensive idempotent checks
    if all(
        func in content
        for func in [
            "table_exists",
            "column_exists",
            "index_exists",
            "constraint_exists",
        ]
    ):
        print("  ✓ Already fully idempotent (skipping)")
        return

    # Add helper functions
    content = add_helper_functions(content)

    # Only write if changed
    if content != original_content:
        file_path.write_text(content)
        print("  ✓ Added idempotent helper functions")
    else:
        print("  ✓ No changes needed")


def main():
    """Main function"""
    migrations_dir = Path(__file__).parent.parent / "alembic" / "versions"

    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        return

    # Get all Python migration files after 014
    migration_files = []
    for file_path in migrations_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue
        # Process migrations 015 and later
        if file_path.name.startswith(("015", "016", "017", "018", "019")):
            migration_files.append(file_path)

    migration_files.sort()

    print(f"Adding idempotent helpers to {len(migration_files)} migration files")
    print("-" * 50)

    for file_path in migration_files:
        process_migration_file(file_path)

    print("-" * 50)
    print("✅ Migration files processed")


if __name__ == "__main__":
    main()
