"""
Gap Detection Logic - Identifies missing critical attributes.

⚠️ DEPRECATION NOTICE (Day 13 - Issue #980):
This module is deprecated. Use app.services.gap_detection.GapAnalyzer instead.

ProgrammaticGapScanner has been refactored to use GapAnalyzer orchestrator with 5 shared inspectors:
- ColumnInspector: Asset SQLAlchemy columns
- EnrichmentInspector: Enrichment tables (resilience, compliance, etc.)
- JSONBInspector: JSONB fields (custom_attributes, technical_details)
- ApplicationInspector: CanonicalApplication metadata
- StandardsInspector: Architecture standards validation

This module is retained for backward compatibility with legacy code paths but will be removed
in a future refactoring. New code should NOT use these functions.

Legacy functionality:
- Handles asset-type-specific attribute checking
- PHASE 2 (Bug #679): Checks enriched asset data from unified assets table and canonical_applications
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.canonical_applications import CanonicalApplication
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
    Check if questionnaire response exists for this field from ANY flow in the engagement.

    CRITICAL FIX (Issue #797): Cross-flow data lookup to prevent duplicate gaps.
    Previously only checked current flow, now checks ALL flows in same engagement.

    Prevents re-asking questions users already answered in previous flows.
    This is PHASE 1 of intelligent gap detection (Bug #679).

    Args:
        asset_id: Asset being analyzed
        field_name: Attribute name (e.g., 'compliance_requirements')
        collection_flow_id: Current collection flow (for engagement lookup)
        db: Database session

    Returns:
        True if response exists from ANY flow in engagement, False otherwise
    """
    from app.models.collection_flow import CollectionFlow

    # STEP 1: Get engagement_id from current flow (for multi-tenant scoping)
    flow_stmt = select(CollectionFlow).where(CollectionFlow.id == collection_flow_id)
    flow_result = await db.execute(flow_stmt)
    current_flow = flow_result.scalar_one_or_none()

    if not current_flow:
        logger.warning(
            f"Could not find flow {collection_flow_id} for engagement lookup"
        )
        return False

    # STEP 2: Get ALL responses for this asset in the engagement (for flexible matching)
    stmt = (
        select(CollectionQuestionnaireResponse)
        .join(
            CollectionFlow,
            CollectionQuestionnaireResponse.collection_flow_id == CollectionFlow.id,
        )
        .where(
            CollectionQuestionnaireResponse.asset_id == asset_id,
            CollectionFlow.client_account_id == current_flow.client_account_id,
            CollectionFlow.engagement_id == current_flow.engagement_id,
            CollectionQuestionnaireResponse.validation_status == "validated",
        )
    )
    result = await db.execute(stmt)
    responses = list(result.scalars().all())

    # STEP 3: Flexible field name matching
    # Try multiple matching strategies for field names with different formats
    for response in responses:
        question_id = response.question_id or ""

        # Strategy 1: Exact match
        if field_name == question_id:
            logger.info(
                f"✓ CROSS-FLOW DATA FOUND (exact): Asset {asset_id}, field '{field_name}' "
                f"matched question_id '{question_id}' in flow {response.collection_flow_id}"
            )
            return True

        # Strategy 2: Strip custom_attributes prefix and compare
        normalized_question_id = question_id.replace("custom_attributes.", "")
        if field_name == normalized_question_id:
            logger.info(
                f"✓ CROSS-FLOW DATA FOUND (normalized): Asset {asset_id}, field '{field_name}' "
                f"matched normalized '{normalized_question_id}' in flow {response.collection_flow_id}"
            )
            return True

        # Strategy 3: Check if normalized question_id is a meaningful substring of field_name
        # e.g., "eol_assessment" should match "eol_technology_assessment"
        if (
            normalized_question_id
            and normalized_question_id in field_name
            and len(normalized_question_id) >= 3
        ):
            logger.info(
                f"✓ CROSS-FLOW DATA FOUND (substring): Asset {asset_id}, field '{field_name}' "
                f"contains '{normalized_question_id}' in flow {response.collection_flow_id}"
            )
            return True

        # Strategy 4: Check field name mappings for alternate names
        # e.g., "complexity" → "business_logic_complexity"
        # "vulnerabilities" → "security_vulnerabilities"
        if (
            field_name.endswith(normalized_question_id)
            and len(normalized_question_id) >= 5
        ):
            logger.info(
                f"✓ CROSS-FLOW DATA FOUND (suffix): Asset {asset_id}, field '{field_name}' "
                f"ends with '{normalized_question_id}' in flow {response.collection_flow_id}"
            )
            return True

    return False


async def get_enriched_asset_data(
    asset_id: UUID,
    asset_type: str,
    db: AsyncSession,
) -> Optional[Dict[str, Any]]:
    """
    Query enriched asset data from unified assets table and canonical_applications.

    PHASE 2 (Bug #679): Check if asset has already been enriched in asset tables.
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
            'technology_stack': 'Python, JavaScript',
            'business_criticality': 'High',
            'description': 'Customer portal application'
        }
    """
    asset_type_lower = asset_type.lower() if asset_type else ""

    # For applications, check CanonicalApplication table for deduplication data
    if asset_type_lower == "application":
        # First try CanonicalApplication for enriched metadata
        stmt = select(CanonicalApplication).where(CanonicalApplication.id == asset_id)
        result = await db.execute(stmt)
        canonical_app = result.scalar_one_or_none()

        if canonical_app:
            logger.debug(
                f"✓ Found canonical application data for asset {asset_id}: "
                f"tech_stack={canonical_app.technology_stack}, "
                f"criticality={canonical_app.business_criticality}"
            )
            return {
                "technology_stack": canonical_app.technology_stack,
                "business_criticality": canonical_app.business_criticality,
                "description": canonical_app.description,
            }

    # For all asset types (including applications if not in CanonicalApplication),
    # query unified assets table with asset_type filter
    stmt = select(Asset).where(
        Asset.id == asset_id,
        Asset.asset_type.ilike(asset_type_lower),
    )
    result = await db.execute(stmt)
    enriched = result.scalar_one_or_none()

    if enriched:
        # Extract asset-type-specific enriched fields
        if asset_type_lower == "server":
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
            logger.debug(
                f"✓ Found enriched database data for asset {asset_id}: "
                f"tech_stack={enriched.technology_stack}, version={enriched.os_version}, "
                f"size={enriched.storage_gb}GB"
            )
            return {
                "database_type": enriched.technology_stack,  # Database type stored in technology_stack
                "version": enriched.os_version,  # Database version stored in os_version
                "size_gb": enriched.storage_gb,
                "business_criticality": enriched.business_criticality
                or enriched.criticality,
            }
        elif asset_type_lower == "application":
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
        else:
            # Generic enriched data for other asset types
            logger.debug(
                f"✓ Found enriched data for asset {asset_id} (type: {asset_type_lower})"
            )
            return {
                "description": enriched.description,
                "environment": enriched.environment,
                # business_owner and technical_owner moved to asset_contacts table (Migration 113)
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
    PHASE 2 (Bug #679): Checks enriched asset data from unified assets table
                        (queried by asset_type filter) before generating gaps.

    Note: Complexity is high (C901) due to comprehensive gap detection logic
    that checks multiple data sources (unified assets table, Asset fields,
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

    # PHASE 2 (Bug #679): Get enriched asset data from unified assets table
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
