"""
GCP Data Transformer

Transforms raw GCP data to normalized format for Discovery Flow.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .constants import ASSET_TYPE_MAP
from .utils import extract_resource_name


class GCPDataTransformer:
    """Transforms GCP data to normalized format"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.logger = logging.getLogger(__name__)
        
    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw GCP data to normalized format for Discovery Flow
        
        Args:
            raw_data: Raw GCP data from collection
            
        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        try:
            normalized_data = {
                "platform": "GCP",
                "platform_version": "1.0",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
                "metadata": raw_data.get("metadata", {})
            }
            
            # Transform each asset type's resources to normalized assets
            for asset_type, type_data in raw_data.items():
                if asset_type == "metadata" or "error" in type_data:
                    continue
                    
                if "resources" in type_data:
                    for resource in type_data["resources"]:
                        normalized_asset = self.transform_resource_to_asset(asset_type, resource)
                        if normalized_asset:
                            normalized_data["assets"].append(normalized_asset)
                            
            # Transform performance metrics
            if "metrics" in raw_data:
                normalized_data["performance_metrics"] = self.transform_metrics(raw_data["metrics"])
                
            self.logger.info(f"Transformed {len(normalized_data['assets'])} GCP assets to normalized format")
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Failed to transform GCP data: {str(e)}")
            return {
                "platform": "GCP",
                "error": f"Data transformation failed: {str(e)}",
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {}
            }
            
    def transform_resource_to_asset(self, asset_type: str, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform GCP resource to normalized asset format"""
        try:
            # Common asset structure
            asset = {
                "platform": "GCP",
                "platform_service": asset_type,
                "asset_type": self.get_asset_type(asset_type),
                "unique_id": resource.get("name"),
                "name": extract_resource_name(resource.get("name", "")),
                "environment": "cloud",
                "project_id": self.project_id,
                "discovery_method": "automated",
                "discovery_timestamp": datetime.utcnow().isoformat(),
                "raw_data": resource
            }
            
            # Asset-type-specific transformations
            if asset_type == "compute.googleapis.com/Instance":
                asset.update({
                    "compute_type": "virtual_machine",
                    "instance_type": resource.get("machine_type"),
                    "zone": resource.get("zone"),
                    "state": resource.get("status"),
                    "cpu_platform": resource.get("cpu_platform"),
                    "deletion_protection": resource.get("deletion_protection"),
                    "network_interfaces": resource.get("network_interfaces", []),
                    "disks": resource.get("disks", []),
                    "labels": resource.get("labels", {}),
                    "tags": resource.get("tags", {})
                })
                
            elif asset_type == "sqladmin.googleapis.com/Instance":
                asset.update({
                    "database_type": "cloud_sql",
                    "database_version": resource.get("database_version"),
                    "backend_type": resource.get("backend_type"),
                    "instance_type": resource.get("instance_type"),
                    "region": resource.get("region"),
                    "gce_zone": resource.get("gce_zone"),
                    "state": resource.get("state"),
                    "connection_name": resource.get("connection_name"),
                    "settings": resource.get("settings", {})
                })
                
            elif asset_type == "storage.googleapis.com/Bucket":
                asset.update({
                    "storage_type": "object_storage",
                    "location": resource.get("location"),
                    "location_type": resource.get("location_type"),
                    "storage_class": resource.get("storage_class"),
                    "versioning_enabled": resource.get("versioning_enabled"),
                    "uniform_bucket_level_access": resource.get("uniform_bucket_level_access"),
                    "labels": resource.get("labels", {})
                })
                
            elif asset_type == "container.googleapis.com/Cluster":
                asset.update({
                    "compute_type": "kubernetes_cluster",
                    "location": resource.get("location"),
                    "cluster_status": resource.get("status"),
                    "current_master_version": resource.get("current_master_version"),
                    "current_node_version": resource.get("current_node_version"),
                    "current_node_count": resource.get("current_node_count"),
                    "node_pools": resource.get("node_pools", []),
                    "network": resource.get("network"),
                    "subnetwork": resource.get("subnetwork")
                })
                
            elif asset_type == "cloudfunctions.googleapis.com/CloudFunction":
                asset.update({
                    "compute_type": "serverless_function",
                    "runtime": resource.get("runtime"),
                    "entry_point": resource.get("entry_point"),
                    "available_memory_mb": resource.get("available_memory_mb"),
                    "timeout": resource.get("timeout"),
                    "function_status": resource.get("status"),
                    "labels": resource.get("labels", {})
                })
                
            return asset
            
        except Exception as e:
            self.logger.warning(f"Failed to transform {asset_type} resource to asset: {str(e)}")
            return None
            
    def get_asset_type(self, asset_type: str) -> str:
        """Get normalized asset type for GCP resource"""
        return ASSET_TYPE_MAP.get(asset_type, "infrastructure")
        
    def transform_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GCP Cloud Monitoring metrics to normalized format"""
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
                        "metrics": {}
                    }
                    
                    # Normalize metric names
                    for key, value in metric.items():
                        if key not in ["resource_id", "resource_type", "resource_name", "timestamp"] and value is not None:
                            normalized_metric["metrics"][key] = value
                            
                    normalized_metrics[service].append(normalized_metric)
                    
        return normalized_metrics