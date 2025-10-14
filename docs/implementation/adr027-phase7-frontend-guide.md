# ADR-027 Phase 7: Frontend Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing Phase 7 of the Universal FlowTypeConfig Migration (ADR-027) in the frontend. The backend is fully complete (Phases 1-6, 8-10), and this phase focuses on making the frontend use the authoritative backend API for phase information.

## Prerequisites

✅ **Backend Complete**: All backend phases (1-6, 8-10) committed and tested
✅ **API Endpoints Available**: `/api/v1/flow-metadata/*` endpoints functional
✅ **Performance Validated**: API responds < 100ms (actual: ~2.5ms average)

## Architecture Overview

### Before (Current State)
```
Frontend → Hardcoded PHASE_SEQUENCES → Component Logic
```

Problems:
- Frontend/backend can get out of sync
- Phase changes require frontend code changes
- No single source of truth

### After (ADR-027)
```
Frontend → useFlowPhases Hook → API → FlowTypeConfig → Component Logic
```

Benefits:
- Single source of truth (FlowTypeConfig)
- Automatic frontend/backend sync
- Phase changes only require backend updates

## Implementation Steps

### Step 1: Create `useFlowPhases` Hook

**File**: `src/hooks/useFlowPhases.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';

export interface PhaseDetail {
  name: string;
  display_name: string;
  description: string;
  order: number;
  estimated_duration_minutes: number;
  can_pause: boolean;
  can_skip: boolean;
  ui_route: string;
  icon?: string;
  help_text?: string;
}

export interface FlowPhases {
  flow_type: string;
  display_name: string;
  version: string;
  phases: string[];
  phase_details: PhaseDetail[];
  phase_count: number;
  estimated_total_duration_minutes: number;
}

/**
 * Fetch authoritative phase sequence from backend
 *
 * Per ADR-027: Replaces hardcoded PHASE_SEQUENCES
 */
export function useFlowPhases(flowType: string) {
  return useQuery<FlowPhases>({
    queryKey: ['flow-phases', flowType],
    queryFn: async () => {
      const response = await apiCall(`/api/v1/flow-metadata/phases/${flowType}`);
      return response as FlowPhases;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 60 * 60 * 1000,     // 1 hour (renamed from cacheTime)
  });
}

/**
 * Fetch all flow phases
 */
export function useAllFlowPhases() {
  return useQuery<Record<string, FlowPhases>>({
    queryKey: ['flow-phases-all'],
    queryFn: async () => {
      const response = await apiCall('/api/v1/flow-metadata/phases');
      return response as Record<string, FlowPhases>;
    },
    staleTime: 30 * 60 * 1000,
    gcTime: 60 * 60 * 1000,
  });
}

/**
 * Get phase display name from phase detail
 */
export function getPhaseDisplayName(
  phases: FlowPhases | undefined,
  phaseName: string
): string {
  if (!phases) return phaseName;

  const phase = phases.phase_details.find(p => p.name === phaseName);
  return phase?.display_name || phaseName;
}

/**
 * Get phase route from phase detail
 */
export function getPhaseRoute(
  phases: FlowPhases | undefined,
  phaseName: string
): string {
  if (!phases) return '/';

  const phase = phases.phase_details.find(p => p.name === phaseName);
  return phase?.ui_route || '/';
}

/**
 * Check if phase is valid for flow type
 */
export function isValidPhase(
  phases: FlowPhases | undefined,
  phaseName: string
): boolean {
  if (!phases) return false;
  return phases.phases.includes(phaseName);
}
```

### Step 2: Update `flowRoutes.ts`

**File**: `src/config/flowRoutes.ts`

Mark the hardcoded sequences as deprecated:

```typescript
/**
 * @deprecated Use useFlowPhases hook instead
 *
 * This constant is kept for backward compatibility only.
 * New code should fetch phases from API using useFlowPhases.
 *
 * Will be removed in v4.0.0
 *
 * Per ADR-027: FlowTypeConfig is the single source of truth
 */
export const PHASE_SEQUENCES_LEGACY: Record<FlowType, string[]> = {
  discovery: [
    "data_import",
    "data_validation",
    "field_mapping",
    "data_cleansing",
    "asset_inventory",
  ],
  assessment: [
    "readiness_assessment",
    "complexity_analysis",
    "dependency_analysis",
    "tech_debt_assessment",
    "risk_assessment",
    "recommendation_generation",
  ],
  // ... other flow types
};

/**
 * Get phase sequence from API (recommended)
 *
 * Per ADR-027: Use this instead of PHASE_SEQUENCES_LEGACY
 */
export async function getPhaseSequence(flowType: FlowType): Promise<string[]> {
  const response = await fetch(`/api/v1/flow-metadata/phases/${flowType}`);
  const data = await response.json();
  return data.phases;
}
```

### Step 3: Update `discoveryRoutes.ts`

**File**: `src/config/discoveryRoutes.ts`

Replace hardcoded routes with API-driven logic:

```typescript
/**
 * @deprecated Use useFlowPhases hook to get routes
 *
 * Phase routes are now provided by the backend API via FlowTypeConfig.
 * This constant kept for backward compatibility only.
 *
 * Per ADR-027: UI routes come from phase metadata
 */
export const DISCOVERY_PHASE_ROUTES_LEGACY = {
  data_import: '/discovery/cmdb-import',
  data_validation: '/discovery/validation',
  field_mapping: '/discovery/field-mapping',
  data_cleansing: '/discovery/cleansing',
  asset_inventory: '/discovery/assets',
};

/**
 * Get phase route from API (recommended)
 *
 * Per ADR-027: Use FlowTypeConfig phase metadata
 */
export async function getPhaseRoute(
  flowType: string,
  phase: string
): Promise<string> {
  const response = await fetch(`/api/v1/flow-metadata/phases/${flowType}`);
  const data = await response.json();
  const phaseDetail = data.phase_details.find((p: any) => p.name === phase);
  return phaseDetail?.ui_route || `/${flowType}`;
}
```

### Step 4: Update Components

**Example**: Update Discovery flow page to use hook

**File**: `src/pages/discovery/DiscoveryFlow.tsx`

```typescript
import { useFlowPhases, getPhaseRoute } from '@/hooks/useFlowPhases';

export function DiscoveryFlow() {
  // Fetch phases from API
  const { data: phases, isLoading, error } = useFlowPhases('discovery');

  // Loading state
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Error state
  if (error) {
    return <ErrorDisplay error={error} />;
  }

  // Use phase data
  const currentPhaseRoute = getPhaseRoute(phases, currentPhase);
  const isValidCurrentPhase = isValidPhase(phases, currentPhase);

  return (
    <div>
      <h1>{phases?.display_name} (v{phases?.version})</h1>

      {/* Phase progress */}
      <PhaseProgress
        phases={phases?.phases || []}
        currentPhase={currentPhase}
        totalDuration={phases?.estimated_total_duration_minutes}
      />

      {/* Phase navigation */}
      {phases?.phase_details.map(phase => (
        <PhaseCard
          key={phase.name}
          name={phase.name}
          displayName={phase.display_name}
          description={phase.description}
          route={phase.ui_route}
          estimatedMinutes={phase.estimated_duration_minutes}
          icon={phase.icon}
          helpText={phase.help_text}
        />
      ))}
    </div>
  );
}
```

### Step 5: Update Navigation Components

**File**: `src/components/Navigation.tsx`

```typescript
import { useAllFlowPhases } from '@/hooks/useFlowPhases';

export function Navigation() {
  const { data: allPhases } = useAllFlowPhases();

  return (
    <nav>
      {Object.entries(allPhases || {}).map(([flowType, phaseInfo]) => (
        <NavItem
          key={flowType}
          label={phaseInfo.display_name}
          phases={phaseInfo.phases}
          version={phaseInfo.version}
        />
      ))}
    </nav>
  );
}
```

### Step 6: Update Phase Validation

**File**: `src/utils/phaseValidation.ts`

```typescript
import { FlowPhases } from '@/hooks/useFlowPhases';

/**
 * Validate phase transition
 *
 * Per ADR-027: Use FlowTypeConfig phase order
 */
export function canTransitionToPhase(
  phases: FlowPhases | undefined,
  currentPhase: string,
  targetPhase: string
): boolean {
  if (!phases) return false;

  const phaseList = phases.phases;
  const currentIndex = phaseList.indexOf(currentPhase);
  const targetIndex = phaseList.indexOf(targetPhase);

  // Can move forward or stay on same phase
  return targetIndex >= currentIndex;
}

/**
 * Get next phase in sequence
 */
export function getNextPhase(
  phases: FlowPhases | undefined,
  currentPhase: string
): string | null {
  if (!phases) return null;

  const phaseList = phases.phases;
  const currentIndex = phaseList.indexOf(currentPhase);

  if (currentIndex === -1 || currentIndex === phaseList.length - 1) {
    return null;
  }

  return phaseList[currentIndex + 1];
}
```

## Testing Checklist

### Unit Tests

- [ ] useFlowPhases hook returns correct data structure
- [ ] getPhaseDisplayName handles missing phases gracefully
- [ ] getPhaseRoute falls back to default route
- [ ] isValidPhase returns false for invalid phases

### Integration Tests

- [ ] Discovery flow loads phases from API
- [ ] Assessment flow shows 6 phases (not 4)
- [ ] Phase navigation respects new phase order
- [ ] Legacy phase names still work (via aliases)

### E2E Tests

```typescript
describe('FlowTypeConfig Frontend Integration', () => {
  it('should load Discovery phases from API', async () => {
    // Visit discovery flow
    await page.goto('/discovery');

    // Wait for phases to load
    await page.waitForSelector('[data-testid="phase-card"]');

    // Verify 5 phases shown (not 9)
    const phases = await page.$$('[data-testid="phase-card"]');
    expect(phases.length).toBe(5);

    // Verify phase names match backend
    const phaseNames = await page.$$eval(
      '[data-testid="phase-name"]',
      elements => elements.map(el => el.textContent)
    );
    expect(phaseNames).toEqual([
      'Data Import & Validation',
      'Data Validation',
      'Field Mapping & Transformation',
      'Data Cleansing & Normalization',
      'Asset Inventory Creation',
    ]);
  });

  it('should handle legacy phase names via aliases', async () => {
    // Navigate using legacy phase name
    await page.goto('/discovery?phase=data_cleaning');

    // Should redirect to canonical name
    await page.waitForURL(/phase=data_cleansing/);
  });
});
```

## Gradual Migration Strategy

### Phase 7.1: Create Infrastructure (Week 1)
- Create useFlowPhases hook
- Add deprecation warnings to legacy constants
- No breaking changes

### Phase 7.2: Update Core Components (Week 2)
- Update Discovery flow to use hook
- Update Assessment flow to use hook
- Keep legacy constants available

### Phase 7.3: Update Navigation (Week 3)
- Update routing logic to use API
- Update phase validation to use API
- Still support legacy code paths

### Phase 7.4: Clean Up (Week 4)
- Remove deprecated constants
- Remove legacy code paths
- Update all remaining components

## Error Handling

### API Failures

```typescript
export function useFlowPhases(flowType: string) {
  return useQuery<FlowPhases>({
    queryKey: ['flow-phases', flowType],
    queryFn: async () => {
      const response = await apiCall(`/api/v1/flow-metadata/phases/${flowType}`);
      return response as FlowPhases;
    },
    staleTime: 30 * 60 * 1000,
    gcTime: 60 * 60 * 1000,
    // Retry strategy
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Fallback to cached data
    refetchOnWindowFocus: false,
  });
}
```

### Graceful Degradation

```typescript
export function DiscoveryFlow() {
  const { data: phases, isLoading, error } = useFlowPhases('discovery');

  // Fallback to legacy constants if API fails
  const fallbackPhases = useMemo(() => {
    if (error) {
      return PHASE_SEQUENCES_LEGACY.discovery;
    }
    return phases?.phases || [];
  }, [phases, error]);

  return (
    <PhaseProgress
      phases={fallbackPhases}
      currentPhase={currentPhase}
      apiError={error}
    />
  );
}
```

## Performance Considerations

### Caching Strategy

```typescript
// Cache phases for 30 minutes (phases rarely change)
staleTime: 30 * 60 * 1000,

// Keep in cache for 1 hour
gcTime: 60 * 60 * 1000,

// Prefetch on app load
queryClient.prefetchQuery({
  queryKey: ['flow-phases-all'],
  queryFn: fetchAllPhases,
});
```

### Lazy Loading

```typescript
// Load phases only when needed
const DiscoveryFlow = lazy(() => import('./DiscoveryFlow'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <DiscoveryFlow />
    </Suspense>
  );
}
```

## Rollback Plan

If Phase 7 causes issues:

1. **Immediate**: Set feature flag `USE_FLOW_TYPE_CONFIG=false` on backend
2. **Frontend**: Revert to using `PHASE_SEQUENCES_LEGACY` constants
3. **Investigation**: Check API endpoint logs, React Query cache
4. **Resolution**: Fix identified issues and redeploy

## Success Criteria

- [ ] All components use `useFlowPhases` hook
- [ ] Zero hardcoded phase sequences in active code
- [ ] Legacy constants marked as deprecated
- [ ] All tests passing (unit, integration, E2E)
- [ ] No performance regression (< 100ms for phase queries)
- [ ] API cache hit rate > 80%
- [ ] Frontend/backend synchronized
- [ ] Documentation updated

## References

- ADR-027: Universal FlowTypeConfig Pattern
- Backend Implementation: Phases 1-6, 8-10 (complete)
- API Endpoint: `/api/v1/flow-metadata/phases/{flow_type}`
- Test Results: All backend tests passing, API < 100ms

---

**Status**: Ready for implementation
**Estimated Duration**: 2-4 weeks (gradual migration)
**Risk Level**: Low (backend feature flags provide safety net)
