"""
Collection CRUD Helper Functions
Extracted helper functions for collection flow operations to keep files under 400 lines.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models import User
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import CollectionFlow
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse

logger = logging.getLogger(__name__)

# Semantic field mapping: response_field → gap_field
# Maps questionnaire field names (LLM-generated) to gap field names (from gap detection)
# This enables gap resolution when LLM generates slightly different field names
RESPONSE_TO_GAP_FIELD_MAPPING = {
    # Code quality variations
    "code_quality_metric_level": "code_quality_metrics",
    "code_quality": "code_quality_metrics",
    "code_quality_score": "code_quality_metrics",
    # Compliance variations
    "compliance_requirements": "compliance_constraints",
    "compliance_status": "compliance_constraints",
    # Resource specs - multiple response fields may map to single composite gap
    "cpu_cores": "cpu_memory_storage_specs",
    "memory_gb": "cpu_memory_storage_specs",
    "storage_gb": "cpu_memory_storage_specs",
    "ram_gb": "cpu_memory_storage_specs",
    "disk_space": "cpu_memory_storage_specs",
    # Documentation variations
    "documentation_completeness": "documentation_quality",
    "documentation_quality_assessment": "documentation_quality",
    "docs_status": "documentation_quality",
    # EOL variations
    "eol_assessment_status": "eol_technology_assessment",
    "eol_status": "eol_technology_assessment",
    "end_of_life_status": "eol_technology_assessment",
    # OS variations
    "operating_system": "operating_system_version",
    "os_version": "operating_system_version",
    "os_type": "operating_system_version",
    # Change tolerance variations
    "change_frequency": "change_tolerance",
    "change_window": "change_tolerance",
    # Business criticality variations
    "criticality": "business_criticality",
    "business_impact": "business_criticality",
    # User load variations
    "user_count": "user_load_patterns",
    "concurrent_users": "user_load_patterns",
    "peak_users": "user_load_patterns",
    # Data volume variations
    "data_size": "data_volume_characteristics",
    "database_size": "data_volume_characteristics",
}


def _find_gap_for_field(
    field_name: str,
    gap_index: Dict[str, Any],
) -> tuple[Any, Optional[str]]:
    """Find a gap in the index that matches the given field name.

    Tries multiple matching strategies:
    1. Exact match
    2. Custom_attributes prefix removal
    3. Composite ID extraction (asset_id__field_name)
    4. Semantic mapping (LLM variations → canonical names)

    Args:
        field_name: The field name from the response
        gap_index: Dictionary mapping field names to gap objects

    Returns:
        Tuple of (gap object or None, extracted_field or None)
    """
    gap = None
    extracted_field = None

    # Strategy 1: Exact match
    gap = gap_index.get(field_name)

    # Strategy 2: Custom_attributes prefix removal
    if not gap and field_name.startswith("custom_attributes."):
        normalized_field = field_name.replace("custom_attributes.", "")
        gap = gap_index.get(normalized_field)

    # Strategy 3: Composite ID extraction (asset_id__field_name)
    if not gap and "__" in field_name:
        parts = field_name.split("__", 1)
        if len(parts) == 2:
            extracted_field = parts[1]
            gap = gap_index.get(extracted_field)

    # Strategy 4: Semantic field mapping (LLM variations → canonical names)
    if not gap:
        lookup_field = extracted_field or field_name
        mapped_field = RESPONSE_TO_GAP_FIELD_MAPPING.get(lookup_field)
        if mapped_field:
            gap = gap_index.get(mapped_field)
            if gap:
                logger.info(f"✅ Semantic mapping: '{lookup_field}' → '{mapped_field}'")

    return gap, extracted_field


def validate_uuid(value: Optional[str], field_name: str) -> Optional[uuid.UUID]:
    """Validate and convert string to UUID, return None if invalid."""
    if not value:
        return None

    try:
        return uuid.UUID(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid UUID for {field_name}: {value} - {e}")
        return None


async def validate_asset_access(
    asset_id: Optional[str], context: RequestContext, db: AsyncSession
) -> Optional[Any]:
    """Validate asset access and return validated asset if found."""
    if not asset_id:
        return None

    # Validate UUID format first
    asset_uuid = validate_uuid(asset_id, "asset_id")
    if not asset_uuid:
        logger.warning(f"Invalid asset_id format: {asset_id}")
        return None

    from app.models.asset import Asset

    try:
        asset_result = await db.execute(
            select(Asset)
            .where(Asset.id == asset_uuid)
            .where(Asset.engagement_id == context.engagement_id)
            .where(Asset.client_account_id == context.client_account_id)
        )
        validated_asset = asset_result.scalar_one_or_none()

        if validated_asset:
            logger.info(
                f"Linking questionnaire responses to existing asset: {validated_asset.name} (ID: {asset_id})"
            )
        else:
            logger.warning(
                f"Asset {asset_id} not found or not accessible - proceeding without asset linkage"
            )

        return validated_asset
    except Exception as e:
        logger.warning(
            f"Failed to validate asset {asset_id}: {e} - proceeding without asset linkage"
        )
        return None


async def fetch_and_index_gaps(
    flow: CollectionFlow, db: AsyncSession
) -> Dict[str, Any]:
    """Fetch pending gaps for the flow and index them by field_name for quick lookup."""
    from app.models.collection_data_gap import CollectionDataGap

    gap_results = await db.execute(
        select(CollectionDataGap)
        .where(CollectionDataGap.collection_flow_id == flow.id)
        .where(CollectionDataGap.resolution_status == "pending")
    )
    pending_gaps = gap_results.scalars().all()

    # Index gaps by field_name for quick lookup
    gap_index = {}
    for gap in pending_gaps:
        if gap.field_name and gap.field_name.strip():
            gap_index[gap.field_name] = gap
        else:
            logger.warning(
                f"Gap {gap.id} has invalid field_name: '{gap.field_name}' - skipping"
            )

    logger.info(
        f"Indexed {len(gap_index)} pending gaps by field_name: {list(gap_index.keys())}"
    )
    return gap_index


def derive_response_type(value: Any) -> str:
    """Derive response type from the actual value."""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, (int, float)):
        return "number"
    elif isinstance(value, dict):
        return "object"
    elif isinstance(value, list):
        return "array"
    else:
        return "text"


async def create_response_records(
    form_responses: Dict[str, Any],
    form_metadata: Dict[str, Any],
    validation_results: Dict[str, Any],
    questionnaire_id: str,
    flow: CollectionFlow,
    asset_id: Optional[str],
    current_user: User,
    gap_index: Dict[str, Any],
    db: AsyncSession,
) -> List[CollectionQuestionnaireResponse]:
    """Create response records for form responses with proper gap_id linkage."""
    response_records = []
    logger.info(f"Processing {len(form_responses)} form responses")

    # Convert asset_id to UUID if provided (fallback for non-composite field IDs)
    default_asset_uuid = validate_uuid(asset_id, "asset_id") if asset_id else None

    for field_id, value in form_responses.items():
        # Validate field_id
        if not field_id or not field_id.strip():
            logger.warning(f"Skipping response with invalid field_id: '{field_id}'")
            continue

        # Skip empty responses
        if value is None or value == "":
            logger.debug(f"Skipping empty response for field: {field_id}")
            continue

        logger.debug(
            f"Processing response for field {field_id}: {type(value).__name__}"
        )

        # CRITICAL FIX: Extract asset_id from composite field ID (format: {asset_id}__{field_id})
        # This handles multi-asset forms where each question has a unique ID prefixed with asset_id
        response_asset_uuid = default_asset_uuid
        if "__" in field_id:
            parts = field_id.split("__", 1)
            potential_asset_id = parts[0]
            # Validate it's a UUID
            validated_uuid = validate_uuid(potential_asset_id, "extracted_asset_id")
            if validated_uuid:
                response_asset_uuid = validated_uuid
                logger.info(
                    f"Extracted asset_id from composite field ID: {potential_asset_id}"
                )

        # CRITICAL FIX: Lookup gap by field_name, handling composite field IDs
        # Extract actual field name from composite ID (format: {asset_id}__{field_name})
        actual_field_name = field_id
        if "__" in field_id:
            parts = field_id.split("__", 1)
            if len(parts) == 2:
                # Try the extracted field name first
                actual_field_name = parts[1]
                # Also try removing any trailing asset_id suffix (e.g., "data_quality_778f9a98..." -> "data_quality")
                if actual_field_name and actual_field_name.count("_") > 2:
                    # Might have asset_id suffix, try base field name
                    base_field = (
                        actual_field_name.rsplit("_", 1)[0]
                        if "_" in actual_field_name
                        else actual_field_name
                    )
                    gap = (
                        gap_index.get(base_field)
                        or gap_index.get(actual_field_name)
                        or gap_index.get(field_id)
                    )
                else:
                    gap = gap_index.get(actual_field_name) or gap_index.get(field_id)
            else:
                gap = gap_index.get(field_id)
        else:
            gap = gap_index.get(field_id)

        gap_id = gap.id if gap else None

        if gap:
            logger.info(
                f"Linking response for field '{field_id}' (actual: '{actual_field_name}') to gap {gap_id}"
            )
        else:
            logger.debug(
                f"No pending gap found for field '{field_id}' "
                f"(tried: '{actual_field_name}') - creating unlinked response"
            )

        # Create response record with proper gap_id linkage
        response = CollectionQuestionnaireResponse(
            collection_flow_id=flow.id,
            gap_id=gap_id,  # CRITICAL: Link response to gap for asset write-back
            asset_id=response_asset_uuid,  # Link response directly to asset (extracted per field)
            questionnaire_type="adaptive_form",
            question_category=form_metadata.get("form_id", "general"),
            question_id=field_id,
            question_text=field_id,  # This should ideally come from the questionnaire definition
            response_type=derive_response_type(value),  # Derive from actual value type
            response_value=({"value": value} if not isinstance(value, dict) else value),
            confidence_score=form_metadata.get("confidence_score"),
            validation_status=(
                "validated" if validation_results.get("isValid") else "pending"
            ),
            responded_by=current_user.id,
            responded_at=datetime.utcnow(),
            response_metadata={
                "questionnaire_id": questionnaire_id,
                "application_id": form_metadata.get(
                    "application_id"
                ),  # Keep for backward compatibility
                "asset_id": (
                    str(response_asset_uuid) if response_asset_uuid else None
                ),  # Store extracted per-field asset_id
                "completion_percentage": form_metadata.get("completion_percentage"),
                "submitted_at": form_metadata.get("submitted_at"),
                "gap_id": (
                    str(gap_id) if gap_id else None
                ),  # Track gap linkage in metadata
            },
        )

        db.add(response)
        response_records.append(response)

    logger.info(f"Created {len(response_records)} response records")
    return response_records


async def resolve_data_gaps(
    gap_index: Dict[str, Any],
    form_responses: Dict[str, Any],
    db: AsyncSession,
) -> int:
    """Mark gaps as resolved for fields that received responses."""
    gaps_resolved = 0

    # 🔍 DIAGNOSTIC LOGGING (Issue #980): Compare gap field names vs response field names
    logger.info(
        f"🔍 Gap Resolution - Comparing field names:\n"
        f"  Gap index has {len(gap_index)} fields: {list(gap_index.keys())}\n"
        f"  Form responses has {len(form_responses)} fields: {list(form_responses.keys())}"
    )

    # Check which gaps should be marked as resolved based on form responses
    for field_name, value in form_responses.items():
        # Skip empty responses
        if value is None or value == "":
            continue

        # Validate field name
        if not field_name or not field_name.strip():
            logger.warning(
                f"Skipping resolution for invalid field_name: '{field_name}'"
            )
            continue

        # Use multi-strategy gap matching (extracted to reduce complexity)
        gap, extracted_field = _find_gap_for_field(field_name, gap_index)

        # Log unmatched fields for debugging
        if not gap:
            lookup_field = extracted_field or field_name
            logger.warning(
                f"🔍 NO MATCH: Response field '{field_name}' "
                f"(lookup: '{lookup_field}') not found in gap_index. "
                f"Available gaps: {list(gap_index.keys())}"
            )

        if gap:
            # Mark gap as resolved
            gap.resolution_status = "resolved"
            gap.resolved_at = datetime.utcnow()
            gap.resolved_by = "manual_submission"

            # ✅ FIX 0.1: Populate resolved_value (Issue #980 - Critical Bug Fix)
            # Store the actual response value so downstream writeback can use it
            import json

            if isinstance(value, dict):
                gap.resolved_value = json.dumps(value.get("value", value))
            elif isinstance(value, list):
                gap.resolved_value = json.dumps(value)
            else:
                gap.resolved_value = str(value) if value is not None else ""

            gaps_resolved += 1

            logger.info(
                f"Resolved gap {gap.id} ({gap.field_name}) through manual submission "
                f"with value: {gap.resolved_value[:50]}..."
            )

            # ✅ CRITICAL FIX: Also resolve ALL OTHER gaps for same (asset_id, field_name)
            # The unique constraint allows multiple gap_types per field, but when user
            # provides an answer, ALL gaps for that field should be marked resolved.
            # This prevents duplicate gaps from appearing in new collection flows.
            if gap.asset_id:
                additional_resolved = await db.execute(
                    update(CollectionDataGap)
                    .where(
                        and_(
                            CollectionDataGap.asset_id == gap.asset_id,
                            CollectionDataGap.field_name == gap.field_name,
                            CollectionDataGap.resolution_status == "pending",
                            CollectionDataGap.id
                            != gap.id,  # Exclude already-updated gap
                        )
                    )
                    .values(
                        resolution_status="resolved",
                        resolved_at=datetime.utcnow(),
                        resolved_by="manual_submission",
                        resolved_value=gap.resolved_value,
                    )
                )
                additional_count = additional_resolved.rowcount
                if additional_count > 0:
                    gaps_resolved += additional_count
                    logger.info(
                        f"🔄 Also resolved {additional_count} additional gap(s) for "
                        f"field '{gap.field_name}' (different gap_types)"
                    )

    if gaps_resolved > 0:
        logger.info(f"Resolved {gaps_resolved} data gaps through manual submission")

    return gaps_resolved


async def apply_asset_writeback(
    gaps_resolved: int,
    flow: CollectionFlow,
    context: RequestContext,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Apply resolved gaps to assets via write-back service."""
    # DIAGNOSTIC: Log entry point
    logger.info(
        f"🔍 WRITEBACK START: gaps_resolved={gaps_resolved}, flow_id={flow.id}, "
        f"engagement_id={context.engagement_id}, client_account_id={context.client_account_id}"
    )

    if gaps_resolved <= 0:
        logger.info(f"🔍 WRITEBACK SKIP: gaps_resolved={gaps_resolved} <= 0")
        return

    try:
        from app.services.flow_configs.collection_handlers.asset_handlers import (
            apply_resolved_gaps_to_assets,
        )

        # Create context for asset write-back with proper tenant scoping
        writeback_context = {
            "engagement_id": context.engagement_id,
            "client_account_id": context.client_account_id,
            "user_id": current_user.id,
        }
        logger.info(f"🔍 WRITEBACK CONTEXT: {writeback_context}")

        await apply_resolved_gaps_to_assets(db, flow.id, writeback_context)
        logger.info(f"✅ Successfully applied {gaps_resolved} resolved gaps to assets")

    except Exception as e:
        logger.error(
            f"❌ Asset write-back failed after manual submission: {e}", exc_info=True
        )
        # Don't fail the entire operation if write-back fails


def update_flow_progress(
    flow: CollectionFlow, form_metadata: Dict[str, Any], flow_id: str
) -> None:
    """Update flow status and progress based on completion percentage."""
    completion_percentage = form_metadata.get("completion_percentage", 0)
    if completion_percentage >= 100:
        logger.info(f"Marking flow {flow_id} as completed (100% completion)")
        flow.status = "completed"
        flow.progress_percentage = 100
    else:
        old_progress = flow.progress_percentage
        flow.progress_percentage = form_metadata.get(
            "completion_percentage", flow.progress_percentage
        )
        logger.info(
            f"Updated flow progress from {old_progress} to {flow.progress_percentage}"
        )
