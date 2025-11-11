"""
Compliance Requirements Matrix - Data requirements based on compliance framework.

Defines required data fields, enrichments, and completeness thresholds for:
- PCI-DSS
- HIPAA
- SOC2
- GDPR
- ISO27001

Performance: Cached with @lru_cache for <1ms lookups

Reference: /backend/app/services/collection/critical_attributes.py for attribute patterns
"""

from typing import Any, Dict

COMPLIANCE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "PCI-DSS": {
        "required_enrichments": ["compliance_flags", "vulnerabilities"],
        "required_jsonb_keys": {
            "technical_details": [
                "encryption_at_rest",
                "encryption_in_transit",
                "network_segmentation",
            ]
        },
        "required_standards": [
            "Encryption at Rest",
            "Network Segmentation",
            "Access Control",
            "Security Logging",
        ],
        "priority_weights": {
            "enrichments": 0.40,
            "jsonb": 0.30,
            "standards": 0.25,
        },
        "completeness_threshold": 0.90,  # Very high bar for PCI
    },
    "HIPAA": {
        "required_enrichments": ["compliance_flags", "vulnerabilities"],
        "required_jsonb_keys": {
            "technical_details": [
                "phi_data_handling",
                "audit_logging",
                "access_controls",
            ]
        },
        "required_standards": [
            "PHI Data Encryption",
            "Audit Logging",
            "Access Control",
            "Data Retention Policy",
        ],
        "priority_weights": {
            "enrichments": 0.40,
            "jsonb": 0.30,
            "standards": 0.25,
        },
        "completeness_threshold": 0.90,  # Very high bar for HIPAA
    },
    "SOC2": {
        "required_enrichments": ["compliance_flags"],
        "required_jsonb_keys": {
            "technical_details": [
                "change_management_process",
                "incident_response_plan",
            ]
        },
        "required_standards": [
            "Change Management",
            "Incident Response",
            "Monitoring and Logging",
        ],
        "priority_weights": {
            "enrichments": 0.35,
            "jsonb": 0.35,
            "standards": 0.25,
        },
        "completeness_threshold": 0.85,
    },
    "GDPR": {
        "required_enrichments": ["compliance_flags"],
        "required_jsonb_keys": {
            "technical_details": [
                "pii_data_handling",
                "data_retention_policy",
                "right_to_be_forgotten_compliance",
            ]
        },
        "required_standards": [
            "Data Privacy",
            "Data Retention",
            "Data Subject Rights",
        ],
        "priority_weights": {
            "enrichments": 0.35,
            "jsonb": 0.35,
            "standards": 0.25,
        },
        "completeness_threshold": 0.85,
    },
    "ISO27001": {
        "required_enrichments": ["compliance_flags", "vulnerabilities"],
        "required_jsonb_keys": {
            "technical_details": [
                "risk_assessment",
                "security_controls",
            ]
        },
        "required_standards": [
            "Risk Management",
            "Information Security Controls",
            "Continuous Monitoring",
        ],
        "priority_weights": {
            "enrichments": 0.40,
            "jsonb": 0.30,
            "standards": 0.25,
        },
        "completeness_threshold": 0.85,
    },
}
