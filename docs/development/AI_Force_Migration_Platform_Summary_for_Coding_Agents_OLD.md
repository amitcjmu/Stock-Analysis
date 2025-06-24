# AI Force Migration Platform - Current Architecture Summary for Coding Agents

## 🎯 **CRITICAL: Current Architecture State (January 2025)**

**This platform has undergone THREE major architectural pivots. You MUST follow the current CrewAI Flow-based architecture and AVOID legacy patterns.**

### **❌ AVOID: Legacy Patterns from Previous Pivots**

#### **Pivot 1: Heuristic-Based Design (DEPRECATED)**
- ❌ Hard-coded rules and static logic
- ❌ Simple AI elements without agent intelligence
- ❌ Manual data processing workflows
- ❌ Static field mapping configurations

#### **Pivot 2: Individual Agent Architecture (SUPERSEDED)**
- ❌ 17 standalone individual agents without crews
- ❌ Direct agent-to-agent communication
- ❌ Simple agent orchestration without flows
- ❌ Basic task distribution patterns

#### **✅ CURRENT: CrewAI Flow-Based Architecture (ACTIVE)**
- ✅ **CrewAI Flows** with @start/@listen decorators
- ✅ **Specialized Crews** with manager agents and hierarchical coordination
- ✅ **Agent Collaboration** within crews using shared memory and knowledge bases
- ✅ **Flow State Management** with proper persistence and phase tracking
- ✅ **Enterprise Features**: Multi-tenancy, learning, and knowledge management

---

## 🏗️ **Current Architecture Overview**

### **CrewAI Flow Architecture (v0.19.1+)**

```mermaid
graph TD
    A[DiscoveryFlow - CrewAI Flow] --> B[Field Mapping Crew]
    B --> C[Data Cleansing Crew]
    C --> D[Inventory Building Crew]
    D --> E[App-Server Dependency Crew]
    E --> F[App-App Dependency Crew]
    F --> G[Technical Debt Crew]
    G --> H[Discovery Integration]
    
    subgraph "Field Mapping Crew"
        B1[CMDB Field Mapping Manager]
        B2[Schema Structure Expert]
        B3[Attribute Mapping Specialist]
        B4[Knowledge Management Coordinator]
    end
    
    subgraph "Inventory Building Crew"
        D1[IT Asset Inventory Manager]
        D2[Server Classification Expert]
        D3[Application Discovery Expert]
        D4[Device Classification Expert]
    end
    
    subgraph "Technical Debt Crew"
        G1[Technical Debt Manager]
        G2[Legacy Technology Analyst]
        G3[Modernization Strategy Expert]
        G4[Risk Assessment Specialist]
    end
```

### **Key Architecture Principles**

1. **CrewAI Flow-First**: All workflows use native CrewAI Flow patterns
2. **Crew-Based Organization**: Specialized crews with manager agents
3. **Hierarchical Coordination**: Manager agents coordinate specialist agents
4. **Shared Memory & Knowledge**: Cross-crew intelligence sharing
5. **Phase-Based Execution**: Sequential crew activation with state validation

---

## 🚀 **HYBRID ARCHITECTURE: UnifiedDiscoveryFlow + V2 Discovery Management**

### **Dual-Layer Architecture Design**

The platform implements a **hybrid architecture** combining CrewAI execution with enterprise management:

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Discovery Pages] --> V2API[V2 Discovery API]
        UI --> MONITOR[HTTP2 Flow Monitoring]
    end
    
    subgraph "V2 Management Layer"
        V2API --> V2SERVICE[DiscoveryFlowService]
        V2SERVICE --> PGSQL[(PostgreSQL)]
        V2SERVICE --> BRIDGE[Flow State Bridge]
    end
    
    subgraph "CrewAI Execution Layer"
        BRIDGE --> UNIFIED[UnifiedDiscoveryFlow]
        UNIFIED --> CREWS[CrewAI Crews]
        CREWS --> AGENTS[Agent Execution]
    end
    
    subgraph "Persistence Layer"
        PGSQL --> MULTITENANT[Multi-Tenant Isolation]
        MULTITENANT --> CLIENTDATA[Client Account Data]
    end
```

### **1. UnifiedDiscoveryFlow (CrewAI Execution Engine)**

**Primary Role**: AI agent execution and crew coordination

```python
# UnifiedDiscoveryFlow - CrewAI native execution
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    @start()
    def initialize_discovery_flow(self):
        """CrewAI Flow initialization with agent crews"""
        return {"status": "initialized", "session_id": self.state.session_id}
    
    @listen(initialize_discovery_flow)
    def execute_field_mapping_crew(self, previous_result):
        """Execute field mapping crew with AI agents"""
        crew = FieldMappingCrew(self.crewai_service, self.context)
        result = crew.kickoff()
        return self._process_crew_result("field_mapping", result)
```

**Features**:
- ✅ Native CrewAI Flow with `@start/@listen` decorators
- ✅ Specialized crews with manager agents and hierarchical coordination
- ✅ Agent collaboration within crews using shared memory
- ✅ CrewAI `@persist()` for flow state persistence
- ✅ Purple logs and real-time agent execution

### **2. V2 Discovery Flow (Enterprise Management Layer)**

**Primary Role**: Multi-tenant flow management and PostgreSQL persistence

```python
# V2 Discovery Flow - Enterprise management
class DiscoveryFlowService:
    def __init__(self, db: Session, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id  # Multi-tenant isolation
    
    async def create_discovery_flow(self, flow_id: str, **kwargs):
        """Create PostgreSQL record with multi-tenant scoping"""
        flow_record = DiscoveryFlow(
            flow_id=flow_id,
            client_account_id=self.client_account_id,  # Enterprise isolation
            engagement_id=kwargs.get('engagement_id'),
            current_phase='initialization',
            status='active'
        )
        self.db.add(flow_record)
        await self.db.commit()
        return flow_record
```

**Features**:
- ✅ **Multi-Tenant PostgreSQL Persistence**: Client account isolation
- ✅ **Enterprise Flow Management**: Flow lifecycle, resumption, deletion
- ✅ **HTTP2 Monitoring**: Production-ready for Vercel + Railway
- ✅ **V2 API Endpoints**: `/api/v2/discovery-flows/*` for flow management
- ✅ **Flow State Bridge**: Connects V2 management to UnifiedDiscoveryFlow

### **3. Multi-Tenant PostgreSQL Persistence Strategy**

**Why PostgreSQL Over CrewAI persist()**:
- CrewAI's `@persist()` **does not support multi-tenancy** or data segregation
- Enterprise deployments require **client account isolation**
- Production needs **audit trails** and **compliance tracking**
- **Vercel + Railway** architecture requires centralized state management

```python
# Multi-tenant repository pattern
class ContextAwareRepository:
    def __init__(self, db: Session, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id
    
    async def query_with_context(self, model):
        """Automatic client account scoping"""
        return self.db.query(model).filter(
            model.client_account_id == self.client_account_id
        )
```

**Database Schema**:
```sql
-- V2 Discovery Flow table with multi-tenancy
CREATE TABLE discovery_flows (
    id UUID PRIMARY KEY,
    flow_id VARCHAR(255) UNIQUE,           -- CrewAI Flow ID
    client_account_id INT NOT NULL,        -- Multi-tenant isolation
    engagement_id INT NOT NULL,
    current_phase VARCHAR(50),
    status VARCHAR(20),
    crewai_state_data JSONB,              -- CrewAI flow state bridge
    agent_insights JSONB,                 -- Agent analysis results
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Automatic client scoping index
CREATE INDEX idx_discovery_flows_client_account 
ON discovery_flows(client_account_id, status);
```

### **4. HTTP2 Monitoring for Production (Vercel + Railway)**

**Why HTTP2 Over WebSocket**:
- **Vercel Frontend** + **Railway Backend** deployment architecture
- WebSocket connections have **connection limits** and **timeout issues**
- HTTP2 polling provides **reliable monitoring** with **automatic reconnection**
- Better **scaling** and **load balancing** support

```typescript
// HTTP2 polling for flow monitoring
const useFlowMonitoring = (flowId: string) => {
  const { data: flowState, isLoading } = useQuery({
    queryKey: ['discovery-flow', flowId],
    queryFn: () => apiCall(`/api/v2/discovery-flows/flows/${flowId}/status`),
    refetchInterval: 2000,  // HTTP2 polling every 2 seconds
    refetchIntervalInBackground: true,
    staleTime: 1000
  });
  
  return { flowState, isLoading };
};
```

**Production Monitoring Architecture**:
```mermaid
graph LR
    VERCEL[Vercel Frontend] -->|HTTP2 Polling| RAILWAY[Railway Backend]
    RAILWAY -->|Query| PGSQL[(PostgreSQL)]
    RAILWAY -->|Bridge| CREWAI[CrewAI Flow]
    CREWAI -->|Purple Logs| RAILWAY
    RAILWAY -->|JSON Response| VERCEL
```

### **5. Hybrid Persistence Strategy**

**Dual Persistence Approach**:
1. **CrewAI `@persist()`**: Flow execution state and agent memory
2. **PostgreSQL V2**: Enterprise management and multi-tenant isolation

```python
# Hybrid persistence in UnifiedDiscoveryFlow
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    @persist()  # ✅ CrewAI native persistence for execution state
    async def _process_crew_result(self, phase: str, result: Any):
        # Update CrewAI flow state
        self.state.crew_status[phase] = {"status": "completed", "result": result}
        
        # Bridge to PostgreSQL for enterprise management
        repo = DiscoveryFlowRepository(self.db, self.client_account_id)
        await repo.update_flow_state(
            flow_id=self.state.session_id,
            current_phase=phase,
            crewai_state_data=self.state.dict(),  # Bridge CrewAI state
            agent_insights=result.get('agent_insights', {})
        )
        
        return result
```

### **6. Integration Flow: CMDBImport → UnifiedDiscoveryFlow**

**Complete Integration Path**:
```mermaid
sequenceDiagram
    participant UI as CMDBImport.tsx
    participant API as Backend API
    participant V2 as V2 DiscoveryFlow
    participant UDF as UnifiedDiscoveryFlow
    participant CREW as CrewAI Crews
    participant PG as PostgreSQL
    
    UI->>API: POST /data-import/store-import
    API->>V2: Create V2 flow record
    V2->>PG: Store with client_account_id
    API->>UDF: Initialize UnifiedDiscoveryFlow
    UDF->>CREW: Execute field mapping crew
    CREW->>UDF: Return agent results
    UDF->>V2: Update flow state via bridge
    V2->>PG: Persist agent insights
    API->>UI: Return flow_id for navigation
```

**Key Integration Points**:
- ✅ **Data Import**: Triggers both V2 record creation AND UnifiedDiscoveryFlow
- ✅ **Navigation**: Uses CrewAI `flow_id` for phase-specific routing
- ✅ **State Sync**: Flow State Bridge keeps V2 and CrewAI in sync
- ✅ **Monitoring**: HTTP2 polling queries V2 API for real-time updates

---

## 🧠 **CrewAI Implementation Patterns**

### **1. Flow Definition Pattern**
```python
from crewai import Flow
from crewai.flow.flow import listen, start

class DiscoveryFlow(Flow[DiscoveryFlowState]):
    @start()
    def initialize_discovery_flow(self):
        """Initialize flow with comprehensive planning"""
        return {"status": "initialized", "session_id": self.state.session_id}
    
    @listen(initialize_discovery_flow)
    def execute_field_mapping_crew(self, previous_result):
        """Execute field mapping crew with manager coordination"""
        crew = FieldMappingCrew(self.crewai_service, self.context)
        result = crew.kickoff()
        return self._process_crew_result("field_mapping", result)
    
    @listen(execute_field_mapping_crew)
    def execute_data_cleansing_crew(self, previous_result):
        """Execute data cleansing crew using field mapping insights"""
        crew = DataCleansingCrew(self.crewai_service, self.context)
        result = crew.kickoff()
        return self._process_crew_result("data_cleansing", result)
```

### **2. Crew Definition Pattern**
```python
from crewai import Agent, Task, Crew, Process

class FieldMappingCrew:
    def __init__(self, crewai_service, context):
        self.llm = crewai_service.llm
        self.context = context
        
    def create_crew(self):
        # Manager Agent with delegation authority
        manager = Agent(
            role="CMDB Field Mapping Coordination Manager",
            goal="Coordinate comprehensive CMDB field mapping analysis",
            backstory="Senior data architect with 15+ years in enterprise migrations",
            llm=self.llm,
            allow_delegation=True,
            max_delegation=3,
            collaboration=True,
            verbose=True
        )
        
        # Specialist Agents with specific domains
        schema_expert = Agent(
            role="CMDB Schema Structure Analysis Expert",
            goal="Analyze data structure semantics and field relationships",
            backstory="Expert in CMDB schema analysis with deep technical knowledge",
            llm=self.llm,
            collaboration=True,
            tools=self._create_schema_analysis_tools()
        )
        
        return Crew(
            agents=[manager, schema_expert, mapping_specialist],
            tasks=self._create_tasks(),
            process=Process.hierarchical,
            manager_llm=self.llm,
            verbose=True
        )
```

### **3. State Management Pattern**
```python
from pydantic import BaseModel
from typing import Dict, List, Any

class DiscoveryFlowState(BaseModel):
    # Flow identification
    session_id: str = ""
    client_account_id: str = ""
    engagement_id: str = ""
    user_id: str = ""
    
    # Current execution state
    current_phase: str = "initialization"
    crew_status: Dict[str, Dict[str, Any]] = {}
    
    # Results from each crew
    field_mappings: Dict[str, Any] = {}
    cleaned_data: List[Dict[str, Any]] = []
    asset_inventory: Dict[str, List[Dict[str, Any]]] = {}
    app_server_dependencies: Dict[str, Any] = {}
    app_app_dependencies: Dict[str, Any] = {}
    technical_debt_assessment: Dict[str, Any] = {}
    
    # Final integration results
    discovery_summary: Dict[str, Any] = {}
```

---

## 📁 **Current File Structure (What to Use)**

### **✅ ACTIVE: Unified CrewAI Flow Implementation (CONSOLIDATED)**
```
backend/app/services/crewai_flows/
├── unified_discovery_flow.py          # ✅ MAIN: Unified CrewAI Flow (732 lines)
├── crews/                             # ✅ Specialized crew implementations
│   ├── field_mapping_crew.py         # ✅ Field mapping with manager coordination
│   ├── data_cleansing_crew.py         # ✅ Data quality and standardization
│   ├── inventory_building_crew.py     # ✅ Multi-domain asset classification
│   ├── app_server_dependency_crew.py  # ✅ Hosting relationship analysis
│   ├── app_app_dependency_crew.py     # ✅ Application integration mapping
│   └── technical_debt_crew.py         # ✅ Technical debt and 6R preparation
├── tools/                             # ✅ Specialized agent tools
│   ├── schema_analysis_tool.py
│   ├── mapping_confidence_tool.py
│   ├── asset_classification_tool.py
│   └── dependency_analysis_tool.py
└── knowledge_bases/                   # ✅ Domain-specific knowledge
    ├── field_mapping_patterns.json
    ├── asset_classification_rules.json
    └── modernization_strategies.yaml

backend/app/models/
├── unified_discovery_flow_state.py    # ✅ MAIN: Unified state model (477 lines)
└── workflow_state.py                  # ✅ Enhanced database model (238 lines)

backend/app/api/v1/
└── unified_discovery.py               # ✅ MAIN: Unified API endpoints (162 lines)

src/hooks/
└── useUnifiedDiscoveryFlow.ts         # ✅ MAIN: Single frontend hook (302 lines)
```

### **❌ DEPRECATED: Legacy Individual Agents & Competing Implementations**
```
backend/app/services/discovery_agents/      # ❌ DO NOT USE - Individual agents
backend/app/services/sixr_agents_handlers/  # ❌ DO NOT USE - Old agent handlers
backend/app/services/analysis_handlers/     # ❌ DO NOT USE - Heuristic handlers

# REMOVED: Competing implementations (2025-01-21 consolidation)
backend/app/api/v1/discovery/discovery_flow.py     # ❌ REMOVED - 2,206 lines
backend/app/services/crewai_flows/models/flow_state.py  # ❌ REMOVED - 442 lines
backend/app/schemas/flow_schemas.py             # ❌ REMOVED - 63 lines
backend/app/schemas/flow_schemas_new.py         # ❌ REMOVED - 63 lines

# LEGACY: Old discovery flow files (superseded by unified flow)
backend/app/services/crewai_flows/discovery_flow_modular.py  # ❌ SUPERSEDED
backend/app/services/crewai_flows/discovery_flow_state_manager.py  # ❌ SUPERSEDED
```

---

## 🛠️ **Development Guidelines**

### **✅ DO: Current Best Practices**

#### **1. Use Unified CrewAI Flow Patterns**
```python
# ✅ Correct: Unified CrewAI Flow with proper decorators
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow

class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    @start()
    def initialize_discovery_flow(self):
        return {"status": "initialized", "session_id": self.state.session_id}

    @listen(initialize_discovery_flow)
    def execute_field_mapping_crew(self, previous_result):
        crew = FieldMappingCrew(self.crewai_service, self.context)
        result = crew.kickoff()
        return self._process_crew_result("field_mapping", result)
```

#### **2. Implement Crew-Based Architecture**
```python
# ✅ Correct: Crew with manager and specialists
class FieldMappingCrew:
    def create_crew(self):
        manager = Agent(role="Manager", allow_delegation=True, max_delegation=3)
        specialist1 = Agent(role="Schema Expert", collaboration=True)
        specialist2 = Agent(role="Mapping Specialist", collaboration=True)
        
        return Crew(
            agents=[manager, specialist1, specialist2],
            process=Process.hierarchical,
            manager_llm=self.llm
        )
```

#### **3. Use Unified State Management**
```python
# ✅ Correct: Unified flow state with persistence
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.models.workflow_state import UnifiedFlowStateRepository

async def _process_crew_result(self, phase: str, result: Any):
    # Update unified flow state
    self.state.crew_status[phase] = {"status": "completed", "result": result}
    self.state.phase_completion[phase] = True
    self.state.progress_percentage = self._calculate_progress()
    
    # Persist to enhanced database model
    repo = UnifiedFlowStateRepository(self.db, self.state.client_account_id)
    await repo.update_workflow_state(self.state.session_id, self.state)
    
    return result
```

### **❌ DON'T: Legacy Patterns to Avoid**

#### **1. Individual Agent Orchestration**
```python
# ❌ Wrong: Direct individual agent calls
agent1 = CMDBAnalystAgent()
result1 = agent1.analyze(data)
agent2 = FieldMappingAgent()
result2 = agent2.map_fields(result1)
```

#### **2. Hard-Coded Heuristics**
```python
# ❌ Wrong: Static rules and heuristics
if field_name.lower() in ['hostname', 'server_name']:
    mapping = 'asset_name'
elif field_name.lower() in ['env', 'environment']:
    mapping = 'environment'
```

#### **3. Simple Service Classes**
```python
# ❌ Wrong: Basic service without CrewAI
class DiscoveryService:
    def analyze_data(self, data):
        # Simple processing without agents
        return processed_data
```

### **❌ CRITICAL: Frontend Independent Agents (ARCHITECTURAL VIOLATION)**

**NEVER implement independent agents in frontend components** - this violates the core UnifiedDiscoveryFlow architecture:

```typescript
// ❌ WRONG: Independent validation agents in frontend (REMOVED 2025-01-27)
const createValidationAgents = (category: string): DataImportAgent[] => {
  return [
    {
      id: 'format_validator',
      name: 'Format Validation Agent',        // ❌ COMPETING with UnifiedDiscoveryFlow
      role: 'Validates file format, structure, and encoding',
    },
    {
      id: 'data_quality_assessor',
      name: 'Data Quality Agent',             // ❌ COMPETING with UnifiedDiscoveryFlow
      role: 'Assesses data completeness, accuracy, consistency',
    }
  ];
};

// ❌ WRONG: Fake agent simulation in frontend
const simulateAgentExecution = async (agents: DataImportAgent[]) => {
  for (const agent of agents) {
    // ❌ FAKE PROGRESS - not real agent execution
    setProgress(agents.indexOf(agent) + 1);
    await new Promise(resolve => setTimeout(resolve, 1500)); // ❌ FAKE DELAY
  }
};
```

**Why This Violates Architecture**:
- **Competing Intelligence**: Frontend agents compete with UnifiedDiscoveryFlow crews
- **Fake Processing**: Simulated delays and results instead of real AI analysis
- **State Confusion**: Frontend shows "agent results" that aren't from actual CrewAI agents
- **Error Handling Mismatch**: Frontend success/failure doesn't match actual flow state

**✅ CORRECT: Direct UnifiedDiscoveryFlow Integration**:
```typescript
// ✅ Correct: Direct flow integration without competing agents
const handleFileUpload = async (files: File[], categoryId: string) => {
  const csvData = await parseCsvData(files[0]);
  
  // Store data and trigger UnifiedDiscoveryFlow directly
  const { flow_id } = await storeImportData(csvData, files[0], sessionId, categoryId);
  
  if (flow_id) {
    // Success - UnifiedDiscoveryFlow was triggered
    navigate(`/discovery/attribute-mapping/${flow_id}`);
  }
};
```

**Key Principles**:
- ✅ **No Frontend Agents**: All intelligence comes from UnifiedDiscoveryFlow
- ✅ **Real Agent Results**: Display actual CrewAI agent insights from flow state
- ✅ **Unified Error Handling**: Frontend status matches actual flow execution
- ✅ **Direct Integration**: File upload → store data → trigger flow → navigate

---

## 🔧 **API Integration Patterns**

### **✅ Current Unified API Endpoints**
```python
# Unified Discovery Flow API (ACTIVE) - backend/app/api/v1/unified_discovery.py
@router.post("/api/v1/unified-discovery/flow/initialize")
async def initialize_discovery_flow(request: InitializeFlowRequest):
    """Initialize a new unified discovery flow"""
    flow = create_unified_discovery_flow(
        session_id=session_id,
        client_account_id=request.client_account_id,
        engagement_id=request.engagement_id,
        user_id=request.user_id,
        raw_data=request.raw_data,
        crewai_service=crewai_service,
        context=context
    )
    return await flow.kickoff()

@router.get("/api/v1/unified-discovery/flow/status/{session_id}")
async def get_flow_status(session_id: str):
    """Get current unified flow execution status"""
    # Returns unified flow state with phase completion, crew status, progress
    
@router.post("/api/v1/unified-discovery/flow/execute/{phase}")
async def execute_flow_phase(phase: str, request: Dict[str, Any]):
    """Execute a specific phase of the discovery flow"""
    
@router.get("/api/v1/unified-discovery/flow/health")
async def get_flow_health():
    """Get health status of the unified discovery flow system"""
```

### **❌ Legacy Endpoints to Avoid**
```python
# ❌ DO NOT USE: Individual agent endpoints
@router.post("/api/v1/discovery/agents/cmdb-analyst")  # DEPRECATED
@router.post("/api/v1/discovery/agents/field-mapper")  # DEPRECATED

# ❌ REMOVED: Competing discovery flow endpoints (2025-01-21)
@router.post("/api/v1/discovery/flow/run")              # REMOVED
@router.get("/api/v1/discovery/flow/status/{flow_id}")  # REMOVED
@router.get("/api/v1/discovery/flow/active")            # REMOVED
# ... and 44 other endpoints from discovery_flow.py     # REMOVED

# ❌ DO NOT CREATE: New competing endpoints
# Always use the unified discovery endpoints instead
```

---

## 🧪 **Testing Patterns**

### **✅ Current Unified Testing Approach**
```python
# Test Unified CrewAI Flow execution
async def test_unified_discovery_flow_execution():
    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
    
    flow = UnifiedDiscoveryFlow(mock_crewai_service, test_context)
    result = await flow.kickoff()
    
    assert result["status"] == "completed"
    assert flow.state.phase_completion["field_mapping"] == True
    assert flow.state.phase_completion["asset_inventory"] == True
    assert flow.state.progress_percentage == 100.0

# Test crew coordination with unified state
async def test_field_mapping_crew_unified():
    crew = FieldMappingCrew(mock_service, test_context)
    result = crew.kickoff()
    
    assert result["confidence_score"] > 0.8
    assert len(result["unmapped_fields"]) < 5
    assert result["crew_coordination"]["manager_delegations"] > 0

# Test unified frontend hook
def test_useUnifiedDiscoveryFlow():
    from src.hooks.useUnifiedDiscoveryFlow import useUnifiedDiscoveryFlow
    # Test hook integration with unified API endpoints
```

---

## 📊 **Frontend Integration**

### **✅ Current Unified Frontend Patterns**
```typescript
// Use Unified Discovery Flow hook (SINGLE SOURCE OF TRUTH)
import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';

const {
  flowState,
  isLoading,
  error,
  isHealthy,
  initializeFlow,
  executeFlowPhase,
  getPhaseData,
  isPhaseComplete,
  canProceedToPhase,
  refreshFlow
} = useUnifiedDiscoveryFlow();

// Monitor unified flow progress
const UnifiedFlowStatusCard = () => {
  return (
    <Card className="border-l-4 border-l-blue-500">
      <CardHeader>
        <CardTitle>Current Unified Discovery Flow</CardTitle>
        <CardDescription>Session: {flowState.session_id}</CardDescription>
      </CardHeader>
      <CardContent>
        <Progress value={flowState.progress_percentage} />
        <p>Phase: {flowState.current_phase}</p>
        <p>Completed: {Object.values(flowState.phase_completion).filter(Boolean).length}/6</p>
      </CardContent>
    </Card>
  );
};

// All discovery pages use the same unified hook
const AssetInventoryPage = () => {
  const { flowState, executeFlowPhase, getPhaseData } = useUnifiedDiscoveryFlow();
  const inventoryData = getPhaseData('asset_inventory');
  // ...
};
```

### **❌ Legacy Frontend Patterns to Avoid**
```typescript
// ❌ DO NOT USE: Individual agent monitoring
const AgentCard = ({ agentName }) => { /* DEPRECATED */ };

// ❌ DO NOT USE: Heuristic-based displays
const HeuristicResults = ({ rules }) => { /* DEPRECATED */ };

// ❌ REMOVED: Competing discovery hooks (2025-01-21)
import { useDiscoveryFlowState } from '...';     // REMOVED
import { useDataCleansingLogic } from '...';     // REMOVED
import { DiscoveryFlowContext } from '...';      // REMOVED

// ❌ DO NOT CREATE: Multiple discovery state hooks
// Always use useUnifiedDiscoveryFlow for ALL discovery pages
```

---

## 🎯 **Key Success Metrics**

### **Current Architecture Achievements**
- ✅ **CrewAI Flow Integration**: 100% native implementation
- ✅ **Unified Flow Consolidation**: Single source of truth achieved (2025-01-21)
- ✅ **Code Sprawl Elimination**: ~2,774 lines of competing code removed
- ✅ **Crew Coordination**: Manager agents with delegation control
- ✅ **Agent Collaboration**: Cross-crew knowledge sharing
- ✅ **State Management**: Unified flow state with enhanced persistence
- ✅ **Enterprise Features**: Multi-tenancy, learning, knowledge management
- ✅ **Frontend Unification**: All 7 discovery pages use single unified hook

### **Performance Targets**
- **Field Mapping Accuracy**: 95%+ with confidence scoring
- **Processing Speed**: 1-2 seconds for CMDB data analysis
- **Crew Coordination**: < 5 seconds for manager delegation
- **Memory Efficiency**: Agent-level memory with shared knowledge

---

## 🚨 **CRITICAL REMINDERS**

1. **NEVER use individual agent patterns** - Always use CrewAI Crews
2. **NEVER implement hard-coded heuristics** - Use agent intelligence
3. **NEVER create competing implementations** - Use unified discovery flow only
4. **ALWAYS use unified discovery endpoints** - `/api/v1/unified-discovery/flow/*`
5. **ALWAYS use useUnifiedDiscoveryFlow hook** - Single frontend hook for all pages
6. **ALWAYS use CrewAI Flow decorators** - @start/@listen for proper sequencing
7. **ALWAYS implement manager agents** - Hierarchical coordination required
8. **ALWAYS use shared memory and knowledge** - Cross-crew intelligence sharing
9. **ALWAYS persist unified flow state** - Enhanced database model with multi-tenancy
10. **ALWAYS test crew coordination** - Verify manager delegation and agent collaboration

---

## 📋 **Quick Reference Commands**

### **Start Development**
```bash
# Always use Docker containers
docker-compose up -d --build

# Access backend for debugging unified flow
docker exec -it migration_backend python -c "
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
print('Unified CrewAI Flow implementation active')
print('Single source of truth architecture confirmed')
"
```

### **Test Unified Architecture**
```bash
# Test Unified CrewAI Flow
docker exec -it migration_backend python -m pytest tests/backend/flows/test_unified_discovery_flow.py

# Test crew coordination
docker exec -it migration_backend python -m pytest tests/crews/test_field_mapping_crew.py

# Test unified frontend hook
npm test -- useUnifiedDiscoveryFlow
```

### **Verify Unified Implementation**
```bash
# Check for legacy patterns (should return empty)
docker exec -it migration_backend find . -name "*individual_agent*" -o -name "*heuristic*"

# Verify competing implementations removed (should return empty)
docker exec -it migration_backend find . -name "*discovery_flow.py" -path "*/api/v1/discovery/*"

# Verify unified CrewAI Flow files exist
docker exec -it migration_backend ls -la app/services/crewai_flows/unified_discovery_flow.py
docker exec -it migration_backend ls -la app/models/unified_discovery_flow_state.py
docker exec -it migration_backend ls -la app/api/v1/unified_discovery.py
```

---

## 🎪 **Final Architecture State**

**The AI Force Migration Platform is now a mature, UNIFIED CrewAI Flow-based system with:**

- **Single Unified Discovery Flow** - All code sprawl eliminated (2025-01-21)
- **Native CrewAI Flows** for workflow orchestration
- **Specialized Crews** with manager coordination
- **Agent Collaboration** within and across crews
- **Shared Memory & Knowledge** for intelligence continuity
- **Enterprise Multi-Tenancy** with proper isolation
- **Learning Capabilities** that improve over time
- **Unified State Management** with enhanced database persistence
- **Single Frontend Hook** for all discovery pages
- **Consolidated API Endpoints** with no competing implementations

## 🌟 **CONSOLIDATION ACHIEVEMENT (2025-01-21)**

**✅ COMPLETED: Unified Discovery Flow Consolidation Plan**
- **Eliminated**: ~2,774 lines of competing/duplicate code
- **Unified**: Single source of truth for all discovery operations
- **Connected**: All 7 discovery pages to unified flow
- **Simplified**: Architecture following CrewAI best practices
- **Enhanced**: Real-time flow state across all pages

**Any coding agent working on this platform MUST use the UNIFIED CrewAI Flow-based architecture and avoid all legacy patterns from previous pivots and competing implementations.**