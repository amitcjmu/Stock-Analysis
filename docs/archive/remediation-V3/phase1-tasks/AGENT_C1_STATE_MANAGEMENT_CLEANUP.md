# Phase 1 - Agent C1: State Management Cleanup

## Context
You are part of a parallel remediation effort to fix critical architectural issues in the AI Modernize Migration Platform. This is Track C of Phase 1, focusing on simplifying state management by removing the complex dual persistence system (CrewAI SQLite + PostgreSQL) and implementing a clean PostgreSQL-only solution.

### Required Reading Before Starting
- `docs/planning/PHASE-1-REMEDIATION-PLAN.md` - Overall Phase 1 objectives
- `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md` - Platform overview
- `docs/development/CrewAI_Development_Guide.md` - Current CrewAI implementation

### Phase 1 Goal
Eliminate the complex state synchronization between CrewAI's SQLite storage and PostgreSQL. Implement a single source of truth using PostgreSQL with proper state recovery and validation mechanisms.

## Your Specific Tasks

### 1. Remove SQLite Persistence from CrewAI Flows
**Files to modify**:
```
backend/app/services/crewai_flows/unified_discovery_flow.py
backend/app/services/crewai_flows/flow_state_persistence.py
backend/app/services/crewai_flows/flow_state_bridge.py (evaluate if needed)
```

Current problematic pattern:
```python
# REMOVE THIS PATTERN
class UnifiedDiscoveryFlow(Flow):
    def __init__(self):
        super().__init__()
        self._setup_sqlite_persistence()  # Remove
        self._sync_with_postgres()         # Remove
```

### 2. Implement PostgreSQL-Only State Storage
**File to create**: `backend/app/services/crewai_flows/persistence/postgres_store.py`

```python
"""
PostgreSQL-based state persistence for CrewAI flows.
Replaces the dual SQLite/PostgreSQL system with a single source of truth.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crewai_flow_state import CrewAIFlowStateExtensions
from app.core.context import RequestContext
import json

class PostgresFlowStateStore:
    """
    Single source of truth for CrewAI flow state.
    Features:
    - Atomic state updates
    - Optimistic locking
    - State recovery
    - Audit trail
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
    
    async def save_state(
        self, 
        flow_id: str, 
        state: Dict[str, Any],
        phase: str,
        version: Optional[int] = None
    ) -> None:
        """
        Save flow state with optimistic locking.
        Raises ConcurrentModificationError if version mismatch.
        """
        # Implementation with version checking
    
    async def load_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Load the latest state for a flow"""
        # Implementation
    
    async def create_checkpoint(self, flow_id: str, phase: str) -> str:
        """Create a recoverable checkpoint"""
        # Implementation
    
    async def recover_from_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Recover state from a checkpoint"""
        # Implementation
```

### 3. Create State Migration Utilities
**File to create**: `backend/app/services/crewai_flows/persistence/state_migrator.py`

```python
"""
Utilities to migrate existing SQLite states to PostgreSQL
"""

class StateMigrator:
    """One-time migration from SQLite to PostgreSQL"""
    
    async def migrate_active_flows(self) -> Dict[str, Any]:
        """
        Migrate all active flow states from SQLite to PostgreSQL
        Returns migration report
        """
        # Read from SQLite
        # Validate state structure
        # Write to PostgreSQL
        # Verify migration
        # Mark as migrated
```

### 4. Implement State Validation
**File to create**: `backend/app/core/flow_state_validator.py`

```python
"""
Validates flow state integrity and structure
"""

from typing import Dict, Any, List
from pydantic import BaseModel, validator
import json

class FlowStateValidator:
    """
    Ensures flow state consistency and validity
    """
    
    REQUIRED_FIELDS = ['flow_id', 'current_phase', 'phases_completed', 'state_data']
    
    @staticmethod
    def validate_state_structure(state: Dict[str, Any]) -> List[str]:
        """
        Validate state structure and return list of errors
        """
        errors = []
        
        # Check required fields
        for field in FlowStateValidator.REQUIRED_FIELDS:
            if field not in state:
                errors.append(f"Missing required field: {field}")
        
        # Validate phase progression
        if 'phases_completed' in state and 'current_phase' in state:
            if state['current_phase'] in state['phases_completed']:
                errors.append("Current phase already marked as completed")
        
        # Validate JSON serializable
        try:
            json.dumps(state)
        except TypeError as e:
            errors.append(f"State not JSON serializable: {e}")
        
        return errors
    
    @staticmethod
    def validate_phase_transition(
        current_state: Dict[str, Any], 
        new_phase: str
    ) -> bool:
        """
        Validate if phase transition is allowed
        """
        # Implementation
```

### 5. Update Flow State Manager
**File to modify**: `backend/app/services/crewai_flows/flow_state_manager.py`

Replace the existing dual-persistence logic with PostgreSQL-only operations:
```python
class FlowStateManager:
    """
    Manages CrewAI flow state with PostgreSQL as single source of truth
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.store = PostgresFlowStateStore(db, context)
        self.validator = FlowStateValidator()
    
    async def save_state(self, flow_id: str, state: Dict[str, Any]) -> None:
        """Save state with validation"""
        errors = self.validator.validate_state_structure(state)
        if errors:
            raise ValidationError(f"Invalid state: {', '.join(errors)}")
        
        await self.store.save_state(flow_id, state)
    
    async def transition_phase(
        self, 
        flow_id: str, 
        new_phase: str
    ) -> Dict[str, Any]:
        """Handle phase transitions with validation"""
        current_state = await self.store.load_state(flow_id)
        
        if not self.validator.validate_phase_transition(current_state, new_phase):
            raise InvalidTransitionError(f"Cannot transition to {new_phase}")
        
        # Update state
        current_state['current_phase'] = new_phase
        current_state['updated_at'] = datetime.utcnow().isoformat()
        
        await self.save_state(flow_id, current_state)
        return current_state
```

### 6. Add State Recovery Mechanisms
**File to create**: `backend/app/services/crewai_flows/persistence/state_recovery.py`

```python
"""
State recovery mechanisms for failed flows
"""

class FlowStateRecovery:
    """Handles recovery scenarios for flow states"""
    
    async def recover_failed_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Recover a failed flow to last known good state
        """
        # Find last checkpoint
        # Validate checkpoint state
        # Restore to checkpoint
        # Mark as recovered
    
    async def handle_corrupted_state(self, flow_id: str) -> None:
        """
        Handle corrupted state scenarios
        """
        # Archive corrupted state
        # Reset to initial state
        # Notify administrators
```

## Success Criteria
- [ ] SQLite persistence completely removed
- [ ] PostgreSQL as single source of truth
- [ ] State validation implemented
- [ ] Recovery mechanisms in place
- [ ] Zero data loss during migration
- [ ] Performance improved (no dual writes)
- [ ] All state operations atomic

## Interfaces with Other Agents
- **Agent A1** provides flow_id implementation
- **Agent B1** uses state management in API endpoints
- **Agent D1** relies on state for field mappings
- Coordinate on state schema in `backend/app/models/`

## Implementation Guidelines

### 1. Migration Strategy
1. Implement PostgreSQL store alongside existing
2. Add feature flag: `USE_POSTGRES_ONLY_STATE`
3. Run both systems in parallel initially
4. Migrate active flows one by one
5. Remove SQLite after verification

### 2. Performance Considerations
- Use connection pooling
- Implement caching for frequently accessed states
- Batch updates where possible
- Add indexes on flow_id and updated_at

### 3. Error Handling
```python
class StateError(Exception):
    """Base exception for state operations"""

class ConcurrentModificationError(StateError):
    """Raised when version conflict detected"""

class StateValidationError(StateError):
    """Raised when state validation fails"""

class StateRecoveryError(StateError):
    """Raised when state recovery fails"""
```

### 4. Monitoring
- Log all state transitions
- Track state operation latency
- Monitor validation failures
- Alert on recovery operations

## Commands to Run
```bash
# Run state migration
docker exec -it migration_backend python -m app.services.crewai_flows.persistence.state_migrator

# Validate all flow states
docker exec -it migration_backend python -m app.core.flow_state_validator --check-all

# Run performance tests
docker exec -it migration_backend python -m pytest tests/performance/test_state_persistence.py

# Check for SQLite references
docker exec -it migration_backend grep -r "sqlite" app/services/crewai_flows/
```

## Definition of Done
- [ ] All SQLite references removed from codebase
- [ ] PostgreSQL state store fully implemented
- [ ] State validation working correctly
- [ ] Recovery mechanisms tested
- [ ] Migration script successful on test data
- [ ] Performance benchmarks met (<50ms for state operations)
- [ ] No regressions in flow execution
- [ ] PR created with title: "feat: [Phase1-C1] PostgreSQL-only state management"
- [ ] Documentation updated

## State Schema
```python
# Unified state structure
{
    "flow_id": "uuid",
    "flow_version": 1,  # For optimistic locking
    "current_phase": "field_mapping",
    "phases_completed": ["data_import"],
    "created_at": "2024-01-20T10:00:00Z",
    "updated_at": "2024-01-20T10:30:00Z",
    "checkpoints": [
        {
            "id": "checkpoint_uuid",
            "phase": "data_import",
            "created_at": "2024-01-20T10:15:00Z"
        }
    ],
    "state_data": {
        # Phase-specific data
        "field_mapping": {
            "mappings": {},
            "confidence_scores": {}
        }
    },
    "metadata": {
        "client_account_id": "uuid",
        "engagement_id": "uuid",
        "user_id": "uuid"
    }
}
```

## Notes
- FlowStateBridge evaluation: Keep if it provides value, remove if redundant
- Consider event sourcing for audit trail
- Plan for state archival in future phases
- Ensure backward compatibility during migration