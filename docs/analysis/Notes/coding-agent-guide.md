# AI Coding Agent Quick Reference Guide

## 🚨 START HERE - MANDATORY READING ORDER 🚨

**Before ANY code change, you MUST read in this order:**
1. ✅ [000-lessons.md](./000-lessons.md) - Core lessons & rationale
2. ✅ **This guide** - Quick reference & implementation patterns
3. ✅ [Architecture Summary](../../adr/) - Design decisions

**This guide is ENFORCED by:**
- CI/CD checks that scan for banned patterns
- PR template requiring compliance checkboxes
- Pre-commit hooks blocking violations

## ⛔ BANNED PATTERNS - CI WILL REJECT THESE

```bash
# These patterns trigger automatic PR rejection:
❌ WebSocket | new WebSocket | ws://  # Use HTTP polling ONLY
❌ asyncio.run() in async context      # Causes event loop errors
❌ .is True in SQLAlchemy             # Use == True
❌ /api/v1/discovery/* direct calls   # Use MFO only
❌ Mock analysis data in APIs         # Return structured errors
❌ camelCase in new API types         # snake_case ONLY
❌ Crew() instantiation per call      # Use TenantScopedAgentPool
```

## 📋 DEFINITION OF DONE CHECKLISTS

### Backend API Change DoD
```markdown
- [ ] Tenant scoping on ALL queries (client_account_id + engagement_id)
- [ ] Atomic transaction used (async with db.begin(); await db.flush())
- [ ] No sync/async mixing in same flow
- [ ] Serializer aligns with model (unit test added)
- [ ] No mock agent data returned
- [ ] Structured error format: {status: 'failed', error_code: 'XXX', details: {}}
```

### Agent Change DoD
```markdown
- [ ] Uses TenantScopedAgentPool (NO per-call Crew instantiation)
- [ ] Telemetry events published to Redis
- [ ] Structured failure codes returned
- [ ] No hardcoded thresholds (agent decides)
```

### Frontend Change DoD
```markdown
- [ ] HTTP polling ONLY (5s active/15s waiting) - NO WebSockets
- [ ] Multi-tenant headers on all API calls
- [ ] snake_case fields preserved end-to-end
- [ ] No camelCase in new interfaces
- [ ] Defensive field access (data.flow_id || data.flowId)
```

## 🚨 CRITICAL: Top Bug Sources & Prevention

### 1. Field Naming Convention (#1 BUG SOURCE)
```python
# Backend: ALWAYS snake_case
flow_id, client_account_id, master_flow_id  ✓

# Frontend: Match backend exactly - NO TRANSFORMATION
interface FlowData {
  flow_id: string;        ✓ (snake_case)
  master_flow_id: string; ✓ (snake_case)
  flowId: string;         ✗ (NEVER use camelCase)
}
```

### 2. Verify Before Assuming (PREVENTS 404s)
```bash
# Component exists? Check first:
find backend -name "*agent_pool*" -type f
# Result: backend/app/services/persistent_agents/tenant_scoped_agent_pool.py

# API endpoint exists? Verify in:
grep -r "router.include" backend/app/api/v1/router_registry.py
```

### 3. Multi-Tenant Security (ENTERPRISE CRITICAL)
```python
# EVERY query needs tenant isolation:
.where(
    Model.client_account_id == context.client_account_id,
    Model.engagement_id == context.engagement_id
)

# Cache keys MUST be tenant-scoped:
cache_key = f"data:{client_id}:{engagement_id}:{key}"
```

## 🏆 GOLDEN PATH PLAYBOOKS

### Add a New Phase Handler
```python
# 1. Create handler in modular structure
backend/app/services/flow_handlers/new_phase_handler.py:

from app.services.persistent_agents import TenantScopedAgentPool

class NewPhaseHandler:
    async def execute(self, flow_id: str, context: RequestContext):
        # Get persistent agent (NOT new Crew!)
        agent_pool = TenantScopedAgentPool(context.client_account_id)
        agent = await agent_pool.get_agent('phase_agent')
        
        # Atomic transaction pattern
        async with self.db.begin():
            master_flow = await self.get_master_flow(flow_id)
            await self.db.flush()  # Critical for FK!
            
            result = await agent.execute(master_flow)
            child_flow.current_phase = 'next_phase'
            await self.db.commit()

# 2. Register in router_registry.py
# 3. Add to PHASE_SEQUENCES constant
```

### Create Polling Endpoint (NO WebSockets!)
```typescript
// Frontend - MANDATORY polling pattern
const useFlowStatus = (flowId: string) => {
  return useQuery({
    queryKey: ['flow-status', flowId],
    queryFn: () => fetchFlowStatus(flowId),
    enabled: !!flowId,
    refetchInterval: (data) => {
      if (!data) return false;
      if (data.status === 'completed') return false;
      return data.status === 'processing' ? 5000 : 15000;
    },
    staleTime: 0,  // Always fresh for status
  });
};
```

### Persist Records with Transitional Read
```python
# Write to normalized tables, fallback to JSON
async def get_analysis_data(flow_id: str):
    # Try normalized table first
    result = await db.execute(
        select(SixRAnalysis).where(
            SixRAnalysis.flow_id == flow_id,
            SixRAnalysis.client_account_id == context.client_account_id
        )
    )
    if result:
        return result.scalar_one()
    
    # Fallback to JSON persistence
    flow = await get_flow(flow_id)
    if flow.persistence_data:
        return flow.persistence_data.get('analysis')
    
    # Return structured error, NEVER mock data
    return {
        'status': 'not_ready',
        'error_code': 'ANALYSIS_PENDING',
        'details': {'flow_id': flow_id}
    }
```

## 🔍 Intelligent Search Patterns (SAVE TOKENS)
*Primary reference: [000-lessons.md#7-debugging--troubleshooting](./000-lessons.md#7-debugging--troubleshooting)*

### Search Decision Tree
```
Need to find something?
├── Know exact symbol? → find_symbol()
├── Know pattern? → search_for_pattern()
├── Need structure? → get_symbols_overview()
├── Need relationships? → find_referencing_symbols()
└── Last resort → read_file() with limits
```

### Example: Finding a Service
```python
# Step 1: Confirm existence (fast)
search_for_pattern("class TenantScopedAgentPool")

# Step 2: Get overview (medium)
get_symbols_overview("backend/app/services/persistent_agents/tenant_scoped_agent_pool.py")

# Step 3: Read specific method only (targeted)
find_symbol("TenantScopedAgentPool/get_agent", include_body=True)
```

## 💾 Database Patterns
*Primary reference: [000-lessons.md#2-backend--database](./000-lessons.md#2-backend--database)*

### Critical Rules
```sql
-- ALWAYS use 'migration' schema
SELECT * FROM migration.table_name;  ✓
SELECT * FROM table_name;  ✗ (uses public)

-- CHECK constraints, not ENUMs
CHECK (status IN ('pending', 'running'))  ✓
ENUM('pending', 'running')  ✗
```

### SQLAlchemy Gotchas
```python
# Boolean comparison
.where(Model.is_active == True)  ✓
.where(Model.is_active is True)  ✗ (breaks)

# UUID type handling
CollectionFlow.flow_id == UUID(flow_id_str)  ✓
CollectionFlow.id == flow_id  ✗ (id is internal PK)

# Atomic transaction pattern
async with db.begin():
    master = create_master_flow()
    await db.flush()  # Critical for FK!
    child = create_child_flow(master.id)
    await db.commit()
```

### Alembic Migration Patterns
```python
# Idempotent enum creation
enum = postgresql.ENUM('pending', 'running', name='status_enum', create_type=False)
enum.create(op.get_bind(), checkfirst=True)  ✓

# Table existence check
if not table_exists('table_name'):
    op.create_table('table_name', ..., schema='migration')
```

## ⚛️ Frontend Patterns
*Primary reference: [000-lessons.md#3-frontend--uiux](./000-lessons.md#3-frontend--uiux)*

### React Query Best Practices
```typescript
// Optimal caching strategy
const { data } = useQuery({
    queryKey: ['collection-questionnaires', flowId],
    enabled: !!flowId,  // Prevent unnecessary calls
    staleTime: 30000,   // 30s before refetch
    refetchInterval: isActive ? 5000 : 15000,  // Smart polling
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
});
```

### Multi-Tenant Headers (REQUIRED)
```typescript
const headers = {
    'X-Client-Account-ID': clientAccountId,  // Always
    'X-Engagement-ID': engagementId,        // Always
    'X-Flow-ID': flowId                     // Discovery only
};
```

### Common UI Patterns
```typescript
// Completion detection
if (questionnaires.length === 0) {
    setIsCompleted(true);
}

// Field name flexibility (handle backend variations)
const flowId = data.flow_id || data.flowId || data.id;
const status = data.flow_status || data.status;
```

### React Hooks Rules
```typescript
// ✗ NEVER call hooks conditionally
if (condition) {
    const [state] = useState();  ✗
}

// ✓ ALWAYS at top level
const [state] = useState();
if (condition) {
    setState(value);  ✓
}
```

## 🏗️ Architecture (RESPECT THESE PATTERNS)
*Primary reference: [000-lessons.md#1-architecture--design-patterns](./000-lessons.md#1-architecture--design-patterns)*

### Two-Table Pattern (REQUIRED - NOT OPTIONAL)
```python
# Master: Lifecycle & orchestration
crewai_flow_state_extensions:
  - flow_status: 'running', 'paused', 'completed'
  - Single source of truth for state

# Child: Domain-specific operations
discovery_flows:
  - current_phase: 'field_mapping', 'data_cleansing'
  - UI needs this data
```

### Data Retrieval Chains
```python
# Common pattern: Multi-step lookups
flow = get_flow(flow_id)
import_data = get_import(flow.data_import_id)
mappings = get_mappings(import_data.id)
# Don't assume single-step access!
```

### 7-Layer Architecture (ENTERPRISE REQUIREMENT)
```
1. API Layer → Routes & validation
2. Service Layer → Business logic
3. Repository Layer → Data access
4. Model Layer → Pydantic/SQLAlchemy
5. Cache Layer → Redis/memory
6. Queue Layer → Async processing
7. Integration Layer → External services
```
**This is NOT over-engineering** - Required for:
- Multi-tenant isolation
- Atomic transactions
- Audit trails
- Graceful degradation

## ❌ Critical Mistakes That Break Production

### API Mistakes
```python
# ❌ Bypassing MFO corrupts state
/api/v1/discovery/start  # NEVER use directly

# ✓ Always use MFO
/api/v1/master-flows/start
```

### SQL Injection Vulnerabilities
```python
# ❌ SECURITY BREACH
sa.text(f"SELECT * FROM {table}")

# ✓ Safe parameterized query
sa.text("SELECT * FROM :table").bindparams(table=table_name)
```

### Performance Killers
```python
# ❌ 94% performance loss - BANNED PATTERN
def execute_phase():
    from crewai import Crew
    crew = Crew(agents=[...])  # Creates new crew each call!

# ✓ MANDATORY: Use persistent agents
from app.services.persistent_agents import TenantScopedAgentPool

def execute_phase(context: RequestContext):
    # Singleton per tenant, reused across phases
    agent_pool = TenantScopedAgentPool(context.client_account_id)
    agent = await agent_pool.get_agent('discovery')
    return await agent.execute()
```

### Business Logic Anti-Patterns
```python
# ❌ Hardcoded thresholds
if confidence_score > 0.8:
    approve_mapping()

# ✓ Agent-driven decisions
if agent.should_approve(confidence_score, context):
    approve_mapping()
```

### Missing Child Records & MFO Atomicity
```python
# ❌ Creating only master flow - BREAKS UI
master_flow = create_master_flow()
await db.commit()

# ✓ MANDATORY: Atomic pattern with orchestrator
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

async with db.begin():
    # Create master with flush for FK availability
    orchestrator = MasterFlowOrchestrator(db)
    master_flow_id = await orchestrator.create_flow(
        flow_type='discovery',
        client_account_id=context.client_account_id,
        atomic=True  # Prevents internal commits
    )
    await db.flush()  # Makes ID available for child
    
    # Create child flow with master reference
    child_flow = DiscoveryFlow(
        flow_id=master_flow_id,
        master_flow_id=master_flow_id,
        client_account_id=context.client_account_id,
        status='initialized'
    )
    db.add(child_flow)
    await db.commit()  # Single commit for both
```

## 🐳 Docker-First Development
*Primary reference: [000-lessons.md#4-devops--deployment](./000-lessons.md#4-devops--deployment)*

### Container Commands
```bash
# Start everything (REQUIRED)
docker-compose up -d --build

# Access containers
docker exec -it migration_backend bash
docker exec migration_postgres psql -U postgres -d migration_db

# View logs
docker-compose logs -f backend

# Test endpoints
curl http://localhost:8081  # Frontend (NOT 3000)
curl http://localhost:8000/health  # Backend
```

### Pre-commit Workflow
```bash
# ALWAYS run once before --no-verify
pre-commit run --all-files

# Fix specific violations
pre-commit run black --files backend/app/file.py
pre-commit run flake8 --files backend/app/file.py

# Only after fixing, use for urgent commits:
git commit --no-verify -m "fix: critical issue"
```

### Railway/Vercel Deployment
```yaml
# Railway specifics:
- Uses requirements-docker.txt (NOT requirements.txt)
- Single DATABASE_URL (not POSTGRES_HOST/PORT)
- Scripts need #!/bin/bash (not #!/bin/sh)

# Vercel specifics:
- No WebSocket support (use polling)
- Environment variables in dashboard
```

## 🔐 Security Requirements
*Primary reference: [000-lessons.md#6-security](./000-lessons.md#6-security)*

### JWT Validation
```python
# Reject suspicious subjects
suspicious = {"system", "admin", "root", "service", "bot"}
if subject.lower() in suspicious or len(subject) < 3:
    raise SecurityError("Invalid JWT subject")
```

### Multi-Tenant Isolation
```python
# EVERY database query needs scoping
query = select(Model).where(
    Model.client_account_id == context.client_account_id,
    Model.engagement_id == context.engagement_id
)

# Cache keys must include tenant
cache_key = f"{client_id}:{engagement_id}:{data_key}"
```

### Secure Logging
```python
# ❌ NEVER log sensitive data
logger.error(f"Failed: {exception}")  # May contain secrets

# ✓ Log safely
logger.error(f"Failed: {type(exception).__name__}")
```

### Password Security
```python
# ❌ NEVER use weak hashing
hashlib.sha256(password)  # Insecure

# ✓ Use bcrypt
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])
hashed = pwd_context.hash(password)
```

## 🔧 Debugging Playbook
*Primary reference: [000-lessons.md#7-debugging--troubleshooting](./000-lessons.md#7-debugging--troubleshooting)*

### When Things Break (Common Fixes)

#### "No Data" Issues
```bash
# 1. Check database has records
docker exec migration_postgres psql -U postgres -d migration_db \
  -c "SELECT COUNT(*) FROM migration.discovery_flows WHERE flow_id='...';"

# 2. Verify API returns data
curl -H "X-Client-Account-ID: ..." \
     http://localhost:8000/api/v1/flows/{flow_id}

# 3. Check frontend receives it
# Browser DevTools → Network → Response tab
```

#### Field Name Mismatches
```javascript
// Frontend defensive coding
const flowId = data.flow_id || data.flowId || data.master_flow_id;
const status = data.status || data.flow_status;
```

#### Missing API Endpoints (404s)
```python
# Check registration in:
# 1. router_imports.py - Is router imported?
# 2. router_registry.py - Is router included?
# 3. Run: curl http://localhost:8000/docs - See all endpoints
```

## ⚡ Performance Optimization

### Model-Serializer Alignment Testing
```python
# MANDATORY: Add unit test for API response alignment
async def test_model_serializer_alignment():
    """Ensure database model matches API response"""
    # Create model instance
    flow = DiscoveryFlow(
        flow_id=uuid4(),
        status='running',
        current_phase='field_mapping'
    )
    
    # Serialize for API
    response = DiscoveryFlowResponse.from_orm(flow)
    
    # Verify field names match (snake_case)
    assert hasattr(response, 'flow_id')
    assert hasattr(response, 'current_phase')
    assert not hasattr(response, 'flowId')  # No camelCase!
    assert not hasattr(response, 'currentPhase')
    
    # Verify serialization round-trip
    json_data = response.json()
    parsed = json.loads(json_data)
    assert 'flow_id' in parsed
    assert 'flowId' not in parsed
```

### Smart Polling Strategy
```typescript
const pollInterval = {
  active: 5000,      // 5s when processing
  waiting: 15000,    // 15s when idle
  error: 30000,      // 30s after errors
  stopped: null      // Stop when complete
};
```

### Caching Strategy
```typescript
// Cache duration by data type
staleTime: {
  userProfile: 24 * 60 * 60 * 1000,  // 24h (rarely changes)
  fieldMappings: 5 * 60 * 1000,      // 5min (occasional updates)
  flowStatus: 0                       // Always fresh
}
```

## 🎯 Modularization Patterns

### When File > 400 Lines
```python
# Structure:
module_name/
  __init__.py         # Backward compatibility exports
  base.py            # Core classes, exceptions
  handlers/          # Business logic modules
  utils.py           # Helper functions
  schemas.py         # Pydantic models

# Preserve public API:
# old: from app.services.big_file import MyClass
# new: from app.services.big_file import MyClass  # Still works!
```

## 🚀 Workflow Automation

### Structured Error Returns (NEVER Mock Data)
```python
# ❌ BANNED: Returning mock analysis
if not analysis_ready:
    return {
        'confidence': 0.5,
        'recommendations': ['Mock recommendation']
    }

# ✓ MANDATORY: Structured error format
if not analysis_ready:
    return {
        'status': 'pending',
        'error_code': 'ANALYSIS_IN_PROGRESS',
        'details': {
            'flow_id': flow_id,
            'estimated_time': 30,
            'retry_after': 5
        }
    }
```

### Telemetry Pattern
```python
# Publish tenant-scoped events
async def publish_event(event_type: str, data: dict, context: RequestContext):
    key = f"events:{context.client_account_id}:{context.engagement_id}:{event_type}"
    await redis.publish(key, json.dumps({
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'data': data,
        'tenant': context.client_account_id
    }))
```

### Bug Fix Workflow
```bash
# 1. Find bugs
gh issue list --label bug --state open

# 2. Create branch
git checkout -b fix/bug-batch-$(date +%Y%m%d)

# 3. Fix with agents (parallel execution)
# QA → SRE → DevSecOps → QA Validation

# 4. Update GitHub issues (CRITICAL - often missed!)
gh issue comment $ISSUE_NUM --body "Fixed in PR #XXX"

# 5. Create PR
gh pr create --title "fix: Bug batch" --body "..."
```

### PR Review Resolution
```markdown
## ✅ ALL Review Items Addressed

### Must-Fix ✅
- Issue: [Description]
- Fixed: [What was done]
- File: [path/to/file]

### High-Priority ✅
- All TypeScript 'any' removed
- Backward compatibility maintained
- Tests added

Ready for merge! 🚀
```

## 📚 Core Principles

1. **Root Cause > Quick Fix** - Dig deep, fix properly
2. **Existing Code > New Code** - Modify don't recreate
3. **Verify > Assume** - Check before coding
4. **Atomic > Partial** - Complete transactions
5. **Secure > Convenient** - No shortcuts on security
6. **Pattern > Ad-hoc** - Follow established patterns
7. **HTTP Polling > WebSockets** - NO WebSocket usage in production
8. **Persistent Agents > New Crews** - Use TenantScopedAgentPool
9. **Structured Errors > Mock Data** - Never return fake analysis
10. **snake_case > camelCase** - Enforce in CI/CD

## 🔨 ENFORCEMENT HOOKS

### CI/CD Checks (Automatic)
```bash
# These run on every PR:
grep -r "WebSocket\|ws://" src/ && exit 1
grep -r "is True" backend/ && exit 1
grep -r "Crew(" backend/ | grep -v "TenantScopedAgentPool" && exit 1
grep -r "asyncio.run" backend/ && exit 1
```

### PR Template Requirements
```markdown
## PR Checklist (REQUIRED)
- [ ] I have read 000-lessons.md and the Quick Reference Guide
- [ ] No WebSocket usage added (HTTP polling only)
- [ ] Tenant scoping verified on all queries
- [ ] Atomic transaction pattern used (begin/flush/commit)
- [ ] Model-serializer alignment test added/validated
- [ ] No mock data returned from APIs
- [ ] snake_case used in all new API types
- [ ] TenantScopedAgentPool used (no new Crew instantiation)
```

### Pre-commit Helpers
```yaml
# .pre-commit-config.yaml additions
- repo: local
  hooks:
    - id: check-banned-patterns
      name: Check for banned patterns
      entry: scripts/check_banned_patterns.py
      language: python
      files: \.(py|ts|tsx)$
    - id: check-snake-case
      name: Verify snake_case in API types
      entry: scripts/check_snake_case.py
      language: python
      files: \.(ts|tsx)$
```