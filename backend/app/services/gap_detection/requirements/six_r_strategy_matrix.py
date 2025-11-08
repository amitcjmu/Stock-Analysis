"""
6R Strategy Requirements Matrix - Data requirements based on migration strategy.

Defines required data fields, enrichments, and completeness thresholds for:
- Rehost
- Replatform
- Refactor
- Repurchase
- Retire
- Retain

Performance: Cached with @lru_cache for <1ms lookups

Reference: /backend/app/services/collection/critical_attributes.py for attribute patterns
"""

from typing import Any, Dict

SIX_R_STRATEGY_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "rehost": {
        "required_columns": [
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            "operating_system",
        ],
        "required_enrichments": ["resilience", "performance_metrics"],
        "required_jsonb_keys": {
            "custom_attributes": [
                "cpu_utilization_baseline",
                "memory_utilization_baseline",
            ]
        },
        "priority_weights": {
            "columns": 0.45,
            "enrichments": 0.35,
        },
    },
    "replatform": {
        "required_columns": [
            "technology_stack",
            "architecture_pattern",
            "dependencies",
        ],
        "required_enrichments": ["tech_debt", "dependencies"],
        "required_jsonb_keys": {
            "technical_details": ["compatibility_assessment", "platform_dependencies"]
        },
        "priority_weights": {
            "columns": 0.35,
            "enrichments": 0.40,
            "jsonb": 0.20,
        },
    },
    "refactor": {
        "required_columns": [
            "technology_stack",
            "architecture_pattern",
            "code_quality",
        ],
        "required_enrichments": ["tech_debt", "vulnerabilities"],
        "required_jsonb_keys": {
            "technical_details": ["refactoring_scope", "technical_debt_items"]
        },
        "priority_weights": {
            "columns": 0.30,
            "enrichments": 0.45,
            "jsonb": 0.20,
        },
        "completeness_threshold": 0.85,  # Higher bar for refactor
    },
    "repurchase": {
        "required_columns": [
            "technology_stack",
            "business_criticality",
        ],
        "required_enrichments": ["cost_optimization"],
        "required_jsonb_keys": {
            "custom_attributes": ["current_licensing_cost"],
            "technical_details": ["saas_alternatives"],
        },
        "priority_weights": {
            "columns": 0.30,
            "enrichments": 0.25,
            "jsonb": 0.40,
        },
    },
    "retire": {
        "required_columns": [
            "asset_name",
            "business_criticality",
        ],
        "required_enrichments": ["dependencies"],
        "required_jsonb_keys": {
            "custom_attributes": ["retirement_justification"],
        },
        "priority_weights": {
            "columns": 0.40,
            "enrichments": 0.35,
            "jsonb": 0.20,
        },
        "completeness_threshold": 0.60,  # Lower bar for retire
    },
    "retain": {
        "required_columns": [
            "asset_name",
            "business_criticality",
            "compliance",
        ],
        "required_enrichments": ["compliance_flags"],
        "required_jsonb_keys": {
            "custom_attributes": ["retention_justification"],
        },
        "priority_weights": {
            "columns": 0.40,
            "enrichments": 0.30,
            "jsonb": 0.25,
        },
    },
}
