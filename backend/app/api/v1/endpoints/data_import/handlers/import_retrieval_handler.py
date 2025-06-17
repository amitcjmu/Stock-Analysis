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
            "session_id": record.session_id
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

@router.get("/imports/latest")
async def get_latest_import(
    db: AsyncSession = Depends(get_db)
):
    """Get the latest data import for the current engagement."""
    context = get_current_context()

    # Create a subquery to get the latest import for the current engagement context.
    # The repository will handle the context filtering.
    import_repo = create_deduplicating_repository(db, DataImport)
    
    # The get_all() method of the repository doesn't support ordering,
    # so we construct a query here.
    query = select(DataImport).order_by(desc(DataImport.created_at))
    query = import_repo._apply_context_filter(query) # Apply context from repo
    
    result = await db.execute(query.limit(1))
    latest_import = result.scalar_one_or_none()

    if not latest_import:
        raise HTTPException(status_code=404, detail="No data imports found for this engagement")

    return import_to_dict(latest_import)

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