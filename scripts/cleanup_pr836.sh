#!/bin/bash

# Cleanup PR-836: Keep only non-6R-specific changes
# Created: 2025-10-28
# Context: Before Assessment Flow migration (#611)

set -e

echo "=========================================="
echo "PR-836 Cleanup Script"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Commit multi-tenant security fix (AssetDependency)"
echo "2. Commit migration plan documentation"
echo "3. Discard all 6R Analysis code changes"
echo ""
echo "Press ENTER to continue, or Ctrl+C to cancel..."
read

echo ""
echo "Step 1: Staging files to keep..."
echo "=========================================="

# Stage multi-tenant security fix
git add backend/app/models/asset/relationships.py
echo "✅ Staged: backend/app/models/asset/relationships.py"

git add backend/alembic/versions/110_add_tenant_fields_to_asset_dependencies.py
echo "✅ Staged: backend/alembic/versions/110_add_tenant_fields_to_asset_dependencies.py"

# Stage migration plan documentation
git add docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md
echo "✅ Staged: docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md"

# Stage this analysis document
git add docs/planning/PR-836_CHANGES_ANALYSIS.md
echo "✅ Staged: docs/planning/PR-836_CHANGES_ANALYSIS.md"

echo ""
echo "Step 2: Committing kept changes..."
echo "=========================================="

git commit -m "fix: Add multi-tenant isolation to AssetDependency model

- Add client_account_id and engagement_id to asset_dependencies table
- Create migration 110 to backfill and add foreign keys
- Add migration plan for Assessment Flow implementation (#611)
- Add PR-836 changes analysis document

Security: Prevents cross-tenant access to asset dependencies
Ref: #611 - Assessment Flow migration preparation

Changes committed:
- backend/app/models/asset/relationships.py (multi-tenant fields)
- backend/alembic/versions/110_*.py (database migration)
- docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md (migration plan)
- docs/planning/PR-836_CHANGES_ANALYSIS.md (this analysis)

All 6R Analysis code changes discarded (will be deleted in migration)."

echo "✅ Commit created"

echo ""
echo "Step 3: Discarding 6R Analysis changes..."
echo "=========================================="

# Restore modified 6R Analysis files
git restore backend/app/api/v1/endpoints/sixr_analysis.py
echo "✅ Restored: sixr_analysis.py"

git restore backend/app/api/v1/endpoints/sixr_analysis_modular/handlers/analysis_handlers/__init__.py
echo "✅ Restored: analysis_handlers/__init__.py"

git restore backend/app/api/v1/endpoints/sixr_analysis_modular/services/background_tasks/initial_analysis_task.py
echo "✅ Restored: initial_analysis_task.py"

git restore backend/app/services/sixr_engine_modular.py
echo "✅ Restored: sixr_engine_modular.py"

git restore src/components/sixr/AnalysisProgress.tsx
echo "✅ Restored: AnalysisProgress.tsx"

git restore src/components/sixr/RecommendationDisplay.tsx
echo "✅ Restored: RecommendationDisplay.tsx"

git restore src/hooks/useSixRAnalysis.ts
echo "✅ Restored: useSixRAnalysis.ts"

git restore src/lib/api/sixr.ts
echo "✅ Restored: sixr.ts"

git restore src/pages/assess/Treatment.tsx
echo "✅ Restored: Treatment.tsx"

# Remove untracked 6R Analysis file
if [ -f "backend/app/api/v1/endpoints/sixr_analysis_modular/handlers/analysis_handlers/accept.py" ]; then
    rm backend/app/api/v1/endpoints/sixr_analysis_modular/handlers/analysis_handlers/accept.py
    echo "✅ Deleted: accept.py (untracked)"
fi

echo ""
echo "Step 4: Verification..."
echo "=========================================="

echo ""
echo "Git status:"
git status

echo ""
echo "=========================================="
echo "✅ PR-836 Cleanup Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Committed: Multi-tenant security fix + migration plan"
echo "- Discarded: All 6R Analysis code changes (will be deleted in migration)"
echo ""
echo "Next steps:"
echo "1. Review git log to verify commit"
echo "2. Push pr-836: git push origin pr-836"
echo "3. Merge PR-836"
echo "4. Create new branch: git checkout -b feature/assessment-flow-migration"
echo "5. Start Phase 1: See issue #837"
echo ""
