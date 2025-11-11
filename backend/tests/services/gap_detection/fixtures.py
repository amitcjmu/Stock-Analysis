"""
Test fixtures for gap detection tests.

Provides mock Asset objects with various states:
- Complete assets (all fields populated)
- Partial assets (some fields missing/empty)
- Empty assets (no fields populated)
"""

from typing import Any, Optional
from unittest.mock import Mock


def create_mock_asset(
    asset_id: str = "asset-123",
    asset_name: str = "Test App",
    technology_stack: Optional[str] = "Python/Django",
    cpu_cores: Optional[int] = 4,
    memory_gb: Optional[int] = 16,
    operating_system: Optional[str] = "Ubuntu 22.04",
    has_enrichments: bool = False,
) -> Any:
    """
    Create a mock Asset with specified attributes.

    Args:
        asset_id: Asset UUID
        asset_name: Asset name
        technology_stack: Technology stack (can be empty string or None)
        cpu_cores: CPU cores (can be None)
        memory_gb: Memory in GB (can be None)
        operating_system: OS version
        has_enrichments: If True, attach mock enrichment relationships

    Returns:
        Mock Asset object with attributes
    """
    asset = Mock()
    asset.id = asset_id
    asset.asset_name = asset_name
    asset.technology_stack = technology_stack
    asset.cpu_cores = cpu_cores
    asset.memory_gb = memory_gb
    asset.operating_system = operating_system

    # System columns (should be excluded from gap analysis)
    asset.created_at = "2025-01-01T00:00:00Z"
    asset.updated_at = "2025-01-01T00:00:00Z"
    asset.client_account_id = "client-123"
    asset.engagement_id = "engagement-456"

    if has_enrichments:
        # Add mock enrichment relationships
        asset.resilience = create_mock_resilience()
        asset.compliance_flags = create_mock_compliance_flags()
        asset.vulnerabilities = None  # Simulate missing enrichment
    else:
        asset.resilience = None
        asset.compliance_flags = None
        asset.vulnerabilities = None

    return asset


def create_mock_resilience(
    rto_minutes: Optional[int] = 60,
    rpo_minutes: Optional[int] = 15,
) -> Any:
    """
    Create a mock AssetResilience enrichment.

    Args:
        rto_minutes: Recovery Time Objective in minutes
        rpo_minutes: Recovery Point Objective in minutes

    Returns:
        Mock AssetResilience object
    """
    resilience = Mock()
    resilience.rto_minutes = rto_minutes
    resilience.rpo_minutes = rpo_minutes
    resilience.sla_json = {"availability": 99.9}
    return resilience


def create_mock_compliance_flags(
    compliance_scopes: Optional[list] = None,
    data_classification: Optional[str] = "confidential",
) -> Any:
    """
    Create a mock AssetComplianceFlags enrichment.

    Args:
        compliance_scopes: List of compliance requirements (e.g., ["PCI-DSS", "HIPAA"])
        data_classification: Data classification level

    Returns:
        Mock AssetComplianceFlags object
    """
    compliance = Mock()
    compliance.compliance_scopes = compliance_scopes or ["PCI-DSS"]
    compliance.data_classification = data_classification
    compliance.residency = "US"
    return compliance


def create_incomplete_resilience() -> Any:
    """
    Create a mock AssetResilience with incomplete fields.

    Returns:
        Mock AssetResilience with None values for critical fields
    """
    resilience = Mock()
    resilience.rto_minutes = None  # Missing critical field
    resilience.rpo_minutes = None  # Missing critical field
    resilience.sla_json = {}
    return resilience
