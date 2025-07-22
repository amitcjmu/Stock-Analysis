#!/usr/bin/env python3
"""Fix migration revision IDs to be shorter for Alembic compatibility."""

import os
import re
import hashlib

def generate_short_revision(long_name):
    """Generate a short revision ID from the long name."""
    # Use first 12 characters of MD5 hash for uniqueness
    hash_obj = hashlib.md5(long_name.encode())
    return hash_obj.hexdigest()[:12]

def fix_migration_file(filepath):
    """Fix revision IDs in a single migration file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract current revision
    revision_match = re.search(r"revision = '([^']+)'", content)
    if not revision_match:
        print(f"No revision found in {filepath}")
        return None
    
    old_revision = revision_match.group(1)
new_revision = generate_short_revision(old_revision)
    
    # Extract down_revision
    down_revision_match = re.search(r"down_revision = ([^\n]+)", content)
old_down_revision = down_revision_match.group(1) if down_revision_match else "None"
    
    # Replace revision
    content = re.sub(
        r"revision = '[^']+'",
        f"revision = '{new_revision}'",
        content
    )
    
    # Update the Revision ID in the docstring
    content = re.sub(
        r"Revision ID: [^\n]+",
        f"Revision ID: {new_revision}",
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return old_revision, new_revision, old_down_revision.strip()

def main():
    """Main function to fix all migration files."""
    versions_dir = "alembic/versions"
    
    # First pass: collect all mappings
    revision_map = {}
files_info = []
for filename in sorted(os.listdir(versions_dir)):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(versions_dir, filename)
result = fix_migration_file(filepath)
            if result:
                old_revision, new_revision, down_revision = result
revision_map[old_revision] = new_revision
                files_info.append((filepath, old_revision, new_revision, down_revision))
                print(f"Fixed {filename}: {old_revision} -> {new_revision}")
    
    # Second pass: update down_revision references
    for filepath, old_revision, new_revision, down_revision in files_info:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Update down_revision if it references an old revision
        if down_revision != "None" and down_revision.strip("'\"") in revision_map:
old_down_rev = down_revision.strip("'\"")
            new_down_rev = revision_map[old_down_rev]
content = re.sub(
                r"down_revision = [^\n]+",
                f"down_revision = '{new_down_rev}'",
                content
            )
            
            # Also update in the docstring
            content = re.sub(
                f"Revises: {old_down_rev}",
                f"Revises: {new_down_rev}",
                content
            )
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            print(f"Updated down_revision in {os.path.basename(filepath)}: {old_down_rev} -> {new_down_rev}")

if __name__ == "__main__":
main()