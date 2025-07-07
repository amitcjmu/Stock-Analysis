# Team Gamma - Component Updates Briefing

## Mission Statement
Team Gamma is responsible for updating all React components to use the new consolidated hooks and services, ensuring consistent UI/UX patterns, and modernizing component architecture for better maintainability and performance.

## Team Objectives
1. Update all components to use new consolidated hooks from Team Beta
2. Remove direct API calls from components
3. Implement consistent error boundaries and loading states
4. Ensure accessibility (a11y) compliance
5. Modernize component patterns (composition over inheritance)

## Specific Tasks

### Task 1: Component Audit and Mapping
**Files to audit:**
```
/src/pages/discovery/
├── CMDBImport.tsx
├── AttributeMapping.tsx
├── DataCleansing.tsx
├── FlowDashboard.tsx
└── index.tsx

/src/components/discovery/
├── FlowProgress.tsx
├── DataImportForm.tsx
├── AttributeMappingTable.tsx
├── ValidationResults.tsx
└── FlowTimeline.tsx

/src/components/common/
├── LoadingSpinner.tsx
├── ErrorBoundary.tsx
├── DataTable.tsx
└── StatusBadge.tsx
```

**Create component map:**
```typescript
// /src/components/COMPONENT_MAP.md
| Component | Current Hook Usage | New Hook | API Calls | Priority |
|-----------|-------------------|----------|-----------|----------|
| CMDBImport | useUnifiedDiscoveryFlow | useDiscoveryFlow | Direct fetch | High |
| AttributeMapping | useDiscoveryFlow | useDiscoveryFlow | Mixed v1/v3 | High |
```

### Task 2: Update Discovery Flow Components
**Example migration - CMDBImport.tsx:**

```typescript
// Before
import { useState, useEffect } from 'react';
import { useUnifiedDiscoveryFlow } from '@/hooks/useUnifiedDiscoveryFlow';

export const CMDBImport = () => {
  const { session, loading } = useUnifiedDiscoveryFlow();
  const [data, setData] = useState(null);
  
  const handleImport = async (file) => {
    // Direct API call - BAD
    const response = await fetch('/api/v3/import', {
      method: 'POST',
      body: file
    });
    setData(await response.json());
  };
  
  return (
    <div>
      {loading && <div>Loading...</div>}
      {/* Component JSX */}
    </div>
  );
};

// After
import { useDiscoveryFlow } from '@/hooks/flows/useDiscoveryFlow';
import { LoadingOverlay } from '@/components/common/LoadingOverlay';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { FileUpload } from '@/components/common/FileUpload';

export const CMDBImport = () => {
  const {
    flow,
    loading,
    error,
    startDataImport,
    currentPhase
  } = useDiscoveryFlow();
  
  const handleImport = async (file: File) => {
    try {
      await startDataImport({
        fileName: file.name,
        fileContent: await file.text(),
        importType: 'cmdb'
      });
    } catch (error) {
      // Error handled by hook
    }
  };
  
  if (loading) return <LoadingOverlay message="Initializing import..." />;
  if (error) return <ErrorAlert error={error} onRetry={() => window.location.reload()} />;
  
  return (
    <div className="cmdb-import">
      <div className="cmdb-import__header">
        <h1>CMDB Data Import</h1>
        <p>Current Phase: {currentPhase}</p>
      </div>
      
      <FileUpload
        onUpload={handleImport}
        acceptedFormats={['.csv', '.json', '.xml']}
        maxSize={100 * 1024 * 1024} // 100MB
        disabled={flow?.status === 'processing'}
      />
      
      {flow?.metadata?.importProgress && (
        <ImportProgress progress={flow.metadata.importProgress} />
      )}
    </div>
  );
};
```

### Task 3: Implement Consistent Loading States
**Create reusable loading components:**

```typescript
// /src/components/common/LoadingOverlay.tsx
interface LoadingOverlayProps {
  message?: string;
  progress?: number;
  fullScreen?: boolean;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  message = 'Loading...',
  progress,
  fullScreen = false
}) => {
  const content = (
    <div className="loading-overlay__content">
      <Spinner size="large" />
      <p className="loading-overlay__message">{message}</p>
      {progress !== undefined && (
        <ProgressBar value={progress} max={100} />
      )}
    </div>
  );
  
  if (fullScreen) {
    return createPortal(content, document.body);
  }
  
  return <div className="loading-overlay">{content}</div>;
};
```

### Task 4: Implement Error Boundaries
**Create error boundary components:**

```typescript
// /src/components/common/ErrorBoundary.tsx
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<
  { children: ReactNode; fallback?: ComponentType<{ error: Error }> },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    hasError: false,
    error: null
  };
  
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
    // Send to error tracking service
  }
  
  render() {
    if (this.state.hasError && this.state.error) {
      const Fallback = this.props.fallback || DefaultErrorFallback;
      return <Fallback error={this.state.error} />;
    }
    
    return this.props.children;
  }
}

// Wrap components
<ErrorBoundary fallback={DiscoveryErrorFallback}>
  <DiscoveryFlowDashboard />
</ErrorBoundary>
```

### Task 5: Update Data Tables
**Modernize table components:**

```typescript
// /src/components/common/DataTable.tsx
interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  error?: Error | null;
  onRowClick?: (row: T) => void;
  pagination?: PaginationConfig;
  sorting?: SortingConfig;
  selection?: SelectionConfig;
}

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  loading,
  error,
  ...props
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<SortState>();
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  
  const sortedData = useMemo(() => {
    if (!sortConfig) return data;
    return [...data].sort((a, b) => {
      // Sorting logic
    });
  }, [data, sortConfig]);
  
  if (loading) return <TableSkeleton columns={columns.length} rows={5} />;
  if (error) return <TableError error={error} />;
  if (!data.length) return <EmptyState message="No data available" />;
  
  return (
    <div className="data-table">
      <table className="data-table__table">
        <TableHeader
          columns={columns}
          sortConfig={sortConfig}
          onSort={setSortConfig}
          selection={props.selection}
        />
        <TableBody
          data={sortedData}
          columns={columns}
          selectedRows={selectedRows}
          onRowClick={props.onRowClick}
          onSelectionChange={setSelectedRows}
        />
      </table>
      {props.pagination && (
        <TablePagination
          {...props.pagination}
          totalItems={data.length}
        />
      )}
    </div>
  );
}
```

### Task 6: Implement Component Tests
**Test each updated component:**

```typescript
// /src/components/discovery/__tests__/CMDBImport.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CMDBImport } from '../CMDBImport';
import { useDiscoveryFlow } from '@/hooks/flows/useDiscoveryFlow';

jest.mock('@/hooks/flows/useDiscoveryFlow');

describe('CMDBImport', () => {
  const mockStartDataImport = jest.fn();
  
  beforeEach(() => {
    (useDiscoveryFlow as jest.Mock).mockReturnValue({
      flow: { id: 'test-flow', status: 'active' },
      loading: false,
      error: null,
      startDataImport: mockStartDataImport,
      currentPhase: 'data_import'
    });
  });
  
  it('should render upload interface', () => {
    render(<CMDBImport />);
    expect(screen.getByText('CMDB Data Import')).toBeInTheDocument();
    expect(screen.getByText('Current Phase: data_import')).toBeInTheDocument();
  });
  
  it('should handle file upload', async () => {
    render(<CMDBImport />);
    
    const file = new File(['test content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText('Upload file');
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(mockStartDataImport).toHaveBeenCalledWith({
        fileName: 'test.csv',
        fileContent: 'test content',
        importType: 'cmdb'
      });
    });
  });
  
  it('should show loading state', () => {
    (useDiscoveryFlow as jest.Mock).mockReturnValue({
      loading: true
    });
    
    render(<CMDBImport />);
    expect(screen.getByText('Initializing import...')).toBeInTheDocument();
  });
});
```

### Task 7: Accessibility Updates
**Ensure a11y compliance:**

```typescript
// Accessibility checklist for each component:
// 1. Proper ARIA labels
<button aria-label="Upload CMDB data file" onClick={handleUpload}>
  Upload File
</button>

// 2. Keyboard navigation
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>

// 3. Screen reader announcements
<div role="status" aria-live="polite" aria-atomic="true">
  {status && <span>{status}</span>}
</div>

// 4. Focus management
useEffect(() => {
  if (error) {
    errorRef.current?.focus();
  }
}, [error]);
```

## Success Criteria
1. All components use new consolidated hooks (no old hooks)
2. No direct API calls in components
3. Consistent loading and error states across all components
4. All components wrapped in error boundaries
5. Accessibility audit passed (WCAG 2.1 AA)
6. Component tests coverage > 80%
7. No console errors or warnings
8. Performance metrics improved (FCP, TTI)

## Common Issues and Solutions

### Issue 1: Props Drilling
**Symptom:** Passing props through multiple levels
**Solution:** Use Context or component composition
```typescript
// Use composition
<FlowProvider>
  <FlowDashboard>
    <FlowHeader />
    <FlowContent />
  </FlowDashboard>
</FlowProvider>
```

### Issue 2: Unnecessary Re-renders
**Symptom:** Performance issues, component flashing
**Solution:** Use React.memo and useMemo
```typescript
export const ExpensiveComponent = React.memo(({ data }) => {
  const processedData = useMemo(() => 
    expensiveCalculation(data), [data]
  );
  return <div>{processedData}</div>;
});
```

### Issue 3: State Management Complexity
**Symptom:** Complex state logic in components
**Solution:** Extract to custom hooks or use reducer
```typescript
const [state, dispatch] = useReducer(flowReducer, initialState);
```

## Rollback Procedures
1. **Component-by-component migration:**
   ```bash
   git checkout -b gamma-component-updates
   # Update one component at a time
   # Test thoroughly before moving to next
   ```

2. **Feature flags for gradual rollout:**
   ```typescript
   const useNewImplementation = featureFlags.useNewComponents;
   return useNewImplementation ? <NewComponent /> : <OldComponent />;
   ```

3. **Quick rollback:**
   ```bash
   # Revert specific component
   git checkout main -- src/pages/discovery/CMDBImport.tsx
   ```

## Component Guidelines
1. **File Structure:**
   ```
   ComponentName/
   ├── index.tsx           # Main component
   ├── ComponentName.tsx   # Component logic
   ├── ComponentName.css   # Styles
   ├── ComponentName.test.tsx # Tests
   └── types.ts           # TypeScript types
   ```

2. **Naming Conventions:**
   - PascalCase for components
   - camelCase for props and functions
   - UPPER_CASE for constants

3. **Performance Best Practices:**
   - Lazy load heavy components
   - Use React.memo for pure components
   - Virtualize long lists
   - Optimize images and assets

## Status Report Template
```markdown
# Gamma Team Status Report - [DATE]

## Component Migration Status
| Component | Status | Hook Migration | Tests | A11y |
|-----------|--------|----------------|-------|------|
| CMDBImport | Complete | ✓ | ✓ | ✓ |
| AttributeMapping | In Progress | ✓ | ✗ | ✗ |

## Completed Tasks
- [ ] Task 1: Component Audit and Mapping
- [ ] Task 2: Update Discovery Flow Components
- [ ] Task 3: Implement Consistent Loading States
- [ ] Task 4: Implement Error Boundaries
- [ ] Task 5: Update Data Tables
- [ ] Task 6: Implement Component Tests
- [ ] Task 7: Accessibility Updates

## Performance Metrics
- Bundle size: -X KB reduction
- First Contentful Paint: X ms improvement
- Component re-renders: X% reduction

## Issues Encountered
- Issue description and resolution

## A11y Audit Results
- Passed: X/Y criteria
- Issues found and fixed

## Next Steps
- Components to migrate next
- Performance optimizations planned
```

## Resources
- React Documentation: https://react.dev
- Testing Library: https://testing-library.com
- Accessibility Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Component Library: `/src/components/common/`
- Design System: `/docs/design-system/`

## Contact
- Team Lead: Gamma Team
- Slack Channel: #gamma-component-updates
- Design Support: #design-team
- A11y Support: #accessibility-team