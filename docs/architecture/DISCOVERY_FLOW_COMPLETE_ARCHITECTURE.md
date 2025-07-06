# Discovery Flow Complete Architecture

## Executive Summary

The Discovery Flow is a complex, multi-phase process that transforms uploaded CMDB data into a complete asset inventory with dependencies, ready for assessment. This document consolidates the complete architecture showing data flow, sequence of operations, state management, and controller hierarchy.

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
├─────────────────────────────────────────────────────────────┤
│                   API Gateway (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│              Master Flow Orchestrator (MFO)                  │
├─────────────────────────────────────────────────────────────┤
│        Discovery Flow Components │ CrewAI Integration        │
├─────────────────────────────────────────────────────────────┤
│              Service Layer │ Phase Executors                 │
├─────────────────────────────────────────────────────────────┤
│                  PostgreSQL Database                         │
└─────────────────────────────────────────────────────────────┘
```

## Complete Data Flow Path

### 1. File Upload → Flow Initialization
```
User → CMDBImport → UploadBlocker → API Gateway → DataImportService → MFO → UnifiedDiscoveryFlow → PostgreSQL
```

### 2. Phase Progression
```
MFO → Phase Executor → Service Layer → Database → MFO → UI Update
```

### 3. State Synchronization
```
MFO → discovery_flows table
MFO → crewai_flow_state_extensions table
MFO → State Reconciliation → UI
```

## Controllers and Orchestration

### Primary Controller: Master Flow Orchestrator

The MFO is the **single source of truth** for all flow operations:

```python
class MasterFlowOrchestrator:
    """THE orchestrator for all flow types"""
    
    def create_flow(flow_type: str, config: dict) -> str:
        # Creates any flow type
        
    def execute_phase(flow_id: str, phase_input: dict) -> dict:
        # Executes current phase
        
    def get_flow_status(flow_id: str) -> dict:
        # Returns unified status
        
    def transition_state(flow_id: str, new_state: str) -> bool:
        # Controls all transitions
```

### Subordinate Components

1. **UnifiedDiscoveryFlow**: CrewAI Flow implementation
2. **Phase Executors**: Business logic for each phase
3. **Service Layer**: Data operations
4. **UI Components**: User interaction triggers

## Discovery Flow Phases

### Phase 1: Data Import
- **Input**: Uploaded CMDB file
- **Processing**: Parse, validate, store raw data
- **Output**: Validated data ready for mapping
- **State**: `data_import` → `field_mapping`

### Phase 2: Field Mapping
- **Input**: Raw data columns
- **Processing**: Generate mapping suggestions
- **Output**: User-approved field mappings
- **State**: `field_mapping` → `awaiting_approval` → `data_cleansing`

### Phase 3: Data Cleansing
- **Input**: Mapped data
- **Processing**: Clean, validate, fix quality issues
- **Output**: Clean asset data
- **State**: `data_cleansing` → `asset_inventory`

### Phase 4: Asset Inventory
- **Input**: Clean data
- **Processing**: Categorize, enrich metadata
- **Output**: Complete asset catalog
- **State**: `asset_inventory` → `dependency_analysis`

### Phase 5: Dependency Analysis
- **Input**: Asset catalog
- **Processing**: Detect app-to-app, app-to-server dependencies
- **Output**: Dependency graph
- **State**: `dependency_analysis` → `tech_debt`

### Phase 6: Tech Debt Assessment
- **Input**: Assets and dependencies
- **Processing**: Analyze patterns, calculate metrics
- **Output**: Tech debt report
- **State**: `tech_debt` → `completed`

## State Management

### Dual Table Architecture

```sql
-- Table 1: Discovery-specific state
discovery_flows {
    flow_id: UUID (PK)
    status: active|paused|completed|failed
    current_phase: data_import|field_mapping|...
    progress_percentage: 0-100
    [phase]_completed: boolean flags
    crewai_state_data: JSONB
}

-- Table 2: Master flow coordination
crewai_flow_state_extensions {
    flow_id: UUID (PK, FK)
    flow_type: discovery
    flow_status: initialized|active|completed
    flow_persistence_data: JSONB
    phase_transitions: JSONB[]
}
```

### State Synchronization Rules

1. **Every state change updates both tables**
2. **MFO ensures atomic updates**
3. **State recovery on mismatch**
4. **Phase transitions logged**

## Critical Integration Points

### 1. Frontend → Backend Communication

```typescript
// Frontend flow status polling
const { data } = await api.get(`/api/v1/discovery/flows/${flowId}/status`);

// Phase execution
await api.post(`/api/v1/flows/${flowId}/execute`, { 
    phase_input: mappings 
});
```

### 2. MFO → Database Operations

```python
# Atomic state update pattern
async with db.begin():
    await update_discovery_flow(flow_id, state)
    await update_crewai_extensions(flow_id, state)
    await log_phase_transition(flow_id, state)
```

### 3. Service Layer Integration

```python
# Service injection pattern
class DataImportExecutor:
    def __init__(self, import_service: DataImportService):
        self.service = import_service
    
    async def execute(self, flow_id: str, input_data: dict):
        return await self.service.process_import(flow_id, input_data)
```

## Error Handling and Recovery

### Error States
- `failed`: Recoverable error, can retry
- `cancelled`: User-initiated termination
- `paused`: Temporary suspension

### Recovery Mechanisms
1. **State Recovery**: Reconcile mismatched states
2. **Partial Progress**: Save incomplete phase data
3. **Retry Logic**: Resume from last checkpoint
4. **Rollback**: Revert to previous phase

## Security and Multi-Tenancy

### Tenant Isolation
```python
# Every query includes tenant context
SELECT * FROM discovery_flows 
WHERE flow_id = ? 
AND client_account_id = ? 
AND engagement_id = ?
```

### Access Control
- JWT authentication required
- Role-based permissions
- Flow ownership validation

## Performance Optimization

### Current Implementation
- **Polling**: 3-second intervals for status updates
- **Batch Operations**: Multiple DB updates in transactions
- **Indexed Queries**: flow_id, tenant IDs indexed

### Future Optimizations
- Event-driven updates (when WebSocket enabled)
- Caching layer for frequently accessed data
- Parallel phase execution where possible

## Known Issues and Solutions

### Issue 1: Navigation Loop
- **Root Cause**: State mismatch between tables
- **Solution**: Synchronized state updates via MFO

### Issue 2: Competing Controllers
- **Root Cause**: Multiple components updating state
- **Solution**: MFO as single controller

### Issue 3: Phase Prerequisites
- **Root Cause**: No validation before phase execution
- **Solution**: PhaseValidator in MFO

## Migration Path to Full CrewAI

### Current State
- CrewAI Flow framework integrated
- Placeholder executors for business logic
- Basic agent structure defined

### Target State
- Intelligent agents for each phase
- Self-improving mappings
- Automated quality assessment
- Smart dependency detection

### Migration Steps
1. Replace executors with CrewAI agents
2. Implement agent memory and learning
3. Add agent collaboration patterns
4. Enable autonomous decision-making

## Monitoring and Observability

### Key Metrics
- Flow completion rate
- Average time per phase
- Error rate by phase
- User intervention points

### Logging Strategy
```python
logger.info(f"Flow {flow_id} transitioning: {old_state} → {new_state}")
logger.error(f"Phase {phase} failed for flow {flow_id}: {error}")
logger.debug(f"State reconciliation: {differences}")
```

### Health Checks
- Database connectivity
- Service availability
- State consistency validation

## API Reference

### Core Endpoints

```yaml
# Create discovery flow
POST /api/v1/flows
{
    "flow_type": "discovery",
    "configuration": {...}
}

# Get flow status
GET /api/v1/discovery/flows/{flow_id}/status

# Execute phase
POST /api/v1/flows/{flow_id}/execute
{
    "phase_input": {...}
}

# List active flows
GET /api/v1/discovery/flows/active

# Delete flow
DELETE /api/v1/flows/{flow_id}
```

## Conclusion

The Discovery Flow architecture provides a robust foundation for processing CMDB data through multiple phases while maintaining state consistency and enabling user interaction at key decision points. The Master Flow Orchestrator serves as the central control point, eliminating competing controllers and ensuring reliable operation.

### Key Strengths
- Single orchestrator pattern
- Comprehensive state management
- Multi-tenant isolation
- Extensible phase system

### Areas for Enhancement
- Full CrewAI agent implementation
- Real-time updates via WebSocket
- Advanced error recovery
- Performance optimization

This architecture supports the current implementation while providing a clear path for future enhancements and the transition to fully autonomous agent-based processing.