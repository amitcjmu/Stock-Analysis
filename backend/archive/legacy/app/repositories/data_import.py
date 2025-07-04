"""
V3 Data Import Repository
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.repositories.v3.base import V3BaseRepository
from app.models import DataImport
from app.models.data_import.enums import ImportStatus
import logging

logger = logging.getLogger(__name__)

class V3DataImportRepository(V3BaseRepository[DataImport]):
    """Repository for V3 data imports using consolidated DataImport model"""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        super().__init__(db, DataImport, client_account_id, engagement_id)
    
    async def get_by_status(self, status: ImportStatus) -> List[DataImport]:
        """Get imports by status"""
        query = select(DataImport).where(
            DataImport.status == status
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_progress(
        self, 
        import_id: str,
        processed: int,
        failed: int = 0
    ) -> bool:
        """Update import progress"""
        # First get the import to verify context
        import_obj = await self.get_by_id(import_id)
        if not import_obj:
            return False
        
        query = update(DataImport).where(
            DataImport.id == import_id
        ).values(
            processed_records=processed,
            failed_records=failed,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def complete_import(
        self,
        import_id: str,
        total_processed: int,
        total_failed: int
    ) -> bool:
        """Mark import as completed"""
        # First get the import to verify context
        import_obj = await self.get_by_id(import_id)
        if not import_obj:
            return False
        
        query = update(DataImport).where(
            DataImport.id == import_id
        ).values(
            status=ImportStatus.COMPLETED,
            processed_records=total_processed,
            failed_records=total_failed,
            completed_at=func.now(),
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def fail_import(
        self,
        import_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark import as failed"""
        # First get the import to verify context
        import_obj = await self.get_by_id(import_id)
        if not import_obj:
            return False
        
        query = update(DataImport).where(
            DataImport.id == import_id
        ).values(
            status=ImportStatus.FAILED,
            error_message=error_message,
            error_details=error_details or {},
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_imports_by_date_range(
        self,
        start_date,
        end_date,
        status: Optional[ImportStatus] = None
    ) -> List[DataImport]:
        """Get imports within a date range"""
        query = select(DataImport).where(
            and_(
                DataImport.created_at >= start_date,
                DataImport.created_at <= end_date
            )
        )
        
        if status:
            query = query.where(DataImport.status == status)
        
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()