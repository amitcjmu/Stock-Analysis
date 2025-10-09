# ApplicationSelection Module

## Overview
Modularized ApplicationSelection component for selecting assets in Collection flows.

**Original Size**: 977 lines
**Modularized Size**: 402 lines (main component) + 1,027 lines (distributed across modules)
**Benefit**: Improved maintainability, testability, and code organization

## Architecture

### Directory Structure
```
ApplicationSelection/
├── index.tsx                    # Main component (402 lines)
├── types.ts                     # Type definitions (79 lines)
├── hooks/
│   ├── index.ts                # Hooks barrel export
│   ├── useApplicationData.ts   # Data fetching (224 lines)
│   ├── useInfiniteScroll.ts    # Infinite scroll logic (61 lines)
│   ├── useApplicationSelection.ts # Selection state (78 lines)
│   └── useCacheInvalidation.ts # Cache management (44 lines)
└── components/
    ├── index.ts                # Components barrel export
    ├── ApplicationCard.tsx     # Single asset card (96 lines)
    ├── ApplicationGrid.tsx     # Asset grid + infinite scroll (90 lines)
    ├── SelectionControls.tsx   # Asset type filters (168 lines)
    ├── SearchFilters.tsx       # Search/filter UI (102 lines)
    └── LoadingStates.tsx       # Loading/error states (66 lines)
```

## Critical Patterns Preserved

### 1. Multi-Tenant Scoping
All queries include `client_account_id` and `engagement_id`:
```typescript
// In useApplicationData.ts
if (!client?.id || !engagement?.id) {
  throw new Error("Missing required tenant context");
}
params.append("client_account_id", client.id.toString());
params.append("engagement_id", engagement.id.toString());
```

### 2. Infinite Scroll with Intersection Observer
Extracted into `useInfiniteScroll` hook:
```typescript
const { loadMoreRef } = useInfiniteScroll({
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
});
```

### 3. Cache Invalidation
Extracted into `useCacheInvalidation` hook:
```typescript
const { invalidateCollectionFlowCache } = useCacheInvalidation();
await invalidateCollectionFlowCache(flowId);
```

### 4. Server-Side Filtering
Filters applied at API level for proper pagination:
```typescript
// searchTerm, environmentFilter, criticalityFilter sent to API
params.append("search", searchTerm.trim());
params.append("environment", environmentFilter);
```

### 5. Client-Side Asset Type Filtering
Asset types filtered client-side to avoid pagination issues:
```typescript
const filteredAssets = useMemo(() => {
  if (selectedAssetTypes.has("ALL")) return allAssets;
  return allAssets.filter(asset =>
    selectedAssetTypes.has(asset.asset_type?.toUpperCase())
  );
}, [allAssets, selectedAssetTypes]);
```

## Usage

### Importing the Component
```typescript
// Via lazy loading (existing pattern)
import { LazyApplicationSelection } from "@/components/lazy/routes/LazyRoutes";

// Direct import (resolves to index.tsx)
import ApplicationSelection from "@/pages/collection/ApplicationSelection";
```

### Using Individual Hooks
```typescript
import {
  useApplicationData,
  useInfiniteScroll,
  useApplicationSelection,
  useCacheInvalidation
} from "@/pages/collection/ApplicationSelection/hooks";
```

### Using Individual Components
```typescript
import {
  ApplicationCard,
  ApplicationGrid,
  SelectionControls,
  SearchFilters
} from "@/pages/collection/ApplicationSelection/components";
```

## Key Features

### Data Management
- **React Query** for server state
- **Infinite scroll** for large datasets
- **Smart caching** with invalidation
- **Multi-tenant isolation** enforced

### User Experience
- **Asset type filters** (Applications, Servers, Databases, etc.)
- **Search** by name/description
- **Filter** by environment and criticality
- **Select all** with awareness of filters
- **Loading states** for each async operation

### Performance
- **Page size**: 50 items (optimal for smooth scrolling)
- **Stale time**: 5 minutes for asset data
- **Intersection Observer** with 100px root margin
- **Memoized computations** for filtered assets

## Testing Considerations

### Unit Testing Hooks
Each hook can now be tested independently:
```typescript
import { renderHook } from '@testing-library/react';
import { useApplicationData } from './hooks/useApplicationData';

test('useApplicationData handles multi-tenant scoping', () => {
  const { result } = renderHook(() => useApplicationData({...}));
  // Assert tenant scoping
});
```

### Component Testing
Components can be tested with mock data:
```typescript
import { ApplicationCard } from './components/ApplicationCard';

test('ApplicationCard displays asset information', () => {
  const mockAsset = { id: 1, name: 'Test App', ... };
  render(<ApplicationCard asset={mockAsset} ... />);
  // Assert rendering
});
```

## Migration Notes

### Backward Compatibility
- **No breaking changes** - default export preserved
- **Routing unchanged** - lazy loading still works
- **API contracts preserved** - all queries identical
- **State management unchanged** - React Query patterns preserved

### Old File Location
Original file backed up to:
- `ApplicationSelection.tsx.backup` (if needed for reference)

## Future Improvements

1. **Extract asset type constants** to shared constants file
2. **Add TypeScript generics** for better type inference
3. **Create shared filter components** for reuse across pages
4. **Add integration tests** for critical user flows
5. **Implement virtualization** for extremely large datasets (10k+ items)

## Related Documentation
- [CLAUDE.md](/CLAUDE.md) - Project guidelines
- [coding-agent-guide.md](/docs/analysis/Notes/coding-agent-guide.md) - Implementation patterns
- [API Request Patterns](/docs/guidelines/API_REQUEST_PATTERNS.md) - API best practices
