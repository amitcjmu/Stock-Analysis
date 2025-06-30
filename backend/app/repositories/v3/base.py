"""
V3 Repository base classes
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.repositories.context_aware_repository import ContextAwareRepository
from app.models.v3 import V3DataImport, V3DiscoveryFlow, V3FieldMapping, V3RawImportRecord
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class V3BaseRepository(ContextAwareRepository[T]):
    """Base repository for V3 models with context awareness"""
    
    def __init__(self, db: AsyncSession, model_class: T, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        """Initialize with session and model"""
        super().__init__(db, model_class, client_account_id, engagement_id)
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create entity with context fields"""
        # Create instance
        instance = self.model_class(**data)
        
        # Apply context fields
        instance = self._apply_context_to_instance(instance)
        
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        
        return instance
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID with context filtering"""
        query = select(self.model_class).where(self.model_class.id == id)
        query = self._apply_context_filter(query)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update entity with context validation"""
        # Get existing entity
        entity = await self.get_by_id(id)
        if not entity:
            return None
        
        # Update fields
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        await self.db.commit()
        await self.db.refresh(entity)
        
        return entity
    
    async def delete(self, id: str) -> bool:
        """Delete entity with context validation"""
        entity = await self.get_by_id(id)
        if not entity:
            return False
        
        await self.db.delete(entity)
        await self.db.commit()
        
        return True
    
    async def list_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """List all entities with context filtering"""
        query = select(self.model_class)
        query = self._apply_context_filter(query)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Bulk create with context"""
        instances = []
        for item_data in items:
            instance = self.model_class(**item_data)
            instance = self._apply_context_to_instance(instance)
            self.db.add(instance)
            instances.append(instance)
        
        await self.db.commit()
        
        # Refresh all instances
        for instance in instances:
            await self.db.refresh(instance)
        
        return instances