"""
Import Storage Handler - Persistent data storage and retrieval.
Handles storing imported data in database for cross-page persistence.
"""

import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, and_
import uuid
import asyncio

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import DataImport, RawImportRecord, ImportStatus

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

@router.post("/store-import")
async def store_import_data(
    file_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    upload_context: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Store imported data in database for persistent access across pages.
    Replaces localStorage with proper database persistence and audit trail.
    """
    try:
        logger.info(f"Storing import data: {len(file_data)} records")
        
        # Get current context from middleware
        context = get_current_context()
        
        # Dynamically resolve demo client and engagement UUIDs
        demo_client_uuid = None
        demo_engagement_uuid = None
        demo_user_uuid = "eef6ea50-6550-4f14-be2c-081d4eb23038"  # John Doe
        
        # Resolve demo client dynamically if context is missing
        if not context.client_account_id:
            try:
                # Find demo client by is_mock=true
                demo_client_query = select(ClientAccount).where(ClientAccount.is_mock == True)
                demo_client_result = await db.execute(demo_client_query)
                demo_client = demo_client_result.scalar_one_or_none()
                
                if demo_client:
                    demo_client_uuid = str(demo_client.id)
                    logger.info(f"Dynamically resolved demo client: {demo_client.name} ({demo_client_uuid})")
                    
                    # Get first engagement for demo client
                    demo_engagement_query = select(Engagement).where(
                        Engagement.client_account_id == demo_client.id
                    ).limit(1)
                    demo_engagement_result = await db.execute(demo_engagement_query)
                    demo_engagement = demo_engagement_result.scalar_one_or_none()
                    
                    if demo_engagement:
                        demo_engagement_uuid = str(demo_engagement.id)
                        logger.info(f"Dynamically resolved demo engagement: {demo_engagement.name} ({demo_engagement_uuid})")
            except Exception as resolve_e:
                logger.warning(f"Failed to resolve demo client/engagement dynamically: {resolve_e}")
                # Keep None values to trigger error handling below
        
        # Use actual context or fallback to dynamically resolved demo values
        client_account_id = context.client_account_id or demo_client_uuid
        engagement_id = context.engagement_id or demo_engagement_uuid  
        user_id = context.user_id or demo_user_uuid
        
        # Verify we have required IDs
        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required context: client_account_id={client_account_id}, engagement_id={engagement_id}"
            )
        
        # Simplified session management - don't fail the whole operation if session fails
        session_id = None
        try:
            if SESSION_MANAGEMENT_AVAILABLE:
                session_service = create_session_management_service(db)
                session = await session_service.get_or_create_active_session(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    auto_create=True
                )
                session_id = str(session.id) if session else None
                logger.info(f"Using session {session_id} for data import from store-import")
        except Exception as session_e:
            logger.warning(f"Session management failed, continuing without session: {session_e}")
            # Continue without session - this is not critical for data storage
        
        # Create import session record with proper context and session
        import_session = DataImport(
            import_name=metadata.get("filename", "Unknown Import"),
            import_type=upload_context.get("intended_type", "unknown"),
            description=f"Data import session from {metadata.get('filename')}",
            source_filename=metadata.get("filename", "unknown.csv"),
            file_size_bytes=metadata.get("size", 0),
            file_type=metadata.get("type", "text/csv"),
            file_hash=hashlib.sha256(str(file_data).encode()).hexdigest()[:32],
            status=ImportStatus.PROCESSED,
            total_records=len(file_data),
            processed_records=len(file_data),
            failed_records=0,
            import_config={
                "upload_context": upload_context,
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            # Use context values with fallbacks for demo/development
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            imported_by=user_id,
            session_id=session_id,  # Link to session if available
            completed_at=datetime.utcnow()
        )
        
        db.add(import_session)
        await db.flush()  # Get the ID using async flush
        
        # Store raw import records
        for index, record in enumerate(file_data):
            raw_record = RawImportRecord(
                data_import_id=import_session.id,
                row_number=index + 1,
                record_id=record.get("hostname") or record.get("asset_name") or f"row_{index + 1}",
                raw_data=record,
                is_processed=True,
                is_valid=True,
                created_at=datetime.utcnow()
            )
            db.add(raw_record)
        
        await db.commit()
        
        logger.info(f"Successfully stored import session {import_session.id} with {len(file_data)} records")
        
        return {
            "success": True,
            "import_session_id": str(import_session.id),
            "records_stored": len(file_data),
            "message": f"Successfully stored {len(file_data)} records with full audit trail"
        }
        
    except Exception as e:
        logger.error(f"Failed to store import data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store import data: {str(e)}")

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
                latest_import_query = select(DataImport).where(
                    and_(
                        DataImport.client_account_id == uuid.UUID(context.client_account_id),
                        DataImport.engagement_id == uuid.UUID(context.engagement_id)
                    )
                ).order_by(
                    # First priority: imports with more records (likely real data)
                    DataImport.total_records.desc(),
                    # Second priority: most recent among those with same record count  
                    DataImport.created_at.desc()
                ).limit(1)
                
                result = await db.execute(latest_import_query)
                import_result = result.scalar_one_or_none()
                
                # Log what we found for debugging
                if import_result:
                    logger.info(f"✅ Found context-filtered import: {import_result.id} with {import_result.total_records} records ({import_result.import_name}) [status: {import_result.status}]")
                else:
                    logger.warning(f"❌ No imports found for context: client={context.client_account_id}, engagement={context.engagement_id}")
                    
                    # Debug: Check if there are any imports at all in the database
                    all_imports_query = select(DataImport).order_by(DataImport.created_at.desc()).limit(5)
                    all_imports_result = await db.execute(all_imports_query)
                    all_imports = all_imports_result.scalars().all()
                    
                    if all_imports:
                        logger.info(f"📊 Found {len(all_imports)} total imports in database (any context):")
                        for imp in all_imports:
                            logger.info(f"  - {imp.id}: {imp.import_name} ({imp.total_records} records, client: {imp.client_account_id}, engagement: {imp.engagement_id}, status: {imp.status})")
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
                    "imported_at": latest_import.created_at.isoformat() if latest_import.created_at else None,
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
                    "imported_at": latest_import.created_at.isoformat() if latest_import.created_at else None,
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
            "imported_at": latest_import.created_at.isoformat() if latest_import.created_at else None,
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