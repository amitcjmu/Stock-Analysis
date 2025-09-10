# Flow State Persistence Debugging Patterns (September 2025)

## Problem Pattern: Multi-Layer Execution Without State Persistence
**Symptom**: Phase executions succeed but database state never updates (completion flags remain false, current_phase doesn't advance)

**Root Cause Pattern**: Complex execution chains where state persistence is assumed but never actually called
- API endpoint → flow_execution_service → Master Flow Orchestrator → execution operations → execution engine → CrewAI execution
- Success bubbles up through all layers, but no layer calls the state persistence method

**Debugging Methodology**:
1. **End-to-End Execution Tracing**: Map the complete execution flow through all layers
2. **Database State Verification**: Use direct SQL queries to verify actual vs expected state
3. **Log Pattern Analysis**: `docker logs container --tail N | grep -E "pattern"` to trace specific execution paths
4. **Incremental Fix Testing**: Make fixes and test each change with curl + database verification

## Solution Pattern: Phase Completion Injection
**Location**: `backend/app/services/discovery/flow_execution_service.py`

**Pattern**: After successful Master Flow Orchestrator execution, inject phase completion persistence:

```python
# After successful MFO execution
if result.get("status") != "failed":
    try:
        from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
            FlowPhaseManagementCommands,
        )
        
        phase_mgmt = FlowPhaseManagementCommands(
            db, context.client_account_id, context.engagement_id
        )
        
        # Extract phase data and agent insights from result
        phase_data = result.get("result", {}).get("crew_results", {}) or {}
        # ... extract agent insights ...
        
        # Call update_phase_completion to persist phase completion
        await phase_mgmt.update_phase_completion(
            flow_id=flow_id,
            phase=phase_to_execute,
            data=phase_data,
            completed=True,
            agent_insights=agent_insights,
        )
        
        # Update current_phase to next_phase if provided by MFO
        next_phase = result.get("result", {}).get("next_phase") or result.get("next_phase")
        if next_phase:
            # Direct SQL update to advance phase
            stmt = update(DiscoveryFlow).where(...).values(current_phase=next_phase)
            await db.execute(stmt)
            await db.commit()
    except Exception as persistence_error:
        # Log but don't fail main execution
        logger.error(f"Failed to persist phase completion: {persistence_error}")
```

## Phase Sequence Management Pattern
**Problem**: Phase sequences defined in multiple files, inconsistent when deprecated phases removed

**Files That Must Stay Synchronized**:
- `flow_phase_management.py` - completion checks and progress calculation
- `transition_utils.py` - phase transition logic  
- `state_transition_utils.py` - state validation

**Pattern**: Use systematic search to update all occurrences:
```bash
# Find all files with deprecated phase
mcp__serena__search_for_pattern "tech_debt_assessment"

# Update each file systematically
# Remove from phase sequences, completion checks, progress weights
```

## Testing Workflow Pattern
**Docker + Database Verification**:
```bash
# Execute phase
curl -X POST "http://localhost:8000/api/v1/unified-discovery/flows/{flow_id}/execute" \
-H "X-Client-Account-ID: {uuid}" -H "X-Engagement-ID: {uuid}" -H "X-User-ID: {uuid}"

# Verify database state  
docker exec -i migration_postgres psql -U postgres -d migration_db -c \
"SELECT flow_id, status, current_phase, asset_inventory_completed, progress_percentage FROM migration.discovery_flows WHERE flow_id = '{flow_id}';"

# Check execution logs
docker logs migration_backend --tail 20 | grep -E "(Phase completion|Auto-completing)"
```

## Key Success Metrics
- Phase completion boolean flags update to `true` 
- `current_phase` advances to next phase
- `progress_percentage` increases appropriately
- `status` transitions to "complete" when all phases done
- Subsequent executions blocked with "Cannot execute phase on completed flow"