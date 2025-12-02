"""Output parsing utilities for gap analysis."""

import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _repair_truncated_json(json_str: str) -> str:
    """
    Repair truncated JSON by closing unclosed brackets using a stack.

    LLM responses often get truncated mid-JSON due to token limits (per ADR-035).
    This method attempts to repair the JSON by:
    1. Removing trailing incomplete strings (e.g., "value": "incomplete...)
    2. Removing trailing incomplete keys (e.g., "field":)
    3. Closing unclosed brackets in the correct order using a stack

    Args:
        json_str: Potentially truncated JSON string

    Returns:
        Repaired JSON string (best effort)

    Example:
        Input:  '{"assets": [{"name": "Test", "gaps": ['
        Output: '{"assets": [{"name": "Test", "gaps": []}]}'
    """
    # Remove trailing incomplete string values (e.g., "field": "incompletetext...)
    # Match pattern: "key": "value... (without closing quote)
    json_str = re.sub(r',?\s*"[^"]*":\s*"[^"]*$', "", json_str)

    # Remove trailing incomplete values after colon (e.g., "field": 123... or "field": tru)
    json_str = re.sub(r',?\s*"[^"]*":\s*[^,\]\}]*$', "", json_str)

    # Remove trailing comma before attempting to close brackets
    json_str = re.sub(r",\s*$", "", json_str)

    # Use a stack to determine the correct closing sequence
    # This handles nested structures correctly (e.g., [{"key": [{...}]}])
    stack: list[str] = []
    in_string = False
    prev_char = ""

    for char in json_str:
        if char == '"' and prev_char != "\\":
            # Toggle string state (handles escaped quotes)
            in_string = not in_string
        elif not in_string:
            if char in "{[":
                stack.append(char)
            elif char == "}":
                if stack and stack[-1] == "{":
                    stack.pop()
            elif char == "]":
                if stack and stack[-1] == "[":
                    stack.pop()
        prev_char = char

    # Build closing sequence from stack (reverse order)
    closing_sequence = []
    for open_char in reversed(stack):
        if open_char == "{":
            closing_sequence.append("}")
        elif open_char == "[":
            closing_sequence.append("]")

    # Append closing sequence
    if closing_sequence:
        closing_str = "".join(closing_sequence)
        logger.warning(f"🔧 Repaired truncated JSON by adding: '{closing_str}'")
        json_str += closing_str

    return json_str


def parse_task_output(task_output: Any) -> Dict[str, Any]:  # noqa: C901
    """Parse task output with proper error handling.

    Args:
        task_output: Raw task output from CrewAI agent

    Returns:
        Parsed dict with gaps, questionnaire, and summary
    """
    raw_output = task_output.raw if hasattr(task_output, "raw") else str(task_output)

    # Strip markdown code block wrappers (handles ```json, ```JSON, plain ```)
    cleaned_output = raw_output.strip()
    cleaned_output = re.sub(r"^```[a-zA-Z0-9]*\s*\n?", "", cleaned_output)
    cleaned_output = re.sub(r"\n?```\s*$", "", cleaned_output)
    cleaned_output = cleaned_output.strip()

    try:
        # Try to parse as JSON
        result = json.loads(cleaned_output)

        # Ensure required structure exists
        if "gaps" not in result:
            result["gaps"] = {}
        if "questionnaire" not in result:
            result["questionnaire"] = {"sections": []}
        if "summary" not in result:
            result["summary"] = {
                "total_gaps": 0,
                "assets_analyzed": 0,
            }

        return result

    except json.JSONDecodeError:
        # Try to repair truncated JSON before falling back to extraction
        logger.info("Initial JSON parse failed, attempting truncated JSON repair")
        try:
            repaired_output = _repair_truncated_json(cleaned_output)
            result = json.loads(repaired_output)
            logger.info("✅ Successfully parsed repaired JSON")

            # Ensure required structure exists
            if "gaps" not in result:
                result["gaps"] = {}
            if "questionnaire" not in result:
                result["questionnaire"] = {"sections": []}
            if "summary" not in result:
                result["summary"] = {
                    "total_gaps": 0,
                    "assets_analyzed": 0,
                }

            return result
        except json.JSONDecodeError:
            logger.info("Truncated JSON repair also failed, falling back to extraction")

    # Fallback to extraction method
    logger.warning("Task output not valid JSON, attempting to extract data")
    logger.debug(f"Raw output length: {len(cleaned_output)} characters")
    logger.debug(f"Raw output preview (first 500 chars): {cleaned_output[:500]}")

    # ✅ FIX Bug #2: Extract JSON blocks, prioritizing larger/outer structures
    # Strategy: Extract all valid JSON, then prioritize by size and structure
    json_candidates = []
    idx = 0
    extraction_attempts = 0
    while idx < len(cleaned_output):
        start = cleaned_output.find("{", idx)
        if start == -1:
            break

        # Find matching closing brace
        depth = 0
        end = start
        for i in range(start, len(cleaned_output)):
            if cleaned_output[i] == "{":
                depth += 1
            elif cleaned_output[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end > start:
            extraction_attempts += 1
            try:
                potential_json = cleaned_output[start : end + 1]
                parsed = json.loads(potential_json)
                # Store candidate with metadata for prioritization
                json_candidates.append(
                    {
                        "data": parsed,
                        "size": end
                        - start,  # Track size to prioritize larger structures
                        "start_pos": start,
                    }
                )
                logger.debug(
                    f"✅ JSON candidate {len(json_candidates)}: "
                    f"Size={end - start}, Keys = {list(parsed.keys())}"
                )
            except json.JSONDecodeError as e:
                logger.debug(
                    f"⚠️ Extraction attempt {extraction_attempts} "
                    f"failed to parse JSON: {str(e)[:100]}"
                )

        idx = end + 1 if end > start else start + 1

    # Sort by size descending - prioritize larger/outer JSON structures over nested fragments
    json_candidates.sort(key=lambda x: x["size"], reverse=True)

    logger.info(
        f"📊 Total JSON candidates extracted: {len(json_candidates)} from "
        f"{extraction_attempts} attempts (sorted by size)"
    )

    # ✅ FIX Bug #2: Prioritize JSON blocks that have "gaps" key with data
    # Now working with sorted candidates (largest first = most likely to be parent structure)
    logger.debug("🔍 Analyzing candidates for 'gaps' key with populated data...")
    for idx, candidate_obj in enumerate(json_candidates):
        candidate = candidate_obj["data"]
        candidate_size = candidate_obj["size"]
        logger.debug(f"📋 Candidate {idx + 1} (size: {candidate_size} chars):")
        logger.debug(f"  - Keys present: {list(candidate.keys())}")

        if "gaps" in candidate:
            gaps_value = candidate.get("gaps", {})
            logger.debug(f"  - 'gaps' type: {type(gaps_value).__name__}")

            if isinstance(gaps_value, dict):
                logger.debug(f"  - 'gaps' sub-keys: {list(gaps_value.keys())}")

                # ✅ FIX Bug #2: Improved gap counting with validation
                gap_count = 0
                for priority in ["critical", "high", "medium", "low"]:
                    if priority in gaps_value:
                        gap_list = gaps_value[priority]
                        if isinstance(gap_list, list):
                            # Validate that items are actually gap objects (have required fields)
                            valid_gaps = [
                                g
                                for g in gap_list
                                if isinstance(g, dict)
                                and "field_name" in g
                                and "asset_id" in g
                            ]
                            count = len(valid_gaps)
                            gap_count += count
                            logger.debug(
                                f"    - {priority}: {count} valid gaps "
                                f"(raw: {len(gap_list)}, "
                                f"type: {type(gap_list).__name__})"
                            )
                        else:
                            logger.debug(
                                f"    - {priority}: NOT a list "
                                f"(type: {type(gap_list).__name__})"
                            )

                logger.debug(f"  - Total valid gaps: {gap_count}")

                if gap_count > 0:
                    logger.info(
                        f"✅ Selected JSON (size: {candidate_size}) with {gap_count} gaps "
                        f"from {len(json_candidates)} candidates (candidate {idx + 1})"
                    )
                    # Ensure required structure exists
                    if "questionnaire" not in candidate:
                        candidate["questionnaire"] = {"sections": []}
                    if "summary" not in candidate:
                        candidate["summary"] = {
                            "total_gaps": gap_count,
                            "assets_analyzed": 0,
                        }
                    return candidate
                else:
                    logger.warning(
                        f"⚠️ Candidate {idx + 1} has 'gaps' key "
                        f"but all arrays are empty or invalid"
                    )
            else:
                logger.warning(
                    f"⚠️ Candidate {idx + 1} has 'gaps' key but value is "
                    f"not a dict (type: {type(gaps_value).__name__})"
                )
        else:
            logger.debug("  - Missing 'gaps' key")

    # ✅ FIX Bug #2: Fallback with updated candidate structure
    logger.debug(
        "🔍 No candidates with populated gaps, looking for any with 'gaps' key..."
    )
    for idx, candidate_obj in enumerate(json_candidates):
        candidate = candidate_obj["data"]
        if "gaps" in candidate:
            logger.warning(
                f"⚠️ Selected candidate {idx + 1} "
                f"(size: {candidate_obj['size']}) with 'gaps' key but empty gaps"
            )
            if "questionnaire" not in candidate:
                candidate["questionnaire"] = {"sections": []}
            if "summary" not in candidate:
                candidate["summary"] = {"total_gaps": 0, "assets_analyzed": 0}
            return candidate

    logger.error(
        f"❌ No valid JSON with gaps found among {len(json_candidates)} candidates"
    )
    logger.error(f"📄 Raw output preview (500 chars): {cleaned_output[:500]}")
    if len(json_candidates) > 0:
        logger.error(
            f"📋 Candidate structures: {[list(c['data'].keys()) for c in json_candidates]}"
        )
        logger.error(f"📏 Candidate sizes: {[c['size'] for c in json_candidates]}")

    # Return minimal structure with raw output
    return {
        "gaps": {},
        "questionnaire": {"sections": []},
        "summary": {"total_gaps": 0, "assets_analyzed": 0},
        "raw_output": raw_output,
    }
