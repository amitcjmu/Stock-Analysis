"""
Critical Attributes Definition for 6R Migration Decision Making

This module defines the 22 critical attributes required for accurate
6R strategy decisions. These attributes are used by the programmatic
gap scanner to identify missing data.

IMPORTANT: These attribute keys MUST match the keys in:
/backend/app/services/crewai_flows/tools/critical_attributes_tool/base.py

If keys don't match, questionnaire generation will produce 0 questions.
Last synchronized: 2025-10-22 (Bug #728 fix)
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CriticalAttributesDefinition:
    """
    Defines the 22 critical attributes for migration assessment.

    Categories:
    - Infrastructure (6): Hardware/platform details
    - Application (4): Software architecture and data
    - Business (4): Business context and compliance
    - Technical Debt (4): Code quality and maintenance
    - Dependencies (4): Integrations and relationships
    """

    @staticmethod
    def get_attribute_mapping() -> Dict[str, Any]:
        """
        Returns mapping of the 22 critical attributes to asset fields.

        IMPORTANT: Keys MUST match crewai_flows/tools/critical_attributes_tool/base.py
        for questionnaire generation to work correctly (Bug #728).

        Returns:
            Dict with attribute name as key and config as value:
            {
                "attribute_name": {
                    "category": "infrastructure|application|business|technical_debt",
                    "priority": 1-4,  # 1=critical, 4=low
                    "asset_fields": ["field_name", "custom_attributes.field"],
                    "description": "What this attribute represents",
                    "required": True/False  # Optional
                }
            }
        """
        return {
            # ==========================================
            # Infrastructure Attributes (6)
            # ==========================================
            "operating_system_version": {
                "category": "infrastructure",
                "priority": 1,
                "asset_fields": [
                    "operating_system",
                    "os_version",
                    "custom_attributes.os",
                ],
                "description": "Operating system type and version",
                "required": True,
            },
            "cpu_memory_storage_specs": {
                "category": "infrastructure",
                "priority": 1,
                "asset_fields": [
                    "cpu_cores",
                    "memory_gb",
                    "storage_gb",
                    "cpu_info",
                    "custom_attributes.cpu_cores",
                    "custom_attributes.memory",
                    "custom_attributes.storage",
                    "custom_attributes.cpu_architecture",
                ],
                "description": "CPU cores, memory, and storage specifications",
                "required": True,
            },
            "network_configuration": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": [
                    "ip_address",
                    "fqdn",
                    "mac_address",
                    "network_config",
                    "custom_attributes.network",
                ],
                "description": "Network settings and connectivity",
                "required": False,
            },
            "virtualization_platform": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": [
                    "virtualization",
                    "custom_attributes.vm_type",
                    "custom_attributes.virtualization_platform",
                ],
                "description": "Virtualization platform (VMware, Hyper-V, KVM, etc.)",
                "required": False,
            },
            "performance_baseline": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": [
                    "cpu_utilization_percent",
                    "memory_utilization_percent",
                    "disk_iops",
                    "network_throughput_mbps",
                ],
                "description": "Performance baseline metrics (utilization, IOPS, throughput)",
                "required": False,
            },
            "availability_requirements": {
                "category": "infrastructure",
                "priority": 1,
                "asset_fields": [
                    "environment",
                    "custom_attributes.environment",
                    "custom_attributes.availability_requirements",
                    "resilience.rto_minutes",  # PHASE 2 Bug #679
                    "resilience.rpo_minutes",  # PHASE 2 Bug #679
                ],
                "description": "Availability requirements (SLA, uptime, RTO, RPO)",
                "required": True,
            },
            # ==========================================
            # Application Attributes (8)
            # ==========================================
            "technology_stack": {
                "category": "application",
                "priority": 1,
                "asset_fields": [
                    "technology_stack",
                    "custom_attributes.tech_stack",
                ],
                "description": "Programming languages, frameworks, runtime environment",
                "required": True,
            },
            "architecture_pattern": {
                "category": "application",
                "priority": 1,
                "asset_fields": [
                    "architecture_pattern",
                    "custom_attributes.architecture",
                    "custom_attributes.architecture_pattern",
                ],
                "description": "Architecture pattern (monolithic, microservices, N-tier)",
                "required": True,
            },
            "integration_dependencies": {
                "category": "application",
                "priority": 1,
                "asset_fields": [
                    "dependencies",
                    "related_assets",
                    "integrations",
                    "custom_attributes.integrations",
                    "custom_attributes.upstream_deps",
                ],
                "description": "Integration points, dependencies, and API connections",
                "required": True,
            },
            "data_volume_characteristics": {
                "category": "application",
                "priority": 2,
                "asset_fields": [
                    "data_size_gb",
                    "custom_attributes.data_volume",
                ],
                "description": "Data volume and growth characteristics",
                "required": False,
            },
            "user_load_patterns": {
                "category": "application",
                "priority": 2,
                "asset_fields": [
                    "user_count",
                    "custom_attributes.user_load",
                    "custom_attributes.stakeholder_count",
                ],
                "description": "User load patterns, concurrent users, traffic characteristics",
                "required": False,
            },
            "business_logic_complexity": {
                "category": "application",
                "priority": 1,
                "asset_fields": [
                    "custom_attributes.complexity",
                ],
                "description": "Business logic complexity, workflow complexity",
                "required": True,
            },
            "configuration_complexity": {
                "category": "application",
                "priority": 2,
                "asset_fields": [
                    "custom_attributes.config_complexity",
                ],
                "description": "Configuration complexity (environment variables, settings)",
                "required": False,
            },
            "security_compliance_requirements": {
                "category": "application",
                "priority": 1,
                "asset_fields": [
                    "compliance",
                    "custom_attributes.compliance",
                    "custom_attributes.compliance_requirements",
                    "compliance_flags.compliance_scopes",  # PHASE 2 Bug #679
                ],
                "description": "Security and compliance requirements (PCI, HIPAA, GDPR, SOX)",
                "required": True,
            },
            # ==========================================
            # Business Context Attributes (4)
            # ==========================================
            "business_criticality_score": {
                "category": "business",
                "priority": 1,
                "asset_fields": [
                    "business_criticality",
                    "criticality",
                ],
                "description": "Business criticality score (critical, high, medium, low)",
                "required": True,
            },
            "change_tolerance": {
                "category": "business",
                "priority": 1,
                "asset_fields": [
                    "risk_tolerance",
                    "custom_attributes.change_tolerance",
                ],
                "description": "Tolerance for change, maintenance windows, flexibility",
                "required": False,
            },
            "compliance_constraints": {
                "category": "business",
                "priority": 1,
                "asset_fields": [
                    "compliance",
                    "custom_attributes.compliance_requirements",
                    "custom_attributes.compliance_constraints",
                    "compliance_flags.compliance_scopes",  # PHASE 2 Bug #679
                ],
                "description": "Regulatory and compliance constraints",
                "required": True,
            },
            "stakeholder_impact": {
                "category": "business",
                "priority": 1,
                "asset_fields": [
                    "business_owner",
                    "technical_owner",
                    "department",
                    "user_count",
                    "custom_attributes.stakeholder_count",
                ],
                "description": "Stakeholder impact (owners, departments, affected users)",
                "required": True,
            },
            # ==========================================
            # Technical Debt Attributes (4)
            # ==========================================
            "code_quality_metrics": {
                "category": "technical_debt",
                "priority": 2,
                "asset_fields": [
                    "code_quality",
                    "custom_attributes.code_quality_score",
                    "custom_attributes.code_quality",
                ],
                "description": "Code quality metrics (technical debt, code coverage)",
                "required": False,
            },
            "security_vulnerabilities": {
                "category": "technical_debt",
                "priority": 1,
                "asset_fields": [
                    "security_issues",
                    "custom_attributes.vulnerabilities",
                    "vulnerabilities.cve_id",  # PHASE 2 Bug #679
                    "vulnerabilities.severity",  # PHASE 2 Bug #679
                ],
                "description": "Known security vulnerabilities (CVEs, security issues)",
                "required": True,
            },
            "eol_technology_assessment": {
                "category": "technical_debt",
                "priority": 1,
                "asset_fields": [
                    "eol_tech",
                    "custom_attributes.eol_components",
                    "custom_attributes.eol_assessment",
                ],
                "description": "End-of-life technology assessment (deprecated, obsolete)",
                "required": True,
            },
            "documentation_quality": {
                "category": "technical_debt",
                "priority": 3,
                "asset_fields": [
                    "documentation",
                    "custom_attributes.documentation_quality",
                ],
                "description": "Quality of technical documentation (runbooks, wikis, README)",
                "required": False,
            },
        }

    @staticmethod
    def get_attributes_by_category(category: str) -> Dict[str, Any]:
        """Get all attributes for a specific category."""
        all_attrs = CriticalAttributesDefinition.get_attribute_mapping()
        return {
            name: config
            for name, config in all_attrs.items()
            if config["category"] == category
        }

    @staticmethod
    def get_attributes_by_priority(priority: int) -> Dict[str, Any]:
        """Get all attributes with a specific priority level."""
        all_attrs = CriticalAttributesDefinition.get_attribute_mapping()
        return {
            name: config
            for name, config in all_attrs.items()
            if config["priority"] == priority
        }

    @staticmethod
    def get_critical_attributes() -> Dict[str, Any]:
        """Get only priority 1 (critical) attributes."""
        return CriticalAttributesDefinition.get_attributes_by_priority(1)

    @staticmethod
    def get_attributes_by_asset_type(asset_type: str) -> Dict[str, Any]:
        """
        Get attributes relevant for a specific asset type.

        Asset-type-aware filtering ensures that only applicable attributes
        are checked for each asset type, preventing irrelevant gaps.

        Args:
            asset_type: Asset type from AssetType enum
                       (server, application, database, etc.)

        Returns:
            Dict of attribute name to config for the given asset type

        Examples:
            - server: infrastructure + operational attributes
            - application: application + business + technical_debt attributes
            - database: dependencies + infrastructure (storage-heavy) attributes
        """
        all_attrs = CriticalAttributesDefinition.get_attribute_mapping()

        # Normalize asset type to lowercase for comparison
        asset_type_lower = asset_type.lower() if asset_type else "other"

        # Define asset type to category mappings
        # Each asset type gets a set of relevant attribute categories
        asset_type_mappings = {
            "server": {
                "categories": ["infrastructure"],
                "excluded_attrs": [
                    "technology_stack",
                    "architecture_pattern",
                    "integration_dependencies",
                    "code_quality_metrics",
                    "eol_technology_assessment",
                    "documentation_quality",
                ],
            },
            "virtual_machine": {
                "categories": ["infrastructure"],
                "excluded_attrs": [
                    "technology_stack",
                    "architecture_pattern",
                    "integration_dependencies",
                    "code_quality_metrics",
                    "eol_technology_assessment",
                    "documentation_quality",
                ],
            },
            "application": {
                "categories": ["application", "business", "technical_debt"],
                "excluded_attrs": [
                    "cpu_memory_storage_specs",
                    "network_configuration",
                    "virtualization_platform",
                    "performance_baseline",
                ],
            },
            "database": {
                "categories": ["infrastructure", "business"],
                "excluded_attrs": [
                    "technology_stack",
                    "architecture_pattern",
                    "virtualization_platform",
                    "code_quality_metrics",
                    "eol_technology_assessment",
                    "documentation_quality",
                ],
                "priority_attrs": [
                    "data_volume_characteristics",
                    "cpu_memory_storage_specs",
                    "business_criticality_score",
                    "compliance_constraints",
                ],
            },
            "network": {
                "categories": ["infrastructure"],
                "excluded_attrs": [
                    "technology_stack",
                    "architecture_pattern",
                    "code_quality_metrics",
                    "eol_technology_assessment",
                    "documentation_quality",
                    "data_volume_characteristics",
                ],
            },
            "load_balancer": {
                "categories": ["infrastructure"],
                "excluded_attrs": [
                    "technology_stack",
                    "architecture_pattern",
                    "code_quality_metrics",
                    "eol_technology_assessment",
                    "documentation_quality",
                    "data_volume_characteristics",
                ],
            },
            "storage": {
                "categories": ["infrastructure"],
                "excluded_attrs": [
                    "technology_stack",
                    "architecture_pattern",
                    "integration_dependencies",
                    "code_quality_metrics",
                    "eol_technology_assessment",
                    "documentation_quality",
                ],
                "priority_attrs": [
                    "cpu_memory_storage_specs",
                    "data_volume_characteristics",
                ],
            },
            "container": {
                "categories": [
                    "application",
                    "infrastructure",
                    "business",
                ],
                "excluded_attrs": ["virtualization_platform"],
            },
            "security_group": {
                "categories": ["infrastructure", "business"],
                "excluded_attrs": [
                    "technology_stack",
                    "architecture_pattern",
                    "code_quality_metrics",
                    "eol_technology_assessment",
                    "documentation_quality",
                    "cpu_memory_storage_specs",
                ],
            },
        }

        # Get mapping for asset type, default to all categories if unknown
        default_mapping = {
            "categories": list(set(c["category"] for c in all_attrs.values())),
            "excluded_attrs": [],
        }
        mapping = asset_type_mappings.get(asset_type_lower, default_mapping)

        # Filter attributes based on category inclusion
        filtered_attrs = {}
        for attr_name, attr_config in all_attrs.items():
            # Skip if in excluded list
            if attr_name in mapping.get("excluded_attrs", []):
                continue

            # Include if category matches OR if it's a priority attribute for the type
            is_in_category = attr_config["category"] in mapping.get("categories", [])
            is_priority_attr = attr_name in mapping.get("priority_attrs", [])

            if is_in_category or is_priority_attr:
                filtered_attrs[attr_name] = attr_config

        return filtered_attrs

    @staticmethod
    def get_attribute_category_map() -> Dict[str, str]:
        """
        Get a simple mapping of attribute names to their categories.

        This is used by frontend-facing endpoints to categorize missing attributes.
        Centralizes the mapping to avoid duplication across collection_crud files.

        Returns:
            Dict mapping attribute name (str) to category name (str)
            Example: {"operating_system_version": "infrastructure", ...}
        """
        all_attrs = CriticalAttributesDefinition.get_attribute_mapping()
        return {name: config["category"] for name, config in all_attrs.items()}


def validate_attribute_consistency() -> bool:
    """
    Validate that critical attributes in this module match CrewAI tool definitions.

    This helps catch configuration drift between gap creation and questionnaire generation.
    Should be called during application startup or in tests.

    Returns:
        bool: True if consistent

    Raises:
        RuntimeError: If critical attributes mismatch or import fails
    """
    try:
        from app.services.crewai_flows.tools.critical_attributes_tool.base import (
            CriticalAttributesDefinition as CrewAIAttrs,
        )

        collection_keys = set(
            CriticalAttributesDefinition.get_attribute_mapping().keys()
        )
        crewai_keys = set(CrewAIAttrs.get_attribute_mapping().keys())

        missing_in_collection = crewai_keys - collection_keys
        missing_in_crewai = collection_keys - crewai_keys

        if missing_in_collection or missing_in_crewai:
            error_msg = (
                "⚠️  Critical attribute mismatch detected! "
                f"Missing in collection: {missing_in_collection}, "
                f"Missing in CrewAI tool: {missing_in_crewai}"
            )
            logger.error(error_msg)
            raise RuntimeError(
                "Critical attribute mismatch detected. Halting application startup."
            )

        logger.info(
            f"✅ Critical attributes validated: {len(collection_keys)} attributes "
            "match between collection and CrewAI tool"
        )
        return True

    except ImportError as e:
        error_msg = f"❌ Could not import CrewAI CriticalAttributesDefinition for validation: {e}"
        logger.error(error_msg)
        raise RuntimeError("Failed to validate critical attribute consistency.") from e


# This function should be called from your application's startup event handler.
# For example, in FastAPI:
#
# @app.on_event("startup")
# async def startup_event():
#     validate_attribute_consistency()
