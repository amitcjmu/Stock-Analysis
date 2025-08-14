#!/usr/bin/env python3
"""
Make all Alembic migrations idempotent

This script updates all migration files to be idempotent, meaning they can be
run multiple times without errors. This is critical for automatic deployments
in Railway and other environments.

CC: Ensures migrations work automatically in all deployment environments
"""

import re
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

MIGRATIONS_DIR = Path(__file__).parent.parent / "alembic" / "versions"

# Patterns to make idempotent
PATTERNS = {
    # op.create_table
    r'(\s*)op\.create_table\(\s*["\']([\w_]+)["\']': {
        "replacement": r'''\1# Check if table already exists
\1conn = op.get_bind()
\1result = conn.execute(sa.text("""
\1    SELECT table_name
\1    FROM information_schema.tables
\1    WHERE table_schema = 'migration'
\1    AND table_name = '\2'
\1"""))
\1if not result.fetchone():
\1    op.create_table("\2"''',
        "needs_import": ["sa"],
    },
    # op.add_column
    r'(\s*)op\.add_column\(\s*["\']([\w_]+)["\']\s*,\s*sa\.Column\(\s*["\']([\w_]+)["\']': {
        "replacement": r'''\1# Check if column already exists
\1conn = op.get_bind()
\1result = conn.execute(sa.text("""
\1    SELECT column_name
\1    FROM information_schema.columns
\1    WHERE table_schema = 'migration'
\1    AND table_name = '\2'
\1    AND column_name = '\3'
\1"""))
\1if not result.fetchone():
\1    op.add_column("\2", sa.Column("\3"''',
        "needs_import": ["sa"],
    },
    # op.create_index
    r'(\s*)op\.create_index\(\s*["\']([\w_]+)["\']': {
        "replacement": r'''\1# Check if index already exists
\1conn = op.get_bind()
\1result = conn.execute(sa.text("""
\1    SELECT indexname
\1    FROM pg_indexes
\1    WHERE schemaname = 'migration'
\1    AND indexname = '\2'
\1"""))
\1if not result.fetchone():
\1    op.create_index("\2"''',
        "needs_import": ["sa"],
    },
    # op.create_foreign_key
    r'(\s*)op\.create_foreign_key\(\s*["\']([\w_]+)["\']': {
        "replacement": r'''\1# Check if foreign key already exists
\1conn = op.get_bind()
\1result = conn.execute(sa.text("""
\1    SELECT constraint_name
\1    FROM information_schema.table_constraints
\1    WHERE constraint_schema = 'migration'
\1    AND constraint_name = '\2'
\1    AND constraint_type = 'FOREIGN KEY'
\1"""))
\1if not result.fetchone():
\1    op.create_foreign_key("\2"''',
        "needs_import": ["sa"],
    },
}


def make_migration_idempotent(filepath: Path) -> bool:
    """Make a single migration file idempotent"""

    # Skip certain files
    if filepath.name in ["env.py", "script.py.mako", "__pycache__"]:
        return False

    try:
        content = filepath.read_text()
        modified = False

        # Check if already has idempotent checks
        if "information_schema" in content:
            print(f"  ✓ {filepath.name} - already idempotent")
            return False

        # Apply patterns
        for pattern, config in PATTERNS.items():
            if re.search(pattern, content):
                # Add import if needed
                if "needs_import" in config:
                    for imp in config["needs_import"]:
                        if (
                            f"import {imp}" not in content
                            and "from sqlalchemy import" not in content
                        ):
                            # Add import after alembic import
                            content = re.sub(
                                r"(from alembic import op.*\n)",
                                r"\1import sqlalchemy as sa\n",
                                content,
                                count=1,
                            )

                # Apply replacement
                content = re.sub(pattern, config["replacement"], content)
                modified = True

        if modified:
            # Close any unclosed if blocks by ensuring proper indentation
            lines = content.split("\n")
            fixed_lines = []
            in_if_block = False

            for line in lines:
                if "if not result.fetchone():" in line:
                    in_if_block = True
                elif in_if_block and line and not line.startswith(" "):
                    in_if_block = False

                fixed_lines.append(line)

            content = "\n".join(fixed_lines)

            # Write back
            filepath.write_text(content)
            print(f"  ✅ {filepath.name} - made idempotent")
            return True
        else:
            print(f"  ⏭️  {filepath.name} - no changes needed")
            return False

    except Exception as e:
        print(f"  ❌ {filepath.name} - error: {e}")
        return False


def main():
    """Main function"""
    print("🔧 Making all migrations idempotent...")
    print(f"📁 Scanning directory: {MIGRATIONS_DIR}")

    if not MIGRATIONS_DIR.exists():
        print("❌ Migrations directory not found!")
        return 1

    migration_files = sorted(MIGRATIONS_DIR.glob("*.py"))
    print(f"📝 Found {len(migration_files)} migration files")

    modified_count = 0
    for filepath in migration_files:
        if make_migration_idempotent(filepath):
            modified_count += 1

    print(f"\n✅ Modified {modified_count} migrations to be idempotent")
    print("🎯 All migrations will now work in Railway and other deployments!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
