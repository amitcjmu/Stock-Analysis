"""
GCP Adapter Main Module

Main GCP adapter class that orchestrates all modular components.
"""

import time
from typing import Any, Dict, List, Set

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.collection_flow.adapters import (
    BaseAdapter,
    CollectionRequest,
    CollectionResponse,
)

from .assets import GCPAssetCollector
from .auth import GCPAuthManager
from .connectivity import GCPConnectivityTester
from .constants import SUPPORTED_ASSET_TYPES, TARGET_MAPPING
from .dependencies import GCP_AVAILABLE
from .enhancers import GCPResourceEnhancer
from .metadata import GCP_ADAPTER_METADATA
from .metrics import GCPMetricsCollector
from .models import GCPCredentials
from .transformer import GCPDataTransformer


class GCPAdapter(BaseAdapter):
    """
    GCP Platform Adapter implementing BaseAdapter interface

    Provides comprehensive GCP resource discovery using:
    - Cloud Asset Inventory for efficient resource queries
    - Cloud Monitoring for performance metrics
    - Compute Engine API for VM details
    - Cloud SQL API for database details
    - Cloud Storage API for bucket details
    - Container API for GKE cluster details
    - Cloud Functions API for function details
    """

    def __init__(self, db: AsyncSession, metadata=GCP_ADAPTER_METADATA):
        """Initialize GCP adapter with metadata and session"""
        super().__init__(db, metadata)
        if not GCP_AVAILABLE:
            self.logger.warning(
                "Google Cloud SDK not installed. GCP adapter will not be functional."
            )

        # Initialize component managers
        self._auth_manager = GCPAuthManager()
        self._connectivity_tester = GCPConnectivityTester(self._auth_manager)
        self._asset_collector = GCPAssetCollector(self._auth_manager)
        self._resource_enhancer = GCPResourceEnhancer(self._auth_manager)
        self._metrics_collector = GCPMetricsCollector(self._auth_manager)
        self._data_transformer = None  # Initialized when project_id is available

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate GCP credentials by attempting to list projects

        Args:
            credentials: GCP credentials dictionary

        Returns:
            True if credentials are valid, False otherwise
        """
        return await self._auth_manager.validate_credentials(credentials)

    async def test_connectivity(self, configuration: Dict[str, Any]) -> bool:
        """
        Test connectivity to GCP APIs and verify required permissions

        Args:
            configuration: GCP configuration including credentials

        Returns:
            True if connectivity successful, False otherwise
        """
        return await self._connectivity_tester.test_connectivity(configuration)

    async def collect_data(self, request: CollectionRequest) -> CollectionResponse:
        """
        Collect data from GCP platform

        Args:
            request: Collection request with parameters

        Returns:
            Collection response with collected data or error information
        """
        start_time = time.time()

        try:
            # Initialize GCP clients
            credentials = request.credentials

            gcp_creds = GCPCredentials(
                project_id=credentials.get("project_id", ""),
                service_account_key=credentials.get("service_account_key", {}),
            )

            creds = self._auth_manager.get_gcp_credentials(gcp_creds)
            self._auth_manager.init_clients(creds, gcp_creds.project_id)

            # Initialize data transformer with project ID
            self._data_transformer = GCPDataTransformer(gcp_creds.project_id)

            # Collect data using Cloud Asset Inventory for efficiency
            collected_data = {}
            total_resources = 0

            if not request.target_resources or "all" in request.target_resources:
                # Collect all supported resources
                target_types = SUPPORTED_ASSET_TYPES
            else:
                # Map request targets to GCP asset types
                target_types = self._map_targets_to_asset_types(
                    request.target_resources
                )

            # Use Cloud Asset Inventory for efficient bulk collection
            asset_data = await self._asset_collector.collect_assets_with_inventory(
                target_types, request.configuration
            )

            if asset_data:
                # Process and enhance asset data
                for asset_type, assets in asset_data.items():
                    try:
                        enhanced_assets = (
                            await self._resource_enhancer.enhance_asset_data(
                                asset_type, assets, request.configuration
                            )
                        )
                        if enhanced_assets:
                            collected_data[asset_type] = {
                                "resources": enhanced_assets,
                                "service": asset_type,
                                "count": len(enhanced_assets),
                            }
                            total_resources += len(enhanced_assets)

                    except Exception as e:
                        self.logger.error(
                            f"Failed to enhance data for {asset_type}: {str(e)}"
                        )
                        collected_data[asset_type] = {"error": str(e), "resources": []}

            # Collect performance metrics if requested
            if request.configuration.get("include_metrics", True):
                try:
                    metrics_data = (
                        await self._metrics_collector.collect_performance_metrics(
                            collected_data
                        )
                    )
                    collected_data["metrics"] = metrics_data
                except Exception as e:
                    self.logger.error(
                        f"Failed to collect performance metrics: {str(e)}"
                    )
                    collected_data["metrics"] = {"error": str(e)}

            duration = time.time() - start_time

            self.logger.info(
                f"GCP data collection completed: {total_resources} resources in {duration:.2f}s"
            )

            return CollectionResponse(
                success=True,
                data=collected_data,
                resource_count=total_resources,
                collection_method=request.collection_method,
                duration_seconds=duration,
                metadata={
                    "project_id": gcp_creds.project_id,
                    "asset_types_collected": list(target_types),
                    "adapter_version": self.metadata.version,
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"GCP data collection failed: {str(e)}"
            self.logger.error(error_msg)

            return CollectionResponse(
                success=False,
                error_message=error_msg,
                error_details={"exception_type": type(e).__name__},
                duration_seconds=duration,
                metadata={
                    "project_id": (
                        gcp_creds.project_id if "gcp_creds" in locals() else "unknown"
                    )
                },
            )

    def _map_targets_to_asset_types(self, targets: List[str]) -> Set[str]:
        """Map request targets to GCP asset types"""
        mapped_types = set()
        for target in targets:
            if target in TARGET_MAPPING:
                mapped_types.add(TARGET_MAPPING[target])
            elif target in SUPPORTED_ASSET_TYPES:
                mapped_types.add(target)

        return mapped_types or SUPPORTED_ASSET_TYPES

    async def get_available_resources(self, configuration: Dict[str, Any]) -> List[str]:
        """
        Get list of available GCP resources for collection

        Args:
            configuration: GCP configuration including credentials

        Returns:
            List of available asset type identifiers
        """
        try:
            # Test connectivity first
            if not await self.test_connectivity(configuration):
                return []

            return await self._asset_collector.get_available_resources(configuration)

        except Exception as e:
            self.logger.error(f"Failed to get available GCP resources: {str(e)}")
            return []

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw GCP data to normalized format for Discovery Flow

        Args:
            raw_data: Raw GCP data from collection

        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        if not self._data_transformer:
            # Initialize with default project ID if not already initialized
            self._data_transformer = GCPDataTransformer(
                raw_data.get("metadata", {}).get("project_id", "unknown")
            )

        return self._data_transformer.transform_data(raw_data)
