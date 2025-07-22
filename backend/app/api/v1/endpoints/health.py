"""
Health check endpoints for the application.
"""
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from app.core.database import db_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("")
async def health_check() -> Dict[str, Any]:
    """
    🏥 ENHANCED: Health check endpoint with database performance monitoring.
    """
    start_time = datetime.utcnow()
    
    # Basic health status
    health_status = {
        "status": "healthy",
        "timestamp": start_time.isoformat(),
        "service": "migration_platform_optimized",
        "version": "2.1.0"
    }
    
    # Database health check
    try:
        db_healthy = await db_manager.health_check()
        health_status["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "performance_metrics": db_manager.get_performance_metrics()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Performance metrics
    response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    health_status["performance"] = {
        "health_check_response_time_ms": response_time,
        "optimizations_active": [
            "database_connection_pooling",
            "query_timeouts",
            "response_caching",
            "fast_path_routing"
        ]
    }
    
    return health_status

@router.get("/database")
async def database_health_detailed() -> Dict[str, Any]:
    """
    🎯 PERFORMANCE: Detailed database health and performance metrics.
    """
    try:
        start_time = datetime.utcnow()
        
        # Perform database health check
        db_healthy = await db_manager.health_check()
        
        # Get detailed performance metrics
        metrics = db_manager.get_performance_metrics()
        
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "database_status": "healthy" if db_healthy else "unhealthy",
            "health_check_time_ms": response_time,
            "connection_health": metrics.get("connection_health", {}),
            "pool_status": metrics.get("pool_status", {}),
            "engine_type": metrics.get("engine_type", "Unknown"),
            "recommendations": _get_performance_recommendations(metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Detailed database health check failed: {e}")
        return {
            "database_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def _get_performance_recommendations(metrics: Dict[str, Any]) -> list:
    """Generate performance recommendations based on metrics."""
    recommendations = []
    
    connection_health = metrics.get("connection_health", {})
    
    # Check success rate
    success_rate = connection_health.get("success_rate", 1.0)
    if success_rate < 0.95:
        recommendations.append({
            "issue": "Low database connection success rate",
            "current_value": f"{success_rate:.2%}",
            "recommendation": "Check database connectivity and increase connection timeout",
            "priority": "high"
        })
    
    # Check response time
    avg_response_time = connection_health.get("avg_response_time_ms", 0)
    if avg_response_time > 1000:
        recommendations.append({
            "issue": "High database response time",
            "current_value": f"{avg_response_time:.1f}ms",
            "recommendation": "Consider database query optimization or connection pool tuning",
            "priority": "medium"
        })
    
    # Check failed connections
    failed_connections = connection_health.get("failed_connections", 0)
    if failed_connections > 5:
        recommendations.append({
            "issue": "Multiple failed database connections",
            "current_value": f"{failed_connections} failures",
            "recommendation": "Monitor database stability and check connection configuration",
            "priority": "medium"
        })
    
    if not recommendations:
        recommendations.append({
            "status": "optimal",
            "message": "Database performance is optimal",
            "priority": "info"
        })
    
    return recommendations 