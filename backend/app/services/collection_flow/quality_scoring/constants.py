"""
Quality Scoring Constants

This module contains constants used for quality scoring and confidence assessment.
"""

from app.services.collection_flow.data_transformation import DataType


# Required fields by data type
REQUIRED_FIELDS = {
    DataType.SERVER: {
        "critical": ["hostname", "ip_address", "operating_system"],
        "important": ["cpu_count", "memory_gb", "status", "environment"],
        "optional": ["serial_number", "model", "manufacturer", "location"]
    },
    DataType.APPLICATION: {
        "critical": ["app_name", "version", "status"],
        "important": ["environment", "owner", "technology"],
        "optional": ["url", "port", "criticality"]
    },
    DataType.DATABASE: {
        "critical": ["db_name", "db_type", "host"],
        "important": ["version", "port", "size_gb", "status"],
        "optional": ["connection_string", "backup_schedule"]
    }
}

# Field validation rules
VALIDATION_RULES = {
    "hostname": {
        "pattern": r"^[a-zA-Z0-9\-\.]+$",
        "max_length": 255
    },
    "ip_address": {
        "pattern": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
        "validator": "ip_address"
    },
    "port": {
        "type": "integer",
        "min": 1,
        "max": 65535
    },
    "memory_gb": {
        "type": "numeric",
        "min": 0
    },
    "cpu_count": {
        "type": "integer",
        "min": 1
    }
}

# Source reliability scores
SOURCE_RELIABILITY = {
    "api": 0.95,
    "automated_script": 0.85,
    "export": 0.75,
    "manual_entry": 0.60,
    "template": 0.50
}

# Platform confidence multipliers
PLATFORM_CONFIDENCE = {
    "servicenow": 0.95,
    "vmware_vcenter": 0.90,
    "aws": 0.95,
    "azure": 0.95,
    "excel": 0.60,
    "manual": 0.50
}

# Dimension weights for overall score calculation
DIMENSION_WEIGHTS = {
    "completeness": 0.25,
    "accuracy": 0.25,
    "consistency": 0.15,
    "timeliness": 0.15,
    "validity": 0.10,
    "uniqueness": 0.10
}

# Confidence factor weights
CONFIDENCE_WEIGHTS = {
    "source_reliability": 0.30,
    "collection_method": 0.25,
    "data_quality": 0.30,
    "validation": 0.10,
    "historical_accuracy": 0.05
}

# Automation tier confidence mapping
TIER_CONFIDENCE = {
    "tier_4": 0.90,
    "tier_3": 0.75,
    "tier_2": 0.60,
    "tier_1": 0.45
}