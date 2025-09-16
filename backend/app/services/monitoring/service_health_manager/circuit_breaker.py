"""
Circuit Breaker functionality for Service Health Manager

Implements circuit breaker pattern for service health monitoring.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional

from app.core.logging import get_logger
from app.services.adapters.retry_handler import CircuitBreakerState

from .base import HealthCheckResult, ServiceType

logger = get_logger(__name__)


class CircuitBreakerManager:
    """Manages circuit breaker states for all monitored services"""

    def __init__(self):
        self.circuit_breakers: Dict[ServiceType, CircuitBreakerState] = {}

    def initialize_circuit_breaker(self, service_type: ServiceType) -> None:
        """Initialize circuit breaker for a service"""
        if service_type not in self.circuit_breakers:
            self.circuit_breakers[service_type] = CircuitBreakerState()

    def check_circuit_breaker_state(
        self, service_type: ServiceType, config
    ) -> Optional[HealthCheckResult]:
        """Check if circuit breaker allows the health check to proceed"""
        circuit_breaker = self.circuit_breakers.get(service_type)
        if not circuit_breaker:
            return None

        if circuit_breaker.is_open:
            # Check if we can attempt to close the circuit
            if (
                circuit_breaker.next_attempt_time
                and datetime.utcnow() >= circuit_breaker.next_attempt_time
            ):
                circuit_breaker.is_open = False
                logger.info(
                    f"Circuit breaker for {service_type} entering half-open state"
                )
                return None
            else:
                # Circuit still open - return failed result
                return HealthCheckResult(
                    service_type=service_type,
                    is_healthy=False,
                    response_time_ms=0,
                    error_message="Circuit breaker is open",
                    additional_data={"circuit_breaker_open": True},
                )

        return None  # Circuit breaker allows the check to proceed

    def update_circuit_breaker(
        self, service_type: ServiceType, result: HealthCheckResult, config
    ) -> None:
        """Update circuit breaker state based on health check result"""
        circuit_breaker = self.circuit_breakers.get(service_type)
        if not circuit_breaker:
            return

        if result.is_healthy:
            # Success - reset failure count and close circuit if needed
            circuit_breaker.failure_count = 0
            if circuit_breaker.is_open:
                circuit_breaker.is_open = False
                circuit_breaker.next_attempt_time = None
                logger.info(f"Circuit breaker for {service_type} closed after success")
        else:
            # Failure - increment failure count
            circuit_breaker.failure_count += 1

            # Check if we should open the circuit breaker
            if (
                not circuit_breaker.is_open
                and circuit_breaker.failure_count >= config.circuit_breaker_threshold
            ):
                circuit_breaker.is_open = True
                circuit_breaker.next_attempt_time = datetime.utcnow() + timedelta(
                    seconds=config.circuit_breaker_timeout_seconds
                )
                logger.warning(
                    f"Circuit breaker for {service_type} opened after {circuit_breaker.failure_count} failures"
                )

    def reset_circuit_breaker(self, service_type: ServiceType) -> bool:
        """Manually reset circuit breaker for a service"""
        circuit_breaker = self.circuit_breakers.get(service_type)
        if not circuit_breaker:
            return False

        circuit_breaker.is_open = False
        circuit_breaker.failure_count = 0
        circuit_breaker.next_attempt_time = None

        logger.info(f"Circuit breaker for {service_type} manually reset")
        return True

    def is_service_available(self, service_type: ServiceType) -> bool:
        """Check if a service is available based on circuit breaker state"""
        circuit_breaker = self.circuit_breakers.get(service_type)
        if not circuit_breaker:
            return True  # No circuit breaker means service is available

        return not circuit_breaker.is_open

    def get_circuit_breaker_status(self, service_type: ServiceType) -> Dict:
        """Get circuit breaker status for a service"""
        circuit_breaker = self.circuit_breakers.get(service_type)
        if not circuit_breaker:
            return {"status": "not_configured"}

        return {
            "is_open": circuit_breaker.is_open,
            "failure_count": circuit_breaker.failure_count,
            "next_attempt_time": (
                circuit_breaker.next_attempt_time.isoformat()
                if circuit_breaker.next_attempt_time
                else None
            ),
        }
