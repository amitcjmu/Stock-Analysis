"""
Decommission Flow Query Endpoints

Handles read operations for decommission flows following ADR-006 MFO pattern.
These endpoints retrieve flow lists and eligible systems for the Overview dashboard.

Reference: backend/app/api/v1/endpoints/collection_crud_queries/lists.py
Per ADR-012: Queries child flows (decommission_flows table) for operational data
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import verify_client_access
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.asset.models import Asset
from app.models.decommission_flow.core_models import DecommissionFlow
from app.schemas.decommission_flow.responses import (
    DecommissionFlowListItem,
    EligibleSystemResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[DecommissionFlowListItem])
async def list_decommission_flows(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=500, description="Maximum flows to return"),
    offset: int = Query(0, ge=0, description="Number of flows to skip"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
) -> List[DecommissionFlowListItem]:
    """
    List all decommission flows for client/engagement.

    Per ADR-006: Queries child flows (decommission_flows table)
    Per ADR-012: Returns operational data for UI display
    Multi-tenant scoping: client_account_id + engagement_id

    Query Parameters:
    - **status**: Optional status filter (initialized/running/paused/completed/failed)
    - **limit**: Maximum number of flows to return (default: 100, max: 500)
    - **offset**: Number of flows to skip for pagination (default: 0)

    Returns:
    - List of decommission flow summary items with status, phase, and metrics
    """
    try:
        logger.info(
            safe_log_format(
                "Listing decommission flows: client_account_id={client_account_id}, "
                "engagement_id={engagement_id}, status={status}",
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                status=status or "all",
            )
        )

        # Build query with multi-tenant scoping (REQUIRED per architecture)
        stmt = select(DecommissionFlow).where(
            DecommissionFlow.client_account_id == UUID(client_account_id),
            DecommissionFlow.engagement_id == UUID(engagement_id),
        )

        # Optional status filter
        if status:
            stmt = stmt.where(DecommissionFlow.status == status)

        # Order by creation time (newest first) and apply pagination
        stmt = (
            stmt.order_by(DecommissionFlow.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)
        flows = result.scalars().all()

        logger.info(
            safe_log_format("Found {count} decommission flows", count=len(flows))
        )

        # Transform to response model (snake_case fields)
        return [
            DecommissionFlowListItem(
                flow_id=str(flow.flow_id),
                master_flow_id=str(flow.master_flow_id),
                flow_name=flow.flow_name or f"Decommission-{str(flow.flow_id)[:8]}",
                status=flow.status,
                current_phase=flow.current_phase,
                system_count=flow.system_count,
                estimated_savings=float(flow.estimated_annual_savings or 0),
                created_at=flow.created_at.isoformat(),
                updated_at=flow.updated_at.isoformat(),
            )
            for flow in flows
        ]

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Invalid UUID in decommission flow list request: {str_e}",
                str_e=str(e),
            )
        )
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")
    except Exception as e:
        logger.error(
            safe_log_format("Failed to list decommission flows: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve decommission flows"
        )


@router.get("/eligible-systems", response_model=List[EligibleSystemResponse])
async def get_eligible_systems(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
) -> List[EligibleSystemResponse]:
    """
    Get systems eligible for decommission.

    Eligibility criteria:
    1. **six_r_strategy = "Retire"** (from Assessment Flow)
    2. **OR status = "decommissioned"** (manually marked)
    3. **Not already in an active decommission flow**

    Per Issue #948: Wave integration sets decommission readiness
    Per Issue #947: Assessment sets six_r_strategy = "Retire"

    Multi-tenant scoping: client_account_id + engagement_id

    Returns:
    - List of assets eligible for decommission with cost and status info
    """
    try:
        logger.info(
            safe_log_format(
                "Getting eligible systems: client_account_id={client_account_id}, "
                "engagement_id={engagement_id}",
                client_account_id=client_account_id,
                engagement_id=engagement_id,
            )
        )

        # Query assets with Retire strategy OR explicitly marked for decommission
        # Per migration_fields.py: six_r_strategy options include "retire"
        # Per migration_fields.py: status can be "decommissioned"
        asset_stmt = select(Asset).where(
            Asset.client_account_id == UUID(client_account_id),
            Asset.engagement_id == UUID(engagement_id),
            or_(
                # Case-insensitive match for six_r_strategy
                Asset.six_r_strategy.ilike("%retire%"),
                Asset.status == "decommissioned",
            ),
        )

        # Get active decommission flow system IDs to exclude
        # Per core_models.py: selected_system_ids is ARRAY(UUID)
        # Active statuses: initialized, decommission_planning, data_migration, system_shutdown
        active_flow_stmt = select(DecommissionFlow.selected_system_ids).where(
            DecommissionFlow.client_account_id == UUID(client_account_id),
            DecommissionFlow.engagement_id == UUID(engagement_id),
            DecommissionFlow.status.in_(
                [
                    "initialized",
                    "decommission_planning",
                    "data_migration",
                    "system_shutdown",
                ]
            ),
        )

        # Execute both queries
        asset_result = await db.execute(asset_stmt)
        assets = asset_result.scalars().all()

        active_flow_result = await db.execute(active_flow_stmt)
        active_system_ids = set()
        for row in active_flow_result.scalars():
            if row:  # selected_system_ids is an array
                active_system_ids.update(str(sid) for sid in row)

        logger.info(
            safe_log_format(
                "Found {total_assets} assets with Retire strategy, "
                "{active_count} already in active flows",
                total_assets=len(assets),
                active_count=len(active_system_ids),
            )
        )

        # Filter out assets already being decommissioned
        eligible_assets = [a for a in assets if str(a.id) not in active_system_ids]

        logger.info(
            safe_log_format(
                "Returning {eligible_count} eligible systems",
                eligible_count=len(eligible_assets),
            )
        )

        # Transform to response model (snake_case fields)
        # Per cmdb_fields.py: annual_cost_estimate is the cost field
        return [
            EligibleSystemResponse(
                asset_id=str(asset.id),
                asset_name=asset.asset_name or "Unknown",
                six_r_strategy=asset.six_r_strategy,
                annual_cost=float(asset.annual_cost_estimate or 0),
                decommission_eligible=True,  # All returned assets are eligible
                grace_period_end=None,  # Not yet implemented in Asset model
                retirement_reason=(
                    "Marked for retirement via Assessment"
                    if asset.six_r_strategy
                    else "Manually marked as decommissioned"
                ),
            )
            for asset in eligible_assets
        ]

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Invalid UUID in eligible systems request: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")
    except Exception as e:
        logger.error(
            safe_log_format("Failed to get eligible systems: {str_e}", str_e=str(e))
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve eligible systems"
        )
