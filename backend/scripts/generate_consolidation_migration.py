#!/usr/bin/env python3
"""
Generate the database consolidation migration with proper revision linking
"""

import os
import subprocess
import sys
from pathlib import Path


def get_latest_revision():
    """Get the latest Alembic revision ID"""
    try:
        result = subprocess.run(
            ['alembic', 'current'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output to get revision ID
        output = result.stdout.strip()
        if output and 'head' not in output:
            # Extract revision ID from output like "abc123def456 (head)"
            revision_id = output.split()[0]
            return revision_id
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error getting current revision: {e}")
        return None


def update_migration_file(down_revision):
    """Update the migration file with the correct down_revision"""
    migration_file = Path(__file__).parent.parent / 'alembic' / 'versions' / '20250101_database_consolidation.py'
    
    if not migration_file.exists():
        print(f"Migration file not found: {migration_file}")
        return False
    
    # Read the file
    with open(migration_file, 'r') as f:
        content = f.read()
    
    # Update the down_revision
    if down_revision:
        content = content.replace(
            "down_revision = None  # Update this to your latest migration",
            f"down_revision = '{down_revision}'"
        )
    else:
        content = content.replace(
            "down_revision = None  # Update this to your latest migration",
            "down_revision = None  # First migration"
        )
    
    # Write the updated content
    with open(migration_file, 'w') as f:
        f.write(content)
    
    print(f"Updated migration file with down_revision: {down_revision or 'None (first migration)'}")
    return True


def generate_proper_migration():
    """Generate the migration with proper Alembic metadata"""
    # Get the latest revision
    latest_revision = get_latest_revision()
    
    # Update the migration file
    if update_migration_file(latest_revision):
        print("\n✓ Database consolidation migration prepared successfully!")
        print("  Migration file: alembic/versions/20250101_database_consolidation.py")
        print(f"  Down revision: {latest_revision or 'None (first migration)'}")
        print("\nTo apply the migration:")
        print("  alembic upgrade head")
        print("\nTo test the migration (dry run):")
        print("  alembic upgrade head --sql")
    else:
        print("\n✗ Failed to prepare migration file")
        return 1
    
    return 0


def main():
    """Main entry point"""
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    print("Preparing database consolidation migration...")
    
    # Check if we're in the right directory
    if not Path('alembic.ini').exists():
        print("Error: alembic.ini not found. Are you in the backend directory?")
        return 1
    
    # Generate the migration
    return generate_proper_migration()


if __name__ == "__main__":
    sys.exit(main())