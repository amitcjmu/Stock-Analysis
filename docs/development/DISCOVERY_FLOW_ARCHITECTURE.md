# Discovery Flow Architecture - Current State (Phase 5)

## 🎯 **Overview**

This document consolidates the current architecture of the Discovery Flow system, reflecting the **Phase 5 Flow-Based Architecture** with **Remediation Phase 1 (75% complete)** status. This is the authoritative architectural reference for the platform's core discovery workflow.

> **📚 Replaces**: Multiple discovery flow analysis files that have been consolidated and archived
> **🔄 Context**: Platform evolution journey detailed in `docs/development/PLATFORM_EVOLUTION_AND_CURRENT_STATE.md`

## 🏗️ **Current Architecture (Remediation State)**

### **Unified Discovery Flow System**
```
Frontend (Vercel) → API v1/v3 Mixed → DiscoveryFlowService → PostgreSQL
                                    ↓
                             UnifiedDiscoveryFlow → CrewAI Crews → True Agents
                                    ↓
                             Event Bus → Flow Coordination → Multi-Tenant Context
```

### **Key Components Status**

#### ✅ **Fully Implemented**
- **UnifiedDiscoveryFlow**: CrewAI Flow with `@start/@listen` decorators
- **PostgreSQL-Only State**: Complete elimination of SQLite persistence
- **Multi-Tenant Context**: `client_account_id` → `engagement_id` → `user_id` hierarchy
- **Event-Driven Coordination**: Real-time flow communication

#### ⚠️ **Partially Implemented (Active Issues)**
- **API Version Integration**: Mixed v1/v3 usage in frontend
- **Flow Context Synchronization**: Occasional data written to wrong tables
- **Session ID Migration**: 132+ files still contain session_id references

## 📊 **Flow Lifecycle Management**

### **Phase Progression**
```
1. Data Import       → 2. Field Mapping      → 3. Data Cleansing
       ↓                       ↓                       ↓
4. Asset Inventory   → 5. Dependency Analysis → 6. Tech Debt Analysis
       ↓                       ↓                       ↓
7. Migration Strategy → 8. Wave Planning      → 9. Final Report
```

### **CrewAI Flow Implementation**
```python
# Current working pattern (Phase 5)
from crewai import Flow

class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    @start()
    def initialize_flow(self):
        """Flow initialization with context setup"""
        self.state.flow_id = str(uuid.uuid4())
        self.state.client_account_id = self.context.client_account_id
        self.state.current_phase = "data_import"
        
    @listen(initialize_flow)
    def data_import_phase(self):
        """Handle CSV import and initial validation"""
        return self.kickoff_crew(DataImportCrew, self.state.data_import_input)
        
    @listen(data_import_phase)  
    def field_mapping_phase(self):
        """AI-driven field mapping with user approval"""
        return self.kickoff_crew(FieldMappingCrew, self.state.import_results)
        
    @listen(field_mapping_phase)
    def data_cleansing_phase(self):
        """Data quality improvement and standardization"""
        return self.kickoff_crew(DataCleansingCrew, self.state.mapped_data)
```

## 🗃️ **Database Architecture**

### **PostgreSQL-Only State Management**
```sql
-- Primary flow tracking table
CREATE TABLE discovery_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID UNIQUE NOT NULL,  -- Primary identifier (Phase 5)
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    flow_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    progress_percentage DECIMAL(5,2) DEFAULT 0.0,
    current_phase VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Multi-tenant asset storage
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id UUID REFERENCES discovery_flows(flow_id),
    client_account_id UUID NOT NULL,  -- Multi-tenant isolation
    engagement_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(50) NOT NULL,
    -- ... additional asset fields
);

-- CrewAI state persistence  
CREATE TABLE crewai_flow_state_extensions (
    flow_id UUID PRIMARY KEY REFERENCES discovery_flows(flow_id),
    state_data JSONB NOT NULL,
    checkpoint_data JSONB,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### **State Persistence Pattern**
```python
# PostgreSQL-only persistence (no SQLite)
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore

async def save_flow_state(flow_id: str, state_data: dict):
    async with managed_postgres_store(context) as store:
        await store.save_state(flow_id, state_data, current_phase)
        checkpoint_id = await store.create_checkpoint(flow_id, current_phase)
```

## 🔗 **API Architecture**

### **Current Endpoint Status (Remediation Context)**

#### **API v3 (Target Architecture)**
```python
# Primary endpoints (fully implemented, partial adoption)
POST /api/v3/discovery-flow/flows          # Create new flow
GET  /api/v3/discovery-flow/flows/{flow_id}/status  # Real-time status
PUT  /api/v3/discovery-flow/flows/{flow_id}/pause   # Flow control
POST /api/v3/data-import/imports           # File upload & processing
PUT  /api/v3/field-mapping/mappings/{flow_id}       # Field mappings
```

#### **API v1 (Current Primary in Practice)**
```python
# Legacy endpoints (still used by frontend during transition)
POST /api/v1/unified-discovery/flow/initialize      # Flow creation
GET  /api/v1/unified-discovery/flow/status/{flow_id} # Status checking
POST /api/v1/data-import/store-import               # Data import
```

### **Multi-Tenant Request Pattern**
```typescript
// Required headers for all API calls
const headers = {
  'Content-Type': 'application/json',
  'X-Client-Account-ID': clientAccountId,
  'X-Engagement-ID': engagementId,
  'Authorization': `Bearer ${token}`
};

// v3 API call pattern (target)
const response = await fetch('/api/v3/discovery-flow/flows', {
  method: 'POST',
  headers,
  body: JSON.stringify(flowData)
});
```

## 🤖 **Agent Architecture**

### **CrewAI Crews and Agents**

#### **Data Import Crew**
```python
class DataImportCrew:
    """Handles CSV file processing and initial validation"""
    
    agents = [
        DataSourceIntelligenceAgent,    # File analysis
        CMDBDataAnalyst,               # Data structure analysis
        DataValidationAgent            # Quality assessment
    ]
    
    async def execute(self, import_data: dict) -> dict:
        # CrewAI crew execution with agent coordination
        return await self.kickoff(context=import_data)
```

#### **Field Mapping Crew**  
```python
class FieldMappingCrew:
    """AI-driven field mapping with user approval workflow"""
    
    agents = [
        CMDBDataAnalyst,              # Source field analysis
        AssetIntelligenceAgent,       # Target schema expertise
        FieldMappingSpecialist        # Mapping recommendation
    ]
    
    async def execute(self, mapping_request: dict) -> dict:
        # Intelligent field mapping with confidence scores
        return await self.kickoff(context=mapping_request)
```

#### **Agent Service Layer Integration**
```python
# Bridge between CrewAI agents and platform services
from app.services.agent_service_layer import AgentServiceLayer

class UnifiedDiscoveryFlow(Flow):
    def __init__(self):
        self.agent_service = AgentServiceLayer()
        
    async def execute_with_agents(self, crew_type: str, data: dict):
        """Execute crew with proper service layer integration"""
        result = await self.agent_service.execute_crew(crew_type, data)
        return result
```

## 🔄 **Event-Driven Coordination**

### **Event Bus Pattern**
```python
# Real-time flow coordination
from app.services.flows.event_bus import EventBus

class FlowEventCoordinator:
    def __init__(self):
        self.event_bus = EventBus()
        
    async def handle_phase_completion(self, flow_id: str, phase: str):
        """Coordinate phase transitions via events"""
        await self.event_bus.emit('phase_completed', {
            'flow_id': flow_id,
            'phase': phase,
            'timestamp': datetime.utcnow()
        })
        
    @listen('phase_completed')
    async def advance_to_next_phase(self, event_data: dict):
        """Auto-advance flow to next phase"""
        await self.transition_flow_phase(
            event_data['flow_id'], 
            next_phase=self.determine_next_phase(event_data['phase'])
        )
```

### **Real-Time Updates**
```python
# WebSocket-style updates (planned for future)
# Currently using polling due to Vercel/Railway constraints

async def get_flow_status_updates(flow_id: str):
    """Real-time status updates for frontend"""
    while flow_active:
        status = await self.get_current_status(flow_id)
        yield status
        await asyncio.sleep(2)  # Polling interval
```

## 🌐 **Frontend Integration**

### **React Hook Pattern**
```typescript
// Current working pattern with mixed API usage
export const useUnifiedDiscoveryFlow = (options: {
  flowId?: string;
  enableRealTimeUpdates?: boolean;
}) => {
  const [flowState, setFlowState] = useState<DiscoveryFlowState>();
  
  // Mixed v1/v3 API usage during transition
  const apiVersion = options.useV3 ? 'v3' : 'v1';
  const baseUrl = `/api/${apiVersion}/discovery-flow`;
  
  const initializeFlow = async (data: FlowInitData) => {
    const response = await fetch(`${baseUrl}/flows`, {
      method: 'POST',
      headers: getMultiTenantHeaders(),
      body: JSON.stringify(data)
    });
    return response.json();
  };
  
  return {
    flowState,
    initializeFlow,
    pauseFlow,
    resumeFlow,
    getStatus
  };
};
```

### **Component Integration**
```typescript
// CMDBImport component integration
const CMDBImport: React.FC = () => {
  const { 
    flowState, 
    initializeFlow, 
    uploadFile 
  } = useUnifiedDiscoveryFlow({
    enableRealTimeUpdates: true
  });
  
  const handleFileUpload = async (file: File) => {
    // Initiate discovery flow with file upload
    const flow = await initializeFlow({
      flowName: `CMDB Import - ${file.name}`,
      dataSource: file
    });
    
    await uploadFile(flow.flow_id, file);
  };
  
  return (
    <DiscoveryFlowProvider>
      <FileUploadComponent onUpload={handleFileUpload} />
      <FlowProgressDisplay flow={flowState} />
      <PhaseNavigator currentPhase={flowState?.current_phase} />
    </DiscoveryFlowProvider>
  );
};
```

## 📈 **Performance & Scalability**

### **Current Performance Characteristics**
- **Flow Initialization**: ~2-3 seconds (includes file upload)
- **Phase Transitions**: ~1-2 seconds (agent coordination)
- **Data Processing**: Varies by file size (1MB = ~30 seconds)
- **Real-time Updates**: 2-second polling interval

### **Scalability Considerations**
```python
# Async processing for large datasets
async def process_large_dataset(flow_id: str, data: List[dict]):
    """Process data in batches to avoid timeouts"""
    batch_size = 1000
    for batch in chunk_data(data, batch_size):
        await process_batch(flow_id, batch)
        await asyncio.sleep(0.1)  # Prevent overwhelming
```

### **Resource Management**
- **Database Connections**: Async connection pooling
- **Memory Usage**: Streaming data processing for large files
- **Agent Coordination**: Event-driven to minimize blocking

## 🔒 **Security & Multi-Tenancy**

### **Row-Level Security**
```sql
-- Multi-tenant data isolation
CREATE POLICY tenant_isolation ON assets
FOR ALL TO application_role
USING (client_account_id = current_setting('app.client_account_id')::UUID);
```

### **Request Context Validation**
```python
# Context validation middleware
async def validate_tenant_context(request: Request):
    """Ensure all requests have proper tenant context"""
    client_id = request.headers.get('X-Client-Account-ID')
    engagement_id = request.headers.get('X-Engagement-ID')
    
    if not client_id or not engagement_id:
        raise HTTPException(401, "Missing tenant context")
        
    # Validate tenant access
    await validate_tenant_access(client_id, engagement_id)
```

## 🎯 **Current Issues & Workarounds**

### **Known Issues (Remediation Phase 1)**

#### **1. Flow Context Synchronization** (Priority: Critical)
- **Issue**: Flow data occasionally written to wrong tables
- **Cause**: Context header propagation issues
- **Workaround**: Manual flow recovery via admin tools
- **Fix Timeline**: Weeks 1-2

#### **2. Field Mapping UI Display** (Priority: Critical)
- **Issue**: Shows "0 active flows" despite flows existing
- **Cause**: API version mismatch in frontend queries
- **Workaround**: Use direct API v1 calls
- **Fix Timeline**: Weeks 1-2

#### **3. Session ID References** (Priority: Medium)
- **Issue**: 132+ files still contain session_id references
- **Cause**: Incomplete migration from Phase 2 architecture
- **Workaround**: Code works with mixed identifiers
- **Fix Timeline**: Weeks 5-6

### **Temporary Solutions**
```python
# Context recovery for lost flows
async def recover_flow_context(flow_id: str):
    """Manual recovery for flows with lost context"""
    flow = await get_flow_by_id(flow_id)
    if flow:
        # Restore proper context headers
        await set_flow_context(flow_id, flow.client_account_id, flow.engagement_id)
```

## 🔮 **Future Architecture (Post-Remediation)**

### **Target State (Phase 5 Complete)**
```
Frontend (Vercel) → API v3 Only → DiscoveryFlowService → PostgreSQL
                                 ↓
                          UnifiedDiscoveryFlow → CrewAI Crews → True Agents (100%)
                                 ↓
                          Event Bus → Flow Coordination → Multi-Tenant Context
                                 ✅                              ✅
                           Perfect Sync                    Working Properly
```

### **Planned Improvements**
- **API v3 Only**: Complete elimination of v1 API
- **True Agent Conversion**: All pseudo-agents converted to CrewAI
- **Performance Optimization**: Reduced agent chattiness
- **Enhanced Real-Time**: WebSocket implementation for better UX

---

**Architecture Status**: Phase 5 Flow-Based with 75% completion  
**Production Ready**: Yes, with known workarounds  
**Remediation Timeline**: 6-8 weeks for full completion  
**Quality**: Good infrastructure foundation, manageable technical debt

*This document consolidates information from multiple discovery flow analysis files and represents the authoritative current architecture state.*