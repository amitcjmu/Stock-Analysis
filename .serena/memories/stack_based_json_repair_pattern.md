# Stack-Based JSON Repair Pattern

## Context
LLM responses often get truncated mid-JSON due to token limits (ADR-035). Simple bracket counting doesn't correctly handle nested structures.

## Implementation Pattern

Use a **stack-based approach** to track open delimiters and close them in the correct order:

```python
def repair_truncated_json(json_str: str) -> str:
    """
    Repair truncated JSON by closing unclosed brackets using a stack.
    Handles nested structures correctly (e.g., [{"key": [{...}]}]).
    """
    import re

    # First, clean up trailing incomplete content
    json_str = re.sub(r',?\s*"[^"]*":\s*"[^"]*$', "", json_str)  # Incomplete strings
    json_str = re.sub(r',?\s*"[^"]*":\s*[^,\]\}]*$', "", json_str)  # Incomplete values
    json_str = re.sub(r",\s*$", "", json_str)  # Trailing commas

    # Use stack to track open brackets
    stack: list[str] = []
    in_string = False
    prev_char = ""

    for char in json_str:
        if char == '"' and prev_char != "\\":
            in_string = not in_string
        elif not in_string:
            if char in "{[":
                stack.append(char)
            elif char == "}" and stack and stack[-1] == "{":
                stack.pop()
            elif char == "]" and stack and stack[-1] == "[":
                stack.pop()
        prev_char = char

    # Close in reverse order
    closing_sequence = []
    for open_char in reversed(stack):
        closing_sequence.append("}" if open_char == "{" else "]")

    return json_str + "".join(closing_sequence)
```

## Why Stack-Based

Simple counting `{` vs `}` doesn't preserve nesting order:
- Input: `{"a": [{"b": [`
- Counting gives: `]]}}` (wrong order)
- Stack gives: `]}]}` (correct order)

## Location
- `backend/app/services/collection/gap_analysis/data_awareness_agent.py`
- Method: `_repair_truncated_json()`

## Related
- ADR-035: Chunking for Large LLM Responses
- Bug #20: Truncated JSON repair
