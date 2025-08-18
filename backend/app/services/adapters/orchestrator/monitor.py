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

            # Offload CPU measurement to thread to avoid blocking event loop
            loop = asyncio.get_running_loop()

            def _collect_metrics():
                """Collect metrics in thread to avoid blocking"""
                proc = psutil.Process()
                # System-wide CPU over a short interval for stability
                system_cpu = psutil.cpu_percent(interval=0.2)
                # Process CPU percent (system interval already elapsed)
                proc_cpu = proc.cpu_percent(interval=None)
                return {
                    "memory_usage_mb": proc.memory_info().rss / 1024 / 1024,
                    "cpu_usage_percent": max(
                        proc_cpu, system_cpu
                    ),  # Use higher of process or system
                    "available_disk_mb": psutil.disk_usage("/").free / 1024 / 1024,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Run metrics collection in thread executor
            metrics = await loop.run_in_executor(None, _collect_metrics)

            if self._monitoring:
                self._metrics_history.append(metrics)

            return metrics

        except ImportError:
            # psutil not available, return empty metrics
            return {}
        except Exception as e:
            self.logger.warning(f"Failed to get system metrics: {str(e)}")
            return {}
