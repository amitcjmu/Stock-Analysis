"""
Performance tracker for agent service layer metrics and monitoring.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Tracks performance metrics for agent service layer operations."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics = {
            "calls_made": 0,
            "errors": 0,
            "total_time": 0.0,
            "last_error": None,
            "start_time": time.time()
        }
        
        # Detailed tracking
        self._call_history = deque(maxlen=max_history)
        self._method_stats = defaultdict(lambda: {
            "calls": 0,
            "errors": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "last_call": None
        })
        self._error_patterns = defaultdict(int)
        self._hourly_stats = defaultdict(lambda: {"calls": 0, "errors": 0, "total_time": 0.0})
    
    def log_call(self, method_name: str, duration: float, success: bool, error: Optional[str] = None):
        """Log a service call with performance metrics"""
        timestamp = datetime.utcnow()
        
        # Update global metrics
        self._metrics["calls_made"] += 1
        self._metrics["total_time"] += duration
        
        if not success:
            self._metrics["errors"] += 1
            self._metrics["last_error"] = {
                "method": method_name,
                "error": error,
                "timestamp": timestamp.isoformat()
            }
        
        # Update method-specific stats
        method_stats = self._method_stats[method_name]
        method_stats["calls"] += 1
        method_stats["total_time"] += duration
        method_stats["avg_time"] = method_stats["total_time"] / method_stats["calls"]
        method_stats["min_time"] = min(method_stats["min_time"], duration)
        method_stats["max_time"] = max(method_stats["max_time"], duration)
        method_stats["last_call"] = timestamp.isoformat()
        
        if not success:
            method_stats["errors"] += 1
            
            # Track error patterns
            if error:
                error_type = self._categorize_error(error)
                self._error_patterns[error_type] += 1
        
        # Update hourly stats
        hour_key = timestamp.strftime("%Y-%m-%d-%H")
        hourly_stat = self._hourly_stats[hour_key]
        hourly_stat["calls"] += 1
        hourly_stat["total_time"] += duration
        if not success:
            hourly_stat["errors"] += 1
        
        # Add to call history
        call_record = {
            "timestamp": timestamp.isoformat(),
            "method": method_name,
            "duration": duration,
            "success": success,
            "error": error
        }
        self._call_history.append(call_record)
        
        # Log the call
        logger.info(f"AgentService.{method_name}", extra={
            "duration_ms": duration * 1000,
            "success": success,
            "error": error,
            "call_count": self._metrics["calls_made"]
        })
    
    def get_metrics(self, context: RequestContext) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        current_time = time.time()
        uptime = current_time - self._metrics["start_time"]
        
        # Calculate overall stats
        avg_time = self._metrics["total_time"] / max(self._metrics["calls_made"], 1)
        error_rate = self._metrics["errors"] / max(self._metrics["calls_made"], 1)
        calls_per_second = self._metrics["calls_made"] / max(uptime, 1)
        
        # Get recent performance (last 100 calls)
        recent_calls = list(self._call_history)[-100:] if self._call_history else []
        recent_performance = self._analyze_recent_performance(recent_calls)
        
        # Get top slow methods
        slow_methods = self._get_slow_methods()
        
        # Get error analysis
        error_analysis = self._analyze_errors()
        
        return {
            "overview": {
                "calls_made": self._metrics["calls_made"],
                "errors": self._metrics["errors"],
                "error_rate": round(error_rate, 4),
                "avg_response_time": round(avg_time, 4),
                "calls_per_second": round(calls_per_second, 2),
                "uptime_seconds": round(uptime, 2)
            },
            "context": {
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(context.engagement_id),
                "user_id": str(context.user_id) if context.user_id else None
            },
            "recent_performance": recent_performance,
            "method_statistics": dict(self._method_stats),
            "slow_methods": slow_methods,
            "error_analysis": error_analysis,
            "last_error": self._metrics["last_error"],
            "hourly_trends": self._get_hourly_trends()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status based on performance metrics"""
        if self._metrics["calls_made"] == 0:
            return {
                "status": "unknown",
                "message": "No calls made yet",
                "indicators": {}
            }
        
        # Calculate health indicators
        error_rate = self._metrics["errors"] / self._metrics["calls_made"]
        avg_time = self._metrics["total_time"] / self._metrics["calls_made"]
        
        # Recent calls analysis
        recent_calls = list(self._call_history)[-50:] if self._call_history else []
        recent_error_rate = sum(1 for call in recent_calls if not call["success"]) / max(len(recent_calls), 1)
        recent_avg_time = sum(call["duration"] for call in recent_calls) / max(len(recent_calls), 1)
        
        # Health thresholds
        health_indicators = {
            "error_rate": {
                "value": round(error_rate, 4),
                "recent_value": round(recent_error_rate, 4),
                "status": "healthy" if error_rate < 0.05 else ("warning" if error_rate < 0.15 else "critical"),
                "threshold": 0.05
            },
            "response_time": {
                "value": round(avg_time, 4),
                "recent_value": round(recent_avg_time, 4),
                "status": "healthy" if avg_time < 1.0 else ("warning" if avg_time < 3.0 else "critical"),
                "threshold": 1.0
            },
            "call_volume": {
                "value": self._metrics["calls_made"],
                "status": "healthy" if self._metrics["calls_made"] > 0 else "unknown"
            }
        }
        
        # Overall status
        statuses = [indicator["status"] for indicator in health_indicators.values() if "status" in indicator]
        if "critical" in statuses:
            overall_status = "critical"
        elif "warning" in statuses:
            overall_status = "warning"
        elif "healthy" in statuses:
            overall_status = "healthy"
        else:
            overall_status = "unknown"
        
        return {
            "status": overall_status,
            "message": self._get_health_message(overall_status),
            "indicators": health_indicators,
            "recommendations": self._get_health_recommendations(health_indicators)
        }
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        self._metrics = {
            "calls_made": 0,
            "errors": 0,
            "total_time": 0.0,
            "last_error": None,
            "start_time": time.time()
        }
        self._call_history.clear()
        self._method_stats.clear()
        self._error_patterns.clear()
        self._hourly_stats.clear()
    
    def get_method_performance(self, method_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific method"""
        if method_name not in self._method_stats:
            return {
                "method": method_name,
                "status": "no_data",
                "message": "No performance data available for this method"
            }
        
        stats = self._method_stats[method_name]
        error_rate = stats["errors"] / max(stats["calls"], 1)
        
        return {
            "method": method_name,
            "calls": stats["calls"],
            "errors": stats["errors"],
            "error_rate": round(error_rate, 4),
            "avg_time": round(stats["avg_time"], 4),
            "min_time": round(stats["min_time"], 4) if stats["min_time"] != float('inf') else 0,
            "max_time": round(stats["max_time"], 4),
            "total_time": round(stats["total_time"], 4),
            "last_call": stats["last_call"]
        }
    
    def _categorize_error(self, error: str) -> str:
        """Categorize error for pattern analysis"""
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "not found" in error_lower:
            return "not_found"
        elif "permission" in error_lower or "access" in error_lower:
            return "permission"
        elif "validation" in error_lower:
            return "validation"
        elif "database" in error_lower or "connection" in error_lower:
            return "database"
        else:
            return "other"
    
    def _analyze_recent_performance(self, recent_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance of recent calls"""
        if not recent_calls:
            return {"status": "no_data", "message": "No recent calls to analyze"}
        
        successful_calls = [call for call in recent_calls if call["success"]]
        failed_calls = [call for call in recent_calls if not call["success"]]
        
        avg_duration = sum(call["duration"] for call in recent_calls) / len(recent_calls)
        success_rate = len(successful_calls) / len(recent_calls)
        
        return {
            "total_calls": len(recent_calls),
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "success_rate": round(success_rate, 4),
            "avg_duration": round(avg_duration, 4),
            "trend": self._determine_performance_trend(recent_calls)
        }
    
    def _get_slow_methods(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the slowest methods by average response time"""
        methods = []
        for method_name, stats in self._method_stats.items():
            if stats["calls"] >= 2:  # Only include methods with multiple calls
                methods.append({
                    "method": method_name,
                    "avg_time": round(stats["avg_time"], 4),
                    "max_time": round(stats["max_time"], 4),
                    "calls": stats["calls"]
                })
        
        return sorted(methods, key=lambda x: x["avg_time"], reverse=True)[:limit]
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns and trends"""
        total_errors = sum(self._error_patterns.values())
        
        if total_errors == 0:
            return {
                "total_errors": 0,
                "error_patterns": {},
                "most_common_error": None
            }
        
        # Convert to percentages
        error_percentages = {}
        for error_type, count in self._error_patterns.items():
            error_percentages[error_type] = {
                "count": count,
                "percentage": round((count / total_errors) * 100, 2)
            }
        
        # Find most common error
        most_common = max(self._error_patterns.items(), key=lambda x: x[1])
        
        return {
            "total_errors": total_errors,
            "error_patterns": error_percentages,
            "most_common_error": {
                "type": most_common[0],
                "count": most_common[1],
                "percentage": round((most_common[1] / total_errors) * 100, 2)
            }
        }
    
    def _get_hourly_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly performance trends"""
        current_time = datetime.utcnow()
        trends = []
        
        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y-%m-%d-%H")
            
            if hour_key in self._hourly_stats:
                stats = self._hourly_stats[hour_key]
                error_rate = stats["errors"] / max(stats["calls"], 1)
                avg_time = stats["total_time"] / max(stats["calls"], 1)
                
                trends.append({
                    "hour": hour_time.strftime("%Y-%m-%d %H:00"),
                    "calls": stats["calls"],
                    "errors": stats["errors"],
                    "error_rate": round(error_rate, 4),
                    "avg_time": round(avg_time, 4)
                })
            else:
                trends.append({
                    "hour": hour_time.strftime("%Y-%m-%d %H:00"),
                    "calls": 0,
                    "errors": 0,
                    "error_rate": 0.0,
                    "avg_time": 0.0
                })
        
        return sorted(trends, key=lambda x: x["hour"])
    
    def _determine_performance_trend(self, recent_calls: List[Dict[str, Any]]) -> str:
        """Determine if performance is improving, degrading, or stable"""
        if len(recent_calls) < 10:
            return "insufficient_data"
        
        # Split into first and second half
        mid_point = len(recent_calls) // 2
        first_half = recent_calls[:mid_point]
        second_half = recent_calls[mid_point:]
        
        # Calculate average response times
        first_avg = sum(call["duration"] for call in first_half) / len(first_half)
        second_avg = sum(call["duration"] for call in second_half) / len(second_half)
        
        # Calculate success rates
        first_success = sum(1 for call in first_half if call["success"]) / len(first_half)
        second_success = sum(1 for call in second_half if call["success"]) / len(second_half)
        
        # Determine trend
        time_improvement = second_avg < first_avg * 0.9  # 10% faster
        time_degradation = second_avg > first_avg * 1.1  # 10% slower
        success_improvement = second_success > first_success + 0.05  # 5% better
        success_degradation = second_success < first_success - 0.05  # 5% worse
        
        if time_improvement or success_improvement:
            return "improving"
        elif time_degradation or success_degradation:
            return "degrading"
        else:
            return "stable"
    
    def _get_health_message(self, status: str) -> str:
        """Get health status message"""
        messages = {
            "healthy": "Agent service layer is performing well",
            "warning": "Agent service layer has some performance issues",
            "critical": "Agent service layer has critical performance issues",
            "unknown": "Agent service layer status is unknown"
        }
        return messages.get(status, "Unknown status")
    
    def _get_health_recommendations(self, indicators: Dict[str, Any]) -> List[str]:
        """Get health improvement recommendations"""
        recommendations = []
        
        if indicators["error_rate"]["status"] in ["warning", "critical"]:
            recommendations.append("Investigate and resolve error patterns")
        
        if indicators["response_time"]["status"] in ["warning", "critical"]:
            recommendations.append("Optimize slow methods and database queries")
        
        if indicators["error_rate"]["recent_value"] > indicators["error_rate"]["value"]:
            recommendations.append("Recent error rate increase - check recent changes")
        
        if indicators["response_time"]["recent_value"] > indicators["response_time"]["value"]:
            recommendations.append("Recent performance degradation - investigate system load")
        
        return recommendations