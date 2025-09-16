"""
Health Check implementations for Service Health Manager

Contains individual health check implementations for different services.
"""

import asyncio
import uuid
from typing import Any, Dict, Optional, Tuple

from app.core.logging import get_logger

from .base import ServiceType

logger = get_logger(__name__)


class HealthCheckService:
    """Service for performing health checks on different service types"""

    def __init__(self):
        pass

    async def execute_health_check(
        self, service_type: ServiceType, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Execute the actual health check for a service"""
        try:
            if service_type == ServiceType.REDIS:
                return await self._check_redis_health(timeout_seconds)
            elif service_type == ServiceType.DATABASE:
                return await self._check_database_health(timeout_seconds)
            elif service_type == ServiceType.AUTH_CACHE:
                return await self._check_auth_cache_health(timeout_seconds)
            elif service_type == ServiceType.STORAGE_MANAGER:
                return await self._check_storage_manager_health(timeout_seconds)
            elif service_type == ServiceType.LLM_SERVICE:
                return await self._check_llm_service_health(timeout_seconds)
            elif service_type == ServiceType.EMBEDDING_SERVICE:
                return await self._check_embedding_service_health(timeout_seconds)
            else:
                return False, f"Unknown service type: {service_type}", {}

        except asyncio.TimeoutError:
            return (
                False,
                f"Health check timeout after {timeout_seconds}s",
                {"timeout": True},
            )
        except Exception as e:
            return False, str(e), {"exception": type(e).__name__}

    async def _check_redis_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check Redis service health"""
        try:
            from app.services.caching.redis_cache import get_redis_cache

            redis_cache = get_redis_cache()
            if not redis_cache.enabled:
                return False, "Redis is disabled", {"enabled": False}

            # Test basic operations with timeout
            test_key = f"health_check_{uuid.uuid4().hex[:8]}"

            await asyncio.wait_for(
                redis_cache.set(test_key, "health_check_value", ttl=10),
                timeout=timeout_seconds,
            )

            await asyncio.wait_for(redis_cache.get(test_key), timeout=timeout_seconds)

            await asyncio.wait_for(
                redis_cache.delete(test_key), timeout=timeout_seconds
            )

            return True, None, {"operations": "set_get_delete_ok"}

        except Exception as e:
            return False, f"Redis health check failed: {str(e)}", {"error": str(e)}

    async def _check_database_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check database service health"""
        try:
            from app.core.database import AsyncSessionLocal

            # Test database connection with timeout and proper session management
            async def db_check():
                session = None
                try:
                    session = AsyncSessionLocal()
                    result = await session.execute("SELECT 1")
                    return result is not None
                finally:
                    if session:
                        await session.close()

            is_healthy = await asyncio.wait_for(db_check(), timeout=timeout_seconds)

            if is_healthy:
                return True, None, {"query": "SELECT 1 ok"}
            else:
                return False, "Database query failed", {}

        except Exception as e:
            return False, f"Database health check failed: {str(e)}", {"error": str(e)}

    async def _check_auth_cache_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check auth cache service health"""
        try:
            from app.services.caching.auth_cache_service import get_auth_cache_service

            auth_cache = get_auth_cache_service()

            # Use the built-in health check if available
            if hasattr(auth_cache, "health_check"):
                health_result = await asyncio.wait_for(
                    auth_cache.health_check(), timeout=timeout_seconds
                )

                is_healthy = health_result.get("status") in ["healthy", "warning"]
                error_message = (
                    None
                    if is_healthy
                    else f"Auth cache status: {health_result.get('status')}"
                )

                return is_healthy, error_message, health_result
            else:
                # Fallback basic check
                return True, None, {"basic_check": "ok"}

        except Exception as e:
            return False, f"Auth cache health check failed: {str(e)}", {"error": str(e)}

    async def _check_storage_manager_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check storage manager service health"""
        try:
            from app.services.storage.storage_manager import get_storage_manager

            storage_manager = get_storage_manager()

            # Use the built-in health check if available
            if hasattr(storage_manager, "health_check"):
                health_result = await asyncio.wait_for(
                    storage_manager.health_check(), timeout=timeout_seconds
                )

                is_healthy = health_result.get("status") in ["healthy", "warning"]
                error_message = (
                    None
                    if is_healthy
                    else f"Storage manager status: {health_result.get('status')}"
                )

                return is_healthy, error_message, health_result
            else:
                # Fallback basic check
                return (
                    storage_manager.enabled,
                    None if storage_manager.enabled else "Storage manager disabled",
                    {},
                )

        except Exception as e:
            return (
                False,
                f"Storage manager health check failed: {str(e)}",
                {"error": str(e)},
            )

    async def _check_llm_service_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check LLM service health"""
        try:
            # This would integrate with your LLM service
            # For now, return a basic check
            return (
                True,
                None,
                {"basic_check": "ok", "note": "LLM health check not implemented"},
            )

        except Exception as e:
            return (
                False,
                f"LLM service health check failed: {str(e)}",
                {"error": str(e)},
            )

    async def _check_embedding_service_health(
        self, timeout_seconds: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check embedding service health"""
        try:
            # Basic health check for embedding service
            return (
                True,
                None,
                {"basic_check": "ok", "note": "Embedding health check not implemented"},
            )

        except Exception as e:
            return (
                False,
                f"Embedding service health check failed: {str(e)}",
                {"error": str(e)},
            )
