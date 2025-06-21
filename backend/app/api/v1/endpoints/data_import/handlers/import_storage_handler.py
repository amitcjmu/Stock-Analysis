"""
Import Storage Handler - Persistent data storage and retrieval.
Handles storing imported data in database for cross-page persistence.
"""

import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, and_
import uuid
import asyncio
import json
import os
from pydantic import BaseModel, ValidationError

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import DataImport, RawImportRecord, ImportStatus, ImportFieldMapping
from app.schemas.data_import_schemas import StoreImportRequest

# Make client_account import conditional to avoid deployment failures
try:
    from app.models.client_account import ClientAccount, Engagement
    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError:
    CLIENT_ACCOUNT_AVAILABLE = False
    ClientAccount = None
    Engagement = None

# Import session management service
try:
    from app.services.session_management_service import SessionManagementService, create_session_management_service
    SESSION_MANAGEMENT_AVAILABLE = True
except ImportError:
    SESSION_MANAGEMENT_AVAILABLE = False
    SessionManagementService = None

router = APIRouter()
logger = logging.getLogger(__name__)

# Validation sessions directory
VALIDATION_SESSIONS_PATH = os.path.join("backend", "data", "validation_sessions")

# Ensure the directory exists
os.makedirs(VALIDATION_SESSIONS_PATH, exist_ok=True)

class ImportStorageResponse(BaseModel):
    success: bool
    import_session_id: Optional[str] = None
    error: Optional[str] = None
    message: str
    records_stored: int = 0

@router.post("/store-import")
async def store_import_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> ImportStorageResponse:
    """
    Store validated import data in the database and trigger Discovery Flow.
    
    This endpoint receives the validated CSV data and:
    1. Stores it in the database
    2. Triggers the Discovery Flow for immediate processing
    3. Returns the import session ID for tracking
    """
    try:
        # Get raw request body and log it
        raw_body = await request.body()
        logger.info(f"🔍 DEBUG: Raw request body: {raw_body.decode()}")
        
        # Parse JSON manually
        try:
            request_data = json.loads(raw_body)
            logger.info(f"🔍 DEBUG: Parsed JSON: {json.dumps(request_data, indent=2, default=str)}")
        except json.JSONDecodeError as e:
            logger.error(f"🚨 JSON decode error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        
        # Try to create StoreImportRequest from parsed data
        try:
            store_request = StoreImportRequest(**request_data)
            logger.info(f"🔄 Starting data storage for session: {store_request.upload_context.validation_session_id}")
        except ValidationError as e:
            logger.error(f"🚨 Pydantic validation error: {e}")
            raise HTTPException(status_code=422, detail=f"Validation error: {e.errors()}")
        
        # Extract data from request
        file_data = store_request.file_data
        filename = store_request.metadata.filename
        file_size = store_request.metadata.size
        file_type = store_request.metadata.type
        intended_type = store_request.upload_context.intended_type
        validation_session_id = store_request.upload_context.validation_session_id
        upload_timestamp = store_request.upload_context.upload_timestamp
        
        # Use context for client/engagement IDs
        client_account_id = context.client_account_id
        engagement_id = context.engagement_id
        user_id = context.user_id
        
        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, 
                detail="Client account and engagement context required"
            )
        
        logger.info(f"Using existing import record {validation_session_id} for store-import")
        
        # Find the existing DataImport record created by the upload endpoint
        from sqlalchemy import select
        existing_import_query = select(DataImport).where(DataImport.id == validation_session_id)
        result = await db.execute(existing_import_query)
        data_import = result.scalar_one_or_none()
        
        if not data_import:
            raise HTTPException(
                status_code=404,
                detail=f"Import record {validation_session_id} not found. Please upload the file first."
            )
        
        # Update the existing import record instead of creating a new one
        data_import.status = "processing"
        data_import.import_config = {
            "validation_session_id": validation_session_id,
            "upload_timestamp": upload_timestamp,
            "intended_type": intended_type
        }
        
        # Store field mappings
        records_stored = 0
        if file_data:
            # Create basic field mappings for each column
            sample_record = file_data[0] if file_data else {}
            for field_name in sample_record.keys():
                field_mapping = ImportFieldMapping(
                    data_import_id=data_import.id,
                    source_field=field_name,
                    target_field=field_name.lower().replace(' ', '_'),
                    confidence_score=0.8,  # Default confidence
                    mapping_type="automatic",
                    sample_values=json.dumps([str(record.get(field_name, "")) for record in file_data[:5]]),
                    status="pending"
                )
                db.add(field_mapping)
                records_stored += 1
        
        # Update status to completed
        data_import.status = "completed"
        data_import.processed_records = records_stored
        data_import.completed_at = datetime.utcnow()
        
        await db.commit()
        
        # 🚀 Trigger Discovery Flow immediately after successful storage
        try:
            await _trigger_discovery_flow(
                data_import_id=str(data_import.id),
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id or "system",
                file_data=file_data,
                context=context
            )
        except Exception as flow_error:
            logger.warning(f"Discovery Flow trigger failed: {flow_error}")
            # Don't fail the import if flow trigger fails
        
        logger.info(f"✅ Successfully stored {records_stored} field mappings for import {data_import.id}")
        
        return ImportStorageResponse(
            success=True,
            import_session_id=str(data_import.id),
            message=f"Successfully stored {records_stored} records and triggered Discovery Flow",
            records_stored=records_stored
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store import data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store import data: {str(e)}")

async def _trigger_discovery_flow(
    data_import_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    file_data: List[Dict[str, Any]],
    context: RequestContext
):
    """
    Trigger the CrewAI Discovery Flow immediately after data import.
    
    This implements the proper CrewAI Flow pattern with @start/@listen decorators
    that produces the purple logs and flow ID tracking.
    """
    try:
        logger.info(f"🚀 Triggering CrewAI Discovery Flow for import {data_import_id}")
        
        # Import the proper CrewAI Flow
        logger.info(f"🔍 DEBUG: Importing CrewAI Flow modules...")
        from app.services.crewai_flows.discovery_flow import DiscoveryFlow, create_discovery_flow
        from app.services.crewai_flow_service import CrewAIFlowService
        logger.info(f"✅ DEBUG: CrewAI Flow modules imported successfully")
        
        # Initialize CrewAI service
        logger.info(f"🔍 DEBUG: Initializing CrewAI service...")
        crewai_service = CrewAIFlowService()
        logger.info(f"✅ DEBUG: CrewAI service initialized")
        
        # Create proper flow using the factory function
        logger.info(f"🔍 DEBUG: Creating discovery flow...")
        discovery_flow = create_discovery_flow(
            session_id=data_import_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            cmdb_data={"file_data": file_data},
            metadata={
                "source": "data_import",
                "filename": f"import_{data_import_id}",
                "import_timestamp": datetime.utcnow().isoformat()
            },
            crewai_service=crewai_service,
            context=context
        )
        logger.info(f"✅ DEBUG: Discovery flow created: {type(discovery_flow)}")
        
        # Execute the CrewAI Flow using kickoff() method - this produces the purple logs
        logger.info(f"🎯 Starting CrewAI Flow kickoff for session: {data_import_id}")
        flow_result = await asyncio.to_thread(discovery_flow.kickoff)
        
        logger.info(f"✅ CrewAI Discovery Flow completed: {flow_result}")
        
    except ImportError as e:
        logger.warning(f"CrewAI Discovery Flow service not available: {e}")
        logger.error(f"🚨 DEBUG: ImportError details: {e}")
    except Exception as e:
        logger.error(f"Failed to trigger CrewAI Discovery Flow: {e}")
        logger.error(f"🚨 DEBUG: Exception details: {e}")
        import traceback
        logger.error(f"🚨 DEBUG: Full traceback: {traceback.format_exc()}")
        # Don't raise - we don't want to fail the import if flow fails

@router.get("/latest-import")
async def get_latest_import(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """⚡ OPTIMIZED: Get the latest import data for the current context with performance improvements."""
    start_time = datetime.utcnow()
    
    try:
        # Extract context from request headers
        from app.core.context import extract_context_from_request
        context = extract_context_from_request(request)
        
        logger.info(f"🔍 Getting latest import for context: client={context.client_account_id}, engagement={context.engagement_id}")
        
        # ⚡ FAST PATH: Missing context - return empty response quickly
        if not context.client_account_id or not context.engagement_id:
            logger.warning(f"⚡ Fast path: Missing context, returning empty response")
            return {
                "success": False,
                "message": "Missing client or engagement context",
                "data": [],
                "import_metadata": None,
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "fast_path": True
                }
            }
        
        # ⚡ OPTIMIZED: Execute database query with timeout
        timeout_seconds = 5
        latest_import = None
        
        try:
            async def _get_latest_import_with_timeout():
                # ⚡ OPTIMIZED: Get the most substantial import (highest record count) for this context
                # First try: Look for any status (not just 'processed')
                # Safely parse UUIDs with fallback
                try:
                    client_uuid = uuid.UUID(context.client_account_id) if context.client_account_id else None
                    engagement_uuid = uuid.UUID(context.engagement_id) if context.engagement_id else None
                except (ValueError, TypeError):
                    logger.warning(f"Invalid UUID format - client: {context.client_account_id}, engagement: {context.engagement_id}")
                    return None
                
                latest_import_query = select(DataImport).where(
                    and_(
                        DataImport.client_account_id == client_uuid,
                        DataImport.engagement_id == engagement_uuid
                    )
                ).order_by(
                    # First priority: imports with more records (likely real data)
                    DataImport.total_records.desc(),
                    # Second priority: most recent among those with same record count  
                    DataImport.completed_at.desc()
                ).limit(1)
                
                result = await db.execute(latest_import_query)
                import_result = result.scalar_one_or_none()
                
                # Log what we found for debugging
                if import_result:
                    logger.info(f"✅ Found context-filtered import: {import_result.id} with {import_result.total_records} records ({import_result.source_filename}) [status: {import_result.status}]")
                else:
                    logger.warning(f"❌ No imports found for context: client={context.client_account_id}, engagement={context.engagement_id}")
                    
                    # Debug: Check if there are any imports at all in the database
                    all_imports_query = select(DataImport).order_by(DataImport.completed_at.desc()).limit(5)
                    all_imports_result = await db.execute(all_imports_query)
                    all_imports = all_imports_result.scalars().all()
                    
                    if all_imports:
                        logger.info(f"📊 Found {len(all_imports)} total imports in database (any context):")
                        for imp in all_imports:
                            logger.info(f"  - {imp.id}: {imp.source_filename} ({imp.total_records} records, client: {imp.client_account_id}, engagement: {imp.engagement_id}, status: {imp.status})")
                    else:
                        logger.warning("📊 No imports found in database at all!")
                
                return import_result
            
            # Execute with timeout to prevent hanging
            latest_import = await asyncio.wait_for(_get_latest_import_with_timeout(), timeout=timeout_seconds)
            
        except asyncio.TimeoutError:
            logger.warning(f"⚡ Database timeout after {timeout_seconds}s, returning timeout response")
            return {
                "success": False,
                "message": "Database query timeout - please try again",
                "data": [],
                "import_metadata": None,
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "timeout": True
                }
            }
        except Exception as db_error:
            logger.error(f"⚡ Database error: {db_error}")
            return {
                "success": False,
                "message": f"Database error: {str(db_error)}",
                "data": [],
                "import_metadata": None,
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "database_error": True
                }
            }
        
        # ⚡ FAST PATH: No import found - return quickly
        if not latest_import:
            logger.info(f"⚡ Fast path: No import data found for context")
            return {
                "success": False,
                "message": "No import data found for this client and engagement",
                "data": [],
                "import_metadata": None,
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "no_data": True
                }
            }
        
        logger.info(f"✅ Found context-filtered import: {latest_import.id}")
        
        # ⚡ OPTIMIZED: Limit raw records retrieval for performance
        max_records = 1000  # Limit to first 1000 records for UI performance
        
        try:
            async def _get_raw_records_with_timeout():
                # ⚡ SIMPLIFIED: Optimized query with limit
                raw_records_query = (
                    select(RawImportRecord)
                    .where(RawImportRecord.data_import_id == latest_import.id)
                    .order_by(RawImportRecord.row_number)
                    .limit(max_records)
                )
                
                result = await db.execute(raw_records_query)
                return result.scalars().all()
            
            # Execute with timeout
            raw_records = await asyncio.wait_for(_get_raw_records_with_timeout(), timeout=timeout_seconds)
            
        except asyncio.TimeoutError:
            logger.warning(f"⚡ Raw records query timeout, returning metadata only")
            return {
                "success": True,
                "data": [],
                "import_metadata": {
                    "filename": latest_import.source_filename or "Unknown",
                    "import_type": latest_import.import_type,
                    "imported_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
                    "total_records": latest_import.total_records or 0,
                    "import_id": str(latest_import.id),
                    "client_account_id": str(latest_import.client_account_id),
                    "engagement_id": str(latest_import.engagement_id),
                    "timeout_notice": "Record data timed out, showing metadata only"
                },
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "records_timeout": True
                }
            }
        except Exception as records_error:
            logger.error(f"⚡ Raw records error: {records_error}")
            return {
                "success": True,
                "data": [],
                "import_metadata": {
                    "filename": latest_import.source_filename or "Unknown",
                    "import_type": latest_import.import_type,
                    "imported_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
                    "total_records": latest_import.total_records or 0,
                    "import_id": str(latest_import.id),
                    "client_account_id": str(latest_import.client_account_id),
                    "engagement_id": str(latest_import.engagement_id),
                    "error_notice": f"Record retrieval error: {str(records_error)}"
                },
                "performance": {
                    "response_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "records_error": True
                }
            }
        
        # ⚡ OPTIMIZED: Transform response data efficiently
        response_data = []
        for record in raw_records:
            response_data.append(record.raw_data)
        
        import_metadata = {
            "filename": latest_import.source_filename or "Unknown",
            "import_type": latest_import.import_type,
            "imported_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
            "total_records": len(response_data),
            "actual_total_records": latest_import.total_records or 0,
            "import_id": str(latest_import.id),
            "client_account_id": str(latest_import.client_account_id),
            "engagement_id": str(latest_import.engagement_id),
            "limited_records": len(response_data) >= max_records
        }
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"✅ Retrieved {len(response_data)} records in {response_time:.2f}ms")
        
        return {
            "success": True,
            "data": response_data,
            "import_metadata": import_metadata,
            "performance": {
                "response_time_ms": response_time,
                "records_retrieved": len(response_data),
                "optimized": True
            }
        }
        
    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"❌ Error getting latest import in {response_time:.2f}ms: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to retrieve latest import: {str(e)}",
            "data": [],
            "import_metadata": None,
            "performance": {
                "response_time_ms": response_time,
                "error": True
            }
        }

@router.get("/import/{import_session_id}")
async def get_import_by_id(
    import_session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific import data by session ID.
    Enables linking and retrieving specific import sessions.
    """
    try:
        # Find the import session using async session pattern
        session_query = select(DataImport).where(
            DataImport.id == import_session_id
        )
        
        result = await db.execute(session_query)
        import_session = result.scalar_one_or_none()
        
        if not import_session:
            raise HTTPException(status_code=404, detail="Import session not found")
        
        # Get the raw records using async session pattern
        records_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == import_session.id
        ).order_by(RawImportRecord.row_number)
        
        records_result = await db.execute(records_query)
        raw_records = records_result.scalars().all()
        
        # Extract the data
        imported_data = [record.raw_data for record in raw_records]
        
        return {
            "success": True,
            "import_session_id": str(import_session.id),
            "import_metadata": {
                "filename": import_session.source_filename,
                "import_type": import_session.import_type,
                "imported_at": import_session.completed_at.isoformat() if import_session.completed_at else None,
                "total_records": import_session.total_records,
                "status": import_session.status
            },
            "data": imported_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve import {import_session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve import: {str(e)}") 