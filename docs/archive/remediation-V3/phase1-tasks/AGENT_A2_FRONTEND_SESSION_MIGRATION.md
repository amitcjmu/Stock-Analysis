# Phase 1 - Agent A2: Frontend Session-to-Flow Migration

## Context
You are part of a parallel remediation effort to fix critical architectural issues in the AI Force Migration Platform. This is Track A (Frontend) of Phase 1, working in coordination with Agent A1 who is handling the backend migration from session_id to flow_id.

### Required Reading Before Starting
- `docs/planning/PHASE-1-REMEDIATION-PLAN.md` - Overall Phase 1 objectives
- `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md` - Platform overview
- `AGENT_A1_BACKEND_SESSION_MIGRATION.md` - Understanding backend changes

### Phase 1 Goal
Complete foundation cleanup to enable proper CrewAI integration. Your work ensures the frontend properly uses flow_id as the primary identifier, maintaining sync with backend changes.

## Your Specific Tasks

### 1. Replace Session ID References in React Hooks
**Files to modify**:
```
src/hooks/discovery/useDiscoveryFlowV2.ts
src/hooks/discovery/useAttributeMappingLogic.ts
src/hooks/discovery/useDiscoveryFlowAutoDetection.ts
src/hooks/useUnifiedDiscoveryFlow.ts
```

Changes needed:
- Replace `sessionId` with `flowId` in all state and props
- Update URL parameters from `session_id` to `flow_id`
- Update localStorage keys from `session_*` to `flow_*`

### 2. Update API Service Calls
**Files to modify**:
```
src/services/discoveryUnifiedService.ts
src/services/dataImportService.ts
src/services/api.ts
src/config/api.ts
```

Update all API calls:
```typescript
// Old
`/api/v1/discovery/session/${sessionId}/status`

// New
`/api/v1/discovery/flow/${flowId}/status`
```

### 3. Update State Management
**Files to modify**:
```
src/store/slices/discoverySlice.ts (if using Redux)
src/contexts/DiscoveryContext.tsx (if using Context)
src/hooks/useDiscoveryState.ts
```

State shape changes:
```typescript
// Old
interface DiscoveryState {
  sessionId: string;
  sessionData: SessionData;
}

// New
interface DiscoveryState {
  flowId: string;
  flowData: FlowData;
  // Temporary: Keep sessionId for backward compatibility
  sessionId?: string; // @deprecated Use flowId
}
```

### 4. Create Migration Utility
**File to create**: `src/utils/migration/sessionToFlow.ts`

```typescript
/**
 * Utilities for migrating from session-based to flow-based storage
 */
export class SessionToFlowMigration {
  /**
   * Migrate localStorage data from session to flow keys
   */
  static migrateLocalStorage(): void {
    // Implementation
  }

  /**
   * Convert session ID to flow ID format if needed
   */
  static convertSessionToFlowId(sessionId: string): string {
    // Implementation
  }

  /**
   * Check if migration is needed
   */
  static isMigrationNeeded(): boolean {
    // Implementation
  }
}
```

## Success Criteria
- [ ] All sessionId references replaced with flowId
- [ ] URL routing uses flow_id parameter
- [ ] localStorage migrated to new key format
- [ ] No breaking changes for active users
- [ ] All TypeScript types updated
- [ ] Frontend tests updated and passing

## Interfaces with Other Agents
- **Agent A1** provides backend endpoints accepting flow_id
- **Agent B2** will create new API client using your flow_id patterns
- Share TypeScript interfaces in `src/types/discovery.ts`

## Implementation Guidelines

### 1. Start with Type Definitions
Create/update `src/types/discovery.ts`:
```typescript
export interface FlowIdentifier {
  flowId: string;
  sessionId?: string; // @deprecated - remove in Phase 2
}
```

### 2. Feature Flag Implementation
Use feature flag for gradual rollout:
```typescript
const USE_FLOW_ID = process.env.REACT_APP_USE_FLOW_ID === 'true';

const identifier = USE_FLOW_ID ? flowId : sessionId;
```

### 3. Migration Strategy
1. Run migration utility on app load
2. Support both identifiers during transition
3. Log deprecation warnings for session_id usage
4. Clean up after Phase 2

### 4. Testing Approach
- Unit tests for migration utility
- Integration tests for API calls
- E2E tests for critical user flows
- Manual testing checklist

## Commands to Run
```bash
# Install dependencies
docker exec -it migration_frontend npm install

# Run type checking
docker exec -it migration_frontend npm run type-check

# Run tests
docker exec -it migration_frontend npm run test

# Run linting
docker exec -it migration_frontend npm run lint

# Build to verify
docker exec -it migration_frontend npm run build
```

## Definition of Done
- [ ] All sessionId references replaced (0 occurrences in codebase)
- [ ] Migration utility created and tested
- [ ] TypeScript types updated with no errors
- [ ] All tests passing (maintain >80% coverage)
- [ ] Backward compatibility verified
- [ ] PR created with title: "feat: [Phase1-A2] Frontend session to flow migration"
- [ ] Code reviewed by Agent A1 for API compatibility
- [ ] User guide updated for any visible changes

## Common Patterns to Update

### API Calls
```typescript
// Old pattern
const response = await apiCall(`/api/v1/discovery/session/${sessionId}/status`);

// New pattern
const response = await apiCall(`/api/v1/discovery/flow/${flowId}/status`);
```

### Route Parameters
```typescript
// Old pattern
<Route path="/discovery/:sessionId" component={DiscoveryFlow} />

// New pattern
<Route path="/discovery/:flowId" component={DiscoveryFlow} />
```

### Hook Usage
```typescript
// Old pattern
const { session, isLoading } = useDiscoverySession(sessionId);

// New pattern
const { flow, isLoading } = useDiscoveryFlow(flowId);
```

## Notes
- Coordinate closely with Agent A1 on API contract
- Some components may need both IDs during transition
- Priority: User-facing components first
- Keep UX seamless during migration