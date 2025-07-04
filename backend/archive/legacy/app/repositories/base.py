"""
V3 Repository base classes
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.repositories.context_aware_repository import ContextAwareRepository
from app.models import DataImport, DiscoveryFlow, ImportFieldMapping, RawImportRecord
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
        # Handle field renames for backward compatibility
        data = self._handle_field_renames(data)
        
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
        # Handle field renames for backward compatibility
        data = self._handle_field_renames(data)
        
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
            # Handle field renames for each item
            item_data = self._handle_field_renames(item_data)
            instance = self.model_class(**item_data)
            instance = self._apply_context_to_instance(instance)
            self.db.add(instance)
            instances.append(instance)
        
        await self.db.commit()
        
        # Refresh all instances
        for instance in instances:
            await self.db.refresh(instance)
        
        return instances
    
    def _handle_field_renames(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle field renames for backward compatibility"""
        # Create a copy to avoid modifying the original
        data = data.copy()
        
        # Common field renames across all models
        field_mappings = {
            # DataImport field renames
            'source_filename': 'filename',
            'file_size_bytes': 'file_size',
            'file_type': 'mime_type',
            
            # RawImportRecord field renames
            'row_number': 'record_index',
            'processed_data': 'cleansed_data',
            
            # ImportFieldMapping field renames
            'mapping_type': 'match_type',
            'validation_rules': 'transformation_rules',
            
            # Common fields to remove
            'is_mock': None,
            'file_hash': None,
            'import_config': None,
            'assessment_package': None,
            'flow_description': None,
            'user_feedback': None,
            'sample_values': None,
            'raw_data': None,
            'field_mappings_used': None
        }
        
        # Apply field mappings
        for old_field, new_field in field_mappings.items():
            if old_field in data:
                if new_field is None:
                    # Remove deprecated field
                    data.pop(old_field, None)
                else:
                    # Rename field
                    data[new_field] = data.pop(old_field)
        
        return data