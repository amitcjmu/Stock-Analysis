# Observability Patterns for LLM and Agent Tracking

**Last Updated**: 2025-11-12
**Status**: Mandatory for all new code (November 2025)
**Enforcement**: Pre-commit hooks + AST validation

## Overview

This system provides comprehensive observability for all LLM calls and CrewAI agent task executions. All tracking is **automatic** via LiteLLM callbacks and agent monitors, with pre-commit enforcement to prevent regressions.

### Why Observability Matters

1. **Cost Control**: Track LLM usage by model, provider, and feature to optimize spending
2. **Performance Monitoring**: Identify slow agents, bottlenecks, and optimization opportunities
3. **Quality Assurance**: Monitor success rates, error patterns, and agent reliability
4. **Multi-Tenant Insights**: Understand usage patterns per client and engagement
5. **Debugging**: Trace agent task execution flow with detailed logs and timestamps

### What We Track

| Layer | What | How | Where |
|-------|------|-----|-------|
| LLM Calls | All LiteLLM API calls | `litellm_tracking_callback.py` | `llm_usage_logs` table |
| Agent Tasks | CrewAI task execution | `CallbackHandler` + `agent_monitor` | `agent_task_history` table |
| Costs | Token usage + pricing | Automatic calculation | `llm_model_pricing` table |
| Performance | Response time, success rate | Built-in metrics | Grafana dashboards |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Call Flow                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. App Startup → setup_litellm_tracking()                 │
│     - Installs LLMUsageCallback globally                   │
│     - Hooks into LiteLLM success/failure events            │
│                                                             │
│  2. CrewAI Agent Calls LLM                                 │
│     ├── LiteLLM makes API call                             │
│     ├── LLMUsageCallback.log_success_event()               │
│     ├── Extract: provider, model, tokens, timing           │
│     └── Save to llm_usage_logs table                       │
│                                                             │
│  3. Alternative: Direct multi_model_service call           │
│     ├── multi_model_service.generate_response()            │
│     ├── Uses LiteLLM internally                            │
│     └── Same callback tracking applies                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Agent Task Flow                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Create CallbackHandler for flow                        │
│     CallbackHandlerIntegration.create_callback_handler()   │
│     - Attach client_account_id, engagement_id, flow_id     │
│                                                             │
│  2. Register task start                                    │
│     callback_handler._step_callback({                      │
│       "status": "starting",                                │
│       "agent": "readiness_assessor",                       │
│       "task": "readiness_assessment"                       │
│     })                                                      │
│     └── Creates row in agent_task_history                  │
│                                                             │
│  3. Execute task                                           │
│     task.execute_async(context=context)                    │
│     - Automatic LLM call tracking via LiteLLM callback     │
│                                                             │
│  4. Mark completion                                        │
│     callback_handler._task_completion_callback({           │
│       "agent": "readiness_assessor",                       │
│       "status": "completed",                               │
│       "task_name": "readiness_assessment"                  │
│     })                                                      │
│     └── Updates agent_task_history with result            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## LLM Call Tracking (Automatic)

### How It Works

**All LLM calls are automatically tracked** via `litellm_tracking_callback.py`. This callback is installed at app startup and hooks into LiteLLM's global success/failure events.

### Setup (Already Done)

The callback is installed in `app/app_setup/lifecycle.py:113-120`:

```python
from app.services.litellm_tracking_callback import setup_litellm_tracking

# At app startup
setup_litellm_tracking()
# ✅ All LLM calls now tracked automatically
```

### What Gets Tracked

For every LLM call:
- **Provider**: `deepinfra`, `openai`, `anthropic`, etc.
- **Model**: Full model name (e.g., `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`)
- **Tokens**: `input_tokens`, `output_tokens`, `total_tokens`
- **Cost**: Calculated from `llm_model_pricing` table
- **Timing**: `response_time_ms` (milliseconds)
- **Success**: Boolean flag + error details on failure
- **Context**: `feature_context` (e.g., `crewai`, `field_mapping`)
- **Tenant**: `client_account_id`, `engagement_id` (when available)

### Database Schema

**Table**: `migration.llm_usage_logs`

```sql
CREATE TABLE migration.llm_usage_logs (
    id SERIAL PRIMARY KEY,
    flow_id UUID,
    client_account_id INTEGER,
    engagement_id INTEGER,
    llm_provider VARCHAR(50) NOT NULL,  -- deepinfra, openai, anthropic
    llm_model VARCHAR(255) NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost NUMERIC(10, 6),  -- Calculated from pricing
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_type VARCHAR(100),
    error_message TEXT,
    feature_context VARCHAR(100),  -- crewai, field_mapping, etc.
    additional_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Provider Detection

The callback uses multiple fallback strategies to detect the provider:

```python
# Strategy 1: LiteLLM's own detection (most reliable)
provider = response_obj._hidden_params.get("custom_llm_provider", "unknown")

# Strategy 2: Extract from kwargs
if provider == "unknown":
    provider = kwargs["litellm_params"].get("custom_llm_provider", "unknown")

# Strategy 3: Pattern matching on model name
if provider == "unknown":
    if model.startswith("meta-llama/") or model.startswith("google/"):
        provider = "deepinfra"  # DeepInfra hosts these models
    elif "gpt" in model.lower():
        provider = "openai"
```

### Cost Calculation

Costs are **automatically calculated** by joining with the `llm_model_pricing` table:

**Table**: `migration.llm_model_pricing`

```sql
CREATE TABLE migration.llm_model_pricing (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(255) NOT NULL,
    cost_per_1k_input_tokens NUMERIC(10, 6) NOT NULL,
    cost_per_1k_output_tokens NUMERIC(10, 6) NOT NULL,
    effective_date DATE DEFAULT CURRENT_DATE,
    UNIQUE(provider, model, effective_date)
);
```

Example pricing:
```sql
INSERT INTO migration.llm_model_pricing (provider, model, cost_per_1k_input_tokens, cost_per_1k_output_tokens)
VALUES
    ('deepinfra', 'meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8', 0.0001, 0.0002),
    ('deepinfra', 'google/gemma-3-4b-it', 0.00005, 0.00010);
```

### Legacy Code Pattern

If you find **direct LiteLLM calls** in legacy code, they are already tracked via the global callback. No changes needed unless you want to add tenant context:

```python
# ❌ This is legacy but already tracked
response = litellm.completion(model="deepinfra/llama-4", messages=[...])
# ✅ LiteLLM callback automatically logs this

# ✅ Better: Add tenant context to metadata
response = litellm.completion(
    model="deepinfra/llama-4",
    messages=[...],
    metadata={
        "feature_context": "readiness_assessment",
        "client_account_id": 1,
        "engagement_id": 123
    }
)
```

### Preferred Pattern: multi_model_service

For **new code**, always use `multi_model_service` for best tenant context:

```python
from app.services.multi_model_service import multi_model_service, TaskComplexity

# ✅ CORRECT - Automatic tracking + tenant context
response = await multi_model_service.generate_response(
    prompt="Your prompt here",
    task_type="chat",  # or "field_mapping", "analysis", etc.
    complexity=TaskComplexity.SIMPLE,  # or AGENTIC for complex tasks
    client_account_id=1,
    engagement_id=123
)
```

**Benefits**:
- ✅ Automatic logging to `llm_usage_logs`
- ✅ Correct model selection (Gemma 3 for chat, Llama 4 for agentic)
- ✅ Cost calculation included
- ✅ Multi-tenant context (client_account_id, engagement_id)
- ✅ Performance metrics (response time, success rate)

## Agent Task Tracking (Manual Integration Required)

### Why Manual Integration?

Unlike LLM calls (which are automatic), **agent task tracking requires explicit CallbackHandler integration** because:
1. Tasks have complex lifecycles (starting → running → completed/failed)
2. Task context varies by flow type (discovery, assessment, collection)
3. Need to capture task-specific metadata (phase, agent name, task objectives)

### Pattern: CrewAI Task Execution

**MANDATORY for all CrewAI task execution**:

```python
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration
)

# 1. Create callback handler with tenant context
callback_handler = CallbackHandlerIntegration.create_callback_handler(
    flow_id=str(master_flow.flow_id),
    context={
        "client_account_id": str(master_flow.client_account_id),
        "engagement_id": str(master_flow.engagement_id),
        "flow_type": "assessment",  # or "discovery", "collection"
        "phase": "readiness"  # Current phase/step
    }
)
callback_handler.setup_callbacks()

# 2. Create task
task = Task(
    description="Assess cloud readiness for selected applications",
    expected_output="Readiness assessment report with scores and gaps",
    agent=(agent._agent if hasattr(agent, "_agent") else agent)
)

# 3. Register task start BEFORE execution
callback_handler._step_callback({
    "type": "starting",
    "status": "starting",
    "agent": "readiness_assessor",
    "task": "readiness_assessment",
    "content": "Starting readiness assessment for 5 applications"
})

# 4. Execute task
future = task.execute_async(context=context_str)
result = await asyncio.wrap_future(future)

# 5. Mark completion with result status
callback_handler._task_completion_callback({
    "agent": "readiness_assessor",
    "task_name": "readiness_assessment",
    "status": "completed" if result else "failed",
    "task_id": "readiness_task",
    "output": result if result else "Task failed"
})
```

### Database Schema

**Table**: `migration.agent_task_history`

```sql
CREATE TABLE migration.agent_task_history (
    id SERIAL PRIMARY KEY,
    task_id UUID NOT NULL,
    flow_id UUID,
    client_account_id INTEGER,
    engagement_id INTEGER,
    agent_name VARCHAR(255) NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(50),  -- starting, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    input_context JSONB,
    output_result JSONB,
    error_details JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### What Gets Tracked

For every agent task:
- **Task ID**: Unique identifier for this task execution
- **Agent Name**: Which agent executed the task (e.g., `readiness_assessor`)
- **Task Name**: What task was executed (e.g., `readiness_assessment`)
- **Status**: `starting` → `running` → `completed`/`failed`
- **Timing**: `started_at`, `completed_at`, `duration_ms`
- **Context**: Input data provided to the task (JSONB)
- **Result**: Output from the task (JSONB)
- **Tenant**: `client_account_id`, `engagement_id`, `flow_id`

### Example: Assessment Flow Executor

```python
# File: backend/app/services/flow_orchestration/execution_engine_crew_assessment/readiness_executor.py

from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration
)

async def execute_readiness_assessment_phase(
    self,
    master_flow: CrewAIFlowStateExtension,
    selected_apps: List[Asset]
) -> Dict[str, Any]:
    """Execute readiness assessment with monitoring."""

    # Create callback handler
    callback_handler = CallbackHandlerIntegration.create_callback_handler(
        flow_id=str(master_flow.flow_id),
        context={
            "client_account_id": str(master_flow.client_account_id),
            "engagement_id": str(master_flow.engagement_id),
            "flow_type": "assessment",
            "phase": "readiness",
            "app_count": len(selected_apps)
        }
    )
    callback_handler.setup_callbacks()

    # Get agent from pool
    agent = await self.agent_pool.get_agent("readiness_assessor")

    # Build context
    context_str = self._build_readiness_context(selected_apps)

    # Create task
    task = Task(
        description=f"Assess cloud readiness for {len(selected_apps)} applications",
        expected_output="Readiness scores (0-100) with gap analysis",
        agent=(agent._agent if hasattr(agent, "_agent") else agent)
    )

    # Register task start
    callback_handler._step_callback({
        "type": "starting",
        "status": "starting",
        "agent": "readiness_assessor",
        "task": "readiness_assessment",
        "content": f"Assessing {len(selected_apps)} applications for cloud readiness"
    })

    # Execute task (LLM calls automatically tracked)
    try:
        future = task.execute_async(context=context_str)
        result = await asyncio.wrap_future(future)

        # Mark completion
        callback_handler._task_completion_callback({
            "agent": "readiness_assessor",
            "task_name": "readiness_assessment",
            "status": "completed",
            "task_id": "readiness_task",
            "output": result
        })

        return {"status": "completed", "result": result}
    except Exception as e:
        # Mark failure
        callback_handler._task_completion_callback({
            "agent": "readiness_assessor",
            "task_name": "readiness_assessment",
            "status": "failed",
            "task_id": "readiness_task",
            "error": str(e)
        })
        raise
```

## Dashboard Access

All observability data is visualized in Grafana dashboards:

### 1. LLM Costs Dashboard
**URL**: http://localhost:9999/d/llm-costs/

**Panels**:
- Total cost over time (time series)
- Cost by provider (pie chart)
- Cost by model (bar chart)
- Top 10 most expensive calls (table)
- Token usage trends (time series)

### 2. Agent Activity Dashboard
**URL**: http://localhost:9999/d/agent-activity/

**Panels**:
- Agent calls over time (time series)
- Top agents by token usage (bar chart)
- Agent response times (gauge)
- Agent success rate (stat)
- Active agents (table)

### 3. CrewAI Flows Dashboard
**URL**: http://localhost:9999/d/crewai-flows/

**Panels**:
- Flows by type (pie chart: discovery, assessment, collection)
- Average tokens per flow type (table)
- Flow execution duration (histogram)
- Failed flows (time series)

### Grafana Access

- **URL**: http://localhost:9999
- **Username**: admin
- **Password**: admin (change on first login)
- **Data Source**: PostgreSQL (pre-configured to `migration_db`)

### Example Queries

**LLM costs for last 7 days**:
```sql
SELECT
  date_trunc('day', created_at) AS time,
  SUM(total_cost) AS total_cost,
  llm_provider
FROM migration.llm_usage_logs
WHERE created_at > NOW() - INTERVAL '7 days'
  AND total_cost IS NOT NULL
GROUP BY 1, 3
ORDER BY 1
```

**Agent success rate**:
```sql
SELECT
  ROUND(
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::numeric /
    COUNT(*)::numeric * 100,
    2
  ) AS success_rate_pct
FROM migration.llm_usage_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
  AND feature_context = 'crewai'
```

## Pre-Commit Enforcement

### How It Works

A pre-commit hook runs **AST-based validation** on all staged Python files to detect observability violations before commit.

### What Gets Checked

The pre-commit script (`backend/scripts/check_llm_observability.py`) detects:

1. **CRITICAL**: `task.execute_async()` without `CallbackHandler` in scope
2. **ERROR**: Direct `litellm.completion()` calls (should use `multi_model_service`)
3. **WARNING**: `crew.kickoff()` without `callbacks` parameter

### Setup (Post-Phase 4)

Add to `backend/.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: check-llm-observability
        name: Check LLM Observability
        entry: python backend/scripts/check_llm_observability.py
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

### Example Violations

```
❌ LLM Observability Violations Found:

📁 backend/app/services/flow_orchestration/execution_engine_crew_assessment/readiness_executor.py
  🚨 Line 145: task.execute_async() called without CallbackHandler [CRITICAL]
  ⚠️  Line 67: Direct litellm.completion() call - use multi_model_service instead [ERROR]

Fix these violations before committing.

Guidance:
  - Use CallbackHandler for CrewAI task execution
  - Use multi_model_service.generate_response() for LLM calls
  - See docs/guidelines/OBSERVABILITY_PATTERNS.md
```

### Fixing Violations

**CRITICAL: task.execute_async() without CallbackHandler**

```python
# ❌ BLOCKED by pre-commit
task = Task(...)
result = await task.execute_async()

# ✅ CORRECT - Import and setup callback handler
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration
)

callback_handler = CallbackHandlerIntegration.create_callback_handler(
    flow_id=str(flow_id),
    context={...}
)
callback_handler.setup_callbacks()

# Register start
callback_handler._step_callback({...})

# Execute task
result = await task.execute_async()

# Mark completion
callback_handler._task_completion_callback({...})
```

**ERROR: Direct litellm.completion() call**

```python
# ❌ BLOCKED by pre-commit
response = litellm.completion(model="deepinfra/llama-4", messages=[...])

# ✅ CORRECT - Use multi_model_service
from app.services.multi_model_service import multi_model_service, TaskComplexity

response = await multi_model_service.generate_response(
    prompt="Your prompt",
    task_type="analysis",
    complexity=TaskComplexity.SIMPLE
)
```

## Examples

### Example 1: Assessment Flow Executor with Full Instrumentation

```python
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration
)
from app.services.multi_model_service import multi_model_service, TaskComplexity

async def execute_complexity_analysis(
    self,
    master_flow: CrewAIFlowStateExtension,
    selected_apps: List[Asset]
) -> Dict[str, Any]:
    """Execute complexity analysis with full observability."""

    # Step 1: Create callback handler
    callback_handler = CallbackHandlerIntegration.create_callback_handler(
        flow_id=str(master_flow.flow_id),
        context={
            "client_account_id": str(master_flow.client_account_id),
            "engagement_id": str(master_flow.engagement_id),
            "flow_type": "assessment",
            "phase": "complexity",
            "app_count": len(selected_apps)
        }
    )
    callback_handler.setup_callbacks()

    # Step 2: Get agent
    agent = await self.agent_pool.get_agent("complexity_analyzer")

    # Step 3: Build context
    context_data = {
        "applications": [app.to_dict() for app in selected_apps],
        "analysis_objectives": [
            "Calculate technical complexity score (0-100)",
            "Identify architecture patterns",
            "Assess dependency complexity",
            "Evaluate data migration complexity"
        ]
    }

    # Step 4: Create task
    task = Task(
        description=f"Analyze technical complexity for {len(selected_apps)} applications",
        expected_output="Complexity scores with breakdown by category",
        agent=(agent._agent if hasattr(agent, "_agent") else agent)
    )

    # Step 5: Generate unique task ID per execution (prevents ID collisions)
    import uuid
    task_id = str(uuid.uuid4())

    # Step 6: Register task start BEFORE execution
    callback_handler._step_callback({
        "type": "starting",
        "status": "starting",
        "agent": "complexity_analyzer",
        "task": "complexity_analysis",
        "task_id": task_id,
        "content": f"Analyzing {len(selected_apps)} applications for complexity"
    })

    # Step 7: Execute task
    try:
        future = task.execute_async(context=str(context_data))
        result = await asyncio.wrap_future(future)

        # Step 8: Mark success
        callback_handler._task_completion_callback({
            "agent": "complexity_analyzer",
            "task_name": "complexity_analysis",
            "status": "completed",
            "task_id": task_id,
            "output": result
        })

        logger.info(f"✅ Complexity analysis completed for {len(selected_apps)} apps")
        return {"status": "completed", "result": result}

    except Exception as e:
        # Step 9: Mark failure
        callback_handler._task_completion_callback({
            "agent": "complexity_analyzer",
            "task_name": "complexity_analysis",
            "status": "failed",
            "task_id": task_id,
            "error": str(e)
        })
        logger.error(f"❌ Complexity analysis failed: {e}")
        raise
```

### Example 2: Direct LLM Call with Tenant Context

```python
from app.services.multi_model_service import multi_model_service, TaskComplexity

async def generate_field_mapping_suggestion(
    source_field: str,
    target_schema: Dict[str, Any],
    client_account_id: int,
    engagement_id: int
) -> Dict[str, Any]:
    """Generate field mapping suggestion with observability."""

    # Build prompt
    prompt = f"""
    Suggest a mapping for source field '{source_field}' to target schema:
    {json.dumps(target_schema, indent=2)}

    Provide:
    1. Best target field name
    2. Confidence score (0-100)
    3. Transformation logic (if needed)
    4. Rationale
    """

    # Call LLM with automatic tracking
    response = await multi_model_service.generate_response(
        prompt=prompt,
        task_type="field_mapping",
        complexity=TaskComplexity.SIMPLE,  # Simple chat task
        client_account_id=client_account_id,
        engagement_id=engagement_id
    )

    # ✅ Automatically logged to llm_usage_logs with:
    # - provider, model, tokens, cost
    # - client_account_id, engagement_id
    # - feature_context="field_mapping"

    return parse_mapping_response(response)
```

### Example 3: Legacy Code with Metadata

```python
import litellm

# Legacy code that can't be refactored yet
async def legacy_llm_call(messages: List[Dict], flow_id: str):
    """Legacy LLM call with tenant context."""

    # ✅ Add metadata for tenant context
    response = litellm.completion(
        model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=messages,
        metadata={
            "feature_context": "legacy_feature",
            "flow_id": flow_id,
            "client_account_id": 1,  # Extract from context
            "engagement_id": 123
        }
    )

    # ✅ Still tracked by LiteLLM callback (no changes needed)
    return response
```

## Troubleshooting

### Issue: Grafana shows no data for LLM costs

**Symptoms**: LLM Costs dashboard is empty despite LLM calls happening

**Diagnosis**:
1. Check if callback is installed:
   ```python
   from app.services.litellm_tracking_callback import is_litellm_tracking_enabled
   print(is_litellm_tracking_enabled())  # Should be True
   ```

2. Check database for logs:
   ```sql
   SELECT COUNT(*), llm_provider
   FROM migration.llm_usage_logs
   WHERE created_at > NOW() - INTERVAL '1 hour'
   GROUP BY llm_provider;
   ```

3. Check for provider='unknown':
   ```sql
   SELECT COUNT(*)
   FROM migration.llm_usage_logs
   WHERE llm_provider = 'unknown';
   ```

**Fixes**:
- If provider='unknown', run backfill script: `python backend/scripts/backfill_llm_costs.py`
- If no logs at all, check callback installation in `lifecycle.py`
- If callback disabled, restart backend: `docker restart migration_backend`

### Issue: Agent Activity dashboard shows no tasks

**Symptoms**: Agent Activity dashboard is empty but flows are executing

**Diagnosis**:
1. Check if CallbackHandler is being created:
   ```bash
   docker logs migration_backend | grep "Created callback handler"
   # Should see: ✅ Created callback handler for flow <uuid>
   ```

2. Check database for task history:
   ```sql
   SELECT COUNT(*), agent_name, status
   FROM migration.agent_task_history
   WHERE created_at > NOW() - INTERVAL '1 hour'
   GROUP BY agent_name, status;
   ```

3. Check for missing instrumentation:
   ```bash
   cd backend
   python scripts/check_llm_observability.py
   # Will show files missing CallbackHandler
   ```

**Fixes**:
- If no logs, executor is missing CallbackHandler integration (see Pattern above)
- If callback created but no DB rows, check `agent_monitor` service is running
- If pre-commit shows violations, fix them and re-run flow

### Issue: Pre-commit hook blocks valid code

**Symptoms**: Pre-commit hook reports false positive violations

**Diagnosis**:
1. Check if CallbackHandler import is present:
   ```python
   from app.services.crewai_flows.handlers.callback_handler_integration import (
       CallbackHandlerIntegration
   )
   ```

2. Verify callback is created in same function:
   ```python
   callback_handler = CallbackHandlerIntegration.create_callback_handler(...)
   ```

**Fixes**:
- AST parser requires CallbackHandler import in same file as `task.execute_async()`
- If using helper function, import CallbackHandler there too
- If false positive persists, add `# noqa: observability` comment (use sparingly)

### Issue: LLM costs showing NULL

**Symptoms**: `llm_usage_logs.total_cost` is NULL despite tokens being tracked

**Diagnosis**:
1. Check pricing table has entry for model:
   ```sql
   SELECT * FROM migration.llm_model_pricing
   WHERE provider = 'deepinfra'
     AND model LIKE '%llama-4%';
   ```

2. Check provider detection:
   ```sql
   SELECT DISTINCT llm_provider, llm_model
   FROM migration.llm_usage_logs
   WHERE total_cost IS NULL
   LIMIT 10;
   ```

**Fixes**:
- If pricing missing, insert into `llm_model_pricing` table
- If provider='unknown', run backfill script to recalculate
- If new model, add pricing entry with current rates

### Issue: Task stuck in "starting" status

**Symptoms**: `agent_task_history.status = 'starting'` never becomes 'completed'

**Diagnosis**:
1. Check if `_task_completion_callback()` is being called:
   ```bash
   docker logs migration_backend | grep "task_completion_callback"
   ```

2. Check for exceptions during task execution:
   ```bash
   docker logs migration_backend | grep "Task failed"
   ```

**Fixes**:
- Ensure `_task_completion_callback()` is in try/finally block
- Add exception handler to mark task as 'failed' on errors
- Check if task is running async without await (common mistake)

## Reference

### Key Files

| File | Purpose | Location |
|------|---------|----------|
| LiteLLM Callback | Automatic LLM tracking | `backend/app/services/litellm_tracking_callback.py` |
| Callback Handler | Agent task tracking | `backend/app/services/crewai_flows/handlers/callback_handler.py` |
| Integration Helper | Create handlers with context | `backend/app/services/crewai_flows/handlers/callback_handler_integration.py` |
| Multi-Model Service | Preferred LLM API | `backend/app/services/multi_model_service.py` |
| Pre-Commit Check | AST-based enforcement | `backend/scripts/check_llm_observability.py` |
| Lifecycle Setup | Install callback at startup | `backend/app/app_setup/lifecycle.py:113-120` |

### Database Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| llm_usage_logs | All LLM API calls | provider, model, tokens, cost, success |
| llm_model_pricing | Cost per 1K tokens | provider, model, cost_per_1k_input, cost_per_1k_output |
| agent_task_history | CrewAI task execution | task_id, agent_name, status, duration_ms |
| llm_usage_summary | Aggregated stats | total_tokens, total_cost, avg_response_time |

### Grafana Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| LLM Costs | /d/llm-costs/ | Cost tracking by model/provider |
| Agent Activity | /d/agent-activity/ | Agent performance and usage |
| CrewAI Flows | /d/crewai-flows/ | Flow execution metrics |

### Related Documentation

- `/docs/guidelines/OBSERVABILITY_ENFORCEMENT_PLAN.md` - Full implementation plan
- `/OBSERVABILITY_IMPLEMENTATION_PROGRESS.md` - Current status and rollout
- `/CLAUDE.md` - Project-wide guidelines (includes observability mandate)
- `/docs/adr/024-tenant-memory-manager-architecture.md` - Agent memory architecture

## Enforcement Policy

### Mandatory Patterns (November 2025+)

1. **All new CrewAI task execution MUST use CallbackHandler**
   - Pre-commit hook will block commits without it
   - Existing code exempt until refactored

2. **All new LLM calls SHOULD use multi_model_service**
   - Direct litellm calls flagged as WARNING (not blocked)
   - Legacy code with LiteLLM still tracked via global callback

3. **All dashboard queries MUST use migration schema**
   - Query `migration.llm_usage_logs`, NOT `public.llm_usage_logs`
   - Join with `migration.llm_model_pricing` for costs

### Migration Timeline

- **Phase 1** (Completed): Fix provider detection + backfill costs
- **Phase 2** (In Progress): Create Grafana dashboards
- **Phase 3** (Pending): Wire CallbackHandler into all executors
- **Phase 4** (Pending): Enable pre-commit enforcement
- **Phase 5** (Current): Documentation and training
- **Phase 6** (Planned): Testing and validation

### Exemptions

Observability enforcement does NOT apply to:
- Test code (`backend/tests/`)
- Migration scripts (`backend/alembic/versions/`)
- Utility scripts (`backend/scripts/`) unless they call LLMs
- Legacy code before November 2025 (but encouraged to adopt)

## Summary

This observability system provides **automatic LLM tracking** via LiteLLM callbacks and **manual agent task tracking** via CallbackHandler integration. All data flows to PostgreSQL tables and is visualized in Grafana dashboards.

**Key Takeaways**:
1. LLM calls are automatically tracked - no action needed for basic tracking
2. Agent tasks require explicit CallbackHandler integration
3. Use `multi_model_service` for new code to get best tenant context
4. Pre-commit hooks enforce observability patterns
5. Grafana dashboards provide real-time visibility into costs and performance

For questions or issues, see Troubleshooting section or consult `/docs/guidelines/OBSERVABILITY_ENFORCEMENT_PLAN.md`.
