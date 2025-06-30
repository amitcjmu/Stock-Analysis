# ADR-001: Migrate from Session ID to Flow ID as Primary Identifier

## Status
Accepted

## Context
The AI Force Migration Platform currently uses two different identification systems:
- **Session IDs** (format: `disc_session_*`) for user sessions and frontend tracking
- **Flow IDs** (UUID v4) for CrewAI flows and backend processing

This dual identifier system causes several problems:
1. **Synchronization Issues**: Mapping between session IDs and flow IDs requires complex bookkeeping
2. **Developer Confusion**: Engineers must understand which identifier to use in different contexts
3. **Data Inconsistency**: Different parts of the system reference different identifiers for the same logical entity
4. **Debugging Complexity**: Tracing a single discovery flow requires following multiple identifier chains
5. **API Inconsistency**: Different endpoints expect different identifier formats
6. **Frontend Complexity**: React components must manage both identifier types and their mappings

## Decision
We will migrate to use **Flow ID as the single primary identifier** throughout the entire system, eliminating session IDs from new development.

### Specific Changes:
1. **Backend APIs**: All v3 endpoints will use `flow_id` instead of `session_id`
2. **Frontend State**: React hooks and context will track `flow_id` primarily
3. **Database Storage**: Flow ID becomes the primary key for all flow-related operations
4. **CrewAI Integration**: Flow ID aligns with CrewAI's native flow identification
5. **Backwards Compatibility**: Legacy endpoints will maintain session ID support during transition

## Consequences

### Positive
- **Single Source of Truth**: One identifier for one logical discovery flow
- **Simplified Codebase**: Eliminates mapping logic and dual tracking
- **Better CrewAI Alignment**: Native compatibility with CrewAI flow patterns
- **Easier Debugging**: Single identifier to trace through entire system
- **Consistent APIs**: All endpoints use the same identifier format
- **Improved Performance**: No need for identifier mapping queries
- **Cleaner Frontend Logic**: Components manage single identifier type

### Negative
- **Migration Effort**: Existing code must be updated to use flow IDs
- **Breaking Changes**: Some existing integrations may need updates
- **Temporary Complexity**: During transition, both identifiers may coexist
- **Data Migration**: Existing session-based data needs flow ID backfill

### Risks
- **User Impact**: Session-based bookmarks or saved links may break
- **Integration Breakage**: External systems using session IDs need updates
- **Migration Complexity**: Complex data relationships need careful migration

## Implementation

### Phase 1: Foundation (Completed)
1. ✅ **Backend Migration Service**: `session_to_flow_migrator.py`
2. ✅ **V3 API Endpoints**: All new endpoints use `flow_id`
3. ✅ **Database Schema**: Flow ID as primary key in new tables
4. ✅ **Frontend Hook**: `useUnifiedDiscoveryFlow` updated for flow ID

### Phase 2: Gradual Migration (In Progress)
1. **Feature Flags**: `USE_FLOW_ID_PRIMARY=true` for gradual rollout
2. **Backward Compatibility**: Legacy endpoints accept both identifiers
3. **Data Backfill**: Populate flow IDs for existing session-based records
4. **Frontend Updates**: Components gradually migrate to flow ID

### Phase 3: Cleanup (Future)
1. **Remove Session ID Support**: Clean up legacy code paths
2. **Database Cleanup**: Remove session ID columns where no longer needed
3. **Documentation Updates**: Update all references to use flow ID

## Migration Strategy

### Data Migration
```sql
-- Backfill flow IDs for existing sessions
UPDATE discovery_sessions 
SET flow_id = gen_random_uuid() 
WHERE flow_id IS NULL;

-- Create mapping table for transition period
CREATE TABLE session_flow_mapping (
    session_id VARCHAR(255) PRIMARY KEY,
    flow_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Compatibility
```python
# Accept both identifiers during transition
@router.get("/flows/{identifier}/status")
async def get_flow_status(identifier: str):
    # Try as flow ID first (UUID format)
    if is_uuid(identifier):
        return await get_status_by_flow_id(identifier)
    # Fall back to session ID lookup
    return await get_status_by_session_id(identifier)
```

### Frontend Migration
```typescript
// New hook pattern
const { flowId, status, progress } = useUnifiedDiscoveryFlow({
  flowId: flowId, // Primary identifier
  enableRealTimeUpdates: true
});

// Legacy support during transition
const legacySessionId = await migrateSessionToFlow(oldSessionId);
```

## Alternatives Considered

### Alternative 1: Keep Both Identifiers
**Rejected** - Maintains complexity and doesn't solve core synchronization issues.

### Alternative 2: Migrate to Session ID as Primary
**Rejected** - Session IDs are less suitable for distributed system identification and don't align with CrewAI patterns.

### Alternative 3: Create New Unified Identifier
**Rejected** - Would require migrating both existing systems and adds unnecessary complexity.

## Validation

### Success Criteria
- [ ] All v3 APIs use flow ID exclusively
- [ ] Frontend components manage single identifier type
- [ ] Database queries simplified (no identifier mapping)
- [ ] End-to-end flow tracing uses single identifier
- [ ] Performance improvement in identifier-heavy operations
- [ ] Reduced codebase complexity metrics

### Testing Strategy
- **Unit Tests**: All identifier-related functions
- **Integration Tests**: End-to-end flow lifecycle with flow ID
- **Migration Tests**: Data integrity during session→flow migration
- **Performance Tests**: Comparison before/after migration
- **Compatibility Tests**: Legacy session ID support during transition

## Related ADRs
- [ADR-002](002-api-consolidation-strategy.md) - API v3 consolidation strategy
- [ADR-003](003-postgresql-only-state-management.md) - State management architecture

## References
- Session Management Analysis: `docs/session_management_architecture.md`
- Migration Implementation: `docs/planning/phase1-tasks/AGENT_A1_BACKEND_SESSION_MIGRATION.md`
- Frontend Updates: `docs/planning/phase1-tasks/AGENT_A2_FRONTEND_SESSION_MIGRATION.md`