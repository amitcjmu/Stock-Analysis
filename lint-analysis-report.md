
# ESLint Analysis Report - Migration UI Orchestrator

## Executive Summary
- **Total Issues**: 2,193
- **Total Errors**: 2,121
- **Total Warnings**: 72

## Issue Categorization by Priority

### 1. Critical/Blocking Issues (Compilation Blockers)
**Count**: 2050
**Impact**: These prevent successful compilation and must be fixed immediately.

Common Issues:
- typescript-eslint/no-explicit-any: 2037 occurrences
- no-case-declarations: 6 occurrences
- expected: 4 occurrences
- no-constant-condition: 1 occurrences
- no-constant-binary-expression: 1 occurrences

### 2. High Priority Issues (Runtime/Logic Errors)
**Count**: 51
**Impact**: These can cause runtime errors or incorrect behavior.

Common Issues:
- react-hooks/exhaustive-deps: 45 occurrences
- react-hooks/rules-of-hooks: 6 occurrences

### 3. Medium Priority Issues (Type Safety & Code Quality)
**Count**: 44
**Impact**: These affect type safety, maintainability, and code quality.

Common Issues:
- typescript-eslint/no-namespace: 32 occurrences
- typescript-eslint/no-require-imports: 9 occurrences
- react-hooks/exhaustive-deps: 3 occurrences

### 4. Low Priority Issues (Style & Conventions)
**Count**: 38
**Impact**: These are style and convention issues with minimal functional impact.

Common Issues:
- react-refresh/only-export-components: 24 occurrences
- prefer-const: 7 occurrences
- no-useless-catch: 7 occurrences

## Most Problematic Files (Top 20)
- src/types/components/data-display.ts: 186 issues
- src/types/discovery.ts: 127 issues
- src/types/modules/shared-utilities.ts: 118 issues
- src/types/components/forms.ts: 117 issues
- src/types/hooks/api.ts: 100 issues
- src/types/hooks/shared.ts: 91 issues
- src/types/components/discovery.ts: 64 issues
- src/types/api/discovery.ts: 51 issues
- src/types/api/shared.ts: 48 issues
- src/types/hooks/discovery.ts: 46 issues
- src/types/components/admin.ts: 44 issues
- src/types/modules/flow-orchestration.ts: 40 issues
- src/hooks/__tests__/useSixRAnalysis.test.ts: 36 issues
- src/components/discovery/attribute-mapping/FieldMappingsTab/components/ThreeColumnFieldMapper.tsx: 32 issues
- src/types/guards.ts: 32 issues
- src/utils/api/apiTypes.ts: 30 issues
- src/hooks/useUnifiedDiscoveryFlow.ts: 26 issues
- src/hooks/useAssessmentFlowMigrated.ts: 21 issues
- src/types/flow.ts: 21 issues
- src/types/modules/discovery.ts: 20 issues

## Most Common Issue Types (Top 15)
- typescript-eslint/no-explicit-any: 2037 occurrences
- react-hooks/exhaustive-deps: 48 occurrences
- typescript-eslint/no-namespace: 32 occurrences
- react-refresh/only-export-components: 24 occurrences
- typescript-eslint/no-require-imports: 9 occurrences
- prefer-const: 7 occurrences
- no-useless-catch: 7 occurrences
- react-hooks/rules-of-hooks: 6 occurrences
- no-case-declarations: 6 occurrences
- no-useless-escape: 5 occurrences
- expected: 4 occurrences
- unknown: 4 occurrences
- typescript-eslint/no-empty-object-type: 2 occurrences
- no-constant-condition: 1 occurrences
- no-constant-binary-expression: 1 occurrences

## Detailed Analysis

### TypeScript Issues
- **`@typescript-eslint/no-explicit-any`**: 0 occurrences
  - Impact: Poor type safety, potential runtime errors
  - Fix: Replace `any` with proper type definitions

### React Issues
- **React Hooks violations**: 6 occurrences
  - Impact: Breaks React's rules of hooks, can cause crashes
  - Fix: Move hooks to component root level, fix conditional hooks

- **Missing Dependencies**: 48 occurrences
  - Impact: Stale closures, incorrect behavior
  - Fix: Add missing dependencies or use callback patterns

### Parsing/Syntax Errors
- **Parsing Errors**: 5 occurrences
  - Impact: Prevents compilation
  - Fix: Fix syntax errors, missing punctuation

### Security/Import Issues
- **require() imports**: 0 occurrences
  - Impact: Inconsistent module system usage
  - Fix: Convert to ES6 imports

## Recommendations

### Immediate Action Required (Critical/High Priority)
1. **Fix all parsing errors** - These prevent compilation
2. **Resolve React Hook violations** - These cause runtime crashes
3. **Address case declaration issues** - These are syntax errors

### Short-term Goals (Medium Priority)
1. **Implement proper TypeScript types** - Replace `any` with specific types
2. **Fix React Hook dependencies** - Add missing dependencies
3. **Modernize imports** - Convert require() to ES6 imports

### Long-term Improvements (Low Priority)
1. **Code style consistency** - Fix prefer-const and similar issues
2. **Component organization** - Address react-refresh violations
3. **Error handling** - Remove unnecessary try/catch wrappers

## Files Requiring Immediate Attention
- backend/app/docs/api/examples/data_import_examples.ts: 11 critical, 0 high priority
- playwright.config.ts: 1 critical, 0 high priority
- scripts/debug-checkbox.tsx: 1 critical, 0 high priority
- src/components/FeedbackWidget.tsx: 1 critical, 0 high priority
- src/components/FlowCrewAgentMonitor/hooks/useAgentMonitor.ts: 1 critical, 0 high priority
- src/components/FlowCrewAgentMonitor/types.ts: 1 critical, 0 high priority
- src/components/FlowCrewAgentMonitor/utils/agentDataProcessor.ts: 5 critical, 0 high priority
- src/components/Phase2CrewMonitor.tsx: 0 critical, 1 high priority
- src/components/admin/SessionComparison.tsx: 1 critical, 0 high priority
- src/components/admin/client-details/types.ts: 7 critical, 0 high priority
- src/components/admin/client-management/ClientManagementMain.tsx: 1 critical, 0 high priority
- src/components/admin/client-management/components/ClientForm/AdvancedSettingsTab.tsx: 1 critical, 0 high priority
- src/components/admin/client-management/components/ClientForm/BasicInfoTab.tsx: 1 critical, 0 high priority
- src/components/admin/client-management/components/ClientForm/BusinessContextTab.tsx: 1 critical, 0 high priority
- src/components/admin/client-management/components/ClientForm/TechnicalPreferencesTab.tsx: 1 critical, 0 high priority
- src/components/admin/client-management/components/ClientForm/index.tsx: 1 critical, 0 high priority
- src/components/admin/client-management/hooks/useClientOperations.ts: 5 critical, 0 high priority
- src/components/admin/client-management/types.ts: 14 critical, 0 high priority
- src/components/admin/engagement-creation/CreateEngagementMain.tsx: 7 critical, 0 high priority
- src/components/admin/engagement-creation/EngagementBasicInfo.tsx: 1 critical, 0 high priority
- src/components/admin/engagement-creation/EngagementScope.tsx: 1 critical, 0 high priority
- src/components/admin/engagement-creation/EngagementTimeline.tsx: 1 critical, 0 high priority
- src/components/admin/engagement-management/EngagementForm.tsx: 1 critical, 0 high priority
- src/components/admin/engagement-management/EngagementManagementMain.tsx: 3 critical, 1 high priority
- src/components/admin/engagement-management/types.ts: 6 critical, 0 high priority
- src/components/admin/platform-admin/PlatformAdminDashboard.tsx: 0 critical, 1 high priority
- src/components/admin/session-comparison/SessionComparisonMain.tsx: 1 critical, 1 high priority
- src/components/admin/user-approvals/UserAccessManagement.tsx: 2 critical, 1 high priority
- src/components/admin/user-approvals/UserApprovalsMain.tsx: 0 critical, 2 high priority
- src/components/admin/user-approvals/UserSearchAndEdit.tsx: 3 critical, 2 high priority
- src/components/admin/user-approvals/types.ts: 1 critical, 0 high priority
- src/components/assessment/ApplicationOverrides.tsx: 5 critical, 0 high priority
- src/components/assessment/ExportAndSharingControls.tsx: 1 critical, 0 high priority
- src/components/assessment/TechDebtAnalysisGrid.tsx: 3 critical, 0 high priority
- src/components/assessment/UserModificationForm.tsx: 2 critical, 0 high priority
- src/components/common/PollingControls.tsx: 6 critical, 1 high priority
- src/components/discovery/AgentClarificationPanel.tsx: 4 critical, 3 high priority
- src/components/discovery/AgentInsightsSection.tsx: 4 critical, 3 high priority
- src/components/discovery/AgentLearningInsights.tsx: 0 critical, 1 high priority
- src/components/discovery/AgentPlanningDashboard.tsx: 5 critical, 1 high priority
- src/components/discovery/DataClassificationDisplay.tsx: 3 critical, 1 high priority
- src/components/discovery/EnhancedAgentOrchestrationPanel.tsx: 2 critical, 0 high priority
- src/components/discovery/EnhancedFlowManagementDashboard.tsx: 3 critical, 0 high priority
- src/components/discovery/FileList.tsx: 3 critical, 0 high priority
- src/components/discovery/FlowDeletionConfirmDialog.tsx: 1 critical, 0 high priority
- src/components/discovery/FlowStatusWidget.tsx: 0 critical, 1 high priority
- src/components/discovery/IncompleteFlowManager.tsx: 1 critical, 0 high priority
- src/components/discovery/RawDataTable.tsx: 4 critical, 0 high priority
- src/components/discovery/SecurityScreeningPanel.tsx: 1 critical, 1 high priority
- src/components/discovery/application-discovery/ApplicationDiscoveryPanel.tsx: 1 critical, 0 high priority
- src/components/discovery/application-discovery/hooks/useApplicationDiscovery.ts: 4 critical, 0 high priority
- src/components/discovery/attribute-mapping/AttributeMappingTabContent.tsx: 5 critical, 0 high priority
- src/components/discovery/attribute-mapping/CriticalAttributesTab.tsx: 1 critical, 0 high priority
- src/components/discovery/attribute-mapping/FieldMappingErrorBoundary.tsx: 2 critical, 0 high priority
- src/components/discovery/attribute-mapping/FieldMappingsTab/components/EnhancedFieldDropdown.tsx: 1 critical, 0 high priority
- src/components/discovery/attribute-mapping/FieldMappingsTab/components/FieldMappingCard.tsx: 1 critical, 0 high priority
- src/components/discovery/attribute-mapping/FieldMappingsTab/components/ThreeColumnFieldMapper.tsx: 32 critical, 0 high priority
- src/components/discovery/attribute-mapping/ImportedDataTab.tsx: 5 critical, 0 high priority
- src/components/discovery/attribute-mapping/ProgressDashboard.tsx: 2 critical, 0 high priority
- src/components/discovery/attribute-mapping/TrainingProgressTab.tsx: 1 critical, 1 high priority
- src/components/discovery/attribute-mapping/field-mappings/FieldMappingsTab.tsx: 4 critical, 0 high priority
- src/components/discovery/dependencies/AgentUIMonitor.tsx: 2 critical, 0 high priority
- src/components/discovery/dependencies/DependencyGraph.tsx: 1 critical, 0 high priority
- src/components/discovery/dependencies/DependencyMappingPanel.tsx: 1 critical, 0 high priority
- src/components/discovery/dependencies/DependencyModal.tsx: 3 critical, 0 high priority
- src/components/discovery/dependencies/DependencyStats.tsx: 3 critical, 0 high priority
- src/components/discovery/dependencies/DependencyTable.tsx: 2 critical, 0 high priority
- src/components/discovery/inventory/EnhancedInventoryInsights.tsx: 3 critical, 0 high priority
- src/components/discovery/inventory/InventoryContent.tsx: 1 critical, 0 high priority
- src/components/discovery/inventory/components/AssetTable/index.tsx: 1 critical, 0 high priority
- src/components/discovery/inventory/types/inventory.types.ts: 2 critical, 0 high priority
- src/components/flows/MasterFlowDashboard.tsx: 1 critical, 0 high priority
- src/components/layout/sidebar/NavigationMenu.tsx: 2 critical, 0 high priority
- src/components/layout/sidebar/types.ts: 2 critical, 0 high priority
- src/components/lazy/LazyLoadingProvider.tsx: 4 critical, 0 high priority
- src/components/lazy/PerformanceDashboard.tsx: 1 critical, 0 high priority
- src/components/lazy/components/LazyComponents.tsx: 6 critical, 0 high priority
- src/components/lazy/routes/LazyRoutes.tsx: 3 critical, 0 high priority
- src/components/sixr/BulkAnalysis/components/JobCreationDialog.tsx: 1 critical, 0 high priority
- src/components/sixr/BulkAnalysis/components/JobResults.tsx: 1 critical, 0 high priority
- src/components/sixr/ErrorBoundary.tsx: 1 critical, 0 high priority
- src/components/sixr/QualifyingQuestions.tsx: 3 critical, 0 high priority
- src/config/api.ts: 8 critical, 0 high priority
- src/constants/flowStates.ts: 4 critical, 0 high priority
- src/contexts/AuthContext/hooks/useAuthInitialization.ts: 2 critical, 1 high priority
- src/contexts/AuthContext/hooks/useDebugLogging.ts: 0 critical, 1 high priority
- src/contexts/AuthContext/services/authService.ts: 8 critical, 0 high priority
- src/contexts/AuthContext/storage.ts: 3 critical, 0 high priority
- src/contexts/AuthContext/types.ts: 2 critical, 0 high priority
- src/contexts/ClientContext.tsx: 1 critical, 1 high priority
- src/contexts/DialogContext.tsx: 2 critical, 2 high priority
- src/contexts/EngagementContext.tsx: 1 critical, 0 high priority
- src/hooks/__tests__/useSixRAnalysis.test.ts: 36 critical, 0 high priority
- src/hooks/api/useDashboardData.ts: 4 critical, 0 high priority
- src/hooks/api/useLatestImport.ts: 1 critical, 0 high priority
- src/hooks/discovery/attribute-mapping/types.ts: 14 critical, 0 high priority
- src/hooks/discovery/attribute-mapping/useAttributeMappingActions.ts: 17 critical, 1 high priority
- src/hooks/discovery/attribute-mapping/useAttributeMappingComposition.ts: 0 critical, 1 high priority
- src/hooks/discovery/attribute-mapping/useAttributeMappingLogic.test.ts: 3 critical, 0 high priority
- src/hooks/discovery/attribute-mapping/useAttributeMappingState.ts: 19 critical, 0 high priority
- src/hooks/discovery/attribute-mapping/useCriticalAttributes.ts: 13 critical, 0 high priority
- src/hooks/discovery/attribute-mapping/useFieldMappings.ts: 14 critical, 0 high priority
- src/hooks/discovery/attribute-mapping/useFlowDetection.ts: 2 critical, 1 high priority
- src/hooks/discovery/attribute-mapping/useImportData.ts: 4 critical, 0 high priority
- src/hooks/discovery/useAttributeMappingNavigation.ts: 2 critical, 1 high priority
- src/hooks/discovery/useDataCleansingNavigation.ts: 2 critical, 0 high priority
- src/hooks/discovery/useDataCleansingQueries.ts: 3 critical, 0 high priority
- src/hooks/discovery/useDependencyNavigation.ts: 1 critical, 1 high priority
- src/hooks/discovery/useDiscoveryFlowAutoDetection.ts: 6 critical, 0 high priority
- src/hooks/discovery/useDiscoveryFlowList.ts: 1 critical, 0 high priority
- src/hooks/discovery/useEnhancedFlowManagement.ts: 9 critical, 0 high priority
- src/hooks/discovery/useFlowOperations.ts: 5 critical, 0 high priority
- src/hooks/discovery/useInventoryLogic.ts: 2 critical, 0 high priority
- src/hooks/discovery/useInventoryNavigation.ts: 1 critical, 0 high priority
- src/hooks/execute/useExecuteQueries.ts: 6 critical, 0 high priority
- src/hooks/lazy/LazyHooks.ts: 2 critical, 1 high priority
- src/hooks/lazy/useLazyComponent.ts: 5 critical, 1 high priority
- src/hooks/lazy/useLazyHook.ts: 4 critical, 0 high priority
- src/hooks/useAgentQuestions.ts: 8 critical, 0 high priority
- src/hooks/useAnalysisQueue.ts: 1 critical, 0 high priority
- src/hooks/useApplication.ts: 1 critical, 0 high priority
- src/hooks/useApplications.ts: 1 critical, 0 high priority
- src/hooks/useAssessmentFlow.ts: 15 critical, 3 high priority
- src/hooks/useAssessmentFlowMigrated.ts: 16 critical, 0 high priority
- src/hooks/useAssetInventory.ts: 3 critical, 0 high priority
- src/hooks/useBulkUpdateAssets.ts: 1 critical, 0 high priority
- src/hooks/useCMDBAnalysis.ts: 3 critical, 0 high priority
- src/hooks/useClients.ts: 1 critical, 0 high priority
- src/hooks/useDemoData.ts: 5 critical, 0 high priority
- src/hooks/useEngagements.ts: 1 critical, 0 high priority
- src/hooks/useFlow.ts: 4 critical, 3 high priority
- src/hooks/useFlowUpdates.ts: 0 critical, 1 high priority
- src/hooks/useOptimisticFlow.ts: 2 critical, 0 high priority
- src/hooks/useResource.ts: 1 critical, 0 high priority
- src/hooks/useSixRAnalysis.ts: 5 critical, 1 high priority
- src/hooks/useSixRWebSocket.ts: 5 critical, 2 high priority
- src/hooks/useTarget.ts: 1 critical, 0 high priority
- src/hooks/useTimeline.ts: 1 critical, 0 high priority
- src/hooks/useUnifiedDiscoveryFlow.ts: 25 critical, 0 high priority
- src/hooks/useUnifiedDiscoveryFlowMigrated.ts: 6 critical, 0 high priority
- src/hooks/useUserType.ts: 0 critical, 1 high priority
- src/hooks/useWavePlanning.ts: 1 critical, 0 high priority
- src/lib/api/auth.ts: 3 critical, 0 high priority
- src/lib/api/context.ts: 1 critical, 0 high priority
- src/lib/api/sixr.ts: 6 critical, 0 high priority
- src/lib/polling-manager.ts: 2 critical, 0 high priority
- src/pages/DebugContext.tsx: 3 critical, 0 high priority
- src/pages/FeedbackView.tsx: 5 critical, 2 high priority
- src/pages/Login.tsx: 1 critical, 0 high priority
- src/pages/admin/AdminDashboard.tsx: 3 critical, 0 high priority
- src/pages/admin/ClientDetails.tsx: 7 critical, 0 high priority
- src/pages/admin/CreateClient.tsx: 2 critical, 0 high priority
- src/pages/admin/CreateUser.tsx: 2 critical, 1 high priority
- src/pages/admin/UserProfile.tsx: 1 critical, 0 high priority
- src/pages/assess/Editor.tsx: 1 critical, 0 high priority
- src/pages/assess/Index.tsx: 3 critical, 0 high priority
- src/pages/assess/Treatment.tsx: 1 critical, 0 high priority
- src/pages/assessment/InitializeFlowWithInventory.tsx: 3 critical, 0 high priority
- src/pages/discovery/AssessmentReadiness/components/ReadinessTabs.tsx: 5 critical, 0 high priority
- src/pages/discovery/AttributeMapping/components/AgentReasoningDisplay.tsx: 1 critical, 0 high priority
- src/pages/discovery/AttributeMapping/components/AttributeMappingContent.tsx: 3 critical, 0 high priority
- src/pages/discovery/AttributeMapping/components/AttributeMappingHeader.tsx: 1 critical, 0 high priority
- src/pages/discovery/AttributeMapping/components/ErrorAndStatusAlerts.tsx: 1 critical, 0 high priority
- src/pages/discovery/AttributeMapping/index.tsx: 0 critical, 3 high priority
- src/pages/discovery/AttributeMapping/services/mappingService.ts: 2 critical, 0 high priority
- src/pages/discovery/AttributeMapping/types.ts: 15 critical, 0 high priority
- src/pages/discovery/CMDBImport/CMDBImport.types.ts: 3 critical, 0 high priority
- src/pages/discovery/CMDBImport/components/CMDBDataTable.tsx: 1 critical, 0 high priority
- src/pages/discovery/CMDBImport/components/CMDBValidationPanel.tsx: 1 critical, 0 high priority
- src/pages/discovery/CMDBImport/hooks/useCMDBImport.ts: 1 critical, 0 high priority
- src/pages/discovery/CMDBImport/hooks/useFileUpload.ts: 4 critical, 0 high priority
- src/pages/discovery/CMDBImport/hooks/useFlowManagement.ts: 1 critical, 0 high priority
- src/pages/discovery/DataCleansing.tsx: 3 critical, 0 high priority
- src/pages/discovery/DependencyAnalysis.tsx: 2 critical, 0 high priority
- src/pages/discovery/EnhancedDiscoveryDashboard/services/dashboardService.ts: 9 critical, 0 high priority
- src/pages/discovery/EnhancedDiscoveryDashboard/types.ts: 2 critical, 0 high priority
- src/pages/discovery/TechDebtAnalysis.tsx: 1 critical, 0 high priority
- src/pages/discovery/components/CMDBImport/AgentFeedbackPanel.tsx: 3 critical, 0 high priority
- src/pages/discovery/components/CMDBImport/AgentOrchestrationPanel.tsx: 5 critical, 0 high priority
- src/pages/discovery/components/CMDBImport/FileAnalysis.tsx: 1 critical, 0 high priority
- src/pages/discovery/components/EnhancedAgentOrchestrationPanel/constants.ts: 1 critical, 0 high priority
- src/pages/discovery/components/EnhancedAgentOrchestrationPanel/hooks/useEnhancedMonitoring.ts: 4 critical, 0 high priority
- src/pages/discovery/components/EnhancedAgentOrchestrationPanel/types.ts: 3 critical, 0 high priority
- src/pages/discovery/components/asset-inventory/AssetDistribution.tsx: 4 critical, 0 high priority
- src/pages/discovery/components/asset-inventory/MigrationReadiness.tsx: 2 critical, 0 high priority
- src/pages/discovery/hooks/useCMDBImport.ts: 17 critical, 0 high priority
- src/services/ApiClient.ts: 5 critical, 0 high priority
- src/services/FlowService.ts: 6 critical, 0 high priority
- src/services/api.ts: 3 critical, 0 high priority
- src/services/api/discoveryFlowService.ts: 16 critical, 0 high priority
- src/services/api/masterFlowService.extensions.ts: 10 critical, 0 high priority
- src/services/api/masterFlowService.ts: 16 critical, 0 high priority
- src/services/appInitializer.ts: 1 critical, 0 high priority
- src/services/assessmentReadinessService.ts: 3 critical, 0 high priority
- src/services/dataCleansingService.ts: 2 critical, 0 high priority
- src/services/dataImportValidationService.ts: 2 critical, 0 high priority
- src/services/demoContextService.ts: 3 critical, 0 high priority
- src/services/flowDeletionService.ts: 2 critical, 0 high priority
- src/services/flowProcessingService.ts: 4 critical, 0 high priority
- src/types/api/admin.ts: 3 critical, 0 high priority
- src/types/api/assessment.ts: 7 critical, 0 high priority
- src/types/api/auth.ts: 3 critical, 0 high priority
- src/types/api/decommission.ts: 2 critical, 0 high priority
- src/types/api/discovery.ts: 51 critical, 0 high priority
- src/types/api/execution.ts: 4 critical, 0 high priority
- src/types/api/finops.ts: 3 critical, 0 high priority
- src/types/api/modernize.ts: 4 critical, 0 high priority
- src/types/api/observability.ts: 2 critical, 0 high priority
- src/types/api/planning.ts: 4 critical, 0 high priority
- src/types/api/shared.ts: 48 critical, 0 high priority
- src/types/assessment.ts: 3 critical, 0 high priority
- src/types/components/admin.ts: 44 critical, 0 high priority
- src/types/components/data-display.ts: 186 critical, 0 high priority
- src/types/components/discovery.ts: 64 critical, 0 high priority
- src/types/components/feedback.ts: 6 critical, 0 high priority
- src/types/components/forms.ts: 117 critical, 0 high priority
- src/types/components/layout.ts: 6 critical, 0 high priority
- src/types/components/navigation.ts: 8 critical, 0 high priority
- src/types/components/shared.ts: 16 critical, 0 high priority
- src/types/dependency.ts: 3 critical, 0 high priority
- src/types/discovery.ts: 127 critical, 0 high priority
- src/types/flow.ts: 21 critical, 0 high priority
- src/types/global.ts: 4 critical, 0 high priority
- src/types/guards.ts: 32 critical, 0 high priority
- src/types/hooks/admin.ts: 11 critical, 0 high priority
- src/types/hooks/api.ts: 100 critical, 0 high priority
- src/types/hooks/discovery.ts: 46 critical, 0 high priority
- src/types/hooks/flow-orchestration.ts: 7 critical, 0 high priority
- src/types/hooks/shared.ts: 90 critical, 0 high priority
- src/types/hooks/state-management.ts: 1 critical, 0 high priority
- src/types/index.ts: 1 critical, 0 high priority
- src/types/lazy.ts: 5 critical, 0 high priority
- src/types/modules/discovery.ts: 14 critical, 0 high priority
- src/types/modules/flow-orchestration.ts: 37 critical, 0 high priority
- src/types/modules/shared-utilities.ts: 110 critical, 0 high priority
- src/types/rbac.ts: 2 critical, 0 high priority
- src/utils/api/apiTypes.ts: 30 critical, 0 high priority
- src/utils/api/cacheStrategies.ts: 3 critical, 0 high priority
- src/utils/api/errorHandling.ts: 3 critical, 0 high priority
- src/utils/api/httpClient.ts: 15 critical, 0 high priority
- src/utils/api/retryPolicies.ts: 1 critical, 0 high priority
- src/utils/dataCleansingUtils.ts: 5 critical, 0 high priority
- src/utils/lazy/LazyUtilities.ts: 3 critical, 0 high priority
- src/utils/lazy/loadingManager.ts: 1 critical, 0 high priority
- src/utils/lazy/performanceMonitor.ts: 9 critical, 0 high priority
- src/utils/lazy/routePreloader.ts: 1 critical, 0 high priority
- src/utils/lazy/viteConfig.ts: 1 critical, 0 high priority
- src/utils/logger.ts: 4 critical, 0 high priority
- src/utils/uuidValidation.ts: 6 critical, 0 high priority
- tests/e2e/admin-interface.spec.ts: 1 critical, 0 high priority
- tests/frontend/AssetInventory.test.js: 1 critical, 0 high priority
- tests/frontend/discovery/test_unified_discovery_flow_hook.test.ts: 1 critical, 0 high priority
- tests/frontend/hooks/test_use_lazy_component.test.ts: 1 critical, 0 high priority
- tests/frontend/integration/test_discovery_flow_ui.test.tsx: 1 critical, 0 high priority
- tests/utils/modular-test-utilities.ts: 12 critical, 0 high priority
