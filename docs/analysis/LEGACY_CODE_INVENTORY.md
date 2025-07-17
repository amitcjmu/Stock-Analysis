# Legacy and Unused Code Inventory

## Overview
- **Total files analyzed**: 450+
- **Total unused/legacy items found**: 47
- **Analysis date**: January 16, 2025
- **Platform version**: v1.16.0

## Agentic System Caveat
**⚠️ CRITICAL WARNING**: This analysis is based on static code references. Due to the platform's dynamic, agentic nature, some code flagged as "unused" may be called dynamically by CrewAI agents at runtime. The platform is also in active transition from legacy discovery APIs to the unified MasterFlowOrchestrator system. Manual verification is required before removal.

**Key Safety Considerations**:
- CrewAI agents in `backend/app/services/crew_services/` use dynamic tool calling
- Multi-tenant `ContextAwareRepository` patterns are critical for security
- Flow-based architecture components may be referenced indirectly
- Platform is transitioning from session-based to flow-based patterns

## Frontend Inventory

### High Confidence Unused (Safe to Remove)

| File Path | Code Element | Type | Reason for Flagging | Confidence Score | Recommendation |
|-----------|--------------|------|--------------------|------------------|----------------|
| `src/components/assessment/AssessmentFlowLayoutOld.tsx` | AssessmentFlowLayoutOld | Component | No imports found, marked as "Old" | 95% | Remove |
| `src/components/common/PollingErrorNotification.tsx` | PollingErrorNotification | Component | Only self-referential imports | 90% | Remove |
| `src/components/examples/DialogExamples.tsx` | DialogExamples | Component | Only used in E2E tests, example code | 85% | Remove |
| `src/hooks/discovery/useAttributeMappingLogic.DEPRECATED.ts` | useAttributeMappingLogic | Hook | Explicitly marked DEPRECATED | 80% | Remove |
| `src/utils/authDataMigration.ts` | authDataMigration | Utility | No imports found, likely one-time migration | 70% | Remove |
| `src/components/FlowCrewAgentMonitor.tsx.backup` | FlowCrewAgentMonitor | Backup | Backup file | 100% | Remove |
| `src/pages/discovery/CMDBImport.tsx.backup` | CMDBImport | Backup | Backup file | 100% | Remove |
| `src/pages/discovery/AttributeMapping.tsx.backup` | AttributeMapping | Backup | Backup file | 100% | Remove |
| `src/components/sixr/BulkAnalysis.tsx.backup` | BulkAnalysis | Backup | Backup file | 100% | Remove |
| `src/components/discovery/inventory/InventoryContent.tsx.backup` | InventoryContent | Backup | Backup file | 100% | Remove |

### Medium Confidence Unused (Investigate Further)

| File Path | Code Element | Type | Reason for Flagging | Confidence Score | Recommendation |
|-----------|--------------|------|--------------------|------------------|----------------|
| `src/hooks/useOptimisticFlow.ts` | useOptimisticFlow | Hook | Only self-referential imports | 75% | Investigate Further |
| `src/utils/migration/sessionToFlow.ts` | sessionToFlow | Utility | Limited imports, migration utility | 50% | Investigate Further |
| `src/components/ui/input-otp.tsx` | InputOTP | Component | UI component with limited usage | 60% | Investigate Further |
| `src/components/ui/menubar.tsx` | Menubar | Component | UI component with limited usage | 50% | Investigate Further |

### Low Confidence (Keep for Now - May be Used by Flow System)

| File Path | Code Element | Type | Reason for Flagging | Confidence Score | Recommendation |
|-----------|--------------|------|--------------------|------------------|----------------|
| `src/components/Phase2CrewMonitor.tsx` | Phase2CrewMonitor | Component | Used as fallback, phased rollout | 30% | Keep |
| `src/components/admin/SessionComparison.tsx` | SessionComparison | Component | Admin functionality, debugging | 40% | Keep |
| `src/hooks/useSixRWebSocket.ts` | useSixRWebSocket | Hook | May be used for real-time analysis | 35% | Keep |

## Backend Inventory

### High Confidence Unused (Safe to Remove)

| File Path | Code Element | Type | Reason for Flagging | Confidence Score | Recommendation |
|-----------|--------------|------|--------------------|------------------|----------------|
| `backend/app/api/v1/discovery/testing_endpoints.py` | TestingEndpoints | API | Not imported in main router | 95% | Remove |
| `backend/app/api/v1/discovery/database_test.py` | DatabaseTest | API | No imports found | 95% | Remove |
| `backend/app/api/v1/endpoints/workflow_integration.py` | WorkflowIntegration | API | No imports, replaced by MFO | 95% | Remove |
| `backend/app/api/v1/endpoints/discovery_escalation.py` | DiscoveryEscalation | API | Not imported anywhere | 90% | Remove |
| `backend/app/api/v1/admin/session_comparison_modular.py` | SessionComparisonModular | API | No imports, duplicate implementation | 95% | Remove |
| `backend/app/api/v1/admin/client_management_original.py` | ClientManagementOriginal | API | Backup version | 95% | Remove |
| `backend/app/services/discovery_flow_cleanup_service_v2.py` | DiscoveryFlowCleanupServiceV2 | Service | No imports, superseded | 95% | Remove |
| `backend/app/services/agent_ui_bridge_example.py` | AgentUIBridgeExample | Service | Example file | 95% | Remove |
| `backend/app/services/master_flow_orchestrator_original.py` | MasterFlowOrchestratorOriginal | Service | Backup implementation | 95% | Remove |
| `backend/app/services/asset_processing_service.py` | AssetProcessingService | Service | No imports found | 90% | Remove |
| `backend/app/services/escalation/crew_escalation_manager.py` | CrewEscalationManager | Service | Only used by unused endpoint | 85% | Remove |

### Medium Confidence Unused (Investigate Further)

| File Path | Code Element | Type | Reason for Flagging | Confidence Score | Recommendation |
|-----------|--------------|------|--------------------|------------------|----------------|
| `backend/app/api/v1/endpoints/simple_admin.py` | SimpleAdmin | API | Conditionally imported | 70% | Investigate Further |
| `backend/app/api/v1/discovery_flow_v2.py` | DiscoveryFlowV2 | API | Commented out in router | 80% | Deprecate |
| `backend/app/services/multi_model_service.py` | MultiModelService | Service | May be used by CrewAI | 70% | Investigate Further |
| `backend/app/services/analysis_modular.py` | AnalysisModular | Service | May be used by analysis endpoints | 65% | Investigate Further |

## Database Inventory

### High Confidence Unused Models (Safe to Remove)

| File Path | Code Element | Type | Reason for Flagging | Confidence Score | Recommendation |
|-----------|--------------|------|--------------------|------------------|----------------|
| `backend/app/models/sixr_analysis.py` | WorkflowProgress | Model | No table exists in migrations | 90% | Remove |
| `backend/app/models/sixr_analysis.py` | SixRIteration | Model | No table exists in migrations | 90% | Remove |
| `backend/app/models/sixr_analysis.py` | SixRRecommendation | Model | No table exists in migrations | 90% | Remove |
| `backend/app/models/sixr_analysis.py` | SixRQuestion | Model | No table exists in migrations | 90% | Remove |
| `backend/app/models/asset.py` | CMDBSixRAnalysis | Model | No table exists in migrations | 85% | Remove |
| `backend/app/models/asset.py` | MigrationWave | Model | No table exists in migrations | 85% | Remove |
| `backend/app/models/feedback.py` | FeedbackSummary | Model | No table exists, not used | 80% | Remove |

### Medium Confidence - Architecture Decision Needed

| File Path | Code Element | Type | Reason for Flagging | Confidence Score | Recommendation |
|-----------|--------------|------|--------------------|------------------|----------------|
| `backend/app/models/rbac_enhanced.py` | EnhancedUserProfile | Model | Duplicate RBAC implementation | 70% | Consolidate RBAC |
| `backend/app/models/rbac_enhanced.py` | RolePermission | Model | Enhanced RBAC not implemented | 70% | Archive or Implement |
| `backend/app/services/models/agent_communication.py` | AgentQuestion | Model | Duplicate location | 70% | Consolidate |

### Low Confidence (Keep - Critical for Architecture)

| File Path | Code Element | Type | Reason for Flagging | Confidence Score | Recommendation |
|-----------|--------------|------|--------------------|------------------|----------------|
| `backend/app/models/agent_memory.py` | AgentDiscoveredPattern | Model | Part of three-tier memory | 20% | Keep |
| `backend/app/models/asset.py` | Asset | Model | Core multi-tenant model | 5% | Keep |
| `backend/app/models/client_account.py` | ClientAccount | Model | Core multi-tenant model | 5% | Keep |

## Archive Directory (Already Identified as Unused)

All files in `src/archive/` directory are confirmed unused and should be removed:
- `components/discovery/DiscoveryFlowV2Dashboard.tsx`
- `components/discovery/RealTimeProcessingMonitor.tsx`
- `components/discovery/UploadBlockerV2.tsx`
- `pages/assessment/DemoInitializeFlow.tsx`
- `pages/discovery/AssetInventory.tsx`
- `pages/discovery/AssetInventoryRedesigned.tsx`
- `pages/discovery/DataImportDemo.tsx`
- `services/discoveryFlowV2Service.ts`

## Recommended Cleanup Strategy

### Phase 1: High Confidence Removals (Safe)
1. Remove all `.backup` files
2. Remove explicitly marked DEPRECATED files
3. Remove testing and example files
4. Remove database models with no corresponding tables

### Phase 2: Architecture Consolidation
1. Choose between RBAC implementations (rbac.py vs rbac_enhanced.py)
2. Consolidate duplicate agent_communication models
3. Deprecate commented-out API endpoints
4. Archive unused service classes

### Phase 3: Investigation Required
1. Verify usage of conditionally imported modules
2. Check if optimistic flow features are planned
3. Validate migration utilities are no longer needed
4. Confirm UI components are not used

## Critical Safety Notes

1. **DO NOT REMOVE**:
   - Anything in `backend/app/services/crew_services/` (CrewAI dynamic usage)
   - Anything in `backend/app/services/crewai_flows/` (Core flow management)
   - Multi-tenant models and repositories (Security critical)
   - Core authentication and authorization code
   - Flow state management components

2. **VERIFY BEFORE REMOVING**:
   - Check if code is used by external systems
   - Verify CrewAI agents don't reference utilities dynamically
   - Confirm migration from legacy to new architecture is complete
   - Test removal in development environment first

3. **ESTIMATED IMPACT**:
   - **Frontend**: ~15-20% reduction in component count
   - **Backend**: ~10-15% reduction in API endpoints and services
   - **Database**: ~25-30% reduction in model complexity
   - **Overall**: ~5-10% reduction in codebase size

## Implementation Checklist

- [ ] Create feature branch for cleanup
- [ ] Start with Phase 1 (high confidence removals)
- [ ] Run full test suite after each phase
- [ ] Update import statements and dependencies
- [ ] Update documentation to reflect removed features
- [ ] Create migration scripts for database changes
- [ ] Archive removed files for 2 sprint cycles
- [ ] Update CHANGELOG.md with cleanup summary

---

**Last Updated**: July 16, 2025  
**Review Required**: Manual verification before any removals  
**Next Review**: After cleanup implementation