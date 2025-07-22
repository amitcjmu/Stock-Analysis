"""
Health Monitoring Module
Team C1 - Task C1.6

Handles health checks, status monitoring, and health assessment.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

from .models import Alert
from .types import HealthStatus

logger = get_logger(__name__)


class HealthMonitor:
    """Monitors system and workflow health"""
    
    def __init__(self):
        self.health_status: Dict[str, HealthStatus] = {}
        
        # Configuration
        self.health_check_interval_ms = 30000  # 30 seconds
    
    async def get_health_status(
        self,
        workflow_id: Optional[str] = None,
        component_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get health status for workflows and components
        
        Args:
            workflow_id: Specific workflow ID (optional)
            component_filter: Filter by specific components
            
        Returns:
            Comprehensive health status information
        """
        try:
            logger.info(f"🏥 Getting health status for workflow: {workflow_id or 'all'}")
            
            # Get overall system health
            system_health = await self._assess_system_health()
            
            # Get workflow-specific health if requested
            workflow_health = {}
            if workflow_id:
                workflow_health = await self._assess_workflow_health(workflow_id)
            else:
                # Get health for all active workflows
                # This would iterate through active workflows
                workflow_health = await self._assess_all_workflow_health()
            
            # Get component health
            component_health = await self._assess_component_health(component_filter)
            
            # Get active alerts (would be passed from AlertManager)
            relevant_alerts = []  # Would be populated by AlertManager
            
            # Calculate overall health score
            overall_health = await self._calculate_overall_health_score(
                system_health=system_health,
                workflow_health=workflow_health,
                component_health=component_health,
                active_alerts=relevant_alerts
            )
            
            health_data = {
                "overall_health": overall_health,
                "system_health": system_health,
                "workflow_health": workflow_health,
                "component_health": component_health,
                "active_alerts": relevant_alerts,
                "health_trends": await self._calculate_health_trends(),
                "recommendations": await self._generate_health_recommendations(
                    overall_health=overall_health,
                    alerts=relevant_alerts
                ),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get health status: {e}")
            raise
    
    async def perform_health_checks(self):
        """Perform health checks on system components"""
        try:
            # Check database connectivity
            db_health = await self._check_database_health()
            self.health_status["database"] = db_health
            
            # Check external service connectivity
            services_health = await self._check_external_services_health()
            self.health_status.update(services_health)
            
            # Check system resources
            resource_health = await self._check_system_resources()
            self.health_status["resources"] = resource_health
            
            logger.debug("✅ Health checks completed")
            
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            self.health_status["system"] = HealthStatus.CRITICAL
    
    async def update_health_status(self):
        """Update overall health status"""
        try:
            # Aggregate all health statuses
            health_values = list(self.health_status.values())
            
            if not health_values:
                overall_status = HealthStatus.HEALTHY
            elif any(status == HealthStatus.CRITICAL for status in health_values):
                overall_status = HealthStatus.CRITICAL
            elif any(status == HealthStatus.UNHEALTHY for status in health_values):
                overall_status = HealthStatus.UNHEALTHY
            elif any(status == HealthStatus.DEGRADED for status in health_values):
                overall_status = HealthStatus.DEGRADED
            else:
                overall_status = HealthStatus.HEALTHY
            
            self.health_status["overall"] = overall_status
            
        except Exception as e:
            logger.error(f"❌ Health status update error: {e}")
    
    async def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health"""
        # Check various system components
        checks = {
            "database": await self._check_database_health(),
            "memory": await self._check_memory_health(),
            "disk": await self._check_disk_health(),
            "network": await self._check_network_health()
        }
        
        # Calculate overall system health score
        healthy_checks = sum(1 for status in checks.values() if status == HealthStatus.HEALTHY)
        health_score = healthy_checks / len(checks)
        
        return {
            "status": HealthStatus.HEALTHY if health_score > 0.8 else HealthStatus.DEGRADED,
            "score": health_score,
            "checks": {k: v.value for k, v in checks.items()},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _assess_workflow_health(self, workflow_id: str) -> Dict[str, Any]:
        """Assess workflow-specific health"""
        # Check workflow execution status
        execution_health = await self._check_workflow_execution_health(workflow_id)
        
        # Check workflow performance
        performance_health = await self._check_workflow_performance_health(workflow_id)
        
        # Check workflow resource usage
        resource_health = await self._check_workflow_resource_health(workflow_id)
        
        # Calculate overall workflow health
        health_checks = [execution_health, performance_health, resource_health]
        healthy_count = sum(1 for status in health_checks if status == HealthStatus.HEALTHY)
        health_score = healthy_count / len(health_checks)
        
        return {
            "workflow_id": workflow_id,
            "status": HealthStatus.HEALTHY if health_score > 0.8 else HealthStatus.DEGRADED,
            "score": health_score,
            "execution_health": execution_health.value,
            "performance_health": performance_health.value,
            "resource_health": resource_health.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _assess_all_workflow_health(self) -> Dict[str, Any]:
        """Assess health for all active workflows"""
        # This would iterate through all active workflows
        # For now, return a mock assessment
        return {
            "total_workflows": 3,
            "healthy_workflows": 2,
            "degraded_workflows": 1,
            "unhealthy_workflows": 0,
            "overall_score": 0.85
        }
    
    async def _assess_component_health(self, component_filter: Optional[List[str]]) -> Dict[str, Any]:
        """Assess component health"""
        components = {
            "orchestrator": HealthStatus.HEALTHY,
            "phase_engine": HealthStatus.HEALTHY,
            "tier_routing": HealthStatus.HEALTHY,
            "handoff_protocol": HealthStatus.HEALTHY,
            "recommendation_engine": HealthStatus.DEGRADED
        }
        
        # Filter components if specified
        if component_filter:
            components = {k: v for k, v in components.items() if k in component_filter}
        
        # Calculate component health score
        healthy_components = sum(1 for status in components.values() if status == HealthStatus.HEALTHY)
        health_score = healthy_components / len(components) if components else 1.0
        
        return {
            "components": {k: v.value for k, v in components.items()},
            "total_components": len(components),
            "healthy_components": healthy_components,
            "health_score": health_score,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _calculate_overall_health_score(
        self,
        system_health: Dict[str, Any],
        workflow_health: Dict[str, Any],
        component_health: Dict[str, Any],
        active_alerts: List[Alert]
    ) -> Dict[str, Any]:
        """Calculate overall health score"""
        # Weight different health aspects
        system_weight = 0.4
        workflow_weight = 0.3
        component_weight = 0.2
        alert_weight = 0.1
        
        # Get individual scores
        system_score = system_health.get("score", 1.0)
        workflow_score = workflow_health.get("score", workflow_health.get("overall_score", 1.0))
        component_score = component_health.get("health_score", 1.0)
        
        # Calculate alert impact (reduce score based on active alerts)
        alert_impact = min(0.2, len(active_alerts) * 0.05)  # Max 20% reduction
        alert_score = 1.0 - alert_impact
        
        # Calculate weighted overall score
        overall_score = (
            system_score * system_weight +
            workflow_score * workflow_weight +
            component_score * component_weight +
            alert_score * alert_weight
        )
        
        # Determine overall status
        if overall_score >= 0.9:
            status = "excellent"
        elif overall_score >= 0.8:
            status = "healthy"
        elif overall_score >= 0.6:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "score": overall_score,
            "status": status,
            "components_healthy": component_health.get("healthy_components", 0),
            "total_components": component_health.get("total_components", 0),
            "active_alerts": len(active_alerts),
            "breakdown": {
                "system": system_score,
                "workflow": workflow_score,
                "component": component_score,
                "alert_impact": alert_score
            }
        }
    
    async def _calculate_health_trends(self) -> Dict[str, Any]:
        """Calculate health trends"""
        # This would analyze historical health data
        return {
            "trend": "stable",
            "health_improving": True,
            "trend_period_hours": 24,
            "stability_score": 0.95
        }
    
    async def _generate_health_recommendations(
        self,
        overall_health: Dict[str, Any],
        alerts: List[Alert]
    ) -> List[str]:
        """Generate health recommendations"""
        recommendations = []
        
        health_score = overall_health.get("score", 1.0)
        
        if health_score < 0.8:
            recommendations.append("System health is below optimal - investigate degraded components")
        
        if len(alerts) > 5:
            recommendations.append("High number of active alerts - review and resolve critical issues")
        
        if health_score >= 0.9:
            recommendations.append("System is operating at optimal health")
        else:
            recommendations.append("Monitor system performance and address any emerging issues")
        
        return recommendations
    
    # Health check implementations
    
    async def _check_database_health(self) -> HealthStatus:
        """Check database connectivity and performance"""
        # Would implement actual database health check
        return HealthStatus.HEALTHY
    
    async def _check_memory_health(self) -> HealthStatus:
        """Check system memory usage"""
        # Would implement actual memory usage check
        return HealthStatus.HEALTHY
    
    async def _check_disk_health(self) -> HealthStatus:
        """Check disk space and I/O"""
        # Would implement actual disk health check
        return HealthStatus.HEALTHY
    
    async def _check_network_health(self) -> HealthStatus:
        """Check network connectivity"""
        # Would implement actual network health check
        return HealthStatus.HEALTHY
    
    async def _check_external_services_health(self) -> Dict[str, HealthStatus]:
        """Check external service connectivity"""
        # Would implement actual external service checks
        return {
            "authentication_service": HealthStatus.HEALTHY,
            "file_storage": HealthStatus.HEALTHY,
            "notification_service": HealthStatus.DEGRADED
        }
    
    async def _check_system_resources(self) -> HealthStatus:
        """Check overall system resource utilization"""
        # Would implement actual resource utilization check
        return HealthStatus.HEALTHY
    
    async def _check_workflow_execution_health(self, workflow_id: str) -> HealthStatus:
        """Check workflow execution health"""
        # Would implement actual workflow execution health check
        return HealthStatus.HEALTHY
    
    async def _check_workflow_performance_health(self, workflow_id: str) -> HealthStatus:
        """Check workflow performance health"""
        # Would implement actual workflow performance health check
        return HealthStatus.HEALTHY
    
    async def _check_workflow_resource_health(self, workflow_id: str) -> HealthStatus:
        """Check workflow resource usage health"""
        # Would implement actual workflow resource health check
        return HealthStatus.HEALTHY