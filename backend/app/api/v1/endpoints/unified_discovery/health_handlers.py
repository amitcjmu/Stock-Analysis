"""
Health Check Handlers for Unified Discovery

Handles health check endpoints for the unified discovery service.
Extracted from the main unified_discovery.py file for better maintainability.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.discovery_flow import DiscoveryFlow
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.asset import Asset

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for the unified discovery API."""
    return {
        "status": "healthy",
        "service": "unified_discovery",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": {
            "dependency_analysis": "active",
            "agent_insights": "active",
            "flow_management": "active",
            "clarifications": "active",
            "data_extraction": "active",
            "asset_listing": "active",
            "field_mapping": "active",
        },
    }


@router.get("/health/asset-pipeline/{flow_id}")
async def check_asset_pipeline_health(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Check health of asset pipeline for a specific flow."""

    # Get discovery flow using flow_id column, not primary key
    discovery_flow = await db.scalar(
        select(DiscoveryFlow)
        .where(DiscoveryFlow.flow_id == flow_id)
        .where(DiscoveryFlow.client_account_id == context.client_account_id)
    )
    if not discovery_flow:
        return {"error": "Flow not found"}

    # Get data import
    data_import = await db.scalar(
        select(DataImport)
        .where(DataImport.master_flow_id == flow_id)
        .where(DataImport.client_account_id == context.client_account_id)
    )

    # Count raw import records
    raw_count = (
        await db.scalar(
            select(func.count())
            .select_from(RawImportRecord)
            .where(RawImportRecord.master_flow_id == flow_id)
        )
        or 0
    )

    # Count assets
    asset_count = (
        await db.scalar(
            select(func.count())
            .select_from(Asset)
            .where(Asset.discovery_flow_id == discovery_flow.id)
        )
        or 0
    )

    return {
        "flow_id": flow_id,
        "data_import_exists": bool(data_import),
        "raw_records_count": raw_count,
        "assets_count": asset_count,
        "current_phase": discovery_flow.current_phase,
        "status": discovery_flow.status,
        "can_create_assets": raw_count > 0 and asset_count == 0,
        "field_mapping_completed": discovery_flow.field_mapping_completed,
        "data_cleansing_completed": discovery_flow.data_cleansing_completed,
        "asset_inventory_completed": discovery_flow.asset_inventory_completed,
    }
