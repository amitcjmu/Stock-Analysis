# Session Learnings - January 2025

## [2025-01-20] Discovery Dashboard & Security Fixes
### Context: Discovery dashboard showing "No active flows" after schema modularization
### Root Cause: Circular import between context.py and context_legacy.py
### Solution:
- Moved legacy getter functions directly into context.py as single source of truth
- Made context_legacy.py simply re-export functions for backward compatibility
### Code:
```python
# context.py - Define functions here
def get_client_account_id() -> Optional[str]:
    return _client_account_id.get()

# context_legacy.py - Just re-export
from app.core.context import (
    get_client_account_id,
    get_engagement_id,
    get_user_id,
    get_flow_id,
)
__all__ = ["get_client_account_id", "get_engagement_id", "get_user_id", "get_flow_id"]
```
### Result: Backend starts without import errors, API returns flows correctly

## [2025-01-20] File Modularization Pattern
### Context: field_mapping_executor.py exceeded 400-line limit (612 lines)
### Solution: Split into focused modules
### Structure:
```
field_mapping_executor.py (346 lines) - Main executor, backward compatibility
field_mapping_utils.py (209 lines) - Utilities and helpers
field_mapping_converters.py (171 lines) - Format conversions
field_mapping_fallback.py (295 lines) - Fallback execution logic
```
### Result: Clean separation of concerns, all pre-commit checks pass

## [2025-01-20] JWT Security Hardening
### Context: JWT decoded without verification for sensitive decisions
### Solution: Add validation to prevent system user impersonation
### Code:
```python
def _decode_jwt_payload(token: str) -> Optional[str]:
    # ... decode logic ...
    sub = payload.get("sub")
    # Reject suspicious subjects
    suspicious_subjects = {"system", "admin", "root", "service", "bot"}
    if not sub or str(sub).strip().lower() in suspicious_subjects:
        return None
    if len(str(sub).strip()) < 3:  # Too short to be valid
        return None
    return sub
```
### Result: Prevents JWT spoofing and system user impersonation

## [2025-01-20] Database Session Lifecycle Management
### Context: Direct iteration of dependency generator without cleanup causing connection leaks
### Solution: Proper async context management with comprehensive cleanup
### Code:
```python
db_session_generator = get_db()
db_session = None
try:
    if hasattr(db_session_generator, "__anext__"):
        db_session = await db_session_generator.__anext__()
    elif hasattr(db_session_generator, "__next__"):
        db_session = next(db_session_generator)
    # ... use session ...
finally:
    if db_session and hasattr(db_session, "close"):
        if hasattr(db_session.close, "__await__"):
            await db_session.close()
        else:
            db_session.close()
    if hasattr(db_session_generator, "aclose"):
        await db_session_generator.aclose()
```
### Result: No connection leaks, supports both async and sync generators

---

# Session Learnings - December 2025

## [2025-12-05] Issue #1060: Declarative Agent Tool Configuration (PR #1254)

### Declarative Configuration Pattern for Agent Tools
### Context: tool_manager.py had scattered if/elif blocks for 6+ agent types, making it hard to add new agents
### Root Cause: Imperative code pattern - each agent type required new code blocks
### Solution: Created `agent_tool_config.py` with dataclasses as single source of truth
### Structure:
```
agent_tool_config.py (194 lines) - Declarative config with dataclasses
  - ToolFactoryConfig: module_path, factory_name, requires_context, requires_registry, is_class
  - AgentToolConfig: agent_type, specific_tools, common_categories, description
  - TOOL_FACTORIES: Dict mapping tool names to factory configs
  - AGENT_TOOL_CONFIGS: Dict mapping agent types to tool configs
tool_manager.py (refactored) - Uses config lookups instead of if/elif
```
### Code:
```python
@dataclass
class ToolFactoryConfig:
    module_path: str
    factory_name: str
    requires_context: bool = True
    requires_registry: bool = False
    is_class: bool = False

TOOL_FACTORIES: Dict[str, ToolFactoryConfig] = {
    "asset_creation": ToolFactoryConfig(
        module_path="app.services.crewai_flows.tools.asset_creation_tool",
        factory_name="create_asset_creation_tools",
    ),
    # ... more tools
}

AGENT_TOOL_CONFIGS: Dict[str, AgentToolConfig] = {
    "discovery": AgentToolConfig(
        agent_type="discovery",
        specific_tools=["asset_creation", "data_validation"],
        common_categories=["data_analysis"],
    ),
    # ... more agents
}
```
### Result: Adding new agents = add dictionary entry, no code changes

### Dynamic Import Security Documentation (Qodo Bot Feedback)
### Context: Qodo Bot raised concern about dynamic imports via importlib.import_module()
### Root Cause: Dynamic imports can be security risk if paths come from user input
### Solution: Added security comment documenting that config is static
### Code:
```python
def _load_tool_from_factory(cls, tool_name: str, context_info: Dict, tools: List) -> int:
    """
    Security Note: Dynamic imports via importlib are safe here because
    TOOL_FACTORIES configuration is static and defined in agent_tool_config.py,
    not from user input. All module paths are hardcoded at development time.
    """
```
### Result: Security concern addressed, reviewers understand config is safe

### Config Flags vs Signature Inspection (Qodo Bot Feedback)
### Context: Original code used inspect.signature() to determine function parameters
### Root Cause: Introspection is implicit and harder to understand
### Solution: Use declarative config flags (requires_context, requires_registry) explicitly
### Code:
```python
# Before (implicit via signature inspection)
sig = inspect.signature(getter)
if "context_info" in sig.parameters:
    new_tools = getter(context_info)

# After (explicit via config flags)
if factory_config.requires_registry:
    service_registry = context_info.get("service_registry")
    if factory_config.requires_context:
        new_tools = factory(context_info, registry=service_registry)
    else:
        new_tools = factory(registry=service_registry)
elif factory_config.requires_context:
    new_tools = factory(context_info)
else:
    new_tools = factory()
```
### Result: Clearer, more explicit code - easier to understand and maintain

## [2025-12-05] Issue #719: Treatment Recommendations Display Polish (PR #1231)

### Accept Button HTTP 400 Fix
### Context: Clicking "Accept" on 6R Strategy Review page threw HTTP 400 "Unsupported phase: six_r_decision"
### Root Cause: Backend `update_assessment_phase_data` endpoint only supported `component_analysis` and `tech_debt_analysis` phases
### Solution: Added `six_r_decision` phase handler to store user acceptance in phase_results JSONB
### Code:
```python
# backend/app/api/v1/master_flows/assessment/lifecycle_endpoints/data_updates.py
elif phase == "six_r_decision":
    app_id = data.get("app_id")
    decision = data.get("decision", {})
    # Get flow and update phase_results with user_modifications
    flow.phase_results["recommendation_generation"]["results"]["recommendation_generation"]["applications"][app_index]["user_modifications"] = decision.get("user_modifications", {})
    await db.commit()
```
### Result: Accept button works, user modifications persisted to JSONB

### Schema-Resilient JSONB Field Detection (Qodo Bot #4)
### Context: Code checked only `six_r_strategy` field to detect completed apps, but older data used `overall_strategy`
### Root Cause: JSONB schema evolved over time, field names changed
### Solution: Helper function that checks multiple field names
### Code:
```python
def has_strategy(app: Dict[str, Any]) -> bool:
    strat = app.get("six_r_strategy") or app.get("overall_strategy")
    return isinstance(strat, str) and len(strat.strip()) > 0
```
### Result: Backward compatibility with all JSONB data versions

### Custom ApiError for HTTP Response Preservation (Qodo Bot #3)
### Context: Frontend needed access to HTTP 409 response body (containing `apps_not_found` list) for proper error display
### Root Cause: Standard Error class lost response body during catch/throw
### Solution: Custom ApiError class in ApiClient.ts that preserves response data
### Code:
```typescript
// src/services/ApiClient.ts
export class ApiError extends Error {
  status: number;
  response: { data: Record<string, unknown>; status: number; statusText: string; };
  constructor(status: number, statusText: string, data: Record<string, unknown>) {
    super(`HTTP ${status}: ${statusText}`);
    this.response = { data, status, statusText };
  }
}
```
### Result: Frontend can display detailed 409 error info including missing apps list

### Pre-Commit Modularization via Linting Agent (Qodo Bot #1)
### Context: recommendation_executor.py hit 408 lines, exceeding 400-line pre-commit limit
### Root Cause: Single file accumulated too much logic
### Solution: Delegated to devsecops-linting-engineer subagent to extract validation logic
### Structure:
```
recommendation_executor.py (380 lines) - Main executor
recommendation_validator.py (50 lines) - Extracted ValidationMixin
```
### Result: Pre-commit passes, clean separation of concerns
