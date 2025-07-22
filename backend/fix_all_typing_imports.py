#!/usr/bin/env python3
"""Script to fix all missing typing imports in Python files."""

import ast
import os
import sys
from pathlib import Path
from typing import Set, List, Tuple, Dict
from collections import defaultdict

def find_undefined_typing_names(file_path: str) -> Set[str]:
    """Find undefined typing names in a file using pyright output."""
    # This is a simplified approach - in practice we'd parse pyright output
    undefined_names = set()
    
    # For now, we'll check common typing names
    typing_names = ['Dict', 'List', 'Optional', 'Union', 'Any', 'Tuple', 'Set', 'Type', 'Callable', 'TypeVar', 'Generic', 'Protocol', 'Literal', 'Final', 'ClassVar', 'cast', 'overload']
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
content = f.read()
        
        # Parse the file
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return undefined_names
        
        # Find all Name nodes
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
        
        # Find existing imports
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'typing':
                if node.names:
                    for alias in node.names:
                        if isinstance(alias.name, str):
                            imported_names.add(alias.name)
        
        # Check which typing names are used but not imported
        for name in typing_names:
            if name in used_names and name not in imported_names:
                undefined_names.add(name)
        
        return undefined_names
        
    except Exception:
        return undefined_names

def add_typing_imports(file_path: str, names_to_add: Set[str]) -> bool:
    """Add missing typing imports to a file."""
    if not names_to_add:
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
content = f.read()
        
        # Parse the file
        try:
            tree = ast.parse(content)
        except SyntaxError:
            print(f"Syntax error in {file_path}, skipping")
            return False
        
        # Find existing typing imports
        imported_names = set()
typing_import_node = None
        typing_import_line = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'typing':
typing_import_node = node
                if hasattr(node, 'lineno'):
                    typing_import_line = node.lineno - 1
                if node.names:
                    for alias in node.names:
                        if isinstance(alias.name, str):
                            imported_names.add(alias.name)
        
        # Filter out already imported names
        names_to_add = names_to_add - imported_names
        
        if not names_to_add:
            return False
        
        lines = content.splitlines(keepends=True)
        
        # Find where to insert the import
        last_import_line = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                if hasattr(node, 'lineno'):
                    last_import_line = max(last_import_line, node.lineno)
        
        if typing_import_line is not None and typing_import_line < len(lines):
            # Extend existing typing import
            line = lines[typing_import_line]
            
            # Parse the existing import to add new names
            if 'from typing import' in line:
                # Extract current imports
                start = line.find('import') + 7
end = line.rfind('\n') if '\n' in line else len(line)
                current_imports = line[start:end].strip()
                
                # Handle multi-line imports
                if '(' in current_imports:
                    # Multi-line import
                    import_end_line = typing_import_line
                    while import_end_line < len(lines) and ')' not in lines[import_end_line]:
                        import_end_line += 1
                    
                    # Extract all names
                    import_text = ''.join(lines[typing_import_line:import_end_line + 1])
start = import_text.find('(') + 1
                    end = import_text.rfind(')')
names_text = import_text[start:end]
                    current_names = [name.strip() for name in names_text.split(',') if name.strip()]
                else:
                    # Single line import
                    current_names = [name.strip() for name in current_imports.split(',')]
                
                # Add missing names
                all_names = sorted(set(current_names + list(names_to_add)))
                
                # Reconstruct the import
                if len(all_names) <= 5:
new_line = f"from typing import {', '.join(all_names)}\n"
                    lines[typing_import_line] = new_line
                else:
                    # Multi-line import
                    new_lines = ["from typing import (\n"] for name in all_names:
                        new_lines.append(f"    {name},\n")
                    new_lines.append(")\n")
                    
                    # Replace old import
                    if '(' in current_imports:
                        # Remove old multi-line import
                        del lines[typing_import_line:import_end_line + 1]
                        # Insert new multi-line import
                        for i, new_line in enumerate(new_lines):
                            lines.insert(typing_import_line + i, new_line)
                    else:
                        # Replace single line with multi-line
                        lines[typing_import_line] = ''.join(new_lines)
        else:
            # Add new typing import
            if last_import_line > 0:
                # Add after last import
                insert_line = last_import_line
            else:
                # Add at the beginning, after docstring if any
                insert_line = 0
                for node in tree.body:
                    if isinstance(node, ast.Expr) and isinstance(node.value, (ast.Str, ast.Constant)):
                        # Skip docstring
                        insert_line = node.end_lineno if hasattr(node, 'end_lineno') else 1
                        break
                    else:
                        break
            
            # Create the import line
            sorted_names = sorted(names_to_add)
            if len(sorted_names) <= 5:
import_statement = f"from typing import {', '.join(sorted_names)}\n"
            else:
                import_statement = "from typing import (\n"
                for name in sorted_names:
                    import_statement += f"    {name},\n"
                import_statement += ")\n"
            
            # Insert the import with proper spacing
            if insert_line < len(lines):
                # Add spacing if needed
                if insert_line > 0 and lines[insert_line - 1].strip() and not lines[insert_line - 1].strip().startswith(('import', 'from')):
                    import_statement = '\n' + import_statement
                if insert_line < len(lines) - 1 and lines[insert_line].strip() and not lines[insert_line].strip().startswith(('import', 'from')):
                    import_statement = import_statement + '\n'
lines.insert(insert_line, import_statement)
            else:
                if lines and lines[-1].strip():
                    lines.append('\n')
                lines.append(import_statement)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
f.writelines(lines)
        
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    # Process specific files that need Dict/List
    files_to_process = [
        "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/data_import/mapping.py",
        "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/models/api/data_import.py",
        "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/models/assessment_flow_state.py",
        "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/models/unified_discovery_flow_state.py",
    ]
    
    # Map of files to their needed imports
    file_imports = {
        "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/data_import/mapping.py": {'List'},
        "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/models/api/data_import.py": {'Dict', 'List'},
        "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/models/assessment_flow_state.py": {'Dict', 'List'},
        "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/models/unified_discovery_flow_state.py": {'Dict', 'List'},
    }
    
    fixed_count = 0
    for file_path, imports_needed in file_imports.items():
        if os.path.exists(file_path):
            print(f"Processing {file_path} for {imports_needed}...")
            if add_typing_imports(file_path, imports_needed):
                fixed_count += 1
print(f"  ✓ Fixed")
            else:
                print(f"  - No changes needed")
    
    print(f"\nFixed typing imports in {fixed_count} files")

if __name__ == '__main__':
main()