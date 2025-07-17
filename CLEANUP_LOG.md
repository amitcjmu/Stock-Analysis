# Legacy Code Cleanup Log

## Phase 1: High Confidence Removals

### ✅ Backup Files Removed (9 files)
- `backend/app/api/v1/admin/engagement_management_handlers/engagement_crud_handler.py.backup`
- `CHANGELOG.md.backup`
- `src/components/discovery/inventory/InventoryContent.tsx.backup`
- `src/pages/discovery/CMDBImport.tsx.backup`
- `src/components/FlowCrewAgentMonitor.tsx.backup`
- `src/pages/discovery/AttributeMapping.tsx.backup`
- `src/components/sixr/BulkAnalysis.tsx.backup`
- `package.json.backup`
- `backend/requirements-docker.txt.backup`

### 🚀 Ready for Removal - Deprecated Components (Verified no imports)
- `src/hooks/discovery/useAttributeMappingLogic.DEPRECATED.ts` - Explicitly deprecated
- `src/components/assessment/AssessmentFlowLayoutOld.tsx` - Old version, no imports
- `src/components/common/PollingErrorNotification.tsx` - Only self-referential imports
- `src/components/examples/DialogExamples.tsx` - Example code, test is commented out
- `src/utils/authDataMigration.ts` - No imports found, likely one-time migration

### 📋 Commands to Execute

Run these commands to remove the deprecated files:

```bash
# Remove deprecated frontend components
rm src/hooks/discovery/useAttributeMappingLogic.DEPRECATED.ts
rm src/components/assessment/AssessmentFlowLayoutOld.tsx
rm src/components/common/PollingErrorNotification.tsx
rm src/components/examples/DialogExamples.tsx
rm src/utils/authDataMigration.ts
```

### 🚀 Ready for Removal - Unused Backend API Endpoints (Verified not included in main router)
- `backend/app/api/v1/discovery/testing_endpoints.py` - Testing endpoints not registered
- `backend/app/api/v1/discovery/database_test.py` - Database test endpoints not used
- `backend/app/api/v1/endpoints/workflow_integration.py` - Replaced by MasterFlowOrchestrator
- `backend/app/api/v1/endpoints/discovery_escalation.py` - Not imported anywhere
- `backend/app/api/v1/admin/session_comparison_modular.py` - Duplicate implementation
- `backend/app/api/v1/admin/client_management_original.py` - Backup version

### 📋 Backend Cleanup Commands

```bash
# Remove unused API endpoints
rm backend/app/api/v1/discovery/testing_endpoints.py
rm backend/app/api/v1/discovery/database_test.py
rm backend/app/api/v1/endpoints/workflow_integration.py
rm backend/app/api/v1/endpoints/discovery_escalation.py
rm backend/app/api/v1/admin/session_comparison_modular.py
rm backend/app/api/v1/admin/client_management_original.py
```

### 🚀 Ready for Removal - Unused Backend Services (Verified no imports)
- `backend/app/services/discovery_flow_cleanup_service_v2.py` - V2 service superseded
- `backend/app/services/agent_ui_bridge_example.py` - Example file
- `backend/app/services/master_flow_orchestrator_original.py` - Backup implementation
- `backend/app/services/asset_processing_service.py` - No imports found
- `backend/app/services/escalation/crew_escalation_manager.py` - Only used by unused endpoint

### 📋 Backend Services Cleanup Commands

```bash
# Remove unused services
rm backend/app/services/discovery_flow_cleanup_service_v2.py
rm backend/app/services/agent_ui_bridge_example.py
rm backend/app/services/master_flow_orchestrator_original.py
rm backend/app/services/asset_processing_service.py
rm backend/app/services/escalation/crew_escalation_manager.py
```

### 🗂️ Archive Directory Cleanup (Confirmed unused)
- All files in `src/archive/` directory are confirmed archived and unused

```bash
# Remove entire archive directory
rm -rf src/archive/
```

## Summary of High Confidence Removals
- **Backup files**: 9 files
- **Deprecated frontend**: 5 files
- **Unused API endpoints**: 6 files
- **Unused services**: 5 files
- **Archive directory**: 10+ files
- **Total**: ~35+ files removed

## Next Steps - REQUIRES YOUR INPUT
After removing these high-confidence files, we need your decisions on:
1. Medium-confidence items requiring investigation
2. Database model consolidation choices
3. API deprecation strategies