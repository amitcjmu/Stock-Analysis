# AI Modernize Migration Platform - Coding Agent Quick Reference

> **🚨 IMPORTANT**: This platform is in a critical transition phase. A new `MasterFlowOrchestrator` has been implemented as the single source of truth for all workflows, but the frontend and some backend services still use a mix of legacy APIs. This creates a "competing controller" problem and is the source of known bugs.

> **📍 Current State**: **Hybrid Architecture**. The new `MasterFlowOrchestrator` is the target, but legacy `DiscoveryFlowService` and siloed APIs are still active and being called by the UI, causing state conflicts.

## 🚨 **CRITICAL RULES - READ FIRST**

### **Architecture: Master Flow Orchestrator (MFO) is KING**
- ✅ **USE**: `MasterFlowOrchestrator` via the unified `/api/v1/flows` endpoint for all flow operations.
- ✅ **USE**: The `UnifiedDiscoveryFlow` is the underlying CrewAI implementation, but it should ONLY be driven by the MFO.
- ❌ **NEVER**: Call legacy discovery endpoints (`/api/v1/discovery/...`). This bypasses the MFO and corrupts flow state.
- ❌ **NEVER**: Use individual agents or hard-coded rules.

### **Database: Async PostgreSQL with Multi-Tenancy**
- ✅ **USE**: `AsyncSessionLocal()` for all database operations.
- ✅ **USE**: `ContextAwareRepository` with `client_account_id` scoping.
- ❌ **NEVER**: Sync sessions in async context.

### **Development: Docker-First**
- ✅ **USE**: `docker-compose up -d --build` for all development.
- ✅ **USE**: `docker exec -it migration_backend python -c "code"`
- ❌ **NEVER**: Run services locally (Next.js, Python, PostgreSQL).

---

## 🏗️ **CURRENT ARCHITECTURE (Hybrid & In Transition)**

### **The Competing Controller Problem**

The platform currently suffers from a "split-brain" problem. The diagram below shows the **correct** (target) architecture and the **incorrect** (legacy) architecture running in parallel.

#### **✅ TARGET Architecture (Correct)**
```
Frontend (Vercel) → Unified API (/api/v1/flows) → MasterFlowOrchestrator
                                                          ↓
                                             CrewAIFlowService → UnifiedDiscoveryFlow
                                                          ↓
                                        PostgreSQL (managed by MFO)
```

#### **❌ LEGACY Architecture (Incorrect & Active)**
```
Frontend (Vercel) → Siloed APIs (/api/v1/discovery/...) → DiscoveryFlowService
                                                                 ↓
                                                    PostgreSQL (direct access, state conflicts)
```

⚠️ **Current Issues Being Fixed**:
- **The UI primarily calls legacy APIs**, bypassing the MFO.
- State is managed by two different controllers, causing data corruption and navigation loops.
- `session_id` logic from legacy systems conflicts with the new `flow_id` standard.
- The field mapping UI shows "0 active flows" because it queries a legacy endpoint that doesn't understand MFO-managed flows.

**Key Components**:
- **MasterFlowOrchestrator**: The **single source of truth** for all flow management. It is the intended controller.
- **UnifiedDiscoveryFlow**: The modern, underlying CrewAI implementation of the discovery process.
- **`DiscoveryFlowService` (Legacy)**: The old controller that directly manages flows and is still being called by the UI.
- **Unified API (`/api/v1/flows`)**: The correct, MFO-driven API.
- **Siloed APIs (`/api/v1/discovery/...`)**: The incorrect, legacy APIs that must be phased out.

## 📚 **Essential Documentation**

### **Platform Architecture (Required Reading)**
- `docs/architecture/DISCOVERY_FLOW_COMPLETE_ARCHITECTURE.md` - **MUST READ** - Describes the target MFO-based architecture.
- `docs/planning/master_flow_orchestrator/DESIGN_DOCUMENT.md` - The design and intent of the central orchestrator.

### **Development & Migration Guides**
- `docs/development/CrewAI_Development_Guide.md` - CrewAI implementation patterns.
- `docs/api/v3-migration-guide.md` - API transition guidance (part of the ongoing cleanup).
- `docs/troubleshooting/discovery-flow-sync-issues.md` - Critical issue resolution stemming from the competing controller problem.

### **Data Flow: CMDBImport → UnifiedDiscoveryFlow (The Conflict)**
The frontend *should* use the MFO, but often uses the legacy path:
- **Legacy Path**: `CMDBImport.tsx` → `/api/v1/discovery/...` → `DiscoveryFlowService` (Bypasses MFO)
- **Correct Path**: `CMDBImport.tsx` → `/api/v1/flows` → `MasterFlowOrchestrator` → `CrewAIFlowService` → `UnifiedDiscoveryFlow.kickoff()`

---

## 🛠️ **DEVELOPMENT PATTERNS**

### **✅ DO: Use the Master Flow Orchestrator**
```python
# Correct: Use the MFO for all flow operations
class YourService:
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.orchestrator = MasterFlowOrchestrator(db, context)

    async def start_new_discovery(self, name: str):
        flow_id, _ = await self.orchestrator.create_flow(
            flow_type="discovery",
            flow_name=name
        )
        return flow_id
```

```typescript
// Correct: Use the '/api/v1/flows' endpoint in the frontend
import { flowApi } from 'src/api/flowApi'; // Hypothetical unified API client

const createFlow = async () => {
  const response = await flowApi.create({ flow_type: 'discovery' });
  const { flow_id } = response.data;
  navigate(`/discovery/flows/${flow_id}`); // Navigate to unified flow page
};
```

### **❌ DON'T: Use Legacy Services or APIs**
```python
# Wrong: Do not instantiate or use legacy services directly
from app.services.discovery_flow_service import DiscoveryFlowService # AVOID THIS

# This service bypasses the MFO and leads to state corruption
service = DiscoveryFlowService(db, session_id) 
service.advance_phase() # CAUSES BUGS
```

```typescript
// Wrong: Do not call discovery-specific APIs
// This hits the legacy DiscoveryFlowService and bypasses the MFO
const response = await api.post(`/api/v1/discovery/flow/${flowId}/resume`);
```

---

## 📁 **FILE STRUCTURE**

### **✅ ACTIVE & STRATEGIC FILES**
```
backend/app/services/
├── master_flow_orchestrator.py      # MAIN: The one and only orchestrator.
└── crewai_flow_service.py           # Service layer called by MFO.

backend/app/services/crewai_flows/
└── unified_discovery_flow.py        # The underlying CrewAI flow logic.

backend/app/api/v1/
└── flows.py                         # MAIN: The unified API for the MFO.

src/hooks/
└── useUnifiedDiscoveryFlow.ts       # A rare example of a hook using the correct, new API.
```

### **❌ DEPRECATED & DANGEROUS**
- `backend/app/services/discovery_flow_service.py` (Legacy controller)
- `backend/app/api/v1/endpoints/discovery_flows.py` (Legacy API implementation)
- Most hooks in `src/hooks/discovery/` (They call legacy endpoints)
- Most components in `src/pages/discovery/` (They use the legacy hooks)

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