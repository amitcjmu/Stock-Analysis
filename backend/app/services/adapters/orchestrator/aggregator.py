"""Data aggregation and correlation for adapter orchestration"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import OrchestrationConfig
from .models import AdapterExecutionResult


class AdapterAggregator:
    """Handles data aggregation and correlation from multiple adapter results"""

    def __init__(
        self, config: OrchestrationConfig, logger: Optional[logging.Logger] = None
    ):
        """Initialize adapter aggregator"""
        self.config = config
        self.logger = logger or logging.getLogger(f"{__name__}.AdapterAggregator")

    async def aggregate_adapter_results(
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
                transformed_data = self._transform_adapter_data(
                    adapter_result, response_data
                )

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
                deduplicated_assets = await self.deduplicate_assets(all_assets)
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
                correlations = await self.correlate_cross_platform_assets(
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

    def _transform_adapter_data(
        self, adapter_result: AdapterExecutionResult, response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform adapter response data - placeholder for adapter-specific transformation"""
        # This would typically call the specific adapter's transform_data method
        # For now, return the data as-is with basic structure
        return {
            "assets": response_data.get("assets", []),
            "dependencies": response_data.get("dependencies", []),
            "performance_metrics": response_data.get("performance_metrics", {}),
        }

    async def deduplicate_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
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

                    similarity = self.calculate_asset_similarity(asset, other_asset)
                    if similarity >= self.config.asset_similarity_threshold:
                        similar_assets.append(other_asset)
                        similar_indices.append(j)
                        processed_indices.add(j)

                processed_indices.update(similar_indices)

                # Merge similar assets or keep as unique
                if len(similar_assets) > 1:
                    merged_asset = self.merge_similar_assets(similar_assets)
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

    def calculate_asset_similarity(
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

    def merge_similar_assets(
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
            # Calculate meaningful confidence based on matching criteria
            # Higher confidence with more platforms reporting the same asset
            merged_asset["merge_confidence"] = min(len(similar_assets) * 0.25, 1.0)
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

    async def correlate_cross_platform_assets(
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

                    network_matches = self.find_network_correlations(assets1, assets2)
                    if network_matches:
                        correlations["network_correlations"].extend(network_matches)

            # Find service correlations (same services, dependencies)
            service_matches = self.find_service_correlations(assets)
            correlations["service_correlations"] = service_matches

            return correlations

        except Exception as e:
            self.logger.error(f"Cross-platform correlation failed: {str(e)}")
            return {"error": str(e)}

    def find_network_correlations(
        self, assets1: List[Dict], assets2: List[Dict]
    ) -> List[Dict]:
        """Find network correlations between asset groups"""
        correlations = []

        try:
            for asset1 in assets1:
                for asset2 in assets2:
                    # Check for same IP addresses
                    ip1 = self.extract_primary_ip(asset1)
                    ip2 = self.extract_primary_ip(asset2)

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

    def find_service_correlations(self, assets: List[Dict]) -> List[Dict]:
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

    def extract_primary_ip(self, asset: Dict[str, Any]) -> Optional[str]:
        """Extract primary IP address from asset"""
        ip_addresses = asset.get("ip_addresses")
        if not ip_addresses:
            return None

        # Try different IP address fields
        candidate_ip = (
            ip_addresses.get("primary")
            or ip_addresses.get("private")
            or ip_addresses.get("public")
        )

        if candidate_ip:
            return candidate_ip

        # Check if unique_id is an IP address
        unique_id = asset.get("unique_id")
        if unique_id and self.is_ip_address(unique_id):
            return unique_id

        return None

    def is_ip_address(self, value: str) -> bool:
        """Check if value is an IP address"""
        if not value:
            return False

        try:
            import ipaddress

            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False
