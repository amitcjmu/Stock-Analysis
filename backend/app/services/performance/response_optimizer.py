"""
Agent Response Time Optimizer
Implements Task 4.1 of the Discovery Flow Redesign.
Optimizes agent response times through caching, parallel processing, and performance monitoring.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for agent operations"""

    operation_type: str
    start_time: float
    end_time: float
    duration: float
    cache_hit: bool
    optimization_applied: List[str]


class ResponseCache:
    """Intelligent caching system for agent responses"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def _generate_cache_key(self, operation: str, context: Dict[str, Any]) -> str:
        """Generate cache key from operation and context"""
        cache_data = {
            "operation": operation,
            "page": context.get("page"),
            "agent_id": context.get("agent_id"),
            "data_hash": self._hash_data(context.get("page_data", {})),
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Create hash of data for cache key"""
        try:
            relevant_fields = ["assets", "fields", "dependencies", "tech_debt"]
            filtered_data = {k: v for k, v in data.items() if k in relevant_fields}
            return hashlib.md5(
                json.dumps(filtered_data, sort_keys=True).encode()
            ).hexdigest()[:16]
        except Exception:
            return "default"

    def get(self, operation: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached response if available and valid"""
        cache_key = self._generate_cache_key(operation, context)

        if cache_key not in self.cache:
            return None

        cached_item = self.cache[cache_key]

        # Check TTL
        if time.time() - cached_item["timestamp"] > self.ttl_seconds:
            self._remove_cache_item(cache_key)
            return None

        self.access_times[cache_key] = time.time()
        logger.info(f"🎯 Cache hit for {operation}")
        return cached_item["data"]

    def set(
        self, operation: str, context: Dict[str, Any], response: Dict[str, Any]
    ) -> None:
        """Cache response with TTL and LRU eviction"""
        cache_key = self._generate_cache_key(operation, context)

        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[cache_key] = {
            "data": response,
            "timestamp": time.time(),
            "operation": operation,
        }
        self.access_times[cache_key] = time.time()
        logger.info(f"🎯 Cached response for {operation}")

    def _evict_lru(self) -> None:
        """Evict least recently used items"""
        if not self.access_times:
            return

        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove_cache_item(lru_key)

    def _remove_cache_item(self, cache_key: str) -> None:
        """Remove item from cache"""
        self.cache.pop(cache_key, None)
        self.access_times.pop(cache_key, None)


class ResponseOptimizer:
    """Main response optimization service"""

    def __init__(self):
        self.cache = ResponseCache(max_size=1000, ttl_seconds=3600)
        self.performance_metrics: List[PerformanceMetrics] = []

        logger.info(
            "🚀 Response Optimizer initialized with caching and performance monitoring"
        )

    async def optimize_agent_response(
        self, operation_type: str, context: Dict[str, Any], response_func: Callable
    ) -> Dict[str, Any]:
        """Optimize agent response using available strategies"""
        start_time = time.time()

        # Check cache first
        cached_response = self.cache.get(operation_type, context)
        if cached_response:
            self._record_metrics(
                operation_type, start_time, time.time(), True, ["cache_hit"]
            )
            cached_response["_cache_hit"] = True
            cached_response["_response_time"] = time.time() - start_time
            return cached_response

        # Execute response function with timeout protection
        try:
            optimized_response = await asyncio.wait_for(
                response_func(context), timeout=30.0
            )

            # Cache successful response
            if optimized_response and not optimized_response.get("error"):
                self.cache.set(operation_type, context, optimized_response)

            self._record_metrics(
                operation_type, start_time, time.time(), False, ["timeout_protection"]
            )

            if isinstance(optimized_response, dict):
                optimized_response["_cache_hit"] = False
                optimized_response["_response_time"] = time.time() - start_time

            return optimized_response

        except asyncio.TimeoutError:
            logger.warning(f"⏰ {operation_type} timed out after 30s")
            self._record_metrics(
                operation_type, start_time, time.time(), False, ["timeout_occurred"]
            )
            return {
                "error": "Operation timed out",
                "operation_type": operation_type,
                "_response_time": time.time() - start_time,
            }
        except Exception as e:
            logger.error(f"❌ {operation_type} optimization failed: {e}")
            self._record_metrics(
                operation_type, start_time, time.time(), False, ["error_occurred"]
            )
            return {
                "error": str(e),
                "operation_type": operation_type,
                "_response_time": time.time() - start_time,
            }

    def _record_metrics(
        self,
        operation_type: str,
        start_time: float,
        end_time: float,
        cache_hit: bool,
        optimizations: List[str],
    ):
        """Record performance metrics"""
        metrics = PerformanceMetrics(
            operation_type=operation_type,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            cache_hit=cache_hit,
            optimization_applied=optimizations,
        )

        self.performance_metrics.append(metrics)

        # Keep only last 1000 metrics to prevent memory issues
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-1000:]

        status = "🎯" if cache_hit else "📊"
        logger.info(f"{status} {operation_type} completed in {metrics.duration:.2f}s")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.performance_metrics:
            return {"message": "No performance data available"}

        total_operations = len(self.performance_metrics)
        cache_hits = sum(1 for m in self.performance_metrics if m.cache_hit)

        durations = [m.duration for m in self.performance_metrics]
        avg_duration = sum(durations) / len(durations)

        return {
            "total_operations": total_operations,
            "cache_hit_rate": cache_hits / total_operations,
            "average_duration": avg_duration,
            "min_duration": min(durations),
            "max_duration": max(durations),
            "performance_grade": self._calculate_performance_grade(
                avg_duration, cache_hits / total_operations
            ),
        }

    def _calculate_performance_grade(
        self, avg_duration: float, cache_hit_rate: float
    ) -> str:
        """Calculate performance grade based on metrics"""
        score = 0

        if avg_duration < 1.0:
            score += 40
        elif avg_duration < 2.0:
            score += 30
        elif avg_duration < 5.0:
            score += 20
        else:
            score += 10

        score += int(cache_hit_rate * 60)

        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"

    def clear_cache(self) -> int:
        """Clear response cache"""
        cleared_count = len(self.cache.cache)
        self.cache.cache.clear()
        self.cache.access_times.clear()
        return cleared_count


# Global optimizer instance
response_optimizer = ResponseOptimizer()


def optimize_response(operation_type: str):
    """Decorator for optimizing agent responses"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            context = kwargs.get("context", {})
            if not context and args:
                for arg in args:
                    if isinstance(arg, dict) and ("page" in arg or "page_data" in arg):
                        context = arg
                        break

            return await response_optimizer.optimize_agent_response(
                operation_type, context, lambda ctx: func(*args, **kwargs)
            )

        return wrapper

    return decorator


def get_performance_metrics():
    """Get current performance metrics"""
    return response_optimizer.get_performance_summary()


def clear_response_cache():
    """Clear the response cache"""
    return response_optimizer.clear_cache()
