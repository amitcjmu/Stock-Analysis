# AgentWrapper Pydantic Validation Fix (October 2025)

**Problem**: CrewAI Task constructor fails with Pydantic v2 validation error when AgentWrapper is passed directly.

**Error**:
```
1 validation error for Task
agent
  Input should be a valid dictionary or instance of BaseAgent
  [type=model_type, input_value=<AgentWrapper object>, input_type=AgentWrapper]
```

**Root Cause**: Pydantic v2 strict validation requires `BaseAgent` instance, not wrapper classes. AgentWrapper uses composition pattern to wrap CrewAI agents, but Task expects the underlying agent.

## Solution Pattern

Unwrap AgentWrapper before passing to Task constructor:

```python
# ❌ WRONG - Causes Pydantic validation error
task = Task(
    description="Process data",
    agent=agent,  # agent is AgentWrapper
    expected_output="Results"
)

# ✅ CORRECT - Unwrap to BaseAgent
task = Task(
    description="Process data",
    agent=agent._agent if hasattr(agent, '_agent') else agent,
    expected_output="Results"
)
```

## Files Fixed in This Session

1. **backend/app/services/persistent_agents/config/agent_wrapper.py**
   - Lines 80, 166: `agent=self._agent` (was `agent=self`)

2. **All 6 Assessment Executors**:
   - `complexity_executor.py:79`
   - `dependency_executor.py:79`
   - `readiness_executor.py:74`
   - `recommendation_executor.py:81`
   - `risk_executor.py:75`
   - `tech_debt_executor.py:81`

Pattern applied:
```python
task = Task(
    description=f"Analyze {self.phase_name}...",
    expected_output="Structured analysis results",
    agent=agent._agent if hasattr(agent, '_agent') else agent,  # Unwrap
)
```

## When to Apply

**Use this pattern when**:
- Creating CrewAI Task instances with agents from TenantScopedAgentPool
- Agent retrieval returns AgentWrapper objects
- Pydantic validation errors mention "Input should be a valid dictionary or instance of BaseAgent"

**Safe checks**:
```python
# Defensive unwrapping
unwrapped_agent = agent._agent if hasattr(agent, '_agent') else agent

# Or in crew_factory create_task
def create_task(agent, description, expected_output):
    actual_agent = agent._agent if hasattr(agent, '_agent') else agent
    return Task(agent=actual_agent, description=description, expected_output=expected_output)
```

## Why AgentWrapper Exists

AgentWrapper adds execution methods (`execute()`, `execute_async()`, `process()`) to CrewAI agents without modifying BaseAgent fields (Pydantic v2 constraint). It's the compatibility layer between our async agent pool and CrewAI's synchronous Task system.

## Related Patterns

- **TenantScopedAgentPool**: Returns AgentWrapper instances from `get_agent()`
- **crew_factory.create_task()**: Should unwrap agents internally (lines 76-82)
- **Executor base classes**: All inherit this unwrapping pattern

**Commits**:
- `91eed767d` - Initial AgentWrapper fix (agent_wrapper.py)
- `25c608537` - Executor fixes (6 assessment executors)

**Date**: October 2025
