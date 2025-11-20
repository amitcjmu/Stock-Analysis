# JSON Parsing with Markdown-Wrapped LLM Output

## Problem
LLM agents (CrewAI, ChatGPT, etc.) often return valid JSON wrapped in markdown code blocks:
```
```json
{"key": "value"}
```
```

This causes `json.loads()` to fail with: `"Expecting value: line 1 column 1 (char 0)"`

## Root Cause
- LLMs format output for readability in chat interfaces
- JSON is wrapped in markdown code fences: ` ```json...``` `
- Python's `json.loads()` expects raw JSON, not markdown

## Solution
Strip markdown wrappers before JSON parsing

```python
# Strip markdown code blocks if present (common LLM output format)
if isinstance(result_str, str):
    result_str = result_str.strip()

    # Remove opening wrapper
    if result_str.startswith("```json"):
        result_str = result_str[7:]  # Remove ```json
    elif result_str.startswith("```"):
        result_str = result_str[3:]  # Remove ```

    # Remove closing wrapper
    if result_str.endswith("```"):
        result_str = result_str[:-3]  # Remove trailing ```

    result_str = result_str.strip()

try:
    parsed_result = json.loads(result_str)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse: {e}")
    # Store raw output for debugging
    return {"raw_output": result_str, "parse_error": str(e)}
```

## When to Use
- ✅ Parsing any LLM-generated JSON output
- ✅ CrewAI agent task results
- ✅ ChatGPT/GPT-4 API responses with JSON mode
- ✅ Claude/Anthropic structured outputs
- ✅ Any AI agent that returns formatted text

## Common LLM Output Formats

```markdown
# Format 1: json fence
```json
{"data": "value"}
```

# Format 2: Generic fence
```
{"data": "value"}
```

# Format 3: Raw JSON (rare)
{"data": "value"}
```

## Implementation Example

```python
# backend/app/services/flow_orchestration/execution_engine_crew_assessment/recommendation_executor.py

result_str = result.raw if hasattr(result, "raw") else str(result)

# Strip markdown wrappers BEFORE parsing
if isinstance(result_str, str):
    result_str = result_str.strip()
    if result_str.startswith("```json"):
        result_str = result_str[7:]
    elif result_str.startswith("```"):
        result_str = result_str[3:]
    if result_str.endswith("```"):
        result_str = result_str[:-3]
    result_str = result_str.strip()

# Now parse clean JSON
parsed_result = json.loads(result_str)
```

## Related Issues
- CrewAI agents returning markdown-wrapped JSON (Issue #999)
- Assessment flow recommendation parsing failures
- Any "Expecting value: line 1 column 1" errors with LLM output

## Files Using This Pattern
- `backend/app/services/flow_orchestration/execution_engine_crew_assessment/recommendation_executor.py:315-325`
