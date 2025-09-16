"""
Storage and persistence logic for performance metrics collection.

This module handles metric storage, cleanup, and performance monitoring
for the metrics collection system itself. Provides thread-safe operations
and background cleanup functionality.
"""

import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict

from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsStorage:
    """Handles metrics storage and cleanup operations"""

    def __init__(self, max_samples: int = 10000, cleanup_interval: int = 300):
        self.max_samples = max_samples
        self.cleanup_interval = cleanup_interval

        # Thread-safe access
        self._lock = threading.Lock()

        # Background cleanup
        self._cleanup_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="metrics-cleanup"
        )
        self._last_cleanup = time.time()

        # Performance tracking
        self._collection_times = deque(maxlen=1000)

        logger.info("MetricsStorage initialized with max_samples=%d", max_samples)

    def cleanup_old_metrics(self) -> None:
        """Clean up old metric samples to prevent memory growth"""
        if time.time() - self._last_cleanup < self.cleanup_interval:
            return

        start_time = time.time()

        # This is a placeholder for metric cleanup logic
        # In a production system, you might want to:
        # 1. Remove old samples beyond retention period
        # 2. Aggregate old data into larger time buckets
        # 3. Export old data to external storage

        cleanup_duration = time.time() - start_time
        self._collection_times.append(cleanup_duration)
        self._last_cleanup = time.time()

        logger.debug("Metrics cleanup completed in %.3fs", cleanup_duration)

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage performance statistics"""
        return {
            "collection_performance": {
                "average_cleanup_time_ms": (
                    sum(self._collection_times) / len(self._collection_times) * 1000
                    if self._collection_times
                    else 0
                ),
                "last_cleanup": datetime.fromtimestamp(self._last_cleanup).isoformat(),
            },
        }
