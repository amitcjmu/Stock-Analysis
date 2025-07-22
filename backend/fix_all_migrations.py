#!/usr/bin/env python3
"""Fix indentation in all migration files."""

import glob
import os
import re


def fix_migration_file(filepath):
    """Fix all indentation issues in a migration file."""
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    inside_table = False
    table_indent = 0
    
    for i, line in enumerate(lines):
        # Check if we're starting a create_table
        if 'op.create_table(' in line:
            inside_table = True
            # Get the indentation of this line
            table_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
        # Check if we're ending a table
        elif inside_table and ')' in line and line.strip() == ')':
            inside_table = False
            fixed_lines.append(' ' * table_indent + line.strip() + '\n')
        # Check for op. lines that should have consistent indentation
        elif line.strip().startswith('op.'):
            # If previous line has op., use same indentation
            if i > 0 and 'op.' in lines[i-1]:
                prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                fixed_lines.append(' ' * prev_indent + line.strip() + '\n')
            else:
                # Default to 4 spaces
                fixed_lines.append('    ' + line.strip() + '\n')
        # Check for sa.Column lines
        elif line.strip().startswith('sa.Column('):
            if inside_table:
                # Inside table, should be indented 8 spaces from table start
                fixed_lines.append(' ' * (table_indent + 8) + line.strip() + '\n')
            else:
                fixed_lines.append(line)
        # Check for other sa. lines inside table
        elif inside_table and line.strip().startswith('sa.'):
            fixed_lines.append(' ' * (table_indent + 8) + line.strip() + '\n')
        else:
            fixed_lines.append(line)
    
    # Write back
    with open(filepath, 'w') as f:
        f.writelines(fixed_lines)
    
    return True

def main():
    """Process all migration files."""
    fixed_count = 0
    
    # Find all migration files
    migration_files = glob.glob('./alembic/versions/*.py')
    
    for filepath in migration_files:
        if '__pycache__' not in filepath:
            print(f"Checking {filepath}...")
            if fix_migration_file(filepath):
                fixed_count += 1
                print(f"  Fixed: {filepath}")
    
    print(f"\nFixed {fixed_count} migration files")

if __name__ == "__main__":
    main()