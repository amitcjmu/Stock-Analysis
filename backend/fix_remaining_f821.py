#!/usr/bin/env python3
"""Fix remaining F821 undefined name errors with more specific imports."""

import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path

# Additional import mappings for undefined names not caught in first pass
ADDITIONAL_MAPPINGS = {
    # Variables that need context
    'user_id': 'from app.core.context import get_current_user',
    'websocket': 'from fastapi import WebSocket',
    
    # Missing SQLAlchemy imports
    'distinct': 'from sqlalchemy import distinct',
    
    # Project-specific models/schemas
    'DataQualityIssue': 'from app.schemas.data_import_schemas import DataQualityIssue',
    'AgentReasoning': 'from app.models.agent_models import AgentReasoning',
    'DiscoveryAsset': 'from app.models.discovery_models import DiscoveryAsset',
    'RequestContext': 'from app.core.context import RequestContext',
    'FieldMapping': 'from app.models.field_mapping import FieldMapping',
    'FieldType': 'from app.schemas.field_mapping import FieldType',
    'IntelligentAnalyzer': 'from app.services.ai_analysis.intelligent_analyzer import IntelligentAnalyzer',
    
    # Constants
    'MAX_DELEGATIONS': 'MAX_DELEGATIONS = 5',
    'ENGAGEMENT_AVAILABLE': 'ENGAGEMENT_AVAILABLE = True',
    
    # Python built-ins
    're': 'import re',
    'concurrent': 'import concurrent.futures',
    'true': 'True',  # This is a typo fix
    
    # Services that should be imported instances
    'asset_debt_by_asset': 'from app.services.tech_debt_analysis_service import asset_debt_by_asset',
    
    # Flow-related
    'flow': 'from app.models.flow import flow',
}

def fix_specific_issues(file_path, content, undefined_names):
    """Fix specific issues that need special handling."""
    lines = content.split('\n')
    modified = False
    
    # Special case: user_id in chat_interface.py
    if 'chat_interface.py' in file_path and 'user_id' in undefined_names:
        # Find the function definition and extract user_id from context
        for i, line in enumerate(lines):
            if 'await save_chat_message(user_id' in line:
                # Check if we're in a function that should have user_id
                # Look backwards for function definition
                for j in range(i-1, max(0, i-20), -1):
                    if 'async def' in lines[j] and 'context:' in lines[j]:
                        # Extract user_id from context
                        lines.insert(j+1, '    user_id = context.get("user_id", "anonymous")')
                        modified = True
                        break
                    elif 'async def' in lines[j] and 'current_user' in lines[j]:
                        # Use current_user
                        lines.insert(j+1, '    user_id = current_user.id if current_user else "anonymous"')
                        modified = True
                        break
    
    # Special case: websocket in chat_interface.py
    if 'chat_interface.py' in file_path and 'websocket' in undefined_names:
        # This is likely in a WebSocket handler, check the function signature
        for i, line in enumerate(lines):
            if 'await websocket.send_text' in line:
                # Look backwards for function definition
                for j in range(i-1, max(0, i-20), -1):
                    if 'async def' in lines[j] and 'WebSocket' not in lines[j]:
                        # Add websocket parameter
                        lines[j] = lines[j].replace(')', ', websocket: WebSocket)')
                        modified = True
                        break
    
    # Fix 'true' typo to 'True'
    if 'true' in undefined_names:
        for i, line in enumerate(lines):
            if ' true' in line or '=true' in line:
                lines[i] = re.sub(r'\btrue\b', 'True', lines[i])
                modified = True
    
    # Fix missing service instances
    if 'crewai_flow_service' in undefined_names:
        # Add import at module level
        import_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not (line.startswith('import ') or line.startswith('from ')):
                import_idx = i
                break
        lines.insert(import_idx, 'from app.services.crewai_flow_service import crewai_flow_service')
        modified = True
    
    if modified:
        return '\n'.join(lines)
    return content

def add_imports_intelligently(file_path, content, undefined_names):
    """Add imports intelligently based on file context."""
    lines = content.split('\n')
    
    # Find import section
    import_end_idx = 0
    has_imports = False
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            has_imports = True
            import_end_idx = i + 1
        elif has_imports and line.strip() and not line.startswith('#'):
            break
    
    # If no imports, add after docstring
    if not has_imports:
        for i, line in enumerate(lines):
            if i > 0 and (lines[i-1].strip() == '"""' or lines[i-1].strip().endswith('"""')):
                import_end_idx = i
                break
    
    imports_to_add = []
    constants_to_add = []
    
    for name in undefined_names:
        if name in ADDITIONAL_MAPPINGS:
            mapping = ADDITIONAL_MAPPINGS[name]
            if '=' in mapping and not mapping.startswith('from ') and not mapping.startswith('import '):
                # It's a constant definition
                constants_to_add.append(mapping)
            else:
                imports_to_add.append(mapping)
    
    # Add imports
    if imports_to_add:
        for imp in reversed(sorted(set(imports_to_add))):
            lines.insert(import_end_idx, imp)
    
    # Add constants after imports
    if constants_to_add:
        const_idx = import_end_idx + len(imports_to_add)
        if lines[const_idx].strip():
            lines.insert(const_idx, '')
            const_idx += 1
        for const in constants_to_add:
            lines.insert(const_idx, const)
    
    return '\n'.join(lines)

def fix_file_advanced(file_path, undefined_names):
    """Fix file with advanced strategies."""
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # First try specific fixes
    content = fix_specific_issues(file_path, content, undefined_names)
    
    # Then add imports
    content = add_imports_intelligently(file_path, content, undefined_names)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    
    return False

def main():
    # Get current F821 errors
    result = subprocess.run(
        ['docker', 'run', '--rm', '-v', f'{os.getcwd()}:/app', '-w', '/app', 
         'backend-lint', 'ruff', 'check', '.', '--select', 'F821'],
        capture_output=True,
        text=True
    )
    
    errors = defaultdict(set)
    pattern = r'(.+?):(\d+):(\d+): F821 Undefined name `(.+?)`'
    
    for match in re.finditer(pattern, result.stdout):
        file_path = match.group(1)
        undefined_name = match.group(4)
        errors[file_path].add(undefined_name)
    
    print(f"Found F821 errors in {len(errors)} files")
    
    fixed_count = 0
    for file_path, undefined_names in errors.items():
        print(f"\nProcessing {file_path}...")
        print(f"  Undefined names: {', '.join(sorted(undefined_names))}")
        
        if fix_file_advanced(file_path, undefined_names):
            fixed_count += 1
            print("  Fixed!")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()