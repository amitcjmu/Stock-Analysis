# Collection Flow Silent Failure Fix Implementation Plan

## Issue Summary
Collection flows are getting stuck silently without proper error reporting or background execution progression. This is causing flows to appear frozen to users with no visibility into what's happening.

## Root Causes Identified

1. **No Background Continuation**: Collection flow executes initialization phase once and stops
2. **Wrong Flow ID Usage**: Using child flow ID instead of master flow ID for MFO operations
3. **Missing next_phase**: Execution results don't include next_phase for state transitions
4. **Frontend Progress Bug**: Using wrong field (progress instead of progress_percentage)

## Implementation Approach

### Phase 1: Core Infrastructure Fixes
- Fix master flow ID usage in collection_crud.py
- Create background initialization helper with idempotency checks
- Create child flow state synchronization helper
- Implement proper error logging to failure journal

### Phase 2: Execution Engine Improvements
- Ensure all phase executions return next_phase
- Use flow registry for next phase determination
- Keep execution layer pure (no DB updates in crew executor)

### Phase 3: Fallback Support
- Create fallback phase runner for non-CrewAI environments
- Sequential phase execution with proper error handling
- Fresh database sessions for background tasks

### Phase 4: Monitoring & Recovery
- Implement stuck flow detection
- Auto-recovery for flows with no progress
- Enhanced failure logging with diagnostic data

### Phase 5: Frontend Fixes
- Fix progress field mapping (use progress_percentage)
- Reduce toast noise (only errors and completion)
- Display current phase and status inline

## Key Technical Decisions

### Correct Imports
- Use `app.core.database.AsyncSessionLocal` for sessions
- Use `app.core.context.RequestContext` for context
- SQLAlchemy async patterns with `select()` statements

### Idempotency
- Check only "initializing" and "running" states (not "initialized")
- Prevent duplicate background starts

### Phase Mapping
- "synthesis" → "finalization" 
- Don't set COMPLETED until next_phase is None
- Keep "finalization" status as AUTOMATED_COLLECTION

### Error Handling
- Use correct failure journal signature
- Include next_phase and agent_decision in logs
- Build context from flow data for monitoring

## Files Modified

1. `/backend/app/api/v1/endpoints/collection_crud.py` - Fix master flow ID usage
2. `/backend/app/api/v1/endpoints/collection_utils.py` - Add helper functions
3. `/backend/app/services/flow_orchestration/execution_engine_core.py` - Always return next_phase
4. `/backend/app/services/flow_orchestration/execution_engine_crew.py` - Include next_phase in results
5. `/backend/app/services/flow_orchestration/collection_phase_runner.py` - New fallback runner
6. `/backend/app/services/monitoring/flow_health_monitor.py` - New stuck flow detection
7. `/src/hooks/collection/useProgressMonitoring.ts` - Fix progress field mapping

## Testing Strategy

### Unit Tests
- Master flow ID usage verification
- next_phase always present in results
- Idempotency checks work correctly

### Integration Tests
- Full flow progression through all phases
- Fallback loop when CrewAI unavailable
- Child state sync after each phase

### End-to-End Tests
- Create collection flow and verify background execution
- UI shows progress_percentage updates
- Stuck flow detection and recovery

## Rollback Plan

- Feature flag: ENABLE_BACKGROUND_COLLECTION (optional)
- Keep one-off execution code commented for quick revert
- Monitor logs for any CrewAI import failures
- All changes are backward compatible

## Success Criteria

- Collection flows no longer get stuck silently
- Real-time progress updates visible in UI
- Automatic detection and recovery of stuck flows
- Complete error visibility through all layers
- Proper cleanup of failed flow resources

## Implementation Timeline

1. Core fixes (Phase 1-2): Critical, implement immediately
2. Fallback support (Phase 3): High priority
3. Monitoring (Phase 4): Medium priority
4. Frontend polish (Phase 5): Low priority

## Risks & Mitigations

- **Risk**: Background tasks with stale sessions
  - **Mitigation**: Use fresh AsyncSessionLocal for each background operation

- **Risk**: Duplicate background starts
  - **Mitigation**: Idempotency check for "initializing"/"running" states

- **Risk**: Phase name mismatches
  - **Mitigation**: Map registry phases to child model phases

## Deployment Notes

- No database migrations required
- All changes are backward compatible
- Can be deployed without downtime
- Monitor logs after deployment for any issues