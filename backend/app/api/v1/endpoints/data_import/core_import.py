"""
Core Import Module - Core data upload and import session management.
Handles file uploads, session creation, and basic import operations.
"""

import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, select
import csv
import io
import logging

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import (
    DataImport, RawImportRecord, ImportStatus
)

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

from app.repositories.session_aware_repository import create_session_aware_repository
from .utilities import import_to_dict

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_data_file(
    file: UploadFile = File(...),
    import_type: str = Form(...),
    import_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload and create a new data import session with automatic session management."""
    try:
        # Get current context from middleware
        context = get_current_context()
        
        # Read file content
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Create or get active session using SessionManagementService
        session_id = None
        if SESSION_MANAGEMENT_AVAILABLE:
            try:
                session_service = create_session_management_service(db)
                session = await session_service.get_or_create_active_session(
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    auto_create=True
                )
                session_id = str(session.id) if session else None
                logger.info(f"Using session {session_id} for data import")
            except Exception as session_e:
                logger.warning(f"Session management failed, continuing without session: {session_e}")
        
        # Create data import record with context and fallback user ID
        # Default demo user for Marathon Petroleum testing
        default_user_id = "eef6ea50-6550-4f14-be2c-081d4eb23038"  # Demo user John Doe
        
        data_import = DataImport(
            client_account_id=context.client_account_id or "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",  # Marathon Petroleum UUID
            engagement_id=context.engagement_id,
            session_id=session_id,  # Link to session if available
            import_name=import_name or f"{file.filename} Import",
            import_type=import_type,
            description=description,
            source_filename=file.filename,
            file_size_bytes=len(content),
            file_type=file.content_type,
            file_hash=file_hash,
            status=ImportStatus.UPLOADED,
            imported_by=context.user_id or default_user_id,  # Use default if no user context
            is_mock=False  # This is now real data import
        )
        
        db.add(data_import)
        await db.commit()
        await db.refresh(data_import)
        
        # Process the file content
        await process_uploaded_file(data_import, content, db, context)
        
        return {
            "import_id": str(data_import.id),
            "session_id": session_id,
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "status": "uploaded",
            "filename": file.filename,
            "size_bytes": len(content),
            "message": "File uploaded and processing started"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_uploaded_file(data_import: DataImport, content: bytes, db: AsyncSession, context: RequestContext):
    """Process uploaded file and create raw import records with context awareness."""
    try:
        # Update status to processing
        data_import.status = ImportStatus.PROCESSING
        await db.commit()
        
        # Parse file content (assuming CSV for demo)
        content_str = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        raw_records = []
        row_number = 1
        
        for row in csv_reader:
            # Create raw import record with client context
            raw_record = RawImportRecord(
                data_import_id=data_import.id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                session_id=data_import.session_id,
                row_number=row_number,
                record_id=row.get('ID') or row.get('id') or f"ROW_{row_number}",
                raw_data=dict(row),  # Store exactly as imported
                is_processed=False,
                is_valid=True
            )
            raw_records.append(raw_record)
            row_number += 1
        
        # Bulk insert raw records
        db.add_all(raw_records)
        
        # Update import statistics
        data_import.total_records = len(raw_records)
        data_import.status = ImportStatus.PROCESSED
        data_import.completed_at = datetime.utcnow()
        
        await db.commit()
        
        # Import quality analysis to trigger analysis
        from .quality_analysis import analyze_data_quality
        await analyze_data_quality(data_import, raw_records, db, context)
        
    except Exception as e:
        data_import.status = ImportStatus.FAILED
        await db.commit()
        raise e

@router.get("/imports")
async def get_data_imports(
    limit: int = 10,
    offset: int = 0,
    view_mode: str = "engagement_view",  # "session_view" or "engagement_view"
    db: AsyncSession = Depends(get_db)
):
    """Get list of data imports with context-aware filtering."""
    context = get_current_context()
    
    # Use session-aware repository for context-aware data access
    import_repo = create_session_aware_repository(db, DataImport, view_mode=view_mode)
    imports = await import_repo.get_all(limit=limit, offset=offset)
    
    return {
        "imports": [import_to_dict(imp) for imp in imports],
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "session_id": context.session_id,
            "view_mode": view_mode
        }
    }

@router.get("/imports/{import_id}/raw-records")
async def get_raw_import_records(
    import_id: str,
    limit: int = 100,
    offset: int = 0,
    view_mode: str = "engagement_view",
    db: AsyncSession = Depends(get_db)
):
    """Get raw import records for a specific import with context awareness."""
    context = get_current_context()
    
    # Use session-aware repository for context-aware data access
    record_repo = create_session_aware_repository(db, RawImportRecord, view_mode=view_mode)
    records = await record_repo.get_by_filters(data_import_id=import_id)
    
    # Apply pagination
    paginated_records = records[offset:offset + limit]
    
    records_list = []
    for record in paginated_records:
        records_list.append({
            "id": str(record.id),
            "row_number": record.row_number,
            "record_id": record.record_id,
            "raw_data": record.raw_data,
            "processed_data": record.processed_data,
            "is_processed": record.is_processed,
            "is_valid": record.is_valid,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "session_id": record.session_id
        })
    
    return {
        "records": records_list,
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "view_mode": view_mode,
            "total_records": len(records),
            "paginated_count": len(paginated_records)
        }
    }

@router.get("/imports/latest")
async def get_latest_import(
    view_mode: str = "engagement_view",
    db: AsyncSession = Depends(get_db)
):
    """Get the latest data import for the current context."""
    context = get_current_context()
    
    # Use session-aware repository for context-aware data access
    import_repo = create_session_aware_repository(db, DataImport, view_mode=view_mode)
    imports = await import_repo.get_all(limit=1)
    
    if not imports:
        raise HTTPException(status_code=404, detail="No imports found for current context")
    
    latest = imports[0]
    result = import_to_dict(latest)
    result["context"] = {
        "client_account_id": context.client_account_id,
        "engagement_id": context.engagement_id,
        "session_id": context.session_id,
        "view_mode": view_mode
    }
    
    return result

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
async def get_latest_import_data(db: AsyncSession = Depends(get_db)):
    """
    Get the most recent import data for attribute mapping.
    Replaces localStorage dependency with database persistence.
    """
    try:
        # Find the most recent completed import using async session pattern
        latest_query = select(DataImport).where(
            DataImport.status == ImportStatus.PROCESSED
        ).order_by(desc(DataImport.completed_at)).limit(1)
        
        result = await db.execute(latest_query)
        latest_import = result.scalar_one_or_none()
        
        if not latest_import:
            return {
                "success": False,
                "message": "No import data found",
                "data": []
            }
        
        # Get the raw records using async session pattern
        records_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == latest_import.id
        ).order_by(RawImportRecord.row_number)
        
        records_result = await db.execute(records_query)
        raw_records = records_result.scalars().all()
        
        # Extract the data
        imported_data = [record.raw_data for record in raw_records]
        
        logger.info(f"Retrieved {len(imported_data)} records from import session {latest_import.id}")
        
        return {
            "success": True,
            "import_session_id": str(latest_import.id),
            "import_metadata": {
                "filename": latest_import.source_filename,
                "import_type": latest_import.import_type,
                "imported_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
                "total_records": latest_import.total_records
            },
            "data": imported_data,
            "message": f"Retrieved {len(imported_data)} records from latest import"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve import data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve import data: {str(e)}")

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

@router.get("/imports")
async def list_imports(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    List recent import sessions for traceability and audit.
    """
    try:
        # Use async session pattern for querying imports
        imports_query = select(DataImport).order_by(
            desc(DataImport.created_at)
        ).limit(limit)
        
        result = await db.execute(imports_query)
        imports = result.scalars().all()
        
        import_list = []
        for imp in imports:
            import_list.append({
                "id": str(imp.id),
                "filename": imp.source_filename,
                "import_type": imp.import_type,
                "status": imp.status,
                "total_records": imp.total_records,
                "imported_at": imp.created_at.isoformat() if imp.created_at else None,
                "completed_at": imp.completed_at.isoformat() if imp.completed_at else None
            })
        
        return {
            "success": True,
            "imports": import_list,
            "total": len(import_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to list imports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list imports: {str(e)}") 