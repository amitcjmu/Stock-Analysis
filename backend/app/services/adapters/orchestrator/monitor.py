"""Resource monitoring for adapter orchestration"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List


class ResourceMonitor:
    """Monitor system resources during adapter execution"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")
        self._monitoring = False
        self._metrics_history: List[Dict[str, Any]] = []

    async def start_monitoring(self):
        """Start resource monitoring"""
        self._monitoring = True
        self._metrics_history = []

    async def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return summary"""
        self._monitoring = False

        if not self._metrics_history:
            return {}

        return {
            "peak_memory_mb": max(
                m.get("memory_usage_mb", 0) for m in self._metrics_history
            ),
            "peak_cpu_percent": max(
                m.get("cpu_usage_percent", 0) for m in self._metrics_history
            ),
            "avg_memory_mb": sum(
                m.get("memory_usage_mb", 0) for m in self._metrics_history
            )
            / len(self._metrics_history),
            "avg_cpu_percent": sum(
                m.get("cpu_usage_percent", 0) for m in self._metrics_history
            )
            / len(self._metrics_history),
            "sample_count": len(self._metrics_history),
        }

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            import psutil

            # Get process info
            process = psutil.Process()

            # CPU percent with interval for accurate measurement
            # First call to cpu_percent() starts the measurement
            process.cpu_percent()
            # Wait a small interval for accurate measurement
            await asyncio.sleep(0.1)

            metrics = {
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_usage_percent": process.cpu_percent(),  # Second call returns actual usage
                "available_disk_mb": psutil.disk_usage("/").free / 1024 / 1024,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if self._monitoring:
                self._metrics_history.append(metrics)

            return metrics

        except ImportError:
            # psutil not available, return empty metrics
            return {}
        except Exception as e:
            self.logger.warning(f"Failed to get system metrics: {str(e)}")
            return {}
