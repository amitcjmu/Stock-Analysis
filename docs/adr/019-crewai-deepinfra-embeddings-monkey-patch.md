# ADR-019: CrewAI DeepInfra Embeddings Monkey Patch

## Status
**SUPERSEDED** (2025-10-01)
Monkey patches for Agent/Crew defaults have been replaced by factory pattern.
DeepInfra embeddings patch remains active (see Embeddings Patch Status below).

## Context
During implementation of GitHub Issue #89 (field mappings not being auto-generated), we discovered that CrewAI's memory system defaults to OpenAI embeddings (`text-embedding-3-small`) which is incompatible with our DeepInfra-based infrastructure. This caused:

- 404 errors when CrewAI tried to access OpenAI embedding endpoints
- Silent memory system failures that made agents appear to return "instantaneous" responses
- Fallback to cached/static data instead of actual CSV field processing
- Inability to store and retrieve historical field mapping patterns

## Decision
We implement a comprehensive monkey patch system in `app/services/crewai_memory_patch.py` that intercepts CrewAI's embedding calls and redirects them to DeepInfra's compatible API.

### Technical Implementation

#### 1. OpenAI Client Patching
```python
def patched_create(self, *args, **kwargs):
    """Patched embeddings.create that forces DeepInfra model and encoding"""
    # Force the correct DeepInfra embedding model
    if 'model' in kwargs:
        original_model = kwargs['model']
        if original_model in ['text-embedding-3-small', 'text-embedding-ada-002']:
            logger.debug(f"Patching model from '{original_model}' to 'thenlper/gte-large' for DeepInfra")
            kwargs['model'] = 'thenlper/gte-large'
    
    # Force encoding_format to 'float' for DeepInfra compatibility
    kwargs['encoding_format'] = 'float'
    
    return original_create(self, *args, **kwargs)

Embeddings.create = patched_create
```

#### 2. Environment Variable Override
```python
os.environ["OPENAI_API_KEY"] = api_key
os.environ["OPENAI_API_BASE"] = "https://api.deepinfra.com/v1/openai"
os.environ["OPENAI_BASE_URL"] = "https://api.deepinfra.com/v1/openai"
```

#### 3. Custom Crew Embedder Configuration
```python
custom_embedder = {
    "provider": "openai",
    "config": {
        "model": "thenlper/gte-large",
        "api_key": os.getenv("DEEPINFRA_API_KEY"),
        "api_base": "https://api.deepinfra.com/v1/openai",
        "encoding_format": "float"
    }
}
```

## Consequences

### Positive
- ✅ **Functional Memory System**: CrewAI agents can now store and retrieve historical field mapping patterns
- ✅ **Cost Efficiency**: Uses DeepInfra's competitive pricing instead of OpenAI
- ✅ **Infrastructure Consistency**: Aligns with our DeepInfra-based LLM strategy
- ✅ **Performance Improvement**: Resolves "instantaneous response" issue that was masking processing failures
- ✅ **Data Quality**: Agents now process real CSV field names instead of fallback data

### Negative
- ⚠️ **Fragile Implementation**: Monkey patching is inherently brittle and could break with CrewAI updates
- ⚠️ **Maintenance Overhead**: Requires monitoring CrewAI releases for compatibility
- ⚠️ **Debugging Complexity**: Patched behavior may complicate troubleshooting
- ⚠️ **Hidden Dependencies**: Other parts of the system may unknowingly rely on this patch

### Risks

#### High Risk: CrewAI Version Updates
**Impact**: Major or minor CrewAI updates could:
- Change internal embedding API structure
- Modify class/method names being patched
- Introduce new initialization paths that bypass our patches
- Break memory system functionality without obvious errors

**Mitigation Strategy**:
- Pin CrewAI version in requirements.txt
- Implement comprehensive integration tests for memory functionality
- Monitor CrewAI release notes for embedding-related changes
- Create fallback mechanism to disable memory if patches fail

#### Medium Risk: DeepInfra API Changes
**Impact**: Changes to DeepInfra's OpenAI-compatible endpoint could break compatibility

**Mitigation Strategy**:
- Monitor DeepInfra API documentation
- Implement graceful fallback to memory-disabled mode
- Add comprehensive error logging for embedding failures

## Alternatives Considered

### 1. Custom CrewAI Fork
**Rejected**: Would require maintaining entire CrewAI codebase and merging upstream changes

### 2. Disable Memory Entirely
**Rejected**: Loses valuable historical context that improves field mapping accuracy

### 3. Wrapper Classes
**Rejected**: CrewAI's internal architecture makes clean wrapper implementation difficult

### 4. Official CrewAI Configuration
**Rejected**: CrewAI doesn't currently support pluggable embedding providers in memory system

## Implementation Notes

### Testing Strategy
```python
# Verify patch effectiveness
assert "thenlper/gte-large" in embedding_request.model
assert embedding_request.encoding_format == "float"
assert "200 OK" in embedding_response.status
```

### Monitoring Requirements
- Log all embedding API calls with model names and response codes
- Alert on 404 errors from embedding endpoints
- Monitor for CrewAI update releases
- Track memory system usage and effectiveness

### Rollback Plan
1. Set `memory=False` in crew configurations
2. Remove monkey patch imports
3. Restart backend services
4. Verify field mapping still works (without historical context)

## Future Considerations

### CrewAI Roadmap Alignment
Monitor CrewAI development for:
- Official multi-provider embedding support
- Configuration-based embedding provider selection
- Plugin architecture for custom providers

### Technical Debt Resolution
Consider migrating to official solution when available:
- CrewAI plugin system (if developed)
- Official DeepInfra integration
- Configurable embedding providers

## References
- GitHub Issue #89: Field mappings not auto-generated after file upload
- DeepInfra OpenAI-compatible API: https://api.deepinfra.com/v1/openai
- CrewAI Memory Documentation: https://docs.crewai.com/how-to/LLM-Connections
- Original bug report: "agents returning instantaneous responses instead of processing data"

---

**Decision Date**: 2025-08-14
**Decision Makers**: Development Team
**Review Date**: 2025-11-14 (or upon next major CrewAI release)

---

## UPDATE: Migration to Factory Pattern (2025-10-01)

### Changes Implemented

As part of addressing over-abstraction issues identified in the Discovery Flow architectural review, **Agent and Crew default monkey patches have been removed** and replaced with an explicit factory pattern.

### What Was Removed

1. **Agent Default Monkey Patches** (`app/services/crewai_flows/crews/__init__.py` lines 41-73):
   - Global override of `Agent.__init__()` for default configurations
   - Automatic `allow_delegation=False` and `max_delegation=0` settings
   - Verbose=False defaults

2. **Crew Default Monkey Patches**:
   - Global override of `Crew.__init__()` for default configurations
   - Automatic process and memory settings

### What Was Replaced

Created **explicit factory pattern** in `app/services/crewai_flows/config/crew_factory/`:

```python
# New factory pattern approach
from app.services.crewai_flows.config.crew_factory import (
    create_agent,
    create_crew,
    create_task,
)

# Explicit configuration via CrewConfig
DEFAULT_AGENT_CONFIG = {
    "allow_delegation": False,
    "max_delegation": 0,
    "max_iter": 1,
    "verbose": False,
}

DEFAULT_CREW_CONFIG = {
    "manager_llm": configured_llm,
    "planning_llm": configured_llm,
    "verbose": False,
}
```

### What Remains Active

**DeepInfra Embeddings Patch** (`app/core/memory/crewai_deepinfra_patch.py`):
- Still required for memory system functionality
- Redirects CrewAI embedding calls to DeepInfra API
- Applied at application startup
- No changes to this critical patch

### Migration Impact

**Files Migrated** (Phase 2 - October 2025):
- 20 crew implementation files migrated to factory pattern
- 9 files modularized to comply with <400 line requirement
- All crews now use explicit `create_agent()`, `create_crew()`, `create_task()` functions

**Benefits of Factory Pattern**:
- ✅ **Explicit over Implicit**: Configuration is visible at call sites
- ✅ **Testability**: Easier to test with dependency injection
- ✅ **Maintainability**: No hidden global state modifications
- ✅ **Debuggability**: Stack traces show actual configuration points
- ✅ **Type Safety**: Better IDE support and type checking

**Reduced Risks**:
- ✅ CrewAI version updates less likely to break agent creation
- ✅ No hidden side effects from global monkey patches
- ✅ Configuration changes are explicit and traceable

### Embeddings Patch Status

The DeepInfra embeddings monkey patch **REMAINS NECESSARY** and active because:
- CrewAI memory system still hardcodes OpenAI embedding calls
- No official configuration API for custom embedding providers
- Factory pattern cannot solve embedding provider selection
- Patch continues to provide critical memory functionality

### Updated Risks

#### CrewAI Version Updates
**Risk Reduced**: With Agent/Crew monkey patches removed, version updates only affect embeddings patch.

**Remaining Risk Area**: Embeddings API changes in CrewAI
**Mitigation**: Continue monitoring CrewAI releases for memory system changes

### Updated Testing Strategy

```python
# Factory pattern tests
def test_agent_creation_with_factory():
    agent = create_agent(role="Test", goal="Test", backstory="Test")
    assert agent.allow_delegation == False
    assert agent.max_delegation == 0
    assert agent.verbose == False

# Embeddings patch still tested
def test_embeddings_patch():
    assert "thenlper/gte-large" in embedding_request.model
    assert embedding_request.encoding_format == "float"
```

### Migration Guide

For new crew implementations:

```python
# ❌ OLD (relied on monkey patches)
from crewai import Agent, Crew, Task
agent = Agent(role="...", goal="...", backstory="...")

# ✅ NEW (explicit factory pattern)
from crewai import Crew, Process  # For type hints only
from app.services.crewai_flows.config.crew_factory import (
    create_agent,
    create_crew,
    create_task,
)

agent = create_agent(
    role="...",
    goal="...",
    backstory="...",
    # Explicit configuration options visible
)
```

### References

- **Phase 2 Implementation**: PR #480 - Monkey Patch Removal
- **Factory Pattern Guide**: `docs/guides/CREWAI_FACTORY_PATTERN_MIGRATION.md`
- **Original Code Review**: `docs/code-reviews/2025-10-01_discovery_flow_over_abstraction_review.md`
- **Modularization Summary**: `docs/code-reviews/2025-10-01_monkey_patch_removal_summary.md`

**Update Date**: 2025-10-01
**Updated By**: Development Team (via Claude Code)
**Next Review**: 2025-11-14 (embeddings patch only)