"""
Cache performance metrics and monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CachePerformanceMetrics:
    """Cache performance metrics"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    errors: int = 0
    total_requests: int = 0
    average_response_time_ms: float = 0.0
    cache_utilization: float = 0.0
    last_reset: datetime = field(default_factory=datetime.utcnow)

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate as percentage"""
        return 100.0 - self.hit_rate

    def reset(self):
        """Reset all metrics"""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.invalidations = 0
        self.errors = 0
        self.total_requests = 0
        self.average_response_time_ms = 0.0
        self.cache_utilization = 0.0
        self.last_reset = datetime.utcnow()
