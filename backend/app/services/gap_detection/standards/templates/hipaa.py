"""
HIPAA Compliance Standards Template

Health Insurance Portability and Accountability Act requirements for gap detection.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 18
Author: CC (Claude Code)
Reference: HIPAA Security Rule (45 CFR Part 164, Subpart C)
"""

from typing import List, Dict

HIPAA_STANDARDS: List[Dict] = [
    {
        "requirement_type": "database",
        "standard_name": "HIPAA PHI Encryption",
        "description": "Protected Health Information (PHI) must be encrypted at rest and in transit",
        "minimum_requirements": {
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "min_encryption_strength": "AES-256",
        },
        "preferred_patterns": {
            "encryption_algorithm": ["AES-256"],
            "key_rotation_days": 90,
        },
        "constraints": {
            "required_features": ["audit_logging", "access_control", "data_backup"],
        },
        "is_mandatory": True,
        "supported_versions": ["PostgreSQL 12+", "MySQL 8.0+", "SQL Server 2017+"],
        "requirement_details": {
            "hipaa_section": "164.312(a)(2)(iv)",
            "description": "Encryption and Decryption (Addressable)",
            "validation_method": "annual_audit",
        },
    },
    {
        "requirement_type": "access_control",
        "standard_name": "HIPAA Access Control",
        "description": "Implement technical policies and procedures for electronic information systems",
        "minimum_requirements": {
            "unique_user_id": True,
            "automatic_logoff": True,
            "encryption_decryption": True,
        },
        "preferred_patterns": {
            "mfa_enabled": True,
            "session_timeout_minutes": 15,
        },
        "constraints": {
            "password_min_length": 8,
            "password_complexity": True,
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "hipaa_section": "164.312(a)(1)",
            "description": "Access Control (Required)",
            "validation_method": "annual_audit",
        },
    },
    {
        "requirement_type": "logging",
        "standard_name": "HIPAA Audit Controls",
        "description": "Implement hardware, software, and/or procedural mechanisms to record and examine activity",
        "minimum_requirements": {
            "audit_logging_enabled": True,
            "log_retention_years": 6,
            "access_logging": True,
        },
        "preferred_patterns": {
            "centralized_logging": True,
            "tamper_proof_logs": True,
        },
        "constraints": {
            "log_review_frequency": "monthly",
        },
        "is_mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "hipaa_section": "164.312(b)",
            "description": "Audit Controls (Required)",
            "validation_method": "annual_audit",
        },
    },
]


def get_hipaa_standards() -> List[Dict]:
    """Get HIPAA compliance standards for gap detection."""
    return HIPAA_STANDARDS


__all__ = ["HIPAA_STANDARDS", "get_hipaa_standards"]
