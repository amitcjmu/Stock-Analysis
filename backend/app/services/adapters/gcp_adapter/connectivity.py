"""
GCP Connectivity Testing

Handles connectivity testing for various GCP services.
"""

import logging
from typing import Any, Dict

from .auth import GCPAuthManager
from .dependencies import asset_v1, compute_v1, monitoring_v3
from .models import GCPCredentials


class GCPConnectivityTester:
    """Tests connectivity to various GCP services"""

    def __init__(self, auth_manager: GCPAuthManager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)

    async def test_connectivity(self, configuration: Dict[str, Any]) -> bool:
        """
        Test connectivity to GCP APIs and verify required permissions

        Args:
            configuration: GCP configuration including credentials

        Returns:
            True if connectivity successful, False otherwise
        """
        try:
            # Extract credentials
            credentials = configuration.get("credentials", {})

            gcp_creds = GCPCredentials(
                project_id=credentials.get("project_id", ""),
                service_account_key=credentials.get("service_account_key", {}),
            )

            # Create credentials and initialize clients
            creds = self.auth_manager.get_gcp_credentials(gcp_creds)
            self.auth_manager.init_clients(creds, gcp_creds.project_id)

            # Test connectivity to core services
            connectivity_tests = {
                "AssetInventory": self._test_asset_inventory_connectivity,
                "Monitoring": self._test_monitoring_connectivity,
                "Compute": self._test_compute_connectivity,
                "Storage": self._test_storage_connectivity,
            }

            results = {}
            for service, test_func in connectivity_tests.items():
                try:
                    results[service] = await test_func()
                except Exception as e:
                    self.logger.warning(
                        f"Connectivity test failed for {service}: {str(e)}"
                    )
                    results[service] = False

            # Log results
            successful_tests = sum(1 for result in results.values() if result)
            total_tests = len(results)

            self.logger.info(
                f"GCP connectivity tests: {successful_tests}/{total_tests} successful"
            )

            # Consider connectivity successful if core services work
            core_services = ["AssetInventory", "Compute"]
            core_success = all(results.get(service, False) for service in core_services)

            return core_success

        except Exception as e:
            self.logger.error(f"GCP connectivity test failed: {str(e)}")
            return False

    async def _test_asset_inventory_connectivity(self) -> bool:
        """Test Cloud Asset Inventory API connectivity"""
        try:
            # Try to list assets with limit 1
            parent = f"projects/{self.auth_manager.project_id}"
            request = asset_v1.ListAssetsRequest(parent=parent, page_size=1)
            self.auth_manager.asset_client.list_assets(request=request)
            return True
        except Exception:
            return False

    async def _test_monitoring_connectivity(self) -> bool:
        """Test Cloud Monitoring API connectivity"""
        try:
            # Try to list metric descriptors
            project_name = f"projects/{self.auth_manager.project_id}"
            request = monitoring_v3.ListMetricDescriptorsRequest(
                name=project_name, page_size=1
            )
            self.auth_manager.monitoring_client.list_metric_descriptors(request=request)
            return True
        except Exception:
            return False

    async def _test_compute_connectivity(self) -> bool:
        """Test Compute Engine API connectivity"""
        try:
            # Try to list instances in all zones
            request = compute_v1.AggregatedListInstancesRequest(
                project=self.auth_manager.project_id, max_results=1
            )
            self.auth_manager.compute_client.aggregated_list(request=request)
            return True
        except Exception:
            return False

    async def _test_storage_connectivity(self) -> bool:
        """Test Cloud Storage API connectivity"""
        try:
            # Try to list buckets
            list(self.auth_manager.storage_client.list_buckets(max_results=1))
            return True
        except Exception:
            return False
