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

import json
import logging
import math
import re
from datetime import date, datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


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


def _extract_markdown_json(text: str) -> str:
    """Extract JSON from markdown code blocks."""
    markdown_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    markdown_match = re.search(markdown_pattern, text)
    if markdown_match:
        logger.debug("Extracted JSON from markdown code block")
        return markdown_match.group(1).strip()
    return text


def _find_json_boundaries(text: str) -> tuple[Optional[int], Optional[int]]:
    """Find start and end positions of outermost JSON object/array."""
    json_start: Optional[int] = None
    json_end: Optional[int] = None
    brace_count = 0
    bracket_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue

        if char == "{":
            if json_start is None and bracket_count == 0:
                json_start = i
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0 and bracket_count == 0 and json_start is not None:
                return json_start, i + 1
        elif char == "[":
            if json_start is None and brace_count == 0:
                json_start = i
            bracket_count += 1
        elif char == "]":
            bracket_count -= 1
            if bracket_count == 0 and brace_count == 0 and json_start is not None:
                return json_start, i + 1

    return json_start, json_end


def _sanitize_json_text(text: str) -> str:
    """Apply sanitization transformations to JSON text."""
    # Replace single quotes with double quotes for JSON keys and values
    text = re.sub(r"(?<![a-zA-Z])'([^']*)'(?=\s*:)", r'"\1"', text)
    text = re.sub(r":\s*'([^']*)'(?=\s*[,}\]])", r': "\1"', text)
    # Remove trailing commas
    text = re.sub(r",\s*([}\]])", r"\1", text)
    # Replace NaN and Infinity with null
    text = re.sub(r"\bNaN\b", "null", text)
    text = re.sub(r"\bInfinity\b", "null", text)
    text = re.sub(r"-Infinity\b", "null", text)
    return text


def _extract_partial_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract any valid JSON objects as a last resort."""
    json_objects = []
    for match in re.finditer(r"\{[^{}]*\}", text):
        try:
            obj = json.loads(match.group())
            json_objects.append(obj)
        except json.JSONDecodeError:
            continue

    if json_objects:
        largest = max(json_objects, key=lambda x: len(str(x)))
        logger.warning(
            f"Returning best-effort partial JSON (found {len(json_objects)} objects)"
        )
        return largest
    return None


def safe_parse_llm_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON from LLM output with comprehensive error handling.

    Handles common LLM output quirks per ADR-029:
    - Markdown code blocks (```json...```)
    - Trailing commas in arrays/objects
    - Single quotes instead of double quotes
    - NaN/Infinity values
    - JSON embedded in text
    - Truncated output (returns partial data if possible)

    Args:
        raw_text: Raw text output from an LLM that may contain JSON

    Returns:
        Parsed dictionary or None if parsing fails completely

    See Also:
        ADR-029: LLM Output JSON Sanitization Pattern
    """
    if not raw_text or not isinstance(raw_text, str):
        logger.warning("safe_parse_llm_json: Empty or non-string input")
        return None

    # Step 1: Remove markdown code blocks
    text = _extract_markdown_json(raw_text.strip())

    # Step 2: Try direct parsing first (fast path for well-formed JSON)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Step 3: Find and extract JSON boundaries
    json_start, json_end = _find_json_boundaries(text)
    if json_start is not None:
        if json_end is not None:
            text = text[json_start:json_end]
        else:
            text = text[json_start:]
            logger.warning(f"Possibly truncated JSON detected (starts at {json_start})")

    # Step 4: Apply sanitization and try parsing
    text = _sanitize_json_text(text)
    try:
        result = json.loads(text)
        logger.debug("Successfully parsed JSON after sanitization")
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed after sanitization: {e}")

    # Step 5: Last resort - try to extract any valid JSON objects
    partial = _extract_partial_json(text)
    if partial:
        return partial

    logger.error(
        f"Failed to parse JSON from LLM output. "
        f"Raw text length: {len(raw_text)}, Preview: {raw_text[:200]}..."
    )
    return None
