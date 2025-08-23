# Master Flow Orchestrator (MFO) Integration Guide

**Last Updated:** 2025-08-23  
**Status:** Complete - All flows integrated

## 📋 Overview

This document provides comprehensive guidance on how ALL flows in the AI Modernize Migration Platform integrate with the Master Flow Orchestrator (MFO) architecture. This integration ensures unified flow management, consistent APIs, and simplified operations across Discovery, Collection, Assessment, and all other flow types.

## 🎯 Core MFO Principles

### 1. Single Source of Truth
- **master_flow_id** is the PRIMARY identifier for ALL flow operations
- Child flow IDs are internal implementation details only
- MFO coordinates all flow lifecycle management

### 2. Unified API Pattern
- ALL flow lifecycle operations use `/api/v1/master-flows/*` endpoints
- Flow-specific operations use `master_flow_id` as the identifier
- No direct child flow ID exposure in public APIs

### 3. Consistent Flow Management
- Create, execute, pause, resume, delete operations follow the same pattern
- All flows register with MFO and get assigned a master_flow_id
- MFO handles state synchronization across tables

## 🏗️ MFO Architecture Pattern

### Master Flow Table (Primary)
```sql
-- crewai_flow_state_extensions - THE master record
CREATE TABLE crewai_flow_state_extensions (
    flow_id UUID PRIMARY KEY,              -- This IS the master_flow_id
    flow_type VARCHAR(50) NOT NULL,        -- 'discovery', 'collection', 'assessment', etc.
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    flow_status VARCHAR(50) NOT NULL,
    flow_configuration JSONB NOT NULL,
    flow_persistence_data JSONB NOT NULL,
    -- ... other MFO fields
);
```

### Child Flow Tables (Implementation Details)
```sql
-- Example: discovery_flows - internal implementation only
CREATE TABLE discovery_flows (
    flow_id UUID PRIMARY KEY,
    master_flow_id UUID NOT NULL,          -- FK to crewai_flow_state_extensions.flow_id
    -- discovery-specific fields for UI display and internal tracking
    data_import_completed BOOLEAN DEFAULT FALSE,
    field_mapping_completed BOOLEAN DEFAULT FALSE,
    -- ... other discovery-specific fields
    
    FOREIGN KEY (master_flow_id) REFERENCES crewai_flow_state_extensions(flow_id)
);
```

## 🔄 Flow Integration Patterns

### Pattern 1: Flow Creation
```python
# Through MFO (CORRECT)
master_flow_id = await mfo.create_flow(
    flow_type="discovery",
    configuration={
        "client_account_id": str(client_account_id),
        "engagement_id": str(engagement_id),
        "initial_data": data
    }
)

# Child flow record created automatically as part of MFO pattern
# Child record links to master via master_flow_id foreign key
```

### Pattern 2: Flow Operations
```python
# All operations use master_flow_id
await mfo.execute_phase(master_flow_id, phase_input)
await mfo.pause_flow(master_flow_id)
await mfo.resume_flow(master_flow_id)
await mfo.delete_flow(master_flow_id)
status = await mfo.get_flow_status(master_flow_id)
```

### Pattern 3: API Endpoints
```yaml
# Flow Lifecycle (ALL flow types)
POST   /api/v1/master-flows                    # Create any flow type
GET    /api/v1/master-flows/{master_flow_id}   # Get flow status
POST   /api/v1/master-flows/{master_flow_id}/execute  # Execute phase
POST   /api/v1/master-flows/{master_flow_id}/pause    # Pause flow
POST   /api/v1/master-flows/{master_flow_id}/resume   # Resume flow
DELETE /api/v1/master-flows/{master_flow_id}          # Delete flow
GET    /api/v1/master-flows/active?type=discovery     # List flows by type

# Flow-Specific Operations (use master_flow_id)
GET    /api/v1/discovery/flows/{master_flow_id}/details
GET    /api/v1/collection/questionnaires/{master_flow_id}
PUT    /api/v1/assessment/{master_flow_id}/applications/{appId}/components
```

## 📊 Flow Type Integration Status

### ✅ Fully Integrated Flows

#### Discovery Flow
- **Primary ID:** master_flow_id
- **Child Table:** discovery_flows
- **Key Endpoints:** `/api/v1/master-flows/*` for lifecycle
- **Specific Operations:** `/api/v1/unified-discovery/*` (using master_flow_id)

#### Collection Flow  
- **Primary ID:** master_flow_id
- **Child Table:** collection_flows
- **Key Endpoints:** `/api/v1/master-flows/*` for lifecycle
- **Specific Operations:** `/api/v1/collection/*` (using master_flow_id)

#### Assessment Flow
- **Primary ID:** master_flow_id  
- **Child Table:** assessment_flows
- **Key Endpoints:** `/api/v1/master-flows/*` for lifecycle
- **Specific Operations:** `/api/v1/assessment/*` (using master_flow_id)

### 🔄 Integration Template for New Flows

When adding a new flow type to the platform:

#### 1. Register Flow Type with MFO
```python
# In flow type registry
PLANNING_FLOW_CONFIG = FlowTypeConfig(
    name="planning",
    display_name="Planning Flow",
    phases=[...],
    crew_class=PlanningFlow,
    output_schema=PlanningFlowOutput
)

flow_registry.register(PLANNING_FLOW_CONFIG)
```

#### 2. Create Child Table (if needed)
```sql
CREATE TABLE planning_flows (
    flow_id UUID PRIMARY KEY,
    master_flow_id UUID NOT NULL,
    -- planning-specific tracking fields
    wave_planning_completed BOOLEAN DEFAULT FALSE,
    resource_allocation_completed BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (master_flow_id) REFERENCES crewai_flow_state_extensions(flow_id)
);
```

#### 3. Implement Flow Service
```python
class PlanningFlowService:
    def __init__(self, mfo: MasterFlowOrchestrator):
        self.mfo = mfo
    
    async def create_planning_flow(self, config: Dict) -> str:
        # Always create through MFO
        master_flow_id = await self.mfo.create_flow(
            flow_type="planning",
            configuration=config
        )
        
        # Create child record linked to master
        await self._create_planning_flow_record(master_flow_id)
        
        return master_flow_id  # Return master_flow_id only
    
    async def execute_planning_phase(self, master_flow_id: str, phase_input: Dict):
        return await self.mfo.execute_phase(master_flow_id, phase_input)
```

#### 4. Implement API Endpoints
```python
@router.post("/api/v1/master-flows")
async def create_flow(request: CreateFlowRequest):
    if request.flow_type == "planning":
        planning_service = get_planning_service()
        master_flow_id = await planning_service.create_planning_flow(request.configuration)
        return {"master_flow_id": master_flow_id}
    # ... handle other flow types

@router.get("/api/v1/planning/{master_flow_id}/details")
async def get_planning_details(master_flow_id: str):
    # Use master_flow_id for all operations
    return await planning_service.get_planning_details(master_flow_id)
```

## 🚨 Critical Don'ts

### ❌ Never Do These Things

```python
# DON'T expose child flow IDs to API consumers
return {"discovery_flow_id": child_flow_id}  # WRONG!

# DON'T use child flow IDs for operations
await some_operation(discovery_flow_id)  # WRONG!

# DON'T bypass MFO for flow operations
await direct_database_update(flow_id)  # WRONG!

# DON'T create flows without going through MFO
flow_id = create_discovery_flow_directly()  # WRONG!
```

### ✅ Always Do These Things

```python
# Always return master_flow_id to clients
return {"master_flow_id": master_flow_id}  # CORRECT!

# Always use master_flow_id for operations
await mfo.execute_phase(master_flow_id, input)  # CORRECT!

# Always route through MFO
master_flow_id = await mfo.create_flow(...)  # CORRECT!

# Always reference master_flow_id in UI
const { data } = useFlowStatus(masterFlowId);  // CORRECT!
```

## 🛠️ Implementation Checklist

Before implementing any flow integration:

- [ ] **CRITICAL**: Use master_flow_id as the primary identifier in ALL public APIs
- [ ] Route all flow lifecycle operations through MFO endpoints
- [ ] Create child flow records that link to master_flow_id (internal use only)
- [ ] Never expose child flow IDs to API consumers or UI components
- [ ] Use `/api/v1/master-flows/*` for create, status, execute, pause, resume, delete
- [ ] Implement flow-specific endpoints that accept master_flow_id as parameter
- [ ] Update frontend components to use master_flow_id exclusively
- [ ] Test complete flow lifecycle using only master_flow_id
- [ ] Document flow-specific operations and their master_flow_id usage

## 🎯 Frontend Integration

### React Hook Pattern
```typescript
// Use master_flow_id throughout
export function useFlowStatus(masterFlowId: string) {
    return useQuery({
        queryKey: ['flow-status', masterFlowId],
        queryFn: () => apiClient.get(`/api/v1/master-flows/${masterFlowId}`)
    });
}

// Flow operations through MFO
export function useFlowOperations() {
    return {
        executePhase: (masterFlowId: string, input: any) => 
            apiClient.post(`/api/v1/master-flows/${masterFlowId}/execute`, input),
        
        pauseFlow: (masterFlowId: string) =>
            apiClient.post(`/api/v1/master-flows/${masterFlowId}/pause`),
        
        resumeFlow: (masterFlowId: string) =>
            apiClient.post(`/api/v1/master-flows/${masterFlowId}/resume`)
    };
}
```

### Component Integration
```typescript
interface FlowComponentProps {
    masterFlowId: string;  // Always use master_flow_id
}

export function DiscoveryFlowComponent({ masterFlowId }: FlowComponentProps) {
    const { data: flowStatus } = useFlowStatus(masterFlowId);
    const { executePhase } = useFlowOperations();
    
    const handlePhaseExecution = async (phaseInput: any) => {
        await executePhase(masterFlowId, phaseInput);
    };
    
    return (
        <div>
            <h1>Flow Status: {flowStatus?.flow_status}</h1>
            {/* Use master_flow_id for all operations */}
        </div>
    );
}
```

## 📈 Migration Guide

### For Existing Flows

If you have existing flows that don't follow the MFO pattern:

#### 1. Assess Current State
```bash
# Check for direct child flow ID usage
grep -r "discovery_flow_id\|collection_flow_id\|assessment_flow_id" src/
grep -r "flows/{flow_id}" backend/app/api/
```

#### 2. Update API Endpoints
```python
# OLD (deprecated)
@router.get("/api/v1/discovery/flows/{flow_id}")
async def get_discovery_flow(flow_id: str):
    return await discovery_service.get_flow(flow_id)

# NEW (MFO-aligned)  
@router.get("/api/v1/master-flows/{master_flow_id}")
async def get_flow_status(master_flow_id: str):
    return await mfo.get_flow_status(master_flow_id)

@router.get("/api/v1/discovery/{master_flow_id}/details")
async def get_discovery_details(master_flow_id: str):
    return await discovery_service.get_details(master_flow_id)
```

#### 3. Update Frontend Services
```typescript
// OLD (deprecated)
export const discoveryService = {
    getFlow: (flowId: string) => api.get(`/api/v1/discovery/flows/${flowId}`)
};

// NEW (MFO-aligned)
export const discoveryService = {
    getFlow: (masterFlowId: string) => api.get(`/api/v1/master-flows/${masterFlowId}`),
    getDetails: (masterFlowId: string) => api.get(`/api/v1/discovery/${masterFlowId}/details`)
};
```

#### 4. Update Database References
```sql
-- Ensure child tables reference master_flow_id
ALTER TABLE discovery_flows 
ADD COLUMN master_flow_id UUID REFERENCES crewai_flow_state_extensions(flow_id);

-- Update existing records to link to master flows
UPDATE discovery_flows df 
SET master_flow_id = cfse.flow_id 
FROM crewai_flow_state_extensions cfse 
WHERE cfse.flow_type = 'discovery' 
AND df.created_at = cfse.created_at;  -- Match by timestamp or other criteria
```

## 🎉 Benefits of MFO Integration

### 1. Unified Management
- Single entry point for all flow operations
- Consistent API patterns across all flow types
- Simplified frontend development

### 2. Better Monitoring
- Centralized flow status tracking  
- Unified analytics across flow types
- Single dashboard for all flows

### 3. Improved Maintainability
- Reduced code duplication
- Consistent error handling
- Simplified testing patterns

### 4. Enhanced Scalability
- Easy to add new flow types
- Consistent performance optimizations
- Unified caching strategies

## 🔍 Troubleshooting

### Common Issues

#### Issue: 404 errors when accessing flow endpoints
**Cause:** Using old endpoint patterns or child flow IDs
**Solution:** Update to use `/api/v1/master-flows/{master_flow_id}` endpoints

#### Issue: Flow operations failing
**Cause:** Passing child flow IDs instead of master_flow_id
**Solution:** Ensure all operations use master_flow_id as the identifier

#### Issue: UI can't find flow data
**Cause:** Frontend using deprecated child flow ID references
**Solution:** Update React components to use master_flow_id exclusively

### Validation Commands

```bash
# Check for deprecated patterns
grep -r "flows/{.*id}" backend/app/api/v1/
grep -r "flow_id}" src/components/
grep -r "/flows/" src/services/

# Verify MFO endpoint usage
grep -r "master-flows" backend/app/api/v1/
grep -r "masterFlowId\|master_flow_id" src/
```

---

## 📚 Related Documentation

- [ADR-006: Master Flow Orchestrator](../adr/006-master-flow-orchestrator.md)
- [MFO Design Document](../development/master_flow_orchestrator/DESIGN_DOCUMENT.md)
- [Discovery Flow Architecture](./DISCOVERY_FLOW_COMPLETE_ARCHITECTURE.md)
- [API Endpoint Patterns](../api/v3/README.md)

---

**Remember:** The master_flow_id is the single source of truth for all flow operations. Child flow IDs are internal implementation details that should never be exposed to API consumers or UI components.