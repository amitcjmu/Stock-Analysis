"""
Flow Processing Base Classes
Core classes and shared utilities for flow processing
"""

import logging
import asyncio
from typing import Any, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class FlowProcessingMetrics:
    """Track performance metrics for flow processing with thread-safe async operations"""

    def __init__(self):
        self.fast_path_count = 0
        self.ai_path_count = 0
        self.simple_logic_count = 0
        self.error_count = 0
        self.execution_times: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()  # Add async lock for thread safety

    async def record_fast_path(self, execution_time: float):
        async with self._lock:
            self.fast_path_count += 1
            self.execution_times["fast_path"].append(execution_time)

    async def record_ai_path(self, execution_time: float):
        async with self._lock:
            self.ai_path_count += 1
            self.execution_times["ai_path"].append(execution_time)

    async def record_simple_logic(self, execution_time: float):
        async with self._lock:
            self.simple_logic_count += 1
            self.execution_times["simple_logic"].append(execution_time)

    async def record_error(self, execution_time: float):
        async with self._lock:
            self.error_count += 1
            self.execution_times["errors"].append(execution_time)

    async def get_p95(self, path_type: str) -> float:
        """Get P95 latency for a given path type"""
        async with self._lock:
            times = sorted(self.execution_times.get(path_type, []))
        if not times:
            return 0.0
        idx = int(len(times) * 0.95)
        return times[min(idx, len(times) - 1)]

    async def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        async with self._lock:
            total = self.fast_path_count + self.ai_path_count + self.simple_logic_count
            fast_path_count = self.fast_path_count
            simple_logic_count = self.simple_logic_count
            ai_path_count = self.ai_path_count
            error_count = self.error_count
            fast_path_times = list(self.execution_times["fast_path"])
            simple_logic_times = list(self.execution_times["simple_logic"])
            ai_path_times = list(self.execution_times["ai_path"])

        # Calculate p95 values outside the lock
        fast_p95 = await self.get_p95("fast_path")
        simple_p95 = await self.get_p95("simple_logic")
        ai_p95 = await self.get_p95("ai_path")

        return {
            "total_requests": total,
            "fast_path": {
                "count": fast_path_count,
                "percentage": (fast_path_count / total * 100) if total > 0 else 0,
                "p95_latency": fast_p95,
                "avg_latency": (
                    sum(fast_path_times) / len(fast_path_times)
                    if fast_path_times
                    else 0
                ),
            },
            "simple_logic": {
                "count": simple_logic_count,
                "percentage": ((simple_logic_count / total * 100) if total > 0 else 0),
                "p95_latency": simple_p95,
                "avg_latency": (
                    sum(simple_logic_times) / len(simple_logic_times)
                    if simple_logic_times
                    else 0
                ),
            },
            "ai_path": {
                "count": ai_path_count,
                "percentage": (ai_path_count / total * 100) if total > 0 else 0,
                "p95_latency": ai_p95,
                "avg_latency": (
                    sum(ai_path_times) / len(ai_path_times) if ai_path_times else 0
                ),
            },
            "errors": error_count,
        }


# Import availability flags for agents
try:
    import app.services.persistent_agents.tenant_scoped_agent_pool  # noqa: F401

    TENANT_AGENT_POOL_AVAILABLE = True
except ImportError:
    TENANT_AGENT_POOL_AVAILABLE = False

# Import the REAL single intelligent CrewAI agent
try:
    from app.services.agents.intelligent_flow_agent import (
        FlowIntelligenceResult,
        IntelligentFlowAgent,
    )

    INTELLIGENT_AGENT_AVAILABLE = True
    logger.info("✅ REAL Single Intelligent CrewAI Agent imported successfully")
except ImportError as e:
    INTELLIGENT_AGENT_AVAILABLE = False
    logger.error(f"❌ Failed to import intelligent agent: {e}")

    # Fallback classes
    class FlowIntelligenceResult:
        def __init__(self, **kwargs):
            from app.core.security.cache_encryption import secure_setattr

            for key, value in kwargs.items():
                secure_setattr(self, key, value)

    class IntelligentFlowAgent:
        async def analyze_flow_continuation(self, flow_id: str, **kwargs):
            return FlowIntelligenceResult(
                success=False,
                flow_id=flow_id,
                flow_type="discovery",
                current_phase="data_import",
                routing_decision="/discovery/overview",
                user_guidance="Intelligent agent not available",
                reasoning="Agent import failed",
                confidence=0.0,
            )
