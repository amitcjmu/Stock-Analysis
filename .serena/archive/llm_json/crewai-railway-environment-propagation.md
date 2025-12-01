# CrewAI Environment Variable Propagation in Async Tasks (Railway)

**Problem**: Production (Railway) showing "Error importing native provider: OPENAI_API_KEY is required" during background flow execution

**Root Cause**:
- CrewAI's `_llm_via_environment_or_fallback()` requires `OPENAI_API_KEY`
- Lifecycle shim sets env vars at startup, but Railway async tasks don't inherit them
- Background tasks run in isolated contexts without parent process env vars

**Solution**: Create reusable environment setup function called at execution boundaries

**Code**:
```python
# backend/app/core/crewai_env_setup.py
def ensure_crewai_environment() -> None:
    """Call before ANY CrewAI code in background tasks"""
    deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
    if not deepinfra_key:
        raise ValueError("DEEPINFRA_API_KEY environment variable not set")

    existing_openai_key = os.getenv("OPENAI_API_KEY")
    if not existing_openai_key:
        os.environ["OPENAI_API_KEY"] = deepinfra_key
        os.environ["OPENAI_API_BASE"] = "https://api.deepinfra.com/v1/openai"

# Usage in background tasks
async def _run_discovery_flow(...):
    from app.core.crewai_env_setup import ensure_crewai_environment
    ensure_crewai_environment()

    # Now safe to create CrewAI flows/agents
    discovery_flow = create_unified_discovery_flow(...)
```

**Usage**: Call `ensure_crewai_environment()` at entry point of ANY:
- Background task via `asyncio.create_task()`
- Async handler in separate execution context
- Isolated worker process

**Railway-Specific**: Environment variables set in parent process don't automatically propagate to `asyncio.create_task()` contexts.

**Files Modified**:
- `backend/app/core/crewai_env_setup.py` (NEW)
- `backend/app/services/data_import/background_execution_service/core.py` (lines 161-164, 284-287)
