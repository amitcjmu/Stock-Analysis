"""
Adapter Management Service

This module provides centralized management, monitoring, and optimization
for all platform adapters in the ADCS system.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from app.services.collection_flow.adapters import CollectionRequest, CollectionResponse

from .enhanced_base_adapter import AdapterConfiguration, EnhancedBaseAdapter
from .performance_monitor import PerformanceMonitor


class AdapterStatus(str, Enum):
    """Adapter status states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


@dataclass
class AdapterInfo:
    """Information about a registered adapter"""
    adapter_id: str
    adapter_class: Type[EnhancedBaseAdapter]
    configuration: AdapterConfiguration
    instance: Optional[EnhancedBaseAdapter] = None
    status: AdapterStatus = AdapterStatus.OFFLINE
    last_health_check: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0


class AdapterManager:
    """
    Centralized manager for all platform adapters
    
    Provides:
    - Adapter registration and lifecycle management
    - Health monitoring and status tracking
    - Performance optimization coordination
    - Load balancing and request routing
    - Comprehensive reporting and analytics
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AdapterManager")
        
        # Adapter registry
        self._adapters: Dict[str, AdapterInfo] = {}
        self._adapter_instances: Dict[str, EnhancedBaseAdapter] = {}
        
        # Global performance monitoring
        self._global_performance_monitor = PerformanceMonitor()
        
        # Health monitoring
        self._health_check_interval = 300  # 5 minutes
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Optimization
        self._optimization_interval = 3600  # 1 hour
        self._optimization_task: Optional[asyncio.Task] = None
        
        # Request routing
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: List[asyncio.Task] = []
        
    async def register_adapter(
        self,
        adapter_id: str,
        adapter_class: Type[EnhancedBaseAdapter],
        configuration: AdapterConfiguration
    ) -> bool:
        """
        Register a new adapter with the manager
        
        Args:
            adapter_id: Unique identifier for the adapter
            adapter_class: Adapter class to instantiate
            configuration: Adapter configuration
            
        Returns:
            True if registration successful
        """
        try:
            if adapter_id in self._adapters:
                self.logger.warning(f"Adapter {adapter_id} already registered, updating configuration")
                
            adapter_info = AdapterInfo(
                adapter_id=adapter_id,
                adapter_class=adapter_class,
                configuration=configuration
            )
            
            self._adapters[adapter_id] = adapter_info
            self.logger.info(f"Registered adapter: {adapter_id} for platform {configuration.platform}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register adapter {adapter_id}: {str(e)}")
            return False
            
    async def start_adapter(self, adapter_id: str) -> bool:
        """Start an adapter instance"""
        if adapter_id not in self._adapters:
            self.logger.error(f"Adapter {adapter_id} not registered")
            return False
            
        adapter_info = self._adapters[adapter_id]
        
        try:
            # Create adapter instance
            instance = adapter_info.adapter_class(adapter_info.configuration)
            adapter_info.instance = instance
            adapter_info.status = AdapterStatus.HEALTHY
            
            self._adapter_instances[adapter_id] = instance
            
            self.logger.info(f"Started adapter: {adapter_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start adapter {adapter_id}: {str(e)}")
            adapter_info.status = AdapterStatus.OFFLINE
            return False
            
    async def stop_adapter(self, adapter_id: str) -> bool:
        """Stop an adapter instance"""
        if adapter_id not in self._adapters:
            return False
            
        adapter_info = self._adapters[adapter_id]
        adapter_info.status = AdapterStatus.OFFLINE
        adapter_info.instance = None
        
        if adapter_id in self._adapter_instances:
            del self._adapter_instances[adapter_id]
            
        self.logger.info(f"Stopped adapter: {adapter_id}")
        return True
        
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        if not self._health_check_task:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
        if not self._optimization_task:
            self._optimization_task = asyncio.create_task(self._optimization_loop())
            
        # Start request workers
        for i in range(5):  # 5 worker tasks
            worker = asyncio.create_task(self._request_worker(f"worker_{i}"))
            self._worker_tasks.append(worker)
            
        self.logger.info("Started adapter monitoring and optimization")
        
    async def stop_monitoring(self):
        """Stop background monitoring tasks"""
        if self._health_check_task:
            self._health_check_task.cancel()
            self._health_check_task = None
            
        if self._optimization_task:
            self._optimization_task.cancel()
            self._optimization_task = None
            
        for worker in self._worker_tasks:
            worker.cancel()
        self._worker_tasks.clear()
        
        self.logger.info("Stopped adapter monitoring and optimization")
        
    async def execute_collection_request(
        self,
        request: CollectionRequest,
        preferred_adapter_id: Optional[str] = None
    ) -> CollectionResponse:
        """
        Execute a data collection request through the optimal adapter
        
        Args:
            request: Collection request to execute
            preferred_adapter_id: Preferred adapter to use (optional)
            
        Returns:
            Collection response
        """
        # Find suitable adapter
        adapter_id = await self._select_adapter(request, preferred_adapter_id)
        
        if not adapter_id:
            return CollectionResponse(
                success=False,
                error_message="No suitable adapter available",
                error_details={"platform": request.platform}
            )
            
        # Get adapter instance
        adapter = self._adapter_instances.get(adapter_id)
        if not adapter:
            return CollectionResponse(
                success=False,
                error_message=f"Adapter {adapter_id} not available",
                error_details={"adapter_id": adapter_id}
            )
            
        # Execute request
        adapter_info = self._adapters[adapter_id]
        adapter_info.total_requests += 1
        
        try:
            response = await adapter.collect_data(request)
            
            if response.success:
                adapter_info.successful_requests += 1
            else:
                adapter_info.failed_requests += 1
                
            return response
            
        except Exception as e:
            adapter_info.failed_requests += 1
            self.logger.error(f"Request failed in adapter {adapter_id}: {str(e)}")
            
            return CollectionResponse(
                success=False,
                error_message=str(e),
                error_details={
                    "adapter_id": adapter_id,
                    "exception_type": type(e).__name__
                }
            )
            
    async def get_adapter_status(self, adapter_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of one or all adapters"""
        if adapter_id:
            if adapter_id not in self._adapters:
                return {"error": "Adapter not found"}
                
            adapter_info = self._adapters[adapter_id]
            instance = adapter_info.instance
            
            status_data = {
                "adapter_id": adapter_id,
                "platform": adapter_info.configuration.platform,
                "status": adapter_info.status.value,
                "total_requests": adapter_info.total_requests,
                "successful_requests": adapter_info.successful_requests,
                "failed_requests": adapter_info.failed_requests,
                "success_rate": (
                    adapter_info.successful_requests / adapter_info.total_requests
                    if adapter_info.total_requests > 0 else 0
                ),
                "last_health_check": (
                    adapter_info.last_health_check.isoformat()
                    if adapter_info.last_health_check else None
                )
            }
            
            if instance:
                health_data = await instance.get_health_status()
                status_data["detailed_health"] = health_data
                
            return status_data
            
        else:
            # Return status for all adapters
            all_status = {}
            for aid, adapter_info in self._adapters.items():
                all_status[aid] = await self.get_adapter_status(aid)
                
            return {
                "total_adapters": len(self._adapters),
                "adapters": all_status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_adapters": len(self._adapters),
            "active_adapters": sum(
                1 for info in self._adapters.values() 
                if info.status == AdapterStatus.HEALTHY
            ),
            "total_requests": sum(info.total_requests for info in self._adapters.values()),
            "successful_requests": sum(info.successful_requests for info in self._adapters.values()),
            "failed_requests": sum(info.failed_requests for info in self._adapters.values()),
            "adapter_details": {},
            "global_performance": self._global_performance_monitor.get_performance_dashboard_data()
        }
        
        # Calculate overall success rate
        total_requests = dashboard_data["total_requests"]
        if total_requests > 0:
            dashboard_data["overall_success_rate"] = (
                dashboard_data["successful_requests"] / total_requests
            )
        else:
            dashboard_data["overall_success_rate"] = 0.0
            
        # Get detailed performance metrics for each adapter
        for adapter_id, adapter_info in self._adapters.items():
            if adapter_info.instance:
                try:
                    metrics = await adapter_info.instance.get_performance_metrics()
                    dashboard_data["adapter_details"][adapter_id] = metrics
                except Exception as e:
                    dashboard_data["adapter_details"][adapter_id] = {
                        "error": f"Failed to get metrics: {str(e)}"
                    }
                    
        return dashboard_data
        
    async def optimize_all_adapters(self) -> Dict[str, Any]:
        """Run optimization for all adapters"""
        optimization_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "adapters_optimized": 0,
            "total_changes": 0,
            "results": {}
        }
        
        for adapter_id, adapter_info in self._adapters.items():
            if adapter_info.instance and adapter_info.status == AdapterStatus.HEALTHY:
                try:
                    result = await adapter_info.instance.optimize_configuration()
                    optimization_results["results"][adapter_id] = result
                    
                    if result.get("optimization_applied"):
                        optimization_results["adapters_optimized"] += 1
                        optimization_results["total_changes"] += len(result.get("changes", {}))
                        
                except Exception as e:
                    optimization_results["results"][adapter_id] = {
                        "error": f"Optimization failed: {str(e)}"
                    }
                    
        return optimization_results
        
    async def _select_adapter(
        self, 
        request: CollectionRequest, 
        preferred_adapter_id: Optional[str]
    ) -> Optional[str]:
        """Select the best adapter for a request"""
        # If preferred adapter specified and available, use it
        if preferred_adapter_id and preferred_adapter_id in self._adapter_instances:
            adapter_info = self._adapters[preferred_adapter_id]
            if adapter_info.status == AdapterStatus.HEALTHY:
                return preferred_adapter_id
                
        # Find adapters that can handle this platform
        suitable_adapters = []
        for adapter_id, adapter_info in self._adapters.items():
            if (adapter_info.configuration.platform == request.platform and
                adapter_info.status == AdapterStatus.HEALTHY and
                adapter_info.instance):
                suitable_adapters.append((adapter_id, adapter_info))
                
        if not suitable_adapters:
            return None
            
        # Select based on success rate and current load
        best_adapter = None
        best_score = -1
        
        for adapter_id, adapter_info in suitable_adapters:
            # Calculate score based on success rate and load
            success_rate = (
                adapter_info.successful_requests / adapter_info.total_requests
                if adapter_info.total_requests > 0 else 1.0
            )
            
            # Simple load balancing - prefer adapters with fewer active operations
            instance = adapter_info.instance
            load_factor = 1.0
            
            try:
                health_data = await instance.get_health_status()
                active_ops = health_data.get("active_operations", 0)
                load_factor = max(0.1, 1.0 - (active_ops / 10))  # Normalize load
            except Exception:
                pass
                
            score = success_rate * load_factor
            
            if score > best_score:
                best_score = score
                best_adapter = adapter_id
                
        return best_adapter
        
    async def _health_check_loop(self):
        """Background health checking loop"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
                
    async def _perform_health_checks(self):
        """Perform health checks on all adapters"""
        for adapter_id, adapter_info in self._adapters.items():
            if adapter_info.instance:
                try:
                    health_data = await adapter_info.instance.get_health_status()
                    
                    # Determine status based on health data
                    if health_data.get("performance_health", {}).get("health_status") == "unhealthy":
                        adapter_info.status = AdapterStatus.UNHEALTHY
                    elif health_data.get("performance_health", {}).get("health_status") == "degraded":
                        adapter_info.status = AdapterStatus.DEGRADED
                    else:
                        adapter_info.status = AdapterStatus.HEALTHY
                        
                    adapter_info.last_health_check = datetime.utcnow()
                    
                except Exception as e:
                    self.logger.error(f"Health check failed for {adapter_id}: {str(e)}")
                    adapter_info.status = AdapterStatus.UNHEALTHY
                    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                await self.optimize_all_adapters()
                await asyncio.sleep(self._optimization_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Optimization loop error: {str(e)}")
                await asyncio.sleep(300)  # Wait before retrying
                
    async def _request_worker(self, worker_name: str):
        """Background worker for processing queued requests"""
        while True:
            try:
                # This is a placeholder for future request queuing implementation
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Request worker {worker_name} error: {str(e)}")
                await asyncio.sleep(1)


# Global adapter manager instance
adapter_manager = AdapterManager()