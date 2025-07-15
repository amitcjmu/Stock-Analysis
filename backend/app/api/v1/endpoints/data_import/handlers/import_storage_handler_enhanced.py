"""
Import Storage Handler - Enhanced with OpenAPI Documentation.
API Endpoints for Data Import Operations with comprehensive documentation.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
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

# Import the new API models
from app.models.api.data_import import (
    DataImportRequest,
    DataImportResponse,
    DataImportErrorResponse,
    ImportStatusResponse,
    ImportDataResponse
)

# Import the modular service
from app.services.data_import import ImportStorageHandler, ImportStorageResponse

router = APIRouter()
logger = get_logger(__name__)

# Validation sessions directory
VALIDATION_SESSIONS_PATH = os.path.join("backend", "data", "validation_sessions")
os.makedirs(VALIDATION_SESSIONS_PATH, exist_ok=True)


@router.post(
    "/store-import",
    summary="Store Import Data",
    description="""
    Store validated CSV data in the database and trigger a Discovery Flow.
    
    This endpoint:
    1. Validates that no incomplete discovery flow exists for the engagement
    2. Stores the CSV data in the database
    3. Triggers a Discovery Flow for immediate processing
    4. Returns the import session ID and flow ID for tracking
    
    **Authentication Required**: Yes  
    **Multi-tenant Headers Required**: X-Client-Account-ID, X-Engagement-ID
    """,
    response_model=DataImportResponse,
    responses={
        200: {
            "description": "Data imported successfully",
            "model": DataImportResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Data imported successfully and discovery flow triggered",
                        "data_import_id": "imp_789e0123-4567-89ab-cdef-0123456789ab",
                        "flow_id": "disc_flow_456e7890-1234-56ab-cdef-0123456789ab",
                        "total_records": 150,
                        "import_type": "servers",
                        "next_steps": [
                            "Monitor discovery flow progress",
                            "Review field mappings when available",
                            "Validate critical attributes"
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid data format",
            "model": DataImportErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "validation_error",
                        "message": "Invalid CSV data format",
                        "details": {
                            "missing_columns": ["server_name", "ip_address"],
                            "invalid_rows": [3, 7, 12]
                        }
                    }
                }
            }
        },
        409: {
            "description": "Conflict - Incomplete discovery flow exists",
            "model": DataImportErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "incomplete_discovery_flow_exists",
                        "message": "An incomplete discovery flow already exists for this engagement",
                        "details": {
                            "existing_flow": {
                                "flow_id": "disc_flow_123",
                                "status": "processing",
                                "created_at": "2025-01-15T09:00:00Z"
                            }
                        },
                        "recommendations": [
                            "Complete or cancel the existing discovery flow",
                            "Review the current flow status"
                        ]
                    }
                }
            }
        },
        422: {
            "description": "Unprocessable Entity - Missing required fields",
            "model": DataImportErrorResponse
        },
        500: {
            "description": "Internal Server Error",
            "model": DataImportErrorResponse
        }
    },
    tags=["Data Import"]
)
@track_async_errors("store_import_data")
async def store_import_data(
    store_request: DataImportRequest,  # Use new model
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DataImportResponse:
    """
    Store validated import data and trigger discovery flow.
    
    Example request:
    ```json
    {
        "file_data": [
            {
                "server_name": "prod-web-01",
                "ip_address": "10.0.1.10",
                "os": "Ubuntu 20.04",
                "cpu_cores": 8,
                "memory_gb": 16
            }
        ],
        "metadata": {
            "filename": "servers.csv",
            "size": 102400,
            "type": "text/csv"
        },
        "upload_context": {
            "intended_type": "servers",
            "upload_timestamp": "2025-01-15T10:30:00Z"
        }
    }
    ```
    """
    try:
        # Convert new model to old schema for service compatibility
        old_request = StoreImportRequest(
            file_data=store_request.file_data,
            metadata=store_request.metadata.model_dump(),
            upload_context=store_request.upload_context.model_dump(),
            client_id=store_request.client_id,
            engagement_id=store_request.engagement_id
        )
        
        # Initialize the modular import handler
        import_handler = ImportStorageHandler(db, context.client_account_id)
        
        # Delegate to the modular service
        response = await import_handler.handle_import(old_request, context)
        
        # Handle HTTP exceptions based on response
        if not response.get("success") and response.get("error"):
            if "incomplete_discovery_flow_exists" in response.get("error", ""):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "error": "incomplete_discovery_flow_exists",
                        "message": response.get("message", ""),
                        "details": {"existing_flow": response.get("existing_flow")},
                        "recommendations": response.get("recommendations")
                    }
                )
            elif "validation_error" in response.get("error", ""):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": "validation_error",
                        "message": response.get("message", "")
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "error": "internal_error",
                        "message": response.get("message", "")
                    }
                )
        
        # Return structured response
        return DataImportResponse(
            success=response["success"],
            message=response["message"],
            data_import_id=response["data_import_id"],
            flow_id=response["flow_id"],
            total_records=response["total_records"],
            import_type=response["import_type"],
            next_steps=response.get("next_steps", [
                "Monitor discovery flow progress",
                "Review field mappings when available",
                "Validate critical attributes"
            ])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store import data: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "internal_error",
                "message": f"Failed to store import data: {str(e)}"
            }
        )


@router.get(
    "/latest-import",
    summary="Get Latest Import",
    description="""
    Retrieve the most recent import data for the current client and engagement context.
    
    **Authentication Required**: Yes  
    **Multi-tenant Headers Required**: X-Client-Account-ID, X-Engagement-ID
    """,
    response_model=ImportDataResponse,
    responses={
        200: {
            "description": "Import data retrieved successfully",
            "model": ImportDataResponse
        },
        404: {
            "description": "No import data found",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "No import data available yet",
                        "data": [],
                        "import_metadata": {
                            "no_imports_exist": True
                        }
                    }
                }
            }
        }
    },
    tags=["Data Import"]
)
async def get_latest_import(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ImportDataResponse:
    """Get the latest import data for the current context."""
    try:
        context = extract_context_from_request(request)
        
        if not context.client_account_id or not context.engagement_id:
            return ImportDataResponse(
                success=False,
                data=[],
                import_metadata={
                    "import_id": "",
                    "filename": "",
                    "import_type": "",
                    "imported_at": datetime.utcnow(),
                    "total_records": 0,
                    "status": "failed",
                    "client_account_id": 0,
                    "engagement_id": 0
                }
            )
        
        import_handler = ImportStorageHandler(db, context.client_account_id)
        latest_import_data = await import_handler.get_latest_import_data(context)
        
        if not latest_import_data:
            return ImportDataResponse(
                success=True,
                data=[],
                import_metadata={
                    "import_id": "",
                    "filename": "",
                    "import_type": "",
                    "imported_at": datetime.utcnow(),
                    "total_records": 0,
                    "status": "pending",
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id
                }
            )
        
        return ImportDataResponse(
            success=True,
            data=latest_import_data["data"],
            import_metadata=latest_import_data["import_metadata"]
        )
        
    except Exception as e:
        logger.error(f"Error getting latest import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Failed to retrieve latest import: {str(e)}"}
        )


@router.get(
    "/import/{import_id}/status",
    summary="Get Import Status",
    description="""
    Get the current status of an import operation.
    
    **Authentication Required**: Yes
    """,
    response_model=ImportStatusResponse,
    responses={
        200: {"description": "Import status retrieved successfully"},
        404: {"description": "Import not found"}
    },
    tags=["Data Import"]
)
async def get_import_status(
    import_id: str,
    db: AsyncSession = Depends(get_db)
) -> ImportStatusResponse:
    """Get the status of an import operation."""
    try:
        import_handler = ImportStorageHandler(db, "system")
        status = await import_handler.get_import_status(import_id)
        
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import not found"
            )
        
        return ImportStatusResponse(
            success=True,
            import_status=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get import status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get import status: {str(e)}"
        )