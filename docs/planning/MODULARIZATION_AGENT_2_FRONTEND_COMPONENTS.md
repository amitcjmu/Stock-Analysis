# Agent 2: Frontend Components Modularization Tasks

## 🎯 Your Mission
Modularize large React/TypeScript components that exceed 400 lines, focusing on separation of concerns, extracting custom hooks, and creating reusable sub-components.

## 📋 Assigned Files

### Task 1: Modularize `CMDBImport.tsx` (1,492 lines) - CRITICAL
**File**: `/src/pages/discovery/CMDBImport.tsx`  
**Current Issues**:
- Monolithic component handling upload, validation, display, and state
- Business logic mixed with UI rendering
- Multiple responsibilities in single component
- Hard to test individual features

**Modularization Plan**:
```
CMDBImport/
├── index.tsx                        # ~150 lines - Main container component
├── CMDBImport.types.ts              # ~50 lines - TypeScript interfaces
├── hooks/
│   ├── useCMDBImport.ts            # ~200 lines - Main business logic hook
│   ├── useFileUpload.ts            # ~150 lines - File upload logic
│   ├── useValidation.ts            # ~150 lines - Validation logic
│   └── useDataTransform.ts         # ~100 lines - Data transformation
├── components/
│   ├── CMDBUploadSection.tsx       # ~200 lines - Upload UI
│   ├── CMDBDataTable.tsx           # ~250 lines - Data display table
│   ├── CMDBValidationPanel.tsx     # ~200 lines - Validation results
│   ├── CMDBMappingConfig.tsx       # ~200 lines - Field mapping UI
│   └── CMDBActionBar.tsx           # ~100 lines - Action buttons
└── utils/
    ├── cmdbValidators.ts            # ~100 lines - Validation functions
    └── cmdbTransformers.ts          # ~100 lines - Data transformers
```

**Implementation Steps**:
1. Extract TypeScript interfaces to separate file
2. Create custom hooks for business logic
3. Extract upload functionality to dedicated hook
4. Split UI into logical sub-components
5. Move validation logic to utilities
6. Create container component pattern
7. Update imports and test each component

### Task 2: Modularize `EnhancedDiscoveryDashboard.tsx` (1,132 lines)
**File**: `/src/pages/discovery/EnhancedDiscoveryDashboard.tsx`  
**Current Issues**:
- Dashboard mixing multiple views and concerns
- State management scattered throughout
- API calls mixed with rendering logic
- Difficult to add new dashboard widgets

**Modularization Plan**:
```
EnhancedDiscoveryDashboard/
├── index.tsx                        # ~150 lines - Dashboard container
├── types.ts                         # ~50 lines - Type definitions
├── hooks/
│   ├── useDashboard.ts             # ~150 lines - Main dashboard hook
│   ├── useFlowMetrics.ts           # ~150 lines - Metrics calculations
│   └── useDashboardFilters.ts      # ~100 lines - Filter logic
├── components/
│   ├── DashboardHeader.tsx         # ~100 lines - Header with filters
│   ├── FlowsOverview.tsx           # ~200 lines - Flows summary widget
│   ├── MetricsPanel.tsx            # ~200 lines - Metrics display
│   ├── ActivityTimeline.tsx        # ~150 lines - Recent activity
│   └── QuickActions.tsx            # ~100 lines - Action buttons
├── widgets/
│   ├── BaseWidget.tsx              # ~100 lines - Base widget component
│   ├── FlowStatusWidget.tsx        # ~150 lines - Flow status
│   └── ProgressWidget.tsx          # ~150 lines - Progress tracking
└── services/
    └── dashboardService.ts          # ~150 lines - API calls
```

### Task 3: Modularize `FlowCrewAgentMonitor.tsx` (1,106 lines)
**File**: `/src/components/FlowCrewAgentMonitor.tsx`  
**Current Issues**:
- Complex monitoring UI with real-time updates
- WebSocket logic mixed with UI
- Multiple agent views in single component
- Performance issues with large data sets

**Modularization Plan**:
```
FlowCrewAgentMonitor/
├── index.tsx                        # ~100 lines - Main monitor container
├── types.ts                         # ~50 lines - Type definitions
├── hooks/
│   ├── useAgentMonitor.ts          # ~150 lines - Monitor logic
│   ├── useWebSocketAgent.ts        # ~150 lines - WebSocket handling
│   └── useAgentMetrics.ts          # ~100 lines - Metrics processing
├── components/
│   ├── AgentList.tsx               # ~150 lines - Agent list view
│   ├── AgentDetail.tsx             # ~200 lines - Single agent detail
│   ├── AgentStatus.tsx             # ~100 lines - Status indicators
│   ├── AgentLogs.tsx               # ~150 lines - Log viewer
│   └── AgentMetrics.tsx            # ~150 lines - Metrics charts
└── utils/
    ├── agentDataProcessor.ts        # ~100 lines - Data processing
    └── agentStatusCalculator.ts     # ~100 lines - Status calculations
```

### Task 4: Modularize `AttributeMapping.tsx` (718 lines)
**File**: `/src/pages/discovery/AttributeMapping.tsx`  
**Current Issues**:
- Complex mapping interface with drag-and-drop
- Validation logic embedded in component
- API calls mixed with UI updates
- Hard to reuse mapping logic

**Modularization Plan**:
```
AttributeMapping/
├── index.tsx                        # ~100 lines - Main container
├── types.ts                         # ~50 lines - Type definitions
├── hooks/
│   ├── useAttributeMapping.ts      # ~150 lines - Mapping logic
│   ├── useMappingValidation.ts     # ~100 lines - Validation
│   └── useDragDrop.ts              # ~100 lines - Drag-drop logic
├── components/
│   ├── SourceAttributes.tsx        # ~150 lines - Source column
│   ├── TargetAttributes.tsx        # ~150 lines - Target column
│   ├── MappingLines.tsx            # ~100 lines - Connection lines
│   └── MappingActions.tsx          # ~100 lines - Action buttons
└── services/
    └── mappingService.ts            # ~100 lines - API operations
```

### Task 5: Modularize `DiscoveryFlowWizard.tsx` (557 lines)
**File**: `/src/components/discovery/DiscoveryFlowWizard.tsx`  
**Current Issues**:
- Multi-step wizard with all steps in one file
- Step validation mixed with navigation
- Complex state management for wizard flow

**Modularization Plan**:
```
DiscoveryFlowWizard/
├── index.tsx                        # ~100 lines - Wizard container
├── types.ts                         # ~50 lines - Type definitions
├── hooks/
│   ├── useWizard.ts                # ~100 lines - Wizard state
│   └── useStepValidation.ts        # ~100 lines - Validation
├── steps/
│   ├── SelectDataSource.tsx        # ~100 lines - Step 1
│   ├── ConfigureImport.tsx         # ~100 lines - Step 2
│   ├── MapFields.tsx               # ~100 lines - Step 3
│   └── ReviewSubmit.tsx            # ~100 lines - Step 4
└── components/
    ├── WizardProgress.tsx           # ~50 lines - Progress bar
    └── WizardNavigation.tsx         # ~50 lines - Nav buttons
```

## ✅ Success Criteria

For each component:
1. **No component exceeds 250 lines** (excluding imports/types)
2. **Business logic extracted to hooks**
3. **Reusable sub-components created**
4. **Props properly typed** with interfaces
5. **Tests updated** for new structure

## 🔧 Common Patterns to Apply

### Pattern 1: Container/Presentational Split
```typescript
// Container (index.tsx)
const CMDBImportContainer: React.FC = () => {
  const {
    data,
    loading,
    uploadFile,
    validateData
  } = useCMDBImport();
  
  return (
    <CMDBImportView
      data={data}
      loading={loading}
      onUpload={uploadFile}
      onValidate={validateData}
    />
  );
};

// Presentational (CMDBImportView.tsx)
interface Props {
  data: ImportData;
  loading: boolean;
  onUpload: (file: File) => void;
  onValidate: () => void;
}
```

### Pattern 2: Custom Hook Extraction
```typescript
// hooks/useFileUpload.ts
export const useFileUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const upload = useCallback(async (file: File) => {
    setUploading(true);
    // Upload logic here
  }, []);
  
  return { upload, uploading, progress };
};
```

### Pattern 3: Compound Component Pattern
```typescript
// FlowCrewAgentMonitor/index.tsx
export const AgentMonitor = {
  Container: AgentMonitorContainer,
  List: AgentList,
  Detail: AgentDetail,
  Status: AgentStatus,
};

// Usage
<AgentMonitor.Container>
  <AgentMonitor.List />
  <AgentMonitor.Detail agentId={selectedId} />
</AgentMonitor.Container>
```

## 📝 Progress Tracking

Update after completing each file:
- [ ] `CMDBImport.tsx` - Split into 11 modules
- [ ] `EnhancedDiscoveryDashboard.tsx` - Split into 12 modules
- [ ] `FlowCrewAgentMonitor.tsx` - Split into 10 modules
- [ ] `AttributeMapping.tsx` - Split into 8 modules
- [ ] `DiscoveryFlowWizard.tsx` - Split into 8 modules

## 🚨 Important Notes

1. **Preserve State Management**: Ensure state flows correctly
2. **Maintain Performance**: Use React.memo where appropriate
3. **Keep Accessibility**: Preserve ARIA attributes
4. **Update Tests**: Jest tests must be updated
5. **Storybook**: Update stories if they exist

## 🔍 Verification Commands

```bash
# Type checking
npm run type-check

# Run component tests
npm test -- --testPathPattern="CMDBImport"

# Check bundle size impact
npm run build
npm run analyze

# Verify no runtime errors
npm run dev
# Then manually test each component
```

## 💡 Tips for Success

1. **Start with types** - Extract interfaces first
2. **Extract hooks before components** - Logic first, UI second
3. **Use barrel exports** - index.ts for clean imports
4. **Maintain prop drilling** - Don't over-optimize yet
5. **Document props** - Add JSDoc comments

---

**Estimated Time**: 3-4 days for all files  
**Priority Order**: 1, 2, 3, 4, 5 (as listed)  
**Risk Level**: Medium (UI changes visible to users)