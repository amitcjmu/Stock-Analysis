#!/usr/bin/env python3
"""Script to fix missing imports in Python files."""

import ast
import os
import sys
from pathlib import Path
from typing import Set, List, Tuple

def find_existing_imports(tree: ast.AST) -> Tuple[Set[str], List[ast.ImportFrom]]:
    """Find existing imports in the file."""
    imported_names = set()
typing_imports = []
for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == 'typing':
typing_imports.append(node)
                if node.names:
                    for alias in node.names:
                        if isinstance(alias.name, str):
                            imported_names.add(alias.name)
    
    return imported_names, typing_imports

def add_typing_import(file_path: str, names_to_add: List[str]) -> bool:
    """Add missing typing imports to a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
content = f.read()
        
        # Parse the file
        try:
            tree = ast.parse(content)
        except SyntaxError:
            print(f"Syntax error in {file_path}, skipping")
            return False
        
        # Find existing imports
        imported_names, typing_imports = find_existing_imports(tree)
        
        # Find what's missing
        missing_names = [name for name in names_to_add if name not in imported_names]
        
        if not missing_names:
            return False  # Nothing to add
        
        lines = content.splitlines(keepends=True)
        
        # Find where to insert the import
        import_line = None
last_import_line = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                if hasattr(node, 'lineno'):
                    last_import_line = max(last_import_line, node.lineno)
        
        # Check if we already have a typing import to extend
        typing_import_line = None
        for typing_import in typing_imports:
            if hasattr(typing_import, 'lineno'):
                typing_import_line = typing_import.lineno - 1  # ast uses 1-based indexing
                break
        
        if typing_import_line is not None and typing_import_line < len(lines):
            # Extend existing typing import
            line = lines[typing_import_line]
            
            # Parse the existing import to add new names
            if 'from typing import' in line:
                # Extract current imports
                start = line.find('import') + 7
end = line.rfind('\n') if '\n' in line else len(line)
                current_imports = line[start:end].strip()
                
                # Parse current names
                current_names = [name.strip() for name in current_imports.split(',')]
                
                # Add missing names
                all_names = sorted(set(current_names + missing_names))
                
                # Reconstruct the import line
                if len(all_names) <= 5:
new_line = f"from typing import {', '.join(all_names)}\n"
                else:
                    # Multi-line import
                    new_line = "from typing import (\n"
                    for i, name in enumerate(all_names):
                        new_line += f"    {name},"
                        if i < len(all_names) - 1:
                            new_line += "\n"
                    new_line += "\n)\n"
lines[typing_import_line] = new_line
        else:
            # Add new typing import
            if last_import_line > 0:
                # Add after last import
                insert_line = last_import_line
            else:
                # Add at the beginning, after docstring if any
                insert_line = 0
                for node in tree.body:
                    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                        # Skip docstring
                        insert_line = node.end_lineno if hasattr(node, 'end_lineno') else 1
                        break
                    else:
                        break
            
            # Create the import line
            if len(missing_names) <= 5:
import_statement = f"from typing import {', '.join(sorted(missing_names))}\n"
            else:
                import_statement = "from typing import (\n"
                for name in sorted(missing_names):
                    import_statement += f"    {name},\n"
                import_statement += ")\n"
            
            # Insert the import
            if insert_line < len(lines):
                # Check if we need to add a blank line
                if insert_line > 0 and lines[insert_line - 1].strip() and not lines[insert_line - 1].strip().startswith('import') and not lines[insert_line - 1].strip().startswith('from'):
                    import_statement = '\n' + import_statement
                if insert_line < len(lines) - 1 and lines[insert_line].strip() and not lines[insert_line].strip().startswith('import') and not lines[insert_line].strip().startswith('from'):
                    import_statement = import_statement + '\n'
lines.insert(insert_line, import_statement)
            else:
                lines.append('\n' + import_statement)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
f.writelines(lines)
        
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    # Read files that need Optional
    with open('/tmp/files_needing_optional.txt', 'r') as f:
        files = [line.strip() for line in f if line.strip()]
print(f"Processing {len(files)} files for Optional import...")
    
    fixed_count = 0
    for file_path in files:
        if os.path.exists(file_path) and file_path.endswith('.py'):
            if add_typing_import(file_path, ['Optional']):
                fixed_count += 1
                if fixed_count % 10 == 0:
print(f"Fixed {fixed_count} files...")
    
    print(f"\nFixed Optional imports in {fixed_count} files")

if __name__ == '__main__':
main()