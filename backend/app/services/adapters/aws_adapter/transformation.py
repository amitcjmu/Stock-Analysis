"""
AWS Data Transformation Module
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transformer for AWS data to normalized format"""

    def __init__(self, region: str):
        self._region = region

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw AWS data to normalized format for Discovery Flow

        Args:
            raw_data: Raw AWS data from collection

        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        try:
            normalized_data = {
                "platform": "AWS",
                "platform_version": "1.0",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
                "metadata": raw_data.get("metadata", {}),
            }

            # Transform each service's resources to normalized assets
            for service, service_data in raw_data.items():
                if service == "metadata" or "error" in service_data:
                    continue

                if "resources" in service_data:
                    for resource in service_data["resources"]:
                        normalized_asset = self._transform_resource_to_asset(
                            service, resource
                        )
                        if normalized_asset:
                            normalized_data["assets"].append(normalized_asset)

            # Transform performance metrics
            if "metrics" in raw_data:
                normalized_data["performance_metrics"] = self._transform_metrics(
                    raw_data["metrics"]
                )

            # Transform configuration data
            if "configuration" in raw_data:
                normalized_data["configuration"] = raw_data["configuration"]

            logger.info(
                f"Transformed {len(normalized_data['assets'])} AWS assets to normalized format"
            )

            return normalized_data

        except Exception as e:
            logger.error(f"Failed to transform AWS data: {str(e)}")
            return {
                "platform": "AWS",
                "error": f"Data transformation failed: {str(e)}",
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
            }

    def _transform_resource_to_asset(
        self, service: str, resource: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Transform AWS resource to normalized asset format"""
        try:
            # Common asset structure
            asset = {
                "platform": "AWS",
                "platform_service": service,
                "asset_type": self._get_asset_type(service, resource),
                "unique_id": self._get_resource_unique_id(service, resource),
                "name": self._get_resource_name(service, resource),
                "environment": "cloud",
                "region": self._region,
                "tags": resource.get("tags", {}),
                "discovery_method": "automated",
                "discovery_timestamp": datetime.utcnow().isoformat(),
                "raw_data": resource,
            }

            # Service-specific transformations
            if service == "EC2":
                asset.update(
                    {
                        "compute_type": "virtual_machine",
                        "instance_type": resource.get("instance_type"),
                        "state": resource.get("state"),
                        "ip_addresses": {
                            "private": resource.get("private_ip"),
                            "public": resource.get("public_ip"),
                        },
                        "network": {
                            "vpc_id": resource.get("vpc_id"),
                            "subnet_id": resource.get("subnet_id"),
                            "security_groups": resource.get("security_groups", []),
                        },
                        "operating_system": resource.get("platform", "linux"),
                        "architecture": resource.get("architecture"),
                    }
                )

            elif service == "RDS":
                asset.update(
                    {
                        "database_type": resource.get("engine"),
                        "database_version": resource.get("engine_version"),
                        "instance_class": resource.get("db_instance_class"),
                        "storage": {
                            "allocated": resource.get("allocated_storage"),
                            "type": resource.get("storage_type"),
                        },
                        "multi_az": resource.get("multi_az"),
                        "endpoint": resource.get("endpoint", {}),
                    }
                )

            elif service == "Lambda":
                asset.update(
                    {
                        "compute_type": "serverless_function",
                        "runtime": resource.get("runtime"),
                        "memory_size": resource.get("memory_size"),
                        "timeout": resource.get("timeout"),
                        "code_size": resource.get("code_size"),
                    }
                )

            return asset

        except Exception as e:
            logger.warning(f"Failed to transform {service} resource to asset: {str(e)}")
            return None

    def _get_asset_type(self, service: str, resource: Dict[str, Any]) -> str:
        """Get normalized asset type for AWS resource"""
        type_map = {
            "EC2": "server",
            "RDS": "database",
            "Lambda": "application",
            "ELB": "load_balancer",
            "ELBv2": "load_balancer",
            "ECS": "container_service",
            "EKS": "kubernetes_cluster",
            "ElastiCache": "cache",
            "Redshift": "data_warehouse",
            "DynamoDB": "nosql_database",
            "S3": "storage",
        }
        return type_map.get(service, "infrastructure")

    def _get_resource_unique_id(self, service: str, resource: Dict[str, Any]) -> str:
        """Get unique identifier for AWS resource"""
        id_fields = {
            "EC2": "instance_id",
            "RDS": "db_instance_identifier",
            "Lambda": "function_arn",
            "ELB": "load_balancer_name",
            "ELBv2": "load_balancer_arn",
            "ECS": "cluster_arn",
            "EKS": "cluster_arn",
            "ElastiCache": "cache_cluster_id",
            "Redshift": "cluster_identifier",
            "DynamoDB": "table_arn",
            "S3": "bucket_name",
        }

        field = id_fields.get(service, "id")
        return resource.get(field, f"unknown-{service}-{id(resource)}")

    def _get_resource_name(self, service: str, resource: Dict[str, Any]) -> str:
        """Get display name for AWS resource"""
        name_fields = {
            "EC2": ["instance_id", "tags.Name"],
            "RDS": ["db_instance_identifier"],
            "Lambda": ["function_name"],
            "ELB": ["load_balancer_name"],
            "ELBv2": ["load_balancer_name"],
            "ECS": ["cluster_name"],
            "EKS": ["cluster_name"],
            "ElastiCache": ["cache_cluster_id"],
            "Redshift": ["cluster_identifier"],
            "DynamoDB": ["table_name"],
            "S3": ["bucket_name"],
        }

        fields = name_fields.get(service, ["id"])
        for field in fields:
            if "." in field:
                # Handle nested fields like tags.Name
                parts = field.split(".")
                value = resource
                for part in parts:
                    value = value.get(part, {}) if isinstance(value, dict) else {}
                if value:
                    return str(value)
            else:
                value = resource.get(field)
                if value:
                    return str(value)

        return f"Unknown {service} Resource"

    def _transform_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AWS CloudWatch metrics to normalized format"""
        normalized_metrics = {}

        for service, service_metrics in metrics_data.items():
            if isinstance(service_metrics, list):
                normalized_metrics[service] = []
                for metric in service_metrics:
                    normalized_metric = {
                        "resource_id": metric.get("resource_id"),
                        "resource_type": metric.get("resource_type"),
                        "timestamp": metric.get("timestamp"),
                        "metrics": {},
                    }

                    # Normalize metric names
                    for key, value in metric.items():
                        if (
                            key not in ["resource_id", "resource_type", "timestamp"]
                            and value is not None
                        ):
                            normalized_metric["metrics"][key] = value

                    normalized_metrics[service].append(normalized_metric)

        return normalized_metrics
