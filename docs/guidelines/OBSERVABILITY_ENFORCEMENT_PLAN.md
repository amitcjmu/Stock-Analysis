# Observability Enforcement Implementation Plan

**Date**: 2025-11-12
**Issue**: Grafana dashboards showing no data
**Root Cause**: Provider detection bug + Missing agent task instrumentation
**Solution**: Hybrid approach with automated enforcement

## Phase 1: Fix LLM Cost Tracking ✅ COMPLETED

### Issues Found
1. **Provider detection bug** in `litellm_tracking_callback.py`
   - Model name `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` didn't match `deepinfra`
   - Resulted in `llm_provider='unknown'` for 1,569 recent calls
   - Pricing lookup failed → `total_cost=NULL`

### Fix Applied
- **File**: `backend/app/services/litellm_tracking_callback.py:48-77, 152-172`
- **Changes**:
  - Extract provider from LiteLLM's `response_obj._hidden_params`
  - Fallback to `kwargs["litellm_params"]["custom_llm_provider"]`
  - Pattern matching for `meta-llama/`, `google/`, `mistralai/` → `deepinfra`
- **Status**: ✅ Fixed, backend restarted

### Backfill Required
- 1,569 rows with `llm_provider='unknown'` need cost recalculation
- Script: `backend/scripts/backfill_llm_costs.py` (to be created)

## Phase 2: Create Log-Based Agent Dashboards (NEXT)

### New Grafana Dashboards

#### Dashboard 1: Agent Activity (from llm_usage_logs)
**File**: `config/docker/observability/grafana/dashboards/agent-activity.json`

**Panels**:
1. **Agent Calls Over Time** (time series)
   ```sql
   SELECT
     date_trunc('hour', created_at) AS time,
     COUNT(*) AS calls
   FROM migration.llm_usage_logs
   WHERE $__timeFilter(created_at)
     AND feature_context = 'crewai'
   GROUP BY 1
   ORDER BY 1
   ```

2. **Top Agents by Token Usage** (bar chart)
   ```sql
   SELECT
     COALESCE(additional_metadata->>'agent_name', 'unknown') AS agent,
     SUM(total_tokens) AS tokens
   FROM migration.llm_usage_logs
   WHERE $__timeFilter(created_at)
     AND feature_context = 'crewai'
   GROUP BY 1
   ORDER BY 2 DESC
   LIMIT 10
   ```

3. **Agent Response Times** (gauge)
   ```sql
   SELECT
     AVG(response_time_ms) AS avg_response_ms
   FROM migration.llm_usage_logs
   WHERE $__timeFilter(created_at)
     AND feature_context = 'crewai'
   ```

4. **Agent Success Rate** (stat)
   ```sql
   SELECT
     ROUND(
       SUM(CASE WHEN success THEN 1 ELSE 0 END)::numeric /
       COUNT(*)::numeric * 100,
       2
     ) AS success_rate_pct
   FROM migration.llm_usage_logs
   WHERE $__timeFilter(created_at)
     AND feature_context = 'crewai'
   ```

#### Dashboard 2: CrewAI Flow Execution
**File**: `config/docker/observability/grafana/dashboards/crewai-flows.json`

**Panels**:
1. **Flows by Type** (pie chart)
   ```sql
   SELECT
     COALESCE(additional_metadata->>'flow_type', 'unknown') AS metric,
     COUNT(*)::float AS value
   FROM migration.llm_usage_logs
   WHERE $__timeFilter(created_at)
     AND feature_context = 'crewai'
     AND additional_metadata ? 'flow_type'
   GROUP BY 1
   ```

2. **Average Tokens per Flow Type** (table)
   ```sql
   SELECT
     COALESCE(additional_metadata->>'flow_type', 'unknown') AS flow_type,
     COUNT(DISTINCT flow_id) AS flow_count,
     AVG(total_tokens) AS avg_tokens_per_call,
     SUM(total_tokens) AS total_tokens
   FROM migration.llm_usage_logs
   WHERE $__timeFilter(created_at)
     AND feature_context = 'crewai'
   GROUP BY 1
   ORDER BY 4 DESC
   ```

## Phase 3: Wire CallbackHandler into All CrewAI Executors

### Assessment Flow Executors (6 files)
**Pattern**: All executors in `backend/app/services/flow_orchestration/execution_engine_crew_assessment/`

#### Files to Modify:
1. `readiness_executor.py`
2. `complexity_executor.py`
3. `dependency_executor.py`
4. `tech_debt_executor.py`
5. `risk_executor.py`
6. `recommendation_executor.py`

#### Changes Required:

**Before** (current code):
```python
# In execute_readiness_assessment_phase():
task = Task(
    description=f"...",
    expected_output="...",
    agent=(agent._agent if hasattr(agent, "_agent") else agent)
)

future = task.execute_async(context=context_str)
result = await asyncio.wrap_future(future)
```

**After** (with callback):
```python
# At top of file - add imports
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration
)

# In execute_readiness_assessment_phase():
# Create callback handler with tenant context
callback_handler = CallbackHandlerIntegration.create_callback_handler(
    flow_id=str(master_flow.flow_id),
    context={
        "client_account_id": str(master_flow.client_account_id),
        "engagement_id": str(master_flow.engagement_id),
        "flow_type": "assessment",
        "phase": "readiness"
    }
)
callback_handler.setup_callbacks()

task = Task(
    description=f"...",
    expected_output="...",
    agent=(agent._agent if hasattr(agent, "_agent") else agent)
)

# Register task with monitor BEFORE execution
callback_handler._step_callback({
    "type": "starting",
    "status": "starting",
    "agent": "readiness_assessor",
    "task": "readiness_assessment",
    "content": "Starting readiness assessment"
})

future = task.execute_async(context=context_str)
result = await asyncio.wrap_future(future)

# Mark completion
callback_handler._task_completion_callback({
    "agent": "readiness_assessor",
    "task_name": "readiness_assessment",
    "status": "completed" if result else "failed",
    "task_id": "readiness_task"
})
```

### Discovery Flow Executors
**Pattern**: Check `backend/app/services/flow_orchestration/execution_engine_crew_discovery/`

- Apply same callback instrumentation
- Ensure flow_type="discovery" in context

### Collection Flow Executors
**Pattern**: Check `backend/app/services/flow_orchestration/execution_engine_crew_collection/`

- Apply same callback instrumentation
- Ensure flow_type="collection" in context

## Phase 4: Pre-Commit Enforcement

### Pre-Commit Hook Script
**File**: `backend/scripts/check_llm_observability.py`

```python
#!/usr/bin/env python3
"""
Pre-commit hook to enforce LLM observability patterns.

Checks:
1. All LLM calls use multi_model_service.generate_response() OR
2. Direct LiteLLM calls are wrapped with proper callbacks
3. CrewAI task execution includes CallbackHandler
4. No task.execute_async() without callback registration
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple

class LLMCallDetector(ast.NodeVisitor):
    """Detect LLM calls that bypass observability."""

    def __init__(self):
        self.violations = []
        # Track per-function state: whether a handler is created/used
        self.func_stack = []

    def visit_FunctionDef(self, node):
        """Track function entry and exit."""
        # Push new function context
        self.func_stack.append({
            "has_handler": False,
            "called_start": False,
            "called_completion": False,
        })
        self.generic_visit(node)
        # Pop when done
        self.func_stack.pop()

    def visit_Assign(self, node):
        """Detect creation of a callback handler via factory."""
        try:
            if isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Attribute) and func.attr == "create_callback_handler":
                    if self.func_stack:
                        self.func_stack[-1]["has_handler"] = True
        finally:
            self.generic_visit(node)

    def visit_Call(self, node):
        """Check function calls for observability patterns."""

        # Track step and completion callbacks
        if isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if self.func_stack:
                if attr == "_step_callback":
                    self.func_stack[-1]["called_start"] = True
                elif attr == "_task_completion_callback":
                    self.func_stack[-1]["called_completion"] = True

            # Check for task.execute_async() without in-scope handler
            if attr == "execute_async":
                ctx = self.func_stack[-1] if self.func_stack else {"has_handler": False, "called_start": False}
                if not (ctx["has_handler"] and ctx["called_start"]):
                    self.violations.append((
                        node.lineno,
                        "task.execute_async() called without in-scope CallbackHandler start registration",
                        "CRITICAL"
                    ))

            # Check for crew.kickoff() without callbacks
            if attr in ['kickoff', 'kickoff_async']:
                # Check if callbacks parameter is provided
                has_callbacks = any(
                    kw.arg == 'callbacks' for kw in node.keywords
                )
                ctx = self.func_stack[-1] if self.func_stack else {"has_handler": False}
                if not has_callbacks and not ctx["has_handler"]:
                    self.violations.append((
                        node.lineno,
                        "crew.kickoff() called without callbacks parameter or in-scope handler",
                        "WARNING"
                    ))

            # Check for direct litellm.completion() calls
            if (attr == 'completion' and
                hasattr(node.func, 'value') and
                hasattr(node.func.value, 'id') and
                node.func.value.id == 'litellm'):
                self.violations.append((
                    node.lineno,
                    "Direct litellm.completion() call - use multi_model_service instead",
                    "ERROR"
                ))

        self.generic_visit(node)

def check_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Check a Python file for observability violations."""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        detector = LLMCallDetector()
        detector.visit(tree)
        return detector.violations
    except SyntaxError:
        return []

def main():
    """Run pre-commit checks on staged Python files."""
    # Get staged Python files from git
    import subprocess
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True,
        text=True
    )

    files = [
        Path(f) for f in result.stdout.strip().split('\n')
        if f.endswith('.py') and 'backend/app' in f
    ]

    all_violations = []
    for file_path in files:
        if not file_path.exists():
            continue

        violations = check_file(file_path)
        if violations:
            all_violations.append((file_path, violations))

    if all_violations:
        print("\n❌ LLM Observability Violations Found:\n")

        for file_path, violations in all_violations:
            print(f"📁 {file_path}")
            for lineno, msg, severity in violations:
                icon = "🚨" if severity == "CRITICAL" else "⚠️" if severity == "ERROR" else "💡"
                print(f"  {icon} Line {lineno}: {msg} [{severity}]")
            print()

        print("Fix these violations before committing.")
        print("\nGuidance:")
        print("  - Use CallbackHandler for CrewAI task execution")
        print("  - Use multi_model_service.generate_response() for LLM calls")
        print("  - See docs/guidelines/OBSERVABILITY_PATTERNS.md")
        print()

        return 1

    print("✅ All LLM calls properly instrumented")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Pre-Commit Configuration
**File**: `backend/.pre-commit-config.yaml`

Add to hooks:
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

## Phase 5: Documentation

### Observability Patterns Guide
**File**: `docs/guidelines/OBSERVABILITY_PATTERNS.md`

(See separate document - will create after approval)

## Phase 6: Testing & Validation

### Unit Tests
**File**: `backend/tests/unit/test_observability_enforcement.py`

- Test provider detection with various model names
- Test callback handler integration
- Test pre-commit script detection logic

### Integration Tests
**File**: `backend/tests/integration/test_llm_tracking.py`

- Execute real CrewAI task with callbacks
- Verify llm_usage_logs populated
- Verify costs calculated
- Verify agent_task_history populated

### Manual Validation Checklist
- [ ] LLM Costs dashboard shows data
- [ ] Agent Activity dashboard shows metrics
- [ ] Pre-commit hook blocks unwired calls
- [ ] Assessment flow execution populates both tables
- [ ] Grafana queries return data within 7-day window

## Rollout Plan

1. ✅ **Fix provider detection** (COMPLETED)
2. **Backfill existing costs** (Run script once)
3. **Create dashboards** (Deploy to Grafana)
4. **Wire executors** (6 assessment + discovery + collection)
5. **Enable pre-commit** (Add to CI/CD)
6. **Documentation** (Patterns guide)
7. **Testing** (Unit + Integration)
8. **Validation** (Manual checklist)

## Success Metrics

- **LLM Costs Dashboard**: Show costs for last 7 days
- **Agent Activity Dashboard**: Show agent metrics from logs
- **Agent Task History**: Populate with execution data
- **Pre-Commit**: Block 100% of unwired LLM calls
- **Test Coverage**: 80%+ for observability code

## Next Steps

**Immediate**:
1. Create backfill script for existing LLM costs
2. Create Agent Activity dashboard JSON
3. Wire CallbackHandler into readiness_executor.py (POC)
4. Test end-to-end with actual flow execution

**After POC Approval**:
1. Wire remaining 5 assessment executors
2. Wire discovery/collection executors
3. Create pre-commit script
4. Add tests
5. Write documentation

## Questions for Review

1. Should we backfill ALL 1,638 rows or just last 30 days?
2. Proceed with all phases or POC first?
3. Any additional metrics needed in dashboards?
4. Should pre-commit be WARNING or ERROR for missing callbacks?
