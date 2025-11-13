"""JSON sanitization utilities for LLM-generated data.

This module provides utilities to sanitize data structures containing
non-JSON-safe values (NaN, Infinity) before FastAPI serialization.

USAGE:
    All LLM-generated numeric data MUST be sanitized before passing to
    FastAPI response models to prevent JSON serialization errors.

    from app.utils.json_sanitization import sanitize_for_json

    # Before returning LLM data in API response
    return ResponseModel(
        data=sanitize_for_json(llm_data)
    )

ARCHITECTURAL DECISION:
    See ADR-029 for architectural decision and usage guidelines.
    This pattern is MANDATORY for all endpoints returning AI-generated data.

WHEN TO USE:
    - ✅ Questionnaire generation (adaptive questions)
    - ✅ Gap analysis results (confidence scores)
    - ✅ Assessment recommendations (risk scores, complexity scores)
    - ✅ Migration wave planning (business impact scores)
    - ✅ Agent insights and analysis results
    - ✅ Any AI-generated numeric data in API responses

WHEN NOT TO USE:
    - ❌ User input data (already validated)
    - ❌ Database primary keys (UUIDs, integers)
    - ❌ Enum values (strings)
    - ❌ Static configuration
"""

import math
from datetime import date, datetime
from typing import Any


def sanitize_for_json(data: Any) -> Any:
    """Recursively sanitize data for JSON serialization.

    Converts non-JSON-safe values to safe alternatives:
    - NaN → null
    - Infinity / -Infinity → null
    - datetime / date → ISO 8601 string
    - Non-serializable objects → string representation

    This function should be applied to all LLM-generated numeric data
    before passing to FastAPI response models to prevent serialization errors.

    Args:
        data: Any Python data structure (dict, list, primitive, etc.)

    Returns:
        JSON-safe version of the input data

    Examples:
        >>> sanitize_for_json({"score": float('nan'), "count": 10})
        {"score": None, "count": 10}

        >>> sanitize_for_json([1, float('inf'), 3])
        [1, None, 3]

        >>> from datetime import datetime
        >>> sanitize_for_json({"created": datetime(2025, 10, 22)})
        {"created": "2025-10-22T00:00:00"}

        >>> # Nested structures are handled recursively
        >>> data = {
        ...     "level1": {
        ...         "score": float('nan'),
        ...         "level2": {"confidence": float('inf'), "valid": 0.95}
        ...     }
        ... }
        >>> sanitize_for_json(data)
        {"level1": {"score": None, "level2": {"confidence": None, "valid": 0.95}}}

    See Also:
        ADR-029: LLM Output JSON Sanitization Pattern
        Issue #682: Questionnaire generation JSON serialization failures

    Note:
        This function operates on a copy of the data structure, so the
        original data is not modified.
    """
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, (str, int, bool, type(None))):
        return data
    else:
        # Fallback: convert to string for any other non-serializable type
        return str(data)
