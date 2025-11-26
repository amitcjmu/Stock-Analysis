# LLM JSON Invalid Escape Sequence Preprocessing Pattern

## Bug #26: Invalid Escape Sequences in LLM JSON Responses

### Problem
LLMs sometimes return JSON responses with invalid escape sequences like `\X`, `\x` (invalid hex), `\.`, etc. which break standard JSON parsers (`json.loads()`) and even lenient parsers (`dirtyjson.loads()`).

Example error:
```
Invalid \X escape sequence '.': line 36 column 83 (char 1418)
```

### Root Cause
LLMs generate text that may include backslash-escaped characters that are NOT valid in JSON.

Valid JSON escape sequences:
- `\"` - double quote
- `\\` - backslash
- `\/` - forward slash
- `\b` - backspace
- `\f` - formfeed
- `\n` - newline
- `\r` - carriage return
- `\t` - tab
- `\uXXXX` - unicode hex

Invalid sequences that LLMs produce:
- `\X`, `\x` (when not followed by proper hex)
- `\.`, `\-`, `\s`, etc.

### Solution Pattern

Add a preprocessing step BEFORE JSON parsing to sanitize invalid escape sequences:

```python
def _sanitize_escape_sequences(self, text: str) -> str:
    """
    Sanitize invalid escape sequences in LLM JSON responses.

    Valid JSON escape sequences: \\", \\\\, \\/, \\b, \\f, \\n, \\r, \\t, \\uXXXX
    """
    import re

    def fix_invalid_escape(match: re.Match) -> str:
        char = match.group(1)
        # If it's a valid escape sequence start, keep it
        if char in '"\\\/bfnrtu':
            return match.group(0)
        # Otherwise, escape the backslash itself
        return '\\\\' + char

    # Match backslash followed by any character
    result = re.sub(r'\\(.)', fix_invalid_escape, text)
    return result
```

### Usage
Call this sanitization AFTER stripping markdown code blocks, BEFORE JSON parsing:

```python
# 1. Strip markdown code blocks
cleaned = re.sub(r"```json\s*|\s*```", "", response.strip())

# 2. Sanitize invalid escape sequences (Bug #26)
cleaned = self._sanitize_escape_sequences(cleaned)

# 3. Parse JSON
try:
    parsed = json.loads(cleaned)
except json.JSONDecodeError:
    parsed = dirtyjson.loads(cleaned)
```

### File Location
`backend/app/services/collection/gap_analysis/section_question_generator/generator.py`

### Related Patterns
- ADR-029: LLM Output JSON Sanitization Pattern
- Bug #15: LLM literal ellipsis (`...`) preprocessing (different issue, similar pattern)

### Testing
This pattern handles:
- `\X` → `\\X` (escapes the backslash)
- `\x` → `\\x` (escapes invalid hex escape)
- `\.` → `\\.` (escapes the backslash)
- `\"` → `\"` (valid, unchanged)
- `\\` → `\\` (valid, unchanged)
- `\n` → `\n` (valid, unchanged)
- `\uABCD` → `\uABCD` (valid, unchanged)
