# ADR-024: TenantMemoryManager Architecture - Replacing CrewAI Memory

## Status
Accepted (2025-10-02)

Supersedes: ADR-019 (CrewAI DeepInfra Embeddings Monkey Patch)

## Context

### Problem Statement
The AI Modernize Migration Platform has been experiencing persistent 401 authentication errors in production (Railway) when CrewAI agents attempt to save to memory:

```
Error code: 401 - {'error': {'message': 'Incorrect API key provided: YxZPkWAf********************0w6Q...'}}
Error during short_term save in upsert
```

Root cause analysis revealed:
1. **LiteLLM tracking callback** is installed at app startup (`lifecycle.py:116`)
2. **Memory patch** is called during crew creation (`field_mapping_crew_fast.py:120`)
3. **OpenAI SDK** creates its client at import time, reading environment variables then
4. **Environment variables set after client creation** have no effect on existing client instances
5. **Result**: DeepInfra API key is sent to OpenAI's actual API endpoint (https://platform.openai.com)

### Historical Evolution

#### Phase 1: Global Monkey Patches (Pre-October 2025)
- Global monkey patches overrode `Agent.__init__` and `Crew.__init__` constructors
- Runtime modification of OpenAI SDK's `Embeddings.create` method
- Environment variable pollution: `OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_BASE_URL`
- Hidden global state caused unpredictable behavior

#### Phase 2: Factory Pattern Migration (October 2025)
- Removed Agent/Crew constructor monkey patches (ADR-019, see docs/code-reviews/2025-10-01_monkey_patch_removal_summary.md)
- Introduced explicit factory pattern (`crew_factory.py`)
- **Deliberately avoided** applying memory patch at startup to prevent global state pollution
- Created `TenantMemoryManager` as the proper enterprise solution

#### Phase 3: Memory System Replacement (Current - October 2025)
- Comprehensive research conducted using Context7 MCP (see `/docs/development/CREWAI_DEEPINFRA_EMBEDDINGS_RESEARCH.md`)
- Evaluated all alternative solutions: custom embedder, custom KnowledgeStorage, Mem0, OpenAI-compatible endpoints
- **Conclusion**: No viable alternatives exist; TenantMemoryManager is optimal

### Why Not Global Memory Patch at Startup?

Option B (apply memory patch at startup) was deliberately rejected during October 2025 remediation for 6 critical reasons:

1. **Violates Explicit Configuration Principle**
   - Factory pattern migration explicitly moved AWAY from global state
   - Global env vars undermine explicit configuration at creation time

2. **Global State Pollution**
   - Multiple LLM providers in use (DeepInfra, OpenAI, Llama)
   - Setting global `OPENAI_API_KEY` affects ALL OpenAI SDK usage
   - Breaks isolation between different LLM integrations

3. **Multi-Provider Strategy Conflict**
   - App uses DeepInfra for CrewAI embeddings
   - App uses OpenAI for direct chat completions
   - Global env vars make it impossible to use both simultaneously

4. **Timing Issues Persist**
   - OpenAI SDK may create clients before patch runs
   - Import order becomes critical and fragile
   - No guarantees about when env vars are read

5. **TenantMemoryManager Already Exists**
   - Enterprise-grade solution with multi-tenant isolation
   - PostgreSQL + pgvector (native to our stack)
   - Per-tenant memory scoping (engagement/client/global)
   - Already integrated with VectorUtils and AgentDiscoveredPatterns

6. **Architectural Integrity**
   - Factory pattern migration had a clear goal: explicit over implicit
   - Reverting to global patches contradicts that architectural decision
   - Proper solution: migrate to TenantMemoryManager

## Decision

**We will disable CrewAI's built-in memory system entirely** and migrate all agent learning to `TenantMemoryManager`.

### Specific Changes:

#### Immediate (Current Sprint)
1. **Disable CrewAI Memory**
   - Set `memory=False` in all `create_crew()` calls
   - Remove `embedder` configuration from crew creation
   - Remove memory patch calls from `field_mapping_crew_fast.py:120-174`

2. **Update Factory Defaults**
   - Change `CrewConfig.DEFAULT_CREW_CONFIG["memory"]` from `True` to `False`
   - Update `CrewConfig.DEFAULT_AGENT_CONFIG["memory"]` from `True` to `False`
   - Document this change in factory configuration

3. **Audit All Crews**
   - Review all crew implementations in `backend/app/services/crewai_flows/crews/`
   - Ensure no crews explicitly enable memory
   - Remove any remaining memory patch imports

#### Short-Term (Next 2 Sprints)
1. **Integrate TenantMemoryManager with Field Mapping**
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

2. **Add Memory Scope Configuration**
   - Environment variable: `TENANT_MEMORY_SCOPE` (engagement/client/global)
   - Per-tenant override via tenant settings table
   - Default: `LearningScope.ENGAGEMENT` for data isolation

#### Long-Term (Future Sprints)
1. **Enhanced Learning Integration**
   - Pattern recognition from `VectorUtils.find_similar_patterns()`
   - Auto-classification via `LearningDataClassification`
   - Cross-tenant learning with consent framework

2. **Remove Memory Patch Entirely**
   - Delete `backend/app/services/crewai_memory_patch.py`
   - Remove all references and imports
   - Update ADR-019 status to "Fully Superseded"

## Consequences

### Positive
- **Eliminates 401 Errors**: No more DeepInfra key sent to OpenAI API
- **Enterprise-Grade Memory**: Multi-tenant isolation, data classification, audit trails
- **Architectural Consistency**: Aligns with factory pattern and explicit configuration
- **Native Stack Integration**: PostgreSQL + pgvector already in use
- **Scalable Learning**: Per-tenant memory scoping with cross-tenant sharing controls
- **No External Dependencies**: Removes ChromaDB file-based storage
- **Better Performance**: Native database queries vs external vector DB calls

### Negative
- **Migration Effort**: All crews must be updated to use TenantMemoryManager
- **Learning Gap**: Short-term loss of memory during migration period
- **Integration Complexity**: Each crew type needs custom integration logic
- **Testing Requirements**: Verify memory retrieval works across all agent types

### Risks
- **Data Loss**: Existing CrewAI memory in ChromaDB will not be migrated (acceptable - dev data only)
- **Performance Impact**: Additional database queries for memory operations (mitigated by pgvector optimization)
- **Integration Bugs**: Custom integration per crew may introduce inconsistencies (mitigated by standardized TenantMemoryManager API)

## Alternatives Considered

Comprehensive research was conducted using Context7 MCP to evaluate ALL possible solutions (see `/docs/development/CREWAI_DEEPINFRA_EMBEDDINGS_RESEARCH.md`):

### 1. Custom Embedder with "custom" Provider ❌
- **How it works**: Use CrewAI's undocumented "custom" provider type
- **Why rejected**:
  - Fragile, relies on undocumented features
  - Still requires encoding format workaround (base64 vs float)
  - No multi-tenant isolation
  - ChromaDB still external dependency

### 2. Custom KnowledgeStorage Pattern ❌
- **How it works**: Extend `KnowledgeSource` and `RAGStorage` classes
- **Why rejected**:
  - More complex than TenantMemoryManager
  - Still tied to CrewAI's ChromaDB dependency
  - No enterprise features (tenant isolation, data classification)
  - Our solution is objectively superior

### 3. Mem0 External Memory ❌
- **How it works**: Third-party memory management service
- **Why rejected**:
  - Adds external dependency and complexity
  - Doesn't solve DeepInfra integration issue
  - No multi-tenant isolation guarantees
  - Cost and vendor lock-in concerns

### 4. OpenAI-Compatible Endpoint Directly ❌
- **How it works**: Point OpenAI SDK directly to DeepInfra
- **Why rejected**:
  - Already attempted and failed (encoding format mismatch)
  - OpenAI expects base64, DeepInfra requires float
  - Breaks when OpenAI SDK validates response format
  - No enterprise features

### 5. Apply Memory Patch at Startup (Option B) ❌
- **How it works**: Set global environment variables before any OpenAI clients are created
- **Why rejected**: See "Why Not Global Memory Patch at Startup?" section above

## Implementation Plan

### Phase 1: Disable CrewAI Memory (Current Sprint)
- [ ] Update `CrewConfig` defaults to `memory=False`
- [ ] Remove memory patch from `field_mapping_crew_fast.py`
- [ ] Audit all crews for memory usage
- [ ] Test all flows without CrewAI memory

### Phase 2: TenantMemoryManager Integration (Next 2 Sprints)
- [ ] Add `store_learning()` calls after agent task completion
- [ ] Implement `retrieve_patterns()` before agent execution
- [ ] Add memory scope configuration
- [ ] Test multi-tenant isolation

### Phase 3: Enhanced Learning (Future)
- [ ] Pattern recognition automation
- [ ] Cross-tenant learning framework
- [ ] Data classification enforcement
- [ ] Remove memory patch entirely

## References

### Related ADRs
- **ADR-019**: CrewAI DeepInfra Embeddings Monkey Patch (superseded)
- **ADR-015**: Persistent Multi-Tenant Agent Architecture
- **ADR-009**: Multi-Tenant Architecture

### Documentation
- `/docs/development/TENANT_MEMORY_STRATEGY.md` - Complete strategy and rationale
- `/docs/development/CREWAI_DEEPINFRA_EMBEDDINGS_RESEARCH.md` - Alternative solutions research
- `/docs/code-reviews/2025-10-01_monkey_patch_removal_summary.md` - Factory pattern migration

### Implementation
- `backend/app/services/crewai_flows/memory/tenant_memory_manager.py` - TenantMemoryManager implementation
- `backend/app/services/crewai_flows/config/crew_factory.py` - Factory pattern for crews
- `backend/app/db/utils/vector_utils.py` - Vector operations (pgvector)
- `backend/app/models/agent_discovered_patterns.py` - Pattern storage model

## Decision Rationale

After comprehensive research and analysis:

1. **No viable alternatives exist** for DeepInfra + CrewAI memory integration
2. **TenantMemoryManager provides superior enterprise features** compared to any CrewAI memory solution
3. **Global memory patches violate architectural principles** established in October 2025 factory pattern migration
4. **Multi-tenant isolation is non-negotiable** for enterprise deployment
5. **Native PostgreSQL + pgvector** is more performant and maintainable than external ChromaDB

**Therefore, disabling CrewAI memory and migrating to TenantMemoryManager is the only architecturally sound solution.**

## Success Criteria

- [ ] Zero 401 authentication errors in production
- [ ] All crews successfully execute without CrewAI memory
- [ ] TenantMemoryManager stores and retrieves patterns correctly
- [ ] Multi-tenant isolation verified (no data leakage)
- [ ] Performance metrics show no degradation
- [ ] All memory patch code removed from codebase
