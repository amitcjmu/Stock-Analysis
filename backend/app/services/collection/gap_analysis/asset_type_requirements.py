"""
Asset Type Specific Requirements for Gap Analysis

This module defines which critical attributes are applicable for each asset type.
Per COLLECTION_FLOW_TWO_CRITICAL_ISSUES.md, gap analysis should only check attributes
that are relevant to the asset's type.

NOTE: 6R strategy-based filtering is NOT implemented here because assessment hasn't
run yet during gap analysis. This only filters by asset type.
"""

from typing import Dict, List, Set

# Import critical attribute names from the base tool
from app.services.crewai_flows.tools.critical_attributes_tool.base import (
    CriticalAttributesDefinition,
)


class AssetTypeRequirements:
    """Defines applicable critical attributes per asset type."""

    # Get all attribute lists from CriticalAttributesDefinition
    ALL_INFRASTRUCTURE = CriticalAttributesDefinition.INFRASTRUCTURE_ATTRIBUTES
    ALL_APPLICATION = CriticalAttributesDefinition.APPLICATION_ATTRIBUTES
    ALL_BUSINESS = CriticalAttributesDefinition.BUSINESS_CONTEXT_ATTRIBUTES
    ALL_TECHNICAL_DEBT = CriticalAttributesDefinition.TECHNICAL_DEBT_ATTRIBUTES

    # Combine all 22 critical attributes
    ALL_CRITICAL_ATTRIBUTES = (
        ALL_INFRASTRUCTURE + ALL_APPLICATION + ALL_BUSINESS + ALL_TECHNICAL_DEBT
    )

    # Asset type specific attribute mappings
    ASSET_TYPE_REQUIREMENTS: Dict[str, Dict[str, List[str]]] = {
        "application": {
            "infrastructure": [
                "operating_system_version",  # Apps run on OS
                "cpu_memory_storage_specs",  # Resource requirements
                "network_configuration",  # Connectivity needs
                "performance_baseline",  # App performance metrics
                "availability_requirements",  # SLA requirements
            ],
            "application": ALL_APPLICATION,  # All app attributes relevant
            "business_context": ALL_BUSINESS,  # All business attributes relevant
            "technical_debt": ALL_TECHNICAL_DEBT,  # All tech debt relevant
        },
        "database": {
            "infrastructure": [
                "operating_system_version",  # DB server OS
                "cpu_memory_storage_specs",  # Resource requirements
                "network_configuration",  # Connectivity
                "performance_baseline",  # Query performance
                "availability_requirements",  # Uptime requirements
            ],
            "application": [
                "technology_stack",  # Database engine (PostgreSQL, MySQL, etc.)
                "architecture_pattern",  # Standalone, clustered, replicated
                "integration_dependencies",  # Apps that connect to this DB
                "data_volume_complexity",  # Database size, table count
                "security_compliance_requirements",  # Data classification
            ],
            "business_context": [
                "business_criticality",  # Mission critical data
                "regulatory_requirements",  # Compliance (GDPR, HIPAA, etc.)
                "data_sensitivity_classification",  # PII, PHI, financial
                "disaster_recovery_needs",  # Backup, replication requirements
            ],
            "technical_debt": [
                "license_dependencies",  # Database licensing
                "version_support_status",  # End of support dates
                "security_vulnerabilities",  # Known CVEs
            ],
        },
        "server": {
            "infrastructure": ALL_INFRASTRUCTURE,  # All infrastructure relevant
            "application": [
                "technology_stack",  # Installed software/services
                "integration_dependencies",  # Services hosted on this server
                "security_compliance_requirements",  # Server hardening
            ],
            "business_context": [
                "business_criticality",  # Server importance
                "disaster_recovery_needs",  # Backup/failover
            ],
            "technical_debt": [
                "license_dependencies",  # OS/software licenses
                "version_support_status",  # OS end of support
                "security_vulnerabilities",  # Patching status
            ],
        },
        "network_device": {
            "infrastructure": [
                "network_configuration",  # Device config, VLANs, routing
                "virtualization_platform",  # Virtual vs physical
                "performance_baseline",  # Throughput, latency
                "availability_requirements",  # Redundancy requirements
            ],
            "application": [
                "technology_stack",  # Device type (router, switch, firewall)
                "integration_dependencies",  # Connected networks/devices
                "security_compliance_requirements",  # Firewall rules, ACLs
            ],
            "business_context": [
                "business_criticality",  # Network importance
                "disaster_recovery_needs",  # Redundancy, failover
            ],
            "technical_debt": [
                "license_dependencies",  # Support contracts
                "version_support_status",  # Firmware end of support
                "security_vulnerabilities",  # Known vulnerabilities
            ],
        },
        "storage": {
            "infrastructure": [
                "cpu_memory_storage_specs",  # Storage capacity, IOPS
                "network_configuration",  # SAN/NAS connectivity
                "virtualization_platform",  # Storage virtualization
                "performance_baseline",  # I/O performance
                "availability_requirements",  # RAID, redundancy
            ],
            "application": [
                "technology_stack",  # Storage type (SAN, NAS, object)
                "integration_dependencies",  # Servers using this storage
                "data_volume_complexity",  # Total capacity, growth rate
                "security_compliance_requirements",  # Encryption
            ],
            "business_context": [
                "business_criticality",  # Data importance
                "data_sensitivity_classification",  # Data classification
                "disaster_recovery_needs",  # Backup, replication
            ],
            "technical_debt": [
                "license_dependencies",  # Support contracts
                "version_support_status",  # End of support
            ],
        },
        "middleware": {
            "infrastructure": [
                "operating_system_version",  # OS middleware runs on
                "cpu_memory_storage_specs",  # Resource requirements
                "network_configuration",  # Connectivity
                "performance_baseline",  # Throughput metrics
                "availability_requirements",  # Clustering, HA
            ],
            "application": [
                "technology_stack",  # Middleware type (app server, message queue)
                "architecture_pattern",  # Standalone, clustered
                "integration_dependencies",  # Apps using this middleware
                "security_compliance_requirements",  # Authentication, encryption
            ],
            "business_context": [
                "business_criticality",  # Middleware importance
                "disaster_recovery_needs",  # Failover capabilities
            ],
            "technical_debt": [
                "license_dependencies",  # Middleware licensing
                "version_support_status",  # End of support
                "security_vulnerabilities",  # Known CVEs
            ],
        },
    }

    @classmethod
    def get_applicable_attributes(cls, asset_type: str) -> List[str]:
        """
        Get list of applicable critical attributes for the given asset type.

        Args:
            asset_type: Type of asset (application, database, server, etc.)

        Returns:
            List of attribute names applicable to this asset type

        Example:
            >>> AssetTypeRequirements.get_applicable_attributes("database")
            ['operating_system_version', 'cpu_memory_storage_specs', ...]
        """
        asset_type_lower = asset_type.lower()

        # Get requirements for this asset type (default to empty if unknown)
        requirements = cls.ASSET_TYPE_REQUIREMENTS.get(asset_type_lower, {})

        if not requirements:
            # Unknown asset type - return all attributes to be safe
            return cls.ALL_CRITICAL_ATTRIBUTES

        # Combine all applicable attributes from all categories
        applicable = []
        for category_attrs in requirements.values():
            applicable.extend(category_attrs)

        # Remove duplicates while preserving order
        seen: Set[str] = set()
        result = []
        for attr in applicable:
            if attr not in seen:
                seen.add(attr)
                result.append(attr)

        return result

    @classmethod
    def get_inapplicable_attributes(cls, asset_type: str) -> List[str]:
        """
        Get list of attributes that should NOT be checked for this asset type.

        Args:
            asset_type: Type of asset (application, database, server, etc.)

        Returns:
            List of attribute names NOT applicable to this asset type

        Example:
            >>> AssetTypeRequirements.get_inapplicable_attributes("database")
            ['user_load_patterns', 'ui_ux_complexity', ...]  # App-only attributes
        """
        applicable = set(cls.get_applicable_attributes(asset_type))
        all_attrs = set(cls.ALL_CRITICAL_ATTRIBUTES)

        # Return attributes in all_attrs that are NOT in applicable
        inapplicable = all_attrs - applicable

        return sorted(list(inapplicable))

    @classmethod
    def is_attribute_applicable(cls, asset_type: str, attribute_name: str) -> bool:
        """
        Check if a specific attribute is applicable for the given asset type.

        Args:
            asset_type: Type of asset (application, database, server, etc.)
            attribute_name: Name of the critical attribute to check

        Returns:
            True if attribute should be checked for this asset type, False otherwise

        Example:
            >>> AssetTypeRequirements.is_attribute_applicable("database", "user_load_patterns")
            False  # Users interact with apps, not databases directly
        """
        applicable = cls.get_applicable_attributes(asset_type)
        return attribute_name in applicable
