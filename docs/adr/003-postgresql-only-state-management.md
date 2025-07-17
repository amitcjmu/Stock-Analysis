# ADR-003: PostgreSQL-Only State Management for CrewAI Flows

## Status
Accepted

## Context
The AI Modernize Migration Platform previously used a **dual persistence system** for CrewAI flow state management:

### Previous Architecture
```
CrewAI Flow (@persist decorator) → SQLite Database (Local File)
           ↓ (sync mechanism)
PostgreSQL Database → Enterprise Features (Multi-tenancy, Audit, etc.)
```

### Problems with Dual Persistence
1. **Synchronization Complexity**: Keeping SQLite and PostgreSQL in sync required complex coordination logic
2. **Data Consistency Issues**: Race conditions between SQLite and PostgreSQL updates
3. **Debugging Difficulty**: State inconsistencies between two data stores
4. **Performance Overhead**: Double writes for every state update
5. **Deployment Complexity**: SQLite file management in containerized environments
6. **Scalability Limitations**: SQLite doesn't support concurrent writes well
7. **Multi-tenancy Conflicts**: SQLite doesn't naturally support tenant isolation
8. **Backup Complications**: Two separate backup strategies required

## Decision
We will implement **PostgreSQL-only state management** for CrewAI flows, eliminating SQLite persistence entirely.

### New Architecture
```
CrewAI Flow → PostgresFlowStateStore → PostgreSQL Database
                        ↓
                Single Source of Truth
                - Multi-tenancy ✓
                - State validation ✓
                - Recovery mechanisms ✓
                - Audit trail ✓
                - Atomic operations ✓
```

### Key Components
1. **PostgresFlowStateStore**: Direct PostgreSQL state storage with optimistic locking
2. **FlowStateValidator**: Comprehensive state validation engine
3. **FlowStateRecovery**: Checkpoint-based recovery mechanisms
4. **StateMigrator**: One-time migration from SQLite to PostgreSQL
5. **FlowStateManager**: High-level state management coordination

## Consequences

### Positive
- **Single Source of Truth**: All flow state in PostgreSQL, eliminating sync issues
- **Better Performance**: No dual writes, faster state operations
- **Simplified Architecture**: Reduced code complexity and maintenance burden
- **Enterprise Features**: Native multi-tenancy, RBAC, and audit capabilities
- **Improved Reliability**: Atomic operations and ACID compliance
- **Better Scalability**: PostgreSQL handles concurrent operations efficiently
- **Unified Backup Strategy**: Single database backup covers all flow state
- **Enhanced Debugging**: Single location to inspect all flow state

### Negative
- **CrewAI Integration Changes**: Remove `@persist()` decorator from flows
- **Migration Effort**: Existing SQLite data needs migration to PostgreSQL
- **Custom Implementation**: Need to implement state management layer ourselves
- **Potential Complexity**: State management logic now in application code

### Risks
- **Data Loss**: SQLite to PostgreSQL migration must be bulletproof
- **Performance Regression**: Custom state management might be slower than CrewAI's built-in persistence
- **Recovery Complexity**: Need robust recovery mechanisms for failed flows

## Implementation

### Phase 1: PostgreSQL State Store ✅ (Completed)

#### PostgresFlowStateStore
```python
class PostgresFlowStateStore:
    async def save_state(self, flow_id: str, state: Dict[str, Any], 
                        phase: str, version: Optional[int] = None):
        # Optimistic locking with version checking
        # JSON serialization safety for UUIDs
        # Atomic database operations
        
    async def create_checkpoint(self, flow_id: str, phase: str) -> str:
        # Checkpoint creation for recovery
        
    async def cleanup_old_versions(self, flow_id: str, keep_versions: int = 5):
        # Version history management
```

#### FlowStateValidator
```python
class FlowStateValidator:
    REQUIRED_FIELDS = ['flow_id', 'current_phase', 'phase_completion', 'client_account_id']
    VALID_PHASES = ['initialization', 'data_import', 'field_mapping', ...]
    
    @staticmethod
    def validate_complete_state(state: Dict[str, Any]) -> Dict[str, Any]:
        # Comprehensive validation with detailed error reporting
        
    def validate_phase_transition(self, state: Dict[str, Any], new_phase: str) -> bool:
        # Phase transition validation with dependency checking
```

### Phase 2: CrewAI Flow Updates ✅ (Completed)
```python
# Before: SQLite persistence
@persist()  # ❌ Removed
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    pass

# After: PostgreSQL-only persistence
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    """
    PostgreSQL-only state management.
    Single source of truth for all discovery flow operations.
    """
```

### Phase 3: Recovery Mechanisms ✅ (Completed)
```python
class FlowStateRecovery:
    async def recover_failed_flow(self, flow_id: str) -> Dict[str, Any]:
        # Find last good checkpoint and recover state
        
    async def handle_corrupted_state(self, flow_id: str) -> None:
        # Archive corrupted state and attempt repair
```

### Phase 4: Migration Utilities ✅ (Completed)
```python
class StateMigrator:
    async def migrate_active_flows(self) -> Dict[str, Any]:
        # One-time migration from SQLite to PostgreSQL
        # Integrity verification and rollback capabilities
```

## State Management Features

### Optimistic Locking
```python
await store.save_state(
    flow_id=flow_id,
    state=updated_state,
    phase=current_phase,
    version=expected_version  # Prevents concurrent modifications
)
```

### Checkpoint Recovery
```python
# Automatic checkpoint creation at phase transitions
checkpoint_id = await store.create_checkpoint(flow_id, 'data_import')

# Recovery from last good checkpoint
recovered_state = await recovery.recover_failed_flow(flow_id)
```

### State Validation
```python
validation_result = validator.validate_complete_state(flow_state)
if not validation_result['valid']:
    await recovery.handle_corrupted_state(flow_id)
```

## Migration Strategy

### Data Migration Process
1. **Backup Current State**: Export all SQLite data before migration
2. **Validate PostgreSQL Schema**: Ensure target tables exist and are correct
3. **Migrate Active Flows**: Transfer in-progress flows with state preservation
4. **Verify Data Integrity**: Compare source and target data
5. **Update Application Config**: Switch to PostgreSQL-only mode
6. **Cleanup SQLite Files**: Remove SQLite databases after successful migration

### Zero-Downtime Migration
```bash
# 1. Run migration in background
python -m app.services.crewai_flows.persistence.state_migrator --migrate-all

# 2. Enable PostgreSQL-only mode
export USE_POSTGRES_ONLY_STATE=true

# 3. Verify all flows working
python -m app.core.flow_state_validator --check-all

# 4. Cleanup SQLite files (after verification)
python -m app.services.crewai_flows.persistence.state_migrator --cleanup-sqlite
```

## Performance Considerations

### Optimizations Implemented
- **Connection Pooling**: Efficient database connection management
- **Batch Operations**: Bulk operations for version cleanup
- **Index Usage**: Optimized queries using database indexes
- **JSON Serialization**: Safe handling of complex Python objects

### Performance Monitoring
```python
# Built-in performance tracking
@track_performance
async def save_state(self, ...):
    # State operation with timing metrics
    
# Target metrics:
# - State operations: <50ms for 95% of requests
# - Validation: <10ms for typical flow state
# - Recovery: <5 seconds for failed flow restoration
```

## Validation and Testing

### Test Coverage ✅ (Completed)
- **Unit Tests**: All state management components
- **Integration Tests**: End-to-end flow lifecycle
- **Performance Tests**: State operation latency and throughput
- **Recovery Tests**: Failure scenario handling
- **Migration Tests**: SQLite to PostgreSQL data integrity

### Success Criteria ✅ (Met)
- [x] SQLite persistence completely removed from codebase
- [x] PostgreSQL as single source of truth for all flow state
- [x] State validation prevents corrupted data
- [x] Recovery mechanisms handle failed flows
- [x] Zero data loss during migration process
- [x] Performance improved (no dual writes)
- [x] All state operations are atomic

## Alternatives Considered

### Alternative 1: Fix Dual Persistence Synchronization
**Rejected** - Would add complexity without solving fundamental architecture issues.

### Alternative 2: Use Redis for State Management
**Rejected** - Redis doesn't provide ACID guarantees needed for critical flow state.

### Alternative 3: External State Management Service
**Rejected** - Adds infrastructure complexity and potential latency.

### Alternative 4: Keep SQLite as Primary, Sync to PostgreSQL
**Rejected** - Doesn't solve multi-tenancy and scalability issues.

## Error Handling Strategy

### Exception Hierarchy
```python
StateError (Base)
├── ConcurrentModificationError    # Version conflicts
├── StateValidationError           # Validation failures  
└── StateRecoveryError            # Recovery failures
```

### Recovery Sequence
1. **Validation Failure** → Automatic repair attempt
2. **Repair Failure** → Checkpoint recovery
3. **No Checkpoints** → Reset to initial state
4. **Complete Failure** → Administrator notification

## Configuration

### Environment Variables
```bash
# Enable PostgreSQL-only mode
USE_POSTGRES_ONLY_STATE=true

# State management settings
FLOW_STATE_VALIDATION_ENABLED=true
FLOW_STATE_RECOVERY_ENABLED=true
FLOW_STATE_CLEANUP_HOURS=72
```

## Related ADRs
- [ADR-001](001-session-to-flow-migration.md) - Flow ID as primary identifier
- [ADR-002](002-api-consolidation-strategy.md) - API consolidation strategy

## References
- Implementation Details: `docs/planning/phase1-tasks/AGENT_C1_IMPLEMENTATION_SUMMARY.md`
- CrewAI Development Guide: `docs/development/CrewAI_Development_Guide.md`
- State Management Code: `backend/app/services/crewai_flows/persistence/`
- Validation Tests: `backend/app/services/crewai_flows/persistence/test_postgres_store.py`