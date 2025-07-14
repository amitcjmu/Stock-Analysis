"""
Import Storage Handler - API Endpoints for Data Import Operations.
Handles storing imported data in database for cross-page persistence.
Now uses modular service architecture for better maintainability.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, and_, func
import uuid
import asyncio
import os

from app.core.logging import get_logger
from app.core.exceptions import (
    DataImportError,
    ValidationError as AppValidationError,
    DatabaseError,
    FlowError
)
from app.middleware.error_tracking import track_async_errors

from app.core.database import get_db, AsyncSessionLocal
from app.core.context import get_current_context, RequestContext, extract_context_from_request
from app.models.data_import import DataImport, RawImportRecord, ImportStatus, ImportFieldMapping
from app.schemas.data_import_schemas import StoreImportRequest

# Import the new modular service
from app.services.data_import import ImportStorageHandler, ImportStorageResponse

router = APIRouter()
logger = get_logger(__name__)

# Validation sessions directory
VALIDATION_SESSIONS_PATH = os.path.join("backend", "data", "validation_sessions")

# Ensure the directory exists
os.makedirs(VALIDATION_SESSIONS_PATH, exist_ok=True)

@router.post("/store-import")
@track_async_errors("store_import_data")
async def store_import_data(
    store_request: StoreImportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Store validated import data in the database and trigger Discovery Flow.
    
    This endpoint receives the validated CSV data and:
    1. Validates no existing incomplete discovery flow exists
    2. Stores it in the database
    3. Triggers the Discovery Flow for immediate processing
    4. Returns the import session ID for tracking
    
    Now uses modular service architecture for better maintainability.
    """
    try:
        # Initialize the modular import handler
        import_handler = ImportStorageHandler(db, context.client_account_id)
        
        # Delegate to the modular service
        response = await import_handler.handle_import(store_request, context)
        
        # Handle HTTP exceptions based on response
        if not response.success and response.error:
            # Check if this is a conflict error
            if "incomplete_discovery_flow_exists" in response.error:
                raise HTTPException(
                    status_code=409,  # Conflict
                    detail={
                        "error": "incomplete_discovery_flow_exists",
                        "message": response.message,
                        "existing_flow": getattr(response, 'existing_flow', None),
                        "recommendations": getattr(response, 'recommendations', None)
                    }
                )
            elif "validation_error" in response.error:
                raise HTTPException(
                    status_code=400,  # Bad Request
                    detail=response.message
                )
            else:
                raise HTTPException(
                    status_code=500,  # Internal Server Error
                    detail=response.message
                )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store import data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store import data: {str(e)}")

@router.get("/latest-import")
async def get_latest_import(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get the latest import data for the current context using modular service."""
    try:
        # Extract context from request headers
        context = extract_context_from_request(request)
        
        if not context.client_account_id or not context.engagement_id:
            return {
                "success": False,
                "message": "Missing client or engagement context",
                "data": [],
                "import_metadata": None
            }
        
        # Initialize the modular import handler
        import_handler = ImportStorageHandler(db, context.client_account_id)
        
        # Get the latest import using the modular service
        latest_import_data = await import_handler.get_latest_import_data(context)
        
        if not latest_import_data:
            return {
                "success": True,
                "message": "No import data available yet for this client and engagement. Please upload data using the Data Import page.",
                "data": [],
                "import_metadata": {
                    "filename": None,
                    "import_type": None,
                    "imported_at": None,
                    "total_records": 0,
                    "actual_total_records": 0,
                    "import_id": None,
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id,
                    "no_imports_exist": True
                }
            }
        
        return {
            "success": True,
            "data": latest_import_data["data"],
            "import_metadata": latest_import_data["import_metadata"]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting latest import: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve latest import: {str(e)}",
            "data": [],
            "import_metadata": None
        }

@router.get("/import/{data_import_id}")
async def get_import_by_id(
    data_import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific import data by data import ID using modular service."""
    try:
        # Extract context from request headers (if available)
        # For this endpoint, we don't require full context since we're looking up by ID
        import_handler = ImportStorageHandler(db, "system")  # Use system context
        
        # Get the import data using the modular service
        import_data = await import_handler.get_import_data(data_import_id)
        
        if not import_data:
            raise HTTPException(status_code=404, detail="Data import not found")
        
        return {
            "success": True,
            "data_import_id": data_import_id,
            "import_metadata": import_data["import_metadata"],
            "data": import_data["data"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve import {data_import_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve import: {str(e)}")

@router.get("/flow/{flow_id}/import-data")
async def get_import_data_by_flow_id(
    flow_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get import data for a specific discovery flow using modular service."""
    try:
        # Extract context from request headers
        context = extract_context_from_request(request)
        
        logger.info(f"🔍 Getting import data for flow: {flow_id}, context: client={context.client_account_id}, engagement={context.engagement_id}")
        
        # First, find the discovery flow by flow_id
        from app.models.discovery_flow import DiscoveryFlow
        flow_query = select(DiscoveryFlow).where(
            DiscoveryFlow.flow_id == flow_id
        )
        
        flow_result = await db.execute(flow_query)
        discovery_flow = flow_result.scalar_one_or_none()
        
        if not discovery_flow:
            logger.warning(f"❌ Discovery flow not found: {flow_id}")
            return {
                "success": False,
                "message": f"Discovery flow not found: {flow_id}",
                "data": [],
                "import_metadata": None
            }
        
        # Check if the flow has a data_import_id
        if not discovery_flow.data_import_id:
            logger.warning(f"⚠️ Discovery flow {flow_id} has no associated data import")
            return {
                "success": True,
                "message": "No data import associated with this flow",
                "data": [],
                "import_metadata": {
                    "flow_id": str(discovery_flow.flow_id),
                    "flow_name": discovery_flow.flow_name,
                    "status": discovery_flow.status,
                    "no_import": True
                }
            }
        
        # Initialize the modular import handler
        import_handler = ImportStorageHandler(db, context.client_account_id)
        
        # Get the import data using the modular service
        import_data = await import_handler.get_import_data(str(discovery_flow.data_import_id))
        
        if not import_data:
            logger.error(f"❌ Data import not found for flow {flow_id}, data_import_id: {discovery_flow.data_import_id}")
            return {
                "success": False,
                "message": f"Data import not found: {discovery_flow.data_import_id}",
                "data": [],
                "import_metadata": None
            }
        
        # Enhance metadata with flow information
        enhanced_metadata = import_data["import_metadata"].copy()
        enhanced_metadata.update({
            "flow_id": str(discovery_flow.flow_id),
            "flow_name": discovery_flow.flow_name,
            "flow_status": discovery_flow.status
        })
        
        logger.info(f"✅ Retrieved {len(import_data['data'])} records for flow {flow_id}")
        
        return {
            "success": True,
            "data": import_data["data"],
            "import_metadata": enhanced_metadata
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting import data for flow {flow_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve import data: {str(e)}",
            "data": [],
            "import_metadata": None
        }

# Additional endpoints for import management
@router.get("/import/{import_id}/status")
async def get_import_status(
    import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the status of an import operation."""
    try:
        import_handler = ImportStorageHandler(db, "system")
        status = await import_handler.get_import_status(import_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Import not found")
        
        return {
            "success": True,
            "import_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get import status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get import status: {str(e)}")

@router.delete("/import/{import_id}")
async def cancel_import(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Cancel an import operation and its associated flows."""
    try:
        import_handler = ImportStorageHandler(db, context.client_account_id)
        success = await import_handler.cancel_import(import_id, context)
        
        if not success:
            raise HTTPException(status_code=404, detail="Import not found or could not be cancelled")
        
        return {
            "success": True,
            "message": f"Import {import_id} cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel import: {str(e)}")

@router.post("/import/{import_id}/retry")
async def retry_failed_import(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Retry a failed import operation."""
    try:
        import_handler = ImportStorageHandler(db, context.client_account_id)
        response = await import_handler.retry_failed_import(import_id, context)
        
        if not response:
            raise HTTPException(status_code=404, detail="Import not found")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry import: {str(e)}")