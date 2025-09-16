"""
Enhanced Error Handler - Utility Functions

Provides utility functions for error handling, statistics collection,
and system management operations.

Key Features:
- Error handling statistics
- Cache management utilities
- System health enrichment helpers
- Configuration management
"""

from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.monitoring.service_health_manager import (
    get_service_health_manager,
)

from .base import ErrorContext
from .formatters import get_error_response_formatter
from .recovery import get_error_recovery_manager
from .strategies import get_error_classification_strategy

logger = get_logger(__name__)


class ErrorHandlerUtils:
    """Utility functions for error handling operations"""

    def __init__(self):
        self.health_manager = get_service_health_manager()
        logger.info("ErrorHandlerUtils initialized")

    async def enrich_context_with_system_state(self, context: ErrorContext):
        """Enrich error context with current system state"""
        try:
            # Get system health status
            system_health = await self.health_manager.get_system_health_status()
            context.system_health = system_health.overall_health.value

            # Get active fallbacks
            if system_health.fallback_active:
                context.active_fallbacks = [
                    service.value for service in system_health.failed_services
                ]

        except Exception as e:
            logger.warning(f"Failed to enrich error context with system state: {e}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error handling statistics"""
        try:
            # Get statistics from all components
            classification_strategy = get_error_classification_strategy()
            recovery_manager = get_error_recovery_manager()
            response_formatter = get_error_response_formatter()

            classification_stats = {
                "classification_cache_size": len(
                    classification_strategy.classification_cache
                ),
            }

            recovery_stats = recovery_manager.get_error_statistics()

            return {
                "classification": classification_stats,
                "recovery": recovery_stats,
                "configuration": {
                    "debug_info_enabled": getattr(settings, "DEBUG", False),
                    "recovery_enabled": getattr(
                        settings, "ERROR_RECOVERY_ENABLED", True
                    ),
                    "pattern_learning_enabled": getattr(
                        settings, "ERROR_PATTERN_LEARNING", True
                    ),
                },
                "formatter": {
                    "debug_info_enabled": response_formatter.enable_debug_info,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get error statistics: {e}")
            return {"error": f"Failed to get statistics: {e}"}

    def clear_all_caches(self) -> Dict[str, int]:
        """Clear all error handling caches"""
        try:
            classification_strategy = get_error_classification_strategy()
            recovery_manager = get_error_recovery_manager()

            classification_cleared = classification_strategy.clear_cache()
            patterns_cleared = recovery_manager.clear_error_patterns()

            total_cleared = classification_cleared + patterns_cleared

            logger.info(
                f"Cleared all error handling caches: {total_cleared} items total"
            )

            return {
                "classification_cache": classification_cleared,
                "error_patterns": patterns_cleared,
                "total_cleared": total_cleared,
            }

        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")
            return {"error": f"Failed to clear caches: {e}"}

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate error handler configuration"""
        config_status = {
            "valid": True,
            "issues": [],
            "recommendations": [],
        }

        try:
            # Check required settings
            debug_enabled = getattr(settings, "DEBUG", False)
            recovery_enabled = getattr(settings, "ERROR_RECOVERY_ENABLED", True)
            pattern_learning = getattr(settings, "ERROR_PATTERN_LEARNING", True)

            # Validate configuration combinations
            if debug_enabled and not pattern_learning:
                config_status["recommendations"].append(
                    "Consider enabling pattern learning in debug mode for better insights"
                )

            if not recovery_enabled and pattern_learning:
                config_status["recommendations"].append(
                    "Pattern learning is most effective when recovery is enabled"
                )

            # Check service dependencies
            try:
                get_service_health_manager()
                config_status["services"] = {
                    "health_manager": "available",
                }
            except Exception as e:
                config_status["valid"] = False
                config_status["issues"].append(f"Health manager unavailable: {e}")

            # Configuration summary
            config_status["current_config"] = {
                "debug_enabled": debug_enabled,
                "recovery_enabled": recovery_enabled,
                "pattern_learning_enabled": pattern_learning,
            }

        except Exception as e:
            config_status["valid"] = False
            config_status["issues"].append(f"Configuration validation failed: {e}")

        return config_status


# Singleton instance
_error_handler_utils_instance: Optional[ErrorHandlerUtils] = None


def get_error_handler_utils() -> ErrorHandlerUtils:
    """Get singleton ErrorHandlerUtils instance"""
    global _error_handler_utils_instance
    if _error_handler_utils_instance is None:
        _error_handler_utils_instance = ErrorHandlerUtils()
    return _error_handler_utils_instance


# Cleanup function for app shutdown
async def shutdown_error_handler_utils():
    """Shutdown error handler utils (call during app shutdown)"""
    global _error_handler_utils_instance
    if _error_handler_utils_instance:
        _error_handler_utils_instance = None
