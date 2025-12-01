# LLM/JSON/CrewAI Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 17 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **ADR-029**: Use `safe_parse_llm_json()` for ALL LLM output parsing
> 2. **Three-Tier Parsing**: json.loads → dirtyjson → safe_sanitize
> 3. **Markdown Stripping**: Remove ` ```json ` wrappers before parsing
> 4. **TaskOutput Extraction**: Use `.raw` attribute, not TaskOutput object directly
> 5. **NaN/Infinity Sanitization**: Call `sanitize_for_json()` before API responses

---

## Table of Contents

1. [Overview](#overview)
2. [JSON Parsing Patterns](#json-parsing-patterns)
3. [CrewAI Patterns](#crewai-patterns)
4. [Serialization Safety](#serialization-safety)
5. [Anti-Patterns](#anti-patterns)
6. [Code Templates](#code-templates)
7. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
LLM output parsing, JSON sanitization, CrewAI task execution, observability integration, and safe serialization patterns.

### When to Reference
- Parsing LLM-generated JSON
- Implementing CrewAI task execution
- Fixing JSON serialization errors
- Handling NaN/Infinity values

### Key ADRs
- **ADR-029**: LLM Output JSON Sanitization (mandatory)
- **ADR-024**: TenantMemoryManager (CrewAI memory disabled)

---

## JSON Parsing Patterns

### Pattern 1: Three-Tier Parsing Strategy (ADR-029)

**Problem**: LLM agents return malformed JSON with:
- Single quotes instead of double quotes
- Unquoted property names
- Trailing commas
- Markdown code block wrappers

**Solution**: Use `safe_parse_llm_json()` - NOT raw `json.loads()`:

```python
from app.utils.llm_json_parser import safe_parse_llm_json

# WRONG - Fails on LLM output
data = json.loads(llm_response)

# CORRECT - Handles all LLM quirks
data = safe_parse_llm_json(llm_response)
```

**Three-Tier Implementation**:

```python
import json
import dirtyjson

def safe_parse_llm_json(result: Any) -> Dict[str, Any]:
    result_str = str(result)

    # Safely extract JSON object - prevent crash if no match found
    match = re.search(r"\{.*\}", result_str, re.DOTALL)
    if not match:
        return {"error": "No JSON object found in output", "raw_output": result_str[:500]}
    json_str = match.group(0)

    # Tier 1: Standard JSON (fastest)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Tier 2: Lenient parser (handles LLM quirks)
    try:
        parsed = dirtyjson.loads(json_str)
        logger.info("Parsed with dirtyjson")
        return parsed
    except Exception:
        pass

    # Tier 3: Conservative fallback
    try:
        sanitized = _safe_sanitize(json_str)
        return json.loads(sanitized)
    except json.JSONDecodeError:
        return {"error": "All parsing failed", "raw_output": result_str[:500]}

def _safe_sanitize(json_str: str) -> str:
    """Only provably safe transformations"""
    # Remove trailing commas
    fixed = re.sub(r",(\s*[}\]])", r"\1", json_str)
    # Quote bare property names
    fixed = re.sub(r"([{,]\s*)(\w+)(\s*:)", r'\1"\2"\3', fixed)
    return fixed
```

---

### Pattern 2: Markdown Wrapper Stripping

**Problem**: LLMs wrap JSON in markdown code blocks:
```
```json
{"key": "value"}
```
```

**Solution**: Strip markdown before parsing:

```python
if isinstance(result_str, str):
    result_str = result_str.strip()

    # Remove markdown code fences (handles ```json, ```JSON, ```json5, plain ```, etc.)
    result_str = re.sub(r"^```[a-zA-Z0-9]*\s*\n?", "", result_str)  # Opening fence
    result_str = re.sub(r"\n?```\s*$", "", result_str)  # Closing fence
    result_str = result_str.strip()

parsed = json.loads(result_str)
```

---

### Pattern 3: Unsafe Transformations to AVOID

```python
# WRONG: Global quote replacement corrupts apostrophes
fixed = json_str.replace("'", '"')  # "it's" → "it"s"

# WRONG: Broad regex matches inside strings
fixed = re.sub(r"(\w+)(?=\s*:)", r'"\1"', fixed)  # Corrupts "Time: 3:00"

# WRONG: Removes valid escape sequences
fixed = fixed.replace('\\"', '"')  # Breaks escaped quotes
```

---

## CrewAI Patterns

### Pattern 4: TaskOutput Extraction

**Problem**: CrewAI's `task.execute_async()` returns `TaskOutput` objects, not strings.

```
TypeError: Object of type TaskOutput is not JSON serializable
```

**Solution**: Extract `.raw` attribute:

```python
from crewai import TaskOutput
from app.utils.json_sanitization import sanitize_for_json

# Execute task
result = await asyncio.wrap_future(task.execute_async(context=context_str))

# Extract string from TaskOutput
if isinstance(result, TaskOutput):
    result_str = result.raw if hasattr(result, 'raw') else str(result)
else:
    result_str = str(result) if not isinstance(result, str) else result

# Parse and sanitize per ADR-029
parsed = safe_parse_llm_json(result_str)
parsed = sanitize_for_json(parsed)
```

---

### Pattern 5: CrewAI Memory Disabled (ADR-024)

**CRITICAL**: CrewAI built-in memory is DISABLED.

```python
from app.services.crewai_flows.config.crew_factory import create_crew

crew = create_crew(
    agents=[agent],
    tasks=[task],
    memory=False,  # REQUIRED - Use TenantMemoryManager instead
    verbose=False
)
```

**Why**: CrewAI memory causes 401 errors (DeepInfra key → OpenAI endpoint).

**Alternative**: Use `TenantMemoryManager` for agent learning.

---

### Pattern 6: Timeout Configuration

```python
import os

# Set configurable timeout
if "max_execution_time" not in kwargs:
    default_timeout = int(os.getenv("CREWAI_TIMEOUT_SECONDS", "600"))
    kwargs["max_execution_time"] = default_timeout
    logger.info(f"Setting CrewAI timeout to {default_timeout} seconds")
```

**Timeout Guidelines**:
| Agent Type | Timeout |
|------------|---------|
| Basic agents | 300s (5 min) |
| Analysis agents | 600s (10 min) |
| Complex reasoning | 1200s (20 min) |
| Multi-step orchestration | 1800s (30 min) |

---

## Serialization Safety

### Pattern 7: NaN/Infinity Sanitization

**Problem**: LLMs may produce NaN/Infinity that can't serialize to JSON.

**Solution**: Always sanitize before API responses:

```python
import math
from typing import Any

def sanitize_for_json(data: Any) -> Any:
    """Recursively sanitize data for JSON serialization."""
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif hasattr(data, 'isoformat'):
        return data.isoformat()
    elif isinstance(data, (str, int, bool, type(None))):
        return data
    else:
        return str(data)
```

**Usage**:
```python
response = ResponseModel(
    questions=sanitize_for_json(llm_data.questions),
    scores=sanitize_for_json(llm_data.scores),
)
```

---

### Pattern 8: UUID JSONB Persistence

**Problem**: UUIDs in JSONB need string conversion.

```python
import json
from uuid import UUID

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)

# Usage
json_str = json.dumps(data, cls=UUIDEncoder)
```

---

## Anti-Patterns

### Don't: Parse TaskOutput Directly

```python
# WRONG - TaskOutput is not JSON serializable
result = await task.execute_async()
json.dumps(result)  # TypeError!

# CORRECT
result_str = result.raw if hasattr(result, 'raw') else str(result)
parsed = safe_parse_llm_json(result_str)
```

### Don't: Skip Sanitization

```python
# WRONG - May contain NaN/Infinity
return ResponseModel(**llm_output)

# CORRECT
return ResponseModel(**sanitize_for_json(llm_output))
```

### Don't: Use Unsafe Regex Transforms

```python
# WRONG - Corrupts data
json_str.replace("'", '"')

# CORRECT - Use dirtyjson or safe_sanitize
import dirtyjson
dirtyjson.loads(json_str)
```

### Don't: Enable CrewAI Memory

```python
# WRONG - Causes 401 errors
crew = create_crew(..., memory=True)

# CORRECT - Per ADR-024
crew = create_crew(..., memory=False)
```

---

## Code Templates

### Template 1: Complete LLM Output Handler

```python
from crewai import TaskOutput
from app.utils.llm_json_parser import safe_parse_llm_json
from app.utils.json_sanitization import sanitize_for_json

async def handle_agent_result(result: Any) -> Dict[str, Any]:
    """Complete pattern for handling CrewAI agent results."""

    # 1. Extract string from TaskOutput
    if isinstance(result, TaskOutput):
        result_str = result.raw if hasattr(result, 'raw') else str(result)
    else:
        result_str = str(result) if not isinstance(result, str) else result

    # 2. Strip markdown wrappers (handles ```json, ```JSON, ```json5, plain ```, etc.)
    result_str = result_str.strip()
    result_str = re.sub(r"^```[a-zA-Z0-9]*\s*\n?", "", result_str)  # Opening fence
    result_str = re.sub(r"\n?```\s*$", "", result_str)  # Closing fence
    result_str = result_str.strip()

    # 3. Parse with three-tier strategy
    parsed = safe_parse_llm_json(result_str)

    # 4. Sanitize for NaN/Infinity
    return sanitize_for_json(parsed)
```

### Template 2: CrewAI Task Execution

```python
async def execute_analysis_task(task, context: str) -> Dict[str, Any]:
    """Execute CrewAI task with proper timeout and result handling."""

    # Execute with timeout
    result = await asyncio.wait_for(
        asyncio.wrap_future(task.execute_async(context=context)),
        timeout=int(os.getenv("CREWAI_TIMEOUT_SECONDS", "600"))
    )

    # Handle result per established patterns
    return await handle_agent_result(result)
```

---

## Troubleshooting

### Issue: "Object of type TaskOutput is not JSON serializable"

**Cause**: Passing TaskOutput directly instead of extracting `.raw`.

**Fix**: Use `result.raw` attribute.

### Issue: "Expecting value: line 1 column 1"

**Cause**: Markdown wrapper around JSON.

**Fix**: Strip ` ```json ` prefix and ` ``` ` suffix.

### Issue: "Unable to serialize Unknown to JSON"

**Cause**: NaN or Infinity in LLM output.

**Fix**: Call `sanitize_for_json()` before response.

### Issue: JSON parse fails with apostrophes

**Cause**: Using `replace("'", '"')` which corrupts strings like "it's".

**Fix**: Use `dirtyjson` library instead.

---

## Consolidated Sources

| Original Memory | Key Contribution |
|-----------------|------------------|
| `llm-json-parsing-dirtyjson-pattern` | Three-tier parsing |
| `llm_json_parsing_markdown_wrapper_stripping` | Markdown stripping |
| `json-serialization-safety-pattern` | NaN/Infinity handling |
| `taskoutput_serialization_crewai` | TaskOutput extraction |
| `crewai_configuration_patterns` | Timeout config |
| `adr024_crewai_memory_disabled_2025_10_02` | Memory disabled |
| `crewai_production_error_fixes` | Production fixes |
| `crewai-environment-initialization-patterns` | Environment setup |
| `uuid_jsonb_serialization_pattern_2025_10` | UUID serialization |
| `deterministic_ids_jsonb_persistence` | ID persistence |
| `json_escape_sequence_sanitization_pattern` | Escape sequences |
| `llm-json-ellipsis-preprocessing-pattern-2025-11` | Ellipsis handling |
| `stack_based_json_repair_pattern` | JSON repair |
| `llm_tracking_implementation_2025_10_02` | LLM tracking |
| `observability-grafana-dashboard-debugging` | Observability |
| `crewai-railway-environment-propagation` | Railway config |
| `crewai_agent_service_registry_fixes_2025_09` | Registry fixes |

**Archive Location**: `.serena/archive/llm_json/`

---

## Search Keywords

llm, json, parsing, crewai, taskoutput, sanitization, nan, infinity, dirtyjson, markdown, serialization
