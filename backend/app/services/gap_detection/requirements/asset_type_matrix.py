"""
Asset Type Requirements Matrix - Data requirements based on asset type.

Defines required data fields, enrichments, and completeness thresholds for:
- Server
- Virtual Machine
- Database
- Application
- Network
- Load Balancer
- Storage
- Container
- Security Group
- Other (default)

Performance: Cached with @lru_cache for <1ms lookups

Reference: /backend/app/services/collection/critical_attributes.py for attribute patterns
"""

from typing import Any, Dict

ASSET_TYPE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "server": {
        "required_columns": [
            "asset_name",
            "operating_system",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            "environment",
        ],
        "required_enrichments": ["resilience"],
        "required_jsonb_keys": {"custom_attributes": ["environment", "vm_type"]},
        "priority_weights": {
            "columns": 0.50,
            "enrichments": 0.30,
            "jsonb": 0.15,
            "application": 0.00,
            "standards": 0.05,
        },
        "completeness_threshold": 0.75,
    },
    "virtual_machine": {
        "required_columns": [
            "asset_name",
            "operating_system",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            "environment",
        ],
        "required_enrichments": ["resilience"],
        "required_jsonb_keys": {
            "custom_attributes": ["environment", "vm_type", "virtualization_platform"]
        },
        "priority_weights": {
            "columns": 0.50,
            "enrichments": 0.30,
            "jsonb": 0.15,
            "application": 0.00,
            "standards": 0.05,
        },
        "completeness_threshold": 0.75,
    },
    "database": {
        "required_columns": [
            "asset_name",
            "technology_stack",
            "storage_gb",
            "memory_gb",
            "business_criticality",
        ],
        "required_enrichments": ["resilience", "compliance_flags"],
        "required_jsonb_keys": {
            "custom_attributes": ["backup_retention_days"],
            "technical_details": ["replication_strategy"],
        },
        "priority_weights": {
            "columns": 0.40,
            "enrichments": 0.40,
            "jsonb": 0.15,
            "application": 0.00,
            "standards": 0.05,
        },
        "completeness_threshold": 0.80,
    },
    "application": {
        "required_columns": [
            "asset_name",
            "technology_stack",
            "architecture_pattern",
            "business_criticality",
        ],
        "required_enrichments": ["resilience", "compliance_flags", "tech_debt"],
        "required_jsonb_keys": {
            "technical_details": ["api_endpoints", "dependencies"],
        },
        "priority_weights": {
            "columns": 0.30,
            "enrichments": 0.30,
            "jsonb": 0.20,
            "application": 0.15,
            "standards": 0.05,
        },
        "completeness_threshold": 0.75,
    },
    "network": {
        "required_columns": [
            "asset_name",
            "ip_address",
            "fqdn",
            "environment",
        ],
        "required_enrichments": ["resilience"],
        "required_jsonb_keys": {
            "custom_attributes": ["network_zone", "firewall_rules"],
            "technical_details": ["port_configuration"],
        },
        "priority_weights": {
            "columns": 0.50,
            "enrichments": 0.20,
            "jsonb": 0.25,
            "application": 0.00,
            "standards": 0.05,
        },
        "completeness_threshold": 0.70,
    },
    "load_balancer": {
        "required_columns": [
            "asset_name",
            "ip_address",
            "environment",
        ],
        "required_enrichments": ["resilience", "performance_metrics"],
        "required_jsonb_keys": {
            "custom_attributes": ["load_balancing_algorithm"],
            "technical_details": ["backend_pools", "health_check_config"],
        },
        "priority_weights": {
            "columns": 0.40,
            "enrichments": 0.30,
            "jsonb": 0.25,
            "application": 0.00,
            "standards": 0.05,
        },
        "completeness_threshold": 0.70,
    },
    "storage": {
        "required_columns": [
            "asset_name",
            "storage_gb",
            "environment",
        ],
        "required_enrichments": ["resilience"],
        "required_jsonb_keys": {
            "custom_attributes": ["storage_type", "iops_provisioned"],
            "technical_details": ["backup_strategy"],
        },
        "priority_weights": {
            "columns": 0.50,
            "enrichments": 0.25,
            "jsonb": 0.20,
            "application": 0.00,
            "standards": 0.05,
        },
        "completeness_threshold": 0.70,
    },
    "container": {
        "required_columns": [
            "asset_name",
            "technology_stack",
            "environment",
        ],
        "required_enrichments": ["resilience", "vulnerabilities"],
        "required_jsonb_keys": {
            "custom_attributes": ["container_runtime", "orchestration_platform"],
            "technical_details": ["image_registry", "resource_limits"],
        },
        "priority_weights": {
            "columns": 0.35,
            "enrichments": 0.35,
            "jsonb": 0.20,
            "application": 0.05,
            "standards": 0.05,
        },
        "completeness_threshold": 0.75,
    },
    "security_group": {
        "required_columns": [
            "asset_name",
            "environment",
        ],
        "required_enrichments": ["compliance_flags"],
        "required_jsonb_keys": {
            "custom_attributes": ["security_rules"],
            "technical_details": ["inbound_rules", "outbound_rules"],
        },
        "priority_weights": {
            "columns": 0.30,
            "enrichments": 0.30,
            "jsonb": 0.35,
            "application": 0.00,
            "standards": 0.05,
        },
        "completeness_threshold": 0.80,
    },
    # Default for unknown asset types
    "other": {
        "required_columns": [
            "asset_name",
            "environment",
        ],
        "required_enrichments": [],
        "required_jsonb_keys": {},
        "priority_weights": {
            "columns": 0.60,
            "enrichments": 0.20,
            "jsonb": 0.15,
            "application": 0.00,
            "standards": 0.05,
        },
        "completeness_threshold": 0.60,
    },
}
