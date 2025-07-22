#!/usr/bin/env python3
"""Script to fix F401 (unused imports) in services directory"""

import subprocess
import re
import os
from typing import Dict, List, Tuple

def get_f401_errors(directory: str) -> Dict[str, List[Tuple[str, str]]]:
    """Get all F401 errors grouped by file"""
    cmd = ["docker", "run", "--rm", "backend-lint", "ruff", "check", directory, "--select", "F401"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    errors_by_file = {}
    
    for line in result.stderr.split('\n'):
        # Parse error lines like: app/services/file.py:11:32: F401 [*] `module.item` imported but unused
        match = re.match(r'^(app/services/[^:]+):(\d+):(\d+): F401 \[\*\] `([^`]+)` imported but unused', line)
        if match:
            filepath = match.group(1)
            import_name = match.group(4)
            
            if filepath not in errors_by_file:
                errors_by_file[filepath] = []
            errors_by_file[filepath].append((import_name, line))
    
    return errors_by_file

def fix_file_imports(filepath: str, unused_imports: List[Tuple[str, str]]) -> bool:
    """Fix unused imports in a single file"""
    try:
        # Read file
        full_path = os.path.join("/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend", filepath)
        with open(full_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix each unused import
        for import_name, error_line in unused_imports:
            # Handle different import patterns
            patterns = [
                # from module import unused
                (rf'from\s+[\w\.]+\s+import\s+.*\b{re.escape(import_name)}\b[,\s]*', 
                 lambda m: remove_import_item(m.group(0), import_name)),
                
                # import unused
                (rf'^import\s+{re.escape(import_name)}\s*$', ''),
            ]
            
            # Handle datetime.timedelta style
            if '.' in import_name:
                module, item = import_name.rsplit('.', 1)
                patterns.append((rf'from\s+{re.escape(module)}\s+import\s+.*\b{re.escape(item)}\b[,\s]*',
                 lambda m: remove_import_item(m.group(0), item)))
            
            for pattern, replacement in patterns:
                if callable(replacement):
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                else:
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Clean up empty import lines
        content = re.sub(r'^from\s+[\w\.]+\s+import\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n\n\n+', '\n\n', content)  # Remove multiple blank lines
        
        if content != original_content:
            with open(full_path, 'w') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def remove_import_item(import_line: str, item: str) -> str:
    """Remove an item from an import statement"""
    # Handle parentheses imports
    if '(' in import_line and ')' in import_line:
        # Multi-line import
        import_line = re.sub(rf'\b{re.escape(item)}\b\s*,?\s*', '', import_line)
        # Clean up trailing commas
        import_line = re.sub(r',\s*\)', ')', import_line)
        import_line = re.sub(r',\s*$', '', import_line)
    else:
        # Single line import
        import_line = re.sub(rf',?\s*\b{re.escape(item)}\b\s*,?', '', import_line)
        # Clean up double commas
        import_line = re.sub(r',,+', ',', import_line)
        # Clean up leading/trailing commas
        import_line = re.sub(r'import\s*,', 'import', import_line)
        import_line = re.sub(r',\s*$', '', import_line)
    
    return import_line

def main():
    print("Fixing F401 errors in app/services directory...")
    
    # Get all F401 errors
    errors = get_f401_errors("app/services")
    
    print(f"Found F401 errors in {len(errors)} files")
    
    fixed_count = 0
    total_errors = sum(len(imports) for imports in errors.values())
    
    # Fix each file
    for filepath, unused_imports in errors.items():
        print(f"Fixing {filepath} ({len(unused_imports)} unused imports)")
        if fix_file_imports(filepath, unused_imports):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files with {total_errors} total F401 errors")
    
    # Verify fixes
    print("\nVerifying fixes...")
    remaining = get_f401_errors("app/services")
    remaining_count = sum(len(imports) for imports in remaining.values())
    
    print(f"Remaining F401 errors: {remaining_count}")
    
    if remaining_count > 0:
        print("\nRemaining errors in files:")
        for filepath, imports in list(remaining.items())[:10]:
            print(f"  {filepath}: {len(imports)} errors")

if __name__ == "__main__":
    main()