"""
Gap Detection Logic - Identifies missing critical attributes.

Handles asset-type-specific attribute checking and questionnaire response validation.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_questionnaire_response import (
    CollectionQuestionnaireResponse,
)

logger = logging.getLogger(__name__)


async def has_questionnaire_response(
    asset_id: UUID,
    field_name: str,
    collection_flow_id: UUID,
    db: AsyncSession,
) -> bool:
    """
    Check if approved questionnaire response exists for this field.

    Prevents re-asking questions users already answered in previous flows.
    This is PHASE 1 of intelligent gap detection (Bug #679).

    Args:
        asset_id: Asset being analyzed
        field_name: Attribute name (e.g., 'compliance_requirements')
        collection_flow_id: Current collection flow
        db: Database session

    Returns:
        True if approved response exists, False otherwise
    """
    # Check if user already answered this via questionnaire
    # Match on asset_id, question_category contains field_name, and validation_status = "approved"
    stmt = select(CollectionQuestionnaireResponse).where(
        CollectionQuestionnaireResponse.asset_id == asset_id,
        CollectionQuestionnaireResponse.question_category.contains(field_name),
        CollectionQuestionnaireResponse.validation_status == "approved",
    )
    result = await db.execute(stmt)
    response = result.scalar_one_or_none()

    if response:
        logger.debug(
            f"✓ Found approved questionnaire response for asset {asset_id}, "
            f"field '{field_name}' in response ID {response.id}"
        )

    return response is not None


async def identify_gaps_for_asset(
    asset: Any,
    attribute_mapping: Dict[str, Any],
    asset_type: str,
    collection_flow_id: UUID,
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    """
    Identify missing critical attributes for a single asset.

    PHASE 1 (Bug #679): Checks questionnaire responses to avoid re-asking questions.

    Args:
        asset: Asset model instance
        attribute_mapping: Asset-type-specific attribute mapping
        asset_type: Asset type (server, application, database, etc.)
        collection_flow_id: Collection flow UUID (for questionnaire check)
        db: Database session (for questionnaire check)

    Returns:
        List of gap dictionaries with asset-type-aware categorization
    """
    gaps = []

    for attr_name, attr_config in attribute_mapping.items():
        asset_fields = attr_config.get("asset_fields", [])

        # Check if asset has any of these fields populated
        has_value = False
        current_value = None

        for field in asset_fields:
            if "." in field:
                # Handle dotted notation (custom_attributes.field_name OR relationship.field)
                parts = field.split(".", 1)
                if hasattr(asset, parts[0]):
                    obj = getattr(asset, parts[0])

                    # Check if it's custom_attributes (JSON field)
                    if parts[0] == "custom_attributes":
                        if obj and parts[1] in obj:
                            has_value = True
                            current_value = obj[parts[1]]
                            break
                    # PHASE 2 Bug #679: Handle relationship attributes
                    # (resilience.rto_minutes, compliance_flags.compliance_scopes, etc.)
                    elif obj is not None and hasattr(obj, parts[1]):
                        related_value = getattr(obj, parts[1])
                        # For ARRAY types (like compliance_scopes), check if not empty
                        if isinstance(related_value, list):
                            if related_value:  # Non-empty list
                                has_value = True
                                current_value = related_value
                                break
                        # For scalar types, check for non-null
                        elif related_value is not None and related_value != "":
                            has_value = True
                            current_value = related_value
                            break
            else:
                # Direct column access (no dot notation)
                if hasattr(asset, field) and getattr(asset, field) is not None:
                    has_value = True
                    current_value = getattr(asset, field)
                    break

        if not has_value:
            # PHASE 1 (Bug #679): Check if user already answered this via questionnaire
            if await has_questionnaire_response(
                asset.id, attr_name, collection_flow_id, db
            ):
                logger.info(
                    f"⏭️ Skipping gap '{attr_name}' for asset '{asset.name}' - "
                    f"approved questionnaire response exists"
                )
                continue  # Skip this gap - user already provided the answer

            gaps.append(
                {
                    "asset_id": str(asset.id),
                    "asset_name": asset.name,
                    "field_name": attr_name,
                    "gap_type": "missing_field",
                    "gap_category": attr_config.get("category", "unknown"),
                    "priority": attr_config.get("priority", 3),
                    "current_value": current_value,
                    "suggested_resolution": "Manual collection required",
                    "confidence_score": None,  # No AI yet
                }
            )

    return gaps
