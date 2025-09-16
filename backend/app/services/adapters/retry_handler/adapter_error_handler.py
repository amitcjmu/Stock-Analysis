"""
High-level error handler for adapter operations.

This module contains the AdapterErrorHandler class that provides unified
error handling across all adapters with automatic error classification,
retry logic, circuit breaking, error reporting and recovery recommendations.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from app.services.collection_flow.adapters import CollectionResponse

from .base import RetryConfig
from .exceptions import CircuitBreakerOpenError, MaxRetriesExceededError
from .handler import RetryHandler


class AdapterErrorHandler:
    """
    High-level error handler for adapter operations

    Provides unified error handling across all adapters with:
    - Automatic error classification and response
    - Retry logic with circuit breaking
    - Error reporting and analytics
    - Recovery recommendations
    """

    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_handler = RetryHandler(retry_config)
        self.logger = logging.getLogger(f"{__name__}.AdapterErrorHandler")

    async def handle_collection_request(
        self,
        adapter_func: Callable,
        request_args: tuple,
        request_kwargs: dict,
        adapter_name: str,
        platform: str,
    ) -> CollectionResponse:
        """
        Handle a collection request with comprehensive error handling

        Args:
            adapter_func: Adapter's collect_data method
            request_args: Arguments for the adapter function
            request_kwargs: Keyword arguments for the adapter function
            adapter_name: Name of the adapter
            platform: Platform being collected from

        Returns:
            CollectionResponse with success or error information
        """
        try:
            response = await self.retry_handler.execute_with_retry(
                adapter_func,
                *request_args,
                adapter_name=adapter_name,
                platform=platform,
                **request_kwargs,
            )

            # Validate response
            if not isinstance(response, CollectionResponse):
                raise ValueError(
                    f"Adapter returned invalid response type: {type(response)}"
                )

            return response

        except CircuitBreakerOpenError as e:
            self.logger.error(
                f"Circuit breaker open for {adapter_name}:{platform}: {str(e)}"
            )
            return CollectionResponse(
                success=False,
                error_message="Service temporarily unavailable due to repeated failures",
                error_details={
                    "error_type": "circuit_breaker_open",
                    "adapter": adapter_name,
                    "platform": platform,
                    "recovery_time": "Please try again in a few minutes",
                },
            )

        except MaxRetriesExceededError as e:
            self.logger.error(
                f"Max retries exceeded for {adapter_name}:{platform}: {str(e)}"
            )
            return CollectionResponse(
                success=False,
                error_message="Collection failed after multiple retry attempts",
                error_details={
                    "error_type": "max_retries_exceeded",
                    "adapter": adapter_name,
                    "platform": platform,
                    "recommendation": "Check adapter configuration and platform connectivity",
                },
            )

        except Exception as e:
            self.logger.error(
                f"Unexpected error in {adapter_name}:{platform}: {str(e)}"
            )
            error_pattern = self.retry_handler._error_classifier.classify_error(e)

            return CollectionResponse(
                success=False,
                error_message=str(e),
                error_details={
                    "error_type": error_pattern.error_type.value,
                    "severity": error_pattern.severity.value,
                    "adapter": adapter_name,
                    "platform": platform,
                    "exception_type": type(e).__name__,
                },
            )

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of error handling system"""
        error_summary = self.retry_handler.get_error_summary(hours=1)
        circuit_status = self.retry_handler.get_circuit_breaker_status()

        # Determine health status
        critical_errors = error_summary.get("severity_distribution", {}).get(
            "critical", 0
        )
        open_circuits = sum(
            1
            for state in circuit_status.get("circuit_breakers", {}).values()
            if state.get("is_open", False)
        )

        if critical_errors > 0 or open_circuits > 0:
            health = "unhealthy"
        elif error_summary.get("total_errors", 0) > 10:
            health = "degraded"
        else:
            health = "healthy"

        return {
            "health_status": health,
            "error_summary": error_summary,
            "circuit_breaker_status": circuit_status,
            "recommendations": self._get_health_recommendations(
                error_summary, circuit_status
            ),
        }

    def _get_health_recommendations(
        self, error_summary: Dict[str, Any], circuit_status: Dict[str, Any]
    ) -> List[str]:
        """Get health recommendations based on current status"""
        recommendations = []

        # Check for critical errors
        critical_count = error_summary.get("severity_distribution", {}).get(
            "critical", 0
        )
        if critical_count > 0:
            recommendations.append(
                "Critical errors detected - check adapter configurations and credentials"
            )

        # Check for high error rates
        total_errors = error_summary.get("total_errors", 0)
        if total_errors > 50:
            recommendations.append(
                "High error rate detected - consider adjusting retry strategies"
            )

        # Check for open circuit breakers
        open_circuits = [
            key
            for key, state in circuit_status.get("circuit_breakers", {}).items()
            if state.get("is_open", False)
        ]
        if open_circuits:
            recommendations.append(
                f"Circuit breakers open for: {', '.join(open_circuits)} - check service availability"
            )

        # Check for authentication errors
        auth_errors = error_summary.get("error_types", {}).get("authentication", 0)
        if auth_errors > 0:
            recommendations.append(
                "Authentication errors detected - verify credentials and permissions"
            )

        # Check for network errors
        network_errors = error_summary.get("error_types", {}).get(
            "network_connectivity", 0
        )
        if network_errors > 5:
            recommendations.append(
                "Network connectivity issues detected - check network configuration"
            )

        if not recommendations:
            recommendations.append("System is operating normally")

        return recommendations
