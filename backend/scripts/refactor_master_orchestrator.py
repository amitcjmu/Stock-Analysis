#!/usr/bin/env python3
"""
Script to refactor MasterFlowOrchestrator by removing extracted methods
and creating a smaller, more focused class.
"""

from pathlib import Path

# Define the methods to remove (they've been extracted to services)
METHODS_TO_REMOVE = [
    "_smart_flow_discovery",
    "_find_related_data_by_timestamp", 
    "_find_related_data_by_context",
    "_find_in_flow_persistence",
    "_build_status_from_discovered_data",
    "_retrieve_field_mappings_from_discovered_data",
    "_find_orphaned_data_for_flow",
    "_generate_repair_options",
    "_summarize_orphaned_data"
]

def refactor_master_orchestrator():
    """Remove extracted methods from MasterFlowOrchestrator"""
    
    file_path = Path("/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/master_flow_orchestrator.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    skip_until_next_method = False
    method_indent = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a method we want to remove
        if skip_until_next_method:
            # Skip lines until we find a method/function at the same or lower indentation level
            current_indent = len(line) - len(line.lstrip())
            
            # If we hit a method/function at same or lower level, stop skipping
            if (line.strip().startswith('def ') or line.strip().startswith('async def ')) and current_indent <= method_indent:
                skip_until_next_method = False
                new_lines.append(line)
            elif line.strip() == '' or current_indent > method_indent:
                # Skip empty lines and lines with deeper indentation
                pass
            else:
                # We've reached content at the same level, stop skipping
                skip_until_next_method = False
                new_lines.append(line)
        else:
            # Check if this line starts a method we want to remove
            method_found = False
            for method_name in METHODS_TO_REMOVE:
                if f"async def {method_name}(" in line or f"def {method_name}(" in line:
                    method_found = True
                    method_indent = len(line) - len(line.lstrip())
                    skip_until_next_method = True
                    
                    # Add a comment explaining what was removed
                    indent = ' ' * method_indent
                    new_lines.append(f"{indent}# {method_name} method extracted to service")
                    break
            
            if not method_found:
                new_lines.append(line)
        
        i += 1
    
    # Write the refactored content
    new_content = '\n'.join(new_lines)
    
    # Create backup
    backup_path = file_path.with_suffix('.py.backup')
    with open(backup_path, 'w') as f:
        f.write(content)
    
    # Write refactored version
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Refactored MasterFlowOrchestrator")
    print(f"📁 Backup saved to: {backup_path}")
    
    # Count lines saved
    original_lines = len(content.split('\n'))
    new_lines_count = len(new_content.split('\n'))
    saved_lines = original_lines - new_lines_count
    
    print(f"📊 Reduced from {original_lines} to {new_lines_count} lines ({saved_lines} lines saved)")

if __name__ == "__main__":
    refactor_master_orchestrator()