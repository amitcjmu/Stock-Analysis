"""
SOC 2 Compliance Standards Template

Service Organization Control 2 requirements for gap detection.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 18
Author: CC (Claude Code)
Reference: SOC 2 Trust Services Criteria (2017)
"""

from typing import List, Dict

SOC2_STANDARDS: List[Dict] = [
    {
        "requirement_type": "security",
        "standard_name": "SOC 2 Security - Logical Access",
        "description": "Logical and physical access controls to protect against threats",
        "minimum_requirements": {
            "mfa_enabled": True,
            "role_based_access": True,
            "access_reviews": "quarterly",
        },
        "preferred_patterns": {
            "least_privilege": True,
            "segregation_of_duties": True,
        },
        "constraints": {
            "password_policy_enforced": True,
            "session_management": True,
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "trust_service_category": "Security",
            "criteria": "CC6.1",
            "description": "Logical and Physical Access Controls",
            "validation_method": "annual_audit",
        },
    },
    {
        "requirement_type": "availability",
        "standard_name": "SOC 2 Availability - System Monitoring",
        "description": "The system is available for operation and use as committed or agreed",
        "minimum_requirements": {
            "uptime_target": 0.99,
            "monitoring_enabled": True,
            "incident_response_plan": True,
        },
        "preferred_patterns": {
            "high_availability": True,
            "disaster_recovery": True,
        },
        "constraints": {
            "backup_frequency": "daily",
            "recovery_time_objective_hours": 4,
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "trust_service_category": "Availability",
            "criteria": "A1.1",
            "description": "The entity maintains, monitors, and evaluates current processing capacity",
            "validation_method": "annual_audit",
        },
    },
    {
        "requirement_type": "processing_integrity",
        "standard_name": "SOC 2 Processing Integrity - Data Quality",
        "description": "System processing is complete, valid, accurate, timely, and authorized",
        "minimum_requirements": {
            "data_validation": True,
            "error_handling": True,
            "transaction_logging": True,
        },
        "preferred_patterns": {
            "automated_validation": True,
            "reconciliation_processes": True,
        },
        "constraints": {
            "validation_frequency": "real_time",
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "trust_service_category": "Processing Integrity",
            "criteria": "PI1.1",
            "description": "Processing is complete, valid, accurate, timely, and authorized",
            "validation_method": "annual_audit",
        },
    },
]


def get_soc2_standards() -> List[Dict]:
    """Get SOC 2 compliance standards for gap detection."""
    return SOC2_STANDARDS


__all__ = ["SOC2_STANDARDS", "get_soc2_standards"]
