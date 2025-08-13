"""
Service Registry Metrics Module

Provides performance monitoring and metrics collection for the Service Registry pattern.
Tracks service instantiation, cache hits, resource usage, and cleanup efficiency.
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from collections import defaultdict
import psutil
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServiceMetrics:
    """Metrics for a single service type"""

    service_name: str
    instantiation_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_execution_time_ms: float = 0.0
    average_execution_time_ms: float = 0.0
    last_accessed: Optional[datetime] = None
    error_count: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


@dataclass
class RegistryMetrics:
    """Overall metrics for a Service Registry instance"""

    registry_id: str
    creation_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cleanup_time: Optional[datetime] = None
    services_created: int = 0
    total_cache_hits: int = 0
    total_cache_misses: int = 0
    metrics_flushed: int = 0
    memory_usage_mb: float = 0.0
    lifetime_seconds: float = 0.0

    @property
    def overall_cache_hit_rate(self) -> float:
        """Calculate overall cache hit rate"""
        total = self.total_cache_hits + self.total_cache_misses
        return (self.total_cache_hits / total * 100) if total > 0 else 0.0


class ServiceRegistryMonitor:
    """
    Monitors Service Registry performance and collects metrics.

    This class provides:
    - Real-time performance tracking
    - Service instantiation metrics
    - Cache efficiency monitoring
    - Resource usage tracking
    - Cleanup performance metrics
    """

    def __init__(self):
        """Initialize the monitor"""
        self._registry_metrics: Dict[str, RegistryMetrics] = {}
        self._service_metrics: Dict[str, Dict[str, ServiceMetrics]] = defaultdict(dict)
        self._lock = asyncio.Lock()

        # Performance thresholds for alerting (configurable via environment)
        self.instantiation_threshold_ms = float(
            os.getenv("SERVICE_REGISTRY_INSTANTIATION_THRESHOLD_MS", "100")
        )  # Alert if service creation takes > this many ms
        self.memory_threshold_mb = float(
            os.getenv("SERVICE_REGISTRY_MEMORY_THRESHOLD_MB", "500")
        )  # Alert if registry uses > this many MB
        self.cache_hit_threshold = float(
            os.getenv("SERVICE_REGISTRY_CACHE_HIT_THRESHOLD", "80")
        )  # Alert if cache hit rate < this percentage

        logger.info(
            f"ServiceRegistryMonitor initialized with thresholds: "
            f"instantiation>{self.instantiation_threshold_ms}ms, "
            f"memory>{self.memory_threshold_mb}MB, "
            f"cache_hit<{self.cache_hit_threshold}%"
        )

    def track_registry_creation(self, registry_id: str) -> None:
        """Track creation of a new Service Registry"""
        self._registry_metrics[registry_id] = RegistryMetrics(registry_id=registry_id)
        logger.debug(f"Tracking new registry: {registry_id}")

    def track_service_instantiation(
        self,
        registry_id: str,
        service_name: str,
        execution_time_ms: float,
        cache_hit: bool,
    ) -> None:
        """
        Track service instantiation metrics.

        Args:
            registry_id: ID of the Service Registry
            service_name: Name of the service class
            execution_time_ms: Time taken to instantiate (milliseconds)
            cache_hit: Whether this was a cache hit
        """
        # Update registry metrics
        if registry_id in self._registry_metrics:
            metrics = self._registry_metrics[registry_id]
            if cache_hit:
                metrics.total_cache_hits += 1
            else:
                metrics.total_cache_misses += 1
                metrics.services_created += 1

        # Update service-specific metrics
        if service_name not in self._service_metrics[registry_id]:
            self._service_metrics[registry_id][service_name] = ServiceMetrics(
                service_name=service_name
            )

        service_metric = self._service_metrics[registry_id][service_name]

        if cache_hit:
            service_metric.cache_hits += 1
        else:
            service_metric.cache_misses += 1
            service_metric.instantiation_count += 1

        service_metric.total_execution_time_ms += execution_time_ms
        service_metric.average_execution_time_ms = (
            service_metric.total_execution_time_ms
            / (service_metric.cache_hits + service_metric.cache_misses)
        )
        service_metric.last_accessed = datetime.now(timezone.utc)

        # Check performance thresholds
        if not cache_hit and execution_time_ms > self.instantiation_threshold_ms:
            logger.warning(
                f"Slow service instantiation: {service_name} took {execution_time_ms:.2f}ms"
            )

    def track_metrics_flush(self, registry_id: str, metrics_count: int) -> None:
        """Track metrics flush operation"""
        if registry_id in self._registry_metrics:
            self._registry_metrics[registry_id].metrics_flushed += metrics_count

    def track_registry_cleanup(self, registry_id: str) -> None:
        """Track registry cleanup"""
        if registry_id in self._registry_metrics:
            metrics = self._registry_metrics[registry_id]
            metrics.cleanup_time = datetime.now(timezone.utc)
            metrics.lifetime_seconds = (
                metrics.cleanup_time - metrics.creation_time
            ).total_seconds()

            # Calculate final memory usage
            process = psutil.Process()
            metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024

            logger.info(
                f"Registry {registry_id} cleaned up - "
                f"Lifetime: {metrics.lifetime_seconds:.2f}s, "
                f"Services created: {metrics.services_created}, "
                f"Cache hit rate: {metrics.overall_cache_hit_rate:.1f}%"
            )

    def get_registry_metrics(self, registry_id: str) -> Optional[RegistryMetrics]:
        """Get metrics for a specific registry"""
        return self._registry_metrics.get(registry_id)

    def get_service_metrics(
        self, registry_id: str, service_name: Optional[str] = None
    ) -> Dict[str, ServiceMetrics]:
        """Get service metrics for a registry"""
        if service_name:
            metric = self._service_metrics.get(registry_id, {}).get(service_name)
            return {service_name: metric} if metric else {}
        return dict(self._service_metrics.get(registry_id, {}))

    def get_performance_summary(self, registry_id: str) -> Dict[str, Any]:
        """
        Get a performance summary for a registry.

        Returns:
            Dictionary with performance metrics and recommendations
        """
        registry_metrics = self._registry_metrics.get(registry_id)
        if not registry_metrics:
            return {"error": "Registry not found"}

        service_metrics = self._service_metrics.get(registry_id, {})

        # Calculate aggregates
        total_service_calls = sum(
            s.cache_hits + s.cache_misses for s in service_metrics.values()
        )
        avg_instantiation_time = (
            (
                sum(s.average_execution_time_ms for s in service_metrics.values())
                / len(service_metrics)
            )
            if service_metrics
            else 0
        )

        # Check for performance issues
        issues = []
        recommendations = []

        if registry_metrics.overall_cache_hit_rate < self.cache_hit_threshold:
            issues.append(
                f"Low cache hit rate: {registry_metrics.overall_cache_hit_rate:.1f}%"
            )
            recommendations.append(
                "Consider increasing service cache lifetime or preloading common services"
            )

        if avg_instantiation_time > self.instantiation_threshold_ms:
            issues.append(f"Slow average instantiation: {avg_instantiation_time:.2f}ms")
            recommendations.append(
                "Review service constructors for performance bottlenecks"
            )

        if registry_metrics.memory_usage_mb > self.memory_threshold_mb:
            issues.append(
                f"High memory usage: {registry_metrics.memory_usage_mb:.1f}MB"
            )
            recommendations.append(
                "Consider implementing service cleanup or reducing cache size"
            )

        return {
            "registry_id": registry_id,
            "lifetime_seconds": registry_metrics.lifetime_seconds,
            "services_created": registry_metrics.services_created,
            "total_service_calls": total_service_calls,
            "cache_hit_rate": registry_metrics.overall_cache_hit_rate,
            "avg_instantiation_time_ms": avg_instantiation_time,
            "memory_usage_mb": registry_metrics.memory_usage_mb,
            "metrics_flushed": registry_metrics.metrics_flushed,
            "performance_issues": issues,
            "recommendations": recommendations,
            "healthy": len(issues) == 0,
        }

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for monitoring systems"""

        def serialize_registry(m: RegistryMetrics) -> Dict[str, Any]:
            """Serialize registry metrics with proper datetime handling"""
            d = vars(m).copy()
            d["creation_time"] = (
                m.creation_time.isoformat() if m.creation_time else None
            )
            d["cleanup_time"] = m.cleanup_time.isoformat() if m.cleanup_time else None
            return d

        def serialize_service(s: ServiceMetrics) -> Dict[str, Any]:
            """Serialize service metrics with proper datetime handling"""
            d = vars(s).copy()
            d["last_accessed"] = (
                s.last_accessed.isoformat() if s.last_accessed else None
            )
            d["cache_hit_rate"] = s.cache_hit_rate
            return d

        return {
            "registries": {
                rid: {
                    "metrics": serialize_registry(metrics),
                    "services": {
                        sname: serialize_service(smetric)
                        for sname, smetric in self._service_metrics.get(rid, {}).items()
                    },
                }
                for rid, metrics in self._registry_metrics.items()
            },
            "summary": {
                "total_registries": len(self._registry_metrics),
                "active_registries": sum(
                    1 for m in self._registry_metrics.values() if m.cleanup_time is None
                ),
                "total_services_created": sum(
                    m.services_created for m in self._registry_metrics.values()
                ),
                "overall_cache_hit_rate": (
                    sum(m.total_cache_hits for m in self._registry_metrics.values())
                    / max(
                        1,
                        sum(
                            m.total_cache_hits + m.total_cache_misses
                            for m in self._registry_metrics.values()
                        ),
                    )
                    * 100
                ),
            },
        }


# Global monitor instance
_monitor = ServiceRegistryMonitor()


def get_monitor() -> ServiceRegistryMonitor:
    """Get the global Service Registry monitor"""
    return _monitor
