# JSON Escape Sequence Sanitization Pattern

## Context
LLMs sometimes return invalid escape sequences in JSON responses (Bug #26). Valid JSON escape sequences are: `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\uXXXX` (unicode).

## Implementation Pattern

Use a **negative lookahead regex** to correctly handle unicode escape sequences:

```python
import re

def sanitize_escape_sequences(text: str) -> str:
    """
    Sanitize invalid escape sequences in LLM JSON responses.
    Uses negative lookahead to correctly handle \uXXXX unicode sequences.
    """
    def fix_invalid_escape(match: re.Match) -> str:
        # The matched group is the character following the backslash
        return r"\\" + match.group(1)

    # Pattern: backslash NOT followed by valid escape chars or unicode sequence
    result = re.sub(r'\\(?![\\"/bfnrt]|u[0-9a-fA-F]{4})(.)', fix_invalid_escape, text)
    return result
```

## Why This Pattern

The previous implementation checked if the character after `\` was in `'"\\/bfnrtu'`, but this incorrectly treated `\u` followed by non-hex digits as valid. The negative lookahead pattern:
- `[\\"/bfnrt]` - matches single valid escape characters
- `u[0-9a-fA-F]{4}` - matches valid unicode sequences with exactly 4 hex digits

## Location
- `backend/app/services/collection/gap_analysis/section_question_generator/generator.py`
- Method: `_sanitize_escape_sequences()`

## Related
- ADR-029: JSON Sanitization Pattern
- Bug #26: Invalid escape sequences in LLM responses
