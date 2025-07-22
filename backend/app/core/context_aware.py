"""
Base classes for context-aware components
"""

import logging
from abc import ABC
from typing import Any, Dict, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_required_context, require_context

logger = logging.getLogger(__name__)

class ContextAwareService(ABC):
    """Base class for all context-aware services"""
    
    def __init__(self):
        """Initialize without context - context comes from ContextVar"""
        super().__init__()
    
    @property
    def context(self) -> RequestContext:
        """Get current context"""
        return get_required_context()
    
    @property
    def client_account_id(self) -> str:
        """Convenience property for client account ID"""
        return self.context.client_account_id
    
    @property
    def engagement_id(self) -> str:
        """Convenience property for engagement ID"""
        return self.context.engagement_id
    
    @property
    def user_id(self) -> str:
        """Convenience property for user ID"""
        return self.context.user_id
    
    def check_permission(self, resource: str, action: str) -> bool:
        """Check if current context has permission"""
        return self.context.has_permission(resource, action)
    
    def log_with_context(self, level: str, message: str, **extra):
        """Log with context information"""
        extra.update({
            'client_account_id': self.client_account_id,
            'engagement_id': self.engagement_id,
            'user_id': self.user_id,
            'request_id': self.context.request_id
        })
        getattr(logger, level)(message, extra=extra)

class ContextAwareTool(ContextAwareService):
    """Base class for context-aware CrewAI tools"""
    
    def __init__(self, **kwargs):
        """Initialize tool with context awareness"""
        super().__init__()
        # Tool-specific initialization
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @require_context
    def _run(self, *args, **kwargs):
        """Run tool with context validation"""
        self.log_with_context('info', f"Tool {self.__class__.__name__} executing")
        return self.run(*args, **kwargs)
    
    def run(self, *args, **kwargs):
        """Override in subclasses"""
        raise NotImplementedError

class ContextAwareRepository(ABC):
    """Enhanced base repository with automatic context filtering"""
    
    def __init__(self, db: AsyncSession, model_class: Any):
        """Initialize with database session and model"""
        self.db = db
        self.model_class = model_class
        self._context = None
    
    @property
    def context(self) -> RequestContext:
        """Get current context"""
        if not self._context:
            self._context = get_required_context()
        return self._context
    
    def apply_context_filter(self, query):
        """Apply context-based filtering to query"""
        # Apply client account filter
        if hasattr(self.model_class, 'client_account_id'):
            query = query.where(
                self.model_class.client_account_id == self.context.client_account_id
            )
        
        # Apply engagement filter if available
        if hasattr(self.model_class, 'engagement_id') and self.context.engagement_id:
            query = query.where(
                self.model_class.engagement_id == self.context.engagement_id
            )
        
        return query
    
    async def get_by_id(self, id: Any) -> Optional[Any]:
        """Get entity by ID with context filtering"""
        query = select(self.model_class).where(self.model_class.id == id)
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_all(self, limit: int = 100, offset: int = 0):
        """List all entities with context filtering"""
        query = select(self.model_class).limit(limit).offset(offset)
        query = self.apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    def set_context_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set context fields on data before insert/update"""
        if hasattr(self.model_class, 'client_account_id'):
            data['client_account_id'] = self.context.client_account_id
        
        if hasattr(self.model_class, 'engagement_id'):
            data['engagement_id'] = self.context.engagement_id
        
        if hasattr(self.model_class, 'created_by'):
            data['created_by'] = self.context.user_id
        
        return data