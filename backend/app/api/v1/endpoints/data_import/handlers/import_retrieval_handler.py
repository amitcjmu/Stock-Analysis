"""
Import Retrieval Handler - Data retrieval and listing operations.
Handles getting import records, raw data, and import metadata.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import DataImport, RawImportRecord
from app.repositories.deduplicating_repository import create_deduplicating_repository
from ..utilities import import_to_dict

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/imports")
async def get_data_imports(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get list of data imports with context-aware filtering."""
    context = get_current_context()
    
    # Use deduplicating repository for context-aware data access
    import_repo = create_deduplicating_repository(db, DataImport)
    imports = await import_repo.get_all(limit=limit, offset=offset)
    
    return {
        "imports": [import_to_dict(imp) for imp in imports],
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id
        }
    }

@router.get("/latest")
async def get_latest_import(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get the latest data import for the current context."""
    try:
        # Query for the latest import
        query = (
            select(DataImport)
            .where(DataImport.client_account_id == context.client_account_id)
            .where(DataImport.engagement_id == context.engagement_id)
            .order_by(desc(DataImport.created_at))
            .limit(1)
        )
        
        result = await db.execute(query)
        latest_import = result.scalar_one_or_none()
        
        if not latest_import:
            raise HTTPException(
                status_code=404, 
                detail="No data imports found for the current context"
            )
        
        # Convert to dictionary format
        import_dict = import_to_dict(latest_import)
        
        # Add import metadata in the expected format
        import_dict["import_metadata"] = {
            "import_id": str(latest_import.id),
            "import_name": latest_import.import_name,
            "status": latest_import.status,
            "filename": latest_import.filename,
            "total_records": latest_import.total_records,
            "processed_records": latest_import.processed_records
        }
        
        return import_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest import: {e}")
        raise HTTPException(status_code=500, detail="Failed to get latest import")

@router.get("/imports/{import_id}/raw-records")
async def get_raw_import_records(
    import_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get raw import records for a specific import with context awareness."""
    context = get_current_context()
    
    # Use deduplicating repository for context-aware data access
    record_repo = create_deduplicating_repository(db, RawImportRecord)
    # Since this is for a specific import_id, deduplication is not the main concern,
    # but the repository correctly applies context filters.
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
            "data_import_id": str(record.data_import_id)
        })
    
    return {
        "records": records_list,
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "total_records": len(records),
            "paginated_count": len(paginated_records)
        }
    }

@router.get("/imports/{import_id}")
async def get_import_by_id(
    import_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get a specific data import by ID with context awareness."""
    
    # Use deduplicating repository for context-aware data access
    import_repo = create_deduplicating_repository(db, DataImport)
    
    # Query for the specific import
    query = select(DataImport).where(DataImport.id == import_id)
    query = import_repo._apply_context_filter(query)
    
    result = await db.execute(query)
    data_import = result.scalar_one_or_none()

    if not data_import:
        raise HTTPException(status_code=404, detail=f"Data import {import_id} not found")

    # Get a sample record to include in the response
    sample_query = select(RawImportRecord).where(
        RawImportRecord.data_import_id == import_id
    ).limit(1)
    sample_result = await db.execute(sample_query)
    sample_record = sample_result.scalar_one_or_none()

    import_dict = import_to_dict(data_import)
    
    # Add sample record data for field mapping
    if sample_record and sample_record.raw_data:
        import_dict["sample_record"] = sample_record.raw_data
        import_dict["field_count"] = len(sample_record.raw_data.keys())
    else:
        import_dict["sample_record"] = {}
        import_dict["field_count"] = 0

    return import_dict

 