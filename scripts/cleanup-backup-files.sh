#!/bin/bash

# Legacy Code Cleanup - Phase 1: Remove Backup Files
# These files are 100% safe to remove as they are backup copies

echo "🧹 Starting backup file cleanup..."

# List of backup files to remove
BACKUP_FILES=(
    "backend/app/api/v1/admin/engagement_management_handlers/engagement_crud_handler.py.backup"
    "CHANGELOG.md.backup"
    "src/components/discovery/inventory/InventoryContent.tsx.backup"
    "src/pages/discovery/CMDBImport.tsx.backup"
    "src/components/FlowCrewAgentMonitor.tsx.backup"
    "src/pages/discovery/AttributeMapping.tsx.backup"
    "src/components/sixr/BulkAnalysis.tsx.backup"
    "package.json.backup"
    "backend/requirements-docker.txt.backup"
)

# Remove each backup file
for file in "${BACKUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Removing: $file"
        rm "$file"
    else
        echo "Already removed or not found: $file"
    fi
done

echo "✅ Backup file cleanup completed!"
echo "Removed $(echo "${BACKUP_FILES[@]}" | wc -w) backup files"
