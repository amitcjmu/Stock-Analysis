"""
Data Cleansing API - Validation Module
Helper functions for validating flows and retrieving data imports.
"""

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_import.core import DataImport
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


async def _validate_and_get_flow(
    flow_id: str, flow_repo: DiscoveryFlowRepository
) -> Any:
    """Validate flow exists and user has access."""
    try:
        flow = await flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "failed",
                    "error_code": "FLOW_NOT_FOUND",
                    "details": {"flow_id": flow_id, "message": "Flow not found"},
                },
            )
        return flow
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "failed",
                "error_code": "FLOW_ACCESS_FAILED",
                "details": {
                    "flow_id": flow_id,
                    "message": "Failed to access flow",
                    "error": str(e),
                },
            },
        )


async def _get_data_import_for_flow(flow_id: str, flow: Any, db: AsyncSession) -> Any:
    """Get data import for the given flow."""
    from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

    # First try to get data import via discovery flow's data_import_id
    data_import = None
    if flow.data_import_id:
        data_import_query = select(DataImport).where(
            DataImport.id == flow.data_import_id
        )
        data_import_result = await db.execute(data_import_query)
        data_import = data_import_result.scalar_one_or_none()

    # If not found, try master flow ID lookup
    if not data_import:
        logger.info(
            f"Flow {flow_id} has no data_import_id, trying master flow ID lookup"
        )

        # Get the database ID for this flow_id (FK references id, not flow_id)
        db_id_query = select(CrewAIFlowStateExtensions.id).where(
            CrewAIFlowStateExtensions.flow_id == flow_id
        )
        db_id_result = await db.execute(db_id_query)
        flow_db_id = db_id_result.scalar_one_or_none()

        if flow_db_id:
            # Look for data imports with this master_flow_id
            import_query = (
                select(
                    DataImport
                )  # SKIP_TENANT_CHECK - master_flow_id FK enforces isolation
                .where(DataImport.master_flow_id == flow_db_id)
                .order_by(DataImport.created_at.desc())
                .limit(1)
            )

            import_result = await db.execute(import_query)
            data_import = import_result.scalar_one_or_none()

    return data_import
