"""
Error Context Manager

Manages error context throughout the application lifecycle, providing context
enrichment, correlation tracking, and integration with monitoring systems.
This ensures consistent error context across all error handling scenarios.

Key Features:
- Request correlation tracking
- Context enrichment from multiple sources
- Sensitive data sanitization
- Integration with tracing systems
- Context propagation across async boundaries
- Performance impact monitoring

Context Sources:
- HTTP request information
- User session data
- Service health status
- System performance metrics
- Business logic context
"""

import contextvars
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

from app.core.logging import get_logger
from app.core.security.cache_encryption import sanitize_for_logging
from app.services.error_handling.enhanced_error_handler import (
    ErrorContext,
    OperationType,
)
from app.services.monitoring.service_health_manager import (
    ServiceType,
    get_service_health_manager,
)

logger = get_logger(__name__)

# Context variables for async context propagation
_error_context_var: contextvars.ContextVar[Optional[ErrorContext]] = (
    contextvars.ContextVar("error_context", default=None)
)
_correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


@dataclass
class ContextEnrichment:
    """Configuration for context enrichment"""

    include_request_headers: bool = True
    include_user_info: bool = True
    include_system_health: bool = True
    include_performance_metrics: bool = False
    sanitize_sensitive_data: bool = True
    max_context_size_bytes: int = 10000  # 10KB limit

    # Header filtering
    allowed_headers: Set[str] = field(
        default_factory=lambda: {
            "user-agent",
            "accept",
            "accept-language",
            "content-type",
            "content-length",
            "x-forwarded-for",
            "x-real-ip",
        }
    )

    blocked_headers: Set[str] = field(
        default_factory=lambda: {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "x-csrf-token",
            "x-session-id",
        }
    )


class ErrorContextManager:
    """
    Error Context Manager for Comprehensive Context Tracking

    Manages error context throughout the application, providing context
    enrichment, correlation tracking, and integration with monitoring systems.
    """

    def __init__(self):
        self.health_manager = get_service_health_manager()

        # Context enrichment configuration
        self.enrichment_config = ContextEnrichment()

        # Context cache for performance
        self._context_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_max_size = 1000

        # Performance tracking
        self._context_creation_times: List[float] = []
        self._enrichment_times: List[float] = []

        logger.info("ErrorContextManager initialized with context tracking")

    def create_context(
        self,
        operation_type: Optional[OperationType] = None,
        service_type: Optional[ServiceType] = None,
        user_id: Optional[str] = None,
        request_info: Optional[Dict[str, Any]] = None,
        **additional_context,
    ) -> ErrorContext:
        """
        Create a new error context

        Args:
            operation_type: Type of operation being performed
            service_type: Service type involved
            user_id: User identifier
            request_info: HTTP request information
            **additional_context: Additional context data

        Returns:
            ErrorContext: New error context instance
        """
        import time

        start_time = time.time()

        try:
            # Generate correlation ID if not present
            correlation_id = _correlation_id_var.get() or str(uuid.uuid4())
            _correlation_id_var.set(correlation_id)

            # Create base context
            context = ErrorContext(
                operation_type=operation_type,
                service_type=service_type,
                user_id=user_id,
                request_id=correlation_id,
            )

            # Enrich with request information
            if request_info:
                self._enrich_with_request_info(context, request_info)

            # Add additional context (sanitized)
            if additional_context:
                sanitized_additional = sanitize_for_logging(additional_context)
                context.context_data.update(sanitized_additional)

            # Set in context variable for async propagation
            _error_context_var.set(context)

            # Track performance
            creation_time = time.time() - start_time
            self._context_creation_times.append(creation_time)
            if len(self._context_creation_times) > 1000:
                self._context_creation_times = self._context_creation_times[-500:]

            logger.debug(
                f"Created error context {context.error_id} in {creation_time*1000:.2f}ms"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to create error context: {e}")
            # Return minimal context as fallback
            return ErrorContext(
                operation_type=operation_type,
                service_type=service_type,
                user_id=user_id,
            )

    def _enrich_with_request_info(
        self, context: ErrorContext, request_info: Dict[str, Any]
    ):
        """Enrich context with HTTP request information"""
        try:
            # Basic request information
            context.endpoint = request_info.get("path")
            context.method = request_info.get("method")
            context.client_ip = request_info.get("client_ip")

            # Headers (filtered for security)
            if self.enrichment_config.include_request_headers:
                headers = request_info.get("headers", {})
                filtered_headers = {}

                for header_name, header_value in headers.items():
                    header_lower = header_name.lower()

                    # Skip blocked headers
                    if header_lower in self.enrichment_config.blocked_headers:
                        continue

                    # Include allowed headers or all if no allow list
                    if (
                        not self.enrichment_config.allowed_headers
                        or header_lower in self.enrichment_config.allowed_headers
                    ):
                        filtered_headers[header_name] = header_value

                if filtered_headers:
                    context.context_data["request_headers"] = filtered_headers

            # User agent parsing
            user_agent = request_info.get("user_agent")
            if user_agent:
                context.user_agent = user_agent
                context.context_data["user_agent_info"] = self._parse_user_agent(
                    user_agent
                )

            # Query parameters (sanitized)
            query_params = request_info.get("query_params")
            if query_params:
                sanitized_params = sanitize_for_logging(query_params)
                context.context_data["query_params"] = sanitized_params

        except Exception as e:
            logger.warning(f"Failed to enrich context with request info: {e}")

    def _parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """Parse user agent string for basic information"""
        try:
            # Simple user agent parsing (you might want to use a library like user-agents)
            ua_lower = user_agent.lower()

            browser = "unknown"
            if "chrome" in ua_lower:
                browser = "chrome"
            elif "firefox" in ua_lower:
                browser = "firefox"
            elif "safari" in ua_lower and "chrome" not in ua_lower:
                browser = "safari"
            elif "edge" in ua_lower:
                browser = "edge"

            platform = "unknown"
            if "windows" in ua_lower:
                platform = "windows"
            elif "mac" in ua_lower:
                platform = "macos"
            elif "linux" in ua_lower:
                platform = "linux"
            elif "android" in ua_lower:
                platform = "android"
            elif "ios" in ua_lower or "iphone" in ua_lower or "ipad" in ua_lower:
                platform = "ios"

            return {
                "browser": browser,
                "platform": platform,
                "is_mobile": any(
                    mobile in ua_lower
                    for mobile in ["mobile", "android", "iphone", "ipad"]
                ),
            }

        except Exception:
            return {"browser": "unknown", "platform": "unknown", "is_mobile": False}

    async def enrich_context_async(
        self,
        context: Optional[ErrorContext] = None,
        include_system_health: bool = True,
        include_performance_metrics: bool = False,
    ) -> ErrorContext:
        """
        Asynchronously enrich error context with additional information

        Args:
            context: Context to enrich (uses current context if None)
            include_system_health: Include system health information
            include_performance_metrics: Include performance metrics

        Returns:
            ErrorContext: Enriched context
        """
        import time

        start_time = time.time()

        if context is None:
            context = self.get_current_context()
            if context is None:
                context = ErrorContext()

        try:
            # System health enrichment
            if include_system_health and self.enrichment_config.include_system_health:
                await self._enrich_with_system_health(context)

            # Performance metrics enrichment
            if (
                include_performance_metrics
                and self.enrichment_config.include_performance_metrics
            ):
                await self._enrich_with_performance_metrics(context)

            # User information enrichment
            if context.user_id and self.enrichment_config.include_user_info:
                await self._enrich_with_user_info(context)

            # Ensure context size limits
            self._enforce_context_size_limits(context)

            # Track enrichment performance
            enrichment_time = time.time() - start_time
            self._enrichment_times.append(enrichment_time)
            if len(self._enrichment_times) > 1000:
                self._enrichment_times = self._enrichment_times[-500:]

            logger.debug(
                f"Enriched context {context.error_id} in {enrichment_time*1000:.2f}ms"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to enrich error context {context.error_id}: {e}")
            return context

    async def _enrich_with_system_health(self, context: ErrorContext):
        """Enrich context with system health information"""
        try:
            system_health = await self.health_manager.get_system_health_status()

            context.system_health = system_health.overall_health.value

            if system_health.failed_services:
                context.active_fallbacks = [
                    s.value for s in system_health.failed_services
                ]

            # Add health summary to context data
            context.context_data["system_health_summary"] = {
                "overall_health": system_health.overall_health.value,
                "available_services": len(system_health.available_services),
                "degraded_services": len(system_health.degraded_services),
                "failed_services": len(system_health.failed_services),
                "fallback_active": system_health.fallback_active,
                "emergency_mode": system_health.emergency_mode,
            }

        except Exception as e:
            logger.warning(f"Failed to enrich context with system health: {e}")

    async def _enrich_with_performance_metrics(self, context: ErrorContext):
        """Enrich context with performance metrics"""
        try:
            # Get performance summary from health manager
            perf_summary = await self.health_manager.get_performance_summary()

            context.context_data["performance_metrics"] = {
                "system_uptime": perf_summary.get("system_uptime_seconds"),
                "active_alerts": perf_summary.get("alerts", {}).get("active_count", 0),
                "critical_alerts": perf_summary.get("alerts", {}).get(
                    "critical_count", 0
                ),
            }

            # Add service-specific performance if relevant
            if context.service_type:
                service_perf = perf_summary.get("services", {}).get(
                    context.service_type.value
                )
                if service_perf:
                    context.context_data["service_performance"] = {
                        "health": service_perf.get("health"),
                        "response_time_ms": service_perf.get("response_time", {}).get(
                            "current_ms"
                        ),
                        "success_rate": service_perf.get("success_rate"),
                    }

        except Exception as e:
            logger.warning(f"Failed to enrich context with performance metrics: {e}")

    async def _enrich_with_user_info(self, context: ErrorContext):
        """Enrich context with user information (sanitized)"""
        try:
            # Check cache first
            cache_key = f"user_info_{context.user_id}"
            cached_info = self._context_cache.get(cache_key)

            if cached_info:
                context.context_data["user_info"] = cached_info
                return

            # In a real implementation, you would fetch user info from your user service
            # For now, we'll create a placeholder
            user_info = {
                "user_id_hash": hash(context.user_id),  # Hashed for privacy
                "has_admin_role": False,  # Would be fetched from user service
                "account_type": "standard",  # Would be fetched from user service
                "last_activity": datetime.utcnow().isoformat(),
            }

            # Cache the info
            self._cache_user_info(cache_key, user_info)
            context.context_data["user_info"] = user_info

        except Exception as e:
            logger.warning(f"Failed to enrich context with user info: {e}")

    def _cache_user_info(self, cache_key: str, user_info: Dict[str, Any]):
        """Cache user info for performance"""
        if len(self._context_cache) >= self._cache_max_size:
            # Remove oldest entries
            keys_to_remove = list(self._context_cache.keys())[:100]
            for key in keys_to_remove:
                del self._context_cache[key]

        self._context_cache[cache_key] = user_info

    def _enforce_context_size_limits(self, context: ErrorContext):
        """Enforce context size limits to prevent memory issues"""
        try:
            # Estimate context size
            context_str = str(context.context_data)
            context_size = len(context_str.encode("utf-8"))

            if context_size > self.enrichment_config.max_context_size_bytes:
                # Reduce context size by removing less important data
                if "request_headers" in context.context_data:
                    del context.context_data["request_headers"]

                if "query_params" in context.context_data:
                    del context.context_data["query_params"]

                # Truncate large string values
                for key, value in context.context_data.items():
                    if isinstance(value, str) and len(value) > 1000:
                        context.context_data[key] = value[:1000] + "...[truncated]"

                logger.warning(
                    f"Context size exceeded limit, reduced from {context_size} bytes",
                    extra={"context_id": context.error_id},
                )

        except Exception as e:
            logger.warning(f"Failed to enforce context size limits: {e}")

    def get_current_context(self) -> Optional[ErrorContext]:
        """Get the current error context from async context"""
        return _error_context_var.get()

    def get_correlation_id(self) -> Optional[str]:
        """Get the current correlation ID"""
        current_context = self.get_current_context()
        if current_context:
            return current_context.request_id
        return _correlation_id_var.get()

    @asynccontextmanager
    async def context_scope(
        self,
        operation_type: Optional[OperationType] = None,
        service_type: Optional[ServiceType] = None,
        user_id: Optional[str] = None,
        request_info: Optional[Dict[str, Any]] = None,
        enrich_async: bool = True,
        **additional_context,
    ) -> AsyncGenerator[ErrorContext, None]:
        """
        Context manager for error context lifecycle

        Args:
            operation_type: Type of operation
            service_type: Service type involved
            user_id: User identifier
            request_info: HTTP request information
            enrich_async: Whether to perform async enrichment
            **additional_context: Additional context data

        Yields:
            ErrorContext: The managed error context
        """
        # Create context
        context = self.create_context(
            operation_type=operation_type,
            service_type=service_type,
            user_id=user_id,
            request_info=request_info,
            **additional_context,
        )

        # Store previous context for restoration
        previous_context = _error_context_var.get()

        try:
            # Set new context
            _error_context_var.set(context)

            # Async enrichment if requested
            if enrich_async:
                context = await self.enrich_context_async(context)

            yield context

        finally:
            # Restore previous context
            _error_context_var.set(previous_context)

    def update_context(self, **updates):
        """Update the current error context"""
        current_context = self.get_current_context()
        if current_context:
            # Update context data with sanitized values
            sanitized_updates = sanitize_for_logging(updates)
            current_context.context_data.update(sanitized_updates)

    def add_context_breadcrumb(self, message: str, category: str = "info", **data):
        """Add a breadcrumb to the current context for debugging"""
        current_context = self.get_current_context()
        if current_context:
            if "breadcrumbs" not in current_context.context_data:
                current_context.context_data["breadcrumbs"] = []

            breadcrumb = {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "category": category,
                "data": sanitize_for_logging(data),
            }

            current_context.context_data["breadcrumbs"].append(breadcrumb)

            # Limit breadcrumbs to prevent context bloat
            if len(current_context.context_data["breadcrumbs"]) > 20:
                current_context.context_data["breadcrumbs"] = (
                    current_context.context_data["breadcrumbs"][-20:]
                )

    def get_context_statistics(self) -> Dict[str, Any]:
        """Get context management statistics"""
        avg_creation_time = 0
        if self._context_creation_times:
            avg_creation_time = sum(self._context_creation_times) / len(
                self._context_creation_times
            )

        avg_enrichment_time = 0
        if self._enrichment_times:
            avg_enrichment_time = sum(self._enrichment_times) / len(
                self._enrichment_times
            )

        return {
            "cache_size": len(self._context_cache),
            "cache_max_size": self._cache_max_size,
            "average_creation_time_ms": avg_creation_time * 1000,
            "average_enrichment_time_ms": avg_enrichment_time * 1000,
            "total_contexts_created": len(self._context_creation_times),
            "total_enrichments_performed": len(self._enrichment_times),
            "enrichment_config": {
                "include_request_headers": self.enrichment_config.include_request_headers,
                "include_user_info": self.enrichment_config.include_user_info,
                "include_system_health": self.enrichment_config.include_system_health,
                "include_performance_metrics": self.enrichment_config.include_performance_metrics,
                "max_context_size_bytes": self.enrichment_config.max_context_size_bytes,
            },
        }

    def clear_cache(self) -> int:
        """Clear the context cache"""
        count = len(self._context_cache)
        self._context_cache.clear()
        logger.info(f"Cleared {count} items from context cache")
        return count


# Singleton instance
_error_context_manager_instance: Optional[ErrorContextManager] = None


def get_error_context_manager() -> ErrorContextManager:
    """Get singleton ErrorContextManager instance"""
    global _error_context_manager_instance
    if _error_context_manager_instance is None:
        _error_context_manager_instance = ErrorContextManager()
    return _error_context_manager_instance


# Cleanup function for app shutdown
async def shutdown_error_context_manager():
    """Shutdown error context manager (call during app shutdown)"""
    global _error_context_manager_instance
    if _error_context_manager_instance:
        _error_context_manager_instance.clear_cache()
        _error_context_manager_instance = None


# Convenience functions for common usage patterns


def get_current_error_context() -> Optional[ErrorContext]:
    """Get the current error context"""
    return _error_context_var.get()


def get_current_correlation_id() -> Optional[str]:
    """Get the current correlation ID"""
    context = get_current_error_context()
    if context:
        return context.request_id
    return _correlation_id_var.get()


def add_breadcrumb(message: str, category: str = "info", **data):
    """Add a breadcrumb to the current context"""
    manager = get_error_context_manager()
    manager.add_context_breadcrumb(message, category, **data)


def update_context(**updates):
    """Update the current context"""
    manager = get_error_context_manager()
    manager.update_context(**updates)
