# ADR-012: Flow Status Management Separation

## Status
**Accepted** - 2025-01-16

## Context

The current flow status management system has been causing significant architectural issues due to conflicting responsibilities between master flows and child flows. The system maintains state in two separate database tables:

1. **Master Flow** (`crewai_flow_state_extensions`): Intended for high-level lifecycle management
2. **Child Flows** (`discovery_flows`, `assessment_flows`, etc.): Intended for operational flow state

### Current Problems

1. **Status Usage Confusion**: Application components inconsistently query master flow status vs child flow status for operational decisions
2. **Agent Decision Chaos**: Agents receive conflicting state information, leading to poor decision-making
3. **API Endpoint Inconsistency**: Different endpoints return different status sources for the same flow
4. **State Synchronization Issues**: Race conditions and inconsistent updates between master and child flows
5. **Frontend Integration Problems**: React hooks call wrong endpoints, causing UI to display incorrect flow status

### Specific Issues Identified

- Frontend `useUnifiedDiscoveryFlow` hook calls master flow status endpoint instead of discovery flow status
- Agent decision framework receives master flow status when it should use child flow status
- API endpoints `/api/v1/unified-discovery/flow/{flow_id}/status` vs `/api/v1/discovery/flow/status` return different status sources
- The Eaton Corp discovery flow stuck in "failed" state due to master flow showing "processing" while child flow shows "failed"

## Decision

We will implement a **clear separation of concerns** for flow status management with the following responsibilities:

### Master Flow Status Responsibilities
- **High-level lifecycle management**: `initialized`, `running`, `paused`, `completed`, `failed`, `deleted`
- **Cross-flow coordination**: When assets move between discovery → assessment → planning → execution
- **Tenant-level operations**: Flow cleanup, monitoring, auditing, performance tracking
- **Deletion/cancellation decisions**: Only master flow can mark flows as deleted or cancelled

### Child Flow Status Responsibilities  
- **All operational decisions**: Field mapping, data cleansing, agent decisions, user approvals
- **Phase-specific state management**: Detailed phase progression and validation
- **Frontend display**: Current operational status, progress indicators, error messages
- **Agent decision context**: All CrewAI agents use child flow status for operational decisions

### Status Synchronization Strategy

1. **Direct Atomic Updates**: For critical state changes (start/pause/resume):
   ```python
   async def update_flow_status_atomically(child_flow_id: str, master_flow_id: str, 
                                         child_status: str, master_status: str):
       async with db.begin():
           await update_child_flow_status(child_flow_id, child_status)
           await update_master_flow_status(master_flow_id, master_status)
   ```

2. **Event-Driven Sync**: For non-critical updates using event-driven architecture:
   ```python
   await publish_event(FlowStatusChangeEvent(
       flow_id=flow_id,
       child_status=child_status,
       requires_master_sync=True
   ))
   ```

3. **MFO Internal Sync Agent**: For terminal states (completed/failed/deleted):
   ```python
   class MFOSyncAgent:
       async def reconcile_master_status(self, master_flow_id: str):
           child_flow = await self.get_child_flow(master_flow_id)
           db_state_complete = await self.verify_db_state_complete(master_flow_id)
           
           if child_flow.status == "completed" and db_state_complete:
               await self.update_master_status(master_flow_id, "completed")
           elif child_flow.status == "failed" or not db_state_complete:
               await self.update_master_status(master_flow_id, "failed")
   ```

### State Transition Rules

**Master Flow Valid Transitions**:
```
initialized → [running, paused, failed]
running → [paused, completed, failed]
paused → [running, completed, failed]
failed → [running, deleted]  # Allow recovery from failed state
completed → [deleted]
deleted → []  # Terminal state
```

**Child Flow Operational Transitions** (examples for discovery):
```
active → [waiting_for_approval, processing, completed, failed]
waiting_for_approval → [processing, failed]
processing → [completed, failed, paused]
failed → [active, processing]  # Allow recovery
completed → [] # Terminal for child flow
```

## Implementation Plan

### Phase 1: Fix Incorrect Status Usage (High Priority)
1. **Frontend**: Update `useUnifiedDiscoveryFlow` to call discovery flow status endpoint
2. **API Routes**: Ensure discovery endpoints return child flow status
3. **Agent Framework**: Update agents to receive child flow status

### Phase 2: Implement Atomic Updates (Medium Priority)
1. **Transaction Handling**: Implement atomic updates for start/pause operations
2. **Error Recovery**: Add rollback mechanisms for failed dual updates
3. **Consistency Validation**: Periodic checks for state consistency

### Phase 3: Event-Driven Architecture (Low Priority)
1. **Event System**: Implement event-driven status synchronization
2. **MFO Sync Agent**: Create internal sync agent for terminal states  
3. **Monitoring**: Add consistency monitoring and alerting

## Consequences

### Positive
- **Clear Separation**: Eliminates confusion about which status to use for different purposes
- **Scalable Design**: Approach works across all flow types (discovery, assessment, planning, etc.)
- **Reduced Complexity**: No need for complex bidirectional synchronization
- **Better Agent Decisions**: Agents receive consistent, operational state information
- **Improved Frontend**: UI displays correct operational status to users

### Negative
- **Migration Effort**: Requires updating multiple components that currently use wrong status
- **Increased Complexity**: Need to implement atomic transactions and event handling
- **Performance Impact**: Dual writes will increase database load for status updates
- **Monitoring Overhead**: Need to monitor consistency between master and child flows

## Alternatives Considered

1. **Single Status Table**: Consolidate all status into one table
   - Rejected: Loses separation of concerns and doesn't scale across flow types
   
2. **Complex Synchronization**: Implement real-time bidirectional sync
   - Rejected: Too complex, prone to race conditions and deadlocks
   
3. **Event-Only Architecture**: Use only event-driven synchronization
   - Rejected: Too loose for critical operations like start/pause

## Related ADRs
- [ADR-006: Master Flow Orchestrator](006-master-flow-orchestrator.md)
- [ADR-011: Flow-Based Architecture Evolution](011-flow-based-architecture-evolution.md)

## Notes
- Master flow status should be treated as a "lifecycle envelope" around child flow operations
- Child flows are the "operational engine" that drives business logic and agent decisions
- Recovery from failed states is explicitly supported in both master and child flows
- The implementation prioritizes correctness over performance for critical state transitions