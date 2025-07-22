"""
Progress Monitor

Monitors collection progress across all platforms with real-time metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.context import get_current_context
from app.core.database_context import get_context_db
from app.services.collection_flow.state_management import CollectionFlowStateService
from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .base import BaseCollectionTool

logger = logging.getLogger(__name__)


class ProgressMonitor(AsyncBaseDiscoveryTool, BaseCollectionTool):
    """Monitors collection progress across all platforms"""
    
    name: str = "ProgressMonitor"
    description: str = "Track and report collection progress in real-time"
    
    def __init__(self):
        super().__init__()
        self.name = "ProgressMonitor"
    
    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="ProgressMonitor",
            description="Monitors collection progress and performance metrics",
            tool_class=cls,
            categories=["collection", "monitoring", "metrics"],
            required_params=["flow_id"],
            optional_params=["metrics_type", "platform_filter"],
            context_aware=True,
            async_tool=True
        )
    
    async def arun(
        self,
        flow_id: str,
        metrics_type: str = "summary",
        platform_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Monitor collection progress.
        
        Args:
            flow_id: Collection flow ID
            metrics_type: Type of metrics (summary, detailed, realtime)
            platform_filter: Filter metrics by specific platforms
            
        Returns:
            Progress metrics and status
        """
        context = get_current_context()
        
        try:
            async with get_context_db() as db:
                state_service = CollectionFlowStateService(db, context)
                
                # Get current flow state
                flow_state = await state_service.get_flow_state(flow_id)
                
                if not flow_state:
                    return {"error": "Flow not found", "flow_id": flow_id}
                
                progress = await self._build_progress_report(
                    flow_id, flow_state, metrics_type, platform_filter
                )
                
                # Add alerts and recommendations
                self._add_progress_alerts(progress, flow_state)
                
                return progress
                
        except Exception as e:
            logger.error(f"Progress monitoring failed: {str(e)}")
            return {
                "error": str(e),
                "flow_id": flow_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _build_progress_report(
        self,
        flow_id: str,
        flow_state: Dict[str, Any],
        metrics_type: str,
        platform_filter: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Build comprehensive progress report"""
        
        progress = {
            "flow_id": flow_id,
            "overall_status": flow_state.get("status"),
            "started_at": flow_state.get("started_at"),
            "updated_at": flow_state.get("updated_at"),
            "automation_tier": flow_state.get("automation_tier")
        }
        
        # Get phase progress
        phases = flow_state.get("phases", {})
        phase_metrics = []
        
        for phase_name, phase_data in phases.items():
            if platform_filter and phase_name not in platform_filter:
                continue
            
            phase_metric = self._build_phase_metrics(phase_name, phase_data, metrics_type)
            phase_metrics.append(phase_metric)
        
        progress["phases"] = phase_metrics
        
        # Calculate overall progress
        progress["overall_progress"] = self._calculate_overall_progress(phase_metrics)
        
        # Add performance summary for detailed metrics
        if metrics_type in ["detailed", "realtime"]:
            progress["performance_summary"] = self._build_performance_summary(
                flow_state, phase_metrics
            )
        
        return progress
    
    def _build_phase_metrics(self, phase_name: str, phase_data: Dict[str, Any], metrics_type: str) -> Dict[str, Any]:
        """Build metrics for a single phase"""
        phase_metric = {
            "phase": phase_name,
            "status": phase_data.get("status"),
            "progress_percentage": phase_data.get("progress", 0),
            "items_collected": phase_data.get("items_collected", 0),
            "items_total": phase_data.get("items_total", 0),
            "quality_score": phase_data.get("quality_score"),
            "errors": phase_data.get("errors", [])
        }
        
        # Add performance details for detailed/realtime metrics
        if metrics_type in ["detailed", "realtime"]:
            phase_metric["performance"] = {
                "collection_rate": phase_data.get("collection_rate", 0),
                "avg_response_time": phase_data.get("avg_response_time", 0),
                "memory_usage": phase_data.get("memory_usage", 0),
                "cpu_usage": phase_data.get("cpu_usage", 0)
            }
        
        return phase_metric
    
    def _calculate_overall_progress(self, phase_metrics: List[Dict[str, Any]]) -> float:
        """Calculate overall progress percentage"""
        total_items = sum(p.get("items_total", 0) for p in phase_metrics)
        collected_items = sum(p.get("items_collected", 0) for p in phase_metrics)
        return (collected_items / total_items * 100) if total_items > 0 else 0
    
    def _build_performance_summary(self, flow_state: Dict[str, Any], phase_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build performance summary"""
        total_items = sum(p.get("items_total", 0) for p in phase_metrics)
        collected_items = sum(p.get("items_collected", 0) for p in phase_metrics)
        
        return {
            "total_items_collected": collected_items,
            "total_items_expected": total_items,
            "collection_efficiency": self._calculate_efficiency(phase_metrics),
            "estimated_completion": self._estimate_completion(flow_state, phase_metrics)
        }
    
    def _calculate_efficiency(self, phase_metrics: List[Dict[str, Any]]) -> float:
        """Calculate collection efficiency"""
        total_expected = sum(p.get("items_total", 0) for p in phase_metrics)
        total_collected = sum(p.get("items_collected", 0) for p in phase_metrics)
        
        if total_expected == 0:
            return 0.0
        
        # Factor in quality scores
        quality_weighted_collected = sum(
            p.get("items_collected", 0) * p.get("quality_score", 1.0)
            for p in phase_metrics
        )
        
        return quality_weighted_collected / total_expected
    
    def _estimate_completion(self, flow_state: Dict[str, Any], phase_metrics: List[Dict[str, Any]]) -> Optional[str]:
        """Estimate completion time based on current progress"""
        started_at = flow_state.get("started_at")
        if not started_at:
            return None
        
        try:
            start_time = datetime.fromisoformat(started_at) if isinstance(started_at, str) else started_at
            elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            total_items = sum(p.get("items_total", 0) for p in phase_metrics)
            collected_items = sum(p.get("items_collected", 0) for p in phase_metrics)
            
            if collected_items == 0 or collected_items >= total_items:
                return None
            
            rate = collected_items / elapsed_seconds
            remaining_items = total_items - collected_items
            estimated_seconds = remaining_items / rate
            
            estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)
            return estimated_completion.isoformat()
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not estimate completion time: {e}")
            return None
    
    def _add_progress_alerts(self, progress: Dict[str, Any], flow_state: Dict[str, Any]):
        """Add alerts for issues or anomalies"""
        alerts = []
        phase_metrics = progress.get("phases", [])
        
        for phase in phase_metrics:
            # Error alerts
            if phase.get("errors"):
                alerts.append({
                    "phase": phase["phase"],
                    "type": "error",
                    "severity": "high",
                    "message": f"{len(phase['errors'])} errors in {phase['phase']}"
                })
            
            # Quality alerts
            quality_score = phase.get("quality_score", 1.0)
            if quality_score and quality_score < 0.7:
                alerts.append({
                    "phase": phase["phase"],
                    "type": "quality",
                    "severity": "medium",
                    "message": f"Low quality score in {phase['phase']}: {quality_score:.1%}"
                })
            
            # Stalled progress alerts
            progress_pct = phase.get("progress_percentage", 0)
            if progress_pct > 0 and progress_pct < 100:
                # Check if phase has been stalled (would need more sophisticated tracking)
                status = phase.get("status", "")
                if status == "running" and progress_pct < 50:  # Simplified check
                    alerts.append({
                        "phase": phase["phase"],
                        "type": "progress",
                        "severity": "low", 
                        "message": f"Progress appears stalled in {phase['phase']}: {progress_pct:.1%}"
                    })
        
        progress["alerts"] = alerts