"""Output parsing utilities for gap analysis."""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_task_output(task_output: Any) -> Dict[str, Any]:  # noqa: C901
    """Parse task output with proper error handling.

    Args:
        task_output: Raw task output from CrewAI agent

    Returns:
        Parsed dict with gaps, questionnaire, and summary
    """
    raw_output = task_output.raw if hasattr(task_output, "raw") else str(task_output)

    try:
        # Try to parse as JSON
        result = json.loads(raw_output)

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
        logger.warning("Task output not valid JSON, attempting to extract data")
        logger.debug(f"Raw output length: {len(raw_output)} characters")
        logger.debug(f"Raw output preview (first 500 chars): {raw_output[:500]}")

        # ✅ FIX Bug #2: Extract JSON blocks, prioritizing larger/outer structures
        # Strategy: Extract all valid JSON, then prioritize by size and structure
        json_candidates = []
        idx = 0
        extraction_attempts = 0
        while idx < len(raw_output):
            start = raw_output.find("{", idx)
            if start == -1:
                break

            # Find matching closing brace
            depth = 0
            end = start
            for i in range(start, len(raw_output)):
                if raw_output[i] == "{":
                    depth += 1
                elif raw_output[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break

            if end > start:
                extraction_attempts += 1
                try:
                    potential_json = raw_output[start : end + 1]
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
                        f"✅ JSON candidate {len(json_candidates)}: Size={end - start}, Keys = {list(parsed.keys())}"
                    )
                except json.JSONDecodeError as e:
                    logger.debug(
                        f"⚠️ Extraction attempt {extraction_attempts} failed to parse JSON: {str(e)[:100]}"
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
                                    f"    - {priority}: NOT a list (type: {type(gap_list).__name__})"
                                )

                    logger.debug(f"  - Total valid gaps: {gap_count}")

                    if gap_count > 0:
                        logger.info(
                            f"✅ Selected JSON (size: {candidate_size}) with {gap_count} gaps from "
                            f"{len(json_candidates)} candidates (candidate {idx + 1})"
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
                            f"⚠️ Candidate {idx + 1} has 'gaps' key but all arrays are empty or invalid"
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
                    f"⚠️ Selected candidate {idx + 1} (size: {candidate_obj['size']}) with 'gaps' key but empty gaps"
                )
                if "questionnaire" not in candidate:
                    candidate["questionnaire"] = {"sections": []}
                if "summary" not in candidate:
                    candidate["summary"] = {"total_gaps": 0, "assets_analyzed": 0}
                return candidate

        logger.error(
            f"❌ No valid JSON with gaps found among {len(json_candidates)} candidates"
        )
        logger.error(f"📄 Raw output preview (500 chars): {raw_output[:500]}")
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
