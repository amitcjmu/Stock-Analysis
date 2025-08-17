"""
Azure data transformation utilities
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .utils import normalize_asset_type

logger = logging.getLogger(__name__)


class AzureDataTransformer:
    """Handles transformation of raw Azure data to normalized formats"""

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw Azure data to normalized format for Discovery Flow

        Args:
            raw_data: Raw Azure data from collection

        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        try:
            normalized_data = {
                "platform": "Azure",
                "platform_version": "1.0",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
                "metadata": raw_data.get("metadata", {}),
            }

            # Transform each resource type's resources to normalized assets
            for resource_type, type_data in raw_data.items():
                if resource_type == "metadata" or "error" in type_data:
                    continue

                if "resources" in type_data:
                    for resource in type_data["resources"]:
                        normalized_asset = self.transform_resource_to_asset(
                            resource_type, resource
                        )
                        if normalized_asset:
                            normalized_data["assets"].append(normalized_asset)

            # Transform performance metrics
            if "metrics" in raw_data:
                normalized_data["performance_metrics"] = self.transform_metrics(
                    raw_data["metrics"]
                )

            logger.info(
                f"Transformed {len(normalized_data['assets'])} Azure assets to normalized format"
            )

            return normalized_data

        except Exception as e:
            logger.error(f"Failed to transform Azure data: {str(e)}")
            return {
                "platform": "Azure",
                "error": f"Data transformation failed: {str(e)}",
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
            }

    def transform_resource_to_asset(
        self, resource_type: str, resource: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Transform Azure resource to normalized asset format"""
        try:
            # Common asset structure
            asset = {
                "platform": "Azure",
                "platform_service": resource_type,
                "asset_type": normalize_asset_type(resource_type),
                "unique_id": resource.get("id"),
                "name": resource.get("name"),
                "environment": "cloud",
                "region": resource.get("location"),
                "resource_group": resource.get("resource_group"),
                "subscription_id": resource.get("subscription_id"),
                "tags": resource.get("tags", {}),
                "discovery_method": "automated",
                "discovery_timestamp": datetime.utcnow().isoformat(),
                "raw_data": resource,
            }

            # Resource-type-specific transformations
            if resource_type == "Microsoft.Compute/virtualMachines":
                asset.update(
                    {
                        "compute_type": "virtual_machine",
                        "instance_type": resource.get("vm_size"),
                        "state": resource.get(
                            "power_state", resource.get("provisioning_state")
                        ),
                        "operating_system": resource.get("os_type"),
                        "computer_name": resource.get("computer_name"),
                        "network_interfaces": resource.get("network_interfaces", []),
                        "zones": resource.get("zones", []),
                    }
                )

            elif resource_type == "Microsoft.Sql/servers/databases":
                asset.update(
                    {
                        "database_type": "sql_server",
                        "database_sku": resource.get("sku", {}),
                        "database_status": resource.get("status"),
                        "max_size_bytes": resource.get("max_size_bytes"),
                        "collation": resource.get("collation"),
                        "zone_redundant": resource.get("zone_redundant"),
                    }
                )

            elif resource_type == "Microsoft.Web/sites":
                asset.update(
                    {
                        "compute_type": "web_application",
                        "app_kind": resource.get("kind"),
                        "app_state": resource.get("state"),
                        "host_names": resource.get("host_names", []),
                        "default_host_name": resource.get("default_host_name"),
                        "https_only": resource.get("https_only"),
                        "site_config": resource.get("site_config", {}),
                    }
                )

            elif resource_type == "Microsoft.Storage/storageAccounts":
                asset.update(
                    {
                        "storage_type": "object_storage",
                        "storage_sku": resource.get("sku", {}),
                        "storage_kind": resource.get("kind"),
                        "access_tier": resource.get("access_tier"),
                        "primary_location": resource.get("primary_location"),
                        "secondary_location": resource.get("secondary_location"),
                        "https_only": resource.get("enable_https_traffic_only"),
                    }
                )

            elif resource_type == "Microsoft.Network/loadBalancers":
                asset.update(
                    {
                        "network_type": "load_balancer",
                        "load_balancer_sku": resource.get("sku", {}),
                        "frontend_ip_configurations": resource.get(
                            "frontend_ip_configurations", []
                        ),
                        "backend_address_pools": resource.get(
                            "backend_address_pools", []
                        ),
                        "load_balancing_rules": resource.get(
                            "load_balancing_rules", []
                        ),
                    }
                )

            return asset

        except Exception as e:
            logger.warning(
                f"Failed to transform {resource_type} resource to asset: {str(e)}"
            )
            return None

    def transform_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Azure Monitor metrics to normalized format"""
        normalized_metrics = {}

        for service, service_metrics in metrics_data.items():
            if isinstance(service_metrics, list):
                normalized_metrics[service] = []
                for metric in service_metrics:
                    normalized_metric = {
                        "resource_id": metric.get("resource_id"),
                        "resource_type": metric.get("resource_type"),
                        "resource_name": metric.get("resource_name"),
                        "timestamp": metric.get("timestamp"),
                        "metrics": {},
                    }

                    # Normalize metric names
                    for key, value in metric.items():
                        if (
                            key
                            not in [
                                "resource_id",
                                "resource_type",
                                "resource_name",
                                "timestamp",
                            ]
                            and value is not None
                        ):
                            normalized_metric["metrics"][key] = value

                    normalized_metrics[service].append(normalized_metric)

        return normalized_metrics
