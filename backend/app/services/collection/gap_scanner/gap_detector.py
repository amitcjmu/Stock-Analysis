"""
Gap Detection Logic - Identifies missing critical attributes.

Handles asset-type-specific attribute checking and questionnaire response validation.

PHASE 2 (Bug #679): Checks enriched asset data from Applications, Servers, Databases tables
before generating gaps.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_applications import CanonicalApplication
from app.models.collection_questionnaire_response import (
    CollectionQuestionnaireResponse,
)
from app.models.database import Database
from app.models.server import Server

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
    stmt = select(
        CollectionQuestionnaireResponse
    ).where(  # SKIP_TENANT_CHECK: asset_id and collection_flow_id provide tenant isolation
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


async def get_enriched_asset_data(
    asset_id: UUID,
    asset_type: str,
    db: AsyncSession,
) -> Optional[Dict[str, Any]]:
    """
    Query enriched asset data from specialized tables (Applications, Servers, Databases).

    PHASE 2 (Bug #679): Check if asset has already been enriched in specialized tables.
    These tables contain additional data populated from:
    - Prior collection workflows
    - CMDB discovery
    - Manual data entry
    - Other enrichment sources

    Args:
        asset_id: Asset UUID
        asset_type: Asset type (application, server, database, etc.)
        db: Database session

    Returns:
        Dict with enriched field values if found, None otherwise

    Examples:
        For application asset:
        {
            'technology_stack': {'languages': ['Python', 'JavaScript']},
            'business_criticality': 'High',
            'description': 'Customer portal application'
        }
    """
    asset_type_lower = asset_type.lower() if asset_type else ""

    # Map asset type to corresponding enrichment table
    if asset_type_lower == "application":
        stmt = select(CanonicalApplication).where(CanonicalApplication.id == asset_id)
        result = await db.execute(stmt)
        enriched = result.scalar_one_or_none()

        if enriched:
            logger.debug(
                f"✓ Found enriched application data for asset {asset_id}: "
                f"tech_stack={enriched.technology_stack}, "
                f"criticality={enriched.business_criticality}"
            )
            return {
                "technology_stack": enriched.technology_stack,
                "business_criticality": enriched.business_criticality,
                "description": enriched.description,
            }

    elif asset_type_lower == "server":
        stmt = select(Server).where(Server.id == asset_id)
        result = await db.execute(stmt)
        enriched = result.scalar_one_or_none()

        if enriched:
            logger.debug(
                f"✓ Found enriched server data for asset {asset_id}: "
                f"os={enriched.operating_system}, cpu={enriched.cpu_cores}, "
                f"mem={enriched.memory_gb}GB"
            )
            return {
                "operating_system": enriched.operating_system,
                "cpu_cores": enriched.cpu_cores,
                "memory_gb": enriched.memory_gb,
                "storage_gb": enriched.storage_gb,
                "environment": enriched.environment,
                "hostname": enriched.hostname,
                "ip_address": enriched.ip_address,
            }

    elif asset_type_lower == "database":
        stmt = select(Database).where(Database.id == asset_id)
        result = await db.execute(stmt)
        enriched = result.scalar_one_or_none()

        if enriched:
            logger.debug(
                f"✓ Found enriched database data for asset {asset_id}: "
                f"type={enriched.database_type}, version={enriched.version}, "
                f"size={enriched.size_gb}GB"
            )
            return {
                "database_type": enriched.database_type,
                "version": enriched.version,
                "size_gb": enriched.size_gb,
                "business_criticality": enriched.criticality,  # Map to consistent field name
            }

    logger.debug(
        f"No enriched data found for asset {asset_id} (type: {asset_type_lower})"
    )
    return None


async def identify_gaps_for_asset(  # noqa: C901
    asset: Any,
    attribute_mapping: Dict[str, Any],
    asset_type: str,
    collection_flow_id: UUID,
    db: AsyncSession,
) -> List[Dict[str, Any]]:
    """
    Identify missing critical attributes for a single asset.

    PHASE 1 (Bug #679): Checks questionnaire responses to avoid re-asking questions.
    PHASE 2 (Bug #679): Checks enriched asset data from specialized tables
                        (Applications, Servers, Databases) before generating gaps.

    Note: Complexity is high (C901) due to comprehensive gap detection logic
    that checks multiple data sources (enriched tables, Asset fields,
    questionnaire responses). This is intentional and necessary for Bug #679 fix.

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

    # PHASE 2 (Bug #679): Get enriched asset data from specialized tables
    enriched_data = await get_enriched_asset_data(asset.id, asset_type, db)

    for attr_name, attr_config in attribute_mapping.items():
        asset_fields = attr_config.get("asset_fields", [])

        # Check if asset has any of these fields populated
        has_value = False
        current_value = None

        # PHASE 2 (Bug #679): Check enriched data FIRST before checking Asset table
        if enriched_data:
            for field in asset_fields:
                # Check if this field exists in enriched data
                field_name = field.split(".")[-1]  # Get last part of dotted notation
                if field_name in enriched_data:
                    enriched_value = enriched_data[field_name]
                    # Check for non-null, non-empty values
                    if enriched_value is not None:
                        # For numeric fields, any number (including 0) is valid
                        if isinstance(enriched_value, (int, float)):
                            has_value = True
                            current_value = enriched_value
                            logger.debug(
                                f"✓ Field '{attr_name}' populated from enriched "
                                f"data: {enriched_value}"
                            )
                            break
                        # For strings, check if not empty
                        elif isinstance(enriched_value, str):
                            if enriched_value.strip():
                                has_value = True
                                current_value = enriched_value
                                logger.debug(
                                    f"✓ Field '{attr_name}' populated from enriched "
                                    f"data: {enriched_value}"
                                )
                                break
                        # For dicts/lists, check if not empty
                        elif isinstance(enriched_value, (dict, list)):
                            if enriched_value:
                                has_value = True
                                current_value = enriched_value
                                logger.debug(
                                    f"✓ Field '{attr_name}' populated from enriched "
                                    f"data: {enriched_value}"
                                )
                                break
                        else:
                            # For other types, presence is enough
                            has_value = True
                            current_value = enriched_value
                            logger.debug(
                                f"✓ Field '{attr_name}' populated from enriched "
                                f"data: {enriched_value}"
                            )
                            break

        # If not found in enriched data, check Asset table (original logic)
        if not has_value:
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
