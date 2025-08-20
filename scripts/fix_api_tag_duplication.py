#!/usr/bin/env python3
"""
Fix API tag duplication in FastAPI routers.
This script removes tags from individual router definitions when they're
already being set during include_router() calls.
"""

import os
import re
from pathlib import Path

def fix_router_tags(file_path):
    """Remove tags from APIRouter() calls if they will be overridden."""

    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern to match APIRouter with tags parameter
    # This will match: APIRouter(prefix="/...", tags=["..."])
    # or APIRouter(tags=["..."])
    pattern = r'(APIRouter\([^)]*?)(\s*,?\s*tags\s*=\s*\[[^\]]+\])([^)]*\))'

    # Remove tags parameter from APIRouter calls
    content = re.sub(pattern, r'\1\3', content)

    # Clean up any double commas that might result
    content = re.sub(r',\s*,', ',', content)
    content = re.sub(r'\(\s*,', '(', content)

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to process all router files."""

    # List of files where we should KEEP the tags (main router includes)
    keep_tags_files = [
        'backend/app/api/v1/api.py',
    ]

    # Files to process (remove tags from)
    files_to_fix = [
        'backend/app/api/v1/endpoints/agents/__init__.py',
        'backend/app/api/v1/endpoints/field_mapping.py',
        'backend/app/api/v1/endpoints/data_import/field_mapping_modular.py',
        'backend/app/api/v1/endpoints/assessment_flow.py',
        'backend/app/api/v1/endpoints/assessment_events.py',
        'backend/app/api/v1/endpoints/agent_events.py',
        'backend/app/api/v1/endpoints/agents/discovery/router.py',
        'backend/app/api/v1/endpoints/data_import/field_mapping/routes/mapping_routes.py',
        'backend/app/api/v1/endpoints/data_import/field_mapping/routes/suggestion_routes.py',
        'backend/app/api/v1/endpoints/data_import/field_mapping/routes/validation_routes.py',
        'backend/app/api/v1/endpoints/data_import/field_mapping/routes/approval_routes.py',
        'backend/app/api/v1/endpoints/asset_inventory/__init__.py',
        'backend/app/api/v1/endpoints/asset_inventory/crud.py',
        'backend/app/api/v1/endpoints/asset_inventory/pagination.py',
        'backend/app/api/v1/endpoints/asset_inventory/intelligence.py',
        'backend/app/api/v1/endpoints/asset_inventory/audit.py',
        'backend/app/api/v1/endpoints/asset_inventory/analysis.py',
        # Additional files with embedded tags
        'backend/app/api/v1/endpoints/agents/discovery/handlers/analysis.py',
        'backend/app/api/v1/endpoints/agents/discovery/handlers/dependencies.py',
        'backend/app/api/v1/endpoints/agents/discovery/handlers/learning.py',
        'backend/app/api/v1/endpoints/agents/discovery/handlers/status.py',
        'backend/app/api/v1/endpoints/cached_context.py',
        'backend/app/api/v1/endpoints/context/api/__init__.py',
        'backend/app/api/v1/endpoints/data_import/agentic_critical_attributes/routes/analysis_routes.py',
        'backend/app/api/v1/endpoints/data_import/agentic_critical_attributes/routes/feedback_routes.py',
        'backend/app/api/v1/endpoints/data_import/agentic_critical_attributes/routes/suggestion_routes.py',
        'backend/app/api/v1/endpoints/data_import/handlers/clean_api_handler.py',
        'backend/app/api/v1/endpoints/system/emergency.py',
        'backend/app/api/v1/endpoints/websocket_cache.py',
    ]

    fixed_count = 0

    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_router_tags(file_path):
                print(f"✅ Fixed tags in: {file_path}")
                fixed_count += 1
            else:
                print(f"⏭️  No changes needed in: {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

    print(f"\n📊 Summary: Fixed {fixed_count} files")

    # Now let's also standardize the tags in api.py
    api_file = 'backend/app/api/v1/api.py'
    if os.path.exists(api_file):
        with open(api_file, 'r') as f:
            content = f.read()

        # Standardize tag names (use Title Case, singular form)
        replacements = [
            ('tags=["agents"]', 'tags=["Agent"]'),
            ('tags=["Agents"]', 'tags=["Agent"]'),
            ('tags=["field-mapping"]', 'tags=["Field Mapping"]'),
            ('tags=["field-mappings"]', 'tags=["Field Mapping"]'),
            ('tags=["Field Mappings"]', 'tags=["Field Mapping"]'),
            ('tags=["Assessment Flow Events"]', 'tags=["Assessment Flow"]'),
            ('tags=["Flow Events"]', 'tags=["Agent Event"]'),
        ]

        original_content = content
        for old, new in replacements:
            content = content.replace(old, new)

        if content != original_content:
            with open(api_file, 'w') as f:
                f.write(content)
            print(f"✅ Standardized tags in: {api_file}")

    return fixed_count

if __name__ == "__main__":
    main()
