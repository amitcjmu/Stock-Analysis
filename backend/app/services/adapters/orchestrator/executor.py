"""Adapter execution and resource management for orchestration"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.collection_flow.adapters import BaseAdapter, CollectionRequest

from .base import AdapterStatus, OrchestrationConfig
from .models import AdapterExecutionResult
from .monitor import ResourceMonitor


class AdapterExecutor:
    """Handles adapter execution and resource management"""

    def __init__(
        self,
        db: AsyncSession,
        config: OrchestrationConfig,
        resource_monitor: ResourceMonitor,
        execution_semaphore: asyncio.Semaphore,
        thread_pool: ThreadPoolExecutor,
        adapter_registry,
        logger: logging.Logger,
    ):
        """Initialize adapter executor"""
        self.db = db
        self.config = config
        self.resource_monitor = resource_monitor
        self.execution_semaphore = execution_semaphore
        self.thread_pool = thread_pool
        self.adapter_registry = adapter_registry
        self.logger = logger

    async def execute_adapters_parallel(
        self,
        adapter_tasks: List[Tuple[BaseAdapter, CollectionRequest, str]],
        orchestration_id: str,
    ) -> List[AdapterExecutionResult]:
        """Execute adapters in parallel with resource management"""
        self.logger.info(f"Executing {len(adapter_tasks)} adapters in parallel")

        # Create execution tasks
        execution_tasks = [
            self.execute_single_adapter(adapter, request, platform, orchestration_id)
            for adapter, request, platform in adapter_tasks
        ]

        # Execute with timeout and resource monitoring
        try:
            results = await asyncio.gather(*execution_tasks, return_exceptions=True)

            # Process results and handle exceptions
            adapter_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    adapter, request, platform = adapter_tasks[i]
                    error_result = AdapterExecutionResult(
                        adapter_name=adapter.metadata.name,
                        adapter_version=adapter.metadata.version,
                        platform=platform,
                        status=AdapterStatus.FAILED,
                        error=str(result),
                        start_time=datetime.utcnow(),
                        end_time=datetime.utcnow(),
                    )
                    adapter_results.append(error_result)
                elif isinstance(result, AdapterExecutionResult):
                    adapter_results.append(result)

        except Exception as e:
            self.logger.error(f"Parallel adapter execution failed: {str(e)}")
            # Create failed results for all adapters
            adapter_results = [
                AdapterExecutionResult(
                    adapter_name=adapter.metadata.name,
                    adapter_version=adapter.metadata.version,
                    platform=platform,
                    status=AdapterStatus.FAILED,
                    error=str(e),
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                )
                for adapter, request, platform in adapter_tasks
            ]

        return adapter_results

    async def execute_single_adapter(
        self,
        adapter: BaseAdapter,
        request: CollectionRequest,
        platform: str,
        orchestration_id: str,
    ) -> AdapterExecutionResult:
        """Execute a single adapter with timeout and error handling"""
        result = AdapterExecutionResult(
            adapter_name=adapter.metadata.name,
            adapter_version=adapter.metadata.version,
            platform=platform,
            status=AdapterStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        async with self.execution_semaphore:
            try:
                self.logger.info(
                    f"Starting adapter {adapter.metadata.name} for platform {platform}"
                )

                # Check resource limits before execution
                if not await self.check_resource_limits():
                    result.status = AdapterStatus.FAILED
                    result.error = "Resource limits exceeded"
                    return result

                # Execute adapter with timeout
                response = await asyncio.wait_for(
                    adapter.collect_data(request),
                    timeout=self.config.adapter_timeout_seconds,
                )

                result.response = response
                result.resource_count = response.resource_count if response else 0

                if response and response.success:
                    result.status = AdapterStatus.COMPLETED
                    duration = getattr(response, "duration_seconds", None)
                    duration_text = (
                        f"{duration:.2f}s"
                        if isinstance(duration, (int, float))
                        else "unknown duration"
                    )
                    self.logger.info(
                        f"Adapter {adapter.metadata.name} completed successfully: "
                        f"{response.resource_count} resources in {duration_text}"
                    )
                else:
                    result.status = AdapterStatus.FAILED
                    result.error = (
                        response.error_message if response else "Unknown error"
                    )
                    self.logger.error(
                        f"Adapter {adapter.metadata.name} failed: {result.error}"
                    )

            except asyncio.TimeoutError:
                result.status = AdapterStatus.TIMEOUT
                result.error = f"Adapter execution timed out after {self.config.adapter_timeout_seconds} seconds"
                self.logger.error(f"Adapter {adapter.metadata.name} timed out")

            except Exception as e:
                result.status = AdapterStatus.FAILED
                result.error = str(e)
                self.logger.error(
                    f"Adapter {adapter.metadata.name} failed with exception: {str(e)}"
                )

            finally:
                result.end_time = datetime.utcnow()
                result.duration_seconds = (
                    result.end_time - result.start_time
                ).total_seconds()

        return result

    async def check_resource_limits(self) -> bool:
        """Check if resource limits allow adapter execution"""
        try:
            current_metrics = await self.resource_monitor.get_current_metrics()

            # Check memory limit
            if current_metrics.get("memory_usage_mb", 0) > self.config.memory_limit_mb:
                self.logger.warning("Memory limit exceeded, skipping adapter execution")
                return False

            # Check CPU limit
            if (
                current_metrics.get("cpu_usage_percent", 0)
                > self.config.cpu_limit_percent
            ):
                self.logger.warning("CPU limit exceeded, waiting before execution")
                await asyncio.sleep(5)  # Brief wait to allow CPU to settle

            # Check disk space
            if (
                current_metrics.get("available_disk_mb", float("inf"))
                < self.config.disk_space_threshold_mb
            ):
                self.logger.warning("Insufficient disk space for adapter execution")
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Resource check failed: {str(e)}")
            return True  # Allow execution if check fails

    def get_adapter_instance(
        self, adapter_result: AdapterExecutionResult
    ) -> BaseAdapter:
        """Get adapter instance for result transformation"""
        return self.adapter_registry.get_adapter(
            adapter_result.adapter_name, adapter_result.adapter_version, self.db
        )
