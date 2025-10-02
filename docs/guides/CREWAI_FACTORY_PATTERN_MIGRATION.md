# CrewAI Factory Pattern Migration Guide

## Overview

As of **2025-10-01**, we have removed global CrewAI constructor monkey patches in favor of an explicit factory pattern. This change improves code maintainability, testability, and compatibility with future CrewAI versions.

## What Changed

### Before (Global Monkey Patches)

```python
# backend/app/services/crewai_flows/crews/__init__.py (OLD - REMOVED)
from crewai import Agent, Crew

# These constructors were globally patched at import time:
Agent.__init__ = optimized_agent_init  # Forced: allow_delegation=False, max_iter=1
Crew.__init__ = optimized_crew_init    # Forced: max_iterations=1, timeout=600s

# All Agent/Crew instances got these defaults automatically (hidden)
agent = Agent(role="Analyst", goal="Analyze", backstory="Expert")
# ↑ Secretly applied: allow_delegation=False, max_iter=1, verbose=False

crew = Crew(agents=[agent], tasks=[task])
# ↑ Secretly applied: max_iterations=1, timeout=600s, embedder=None
```

**Problems with this approach:**
- ❌ Hidden behavior - defaults not visible at construction site
- ❌ Brittle - breaks on CrewAI internal changes
- ❌ Hard to test - global state affects all tests
- ❌ Hard to override - monkey patches fight explicit parameters
- ❌ IDE confusion - autocomplete shows wrong signatures

### After (Explicit Factory Pattern)

```python
from app.services.crewai_flows.config.crew_factory import create_agent, create_crew

# Explicit configuration at creation time
agent = create_agent(
    role="Analyst",
    goal="Analyze data",
    backstory="Expert analyst",
    # Defaults applied explicitly: allow_delegation=False, max_iter=1, memory=True
)

crew = create_crew(
    agents=[agent],
    tasks=[task],
    # Defaults applied explicitly: max_iterations=1, timeout=600s, memory=True
)
```

**Benefits:**
- ✅ Explicit - see exactly what defaults are applied
- ✅ Testable - easy to mock factory or inject configs
- ✅ Flexible - override any default at creation time
- ✅ Maintainable - no global state modifications
- ✅ Compatible - works with CrewAI version upgrades
- ✅ IDE-friendly - proper autocomplete and type hints

## Migration Steps

### Step 1: Replace Agent Creation

**OLD:**
```python
from crewai import Agent

agent = Agent(
    role="Data Analyst",
    goal="Analyze migration data",
    backstory="Expert in data analysis",
    llm=my_llm,
    tools=[tool1, tool2],
)
# Monkey patch secretly applied: allow_delegation=False, max_iter=1
```

**NEW (Option 1 - Recommended):**
```python
from app.services.crewai_flows.config.crew_factory import create_agent

agent = create_agent(
    role="Data Analyst",
    goal="Analyze migration data",
    backstory="Expert in data analysis",
    llm=my_llm,
    tools=[tool1, tool2],
    # Defaults: allow_delegation=False, max_iter=1, memory=True
    # Override if needed:
    # max_iter=3,
    # allow_delegation=True,
)
```

**NEW (Option 2 - Factory Instance):**
```python
from app.services.crewai_flows.config.crew_factory import CrewFactory

factory = CrewFactory(enable_memory=True, verbose=False)

agent = factory.create_agent(
    role="Data Analyst",
    goal="Analyze migration data",
    backstory="Expert in data analysis",
    llm=my_llm,
    tools=[tool1, tool2],
)
```

**NEW (Option 3 - Advanced/Direct):**
```python
from crewai import Agent
from app.services.crewai_flows.config.crew_factory import CrewConfig
from app.services.crewai_flows.config.embedder_config import EmbedderConfig

# Get default configuration
config = CrewConfig.get_agent_defaults(memory=True)

# Add your specific settings
config.update({
    "role": "Data Analyst",
    "goal": "Analyze migration data",
    "backstory": "Expert in data analysis",
    "llm": my_llm,
    "tools": [tool1, tool2],
    "embedder": EmbedderConfig.get_embedder_for_crew(memory_enabled=True),
})

agent = Agent(**config)
```

### Step 2: Replace Crew Creation

**OLD:**
```python
from crewai import Crew, Process

crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    process=Process.sequential,
)
# Monkey patch secretly applied: max_iterations=1, timeout=600s
```

**NEW:**
```python
from crewai import Process
from app.services.crewai_flows.config.crew_factory import create_crew

crew = create_crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    process=Process.sequential,
    # Defaults: max_iterations=1, timeout=600s, memory=True
    # Override if needed:
    # max_execution_time=1200,  # 20 minutes
    # max_iterations=3,
)
```

### Step 3: Replace Task Creation

**OLD:**
```python
from crewai import Task

task = Task(
    description="Analyze the data",
    agent=analyst_agent,
    expected_output="Detailed analysis report",
)
```

**NEW:**
```python
from app.services.crewai_flows.config.crew_factory import create_task

task = create_task(
    description="Analyze the data",
    agent=analyst_agent,
    expected_output="Detailed analysis report",
    # Optional: async_execution=True, context=[other_tasks]
)
```

## Default Configurations

### Agent Defaults

```python
{
    "allow_delegation": False,  # No delegation between agents
    "max_delegation": 0,        # Explicit: no delegation chains
    "max_iter": 1,              # Single-pass execution
    "verbose": False,           # Quiet by default
    "memory": True,             # Memory enabled with DeepInfra embeddings
}
```

### Crew Defaults

```python
{
    "max_iterations": 1,              # Single crew iteration
    "verbose": False,                 # Quiet by default
    "max_execution_time": 600,        # 10 minutes (from CREWAI_TIMEOUT_SECONDS)
    "memory": True,                   # Memory enabled
    "embedder": <DeepInfra config>,   # From EmbedderConfig
}
```

## Environment Variables

Configure defaults via environment variables:

```bash
# Crew execution timeout (seconds)
CREWAI_TIMEOUT_SECONDS=600  # Default: 10 minutes

# Disable memory globally (not recommended)
CREWAI_DISABLE_MEMORY=false  # Default: false (memory enabled)

# Enable verbose logging
CREWAI_VERBOSE=false  # Default: false

# Embeddings configuration
DEEPINFRA_API_KEY=your_key_here  # Required for memory support
USE_OPENAI_EMBEDDINGS=false      # Default: false (use DeepInfra)
```

## Common Migration Patterns

### Pattern 1: Base Crew Class

**OLD:**
```python
from crewai import Agent, Crew, Task

class MyBaseCrew:
    def create_agent(self, role, goal, backstory):
        return Agent(role=role, goal=goal, backstory=backstory)
        # Monkey patch applied here

    def create_crew(self, agents, tasks):
        return Crew(agents=agents, tasks=tasks)
        # Monkey patch applied here
```

**NEW:**
```python
from app.services.crewai_flows.config.crew_factory import CrewFactory

class MyBaseCrew:
    def __init__(self):
        self.factory = CrewFactory(enable_memory=True)

    def create_agent(self, role, goal, backstory):
        return self.factory.create_agent(
            role=role,
            goal=goal,
            backstory=backstory,
        )

    def create_crew(self, agents, tasks):
        return self.factory.create_crew(
            agents=agents,
            tasks=tasks,
        )
```

### Pattern 2: Dynamic Agent Creation in Loops

**OLD:**
```python
agents = []
for role_config in agent_configs:
    agent = Agent(**role_config)  # Monkey patch applied
    agents.append(agent)
```

**NEW:**
```python
from app.services.crewai_flows.config.crew_factory import create_agent

agents = []
for role_config in agent_configs:
    agent = create_agent(**role_config)
    agents.append(agent)
```

### Pattern 3: Testing with Custom Configurations

**OLD:**
```python
def test_agent():
    # Had to work around monkey patches
    agent = Agent(role="Test", goal="Test", backstory="Test")
    # Forced defaults made testing specific behaviors hard
```

**NEW:**
```python
from app.services.crewai_flows.config.crew_factory import CrewFactory

def test_agent():
    # Full control over configuration
    factory = CrewFactory(enable_memory=False, verbose=True)
    agent = factory.create_agent(
        role="Test",
        goal="Test",
        backstory="Test",
        max_iter=5,  # Easy to override for specific tests
        allow_delegation=True,
    )
```

## Files Modified in This Migration

1. **Removed monkey patches:**
   - `backend/app/services/crewai_flows/crews/__init__.py` - No more global patches

2. **Created factory pattern:**
   - `backend/app/services/crewai_flows/config/crew_factory.py` - New factory implementation
   - `backend/app/services/crewai_flows/config/embedder_config.py` - Already existed, still used

3. **Example updates:**
   - `backend/app/services/persistent_agents/config/agent_wrapper.py` - Updated to use factory

## Backward Compatibility

### What Still Works

- **Embedder configuration (ADR-019):** The DeepInfra embeddings adapter is **NOT** affected by this change. It remains active and separate.
- **Environment variables:** All existing env vars still work the same way
- **Memory system:** Memory is still enabled by default with DeepInfra

### What Changed

- **Direct `Agent()` / `Crew()` calls:** No longer get automatic defaults
  - **Action:** Replace with `create_agent()` / `create_crew()`
- **Import side effects:** No more automatic patching at import time
  - **Action:** Explicitly call factory functions

## Rollout Strategy

This change requires updating crew implementations across the codebase. Recommended approach:

### Phase 1: Core Infrastructure (Completed)
- ✅ Remove monkey patches from `crews/__init__.py`
- ✅ Create `crew_factory.py` with factory pattern
- ✅ Update `agent_wrapper.py` as reference example
- ✅ Create migration documentation

### Phase 2: Update Existing Crews (In Progress)
- 🔄 Update crews in `backend/app/services/crewai_flows/crews/` directory
- 🔄 Update base crew classes (`optimized_crew_base.py`, `base_crew.py`)
- 🔄 Update agent implementations that create crews

### Phase 3: Verification
- Test all discovery flows end-to-end
- Test collection flows end-to-end
- Verify memory system still works with DeepInfra
- Check performance metrics (should be identical)

### Phase 4: Cleanup
- Remove any remaining direct `Agent()` / `Crew()` instantiations
- Add linting rules to prevent direct usage
- Update developer documentation

## Troubleshooting

### Issue: Agent/Crew not getting expected defaults

**Symptom:** Agent has delegation enabled, or crew times out quickly

**Cause:** Using direct `Agent()` / `Crew()` constructors instead of factory

**Fix:**
```python
# DON'T
from crewai import Agent
agent = Agent(role="Analyst", ...)  # No defaults applied!

# DO
from app.services.crewai_flows.config.crew_factory import create_agent
agent = create_agent(role="Analyst", ...)  # Defaults applied
```

### Issue: Memory not working

**Symptom:** Agents don't remember past interactions

**Cause:** Missing embedder configuration

**Fix:**
```python
# Ensure DEEPINFRA_API_KEY is set
# Factory automatically adds embedder config when memory=True

agent = create_agent(
    role="Analyst",
    goal="Analyze",
    backstory="Expert",
    memory=True,  # Default, but can be explicit
)
```

### Issue: Tests failing after migration

**Symptom:** Tests that relied on monkey patches now fail

**Cause:** Tests expected global defaults

**Fix:**
```python
# OLD TEST
def test_agent():
    agent = Agent(role="Test", ...)
    assert agent.allow_delegation is False  # Expected from monkey patch

# NEW TEST
from app.services.crewai_flows.config.crew_factory import create_agent

def test_agent():
    agent = create_agent(role="Test", ...)
    assert agent.allow_delegation is False  # Explicit from factory
```

## References

- **Code Review:** `docs/code-reviews/2025-10-01_discovery_flow_over_abstraction_review.md`
- **ADR-019:** CrewAI DeepInfra Embeddings (unchanged, still active)
- **Factory Implementation:** `backend/app/services/crewai_flows/config/crew_factory.py`
- **Embedder Config:** `backend/app/services/crewai_flows/config/embedder_config.py`

## Questions?

For questions or issues with this migration:
1. Check the migration guide examples above
2. Review `crew_factory.py` docstrings for detailed usage
3. Look at updated example in `agent_wrapper.py`
4. Search for `create_agent` / `create_crew` usage in codebase for patterns

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Configuration | Hidden (monkey patches) | Explicit (factory pattern) |
| Testability | Hard (global state) | Easy (inject config) |
| Maintainability | Brittle (patches internals) | Robust (uses public API) |
| Flexibility | Limited (patches override) | Full (override at creation) |
| Visibility | Poor (hidden at import) | Excellent (visible at call site) |
| Compatibility | Risky (version-dependent) | Safe (standard constructor params) |

**The factory pattern is a best practice for configuration management and significantly improves code quality.**
