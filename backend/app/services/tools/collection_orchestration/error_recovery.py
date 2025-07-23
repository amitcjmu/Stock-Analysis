"""
Error Recovery Manager

Manages error recovery during collection with intelligent retry strategies.
"""

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .base import BaseCollectionTool

logger = logging.getLogger(__name__)


class ErrorRecoveryManager(AsyncBaseDiscoveryTool, BaseCollectionTool):
    """Manages error recovery during collection"""

    name: str = "ErrorRecoveryManager"
    description: str = "Handle errors and implement recovery strategies"

    def __init__(self):
        super().__init__()
        self.name = "ErrorRecoveryManager"
        self.error_success_probabilities = {
            "timeout": 0.6,
            "rate_limit": 0.3,
            "connection": 0.7,
            "authentication": 0.1,
            "permission_denied": 0.1,
            "unknown": 0.4,
        }

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="ErrorRecoveryManager",
            description="Manages error recovery and retry strategies",
            tool_class=cls,
            categories=["collection", "error_handling", "recovery"],
            required_params=["error_context", "recovery_action"],
            optional_params=["retry_config", "fallback_strategy"],
            context_aware=True,
            async_tool=True,
        )

    async def arun(
        self,
        error_context: Dict[str, Any],
        recovery_action: str,
        retry_config: Optional[Dict[str, Any]] = None,
        fallback_strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Manage error recovery during collection.

        Args:
            error_context: Context about the error (platform, error_type, details)
            recovery_action: Action to take (retry, skip, fallback, manual)
            retry_config: Retry configuration (max_retries, backoff)
            fallback_strategy: Fallback approach if retry fails

        Returns:
            Recovery results and recommendations
        """
        recovery_result = self._create_base_result("error_recovery") | {
            "error_context": error_context,
            "recovery_action": recovery_action,
            "actions_taken": [],
            "recommendations": [],
        }

        try:
            platform = error_context.get("platform")
            error_type = error_context.get("error_type")
            error_details = error_context.get("details", {})

            # Default retry config
            if not retry_config:
                retry_config = self._get_default_retry_config()

            if recovery_action == "retry":
                await self._handle_retry_action(
                    recovery_result,
                    platform,
                    error_type,
                    error_details,
                    retry_config,
                    fallback_strategy,
                )
            elif recovery_action == "skip":
                self._handle_skip_action(recovery_result, platform, error_type)
            elif recovery_action == "fallback":
                await self._handle_fallback_action(
                    recovery_result, platform, error_type, fallback_strategy
                )
            elif recovery_action == "manual":
                self._handle_manual_action(
                    recovery_result, platform, error_type, error_details
                )
            else:
                self._add_error(
                    recovery_result, f"Unknown recovery action: {recovery_action}"
                )
                return recovery_result

            # Add error-specific recommendations
            recovery_result["recommendations"].extend(
                self._generate_error_recommendations(
                    error_type, recovery_result["success"]
                )
            )

            self._mark_success(recovery_result)
            return recovery_result

        except Exception as e:
            self._add_error(recovery_result, f"Error recovery failed: {str(e)}")
            return recovery_result

    async def _handle_retry_action(
        self,
        recovery_result: Dict[str, Any],
        platform: str,
        error_type: str,
        error_details: Dict[str, Any],
        retry_config: Dict[str, Any],
        fallback_strategy: Optional[str],
    ):
        """Handle retry recovery action"""
        retry_result = await self._execute_retry(
            platform, error_type, error_details, retry_config
        )
        recovery_result["actions_taken"].append(retry_result)
        recovery_result["success"] = retry_result.get("success", False)

        # Apply fallback if retry failed
        if not recovery_result["success"] and fallback_strategy:
            fallback_result = await self._apply_fallback_strategy(
                platform, error_type, fallback_strategy
            )
            recovery_result["actions_taken"].append(fallback_result)
            recovery_result["success"] = fallback_result.get("success", False)

    def _handle_skip_action(
        self, recovery_result: Dict[str, Any], platform: str, error_type: str
    ):
        """Handle skip recovery action"""
        recovery_result["actions_taken"].append(
            {
                "action": "skip",
                "platform": platform,
                "reason": f"Skipping due to {error_type}",
            }
        )
        recovery_result["success"] = True
        recovery_result["recommendations"].append(
            f"Consider manual collection for {platform} data"
        )

    async def _handle_fallback_action(
        self,
        recovery_result: Dict[str, Any],
        platform: str,
        error_type: str,
        fallback_strategy: Optional[str],
    ):
        """Handle fallback recovery action"""
        if fallback_strategy:
            fallback_result = await self._apply_fallback_strategy(
                platform, error_type, fallback_strategy
            )
            recovery_result["actions_taken"].append(fallback_result)
            recovery_result["success"] = fallback_result.get("success", False)
        else:
            self._add_error(recovery_result, "Fallback strategy not specified")

    def _handle_manual_action(
        self,
        recovery_result: Dict[str, Any],
        platform: str,
        error_type: str,
        error_details: Dict[str, Any],
    ):
        """Handle manual intervention recovery action"""
        priority = self._determine_intervention_priority(error_type, error_details)

        recovery_result["actions_taken"].append(
            {
                "action": "queue_manual",
                "platform": platform,
                "priority": priority,
                "estimated_resolution_time": self._estimate_resolution_time(
                    error_type, priority
                ),
            }
        )
        recovery_result["success"] = True
        recovery_result["manual_intervention_required"] = True

    async def _execute_retry(
        self,
        platform: str,
        error_type: str,
        error_details: Dict[str, Any],
        retry_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute retry logic with backoff"""
        retry_result = {
            "action": "retry",
            "platform": platform,
            "attempts": 0,
            "success": False,
            "retry_details": [],
        }

        max_retries = retry_config.get("max_retries", 3)
        backoff = retry_config.get("backoff", "exponential")
        initial_delay = retry_config.get("initial_delay", 1)
        max_delay = retry_config.get("max_delay", 60)

        for attempt in range(max_retries):
            retry_result["attempts"] = attempt + 1

            # Calculate delay
            delay = self._calculate_backoff_delay(
                attempt, backoff, initial_delay, max_delay
            )

            # Wait before retry (except first attempt)
            if attempt > 0:
                await asyncio.sleep(delay)

            # Simulate retry attempt
            success = self._simulate_retry_attempt(error_type)

            attempt_details = {
                "attempt": attempt + 1,
                "delay": delay if attempt > 0 else 0,
                "success": success,
            }
            retry_result["retry_details"].append(attempt_details)

            if success:
                retry_result["success"] = True
                retry_result["recovered_at_attempt"] = attempt + 1
                break

        return retry_result

    async def _apply_fallback_strategy(
        self, platform: str, error_type: str, fallback_strategy: str
    ) -> Dict[str, Any]:
        """Apply fallback strategy"""
        fallback_result = {
            "action": "fallback",
            "platform": platform,
            "strategy": fallback_strategy,
            "success": False,
        }

        if fallback_strategy == "alternative_endpoint":
            fallback_result["details"] = "Attempting alternative API endpoint"
            fallback_result["success"] = True

        elif fallback_strategy == "reduced_scope":
            fallback_result["details"] = (
                "Reducing collection scope to critical data only"
            )
            fallback_result["success"] = True
            fallback_result["scope_reduction"] = "critical_only"

        elif fallback_strategy == "cached_data":
            fallback_result["details"] = "Using cached data from previous collection"
            fallback_result["success"] = True
            fallback_result["data_age"] = "2 hours"  # Simulated
            fallback_result["freshness_impact"] = "medium"

        elif fallback_strategy == "manual_upload":
            fallback_result["details"] = "Switching to manual data upload process"
            fallback_result["success"] = True
            fallback_result["manual_required"] = True

        else:
            fallback_result["details"] = (
                f"Unknown fallback strategy: {fallback_strategy}"
            )
            fallback_result["success"] = False

        return fallback_result

    def _calculate_backoff_delay(
        self, attempt: int, backoff: str, initial_delay: float, max_delay: float
    ) -> float:
        """Calculate delay for retry attempt"""
        if backoff == "exponential":
            delay = min(initial_delay * (2**attempt), max_delay)
        elif backoff == "linear":
            delay = min(initial_delay * (attempt + 1), max_delay)
        elif backoff == "constant":
            delay = initial_delay
        else:
            delay = initial_delay

        return delay

    def _simulate_retry_attempt(self, error_type: str) -> bool:
        """Simulate a retry attempt (for demonstration)"""
        success_probability = self.error_success_probabilities.get(error_type, 0.5)
        return random.random() < success_probability

    def _determine_intervention_priority(
        self, error_type: str, error_details: Dict[str, Any]
    ) -> str:
        """Determine priority for manual intervention"""
        # Critical errors get high priority
        critical_errors = ["authentication", "permission_denied", "invalid_credentials"]
        if error_type in critical_errors:
            return "high"

        # Repeated failures get medium priority
        if error_details.get("retry_count", 0) > 3:
            return "medium"

        # Volume-based priority
        affected_records = error_details.get("affected_records", 0)
        if affected_records > 1000:
            return "medium"

        return "low"

    def _estimate_resolution_time(self, error_type: str, priority: str) -> str:
        """Estimate time to resolve manual intervention"""
        base_times = {"high": "1-2 hours", "medium": "4-6 hours", "low": "1-2 days"}

        # Adjust for error type complexity
        complex_errors = ["authentication", "permission_denied", "configuration"]
        if error_type in complex_errors and priority != "low":
            time_map = {"high": "2-4 hours", "medium": "6-12 hours"}
            return time_map.get(priority, base_times[priority])

        return base_times.get(priority, "unknown")

    def _generate_error_recommendations(
        self, error_type: str, recovery_success: bool
    ) -> List[str]:
        """Generate error-specific recommendations"""
        recommendations = []

        error_recommendations = {
            "authentication": [
                "Verify and update platform credentials",
                "Check for expired API keys or tokens",
                "Review authentication method compatibility",
            ],
            "permission_denied": [
                "Verify user permissions for data access",
                "Check API scope and access rights",
                "Contact platform administrator if needed",
            ],
            "rate_limit": [
                "Implement request throttling",
                "Consider upgrading API tier for higher limits",
                "Distribute requests across time periods",
            ],
            "timeout": [
                "Increase timeout values for slow endpoints",
                "Consider breaking large requests into smaller batches",
                "Check network connectivity and latency",
            ],
            "connection": [
                "Verify network connectivity to platform",
                "Check firewall rules and proxy settings",
                "Test platform endpoint availability",
            ],
        }

        recommendations.extend(error_recommendations.get(error_type, []))

        if not recovery_success:
            recommendations.extend(
                [
                    "Consider scheduling collection during off-peak hours",
                    "Evaluate alternative collection methods",
                    "Review platform-specific best practices",
                ]
            )

        return recommendations

    def _get_default_retry_config(self) -> Dict[str, Any]:
        """Get default retry configuration"""
        return {
            "max_retries": 3,
            "backoff": "exponential",
            "initial_delay": 1,
            "max_delay": 60,
        }
