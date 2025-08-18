"""Core adapter orchestration implementation"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.collection_flow.adapters import (
    AdapterRegistry,
    BaseAdapter,
    CollectionRequest,
)

from .aggregator import AdapterAggregator
from .base import OrchestrationConfig, OrchestrationStatus
from .executor import AdapterExecutor
from .models import OrchestrationResult
from .monitor import ResourceMonitor


class AdapterOrchestrator:
    """Orchestrates multiple platform adapters for parallel data collection"""

    def __init__(
        self,
        db: AsyncSession,
        adapter_registry: AdapterRegistry,
        config: Optional[OrchestrationConfig] = None,
    ):
        """Initialize adapter orchestrator"""
        self.db = db
        self.adapter_registry = adapter_registry
        self.config = config or OrchestrationConfig()
        self.logger = logging.getLogger(f"{__name__}.AdapterOrchestrator")

        # Execution state
        self._active_orchestrations: Dict[str, OrchestrationResult] = {}
        self._execution_semaphore = asyncio.Semaphore(self.config.max_parallel_adapters)
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.config.max_parallel_adapters
        )

        # Performance monitoring
        self._resource_monitor = ResourceMonitor()

        # Initialize specialized components
        self._executor = AdapterExecutor(
            db=self.db,
            config=self.config,
            resource_monitor=self._resource_monitor,
            execution_semaphore=self._execution_semaphore,
            thread_pool=self._thread_pool,
            adapter_registry=self.adapter_registry,
            logger=self.logger,
        )
        self._aggregator = AdapterAggregator(
            config=self.config,
            logger=self.logger,
        )

    async def orchestrate_collection(
        self,
        platform_requests: Dict[str, CollectionRequest],
        orchestration_id: Optional[str] = None,
    ) -> OrchestrationResult:
        """Orchestrate parallel data collection across multiple platforms"""
        if not orchestration_id:
            orchestration_id = f"orch_{int(time.time())}_{id(self)}"

        self.logger.info(
            f"Starting orchestration {orchestration_id} for {len(platform_requests)} platforms"
        )

        # Initialize orchestration result
        result = OrchestrationResult(
            orchestration_id=orchestration_id,
            status=OrchestrationStatus.RUNNING,
            start_time=datetime.utcnow(),
            total_adapters=len(platform_requests),
        )

        self._active_orchestrations[orchestration_id] = result

        try:
            # Start resource monitoring
            await self._resource_monitor.start_monitoring()

            # Validate and prepare adapters
            adapter_tasks = await self._prepare_adapter_tasks(
                platform_requests, orchestration_id
            )

            if not adapter_tasks:
                result.status = OrchestrationStatus.FAILED
                result.error_summary = {
                    "error": "No valid adapters found for execution"
                }
                return result

            # Execute adapters in parallel with resource management
            adapter_results = await self._executor.execute_adapters_parallel(
                adapter_tasks, orchestration_id
            )

            # Process and aggregate results
            result.adapter_results = adapter_results
            result.successful_adapters = sum(1 for r in adapter_results if r.success)
            result.failed_adapters = len(adapter_results) - result.successful_adapters

            # Aggregate data from successful adapters
            if result.successful_adapters > 0:
                aggregated_data = await self._aggregator.aggregate_adapter_results(
                    adapter_results
                )
                result.aggregated_data = aggregated_data
                result.total_resources = aggregated_data.get("total_resources", 0)
                result.unique_resources = aggregated_data.get("unique_resources", 0)
                result.duplicate_resources = aggregated_data.get(
                    "duplicate_resources", 0
                )

            # Determine final status
            if result.successful_adapters == 0:
                result.status = OrchestrationStatus.FAILED
            elif result.failed_adapters == 0:
                result.status = OrchestrationStatus.COMPLETED
            else:
                result.status = OrchestrationStatus.PARTIAL_SUCCESS

            # Collect platform summary
            result.platforms_collected = [
                r.platform for r in adapter_results if r.success
            ]
            result.collection_methods_used = list(
                set(
                    [
                        r.response.collection_method.value
                        for r in adapter_results
                        if r.response and r.response.collection_method
                    ]
                )
            )

            # Stop resource monitoring and collect metrics
            monitoring_result = await self._resource_monitor.stop_monitoring()
            result.peak_memory_usage_mb = monitoring_result.get("peak_memory_mb")
            result.peak_cpu_usage_percent = monitoring_result.get("peak_cpu_percent")
            result.disk_usage_mb = monitoring_result.get("disk_usage_mb")

        except Exception as e:
            self.logger.error(f"Orchestration {orchestration_id} failed: {str(e)}")
            result.status = OrchestrationStatus.FAILED
            result.error_summary = {"error": str(e), "error_type": type(e).__name__}

        finally:
            # Finalize timing
            result.end_time = datetime.utcnow()
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

            # Cleanup
            self._active_orchestrations.pop(orchestration_id, None)

        self.logger.info(
            f"Orchestration {orchestration_id} completed: {result.status.value}, "
            f"{result.successful_adapters}/{result.total_adapters} adapters successful, "
            f"{result.total_resources} total resources"
        )

        return result

    async def _prepare_adapter_tasks(
        self, platform_requests: Dict[str, CollectionRequest], orchestration_id: str
    ) -> List[Tuple[BaseAdapter, CollectionRequest, str]]:
        """Prepare adapter tasks for execution"""
        adapter_tasks = []

        for platform, request in platform_requests.items():
            try:
                # Find suitable adapter for platform
                adapter_metadata_list = self.adapter_registry.get_adapters_by_platform(
                    platform
                )

                if not adapter_metadata_list:
                    self.logger.warning(f"No adapters found for platform: {platform}")
                    continue

                # Select best adapter (highest version, most capabilities)
                best_metadata = max(
                    adapter_metadata_list,
                    key=lambda m: (m.version, len(m.capabilities)),
                )

                # Get adapter instance
                adapter = self.adapter_registry.get_adapter(
                    best_metadata.name, best_metadata.version, self.db
                )

                if not adapter:
                    self.logger.warning(
                        f"Failed to instantiate adapter for platform: {platform}"
                    )
                    continue

                # Validate adapter configuration
                if not await self._validate_adapter_request(adapter, request):
                    self.logger.warning(
                        f"Invalid configuration for adapter: {best_metadata.name}"
                    )
                    continue

                adapter_tasks.append((adapter, request, platform))

            except Exception as e:
                self.logger.error(
                    f"Failed to prepare adapter for platform {platform}: {str(e)}"
                )
                continue

        return adapter_tasks

    async def _validate_adapter_request(
        self, adapter: BaseAdapter, request: CollectionRequest
    ) -> bool:
        """Validate adapter request configuration"""
        try:
            # Validate credentials
            if not await adapter.validate_credentials(request.credentials):
                return False

            # Validate configuration schema
            if not adapter.validate_configuration(request.configuration):
                return False

            # Test connectivity if required
            if request.configuration.get("test_connectivity", True):
                if not await adapter.test_connectivity(request.configuration):
                    self.logger.warning(
                        f"Connectivity test failed for adapter: {adapter.metadata.name}"
                    )
                    # Don't fail validation for connectivity issues - might be temporary

            return True

        except Exception as e:
            self.logger.error(f"Adapter validation failed: {str(e)}")
            return False

    async def get_orchestration_status(
        self, orchestration_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current status of an orchestration"""
        result = self._active_orchestrations.get(orchestration_id)
        if not result:
            return None

        return {
            "orchestration_id": result.orchestration_id,
            "status": result.status.value,
            "start_time": result.start_time.isoformat(),
            "duration_seconds": (datetime.utcnow() - result.start_time).total_seconds(),
            "total_adapters": result.total_adapters,
            "successful_adapters": result.successful_adapters,
            "failed_adapters": result.failed_adapters,
            "platforms_collected": result.platforms_collected,
            "total_resources": result.total_resources,
        }

    async def cancel_orchestration(self, orchestration_id: str) -> bool:
        """Cancel a running orchestration"""
        result = self._active_orchestrations.get(orchestration_id)
        if not result or result.status != OrchestrationStatus.RUNNING:
            return False

        result.status = OrchestrationStatus.CANCELLED
        return True

    async def list_active_orchestrations(self) -> List[Dict[str, Any]]:
        """List all active orchestrations"""
        return [
            await self.get_orchestration_status(orch_id)
            for orch_id in self._active_orchestrations.keys()
        ]

    def __del__(self):
        """Cleanup resources"""
        try:
            if hasattr(self, "_thread_pool"):
                self._thread_pool.shutdown(wait=False)
        except Exception:
            pass
