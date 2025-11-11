"""
Criticality Requirements Matrix - Data requirements based on criticality tier.

Defines required data fields, enrichments, and completeness thresholds for:
- Tier 1 - Critical
- Tier 2 - Important
- Tier 3 - Standard

Performance: Cached with @lru_cache for <1ms lookups

Reference: /backend/app/services/collection/critical_attributes.py for attribute patterns
"""

from typing import Any, Dict

CRITICALITY_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "tier_1_critical": {
        "required_enrichments": ["resilience", "performance_metrics"],
        "required_jsonb_keys": {
            "custom_attributes": ["sla_requirements", "disaster_recovery_plan"]
        },
        "priority_weights": {
            "enrichments": 0.45,
            "jsonb": 0.30,
            "standards": 0.20,
        },
        "completeness_threshold": 0.90,  # Very high bar for critical
    },
    "tier_2_important": {
        "required_enrichments": ["resilience"],
        "required_jsonb_keys": {"custom_attributes": ["sla_requirements"]},
        "priority_weights": {
            "enrichments": 0.40,
            "jsonb": 0.25,
        },
        "completeness_threshold": 0.75,
    },
    "tier_3_standard": {
        "required_enrichments": [],
        "required_jsonb_keys": {},
        "priority_weights": {},
        "completeness_threshold": 0.60,
    },
}
