"""
Data models for multi-tenant memory management
"""

from dataclasses import dataclass
from typing import List


@dataclass
class LearningDataClassification:
    """Classification of learning data for privacy compliance"""

    sensitivity_level: str  # "public", "internal", "confidential", "restricted"
    data_categories: List[
        str
    ]  # ["field_patterns", "asset_classification", "dependencies"]
    retention_period: int  # Days
    encryption_required: bool
    audit_required: bool
    cross_tenant_sharing_allowed: bool
