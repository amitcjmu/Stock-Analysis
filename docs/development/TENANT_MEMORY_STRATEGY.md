# Tenant Memory Management Strategy for Agentic Learning

**Status**: Active Development
**Last Updated**: 2025-10-02
**Stakeholders**: Development Team, Architecture Review Board

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Historical Context](#historical-context)
3. [Current State](#current-state)
4. [Architecture Decision](#architecture-decision)
5. [Implementation Strategy](#implementation-strategy)
6. [Migration Steps](#migration-steps)
7. [Future Roadmap](#future-roadmap)

---

## Executive Summary

This document defines the strategic approach for implementing enterprise-grade agentic learning with proper multi-tenant isolation. It explains why the current CrewAI memory monkey patches must be removed and how the `TenantMemoryManager` provides the correct architectural foundation for agent learning.

### Key Decisions

- ✅ **Remove all CrewAI memory monkey patches** - they violate explicit configuration principles
- ✅ **Use TenantMemoryManager for agent learning** - provides multi-tenant isolation
- ✅ **Leverage existing VectorUtils + AgentDiscoveredPatterns** - proven pgvector implementation
- ✅ **Keep embeddings adapter isolated** per ADR-019, but NOT applied globally

---

## Historical Context

### Phase 1: Initial CrewAI Memory Implementation (August 2025)

**Problem Discovered**: GitHub Issue #89 - Field mappings not auto-generated after file upload

**Root Cause**: CrewAI's memory system defaults to OpenAI embeddings (`text-embedding-3-small`), causing:
- 404 errors when trying to access OpenAI embedding endpoints
- Silent memory system failures
- Agents returning instantaneous responses instead of processing data
- Inability to store historical field mapping patterns

**Initial Solution**: ADR-019 - CrewAI DeepInfra Embeddings Monkey Patch

```python
# app/services/crewai_memory_patch.py
def patch_crewai_memory_for_deepinfra():
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = deepinfra_api_key
    os.environ["OPENAI_API_BASE"] = "https://api.deepinfra.com/v1/openai"

    # Monkey patch Embeddings.create
    Embeddings.create = patched_create
```

**Result**: Memory worked, but created global state pollution and hidden dependencies.

### Phase 2: Factory Pattern Migration (October 1, 2025)

**Problem Identified**: Architectural review found over-abstraction issues

**Key Finding**:
> "CrewAI global constructor monkey patching is brittle and conflicts with agentic-first goals. Remove global Agent/Crew constructor patches; replace with explicit CrewConfig/CrewFactory."

**Decision**: Remove ALL global monkey patches except isolated embeddings adapter

**Implementation**: PR #480 - Monkey Patch Removal
- ✅ Removed global `Agent.__init__` and `Crew.__init__` patches
- ✅ Created `CrewFactory` for explicit configuration
- ✅ Created `TenantMemoryManager` for enterprise memory management
- ✅ Updated ADR-019 to reflect changes

**Critical Recommendation from Review**:
> "Provide a `CrewMemoryManager` to standardize memory on/off and embedder config explicitly. Keep the DeepInfra embeddings adapter in a dedicated module; guard with env/version checks."

### Phase 3: LiteLLM Tracking Addition (October 2, 2025)

**New Requirement**: Track all LLM usage for cost monitoring

**Implementation**: Commit 3152852d8
- Added `LiteLLMTrackingCallback` to log all LiteLLM calls
- Installed callback at app startup in `lifecycle.py`

**Unintended Consequence**: Exposed conflict between:
1. LiteLLM callback (global, tracks all calls)
2. Memory patch (sets global env vars)
3. CrewAI memory (creates OpenAI client before patch runs)

**Result**: Railway 401 errors when agents try to save to memory

---

## Current State

### What Works

1. **Factory Pattern** (`app/services/crewai_flows/config/crew_factory/`)
   - ✅ Explicit agent/crew configuration
   - ✅ No global constructor overrides
   - ✅ Testable and maintainable

2. **TenantMemoryManager** (`app/services/crewai_flows/memory/tenant_memory_manager.py`)
   - ✅ Multi-tenant isolation (ENGAGEMENT, CLIENT, GLOBAL scopes)
   - ✅ Data classification and privacy controls
   - ✅ Encryption and audit trail support
   - ❌ **NOT CURRENTLY USED** - exists but not integrated

3. **VectorUtils + AgentDiscoveredPatterns**
   - ✅ pgvector-based pattern storage (1536 dimensions)
   - ✅ Similarity search working
   - ✅ Direct DeepInfra embeddings API calls
   - ✅ Proven implementation since August 2025

4. **EmbeddingService** (`app/services/embedding_service.py`)
   - ✅ Direct DeepInfra API calls via httpx
   - ✅ No dependency on OpenAI SDK
   - ✅ Returns 1024-dimensional vectors from `thenlper/gte-large`

### What's Broken

1. **Per-Crew Memory Patch** (`field_mapping_crew_fast.py` lines 120-174)
   ```python
   # ❌ PROBLEMATIC: Called during crew creation, not at startup
   from app.services.crewai_memory_patch import apply_memory_patch

   patch_success = apply_memory_patch()  # Sets global env vars

   custom_embedder = {
       "provider": "openai",  # Tells CrewAI to use OpenAI provider
       "config": {
           "api_base": "https://api.deepinfra.com/v1/openai",
           # ...
       }
   }

   crew = create_crew(..., memory=True, embedder=custom_embedder)
   ```

   **Issues**:
   - Sets global `OPENAI_API_KEY` environment variable
   - ChromaDB creates OpenAI client BEFORE env vars are set
   - LiteLLM callback tracks calls but they go to wrong endpoint
   - Results in 401 authentication errors in Railway

2. **CrewAI Memory Not Actually Working**
   - Environment variables don't affect already-created clients
   - `custom_embedder` config not properly applied by CrewAI
   - Memory saves fail with OpenAI 401 errors

---

## Architecture Decision

### Why NOT Apply Memory Patch Globally at Startup

#### Decision: Do NOT move `apply_memory_patch()` to app startup

**Reasons**:

1. **Violates Explicit Configuration Principle**
   - October 1st review mandated: "explicit over implicit"
   - Global env vars create hidden state
   - Goes against factory pattern migration goals

2. **Global State Pollution**
   ```python
   # What global patch does:
   os.environ["OPENAI_API_KEY"] = deepinfra_key  # ❌ Affects ALL OpenAI usage
   os.environ["OPENAI_API_BASE"] = deepinfra_url # ❌ Redirects ALL OpenAI calls
   ```

   **Risk**: ANY code creating `openai.OpenAI()` now uses DeepInfra

3. **Multi-Provider Strategy Conflict**
   - Codebase uses BOTH DeepInfra and OpenAI
   - Gemma 3 (DeepInfra) for chat
   - Llama 4 (DeepInfra) for agents
   - Potential future OpenAI usage
   - Global env vars break this flexibility

4. **Tenant Isolation Risk**
   - Global memory config affects all tenants
   - Violates `TenantMemoryManager` design
   - No per-tenant memory controls

5. **LiteLLM Callback Interference**
   ```
   Startup with global patch:
   1. Apply memory patch → OPENAI_API_KEY = DeepInfra
   2. Install LiteLLM callback → Track all calls
   3. Any OpenAI usage → Goes to DeepInfra unexpectedly
   4. Logs show DeepInfra but code thinks it's OpenAI
   ```

6. **Bypasses TenantMemoryManager Architecture**
   - `TenantMemoryManager` was created specifically for this
   - Global patch makes it redundant
   - Loses enterprise-grade memory isolation

### Why REMOVE CrewAI Memory (Current Recommendation)

#### Decision: Disable `memory=True` in all CrewAI crews

**Rationale**:

1. **CrewAI Memory Never Worked Properly**
   - 401 errors in production (Railway)
   - Environment variable timing issues
   - Monkey patch too fragile

2. **Better Alternative Exists**
   - `VectorUtils` + `AgentDiscoveredPatterns` proven working
   - Direct DeepInfra API calls (no OpenAI SDK needed)
   - Proper multi-tenant isolation
   - Already used for field mapping patterns

3. **Aligns with Architecture Review**
   - Review recommended explicit memory management
   - `TenantMemoryManager` provides the framework
   - Can build proper learning on this foundation

4. **Removes Technical Debt**
   - Eliminates monkey patches
   - Removes global state dependencies
   - Simplifies maintenance

---

## Implementation Strategy

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CrewAI Agents                           │
│                    (memory=False)                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ Store/Retrieve Patterns
                  ↓
┌─────────────────────────────────────────────────────────────┐
│              TenantMemoryManager                            │
│  - Multi-tenant isolation (engagement/client/global)        │
│  - Privacy controls & data classification                   │
│  - Encryption & audit trail                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                   VectorUtils                               │
│  - pgvector operations (1536 dimensions)                    │
│  - Pattern storage & similarity search                      │
│  - Feedback loop integration                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌──────────────────────────────────┬──────────────────────────┐
│     AgentDiscoveredPatterns      │    EmbeddingService      │
│  - PostgreSQL + pgvector         │  - DeepInfra API         │
│  - 1536-dim embeddings           │  - thenlper/gte-large    │
│  - Multi-tenant scoped           │  - 1024-dim vectors      │
└──────────────────────────────────┴──────────────────────────┘
```

### How It Works

1. **Agent Execution** (No CrewAI Memory)
   ```python
   # Crew created WITHOUT memory
   crew = create_crew(
       agents=[agent],
       tasks=[task],
       memory=False,  # ✅ No CrewAI memory
       embedder=None
   )
   ```

2. **Pattern Learning** (Via TenantMemoryManager)
   ```python
   # After agent completes task
   memory_manager = TenantMemoryManager(
       crewai_service=crewai_service,
       database_session=db
   )

   await memory_manager.store_learning(
       client_account_id=client_account_id,
       engagement_id=engagement_id,
       scope=LearningScope.ENGAGEMENT,
       pattern_type="field_mapping",
       pattern_data={
           "source_field": "cust_name",
           "target_field": "customer_name",
           "confidence": 0.95
       }
   )
   ```

3. **Pattern Retrieval** (For Future Tasks)
   ```python
   # When agent needs historical context
   similar_patterns = await memory_manager.retrieve_similar_patterns(
       client_account_id=client_account_id,
       engagement_id=engagement_id,
       pattern_type="field_mapping",
       query_context={"source_fields": ["cust_name", "cust_id"]},
       limit=5
   )
   ```

4. **Vector Storage** (Under the Hood)
   ```python
   # TenantMemoryManager uses VectorUtils internally
   pattern_id = await vector_utils.store_pattern_embedding(
       pattern_text=pattern_description,
       pattern_metadata={
           "client_account_id": client_account_id,
           "engagement_id": engagement_id,
           "pattern_type": "field_mapping",
           "confidence": 0.95
       },
       embedding_vector=embedding_vector  # From EmbeddingService
   )
   ```

### Key Differences from CrewAI Memory

| Feature | CrewAI Memory (Old) | TenantMemoryManager (New) |
|---------|--------------------|-----------------------------|
| **Configuration** | Global monkey patches | Explicit per-tenant config |
| **Isolation** | None (shared state) | Engagement/Client/Global scopes |
| **Embeddings** | OpenAI SDK (patched) | Direct DeepInfra API calls |
| **Storage** | ChromaDB (external) | PostgreSQL + pgvector (native) |
| **Privacy** | No controls | Data classification, encryption |
| **Audit** | No trail | Full audit logging |
| **Reliability** | Fragile (401 errors) | Proven working (since Aug 2025) |

---

## Migration Steps

### Immediate Actions (Current Sprint)

#### Step 1: Disable CrewAI Memory in Field Mapping Crew

**File**: `backend/app/services/crewai_flows/crews/field_mapping_crew_fast.py`

**Changes**:
```python
# REMOVE lines 120-174 (memory patch and custom embedder)

# BEFORE:
from app.services.crewai_memory_patch import apply_memory_patch
patch_success = apply_memory_patch()
custom_embedder = {...}
crew = create_crew(..., memory=True, embedder=custom_embedder)

# AFTER:
crew = create_crew(
    agents=[field_mapping_specialist],
    tasks=[mapping_task],
    process=Process.sequential,
    verbose=False,
    max_execution_time=300,
    memory=False,  # ✅ Disabled
    embedder=None  # ✅ No embedder needed
)
```

**Rationale**: Removes broken monkey patch, eliminates 401 errors

#### Step 2: Audit All Crews for Memory Usage

**Command**:
```bash
grep -r "memory=True" backend/app/services/crewai_flows/crews/
```

**Action**: Set `memory=False` in ALL crews

**Files to Check**:
- `agentic_asset_enrichment_crew.py`
- `optimized_field_mapping_crew/`
- Any other crews using `memory=True`

#### Step 3: Remove Global Memory Patch (If Still Present)

**Check**: Search for memory patch calls at startup
```bash
grep -rn "apply_memory_patch" backend/app/app_setup/
grep -rn "apply_memory_patch" backend/app/core/
```

**Action**: Remove any global memory patch calls

**Note**: Per-crew memory patch already identified and will be removed in Step 1

#### Step 4: Verify Railway Deployment

**Test**:
1. Deploy to Railway
2. Monitor logs for 401 errors: `railway logs --deployment | grep "401"`
3. Verify no "Error during short_term save" messages
4. Confirm agents execute without memory-related errors

**Success Criteria**: No 401 authentication errors in Railway logs

### Short-Term Enhancements (Next Sprint)

#### Step 5: Integrate TenantMemoryManager with Field Mapping

**File**: `backend/app/services/crewai_flows/crews/field_mapping_crew_fast.py`

**Implementation**:
```python
async def field_mapping_crew_execution(
    client_account_id: int,
    engagement_id: int,
    source_fields: List[str],
    target_schema: Dict[str, Any],
    db: AsyncSession
):
    # 1. Retrieve historical patterns
    memory_manager = TenantMemoryManager(crewai_service, db)

    historical_patterns = await memory_manager.retrieve_similar_patterns(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        pattern_type="field_mapping",
        query_context={"source_fields": source_fields},
        limit=10
    )

    # 2. Create crew WITHOUT memory
    crew = create_crew(
        agents=[agent],
        tasks=[task],
        memory=False
    )

    # 3. Provide historical patterns as context
    task_context = {
        "source_fields": source_fields,
        "target_schema": target_schema,
        "historical_patterns": historical_patterns,  # ✅ Explicit context
    }

    # 4. Execute crew
    result = await crew.kickoff(inputs=task_context)

    # 5. Store new patterns learned
    await memory_manager.store_learning(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        scope=LearningScope.ENGAGEMENT,
        pattern_type="field_mapping",
        pattern_data=result.patterns_discovered
    )

    return result
```

**Benefits**:
- ✅ Explicit pattern retrieval (no hidden memory)
- ✅ Multi-tenant isolation
- ✅ Proper learning persistence
- ✅ No monkey patches required

#### Step 6: Add Memory Scope Configuration

**File**: `backend/app/core/config.py`

**Add Settings**:
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Tenant Memory Configuration
    DEFAULT_LEARNING_SCOPE: str = "ENGAGEMENT"  # ENGAGEMENT, CLIENT, GLOBAL, DISABLED
    ENABLE_CROSS_TENANT_LEARNING: bool = False
    MEMORY_RETENTION_DAYS: int = 365
    ENABLE_MEMORY_ENCRYPTION: bool = True

    @property
    def learning_scope(self) -> LearningScope:
        return LearningScope[self.DEFAULT_LEARNING_SCOPE]
```

**Usage**:
```python
memory_manager = TenantMemoryManager(crewai_service, db)
await memory_manager.configure_scope(settings.learning_scope)
```

#### Step 7: Create Memory Admin API Endpoints

**File**: `backend/app/api/v1/admin/memory_management.py` (NEW)

**Endpoints**:
```python
@router.get("/api/v1/admin/memory/stats")
async def get_memory_statistics(
    client_account_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get learning statistics and pattern counts"""
    pass

@router.post("/api/v1/admin/memory/scope")
async def update_memory_scope(
    client_account_id: int,
    scope: LearningScope,
    db: AsyncSession = Depends(get_db)
):
    """Update learning scope for a client"""
    pass

@router.delete("/api/v1/admin/memory/purge")
async def purge_client_memory(
    client_account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Purge all learning data for a client (GDPR compliance)"""
    pass
```

### Long-Term Roadmap (Future Sprints)

#### Phase 1: Enhanced Pattern Learning (Q4 2025)

**Goals**:
- Implement feedback loops for pattern refinement
- Add confidence score adjustments based on outcomes
- Support pattern versioning and rollback

**Files**:
- `backend/app/services/crewai_flows/memory/pattern_learning_service.py` (NEW)
- `backend/alembic/versions/xxx_add_pattern_versioning.py` (NEW)

#### Phase 2: Cross-Tenant Learning (Q1 2026)

**Goals**:
- Implement privacy-preserving pattern sharing
- Add opt-in mechanism for global learning
- Create anonymization pipeline for shared patterns

**Requirements**:
- Legal review for data sharing compliance
- Client consent management
- Differential privacy implementation

#### Phase 3: Advanced Memory Features (Q2 2026)

**Goals**:
- Implement episodic memory (task-specific contexts)
- Add semantic memory (general knowledge)
- Support procedural memory (learned workflows)

**Architecture**:
```python
class EnterpriseMemorySystem:
    episodic_memory: EpisodicMemoryManager  # Task contexts
    semantic_memory: SemanticMemoryManager  # General knowledge
    procedural_memory: ProceduralMemoryManager  # Workflows

    def integrate_with_agents(self, agent: Agent):
        """Provide multi-layer memory to agents"""
        pass
```

---

## Appendices

### Appendix A: Why Monkey Patches Were Removed

From the October 1st architectural review:

> **Finding**: `crews/__init__.py` globally overrides `Agent.__init__` and `Crew.__init__` (no delegation, max_iter=1, etc.), which is brittle and conflicts with agentic-first goals.
>
> **Recommendation**: Remove global Agent/Crew constructor patches; replace with explicit `CrewConfig/CrewFactory` that applies defaults via constructor parameters.

**Problems with Monkey Patches**:
1. **Hidden Behavior**: Global overrides make it unclear what configuration is applied
2. **Testing Difficulty**: Hard to mock or test individual components
3. **Version Fragility**: CrewAI updates can break monkey patches without warning
4. **Debugging Complexity**: Stack traces don't show configuration points
5. **Type Safety**: IDE support breaks with runtime modifications

**Benefits of Factory Pattern**:
- ✅ Explicit configuration at call sites
- ✅ Testable with dependency injection
- ✅ Clear ownership of defaults
- ✅ Better IDE support and type checking
- ✅ Version-safe (uses public APIs)

### Appendix B: TenantMemoryManager Implementation Details

**Current Implementation**: `backend/app/services/crewai_flows/memory/tenant_memory_manager.py`

**Key Features**:

1. **Multi-Tenant Isolation**
   ```python
   class LearningScope(Enum):
       DISABLED = "disabled"      # No learning
       ENGAGEMENT = "engagement"  # Isolated to engagement
       CLIENT = "client"          # Shared across client engagements
       GLOBAL = "global"          # Shared with consent
   ```

2. **Data Classification**
   ```python
   LearningDataClassification(
       sensitivity_level="confidential",
       data_categories=["field_patterns", "schema_analysis"],
       retention_period=365,
       encryption_required=True,
       audit_required=True,
       cross_tenant_sharing_allowed=False
   )
   ```

3. **Privacy Controls**
   - Encryption at rest for sensitive patterns
   - Audit trail for all memory operations
   - Configurable retention periods
   - GDPR-compliant data purging

**Integration Points**:
- `VectorUtils` for embeddings storage
- `EmbeddingService` for vector generation
- `AgentDiscoveredPatterns` model for persistence
- CrewAI crews for pattern discovery

### Appendix C: Embeddings Architecture

**Current Stack**:

1. **EmbeddingService** (`app/services/embedding_service.py`)
   - Direct DeepInfra API calls via httpx
   - Model: `thenlper/gte-large` (1024 dimensions)
   - No OpenAI SDK dependency

2. **VectorUtils** (`app/utils/vector_utils.py`)
   - pgvector operations (1536 dimensions)
   - Handles dimension mismatch (1024→1536 padding)
   - Similarity search with cosine distance

3. **AgentDiscoveredPatterns** Model
   ```python
   class AgentDiscoveredPatterns(Base):
       __tablename__ = "agent_discovered_patterns"

       id: UUID
       client_account_id: int
       engagement_id: int
       pattern_type: str
       pattern_description: str
       embedding: List[float]  # 1536 dimensions
       confidence_score: float
       created_at: datetime
   ```

**Why This Works**:
- ✅ No global state modifications
- ✅ Direct API calls (no SDK hijacking)
- ✅ Multi-tenant isolation built-in
- ✅ Proven working since August 2025

### Appendix D: Migration Checklist

#### Pre-Migration

- [ ] Backup Railway database
- [ ] Document current memory behavior
- [ ] Identify all crews using `memory=True`
- [ ] Review TenantMemoryManager code

#### Migration

- [ ] Disable CrewAI memory in all crews
- [ ] Remove memory patch calls
- [ ] Update crew factory defaults
- [ ] Add TenantMemoryManager integration
- [ ] Create admin API endpoints

#### Post-Migration

- [ ] Deploy to Railway staging
- [ ] Monitor for 401 errors
- [ ] Verify agent execution
- [ ] Test pattern storage/retrieval
- [ ] Update documentation

#### Validation

- [ ] Run integration tests
- [ ] Check LLM usage tracking
- [ ] Verify multi-tenant isolation
- [ ] Confirm no memory-related errors
- [ ] Performance benchmarking

---

## References

- **ADR-019**: CrewAI DeepInfra Embeddings Monkey Patch
- **PR #480**: Monkey Patch Removal and Factory Pattern Migration
- **Commit 3152852d8**: LiteLLM Usage Tracking Implementation
- **October 1st Review**: Discovery Flow Over-Abstraction Review
- **GitHub Issue #89**: Field Mappings Not Auto-Generated

---

**Document Owner**: Development Team
**Review Cycle**: Monthly
**Next Review**: 2025-11-02
