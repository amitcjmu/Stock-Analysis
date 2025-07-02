"""
Legacy Upload Handler - Updated for V2 Discovery Flow Architecture
Handles traditional file upload workflow with V2 flow management.
"""

import hashlib
import csv
import io
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

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

# V2 Discovery Flow Services
try:
    from app.services.discovery_flow_service import DiscoveryFlowService
    from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
    DISCOVERY_FLOW_AVAILABLE = True
except ImportError:
    DISCOVERY_FLOW_AVAILABLE = False
    DiscoveryFlowService = None
    DiscoveryFlowRepository = None

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
    """Upload and create a new data import session with V2 Discovery Flow management."""
    data_import = None
    try:
        # Get current context from middleware
        context = get_current_context()
        
        # Read file content
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Create Discovery Flow using V2 architecture
        flow_id = None
        if DISCOVERY_FLOW_AVAILABLE:
            try:
                flow_repo = DiscoveryFlowRepository(db, context.client_account_id)
                flow_service = DiscoveryFlowService(flow_repo)
                
                # Create new discovery flow
                flow = await flow_service.create_flow(
                    initial_phase="data_import",
                    metadata={
                        "filename": file.filename,
                        "import_type": import_type,
                        "file_size": len(content),
                        "file_hash": file_hash
                    }
                )
                flow_id = flow.flow_id
                logger.info(f"Created V2 Discovery Flow: {flow_id}")
            except Exception as flow_e:
                logger.warning(f"V2 Discovery Flow creation failed, continuing without flow: {flow_e}")
        
        # Default user for testing if not in context
        default_user_id = "eef6ea50-6550-4f14-be2c-081d4eb23038" # John Doe

        # Create DataImport object but don't commit yet
        data_import = DataImport(
            client_account_id=context.client_account_id or "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",
            engagement_id=context.engagement_id,
            import_name=import_name or f"{file.filename} Import",
            import_type=import_type,
            description=description,
            source_filename=file.filename,
            file_size_bytes=len(content),
            file_type=file.content_type,
            file_hash=file_hash,
            status=ImportStatus.UPLOADING, # New status for atomicity
            imported_by=context.user_id or default_user_id,
            is_mock=False
        )
        db.add(data_import)
        await db.flush() # Flush to get ID for relationships

        # Process the file and create raw records within the same transaction
        await process_uploaded_file(data_import, content, db, context)
        
        # Final commit for the entire operation
        await db.commit()
        await db.refresh(data_import)

        return {
            "import_id": str(data_import.id),
            "flow_id": flow_id,  # Return flow_id instead of session_id
            # "session_id": flow_id,  # Backward compatibility - removed as field doesn't exist
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "status": data_import.status,
            "filename": file.filename,
            "size_bytes": len(content),
            "message": "File uploaded and processed successfully with V2 Discovery Flow"
        }
        
    except Exception as e:
        logger.error(f"Data import failed: {e}", exc_info=True)
        await db.rollback()
        # Update status if data_import object was created
        if data_import:
            try:
                # Need a separate session to update status after rollback
                async with get_db() as new_db_session:
                    data_import.status = ImportStatus.FAILED
                    new_db_session.add(data_import)
                    await new_db_session.commit()
            except Exception as update_e:
                logger.error(f"Failed to update import status to FAILED: {update_e}")

        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_uploaded_file(data_import: DataImport, content: bytes, db: AsyncSession, context: RequestContext):
    """Process uploaded file and create raw import records with context awareness."""
    # This function now operates within the transaction of upload_data_file
    # It should not commit or handle exceptions that need to roll back the whole import.
    
    # Update status to processing in memory
    data_import.status = ImportStatus.PROCESSING
    
    # Parse file content
    content_str = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(content_str))
    
    raw_records = []
    row_number = 1
    
    for row in csv_reader:
        raw_record = RawImportRecord(
            data_import_id=data_import.id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            row_number=row_number,
            record_id=row.get('ID') or row.get('id') or f"ROW_{row_number}",
            raw_data=dict(row),
            is_processed=False,
            is_valid=True
        )
        raw_records.append(raw_record)
        row_number += 1
    
    # Bulk add raw records to the session
    if raw_records:
        db.add_all(raw_records)
    
    # Update import statistics in memory
    data_import.total_records = len(raw_records)
    data_import.completed_at = datetime.utcnow()
    
    # Trigger quality analysis (runs in the same transaction)
    from ..quality_analysis import analyze_data_quality
    await analyze_data_quality(data_import, raw_records, db, context)

    # Final status update in memory
    # The commit in the parent function will persist this.
    data_import.status = ImportStatus.PROCESSED 