"""
Utility functions for Service Health Manager

Contains helper functions for health calculations, recommendations, and analysis.
"""

from typing import Dict, List

from .base import ServiceConfig, ServiceHealth, ServiceType, SystemHealth


class HealthUtils:
    """Utility class for health monitoring calculations and analysis"""

    @staticmethod
    def calculate_overall_health(
        service_configs: Dict[ServiceType, ServiceConfig],
        unhealthy_services: List[ServiceType],
        degraded_services: List[ServiceType],
    ) -> SystemHealth:
        """Calculate overall system health based on service statuses"""
        total_services = len(service_configs)
        critical_services = {
            ServiceType.REDIS,
            ServiceType.DATABASE,
            ServiceType.AUTH_CACHE,
        }

        # Convert to sets for easier operations
        unhealthy_set = set(unhealthy_services)
        degraded_set = set(degraded_services)

        # Check critical services
        critical_failed = unhealthy_set.intersection(critical_services)
        critical_degraded = degraded_set.intersection(critical_services)

        if len(critical_failed) >= 2:
            return SystemHealth.EMERGENCY_MODE

        if len(critical_failed) == 1 or len(unhealthy_services) > total_services * 0.5:
            return SystemHealth.LIMITED_FUNCTIONALITY

        if len(degraded_services) > 0 or len(critical_degraded) > 0:
            return SystemHealth.DEGRADED_PERFORMANCE

        return SystemHealth.FULLY_OPERATIONAL

    @staticmethod
    def generate_health_recommendations(
        service_statuses: Dict[ServiceType, ServiceHealth],
        unhealthy_services: List[ServiceType],
        degraded_services: List[ServiceType],
    ) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        # Critical service failures
        if ServiceType.REDIS in unhealthy_services:
            recommendations.append(
                "Redis service is down - fallback to in-memory cache active. "
                "Check Redis configuration and network connectivity."
            )

        if ServiceType.DATABASE in unhealthy_services:
            recommendations.append(
                "Database service is down - system in emergency mode. "
                "Check database server status and connection parameters."
            )

        if ServiceType.AUTH_CACHE in unhealthy_services:
            recommendations.append(
                "Authentication cache is down - login performance may be degraded. "
                "Verify auth cache service status."
            )

        # Storage and external service issues
        if ServiceType.STORAGE_MANAGER in unhealthy_services:
            recommendations.append(
                "Storage manager is unavailable - file operations may fail. "
                "Check storage service connectivity."
            )

        if ServiceType.LLM_SERVICE in unhealthy_services:
            recommendations.append(
                "LLM service is unavailable - AI features may be disabled. "
                "Check external LLM service status and API keys."
            )

        if ServiceType.EMBEDDING_SERVICE in unhealthy_services:
            recommendations.append(
                "Embedding service is unavailable - search features may be limited. "
                "Check embedding service configuration."
            )

        # Degraded services
        for service_type in degraded_services:
            recommendations.append(
                f"{service_type.value} service is experiencing degraded performance. "
                f"Monitor response times and consider scaling resources."
            )

        # General recommendations based on system state
        if len(unhealthy_services) > 2:
            recommendations.append(
                "Multiple services are failing. Check system resources (CPU, memory, network) "
                "and consider implementing emergency procedures."
            )

        if not recommendations:
            recommendations.append("All services are operating normally.")

        return recommendations

    @staticmethod
    def estimate_recovery_time(
        service_statuses: Dict[ServiceType, ServiceHealth],
    ) -> int:
        """Estimate recovery time in minutes based on service failures"""
        unhealthy_count = sum(
            1
            for health in service_statuses.values()
            if health == ServiceHealth.CRITICAL
        )

        if unhealthy_count == 0:
            return 0
        elif unhealthy_count == 1:
            return 5  # Single service recovery
        elif unhealthy_count <= 3:
            return 15  # Multiple service recovery
        else:
            return 30  # System-wide issues

    @staticmethod
    def get_service_priority(service_type: ServiceType) -> int:
        """Get priority level for service recovery (1=highest, 3=lowest)"""
        critical_services = {
            ServiceType.REDIS,
            ServiceType.DATABASE,
            ServiceType.AUTH_CACHE,
        }

        if service_type in critical_services:
            return 1
        elif service_type == ServiceType.STORAGE_MANAGER:
            return 2
        else:
            return 3

    @staticmethod
    def should_trigger_failover(
        service_type: ServiceType, consecutive_failures: int, config: ServiceConfig
    ) -> bool:
        """Determine if failover should be triggered for a service"""
        if service_type in [ServiceType.REDIS, ServiceType.AUTH_CACHE]:
            # These have in-memory fallbacks
            return consecutive_failures >= config.failure_threshold
        elif service_type == ServiceType.DATABASE:
            # Database failures are critical - trigger failover quickly
            return consecutive_failures >= 2
        else:
            # Other services use standard threshold
            return consecutive_failures >= config.failure_threshold
