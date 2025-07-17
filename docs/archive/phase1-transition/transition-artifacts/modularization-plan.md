# AI Modernize Migration Platform - Modularization Plan

## Overview

This document tracks the modularization effort to ensure all source code files adhere to the **300-400 line mandate**. The goal is to break down large files into focused, maintainable modules following the **modular handler pattern** established in the platform's architecture.

## Current Status

**Total Files Exceeding Mandate**: 89 files  
**Largest File**: `src/pages/discovery/Inventory.tsx` (1,377 lines)  
**Target**: All files under 400 lines  

## Modularization Strategy

### Core Principles

1. **Modular Handler Pattern**: Main service + specialized handlers (each <200 lines)
2. **Single Responsibility**: Each module has one clear purpose
3. **Graceful Fallbacks**: Conditional imports and error handling
4. **Agent-First Architecture**: Preserve agentic intelligence patterns
5. **Cross-Page Communication**: Maintain agent state coordination

## Frontend Modularization Tasks

### 🔥 Critical Priority (1000+ lines)

#### 1. `src/pages/discovery/Inventory.tsx` (1,377 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/pages/discovery/Inventory/
├── index.tsx (main component, <200 lines)
├── hooks/
│   ├── useInventoryData.ts (data fetching, caching)
│   ├── useInventoryFilters.ts (filtering, pagination)
│   ├── useBulkOperations.ts (bulk edit, delete)
│   └── useAppMappings.ts (app-server mappings)
├── components/
│   ├── InventoryTable.tsx (table display)
│   ├── FilterControls.tsx (filter UI)
│   ├── BulkOperationsDialog.tsx (bulk actions)
│   ├── AssetSummaryCards.tsx (summary statistics)
│   └── ExportControls.tsx (CSV export)
└── utils/
    ├── inventoryUtils.ts (utility functions)
    ├── filterUtils.ts (filter logic)
    └── exportUtils.ts (export logic)
```

#### 2. `src/pages/discovery/CMDBImport.tsx` (1,061 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/pages/discovery/CMDBImport/
├── index.tsx (main component, <200 lines)
├── hooks/
│   ├── useFileUpload.ts (upload logic)
│   ├── useDataPreview.ts (preview functionality)
│   ├── useFieldMapping.ts (field mapping)
│   └── useImportValidation.ts (validation)
├── components/
│   ├── FileUploadZone.tsx (drag-drop upload)
│   ├── DataPreviewTable.tsx (preview display)
│   ├── FieldMappingPanel.tsx (mapping interface)
│   ├── ValidationSummary.tsx (validation results)
│   └── ImportProgress.tsx (progress tracking)
└── utils/
    ├── uploadUtils.ts (upload helpers)
    ├── validationUtils.ts (validation logic)
    └── mappingUtils.ts (mapping helpers)
```

#### 3. `src/pages/discovery/Dependencies.tsx` (1,053 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/pages/discovery/Dependencies/
├── index.tsx (main component, <200 lines)
├── hooks/
│   ├── useDependencyAnalysis.ts (analysis logic)
│   ├── useDependencyGraph.ts (graph data)
│   └── useDependencyFeedback.ts (feedback handling)
├── components/
│   ├── DependencyGraph.tsx (visualization)
│   ├── ApplicationClusters.tsx (cluster display)
│   ├── DependencyTable.tsx (dependency list)
│   ├── ImpactAnalysis.tsx (impact display)
│   └── DependencyEditor.tsx (edit dependencies)
└── utils/
    ├── graphUtils.ts (graph processing)
    ├── clusterUtils.ts (clustering logic)
    └── dependencyUtils.ts (dependency helpers)
```

### 🚨 High Priority (800-1000 lines)

#### 4. `src/components/sixr/BulkAnalysis.tsx` (938 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/components/sixr/BulkAnalysis/
├── index.tsx (main component, <200 lines)
├── hooks/
│   ├── useBulkAnalysis.ts (analysis logic)
│   ├── useBulkProgress.ts (progress tracking)
│   └── useBulkResults.ts (results handling)
├── components/
│   ├── AssetSelection.tsx (asset picker)
│   ├── AnalysisProgress.tsx (progress display)
│   ├── BulkResults.tsx (results table)
│   └── AnalysisControls.tsx (control panel)
└── utils/
    ├── bulkAnalysisUtils.ts (analysis helpers)
    └── progressUtils.ts (progress calculations)
```

#### 5. `src/pages/discovery/AssessmentReadiness.tsx` (906 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/pages/discovery/AssessmentReadiness/
├── index.tsx (main component, <200 lines)
├── hooks/
│   ├── useReadinessAssessment.ts (assessment logic)
│   ├── useStakeholderFeedback.ts (feedback handling)
│   └── useReadinessMetrics.ts (metrics calculation)
├── components/
│   ├── ReadinessMetrics.tsx (metrics display)
│   ├── StakeholderPanel.tsx (stakeholder interface)
│   ├── RequirementsChecklist.tsx (requirements)
│   └── ReadinessActions.tsx (action items)
└── utils/
    ├── readinessUtils.ts (calculation helpers)
    └── metricsUtils.ts (metrics processing)
```

#### 6. `src/components/discovery/application-discovery/ApplicationDiscoveryPanel.tsx` (864 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/components/discovery/application-discovery/
├── ApplicationDiscoveryPanel/
│   ├── index.tsx (main component, <200 lines)
│   ├── hooks/
│   │   ├── useApplicationDiscovery.ts
│   │   ├── useApplicationValidation.ts
│   │   └── useApplicationGrouping.ts
│   ├── components/
│   │   ├── ApplicationList.tsx
│   │   ├── DiscoveryControls.tsx
│   │   ├── ValidationPanel.tsx
│   │   └── GroupingInterface.tsx
│   └── utils/
│       ├── discoveryUtils.ts
│       └── validationUtils.ts
```

### ⚡ Medium Priority (600-800 lines)

#### 7. `src/lib/api/sixr.ts` (857 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/lib/api/sixr/
├── index.ts (main exports, <100 lines)
├── analysis.ts (analysis endpoints)
├── bulk.ts (bulk operations)
├── history.ts (history endpoints)
├── feedback.ts (feedback endpoints)
└── utils/
    ├── apiUtils.ts (common API helpers)
    ├── responseUtils.ts (response processing)
    └── errorUtils.ts (error handling)
```

#### 8. `src/pages/discovery/AttributeMapping.tsx` (843 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/pages/discovery/AttributeMapping/
├── index.tsx (main component, <200 lines)
├── hooks/
│   ├── useAttributeMapping.ts (mapping logic)
│   ├── useFieldSuggestions.ts (AI suggestions)
│   └── useMappingValidation.ts (validation)
├── components/
│   ├── MappingTable.tsx (mapping interface)
│   ├── FieldSuggestions.tsx (AI suggestions)
│   ├── ValidationPanel.tsx (validation display)
│   └── MappingControls.tsx (control panel)
└── utils/
    ├── mappingUtils.ts (mapping helpers)
    └── suggestionUtils.ts (suggestion logic)
```

#### 9. `src/pages/discovery/DiscoveryDashboard.tsx` (826 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/pages/discovery/DiscoveryDashboard/
├── index.tsx (main component, <200 lines)
├── hooks/
│   ├── useDashboardData.ts (data aggregation)
│   ├── useDashboardMetrics.ts (metrics calculation)
│   └── useDashboardRefresh.ts (refresh logic)
├── components/
│   ├── MetricCards.tsx (summary cards)
│   ├── ProgressCharts.tsx (progress visualization)
│   ├── RecentActivity.tsx (activity feed)
│   └── QuickActions.tsx (action buttons)
└── utils/
    ├── dashboardUtils.ts (dashboard helpers)
    └── chartUtils.ts (chart processing)
```

#### 10. `src/pages/assess/Treatment.tsx` (810 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
src/pages/assess/Treatment/
├── index.tsx (main component, <200 lines)
├── hooks/
│   ├── useTreatmentAnalysis.ts (6R analysis)
│   ├── useTreatmentRecommendations.ts (recommendations)
│   └── useTreatmentValidation.ts (validation)
├── components/
│   ├── TreatmentMatrix.tsx (6R matrix)
│   ├── RecommendationPanel.tsx (recommendations)
│   ├── TreatmentControls.tsx (controls)
│   └── ValidationSummary.tsx (validation)
└── utils/
    ├── treatmentUtils.ts (treatment helpers)
    └── recommendationUtils.ts (recommendation logic)
```

### 🔧 Standard Priority (400-600 lines)

#### 11-20. Additional Frontend Files (400-600 lines)
- `src/components/AgentMonitor.tsx` (787 lines)
- `src/components/sixr/AnalysisHistory.tsx` (786 lines)
- `src/components/ui/sidebar.tsx` (761 lines)
- `src/components/discovery/AgentClarificationPanel.tsx` (684 lines)
- `src/hooks/useDataCleansing.ts` (662 lines)
- `src/components/sixr/ErrorBoundary.tsx` (581 lines)
- `src/components/sixr/ApplicationSelector.tsx` (559 lines)
- `src/pages/FeedbackView.tsx` (550 lines)
- `src/components/sixr/QualifyingQuestions.tsx` (503 lines)
- `src/components/sixr/RecommendationDisplay.tsx` (482 lines)

**Strategy**: Similar modular breakdown with hooks, components, and utils folders.

## Backend Modularization Tasks

### 🔥 Critical Priority (1000+ lines)

#### 1. `backend/app/api/v1/endpoints/data_import.py` (1,337 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
backend/app/api/v1/endpoints/data_import/
├── __init__.py
├── main.py (main router, <200 lines)
├── handlers/
│   ├── upload_handler.py (file upload logic)
│   ├── processing_handler.py (data processing)
│   ├── quality_handler.py (quality analysis)
│   ├── mapping_handler.py (field mapping)
│   └── learning_handler.py (learning integration)
├── utils/
│   ├── file_utils.py (file processing)
│   ├── validation_utils.py (validation logic)
│   └── export_utils.py (export helpers)
└── schemas/
    ├── upload_schemas.py (upload models)
    └── processing_schemas.py (processing models)
```

#### 2. `backend/app/api/v1/endpoints/agent_discovery.py` (1,210 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
backend/app/api/v1/endpoints/agent_discovery/
├── __init__.py
├── main.py (main router, <200 lines)
├── handlers/
│   ├── analysis_handler.py (agent analysis)
│   ├── clarification_handler.py (clarifications)
│   ├── learning_handler.py (learning logic)
│   ├── dependency_handler.py (dependency analysis)
│   └── readiness_handler.py (readiness assessment)
├── utils/
│   ├── agent_utils.py (agent helpers)
│   ├── analysis_utils.py (analysis processing)
│   └── learning_utils.py (learning helpers)
└── schemas/
    ├── analysis_schemas.py (analysis models)
    └── learning_schemas.py (learning models)
```

#### 3. `backend/app/services/sixr_engine.py` (1,108 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
backend/app/services/sixr_engine/
├── __init__.py
├── main.py (main service, <200 lines)
├── handlers/
│   ├── analysis_handler.py (6R analysis)
│   ├── strategy_handler.py (strategy logic)
│   ├── recommendation_handler.py (recommendations)
│   └── validation_handler.py (validation)
├── engines/
│   ├── rehost_engine.py (rehost analysis)
│   ├── replatform_engine.py (replatform analysis)
│   ├── refactor_engine.py (refactor analysis)
│   └── retire_engine.py (retire analysis)
└── utils/
    ├── analysis_utils.py (analysis helpers)
    └── strategy_utils.py (strategy helpers)
```

#### 4. `backend/app/api/v1/endpoints/sixr_analysis.py` (1,077 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
backend/app/api/v1/endpoints/sixr_analysis/
├── __init__.py
├── main.py (main router, <200 lines)
├── handlers/
│   ├── individual_handler.py (individual analysis)
│   ├── bulk_handler.py (bulk analysis)
│   ├── history_handler.py (analysis history)
│   └── feedback_handler.py (feedback processing)
├── utils/
│   ├── analysis_utils.py (analysis helpers)
│   └── response_utils.py (response formatting)
└── schemas/
    ├── analysis_schemas.py (analysis models)
    └── response_schemas.py (response models)
```

### 🚨 High Priority (800-1000 lines)

#### 5. `backend/app/api/v1/discovery/asset_management.py` (979 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
backend/app/api/v1/discovery/asset_management/
├── __init__.py
├── main.py (main router, <200 lines)
├── handlers/
│   ├── crud_handler.py (CRUD operations)
│   ├── search_handler.py (search/filter)
│   ├── bulk_handler.py (bulk operations)
│   └── intelligence_handler.py (AI intelligence)
├── utils/
│   ├── asset_utils.py (asset helpers)
│   └── search_utils.py (search logic)
└── schemas/
    ├── asset_schemas.py (asset models)
    └── search_schemas.py (search models)
```

#### 6. `backend/app/services/tech_debt_analysis_agent.py` (954 lines)
**Status**: 📋 Planned  
**Target Modules**:
```
backend/app/services/tech_debt_analysis_agent/
├── __init__.py
├── main.py (main agent, <200 lines)
├── analyzers/
│   ├── code_analyzer.py (code analysis)
│   ├── dependency_analyzer.py (dependency analysis)
│   ├── security_analyzer.py (security analysis)
│   └── performance_analyzer.py (performance analysis)
├── utils/
│   ├── analysis_utils.py (analysis helpers)
│   └── scoring_utils.py (scoring logic)
└── tools/
    ├── code_tools.py (code analysis tools)
    └── metric_tools.py (metric calculation tools)
```

### ⚡ Medium Priority (600-800 lines)

#### 7-15. Additional Backend Files (600-800 lines)
- `backend/app/services/discovery_agents/dependency_intelligence_agent.py` (868 lines)
- `backend/app/services/assessment_readiness_orchestrator.py` (780 lines)
- `backend/app/services/tools/sixr_tools.py` (745 lines)
- `backend/app/services/agent_registry.py` (744 lines)
- `backend/app/services/discovery_agents/presentation_reviewer_agent.py` (733 lines)
- `backend/app/api/v1/discovery/cmdb_analysis.py` (684 lines)
- `backend/app/services/field_mapper.py` (669 lines)
- `backend/app/services/field_mapper_modular.py` (661 lines)
- `backend/app/services/sixr_agents.py` (639 lines)

**Strategy**: Apply modular handler pattern with specialized handlers for each domain.

## Implementation Phases

### Phase 1: Critical Frontend Files (Weeks 1-3)
- [x] ✅ Complete: Enhanced Agent UI Bridge (already modularized)
- [ ] 📋 `src/pages/discovery/Inventory.tsx` → Modular structure
- [ ] 📋 `src/pages/discovery/CMDBImport.tsx` → Modular structure
- [ ] 📋 `src/pages/discovery/Dependencies.tsx` → Modular structure

### Phase 2: Critical Backend Files (Weeks 4-6)
- [x] ✅ Complete: Data Source Intelligence Agent (already modularized)
- [ ] 📋 `backend/app/api/v1/endpoints/data_import.py` → Modular structure
- [ ] 📋 `backend/app/api/v1/endpoints/agent_discovery.py` → Modular structure
- [ ] 📋 `backend/app/services/sixr_engine.py` → Modular structure

### Phase 3: High Priority Files (Weeks 7-9)
- [ ] 📋 Frontend components (BulkAnalysis, AssessmentReadiness, etc.)
- [ ] 📋 Backend services (asset_management, tech_debt_analysis_agent, etc.)

### Phase 4: Medium Priority Files (Weeks 10-12)
- [ ] 📋 Remaining frontend files (400-600 lines)
- [ ] 📋 Remaining backend files (400-600 lines)

### Phase 5: Testing & Validation (Weeks 13-14)
- [ ] 📋 Comprehensive testing of modularized components
- [ ] 📋 Performance validation
- [ ] 📋 Integration testing
- [ ] 📋 Documentation updates

## Modularization Guidelines

### File Structure Standards

#### Frontend Modular Pattern
```
src/[domain]/[component]/
├── index.tsx (main component, <200 lines)
├── hooks/ (custom hooks, each <200 lines)
├── components/ (sub-components, each <200 lines)
├── utils/ (utility functions, each <200 lines)
├── types/ (TypeScript types)
└── __tests__/ (test files)
```

#### Backend Modular Pattern
```
backend/app/[domain]/[service]/
├── __init__.py
├── main.py (main service, <200 lines)
├── handlers/ (specialized handlers, each <200 lines)
├── utils/ (utility functions, each <200 lines)
├── schemas/ (Pydantic models)
├── tools/ (CrewAI tools, each <200 lines)
└── tests/ (test files)
```

### Code Organization Rules

1. **Single Responsibility**: Each file has one clear purpose
2. **Line Limit**: Maximum 200 lines per handler/component
3. **Import Strategy**: Conditional imports with fallbacks
4. **Error Handling**: Graceful degradation patterns
5. **Agent Integration**: Preserve agentic intelligence
6. **Cross-Module Communication**: Clear interfaces between modules

### Breaking Down Large Functions

#### Common Patterns to Extract:
- **Data Fetching Logic** → Custom hooks (frontend) / Service methods (backend)
- **UI State Management** → State hooks / Context providers
- **Business Logic** → Utility functions / Service handlers
- **API Calls** → API service modules
- **Validation Logic** → Validation utilities
- **Error Handling** → Error handling utilities
- **Data Transformation** → Transformation utilities

### Testing Strategy

#### Each Modularized Component Should Include:
- **Unit Tests**: Test individual handlers/components
- **Integration Tests**: Test module interactions
- **E2E Tests**: Test complete workflows
- **Performance Tests**: Validate no performance regression

## Success Metrics

### Quantitative Goals
- [ ] **All files under 400 lines** (Target: 100% compliance)
- [ ] **Handler files under 200 lines** (Target: 100% compliance)
- [ ] **Maintainability Index** > 85 (improved from current baseline)
- [ ] **Cyclomatic Complexity** < 10 per function
- [ ] **Test Coverage** > 90% for all modularized components

### Qualitative Goals
- [ ] **Improved Readability**: Easier to understand component purposes
- [ ] **Enhanced Maintainability**: Easier to modify and extend
- [ ] **Better Testability**: More focused unit testing
- [ ] **Reduced Coupling**: Clear separation of concerns
- [ ] **Preserved Functionality**: All existing features work as before

## Risk Mitigation

### Potential Risks
1. **Breaking Existing Functionality**: Comprehensive testing required
2. **Performance Impact**: Monitor for any performance regression
3. **Complex Interdependencies**: Careful dependency mapping needed
4. **Agent State Management**: Preserve cross-page communication
5. **Import Cycles**: Prevent circular dependencies

### Mitigation Strategies
1. **Feature Flags**: Enable/disable modularized components during transition
2. **Parallel Development**: Keep existing files until new modules are validated
3. **Comprehensive Testing**: Multi-tier testing strategy
4. **Gradual Migration**: Phase-by-phase approach
5. **Rollback Plan**: Quick revert capability for each phase

## Monitoring & Progress Tracking

### Weekly Checkpoints
- [ ] **Files Modularized**: Count and percentage
- [ ] **Line Count Reduction**: Total lines before/after
- [ ] **Test Coverage**: Coverage percentage for new modules
- [ ] **Performance Metrics**: Response time comparisons
- [ ] **Integration Health**: Cross-module communication status

### Completion Criteria
- [ ] All files under 400-line mandate
- [ ] No functionality regression
- [ ] Test coverage maintained/improved
- [ ] Documentation updated
- [ ] Team approval and sign-off

---

## Summary

This modularization plan addresses **89 files** that currently exceed the 300-400 line mandate. The approach follows the established **modular handler pattern** from the CrewAI agent architecture, ensuring consistency with the platform's agentic-first principles.

**Key Benefits**:
- **Improved Maintainability**: Smaller, focused modules are easier to understand and modify
- **Enhanced Testability**: Targeted testing of specific functionality
- **Better Collaboration**: Multiple developers can work on different modules simultaneously
- **Preserved Intelligence**: Maintains the agentic AI capabilities that define the platform
- **Scalable Architecture**: Foundation for future feature development

**Implementation Timeline**: 14 weeks with phased approach to minimize risk and ensure quality.

This plan serves as a living document that will be updated as modularization progresses, with regular checkpoints to ensure we maintain the platform's core value proposition while achieving the architectural excellence required for enterprise-grade software. 