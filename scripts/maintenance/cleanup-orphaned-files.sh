#!/bin/bash
# Script to remove orphaned/unused legacy files

echo "Removing orphaned legacy files..."

# Remove unused hooks
rm -f src/hooks/useDataCleansingAnalysis.ts
echo "✓ Removed useDataCleansingAnalysis.ts (orphaned)"

# Remove unused components
rm -f src/components/discovery/MemoryKnowledgePanel.tsx
echo "✓ Removed MemoryKnowledgePanel.tsx (orphaned)"

rm -f src/components/discovery/AgentCommunicationPanel.tsx
echo "✓ Removed AgentCommunicationPanel.tsx (orphaned)"

# Remove deprecated service with compilation errors
rm -f src/services/dataImportV2Service.ts
echo "✓ Removed dataImportV2Service.ts (has compilation errors, not used)"

# Remove non-existent file references
rm -f src/hooks/discovery/useTechDebtQueries.ts 2>/dev/null
echo "✓ Checked useTechDebtQueries.ts (already doesn't exist)"

echo "Cleanup complete!"
