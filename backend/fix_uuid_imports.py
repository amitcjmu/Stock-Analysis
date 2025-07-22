#!/usr/bin/env python3
"""Fix UUID imports in all Python files."""

import os
import re


def fix_uuid_imports_in_file(filepath):
    """Fix UUID imports in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has Mapped[UUID] or similar patterns
        if 'Mapped[UUID' not in content:
            return False
        
        # Check if UUID is only imported in TYPE_CHECKING
        if 'if TYPE_CHECKING:' in content and 'from uuid import UUID' in content:
            # Find the TYPE_CHECKING block
            type_checking_pattern = r'if TYPE_CHECKING:.*?(?=\n(?:\S|\Z))'
            type_checking_match = re.search(type_checking_pattern, content, re.DOTALL)
            
            if type_checking_match and 'from uuid import UUID' in type_checking_match.group():
                # UUID is only in TYPE_CHECKING, need to move it out
                
                # Remove from TYPE_CHECKING block
                new_content = content
                
                # Find all imports at the top (before any class or function definitions)
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith(('import ', 'from ', '#', '"""', "'''")) and not line.strip() == '':
                        if 'TYPE_CHECKING' not in line and 'if TYPE_CHECKING:' not in lines[i-1] if i > 0 else True:
                            break
                
                # Add UUID import after datetime imports or before sqlalchemy imports
                if 'from datetime import' in content:
                    new_content = re.sub(
                        r'(from datetime import.*?\n)',
                        r'\1from uuid import UUID\n',
                        new_content,
                        count=1
                    )
                else:
                    # Add before first sqlalchemy import
                    new_content = re.sub(
                        r'(from typing.*?\n\n)',
                        r'\1from uuid import UUID\n\n',
                        new_content,
                        count=1
                    )
                
                # Remove UUID from TYPE_CHECKING imports
                new_content = re.sub(
                    r'(\s+from uuid import UUID\n)',
                    '',
                    new_content
                )
                
                # Write back
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
        
        # Check if UUID is not imported at all
        elif 'from uuid import UUID' not in content and 'import uuid' not in content:
            # Add UUID import
            if 'from datetime import' in content:
                new_content = re.sub(
                    r'(from datetime import.*?\n)',
                    r'\1from uuid import UUID\n',
                    content,
                    count=1
                )
            else:
                # Add after typing imports
                new_content = re.sub(
                    r'(from typing.*?\n)',
                    r'\1from uuid import UUID\n',
                    content,
                    count=1
                )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False
    
    return False

def main():
    """Process all Python files."""
    fixed_count = 0
    
    # Focus on models directory first
    for root, dirs, files in os.walk('./app/models'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_uuid_imports_in_file(filepath):
                    fixed_count += 1
                    print(f"Fixed UUID imports in: {filepath}")
    
    print(f"\nFixed UUID imports in {fixed_count} files")

if __name__ == "__main__":
    main()