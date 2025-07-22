#!/usr/bin/env python3
"""Comprehensive fix for all UUID import issues."""

import os
import re


def fix_uuid_in_file(filepath):
    """Fix UUID imports comprehensively."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        
        # Skip if file already has proper UUID import at module level
        if re.search(r'^from uuid import UUID$', content, re.MULTILINE):
            # Check if it's in TYPE_CHECKING block
            lines = content.split('\n')
            in_type_checking = False
            uuid_in_type_checking = False
            
            for line in lines:
                if 'if TYPE_CHECKING:' in line:
                    in_type_checking = True
                elif in_type_checking and not line.startswith((' ', '\t')):
                    in_type_checking = False
                elif in_type_checking and 'from uuid import UUID' in line:
                    uuid_in_type_checking = True
                    break
            
            if not uuid_in_type_checking:
                return False  # Already has proper import
        
        # Check if file uses UUID in type annotations
        if ('Mapped[UUID' in content or 
            ': UUID' in content or 
            'Optional[UUID]' in content or 
            'UUID |' in content or 
            '| UUID' in content):
            
            # Find import section
            lines = content.split('\n')
            import_end = 0
            
            for i, line in enumerate(lines):
                if (line.strip() and 
                    not line.startswith(('import ', 'from ', '#', '"""', "'''", ' ', '\t')) and
                    'TYPE_CHECKING' not in line and
                    not (i > 0 and 'TYPE_CHECKING' in lines[i-1])):
                    import_end = i
                    break
            
            # Add UUID import at the right place
            new_lines = []
            uuid_added = False
            
            for i, line in enumerate(lines):
                # Skip UUID imports in TYPE_CHECKING blocks
                if 'from uuid import UUID' in line:
                    # Check if this is in TYPE_CHECKING
                    in_type_checking = False
                    for j in range(max(0, i-10), i):
                        if 'if TYPE_CHECKING:' in lines[j]:
                            in_type_checking = True
                            break
                    
                    if in_type_checking:
                        continue  # Skip this line
                    else:
                        return False  # Already has proper import
                
                # Add UUID import after other imports
                if not uuid_added and i < import_end:
                    if line.startswith('from datetime import'):
                        new_lines.append(line)
                        new_lines.append('from uuid import UUID')
                        uuid_added = True
                    elif line.startswith('from typing'):
                        new_lines.append(line)
                        if i+1 < len(lines) and lines[i+1].strip() == '':
                            new_lines.append('')
                            new_lines.append('from uuid import UUID')
                            uuid_added = True
                    else:
                        new_lines.append(line)
                elif i == import_end - 1 and not uuid_added:
                    new_lines.append(line)
                    new_lines.append('from uuid import UUID')
                    new_lines.append('')
                    uuid_added = True
                else:
                    new_lines.append(line)
            
            if uuid_added:
                new_content = '\n'.join(new_lines)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return False

def main():
    """Process all Python files."""
    fixed_count = 0
    checked_count = 0
    
    # Process all Python files
    for root, dirs, files in os.walk('./app'):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                checked_count += 1
                
                if fix_uuid_in_file(filepath):
                    fixed_count += 1
                    print(f"Fixed: {filepath}")
    
    print(f"\nChecked {checked_count} files")
    print(f"Fixed UUID imports in {fixed_count} files")

if __name__ == "__main__":
    main()