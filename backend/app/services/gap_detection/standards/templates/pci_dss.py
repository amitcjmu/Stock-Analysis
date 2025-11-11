"""
PCI-DSS Compliance Standards Template

Payment Card Industry Data Security Standard requirements for gap detection.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 18
Author: CC (Claude Code)
Reference: PCI-DSS v4.0 (March 2022)
"""

from typing import List, Dict

PCI_DSS_STANDARDS: List[Dict] = [
    {
        "requirement_type": "database",
        "standard_name": "PCI-DSS Database Encryption",
        "description": "Databases storing cardholder data must use strong encryption",
        "minimum_requirements": {
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "min_tls_version": "1.2",
        },
        "preferred_patterns": {
            "encryption_algorithm": ["AES-256", "AES-192"],
            "key_management": "HSM",
        },
        "constraints": {
            "prohibited_versions": ["MySQL 5.5", "PostgreSQL 9.6"],
            "required_features": ["audit_logging", "access_control"],
        },
        "is_mandatory": True,
        "supported_versions": ["PostgreSQL 12+", "MySQL 8.0+", "SQL Server 2017+"],
        "requirement_details": {
            "pci_requirement": "3.4",
            "description": "Protect stored cardholder data",
            "validation_method": "quarterly_scan",
        },
    },
    {
        "requirement_type": "network",
        "standard_name": "PCI-DSS Network Segmentation",
        "description": "Cardholder data environment must be segmented from other networks",
        "minimum_requirements": {
            "firewall_enabled": True,
            "network_segmentation": True,
            "dmz_configured": True,
        },
        "preferred_patterns": {
            "firewall_type": ["next_generation", "stateful"],
            "intrusion_detection": True,
        },
        "constraints": {
            "max_network_exposure": "internal_only",
            "required_features": ["network_monitoring", "access_logging"],
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "pci_requirement": "1.2",
            "description": "Build firewall configuration that restricts connections",
            "validation_method": "quarterly_scan",
        },
    },
    {
        "requirement_type": "access_control",
        "standard_name": "PCI-DSS Access Control",
        "description": "Restrict access to cardholder data by business need-to-know",
        "minimum_requirements": {
            "mfa_enabled": True,
            "role_based_access": True,
            "access_logging": True,
        },
        "preferred_patterns": {
            "authentication_method": ["mfa", "certificate"],
            "session_timeout": 15,  # minutes
        },
        "constraints": {
            "max_failed_login_attempts": 6,
            "password_min_length": 12,
            "password_complexity": True,
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "pci_requirement": "7.1",
            "description": "Limit access to system components and cardholder data",
            "validation_method": "quarterly_review",
        },
    },
    {
        "requirement_type": "logging",
        "standard_name": "PCI-DSS Audit Logging",
        "description": "Track and monitor all access to network resources and cardholder data",
        "minimum_requirements": {
            "audit_logging_enabled": True,
            "log_retention_days": 365,
            "centralized_logging": True,
        },
        "preferred_patterns": {
            "siem_integration": True,
            "real_time_alerting": True,
        },
        "constraints": {
            "log_review_frequency": "daily",
            "required_log_fields": ["timestamp", "user_id", "event_type", "result"],
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "pci_requirement": "10.2",
            "description": "Implement automated audit trails for all system components",
            "validation_method": "quarterly_review",
        },
    },
    {
        "requirement_type": "vulnerability_management",
        "standard_name": "PCI-DSS Vulnerability Management",
        "description": "Maintain a vulnerability management program",
        "minimum_requirements": {
            "antivirus_enabled": True,
            "patch_management": True,
            "vulnerability_scanning": "quarterly",
        },
        "preferred_patterns": {
            "automated_patching": True,
            "continuous_monitoring": True,
        },
        "constraints": {
            "max_patch_delay_days": 30,
            "critical_patch_delay_days": 7,
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "pci_requirement": "5.1",
            "description": "Deploy anti-virus software on all systems commonly affected by malicious software",
            "validation_method": "quarterly_scan",
        },
    },
]


def get_pci_dss_standards() -> List[Dict]:
    """
    Get PCI-DSS compliance standards for gap detection.

    Returns:
        List of standard dictionaries compatible with EngagementArchitectureStandard
    """
    return PCI_DSS_STANDARDS


__all__ = ["PCI_DSS_STANDARDS", "get_pci_dss_standards"]
