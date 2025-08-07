"""
Flow Cache Manager

Handles comprehensive cache invalidation across all cache layers:
- Redis cache
- SQLAlchemy session cache  
- Application-level cache clearing
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class FlowCacheManager:
    """Manages cache invalidation and coordination across all cache layers"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def invalidate_comprehensive_cache(
        self, flow_id: str, operation_type: str = "generic"
    ) -> Dict[str, Any]:
        """
        Comprehensive cache invalidation across all layers
        
        Args:
            flow_id: Flow identifier
            operation_type: Type of operation for targeted invalidation
            
        Returns:
            Dict with invalidation results
        """
        results = {
            "redis_cache": False,
            "sqlalchemy_session": False,
            "application_cache": False,
            "errors": []
        }
        
        try:
            # 1. Redis cache invalidation
            redis_result = await self._invalidate_redis_cache(flow_id, operation_type)
            results["redis_cache"] = redis_result
            
            # 2. SQLAlchemy session cache invalidation
            session_result = await self._invalidate_session_cache(flow_id)
            results["sqlalchemy_session"] = session_result
            
            # 3. Application-level cache invalidation
            app_result = await self._invalidate_application_cache(flow_id)
            results["application_cache"] = app_result
            
            logger.info(f"✅ Comprehensive cache invalidation completed for flow {flow_id}")
            
        except Exception as e:
            error_msg = f"Cache invalidation failed for flow {flow_id}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            
        return results

    async def _invalidate_redis_cache(self, flow_id: str, operation_type: str) -> bool:
        """Invalidate Redis cache entries for flow"""
        try:
            # Import Redis cache here to avoid circular imports
            from app.services.redis_cache import redis_cache
            
            # Invalidate flow-specific keys
            await redis_cache.invalidate_flow_cache(
                flow_id, 
                self.context.client_account_id,
                self.context.engagement_id
            )
            
            # Invalidate operation-specific keys if needed
            if operation_type == "delete":
                await redis_cache.cleanup_deleted_flow_references(flow_id)
                
            return True
            
        except Exception as e:
            logger.warning(f"Redis cache invalidation failed for {flow_id}: {e}")
            return False

    async def _invalidate_session_cache(self, flow_id: str) -> bool:
        """Invalidate SQLAlchemy session cache"""
        try:
            # Expire all cached objects in the current session
            self.db.expire_all()
            
            # Force session to refresh on next query
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.warning(f"Session cache invalidation failed for {flow_id}: {e}")
            return False

    async def _invalidate_application_cache(self, flow_id: str) -> bool:
        """Invalidate application-level caches"""
        try:
            # Clear flow registry cache if it exists
            try:
                from app.services.flow_registry import flow_registry
                if hasattr(flow_registry, 'clear_flow_cache'):
                    flow_registry.clear_flow_cache(flow_id)
            except ImportError:
                pass
                
            # Clear any other application caches
            logger.info(f"Application cache cleared for flow {flow_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Application cache invalidation failed for {flow_id}: {e}")
            return False

    async def warm_cache_for_flow(self, flow_id: str) -> Dict[str, bool]:
        """Pre-warm caches for a flow to improve performance"""
        results = {"redis": False, "application": False}
        
        try:
            # Pre-load commonly accessed data
            from app.services.redis_cache import redis_cache
            
            # Cache flow metadata
            await redis_cache.cache_flow_metadata(
                flow_id,
                self.context.client_account_id,
                self.context.engagement_id
            )
            results["redis"] = True
            
            logger.info(f"Cache warmed for flow {flow_id}")
            
        except Exception as e:
            logger.warning(f"Cache warming failed for {flow_id}: {e}")
            
        return results