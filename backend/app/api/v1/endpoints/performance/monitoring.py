"""
Performance Monitoring API Endpoints
Implements Task 4.3 of the Discovery Flow Redesign.
Provides API endpoints for performance monitoring and optimization metrics.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

try:
    from app.services.monitoring.performance_monitor import get_performance_dashboard
    from app.services.performance.response_optimizer import clear_response_cache, get_performance_metrics
    PERFORMANCE_SERVICES_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_SERVICES_AVAILABLE = False
    logging.warning(f"⚠️ Performance services not available: {e}")

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/dashboard")
async def get_performance_dashboard_endpoint() -> Dict[str, Any]:
    """Get comprehensive performance dashboard"""
    try:
        if not PERFORMANCE_SERVICES_AVAILABLE:
            return {
                "error": "Performance monitoring services not available",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "service_unavailable"
            }
        
        dashboard = get_performance_dashboard()
        
        # Add service status
        dashboard["service_status"] = {
            "response_optimizer": "active",
            "performance_monitor": "active",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        logger.info("📊 Performance dashboard requested")
        return dashboard
        
    except Exception as e:
        logger.error(f"❌ Error getting performance dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance dashboard: {str(e)}")

@router.get("/metrics/summary")
async def get_performance_metrics_summary() -> Dict[str, Any]:
    """Get performance metrics summary"""
    try:
        if not PERFORMANCE_SERVICES_AVAILABLE:
            return {
                "error": "Performance services not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get response optimizer metrics
        optimizer_metrics = get_performance_metrics()
        
        # Get performance monitor dashboard
        monitor_dashboard = get_performance_dashboard()
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "response_optimization": optimizer_metrics,
            "operation_monitoring": monitor_dashboard,
            "performance_insights": {
                "top_performing_operations": [],
                "bottlenecks_identified": [],
                "optimization_recommendations": []
            }
        }
        
        # Add optimization recommendations
        if isinstance(optimizer_metrics, dict):
            cache_hit_rate = optimizer_metrics.get("cache_hit_rate", 0)
            if cache_hit_rate < 0.3:
                summary["performance_insights"]["optimization_recommendations"].append({
                    "type": "caching",
                    "message": f"Low cache hit rate ({cache_hit_rate:.1%}). Consider increasing cache TTL.",
                    "priority": "medium"
                })
            
            avg_duration = optimizer_metrics.get("average_duration", 0)
            if avg_duration > 5.0:
                summary["performance_insights"]["optimization_recommendations"].append({
                    "type": "performance",
                    "message": f"High average response time ({avg_duration:.1f}s). Consider optimization.",
                    "priority": "high"
                })
        
        logger.info("📈 Performance metrics summary requested")
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/health")
async def get_performance_health() -> Dict[str, Any]:
    """Get performance monitoring health status"""
    try:
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "response_optimizer": "available" if PERFORMANCE_SERVICES_AVAILABLE else "unavailable",
                "performance_monitor": "available" if PERFORMANCE_SERVICES_AVAILABLE else "unavailable"
            },
            "status": "healthy" if PERFORMANCE_SERVICES_AVAILABLE else "degraded"
        }
        
        if PERFORMANCE_SERVICES_AVAILABLE:
            try:
                get_performance_metrics()
                monitor_dashboard = get_performance_dashboard()
                
                health_status["services"]["response_optimizer"] = "active"
                health_status["services"]["performance_monitor"] = "active"
                health_status["status"] = "healthy"
                
                # Add basic stats
                health_status["stats"] = {
                    "total_operations": monitor_dashboard.get("total_operations", 0),
                    "active_operations": monitor_dashboard.get("active_operations", 0),
                    "performance_grade": monitor_dashboard.get("performance_grade", "unknown")
                }
                
            except Exception as e:
                logger.warning(f"⚠️ Performance services partially available: {e}")
                health_status["status"] = "degraded"
                health_status["warning"] = str(e)
        
        logger.debug("🏥 Performance health check completed")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Error checking performance health: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }

@router.post("/cache/clear")
async def clear_performance_cache() -> Dict[str, Any]:
    """Clear performance cache"""
    try:
        if not PERFORMANCE_SERVICES_AVAILABLE:
            return {
                "error": "Performance services not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        cleared_count = clear_response_cache()
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_cleared": True,
            "items_cleared": cleared_count,
            "message": f"Successfully cleared {cleared_count} cache items"
        }
        
        logger.info(f"🧹 Performance cache cleared ({cleared_count} items)")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/insights")
async def get_performance_insights() -> Dict[str, Any]:
    """Get AI-powered performance insights and recommendations"""
    try:
        if not PERFORMANCE_SERVICES_AVAILABLE:
            return {
                "error": "Performance services not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get current metrics
        optimizer_metrics = get_performance_metrics()
        get_performance_dashboard()
        
        insights = {
            "timestamp": datetime.utcnow().isoformat(),
            "performance_insights": [],
            "optimization_opportunities": [],
            "system_recommendations": []
        }
        
        # Analyze optimizer metrics
        if isinstance(optimizer_metrics, dict):
            cache_hit_rate = optimizer_metrics.get("cache_hit_rate", 0)
            avg_duration = optimizer_metrics.get("average_duration", 0)
            
            # Cache performance insights
            if cache_hit_rate > 0.8:
                insights["performance_insights"].append({
                    "type": "cache_performance",
                    "level": "excellent",
                    "message": f"Excellent cache performance with {cache_hit_rate:.1%} hit rate"
                })
            elif cache_hit_rate < 0.3:
                insights["optimization_opportunities"].append({
                    "type": "caching",
                    "priority": "high",
                    "message": f"Low cache hit rate ({cache_hit_rate:.1%}). Consider cache optimization."
                })
            
            # Response time insights
            if avg_duration < 1.0:
                insights["performance_insights"].append({
                    "type": "response_time",
                    "level": "excellent",
                    "message": f"Excellent response times averaging {avg_duration:.2f}s"
                })
            elif avg_duration > 5.0:
                insights["optimization_opportunities"].append({
                    "type": "response_time",
                    "priority": "high",
                    "message": f"High response times averaging {avg_duration:.2f}s"
                })
        
        # Add general recommendations
        insights["system_recommendations"].extend([
            {
                "type": "monitoring",
                "priority": "low",
                "message": "Continue monitoring performance metrics regularly"
            },
            {
                "type": "optimization",
                "priority": "medium",
                "message": "Consider implementing performance budgets"
            }
        ])
        
        logger.info("🔍 Performance insights generated")
        return insights
        
    except Exception as e:
        logger.error(f"❌ Error generating performance insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}") 