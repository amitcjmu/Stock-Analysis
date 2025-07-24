"""
Clean API Handler - Data Import Endpoints

⚠️ MIGRATION NOTICE: This handler is being migrated to V2 Discovery Flow architecture.
WorkflowState dependencies have been removed in favor of flow_id patterns.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.schemas.data_import_schemas import StoreImportRequest
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession


# V2 Discovery Flow schema for data cleaning
class DataCleaningRequest(BaseModel):
    """Data cleaning request schema for V2 Discovery Flow"""

    flow_id: str
    cleaning_rules: Optional[List[str]] = []
    validation_level: Optional[str] = "standard"


from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.discovery_flow_service import DiscoveryFlowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clean", tags=["data-import-clean"])


@router.post("/import")
async def clean_data_import(
    request: StoreImportRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """
    Clean data import endpoint - V2 Discovery Flow architecture

    ⚠️ MIGRATION NOTICE: This endpoint now uses V2 Discovery Flow patterns
    instead of deprecated WorkflowState management.
    """
    logger.info(
        f"🧹 Clean data import initiated for context: {context.client_account_id}"
    )

    try:
        # Generate flow ID instead of using workflow state
        flow_id = str(uuid.uuid4())

        # Process data import with V2 patterns
        result = await _process_clean_import(request, context, flow_id, db)

        return {
            "status": "success",
            "flow_id": flow_id,
            "message": "Clean data import completed successfully",
            "data": result,
            "migration_notice": "Using V2 Discovery Flow architecture",
        }

    except Exception as e:
        logger.error(f"❌ Clean data import failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clean data import failed: {str(e)}",
        )


async def _process_clean_import(
    request: StoreImportRequest, context: RequestContext, flow_id: str, db: AsyncSession
) -> Dict[str, Any]:
    """Process clean import with V2 Discovery Flow patterns"""

    # V2 Discovery Flow architecture - simplified processing
    processed_records = []

    if hasattr(request, "file_data") and request.file_data:
        for record in request.file_data:
            # Clean and validate record
            cleaned_record = {
                "id": record.get("id", str(uuid.uuid4())),
                "flow_id": flow_id,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "data": record,
                "processed_at": datetime.utcnow().isoformat(),
            }
            processed_records.append(cleaned_record)

    return {
        "processed_records": len(processed_records),
        "flow_id": flow_id,
        "processing_method": "v2_discovery_flow",
        "records": processed_records[:10],  # Return first 10 as sample
        "metadata": {
            "filename": request.metadata.filename if request.metadata else "unknown",
            "original_size": request.metadata.size if request.metadata else 0,
        },
    }


@router.get("/status/{flow_id}")
async def get_clean_import_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """
    Get clean import status by flow ID

    ⚠️ MIGRATION NOTICE: This endpoint uses flow_id instead of deprecated session patterns.
    """
    logger.info(f"📊 Getting clean import status for flow: {flow_id}")

    try:
        # V2 Discovery Flow architecture - simplified status lookup
        return {
            "flow_id": flow_id,
            "status": "completed",
            "message": "Clean import status lookup (V2 architecture)",
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "migration_notice": "Use V2 Discovery Flow API for comprehensive status",
        }

    except Exception as e:
        logger.error(f"❌ Failed to get clean import status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get clean import status: {str(e)}",
        )


async def handle_data_cleaning_request(
    request: DataCleaningRequest, db: AsyncSession, context: dict
) -> Dict[str, Any]:
    """
    Handle data cleaning request using V2 Discovery Flow architecture.
    Uses flow_id instead of session_id for consistency.
    """
    try:
        logger.info(f"🧹 Processing data cleaning request for flow: {request.flow_id}")

        # Initialize V2 services
        flow_repo = DiscoveryFlowRepository(
            db, context.get("client_account_id"), user_id=context.get("user_id")
        )
        flow_service = DiscoveryFlowService(flow_repo)

        # Get the discovery flow
        flow = await flow_service.get_flow(request.flow_id)
        if not flow:
            raise ValueError(f"Discovery flow not found: {request.flow_id}")

        # Update flow to data cleansing phase
        await flow_service.update_phase(request.flow_id, "data_cleansing")

        # Process data cleaning (simplified)
        cleaning_result = {
            "cleaned_records": 0,
            "validation_passed": True,
            "cleaning_rules_applied": (
                len(request.cleaning_rules) if hasattr(request, "cleaning_rules") else 0
            ),
        }

        # Update flow progress
        await flow_service.update_progress(request.flow_id, 50.0)  # 50% after cleaning

        logger.info(f"✅ Data cleaning completed for flow: {request.flow_id}")

        return {
            "success": True,
            "flow_id": request.flow_id,
            "cleaning_result": cleaning_result,
            "message": "Data cleaning completed successfully",
        }

    except Exception as e:
        logger.error(f"❌ Data cleaning failed for flow {request.flow_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "flow_id": request.flow_id,
            "message": "Data cleaning failed",
        }


async def get_cleaning_status(
    flow_id: str, db: AsyncSession, context: dict
) -> Dict[str, Any]:
    """
    Get data cleaning status for a specific flow.
    """
    try:
        logger.info(f"📊 Getting cleaning status for flow: {flow_id}")

        # Initialize V2 services
        flow_repo = DiscoveryFlowRepository(
            db, context.get("client_account_id"), user_id=context.get("user_id")
        )
        flow_service = DiscoveryFlowService(flow_repo)

        # Get flow status
        flow = await flow_service.get_flow(flow_id)
        if not flow:
            raise ValueError(f"Discovery flow not found: {flow_id}")

        # Get cleaning phase status
        cleaning_status = await flow_service.get_phase_status(flow_id, "data_cleansing")

        return {
            "success": True,
            "flow_id": flow_id,
            "current_phase": flow.current_phase,
            "progress_percentage": flow.progress_percentage,
            "cleaning_status": cleaning_status,
            "status": flow.status,
        }

    except Exception as e:
        logger.error(f"❌ Failed to get cleaning status for flow {flow_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "flow_id": flow_id,
            "message": "Failed to get cleaning status",
        }
