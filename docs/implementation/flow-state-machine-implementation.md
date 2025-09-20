# Flow State Machine Implementation Guide

## Overview

This document describes the comprehensive flow state machine implementation that addresses the status transition logic issues identified in PR #374. The solution provides robust state management for discovery flow phases with support for failures, rollbacks, partial completions, and error recovery.

## Problem Statement

The original `flow_phase_management.py` had several critical issues:

1. **No handling for phase failures or rollbacks**: Status transitions only accounted for successful completion
2. **Progress percentage not incrementally updated**: Only forced to 100% on completion
3. **No validation of status transition order**: Could transition to invalid states
4. **Missing error states**: No support for retry mechanisms or recovery

## Solution Architecture

### 1. State Machine Design

The solution implements a comprehensive state machine with two levels:

#### Phase States (Individual Phase Tracking)
```python
class PhaseState(Enum):
    NOT_STARTED = "not_started"           # Phase has not begun
    IN_PROGRESS = "in_progress"           # Phase is currently executing
    WAITING_VALIDATION = "waiting_validation"  # Phase completed, awaiting validation
    WAITING_APPROVAL = "waiting_approval"     # Phase completed, awaiting user approval
    COMPLETED = "completed"               # Phase successfully completed
    FAILED = "failed"                     # Phase failed execution
    RETRY_NEEDED = "retry_needed"         # Phase failed but can be retried
    ROLLED_BACK = "rolled_back"           # Phase was completed but rolled back
```

#### Flow Status (Overall Flow State)
```python
class FlowStatus(Enum):
    INITIALIZED = "initialized"          # Flow created but not started
    ACTIVE = "active"                    # Flow is running with phases in progress
    DATA_GATHERING = "data_gathering"    # Data import and validation phases
    DISCOVERY = "discovery"              # Field mapping and data cleansing phases
    ASSESSMENT_READY = "assessment_ready" # Asset inventory completed
    PLANNING = "planning"                # Dependency analysis phase
    WAITING_APPROVAL = "waiting_approval" # One or more phases need user approval
    RETRY_PENDING = "retry_pending"      # One or more phases need retry
    ERROR_RECOVERY = "error_recovery"    # Flow is in error recovery mode
    COMPLETED = "completed"              # All phases completed successfully
    FAILED = "failed"                    # Flow failed and cannot continue
    PAUSED = "paused"                    # Flow execution paused by user
    CANCELLED = "cancelled"              # Flow cancelled by user
```

### 2. Transition Validation

The state machine enforces valid transitions through comprehensive validation matrices:

```python
VALID_PHASE_TRANSITIONS = {
    PhaseState.NOT_STARTED: {PhaseState.IN_PROGRESS},
    PhaseState.IN_PROGRESS: {
        PhaseState.WAITING_VALIDATION,
        PhaseState.WAITING_APPROVAL,
        PhaseState.COMPLETED,
        PhaseState.FAILED,
        PhaseState.RETRY_NEEDED
    },
    PhaseState.COMPLETED: {
        PhaseState.ROLLED_BACK,
        PhaseState.RETRY_NEEDED
    },  # Can be reverted
    # ... (full matrix in implementation)
}
```

### 3. Incremental Progress Calculation

Progress is calculated based on both phase completion and internal progress within phases:

```python
PHASE_PROGRESS_WEIGHTS = {
    PhaseState.NOT_STARTED: 0.0,
    PhaseState.IN_PROGRESS: 0.3,          # 30% when started
    PhaseState.WAITING_VALIDATION: 0.7,   # 70% when awaiting validation
    PhaseState.WAITING_APPROVAL: 0.8,     # 80% when awaiting approval
    PhaseState.COMPLETED: 1.0,            # 100% when completed
    PhaseState.FAILED: 0.0,               # Back to 0% on failure
    PhaseState.RETRY_NEEDED: 0.1,         # 10% when retry needed
    PhaseState.ROLLED_BACK: 0.0           # Back to 0% when rolled back
}
```

## Implementation Components

### 1. FlowStateMachine Service

**File**: `backend/app/services/flow_state_machine.py`

Core state machine logic providing:
- Transition validation
- Progress calculation
- Flow status determination
- Error handling
- Recovery options generation

**Key Methods**:
- `validate_phase_transition()`: Validates individual phase transitions
- `validate_flow_transition()`: Validates overall flow transitions
- `calculate_progress()`: Computes incremental progress
- `determine_flow_status()`: Determines appropriate flow status
- `get_recovery_options()`: Provides recovery paths for failed states

### 2. Enhanced Phase Management Commands

**File**: `backend/app/repositories/discovery_flow_repository/commands/enhanced_flow_phase_management.py`

Enhanced phase management with backward compatibility:
- Robust state validation
- Error recovery mechanisms
- Rollback capabilities
- Audit trail maintenance

**New Methods**:
- `rollback_phase()`: Rollback completed phases for revision
- `retry_failed_phase()`: Retry failed phases
- `get_flow_status_summary()`: Comprehensive status overview

### 3. Database Schema Enhancements

**File**: `backend/alembic/versions/add_phase_state_machine_fields.py`

New database fields:
- `phase_states`: JSONB field for granular phase state tracking
- `transition_history`: Audit trail of all state transitions
- `error_context`: Detailed error context for debugging
- `retry_count`: Number of retry attempts
- `last_retry_at`: Timestamp of last retry

### 4. Comprehensive Test Suite

**File**: `backend/tests/services/test_flow_state_machine.py`

Complete test coverage including:
- Valid and invalid transitions
- Progress calculation scenarios
- Error handling and recovery
- Edge cases and rollback scenarios
- Integration tests with realistic workflows

## Key Features

### 1. Backward Compatibility

The implementation maintains full backward compatibility:
- Existing boolean completion fields still work
- Existing API contracts preserved
- Gradual migration path provided
- No breaking changes to existing functionality

### 2. Error Recovery and Retry Mechanisms

Comprehensive error handling:
- Structured error responses following CLAUDE.md patterns
- Distinction between retryable and non-retryable errors
- Automatic recovery path suggestions
- Retry count tracking and limits

### 3. Phase Order Enforcement

Dependency validation:
- Phases must complete in correct order
- Dependencies validated before transitions
- Clear error messages for order violations
- Rollback support for dependency changes

### 4. Audit Trail and Monitoring

Complete observability:
- All transitions logged with metadata
- User attribution for manual transitions
- Performance metrics and timing
- Error context preservation

## Migration Strategy

### Phase 1: Database Schema Update
1. Run the Alembic migration to add new fields
2. Execute data migration function to populate phase_states
3. Validate data consistency

### Phase 2: Service Integration
1. Update existing services to use enhanced commands
2. Add new endpoints for rollback and retry operations
3. Implement state machine validation in workflows

### Phase 3: Frontend Integration
1. Update UI components to display granular states
2. Add controls for rollback and retry operations
3. Enhance progress indicators with incremental updates

### Phase 4: Monitoring and Optimization
1. Add monitoring for state machine performance
2. Implement alerting for stuck or failed flows
3. Optimize transition logic based on usage patterns

## Usage Examples

### Basic Phase Transition
```python
from app.services.flow_state_machine import FlowStateMachine, PhaseState

state_machine = FlowStateMachine()

# Validate transition
is_valid, error = state_machine.validate_phase_transition(
    "data_import", PhaseState.NOT_STARTED, PhaseState.IN_PROGRESS
)

if is_valid:
    # Execute transition
    success, error = state_machine.transition_phase(
        phase="data_import",
        current_state=PhaseState.NOT_STARTED,
        target_state=PhaseState.IN_PROGRESS,
        reason="user_initiated",
        user_id="user123"
    )
```

### Rollback Completed Phase
```python
commands = EnhancedFlowPhaseManagementCommands(db, client_id, engagement_id)

result = await commands.rollback_phase(
    flow_id="flow123",
    phase="field_mapping",
    reason="Data quality issues discovered",
    user_id="user123"
)
```

### Retry Failed Phase
```python
result = await commands.retry_failed_phase(
    flow_id="flow123",
    phase="asset_inventory",
    user_id="user123"
)
```

### Get Recovery Options
```python
phase_states = {
    "data_import": PhaseState.COMPLETED,
    "field_mapping": PhaseState.FAILED,
    "data_cleansing": PhaseState.NOT_STARTED
}

recovery_options = state_machine.get_recovery_options(phase_states)
# Returns list of available recovery actions
```

## Error Handling

### Structured Error Responses

All errors follow the CLAUDE.md pattern:
```python
{
    "status": "failed",
    "error_code": "INVALID_PHASE_TRANSITION",
    "message": "Cannot transition phase 'data_import' from 'not_started' to 'completed'",
    "details": {
        "valid_transitions": ["in_progress"]
    },
    "retry_allowed": false,
    "timestamp": "2025-01-19T10:30:00Z"
}
```

### Retryable vs Non-Retryable Errors

**Retryable Errors**:
- `PHASE_EXECUTION_FAILED`
- `AGENT_TIMEOUT`
- `EXTERNAL_SERVICE_ERROR`
- `TEMPORARY_RESOURCE_UNAVAILABLE`

**Non-Retryable Errors**:
- `INVALID_TRANSITION`
- `DATA_VALIDATION_FAILED`
- `PERMISSION_DENIED`
- `MALFORMED_REQUEST`

## Performance Considerations

### Database Optimizations
- GIN index on `phase_states` JSONB field for fast queries
- Regular index on `retry_count` for monitoring
- Efficient JSON operations for state updates

### Memory Management
- Lightweight state machine instances
- Minimal memory footprint for transition history
- Efficient enum usage for state representation

### Caching Strategy
- Phase state caching for frequently accessed flows
- Transition validation result caching
- Recovery options caching

## Monitoring and Alerting

### Key Metrics
- Phase transition success/failure rates
- Average time spent in each phase state
- Retry attempt frequency and success rates
- Rollback frequency by phase

### Alerts
- Flows stuck in error states for extended periods
- High retry rates indicating systemic issues
- Unexpected state transitions
- Performance degradation in state machine operations

## Future Enhancements

### Advanced Features
- Conditional phase execution based on data quality
- Parallel phase execution for independent phases
- Machine learning-based failure prediction
- Automated recovery for known failure patterns

### Integration Opportunities
- Integration with master flow orchestrator state machine
- Cross-flow dependency tracking
- Tenant-specific state machine customization
- External system integration for approvals

## Conclusion

This comprehensive state machine implementation addresses all the critical issues identified in PR #374 while maintaining backward compatibility and following established architectural patterns. The solution provides:

✅ **Robust state transitions** with comprehensive validation
✅ **Error recovery mechanisms** with retry and rollback support
✅ **Incremental progress calculation** for better user experience
✅ **Phase order enforcement** preventing invalid transitions
✅ **Comprehensive testing** ensuring reliability
✅ **Migration strategy** for safe deployment
✅ **Performance optimization** for enterprise scale
✅ **Monitoring and observability** for operational excellence

The implementation follows all CLAUDE.md guidelines including atomic transactions, tenant scoping, structured error responses, and the ADR-012 separation of concerns between master and child flow status management.