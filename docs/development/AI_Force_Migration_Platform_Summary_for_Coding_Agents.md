# AI Force Migration Platform - Coding Agent Quick Reference

## 🚨 **CRITICAL RULES - READ FIRST**

### **Architecture: CrewAI Flow-Based (NOT Individual Agents)**
- ✅ **USE**: `UnifiedDiscoveryFlow` with `@start/@listen` decorators
- ✅ **USE**: Specialized crews with manager agents
- ❌ **NEVER**: Individual agents, hard-coded rules, or frontend agent simulation

### **Database: Async PostgreSQL with Multi-Tenancy**
- ✅ **USE**: `AsyncSessionLocal()` for all database operations
- ✅ **USE**: `ContextAwareRepository` with `client_account_id` scoping
- ❌ **NEVER**: Sync sessions in async context

### **Development: Docker-First**
- ✅ **USE**: `docker-compose up -d --build` for all development
- ✅ **USE**: `docker exec -it migration_backend python -c "code"`
- ❌ **NEVER**: Run services locally (Next.js, Python, PostgreSQL)

---

## 🏗️ **CURRENT ARCHITECTURE**

### **Hybrid Architecture: UnifiedDiscoveryFlow + V2 Management**
```
Frontend (Vercel) → V2 API → DiscoveryFlowService → PostgreSQL
                           ↓
                    UnifiedDiscoveryFlow → CrewAI Crews → Agents
```

**Key Components**:
- **UnifiedDiscoveryFlow**: CrewAI execution engine (`@persist()` + crews)
- **V2 DiscoveryFlow**: Enterprise management (PostgreSQL + multi-tenancy)
- **Flow State Bridge**: Connects CrewAI execution to enterprise management

### **Data Flow: CMDBImport → UnifiedDiscoveryFlow**
```
CMDBImport.tsx → storeImportData() → /api/v1/data-import/store-import 
→ _trigger_discovery_flow() → UnifiedDiscoveryFlow.kickoff() → CrewAI Crews
```

---

## 🛠️ **DEVELOPMENT PATTERNS**

### **✅ DO: CrewAI Flow Patterns**
```python
# Correct: CrewAI Flow with crews
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    @start()
    def initialize_discovery_flow(self):
        return {"status": "initialized"}
    
    @listen(initialize_discovery_flow)
    def execute_field_mapping_crew(self, previous_result):
        crew = FieldMappingCrew(self.crewai_service, self.context)
        return crew.kickoff()
```

```python
# Correct: Multi-tenant repository
class YourRepository(ContextAwareRepository):
    def __init__(self, db: Session, client_account_id: int):
        super().__init__(db, client_account_id)
    
    async def get_data(self):
        return await self.query_with_context(YourModel)
```

```typescript
// Correct: Direct flow integration
const handleFileUpload = async (files: File[]) => {
  const csvData = await parseCsvData(files[0]);
  const { flow_id } = await storeImportData(csvData, files[0], sessionId);
  if (flow_id) {
    navigate(`/discovery/attribute-mapping/${flow_id}`);
  }
};
```

### **❌ DON'T: Anti-Patterns**
```python
# Wrong: Individual agents
agent1 = CMDBAnalystAgent()
result1 = agent1.analyze(data)

# Wrong: Hard-coded rules
if field_name.lower() in ['hostname']:
    mapping = 'asset_name'

# Wrong: Sync sessions in async
def wrong_pattern():
    session = SessionLocal()  # Fails in async context!
```

```typescript
// Wrong: Independent frontend agents
const createValidationAgents = () => [
  { name: 'Format Validator' },  // Competes with UnifiedDiscoveryFlow
  { name: 'Data Quality Agent' }
];

// Wrong: Fake agent simulation
await new Promise(resolve => setTimeout(resolve, 1500)); // Fake delay
```

---

## 📁 **FILE STRUCTURE**

### **✅ ACTIVE FILES**
```
backend/app/services/crewai_flows/
├── unified_discovery_flow.py          # MAIN: CrewAI Flow execution
├── crews/                             # Specialized crews
│   ├── field_mapping_crew.py
│   ├── data_cleansing_crew.py
│   └── inventory_building_crew.py
└── tools/                             # Agent tools

backend/app/models/
├── unified_discovery_flow_state.py    # MAIN: Flow state model
└── workflow_state.py                  # V2 database model

backend/app/api/
├── v1/unified_discovery.py            # MAIN: Unified API
└── v2/discovery_flow_v2.py            # V2 management API

src/hooks/
└── useUnifiedDiscoveryFlow.ts         # MAIN: Single frontend hook
```

### **❌ DEPRECATED/REMOVED**
- `backend/app/services/discovery_agents/` (individual agents)
- `backend/app/api/v1/discovery/discovery_flow.py` (competing implementation)
- Frontend agent simulation components

---

## 🔧 **CRITICAL TECHNICAL PATTERNS**

### **Database Sessions (CRITICAL)**
```python
# ✅ Correct: Async sessions
async def get_data():
    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        return result

# ❌ Wrong: Sync in async context
def wrong():
    session = SessionLocal()  # Will fail!
```

### **JSON Serialization (CRITICAL)**
```python
# ✅ Handle NaN/Infinity values
def safe_json_serialize(data):
    def convert_numeric(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj
    return json.dumps(data, default=convert_numeric)
```

### **CORS for Production (CRITICAL)**
```python
# ✅ Explicit domain lists (no wildcards)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-app.vercel.app"  # Specific domain
]

# ❌ Wrong: Wildcards don't work
WRONG_CORS = ["https://*.vercel.app"]  # FastAPI doesn't support
```

### **Import Safety (CRITICAL)**
```python
# ✅ Conditional imports with fallbacks
try:
    from app.models.client_account import ClientAccount
    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError:
    CLIENT_ACCOUNT_AVAILABLE = False

if CLIENT_ACCOUNT_AVAILABLE:
    # Full functionality
else:
    # Fallback functionality
```

---

## 🚀 **DEPLOYMENT**

### **Environment Configuration**
```bash
# Railway Backend
DATABASE_URL=postgresql://...
DEEPINFRA_API_KEY=your_key
CREWAI_ENABLED=true
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app

# Vercel Frontend
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app/api/v1
```

### **Docker Development Commands**
```bash
# Start development
docker-compose up -d --build

# Backend debugging
docker exec -it migration_backend python -c "test_code"
docker exec -it migration_backend python -m pytest tests/

# Database access
docker exec -it migration_db psql -U user -d migration_db
```

---

## 🎯 **API ENDPOINTS**

### **✅ CURRENT: Unified Discovery**
- `POST /api/v1/unified-discovery/flow/initialize`
- `GET /api/v1/unified-discovery/flow/status/{session_id}`
- `POST /api/v1/unified-discovery/flow/execute/{phase}`

### **✅ CURRENT: V2 Flow Management**
- `GET /api/v2/discovery-flows/flows/active`
- `POST /api/v2/discovery-flows/flows/{flow_id}/continue`
- `DELETE /api/v2/discovery-flows/flows/{flow_id}`

### **❌ DEPRECATED**
- `/api/v1/discovery/agents/*` (individual agents)
- `/api/v1/discovery/flow/*` (competing implementation)

---

## 📋 **MANDATORY WORKFLOW**

### **After Task Completion**
1. **Update CHANGELOG.md** with new version entry
2. **Git commit** with descriptive message using emoji prefixes:
   ```bash
   git commit -m "🎯 [Category]: [Brief description]
   
   ✨ [Change type]:
   - [Change 1]
   - [Change 2]"
   ```
3. **Git push** to main branch

### **Code Review Checklist**
- [ ] No hard-coded heuristics or static rules
- [ ] All intelligence comes from CrewAI agents
- [ ] Docker containers used for testing
- [ ] Multi-tenant data scoping implemented
- [ ] Async sessions used (`AsyncSessionLocal`)
- [ ] JSON serialization safety
- [ ] CHANGELOG.md updated
- [ ] Git commit and push completed

---

## 🌟 **REMEMBER**

**This is an AGENTIC platform where all intelligence comes from CrewAI agents that learn and adapt. Never implement static rules or competing agent systems. Always develop in Docker containers with proper multi-tenant isolation.**

**Key Files**: `unified_discovery_flow.py`, `useUnifiedDiscoveryFlow.ts`, `unified_discovery.py`

**Architecture**: UnifiedDiscoveryFlow (CrewAI) + V2 DiscoveryFlow (Enterprise) = Hybrid System