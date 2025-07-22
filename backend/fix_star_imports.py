#!/usr/bin/env python3
"""Fix all star imports (F403/F405) in the codebase."""

import ast
import os
import re
from pathlib import Path
from typing import Set, List, Tuple, Dict

def get_imported_names_from_module(module_path: str, import_from: str) -> Set[str]:
    """Get all exported names from a module."""
    # Handle relative imports
    if import_from.startswith('.'):
        # For relative imports, we need to resolve based on the current file's location
        current_dir = Path(module_path).parent
        # Count leading dots
        level = len(import_from) - len(import_from.lstrip('.'))
        # Go up directories based on level
        for _ in range(level - 1):
            current_dir = current_dir.parent
        # Add the remaining path
        remaining = import_from.lstrip('.')
        if remaining:
            target_path = current_dir / remaining.replace('.', '/')
        else:
            target_path = current_dir
    else:
        # For absolute imports
        target_path = Path(import_from.replace('.', '/'))
    
    # Try different locations and file extensions
    possible_paths = [
        target_path / '__init__.py',
        str(target_path) + '.py',
        Path('app') / target_path / '__init__.py',
        Path('app') / (str(target_path) + '.py'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    tree = ast.parse(f.read())
                    
                # Check for __all__
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == '__all__':
                                if isinstance(node.value, ast.List):
                                    return {
                                        elt.s if isinstance(elt, ast.Str) else
                                        elt.value if isinstance(elt, ast.Constant) else None
                                        for elt in node.value.elts
                                        if isinstance(elt, (ast.Str, ast.Constant))
                                    }
                
                # If no __all__, get all public names
                names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                        names.add(node.name)
                    elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                        names.add(node.name)
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and not target.id.startswith('_'):
                                names.add(target.id)
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            name = alias.asname if alias.asname else alias.name
                            if name != '*' and not name.startswith('_'):
                                names.add(name)
                return names
            except:
                pass
    
    return set()

def find_used_names(file_content: str, potential_names: Set[str]) -> Set[str]:
    """Find which names from the star import are actually used."""
    used_names = set()
    
    # Parse the file
    try:
        tree = ast.parse(file_content)
    except:
        # Fallback to regex if AST parsing fails
        for name in potential_names:
            if re.search(r'\b' + re.escape(name) + r'\b', file_content):
                used_names.add(name)
        return used_names
    
    # Walk the AST to find name usage
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in potential_names:
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in potential_names:
            used_names.add(node.attr)
    
    return used_names

def fix_star_imports_in_file(file_path: str) -> Tuple[bool, List[str]]:
    """Fix star imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # Find all star imports
    star_import_pattern = re.compile(r'^(\s*)from\s+([^\s]+)\s+import\s+\*\s*$', re.MULTILINE)
    
    for match in star_import_pattern.finditer(content):
        indent = match.group(1)
        module = match.group(2)
        
        # Get all names from the module
        potential_names = get_imported_names_from_module(file_path, module)
        
        if not potential_names:
            # If we can't determine names, use common patterns
            if 'models' in module:
                potential_names = {
                    'ClientAccount', 'EngagementData', 'FlowState', 'Asset',
                    'Assessment', 'FlowType', 'FlowStatus', 'Base',
                    'ImportFlowState', 'DataImport', 'MappingConfiguration',
                    'CriticalAttribute', 'AttributeAnalysisRequest', 'AttributeAnalysisResponse',
                    'AttributeSuggestion', 'AgentFeedback', 'AnalysisStatistics',
                    'CrewExecutionRequest', 'CrewExecutionResponse',
                    'FieldMappingCreate', 'FieldMappingUpdate', 'FieldMappingResponse',
                    'FieldMappingSuggestion', 'FieldMappingAnalysis', 'CustomFieldCreate',
                    'TargetFieldDefinition', 'DiscoveryFlowState', 'CollectionFlowState',
                    'AssessmentFlowState', 'UnifiedDiscoveryFlowState'
                }
            elif 'schemas' in module:
                potential_names = {
                    'BaseModel', 'Optional', 'List', 'Dict', 'Any', 'Union',
                    'Field', 'validator', 'root_validator'
                }
            elif 'typing' in module:
                potential_names = {
                    'Any', 'Dict', 'List', 'Optional', 'Union', 'Tuple', 'Set',
                    'Callable', 'Type', 'TypeVar', 'Generic', 'Protocol',
                    'Literal', 'Final', 'ClassVar', 'cast', 'overload'
                }
            elif 'utils' in module or 'helpers' in module:
                # For utils, look for function names in the content after the import
                potential_names = {
                    'intelligent_field_mapping', 'calculate_mapping_confidence',
                    'get_field_patterns', 'infer_field_type', 'validate_data_type_compatibility',
                    'normalize_field_name', 'extract_field_metadata', 'validate_mapping',
                    'generate_mapping_suggestions', 'apply_transformation_rules'
                }
            else:
                continue
        
        # Find which names are actually used
        # Get content after the import
        import_end = match.end()
        remaining_content = content[import_end:]
        used_names = find_used_names(remaining_content, potential_names)
        
        if used_names:
            # Sort names for consistency
            sorted_names = sorted(used_names)
            
            # Create explicit import
            if len(sorted_names) <= 3:
                new_import = f"{indent}from {module} import {', '.join(sorted_names)}"
            else:
                # Multi-line import
                import_lines = [f"{indent}from {module} import ("]
                for i, name in enumerate(sorted_names):
                    comma = ',' if i < len(sorted_names) - 1 else ''
                    import_lines.append(f"{indent}    {name}{comma}")
                import_lines.append(f"{indent})")
                new_import = '\n'.join(import_lines)
            
            # Replace the star import
            content = content[:match.start()] + new_import + content[match.end():]
            changes.append(f"Replaced 'from {module} import *' with explicit imports: {', '.join(sorted_names)}")
        else:
            # If no names are used, remove the import
            content = content[:match.start()] + content[match.end():]
            if match.start() > 0 and content[match.start()-1:match.start()] == '\n':
                content = content[:match.start()-1] + content[match.start():]
            changes.append(f"Removed unused 'from {module} import *'")
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True, changes
    
    return False, []

def main():
    """Fix all star imports in the codebase."""
    # Get all Python files with star imports
    import subprocess
    result = subprocess.run(
        ['docker', 'run', '--rm', '-v', f'{os.getcwd()}:/app', '-w', '/app', 'backend-lint', 
         'ruff', 'check', '.', '--select', 'F403'],
        capture_output=True, text=True
    )
    
    files_to_fix = set()
    for line in result.stdout.split('\n'):
        if 'F403' in line and '.py:' in line:
            file_path = line.split(':')[0]
            files_to_fix.add(file_path)
    
    print(f"Found {len(files_to_fix)} files with star imports to fix")
    
    total_changes = 0
    for file_path in sorted(files_to_fix):
        if os.path.exists(file_path):
            print(f"\nProcessing {file_path}...")
            changed, changes = fix_star_imports_in_file(file_path)
            if changed:
                total_changes += 1
                for change in changes:
                    print(f"  - {change}")
    
    print(f"\nFixed star imports in {total_changes} files")
    
    # Run ruff check again to see remaining issues
    print("\nRunning final check...")
    result = subprocess.run(
        ['docker', 'run', '--rm', '-v', f'{os.getcwd()}:/app', '-w', '/app', 'backend-lint', 
         'ruff', 'check', '.', '--select', 'F403,F405'],
        capture_output=True, text=True
    )
    
    error_count = len([line for line in result.stdout.split('\n') if 'F403' in line or 'F405' in line])
    print(f"Remaining F403/F405 errors: {error_count}")

if __name__ == '__main__':
    main()