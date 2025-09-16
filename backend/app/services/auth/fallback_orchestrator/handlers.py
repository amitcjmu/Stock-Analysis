"""
Emergency Handlers and Recovery Operations

This module contains emergency data handlers and recovery operations
that provide minimal functionality when all primary services fail.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.services.monitoring.service_health_manager import ServiceType

from .base import (
    FallbackAttempt,
    FallbackConfig,
    FallbackLevel,
    FallbackResult,
)

logger = get_logger(__name__)


class EmergencyHandlerManager:
    """Manages emergency handlers and fallback data caching"""

    def __init__(self):
        # Emergency data cache
        self.emergency_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.emergency_cache_lock = asyncio.Lock()

    async def execute_emergency_handler(
        self,
        handler: Callable,
        args: tuple,
        kwargs: dict,
        context_data: Optional[Dict[str, Any]],
    ) -> Any:
        """Execute emergency fallback handler"""
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(*args, context=context_data, **kwargs)
            else:
                return handler(*args, context=context_data, **kwargs)
        except Exception as e:
            logger.error(f"Emergency handler failed: {e}")
            raise

    async def get_emergency_user_session(
        self, user_id: str, *args, context=None, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Emergency handler for user session data"""
        cache_key = f"emergency_session_{user_id}"

        async with self.emergency_cache_lock:
            if cache_key in self.emergency_cache:
                data, expires_at = self.emergency_cache[cache_key]
                if datetime.utcnow() < expires_at:
                    logger.debug(
                        f"Returning cached emergency session for user {user_id}"
                    )
                    return data
                else:
                    del self.emergency_cache[cache_key]

        # Generate minimal session data
        emergency_session = {
            "user_id": user_id,
            "email": f"user_{user_id}@emergency.local",
            "full_name": "Emergency User",
            "role": "user",
            "is_admin": False,
            "emergency_mode": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
        }

        # Cache for future use
        async with self.emergency_cache_lock:
            expires_at = datetime.utcnow() + timedelta(seconds=300)  # 5 minutes
            self.emergency_cache[cache_key] = (emergency_session, expires_at)

        logger.warning(f"Generated emergency session data for user {user_id}")
        return emergency_session

    async def get_emergency_user_context(
        self, user_id: str, *args, context=None, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Emergency handler for user context data"""
        emergency_context = {
            "user_id": user_id,
            "active_client_id": None,
            "active_engagement_id": None,
            "active_flow_id": None,
            "preferences": {"theme": "light", "language": "en"},
            "permissions": ["read"],
            "recent_activities": [],
            "emergency_mode": True,
            "last_updated": datetime.utcnow().isoformat(),
        }

        logger.warning(f"Generated emergency context data for user {user_id}")
        return emergency_context

    async def get_emergency_auth_response(
        self, *args, context=None, **kwargs
    ) -> Dict[str, Any]:
        """Emergency handler for authentication operations"""
        return {
            "authenticated": False,
            "error": "Authentication services temporarily unavailable",
            "emergency_mode": True,
            "retry_after_seconds": 300,
        }

    async def get_emergency_client_data(
        self, user_id: str, *args, context=None, **kwargs
    ) -> List[Dict[str, Any]]:
        """Emergency handler for client data"""
        return [
            {
                "id": "emergency_client",
                "name": "Emergency Client",
                "status": "limited",
                "emergency_mode": True,
                "available_features": ["basic_viewing"],
            }
        ]

    async def clear_emergency_cache(self) -> int:
        """Clear emergency cache and return number of items cleared"""
        async with self.emergency_cache_lock:
            count = len(self.emergency_cache)
            self.emergency_cache.clear()

        logger.info(f"Cleared {count} items from emergency cache")
        return count


class LevelExecutor:
    """Executes operations at specific fallback levels"""

    def __init__(self, health_manager):
        self.health_manager = health_manager

    async def execute_level(
        self,
        level: FallbackLevel,
        services: List[ServiceType],
        operation_func: Callable,
        args: tuple,
        kwargs: dict,
        config: FallbackConfig,
        context_data: Optional[Dict[str, Any]],
    ) -> FallbackResult:
        """Execute operation at a specific fallback level"""
        level_result = FallbackResult(success=False)

        # Try each service in the level
        for service in services:
            if not await self.health_manager.is_service_available(service):
                continue

            attempt_start = time.time()

            try:
                # Execute operation with timeout
                result_value = await asyncio.wait_for(
                    operation_func(*args, service_context=service, **kwargs),
                    timeout=config.timeout_per_level_seconds,
                )

                attempt_time = (time.time() - attempt_start) * 1000

                # Record successful attempt
                attempt = FallbackAttempt(
                    operation_type=config.operation_type,
                    level=level,
                    service_type=service,
                    success=True,
                    response_time_ms=attempt_time,
                    metadata={"context": context_data},
                )

                level_result.attempts.append(attempt)
                level_result.total_attempts += 1
                level_result.success = True
                level_result.value = result_value
                level_result.service_used = service

                logger.debug(
                    f"Service {service} succeeded for {level} level in {attempt_time:.1f}ms"
                )
                return level_result

            except asyncio.TimeoutError:
                attempt_time = (time.time() - attempt_start) * 1000
                error_msg = f"Timeout after {attempt_time:.1f}ms"

                attempt = FallbackAttempt(
                    operation_type=config.operation_type,
                    level=level,
                    service_type=service,
                    success=False,
                    response_time_ms=attempt_time,
                    error_message=error_msg,
                    metadata={"timeout": True},
                )

                level_result.attempts.append(attempt)
                level_result.total_attempts += 1
                level_result.error_message = error_msg

                logger.warning(f"Service {service} timed out for {level} level")
                continue

            except Exception as e:
                attempt_time = (time.time() - attempt_start) * 1000
                error_msg = str(e)

                attempt = FallbackAttempt(
                    operation_type=config.operation_type,
                    level=level,
                    service_type=service,
                    success=False,
                    response_time_ms=attempt_time,
                    error_message=error_msg,
                    metadata={"exception": type(e).__name__},
                )

                level_result.attempts.append(attempt)
                level_result.total_attempts += 1
                level_result.error_message = error_msg

                logger.error(f"Service {service} failed for {level} level: {e}")
                continue

        return level_result
