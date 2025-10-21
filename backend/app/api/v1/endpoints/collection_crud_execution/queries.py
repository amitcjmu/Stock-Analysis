"""
Collection Flow Execution - Query Operations
Read operations for collection flows including ensuring flow existence.
"""

import logging
import uuid

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import COLLECTION_CREATE_ROLES, require_role
from app.models import User
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
)
from app.models.collection_data_gap import CollectionDataGap
from app.schemas.collection_flow import CollectionFlowCreate, CollectionFlowResponse

# Import modular functions
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)


async def _add_gaps_to_existing_flow(
    db: AsyncSession,
    collection_flow: CollectionFlow,
    missing_attributes: dict[str, list[str]],
) -> None:
    """Add missing attribute gaps to an existing collection flow.

    Prevents duplicate gaps by checking if a gap already exists for the same
    asset/field combination before creating a new one.

    Args:
        db: Database session
        collection_flow: Existing collection flow to add gaps to
        missing_attributes: Dict mapping asset_id to list of missing attribute names
    """
    # Map critical attribute names to their categories (same as in create_collection_flow)
    ATTRIBUTE_CATEGORY_MAP = {
        # Infrastructure (6)
        "application_name": "infrastructure",
        "technology_stack": "infrastructure",
        "operating_system": "infrastructure",
        "cpu_cores": "infrastructure",
        "memory_gb": "infrastructure",
        "storage_gb": "infrastructure",
        # Application (8)
        "business_criticality": "application",
        "application_type": "application",
        "architecture_pattern": "application",
        "dependencies": "application",
        "user_base": "application",
        "data_sensitivity": "application",
        "compliance_requirements": "application",
        "sla_requirements": "application",
        # Business (4)
        "business_owner": "business",
        "annual_operating_cost": "business",
        "business_value": "business",
        "strategic_importance": "business",
        # Technical Debt (4)
        "code_quality_score": "technical_debt",
        "last_update_date": "technical_debt",
        "support_status": "technical_debt",
        "known_vulnerabilities": "technical_debt",
    }

    gaps_created = 0
    gaps_skipped = 0

    for asset_id_str, missing_attrs in missing_attributes.items():
        try:
            asset_uuid = uuid.UUID(asset_id_str)
        except ValueError:
            logger.warning(
                f"Invalid asset_id format in missing_attributes: {asset_id_str}"
            )
            continue

        for attr_name in missing_attrs:
            # Check if gap already exists for this asset/field combination
            existing_gap_result = await db.execute(
                select(CollectionDataGap).where(
                    and_(
                        CollectionDataGap.collection_flow_id == collection_flow.id,
                        CollectionDataGap.asset_id == asset_uuid,
                        CollectionDataGap.field_name == attr_name,
                    )
                )
            )
            existing_gap = existing_gap_result.scalar_one_or_none()

            if existing_gap:
                gaps_skipped += 1
                logger.debug(
                    f"Gap already exists for asset {asset_uuid} field {attr_name}, skipping"
                )
                continue

            # Determine category from mapping, default to "application" if not found
            category = ATTRIBUTE_CATEGORY_MAP.get(attr_name, "application")

            # Create new gap with asset_id in metadata (Bug #668 fix)
            gap = CollectionDataGap(
                collection_flow_id=collection_flow.id,
                asset_id=asset_uuid,
                field_name=attr_name,
                gap_type="missing_critical_attribute",
                gap_category=category,
                impact_on_sixr="high",  # Critical attributes block assessment
                priority=10,  # High priority
                resolution_status="identified",
                description=f"Missing critical attribute: {attr_name}",
                suggested_resolution=f"Provide value for {attr_name} via questionnaire",
                gap_metadata={  # Fixed: Use gap_metadata (Python attr) not metadata (DB column)
                    "source": "assessment_readiness",
                    "is_critical": True,
                    "required_for_assessment": True,
                    "asset_id": str(
                        asset_uuid
                    ),  # Critical: Required for asset writeback
                },
            )
            db.add(gap)
            gaps_created += 1

    if gaps_created > 0 or gaps_skipped > 0:
        await db.flush()  # Persist gaps immediately
        logger.info(
            f"✅ Added {gaps_created} new gaps ({gaps_skipped} skipped as duplicates) "
            f"for {len(missing_attributes)} assets in collection flow {collection_flow.flow_id}"
        )


async def ensure_collection_flow(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
    missing_attributes: dict[str, list[str]] | None = None,
    assessment_flow_id: str | None = None,
) -> CollectionFlowResponse:
    """Return an active Collection flow for the engagement, or create one via MFO.

    This enables seamless navigation from Discovery/Assessment to Collection without users
    needing to manually start a flow. It reuses any non-completed flow linked to the same
    assessment/discovery flow; if none exist, it creates a new one and returns it immediately.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context
        missing_attributes: Optional dict of asset_id -> list of missing attribute names
                           If provided, creates data gaps for specific attributes
        assessment_flow_id: Optional UUID of assessment flow to link to
                           If provided, only returns flows linked to this assessment

    Returns:
        CollectionFlowResponse for existing or newly created flow
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "ensure collection flows")

    # Validate tenant context early
    collection_validators.validate_tenant_context(context)

    try:
        # Try to find an active collection flow for this engagement
        # Bug Fix: If assessment_flow_id provided, only match flows linked to that assessment
        from uuid import UUID

        query_conditions = [
            CollectionFlow.client_account_id == context.client_account_id,
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.status.notin_(
                [
                    CollectionFlowStatus.COMPLETED.value,
                    CollectionFlowStatus.CANCELLED.value,
                ]
            ),
        ]

        # Bug Fix: Add assessment_flow_id filter if provided
        if assessment_flow_id:
            assessment_uuid = (
                UUID(assessment_flow_id)
                if isinstance(assessment_flow_id, str)
                else assessment_flow_id
            )
            query_conditions.append(
                CollectionFlow.assessment_flow_id == assessment_uuid
            )

        result = await db.execute(
            select(CollectionFlow)
            .where(*query_conditions)
            .order_by(CollectionFlow.created_at.desc())
            .limit(1)  # Ensure we only get one row
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Bug #668 Fix: Add missing attributes as gaps even when reusing flow
            if missing_attributes:
                await _add_gaps_to_existing_flow(db, existing, missing_attributes)
            return collection_serializers.build_collection_flow_response(existing)

        # Otherwise, create a new one (delegates to existing create logic)
        # Import locally to avoid circular import
        from app.api.v1.endpoints.collection_crud_create_commands import (
            create_collection_flow,
        )

        # Bug #668 Fix: Pass missing_attributes to trigger gap creation and questionnaire generation
        # Bug Fix: Pass assessment_flow_id to link collection flow to assessment
        flow_data = CollectionFlowCreate(
            automation_tier=AutomationTier.TIER_2.value,
            missing_attributes=missing_attributes,
            assessment_flow_id=assessment_flow_id,
        )
        return await create_collection_flow(flow_data, db, current_user, context)

    except HTTPException:
        # Pass through known HTTP exceptions intact
        raise
    except Exception:
        logger.error("Error ensuring collection flow", exc_info=True)
        # Sanitize error exposure
        raise HTTPException(status_code=500, detail="Failed to ensure collection flow")
