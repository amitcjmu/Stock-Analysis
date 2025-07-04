# Discovery Flow Architecture - Current State (Post-Cleanup July 2025)

## 🎯 **Overview**

This document provides the authoritative architectural reference for the Discovery Flow system after major cleanup (95% complete). It reflects the actual working implementation with real CrewAI flows, performance-optimized agent patterns, and multi-tenant architecture.

> **📚 Context**: Platform evolution journey detailed in `docs/development/PLATFORM_EVOLUTION_AND_CURRENT_STATE.md`
> **🔄 Status**: Major cleanup complete, V3 APIs removed, real CrewAI implementation active

## 🏗️ **Current Architecture (Post-Cleanup)**

### **Unified Discovery Flow System**
```
Frontend (React) → API v1 Only → Multiple Entry Points → Orchestration Layer
                                          ↓                        ↓
                                  Data Import Handler    UnifiedDiscoveryFlow
                                          ↓                        ↓
                                  DiscoveryFlowService   CrewAI Flow Manager
                                          ↓                        ↓
                                     PostgreSQL      →   CrewAI Crews/Agents
                                          ↓                        ↓
                                  Multi-Tenant Context    Performance Optimized
```

### **Key Components Status**

#### ✅ **Fully Implemented & Working**
- **UnifiedDiscoveryFlow**: Real CrewAI Flow with `@start/@listen` decorators
- **PostgreSQL-Only State**: Complete elimination of SQLite, using CrewAIFlowStateExtensions
- **Multi-Tenant Context**: Enforced via middleware with proper header validation
- **Performance-Optimized Mix**: Judicious use of single agents and crews (40-60s → <10s for 10 records)
- **Real CrewAI Integration**: No pseudo-agents, all real CrewAI patterns

#### ⚠️ **Remaining Issues (5%)**
- **Frontend API Usage**: Still needs consolidation to v1-only patterns
- **Session ID References**: Some files still use session_id instead of flow_id
- **Field Mapping UI**: Shows "0 active flows" - endpoint confusion

## 📊 **Complete Data Flow Diagram**

### **1. File Upload Flow**
```
User uploads CSV file
        ↓
Frontend: /discovery/import page
        ↓
POST /api/v1/data-import/store-import
        ↓
import_storage_handler.py
        ↓
Validates no incomplete flows exist (multi-tenant check)
        ↓
Stores in DataImport & RawImportRecord tables
        ↓
Triggers DiscoveryFlowService.initialize_discovery_flow()
        ↓
Creates flow in discovery_flows table
        ↓
Launches UnifiedDiscoveryFlow (CrewAI)
        ↓
Returns flow_id to frontend
```

### **2. Discovery Flow Execution**
```
UnifiedDiscoveryFlow.initialize_flow() [@start decorator]
        ↓
Sets up state in UnifiedDiscoveryFlowState model
        ↓
data_import_phase() [@listen(initialize_flow)]
        ↓
PhaseExecutionManager.execute_phase("data_import")
        ↓
DataImportValidationExecutor.execute()
        ↓
UnifiedFlowCrewManager.create_crew_on_demand("data_import_validation")
        ↓
Creates & executes DataImportValidationCrew (real CrewAI)
        ↓
Stores results in PostgreSQL via FlowStateManager
        ↓
field_mapping_phase() [@listen(data_import_phase)]
        ↓
... continues through all phases ...
```

### **3. Frontend Status Updates**
```
Frontend polls for status
        ↓
GET /api/v1/unified-discovery/flow/status/{flow_id}
        ↓
unified_discovery_modular.py → flow_routes.py
        ↓
DiscoveryOrchestrator.get_discovery_flow_status()
        ↓
Queries both:
  - discovery_flows table (main status)
  - CrewAIFlowStateExtensions (detailed state)
        ↓
Returns unified status to frontend
```

## 🗃️ **Database Architecture**

### **Primary Tables**
```sql
-- Main flow tracking
discovery_flows:
  - id: UUID (internal)
  - flow_id: UUID (from CrewAI, used everywhere)
  - client_account_id: UUID (multi-tenant)
  - engagement_id: UUID (multi-tenant)
  - user_id: UUID (defaults to "system")
  - status: VARCHAR
  - current_phase: VARCHAR
  - created_at, updated_at: TIMESTAMP

-- CrewAI state persistence
crewai_flow_state_extensions:
  - flow_id: UUID (foreign key)
  - flow_persistence_data: JSONB (full state)
  - flow_status: VARCHAR
  - flow_configuration: JSONB
  - updated_at: TIMESTAMP

-- Import data storage
data_imports:
  - id: UUID
  - client_account_id: UUID
  - engagement_id: UUID
  - file_name: VARCHAR
  - file_content: JSONB
  - status: VARCHAR

raw_import_records:
  - id: UUID
  - data_import_id: UUID (foreign key)
  - record_data: JSONB
  - validation_status: VARCHAR
```

### **Multi-Tenant Isolation**
- All tables include client_account_id and engagement_id
- Middleware enforces tenant context from headers
- Repository pattern (ContextAwareRepository) ensures tenant filtering

## 🔗 **API Architecture (Current Working State)**

### **API v1 Only (V3 Removed)**

#### **Discovery Flow Endpoints**
```python
# Unified Discovery (Modular Implementation)
POST /api/v1/unified-discovery/flow/initialize
GET  /api/v1/unified-discovery/flow/status/{flow_id}
POST /api/v1/unified-discovery/flow/execute
GET  /api/v1/unified-discovery/flows/active

# Data Import
POST /api/v1/data-import/store-import
GET  /api/v1/data-import/imports/{import_id}

# Discovery (Minimal for Frontend Compatibility)
GET  /api/v1/discovery/flows/active
GET  /api/v1/discovery/flow/status/{flow_id}
GET  /api/v1/discovery/flow/{flow_id}/agent-insights
GET  /api/v1/discovery/flow/{flow_id}/validation-status
```

### **Request Flow with Headers**
```typescript
// Required headers for ALL requests
const headers = {
  'Content-Type': 'application/json',
  'X-Client-Account-ID': clientAccountId,  // Required
  'X-Engagement-ID': engagementId,        // Required
  'X-User-ID': userId,                    // Optional (defaults to "system")
  'Authorization': `Bearer ${token}`
};

// Example: Initialize flow
const response = await fetch('/api/v1/unified-discovery/flow/initialize', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    execution_mode: 'hybrid',
    metadata: { source: 'cmdb_import' }
  })
});
```

## 🤖 **CrewAI Architecture**

### **Performance-Optimized Pattern**
Based on `docs/development/FLOW_PROCESSING_AGENT_DESIGN.md`, the system uses a judicious mix of:
- **Single Agents**: For focused, fast tasks (data validation, field analysis)
- **CrewAI Crews**: For complex, collaborative tasks (dependency mapping, tech debt analysis)

### **Crew Management Structure**
```
UnifiedDiscoveryFlow (CrewAI Flow)
    ↓
UnifiedFlowCrewManager
    ↓
Crew Factories:
  - data_import_validation → DataImportValidationCrew
  - attribute_mapping → FieldMappingCrew (fast/optimized)
  - data_cleansing → DataCleansingCrew
  - inventory → InventoryBuildingCrew
  - dependencies → AppServerDependencyCrew
  - tech_debt → TechnicalDebtCrew
```

### **Actual Working Code Pattern**
```python
# From UnifiedFlowCrewManager
def create_crew_on_demand(self, crew_type: str, **kwargs):
    if crew_type == "data_import_validation":
        # Single agent for speed
        crew = create_data_import_validation_crew(
            self.crewai_service,
            kwargs.get('raw_data', []),
            kwargs.get('metadata', {}),
            kwargs.get('shared_memory')
        )
    elif crew_type == "attribute_mapping":
        # Optimized crew (uses fast implementation)
        crew = create_fast_field_mapping_crew(
            self.crewai_service, 
            self.state
        )
    # ... other crews ...
    
    return crew
```

## 🔄 **Service Layer Architecture**

### **Key Services**

1. **DiscoveryFlowService** (`/services/discovery_flow_service/`)
   - Manages flow lifecycle
   - Coordinates with UnifiedDiscoveryFlow
   - Handles multi-tenant context

2. **CrewAIFlowService** (`/services/crewai_flow_service.py`)
   - Provides LLM configuration
   - Manages CrewAI integration
   - Handles crew execution

3. **FlowStateManager** (`/services/crewai_flows/flow_state_manager.py`)
   - High-level state management
   - Coordinates with PostgreSQL persistence
   - Handles state recovery

4. **PostgresFlowStateStore** (`/services/crewai_flows/persistence/postgres_store.py`)
   - Low-level PostgreSQL operations
   - Manages CrewAIFlowStateExtensions table
   - Handles checkpointing

### **Middleware Stack**
```python
# Applied in order (executes in reverse)
1. MultiTenantContextMiddleware
   - Extracts X-Client-Account-ID, X-Engagement-ID
   - Validates tenant context
   - Platform admin exemptions

2. CORSMiddleware
   - Handles CORS headers
   - Must be last (executes first)
```

## 🌐 **Frontend Integration**

### **React Hooks Architecture**
```typescript
// Current working implementation
useUnifiedDiscoveryFlow.ts:
  - Manages flow state
  - Handles API calls (currently mixed v1)
  - Provides flow operations

useDiscoveryFlowPolling.ts:
  - Polls for status updates
  - 2-second intervals
  - Updates UI state
```

### **Component Flow**
```
CMDBImport.tsx
    ↓
Calls useUnifiedDiscoveryFlow()
    ↓
User uploads file → initializeFlow()
    ↓
Polls status → updateFlowState()
    ↓
Shows progress in FlowProgressDisplay
```

## 📈 **Performance Characteristics**

### **Optimized Timings**
- **10 records processing**: ~8-10 seconds (down from 40-60s)
- **Flow initialization**: ~2-3 seconds
- **Phase transitions**: ~1-2 seconds
- **Status polling**: 2-second intervals

### **Optimization Techniques**
1. **Single Agent Usage**: For focused tasks like validation
2. **Fast Crew Implementations**: Optimized field mapping crew
3. **State-Based Processing**: Crews work directly with flow state
4. **Batch Processing**: For large datasets

## 🔒 **Security & Multi-Tenancy**

### **Enforcement Points**
1. **Middleware Level**: Validates headers, extracts context
2. **Service Level**: ContextAwareRepository pattern
3. **Database Level**: All queries filtered by tenant IDs
4. **API Level**: No automatic demo fallbacks

### **Platform Admin Exemptions**
- Admin endpoints exempt from tenant requirements
- Authenticated via platform admin role
- Can access cross-tenant data

## 🧹 **Legacy Code Status (Post-Cleanup)**

### **Archived to `/backend/archive/legacy/`**
- ❌ V3 API infrastructure (database abstraction layer)
- ❌ Pseudo-agent implementations (BaseDiscoveryAgent, etc.)
- ❌ Session-based flow management
- ❌ Dual persistence (SQLite + PostgreSQL)

### **Active Code Paths**
- ✅ `/api/v1/unified_discovery/` - Modular implementation
- ✅ `/services/crewai_flows/` - Real CrewAI flows
- ✅ `/services/discovery_flow_service/` - Flow management
- ✅ `/models/unified_discovery_flow_state.py` - Single state model

## 🎯 **Known Issues & Solutions**

### **1. Frontend API Version Mix**
- **Issue**: Frontend uses mixed v1 patterns
- **Solution**: Update `useUnifiedDiscoveryFlow.ts` to use v1 only
- **Timeline**: 1-2 weeks

### **2. Field Mapping UI "0 flows"**
- **Issue**: Endpoint confusion between different APIs
- **Solution**: Consolidate to unified discovery endpoints
- **Timeline**: 1 week

### **3. Session ID References**
- **Issue**: Some files still reference session_id
- **Solution**: Global search/replace to flow_id
- **Timeline**: 2-3 weeks

## 🔮 **Architecture Best Practices**

### **When Adding New Features**
1. **Use flow_id everywhere** - never session_id
2. **Include multi-tenant headers** - no exceptions
3. **Use real CrewAI patterns** - no pseudo-agents
4. **Follow performance patterns** - single agents for speed
5. **Update UnifiedDiscoveryFlowState** - single source of truth

### **Code Organization**
```
/backend/app/
  /api/v1/
    /unified_discovery/    # Main discovery API
  /services/
    /crewai_flows/        # CrewAI implementation
    /discovery_flow_service/  # Flow management
  /models/
    unified_discovery_flow_state.py  # State model
```

---

**Architecture Status**: Phase 5 with Major Cleanup Complete (95%)  
**Production Ready**: Yes, with minor UI issues  
**Performance**: Optimized with <10s for typical operations  
**Quality**: Clean architecture, minimal technical debt

*Last Updated: July 2025 - Post Major Cleanup*