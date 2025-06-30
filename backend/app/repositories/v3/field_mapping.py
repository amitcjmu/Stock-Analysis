"""
V3 Field Mapping Repository
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.repositories.v3.base import V3BaseRepository
from app.models.v3 import V3FieldMapping, MappingStatus
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class V3FieldMappingRepository(V3BaseRepository[V3FieldMapping]):
    """Repository for V3 field mappings"""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        super().__init__(db, V3FieldMapping, client_account_id, engagement_id)
    
    async def get_by_import(self, import_id: str) -> List[V3FieldMapping]:
        """Get all mappings for an import"""
        query = select(V3FieldMapping).where(
            V3FieldMapping.data_import_id == import_id
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_source_field(
        self,
        import_id: str,
        source_field: str
    ) -> Optional[V3FieldMapping]:
        """Get mapping by source field"""
        query = select(V3FieldMapping).where(
            and_(
                V3FieldMapping.data_import_id == import_id,
                V3FieldMapping.source_field == source_field
            )
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_status(self, import_id: str, status: MappingStatus) -> List[V3FieldMapping]:
        """Get mappings by status for an import"""
        query = select(V3FieldMapping).where(
            and_(
                V3FieldMapping.data_import_id == import_id,
                V3FieldMapping.status == status
            )
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def approve_mapping(
        self,
        mapping_id: str,
        approved_by: str
    ) -> bool:
        """Approve a field mapping"""
        # First get the mapping to verify context
        mapping = await self.get_by_id(mapping_id)
        if not mapping:
            return False
        
        query = update(V3FieldMapping).where(
            V3FieldMapping.id == mapping_id
        ).values(
            status=MappingStatus.APPROVED,
            approved_by=approved_by,
            approved_at=func.now(),
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def reject_mapping(
        self,
        mapping_id: str,
        rejected_by: str
    ) -> bool:
        """Reject a field mapping"""
        # First get the mapping to verify context
        mapping = await self.get_by_id(mapping_id)
        if not mapping:
            return False
        
        query = update(V3FieldMapping).where(
            V3FieldMapping.id == mapping_id
        ).values(
            status=MappingStatus.REJECTED,
            updated_at=func.now()
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def update_mapping(
        self,
        mapping_id: str,
        target_field: str,
        transformation_rules: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update mapping target and rules"""
        # First get the mapping to verify context
        mapping = await self.get_by_id(mapping_id)
        if not mapping:
            return False
        
        values = {
            "target_field": target_field,
            "status": MappingStatus.MODIFIED,
            "updated_at": func.now()
        }
        
        if transformation_rules:
            values["transformation_rules"] = transformation_rules
        
        query = update(V3FieldMapping).where(
            V3FieldMapping.id == mapping_id
        ).values(**values)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def bulk_create_mappings(
        self,
        import_id: str,
        mappings: List[Dict[str, Any]]
    ) -> List[V3FieldMapping]:
        """Create multiple mappings at once"""
        # Add import_id to all mappings
        for mapping in mappings:
            mapping["data_import_id"] = import_id
        
        return await self.bulk_create(mappings)
    
    async def get_mapping_statistics(self, import_id: str) -> Dict[str, Any]:
        """Get mapping statistics for an import"""
        mappings = await self.get_by_import(import_id)
        
        total_mappings = len(mappings)
        approved_count = len([m for m in mappings if m.status == MappingStatus.APPROVED])
        rejected_count = len([m for m in mappings if m.status == MappingStatus.REJECTED])
        suggested_count = len([m for m in mappings if m.status == MappingStatus.SUGGESTED])
        modified_count = len([m for m in mappings if m.status == MappingStatus.MODIFIED])
        
        # Calculate average confidence for suggested mappings
        suggested_mappings = [m for m in mappings if m.confidence_score is not None]
        avg_confidence = (
            sum(m.confidence_score for m in suggested_mappings) / len(suggested_mappings)
            if suggested_mappings else 0.0
        )
        
        return {
            "total_mappings": total_mappings,
            "approved": approved_count,
            "rejected": rejected_count,
            "suggested": suggested_count,
            "modified": modified_count,
            "approval_rate": approved_count / total_mappings if total_mappings > 0 else 0.0,
            "average_confidence": avg_confidence
        }