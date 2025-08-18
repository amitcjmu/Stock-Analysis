#!/bin/bash

# Script to clean up orphaned files from incomplete modularization (PR116 & PR118)

echo "🧹 Starting cleanup of orphaned modularization files..."

# 1. Azure Adapter Cleanup
echo "📁 Cleaning up Azure Adapter files..."

# Check if module directory exists and has proper structure
if [ -d "backend/app/services/adapters/azure_adapter" ]; then
    echo "✅ Azure adapter module directory exists"

    # Remove the old monolithic file
    if [ -f "backend/app/services/adapters/azure_adapter.py" ]; then
        echo "  🗑️  Removing old monolithic azure_adapter.py"
        rm "backend/app/services/adapters/azure_adapter.py"
    fi

    # Remove backup file
    if [ -f "backend/app/services/adapters/azure_adapter.py.backup" ]; then
        echo "  🗑️  Removing azure_adapter.py.backup"
        rm "backend/app/services/adapters/azure_adapter.py.backup"
    fi

    # Remove duplicate split files from parent directory
    for file in azure_adapter_auth.py azure_adapter_compute.py azure_adapter_data.py azure_adapter_storage.py azure_adapter_utils.py; do
        if [ -f "backend/app/services/adapters/$file" ]; then
            echo "  🗑️  Removing duplicate $file from parent directory"
            rm "backend/app/services/adapters/$file"
        fi
    done
else
    echo "⚠️  Azure adapter module directory not found!"
fi

# 2. Collection Endpoint Cleanup
echo "📁 Checking Collection endpoint files..."

# Check the state of collection files
if [ -f "backend/app/api/v1/endpoints/collection.py" ] && [ -f "backend/app/api/v1/endpoints/collection_crud.py" ]; then
    echo "  ⚠️  Both collection.py and collection_crud.py exist - needs investigation"
    # We'll handle this after checking what imports what
fi

# 3. Assessment Flow Cleanup
echo "📁 Checking Assessment Flow files..."

# Check for assessment flow duplicates
if [ -f "backend/app/api/v1/endpoints/assessment_flow.py" ] && [ -f "backend/app/api/v1/endpoints/assessment_flow_crud.py" ]; then
    echo "  ⚠️  Both assessment_flow.py and assessment_flow_crud.py exist"
fi

# 4. CrewAI Flow Service Cleanup
echo "📁 Checking CrewAI Flow Service files..."

# Check for crewai flow service files
if [ -f "backend/app/services/crewai_flow_service.py" ] && [ -f "backend/app/services/crewai_flow_service_original.py" ]; then
    echo "  🗑️  Removing backup file crewai_flow_service_original.py"
    rm "backend/app/services/crewai_flow_service_original.py"
fi

# Check if there are split files for crewai_flow_service
for file in crewai_flow_executor.py crewai_flow_lifecycle.py crewai_flow_monitoring.py crewai_flow_state_manager.py crewai_flow_utils.py; do
    if [ -f "backend/app/services/$file" ]; then
        echo "  ✅ Found modular file: $file"
    fi
done

# 5. Check for test files that should be removed
echo "📁 Cleaning up test files from root backend..."

for test_file in test_api_integration.py test_breaking_changes.py test_modularization.py test_modularization_isolated.py test_service_functionality.py test_specific_imports.py; do
    if [ -f "backend/$test_file" ]; then
        echo "  🗑️  Removing test file from backend root: $test_file"
        rm "backend/$test_file"
    fi
done

# 6. Look for other potential duplicates
echo "📁 Searching for other potential duplicate/orphaned files..."

# Find Python files with .backup extension
find backend -name "*.py.backup" -type f 2>/dev/null | while read -r file; do
    echo "  🗑️  Removing backup file: $file"
    rm "$file"
done

# Find files with _original suffix
find backend -name "*_original.py" -type f 2>/dev/null | while read -r file; do
    echo "  🗑️  Removing original backup: $file"
    rm "$file"
done

echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary of actions:"
echo "  - Removed orphaned azure_adapter files"
echo "  - Removed test files from backend root"
echo "  - Removed backup and original files"
echo ""
echo "⚠️  Manual review needed for:"
echo "  - Collection endpoint structure (collection.py vs collection_crud.py)"
echo "  - Assessment flow structure"
echo "  - Verify imports are using correct module paths"
