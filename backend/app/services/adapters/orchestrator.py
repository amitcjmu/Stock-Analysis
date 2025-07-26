"""
Adapter Orchestration and Parallel Execution for ADCS Implementation

This module provides orchestration capabilities for managing multiple platform adapters
with parallel execution, result aggregation, and resource management.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.collection_flow.adapters import (
    AdapterRegistry,
    BaseAdapter,
    CollectionRequest,
    CollectionResponse,
)


class OrchestrationStatus(str, Enum):
    """Orchestration execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"


class AdapterStatus(str, Enum):
    """Individual adapter execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class AdapterExecutionResult:
    """Result of adapter execution"""

    adapter_name: str
    adapter_version: str
    platform: str
    status: AdapterStatus
    response: Optional[CollectionResponse] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    resource_count: int = 0

    @property
    def success(self) -> bool:
        return (
            self.status == AdapterStatus.COMPLETED
            and self.response
            and self.response.success
        )


@dataclass
class OrchestrationConfig:
    """Configuration for adapter orchestration"""

    max_parallel_adapters: int = 5
    adapter_timeout_seconds: int = 1800  # 30 minutes
    enable_result_deduplication: bool = True
    enable_cross_platform_correlation: bool = True
    resource_limit_per_adapter: Optional[int] = None
    retry_failed_adapters: bool = False
    retry_attempts: int = 1
    retry_delay_seconds: int = 30

    # Performance settings
    memory_limit_mb: int = 2048
    cpu_limit_percent: float = 80.0
    disk_space_threshold_mb: int = 1024

    # Result aggregation settings
    merge_duplicate_assets: bool = True
    confidence_threshold: float = 0.7
    asset_similarity_threshold: float = 0.8


@dataclass
class OrchestrationResult:
    """Result of orchestrated collection"""

    orchestration_id: str
    status: OrchestrationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Adapter results
    adapter_results: List[AdapterExecutionResult] = field(default_factory=list)
    successful_adapters: int = 0
    failed_adapters: int = 0
    total_adapters: int = 0

    # Aggregated data
    aggregated_data: Optional[Dict[str, Any]] = None
    total_resources: int = 0
    unique_resources: int = 0
    duplicate_resources: int = 0

    # Performance metrics
    peak_memory_usage_mb: Optional[float] = None
    peak_cpu_usage_percent: Optional[float] = None
    disk_usage_mb: Optional[float] = None

    # Summary
    platforms_collected: List[str] = field(default_factory=list)
    collection_methods_used: List[str] = field(default_factory=list)
    error_summary: Optional[Dict[str, Any]] = None


class AdapterOrchestrator:
    """
    Orchestrates multiple platform adapters for parallel data collection

    Provides capabilities for:
    - Parallel adapter execution with resource management
    - Result aggregation and deduplication
    - Error handling and retry logic
    - Performance monitoring and optimization
    - Cross-platform correlation
    """

    def __init__(
        self,
        db: AsyncSession,
        adapter_registry: AdapterRegistry,
        config: Optional[OrchestrationConfig] = None,
    ):
        """
        Initialize adapter orchestrator

        Args:
            db: Database session
            adapter_registry: Registry of available adapters
            config: Orchestration configuration
        """
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

    async def orchestrate_collection(
        self,
        platform_requests: Dict[str, CollectionRequest],
        orchestration_id: Optional[str] = None,
    ) -> OrchestrationResult:
        """
        Orchestrate parallel data collection across multiple platforms

        Args:
            platform_requests: Dictionary mapping platform names to collection requests
            orchestration_id: Optional orchestration identifier

        Returns:
            Orchestration result with aggregated data and execution details
        """
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
            adapter_results = await self._execute_adapters_parallel(
                adapter_tasks, orchestration_id
            )

            # Process and aggregate results
            result.adapter_results = adapter_results
            result.successful_adapters = sum(1 for r in adapter_results if r.success)
            result.failed_adapters = len(adapter_results) - result.successful_adapters

            # Aggregate data from successful adapters
            if result.successful_adapters > 0:
                aggregated_data = await self._aggregate_adapter_results(adapter_results)
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

    async def _execute_adapters_parallel(
        self,
        adapter_tasks: List[Tuple[BaseAdapter, CollectionRequest, str]],
        orchestration_id: str,
    ) -> List[AdapterExecutionResult]:
        """Execute adapters in parallel with resource management"""
        self.logger.info(f"Executing {len(adapter_tasks)} adapters in parallel")

        # Create execution tasks
        execution_tasks = [
            self._execute_single_adapter(adapter, request, platform, orchestration_id)
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

    async def _execute_single_adapter(
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

        async with self._execution_semaphore:
            try:
                self.logger.info(
                    f"Starting adapter {adapter.metadata.name} for platform {platform}"
                )

                # Check resource limits before execution
                if not await self._check_resource_limits():
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
                    self.logger.info(
                        f"Adapter {adapter.metadata.name} completed successfully: "
                        f"{response.resource_count} resources in {response.duration_seconds:.2f}s"
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

    async def _check_resource_limits(self) -> bool:
        """Check if resource limits allow adapter execution"""
        try:
            current_metrics = await self._resource_monitor.get_current_metrics()

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

    async def _aggregate_adapter_results(
        self, adapter_results: List[AdapterExecutionResult]
    ) -> Dict[str, Any]:
        """Aggregate results from multiple adapters"""
        try:
            aggregated_data = {
                "platform": "Multi-Platform",
                "platform_version": "1.0",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "platforms": [],
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
                "metadata": {
                    "orchestration_summary": {
                        "total_adapters": len(adapter_results),
                        "successful_adapters": len(
                            [r for r in adapter_results if r.success]
                        ),
                        "platforms_collected": [],
                    }
                },
            }

            # Aggregate data from successful adapters
            all_assets = []
            all_dependencies = []
            platform_metrics = {}

            for adapter_result in adapter_results:
                if not adapter_result.success or not adapter_result.response:
                    continue

                response_data = adapter_result.response.data
                if not response_data:
                    continue

                # Add platform info
                platform_info = {
                    "platform": adapter_result.platform,
                    "adapter": adapter_result.adapter_name,
                    "version": adapter_result.adapter_version,
                    "resource_count": adapter_result.resource_count,
                    "collection_duration": adapter_result.duration_seconds,
                }
                aggregated_data["platforms"].append(platform_info)
                aggregated_data["metadata"]["orchestration_summary"][
                    "platforms_collected"
                ].append(adapter_result.platform)

                # Transform and collect assets
                transformed_data = self._get_adapter_instance(
                    adapter_result
                ).transform_data(response_data)

                if "assets" in transformed_data:
                    all_assets.extend(transformed_data["assets"])

                if "dependencies" in transformed_data:
                    all_dependencies.extend(transformed_data["dependencies"])

                if "performance_metrics" in transformed_data:
                    platform_metrics[adapter_result.platform] = transformed_data[
                        "performance_metrics"
                    ]

            # Deduplicate and merge assets if enabled
            if self.config.enable_result_deduplication and all_assets:
                deduplicated_assets = await self._deduplicate_assets(all_assets)
                aggregated_data["assets"] = deduplicated_assets["unique_assets"]
                aggregated_data["duplicate_assets"] = deduplicated_assets["duplicates"]
                aggregated_data["unique_resources"] = len(
                    deduplicated_assets["unique_assets"]
                )
                aggregated_data["duplicate_resources"] = len(
                    deduplicated_assets["duplicates"]
                )
            else:
                aggregated_data["assets"] = all_assets
                aggregated_data["unique_resources"] = len(all_assets)
                aggregated_data["duplicate_resources"] = 0

            aggregated_data["dependencies"] = all_dependencies
            aggregated_data["performance_metrics"] = platform_metrics
            aggregated_data["total_resources"] = len(all_assets)

            # Cross-platform correlation if enabled
            if self.config.enable_cross_platform_correlation:
                correlations = await self._correlate_cross_platform_assets(
                    aggregated_data["assets"]
                )
                aggregated_data["cross_platform_correlations"] = correlations

            return aggregated_data

        except Exception as e:
            self.logger.error(f"Result aggregation failed: {str(e)}")
            return {
                "error": f"Aggregation failed: {str(e)}",
                "raw_results": [r.__dict__ for r in adapter_results if r.success],
            }

    def _get_adapter_instance(
        self, adapter_result: AdapterExecutionResult
    ) -> BaseAdapter:
        """Get adapter instance for result transformation"""
        return self.adapter_registry.get_adapter(
            adapter_result.adapter_name, adapter_result.adapter_version, self.db
        )

    async def _deduplicate_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Deduplicate assets across platforms using similarity matching"""
        try:
            unique_assets = []
            duplicates = []
            processed_indices = set()

            for i, asset in enumerate(assets):
                if i in processed_indices:
                    continue

                # Find similar assets
                similar_assets = [asset]
                similar_indices = [i]

                for j, other_asset in enumerate(assets[i + 1 :], i + 1):
                    if j in processed_indices:
                        continue

                    similarity = self._calculate_asset_similarity(asset, other_asset)
                    if similarity >= self.config.asset_similarity_threshold:
                        similar_assets.append(other_asset)
                        similar_indices.append(j)
                        processed_indices.add(j)

                processed_indices.update(similar_indices)

                # Merge similar assets or keep as unique
                if len(similar_assets) > 1:
                    merged_asset = self._merge_similar_assets(similar_assets)
                    unique_assets.append(merged_asset)
                    duplicates.extend(similar_assets[1:])  # Keep first as original
                else:
                    unique_assets.append(asset)

            return {
                "unique_assets": unique_assets,
                "duplicates": duplicates,
                "deduplication_summary": {
                    "original_count": len(assets),
                    "unique_count": len(unique_assets),
                    "duplicate_count": len(duplicates),
                },
            }

        except Exception as e:
            self.logger.error(f"Asset deduplication failed: {str(e)}")
            return {
                "unique_assets": assets,
                "duplicates": [],
                "deduplication_summary": {"error": str(e)},
            }

    def _calculate_asset_similarity(
        self, asset1: Dict[str, Any], asset2: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between two assets"""
        try:
            # Simple similarity calculation based on key fields
            similarity_score = 0.0
            total_checks = 0

            # Check IP addresses
            if asset1.get("ip_addresses") and asset2.get("ip_addresses"):
                total_checks += 1
                ip1 = asset1["ip_addresses"].get("primary") or asset1[
                    "ip_addresses"
                ].get("private")
                ip2 = asset2["ip_addresses"].get("primary") or asset2[
                    "ip_addresses"
                ].get("private")
                if ip1 and ip2 and ip1 == ip2:
                    similarity_score += 0.4

            # Check hostnames
            if asset1.get("name") and asset2.get("name"):
                total_checks += 1
                if asset1["name"].lower() == asset2["name"].lower():
                    similarity_score += 0.3

            # Check MAC addresses
            if asset1.get("mac_address") and asset2.get("mac_address"):
                total_checks += 1
                if asset1["mac_address"] == asset2["mac_address"]:
                    similarity_score += 0.2

            # Check unique IDs
            if asset1.get("unique_id") and asset2.get("unique_id"):
                total_checks += 1
                if asset1["unique_id"] == asset2["unique_id"]:
                    similarity_score += 0.1

            return similarity_score if total_checks > 0 else 0.0

        except Exception:
            return 0.0

    def _merge_similar_assets(
        self, similar_assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge similar assets into a single consolidated asset"""
        try:
            # Use first asset as base
            merged_asset = similar_assets[0].copy()

            # Add metadata about merge
            merged_asset["merged_from_platforms"] = [
                asset.get("platform") for asset in similar_assets
            ]
            merged_asset["merge_confidence"] = len(similar_assets) / len(similar_assets)
            merged_asset["original_asset_count"] = len(similar_assets)

            # Merge platform-specific data
            merged_asset["platform_data"] = {}
            for asset in similar_assets:
                platform = asset.get("platform")
                if platform:
                    merged_asset["platform_data"][platform] = asset.get("raw_data", {})

            # Merge performance metrics
            if any("performance_metrics" in asset for asset in similar_assets):
                merged_metrics = {}
                for asset in similar_assets:
                    if "performance_metrics" in asset:
                        platform = asset.get("platform", "unknown")
                        merged_metrics[platform] = asset["performance_metrics"]
                merged_asset["performance_metrics"] = merged_metrics

            return merged_asset

        except Exception as e:
            self.logger.warning(f"Asset merge failed: {str(e)}")
            return similar_assets[0]  # Return first asset as fallback

    async def _correlate_cross_platform_assets(
        self, assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Correlate assets across platforms to identify relationships"""
        try:
            correlations = {
                "network_correlations": [],
                "service_correlations": [],
                "dependency_correlations": [],
            }

            # Group assets by platform
            platform_assets = {}
            for asset in assets:
                platform = asset.get("platform", "unknown")
                if platform not in platform_assets:
                    platform_assets[platform] = []
                platform_assets[platform].append(asset)

            # Find network correlations (same IP ranges, subnets)
            for platform1, assets1 in platform_assets.items():
                for platform2, assets2 in platform_assets.items():
                    if platform1 >= platform2:  # Avoid duplicates
                        continue

                    network_matches = self._find_network_correlations(assets1, assets2)
                    if network_matches:
                        correlations["network_correlations"].extend(network_matches)

            # Find service correlations (same services, dependencies)
            service_matches = self._find_service_correlations(assets)
            correlations["service_correlations"] = service_matches

            return correlations

        except Exception as e:
            self.logger.error(f"Cross-platform correlation failed: {str(e)}")
            return {"error": str(e)}

    def _find_network_correlations(
        self, assets1: List[Dict], assets2: List[Dict]
    ) -> List[Dict]:
        """Find network correlations between asset groups"""
        correlations = []

        try:
            for asset1 in assets1:
                for asset2 in assets2:
                    # Check for same IP addresses
                    ip1 = self._extract_primary_ip(asset1)
                    ip2 = self._extract_primary_ip(asset2)

                    if ip1 and ip2 and ip1 == ip2:
                        correlation = {
                            "type": "same_ip_address",
                            "asset1": {
                                "platform": asset1.get("platform"),
                                "unique_id": asset1.get("unique_id"),
                                "name": asset1.get("name"),
                            },
                            "asset2": {
                                "platform": asset2.get("platform"),
                                "unique_id": asset2.get("unique_id"),
                                "name": asset2.get("name"),
                            },
                            "correlation_data": {"ip_address": ip1},
                        }
                        correlations.append(correlation)

        except Exception as e:
            self.logger.warning(f"Network correlation failed: {str(e)}")

        return correlations

    def _find_service_correlations(self, assets: List[Dict]) -> List[Dict]:
        """Find service correlations across all assets"""
        correlations = []

        try:
            # Group assets by services
            service_groups = {}

            for asset in assets:
                services = asset.get("services", [])
                if not services:
                    continue

                for service in services:
                    service_key = (
                        f"{service.get('service', 'unknown')}:{service.get('port', 0)}"
                    )
                    if service_key not in service_groups:
                        service_groups[service_key] = []
                    service_groups[service_key].append(asset)

            # Find correlations where multiple platforms have the same service
            for service_key, service_assets in service_groups.items():
                if len(service_assets) > 1:
                    platforms = set(asset.get("platform") for asset in service_assets)
                    if len(platforms) > 1:  # Cross-platform correlation
                        correlation = {
                            "type": "common_service",
                            "service": service_key,
                            "platforms": list(platforms),
                            "asset_count": len(service_assets),
                            "assets": [
                                {
                                    "platform": asset.get("platform"),
                                    "unique_id": asset.get("unique_id"),
                                    "name": asset.get("name"),
                                }
                                for asset in service_assets
                            ],
                        }
                        correlations.append(correlation)

        except Exception as e:
            self.logger.warning(f"Service correlation failed: {str(e)}")

        return correlations

    def _extract_primary_ip(self, asset: Dict[str, Any]) -> Optional[str]:
        """Extract primary IP address from asset"""
        ip_addresses = asset.get("ip_addresses")
        if not ip_addresses:
            return None

        # Try different IP address fields
        return (
            ip_addresses.get("primary")
            or ip_addresses.get("private")
            or ip_addresses.get("public")
            or asset.get("unique_id")
            if self._is_ip_address(asset.get("unique_id"))
            else None
        )

    def _is_ip_address(self, value: str) -> bool:
        """Check if value is an IP address"""
        if not value:
            return False

        try:
            import ipaddress

            ipaddress.ip_address(value)
            return True
        except ValueError:
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


class ResourceMonitor:
    """Monitor system resources during adapter execution"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")
        self._monitoring = False
        self._metrics_history = []

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

            # Get process info
            process = psutil.Process()

            metrics = {
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_usage_percent": process.cpu_percent(),
                "available_disk_mb": psutil.disk_usage("/").free / 1024 / 1024,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if self._monitoring:
                self._metrics_history.append(metrics)

            return metrics

        except ImportError:
            # psutil not available, return empty metrics
            return {}
        except Exception as e:
            self.logger.warning(f"Failed to get system metrics: {str(e)}")
            return {}
