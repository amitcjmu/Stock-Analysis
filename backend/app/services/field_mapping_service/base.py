"""
Base classes, dataclasses, and constants for field mapping service.

This module contains the core data structures and constants used across
all field mapping functionality.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)


@dataclass
class MappingAnalysis:
    """Result of field mapping analysis"""

    mapped_fields: Dict[str, str]
    unmapped_fields: List[str]
    suggested_mappings: Dict[str, List[str]]
    confidence_scores: Dict[str, float]
    missing_required_fields: List[str]
    overall_confidence: float


@dataclass
class MappingRule:
    """Field mapping rule with metadata"""

    source_field: str
    target_field: str
    confidence: float
    source: str  # 'learned', 'base', 'user', 'ai'
    context: Optional[str] = None
    created_at: Optional[datetime] = None


# Base mappings for common field variations
BASE_MAPPINGS = {
    "hostname": [
        "host_name",
        "server_name",
        "machine_name",
        "computer_name",
        "fqdn",
    ],
    "ip_address": ["ip", "ip_addr", "ipv4", "ipv6", "network_address"],
    "asset_name": ["name", "asset", "resource_name", "display_name"],
    "asset_type": ["type", "resource_type", "category", "asset_category"],
    "environment": ["env", "stage", "deployment_env", "environment_type"],
    "business_owner": [
        "owner",
        "business_contact",
        "responsible_party",
        "app_owner",
    ],
    "department": ["dept", "division", "business_unit", "org_unit"],
    "operating_system": ["os", "os_name", "os_version", "platform"],
    "cpu_cores": ["cpu", "cores", "vcpu", "processors", "cpu_count"],
    "memory_gb": ["ram", "memory", "ram_gb", "total_memory", "mem_size"],
    "storage_gb": ["disk", "storage", "disk_size", "total_storage", "disk_gb"],
    "location": ["datacenter", "site", "region", "dc", "data_center"],
    "status": ["state", "operational_status", "current_status"],
    "criticality": ["priority", "importance", "critical_level", "tier"],
}

# Required fields for different asset types
REQUIRED_FIELDS = {
    "server": [
        "hostname",
        "asset_name",
        "asset_type",
        "environment",
        "operating_system",
    ],
    "application": ["asset_name", "asset_type", "environment", "business_owner"],
    "database": ["asset_name", "asset_type", "environment", "database_type"],
    "network": ["asset_name", "asset_type", "ip_address", "location"],
    "storage": ["asset_name", "asset_type", "capacity", "location"],
}

# Field validation patterns
VALIDATION_PATTERNS = {
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "ip_address": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    "hostname": r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$",
}

# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "HIGH": 0.9,
    "MEDIUM": 0.7,
    "LOW": 0.5,
    "MINIMUM": 0.3,
}

# Maximum items for suggestions and validation
MAX_SUGGESTIONS = 3
MAX_VALIDATION_SAMPLES = 5
MAX_ISSUES_REPORTED = 3

# Cache and performance settings
CACHE_TTL_SECONDS = 300  # 5 minutes
MAX_CACHE_SIZE = 1000
