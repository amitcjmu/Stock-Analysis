"""
Question deduplication service for cross-asset questionnaires.

Per ADR-035: Deduplicate common questions asked across multiple assets.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def deduplicate_common_questions(
    sections: List[dict],
    assets: List[dict],
) -> dict:
    """
    Deduplicate questions that appear for multiple assets.

    Per ADR-035: Common questions (like "business_criticality") should be
    asked once and applied to all relevant assets.

    Strategy:
    1. Group questions by field_id within each section
    2. For duplicate field_ids, merge asset_ids
    3. Keep intelligent options from first occurrence
    4. Preserve asset-specific questions (unique to one asset)

    Args:
        sections: List of section dicts with questions
        assets: List of Asset dicts for metadata

    Returns:
        Deduplicated questionnaire structure with stats
    """
    question_map: Dict[str, dict] = {}

    for section in sections:
        section_id = section.get("section_id", "unknown")

        for question in section.get("questions", []):
            field_id = question.get("field_id")
            if not field_id:
                logger.warning(f"Question missing field_id in section {section_id}")
                continue

            # Use composite key: section_id:field_id
            # This allows same field_id in different sections
            composite_key = f"{section_id}:{field_id}"

            if composite_key in question_map:
                # Duplicate found - merge asset_ids
                existing = question_map[composite_key]

                # Merge asset_ids from metadata
                existing_asset_ids = set(
                    existing.get("metadata", {}).get("asset_ids", [])
                )
                new_asset_ids = set(question.get("metadata", {}).get("asset_ids", []))
                merged_asset_ids = list(existing_asset_ids | new_asset_ids)

                # Update existing question with merged asset_ids
                if "metadata" not in existing:
                    existing["metadata"] = {}

                existing["metadata"]["asset_ids"] = merged_asset_ids
                existing["metadata"]["applies_to_count"] = len(merged_asset_ids)

                logger.debug(
                    f"Deduplicated {field_id} in {section_id}: "
                    f"merged {len(new_asset_ids)} assets "
                    f"(total: {len(merged_asset_ids)} assets)"
                )
            else:
                # First occurrence - store with intelligent options
                question_map[composite_key] = question.copy()

                # Ensure metadata structure
                if "metadata" not in question_map[composite_key]:
                    question_map[composite_key]["metadata"] = {}

                if "asset_ids" not in question_map[composite_key]["metadata"]:
                    question_map[composite_key]["metadata"]["asset_ids"] = []

                question_map[composite_key]["metadata"]["applies_to_count"] = len(
                    question_map[composite_key]["metadata"]["asset_ids"]
                )

    # Rebuild sections with deduplicated questions
    deduplicated_sections = []
    section_map = {}

    for composite_key, question in question_map.items():
        section_id, _ = composite_key.split(":", 1)

        if section_id not in section_map:
            # Find original section metadata
            original_section = next(
                (s for s in sections if s.get("section_id") == section_id), None
            )

            if original_section:
                section_map[section_id] = {
                    "section_id": section_id,
                    "section_title": original_section.get("section_title", ""),
                    "section_description": original_section.get(
                        "section_description", ""
                    ),
                    "category": original_section.get("category", ""),
                    "questions": [],
                }
            else:
                # Fallback if original section not found
                section_map[section_id] = {
                    "section_id": section_id,
                    "section_title": section_id.replace("_", " ").title(),
                    "section_description": "",
                    "category": section_id.replace("section_", ""),
                    "questions": [],
                }

        section_map[section_id]["questions"].append(question)

    deduplicated_sections = list(section_map.values())

    # Calculate deduplication stats
    total_original = sum(len(s.get("questions", [])) for s in sections)
    total_deduplicated = sum(len(s.get("questions", [])) for s in deduplicated_sections)
    duplicates_removed = total_original - total_deduplicated

    logger.info(
        f"Deduplication: {total_original} questions → {total_deduplicated} questions "
        f"({duplicates_removed} duplicates removed, "
        f"{(duplicates_removed / total_original * 100):.1f}% reduction)"
    )

    return {
        "sections": deduplicated_sections,
        "total_questions": total_deduplicated,
        "deduplication_stats": {
            "original_count": total_original,
            "deduplicated_count": total_deduplicated,
            "duplicates_removed": duplicates_removed,
            "reduction_percentage": (
                (duplicates_removed / total_original * 100) if total_original > 0 else 0
            ),
        },
    }


def deduplicate_cross_asset_questions(sections: List[dict]) -> List[dict]:
    """
    Simplified deduplication when asset list not available.

    Args:
        sections: List of section dicts with questions

    Returns:
        List of deduplicated sections
    """
    result = deduplicate_common_questions(sections, [])
    return result["sections"]
