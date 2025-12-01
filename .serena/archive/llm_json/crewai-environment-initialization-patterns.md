# CrewAI Environment Initialization - Critical Patterns

## Problem: OPENAI_API_KEY Required Errors in Production

**Symptom**: `Error importing native provider: OPENAI_API_KEY is required`

**Root Cause**: CrewAI falls back to environment variables when:
1. LLM initialization fails
2. Agent creation occurs without explicit LLM config
3. Flow configs import CrewAI modules that instantiate LLMs

**Critical Locations Where This Occurs**:

### 1. MasterFlowOrchestrator Initialization
```python
# backend/app/services/master_flow_orchestrator/core.py:90-94
from app.services.flow_configs import initialize_all_flows
result = initialize_all_flows()  # ← Instantiates LLMs
```

**Error Path**: `import_storage_handler.py` → `MasterFlowOrchestrator()` → `initialize_all_flows()` → CrewAI LLM fallback

### 2. Background Task Execution
```python
# backend/app/services/data_import/background_execution_service/core.py
from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
discovery_flow = create_unified_discovery_flow(...)  # ← May instantiate LLMs
```

### 3. Persistent Agent Creation
```python
# backend/app/services/persistent_agents/config/manager.py
from crewai import Agent
agent = Agent(...)  # ← Falls back to env if llm=None
```

## Solution Pattern: ensure_crewai_environment()

**Location**: `backend/app/core/crewai_env_setup.py`

```python
def ensure_crewai_environment() -> None:
    """
    Set OPENAI_API_KEY from DEEPINFRA_API_KEY for CrewAI compatibility.
    Must be called BEFORE any CrewAI code that might instantiate LLMs.
    """
    deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
    if not deepinfra_key:
        raise ValueError("DEEPINFRA_API_KEY not set")

    if not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = deepinfra_key
        os.environ["OPENAI_API_BASE"] = "https://api.deepinfra.com/v1/openai"
        os.environ["OPENAI_BASE_URL"] = "https://api.deepinfra.com/v1/openai"
```

## Required Coverage (All Four Paths)

### 1. Application Startup
```python
# backend/app/app_setup/lifecycle.py
# Run once at startup - covers most cases
ensure_crewai_environment()
```

### 2. Data Import Transaction Phase
```python
# backend/app/services/data_import/import_storage_handler.py:290
# CRITICAL: Before MasterFlowOrchestrator creation
from app.core.crewai_env_setup import ensure_crewai_environment

ensure_crewai_environment()
orchestrator = MasterFlowOrchestrator(self.db, context)
```

### 3. Background Execution
```python
# backend/app/services/data_import/background_execution_service/core.py:163
# Before creating CrewAI flows in async tasks
ensure_crewai_environment()
discovery_flow = create_unified_discovery_flow(...)
```

### 4. Agent Creation Failsafe
```python
# backend/app/services/persistent_agents/config/manager.py
# Before each agent instantiation
ensure_crewai_environment()
agent = Agent(...)
```

## Why Multiple Calls Are Needed

**Environment Variable Inheritance Issues**:
- Railway/Vercel async tasks don't inherit startup env vars
- Transaction boundaries create new execution contexts
- Background tasks run in separate processes/threads

**Idempotent Design**: `ensure_crewai_environment()` safely no-ops if already set

## Diagnostic Commands

```bash
# Find where error occurs (shows CrewAI's llm_utils.py)
docker exec migration_backend bash -c "cd /app && grep -r 'Error instantiating LLM' ."

# Check git history for when initialize_all_flows was added
git blame backend/app/services/master_flow_orchestrator/core.py | grep "initialize_all_flows"

# Find all MFO instantiation points
grep -r "MasterFlowOrchestrator(" backend/
```

## Historical Bug Timeline

1. **Aug 21, 2025**: `initialize_all_flows()` added to MFO.__init__ (c29baeca9b)
2. **Oct 27, 2025**: First fix - startup + agent creation (31d2e9c99)
3. **Oct 30, 2025**: Second fix - background execution (03e4a67d9)
4. **Nov 4, 2025**: Final fix - data import transaction (34b947b67)

## Pattern: Always Check Transaction Boundaries

When fixing environment issues:
1. ✅ Check startup initialization
2. ✅ Check background tasks
3. ✅ **Check transaction phases** (often missed!)
4. ✅ Check agent/crew creation points

Transaction-scoped code may not inherit startup env vars.
