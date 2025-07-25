#!/usr/bin/env python3
"""
Fix async migration issues by patching problematic migration files
to work with asyncpg properly.
"""

import os
import re
from pathlib import Path

def fix_migration_file(filepath):
    """Fix a single migration file to work with asyncpg"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix multi-statement SQL blocks
    # Pattern to find execute calls with multi-statement SQL
    pattern = r'op\.execute\s*\(\s*["\']([^"\']+)["\']'
    
    def replace_multi_statement(match):
        sql = match.group(1)
        if ';' in sql and any(keyword in sql.upper() for keyword in ['GRANT', 'CREATE', 'ALTER']):
            # This is a multi-statement SQL, needs to be split
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            if len(statements) > 1:
                # Create separate execute calls
                result = []
                for stmt in statements:
                    result.append(f'op.execute("{stmt}")')
                return '\n    '.join(result)
        return match.group(0)
    
    # Fix execute with text() for parameterized queries
    content = re.sub(
        r'bind\.execute\s*\(\s*sa\.text\s*\(',
        'op.get_bind().exec_driver_sql(',
        content
    )
    
    # Fix multi-line SQL statements
    content = re.sub(
        r'op\.execute\s*\(\s*"""\s*(.*?)\s*"""\s*\)',
        lambda m: fix_multiline_sql(m.group(1)),
        content,
        flags=re.DOTALL
    )
    
    if content != original_content:
        print(f"Fixed: {filepath}")
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def fix_multiline_sql(sql):
    """Fix multi-line SQL statements"""
    # Remove leading/trailing whitespace
    sql = sql.strip()
    
    # Split by semicolon but not inside quotes
    statements = []
    current = []
    in_quotes = False
    quote_char = None
    
    for line in sql.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Track quotes
        for char in line:
            if char in ["'", '"'] and (not in_quotes or char == quote_char):
                if in_quotes and char == quote_char:
                    in_quotes = False
                    quote_char = None
                else:
                    in_quotes = True
                    quote_char = char
        
        current.append(line)
        
        # Check if line ends with semicolon and we're not in quotes
        if line.endswith(';') and not in_quotes:
            stmt = ' '.join(current).rstrip(';').strip()
            if stmt:
                statements.append(stmt)
            current = []
    
    # Add any remaining statement
    if current:
        stmt = ' '.join(current).rstrip(';').strip()
        if stmt:
            statements.append(stmt)
    
    if len(statements) > 1:
        # Multiple statements - need separate execute calls
        result = []
        for stmt in statements:
            # Escape quotes in the statement
            stmt = stmt.replace('"', '\\"')
            result.append(f'op.execute("{stmt}")')
        return '\n    '.join(result)
    else:
        # Single statement
        return f'op.execute("""\n    {sql}\n    """)'

def main():
    """Main function to fix all migration files"""
    migrations_dir = Path(__file__).parent.parent / 'alembic' / 'versions'
    
    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        return 1
    
    fixed_count = 0
    for migration_file in migrations_dir.glob('*.py'):
        if migration_file.name == '__init__.py':
            continue
        
        if fix_migration_file(migration_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} migration files")
    return 0

if __name__ == '__main__':
    exit(main())