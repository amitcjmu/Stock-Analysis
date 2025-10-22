"""
Critical Attributes Definition for 6R Migration Decision Making

This module defines the 22 critical attributes required for accurate
6R strategy decisions. These attributes are used by the programmatic
gap scanner to identify missing data.
"""

from typing import Any, Dict


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
        Returns mapping of critical attributes to asset fields.

        Returns:
            Dict with attribute name as key and config as value:
            {
                "attribute_name": {
                    "category": "infrastructure|application|business|"
                                "technical_debt|dependencies",
                    "priority": 1-4,  # 1=critical, 4=low
                    "asset_fields": ["field_name", "custom_attributes.field"],
                    "description": "What this attribute represents"
                }
            }
        """
        return {
            # Infrastructure Attributes (6)
            "operating_system": {
                "category": "infrastructure",
                "priority": 1,
                "asset_fields": ["operating_system", "custom_attributes.os"],
                "description": "Operating system type and version",
            },
            "cpu_architecture": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": ["cpu_info", "custom_attributes.cpu_architecture"],
                "description": "CPU architecture (x86, ARM, etc.)",
            },
            "memory_allocation": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": ["memory_gb", "custom_attributes.memory"],
                "description": "Allocated memory in GB",
            },
            "storage_capacity": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": ["storage_gb", "custom_attributes.storage"],
                "description": "Storage capacity in GB",
            },
            "network_configuration": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": ["network_config", "custom_attributes.network"],
                "description": "Network settings and connectivity",
            },
            "virtualization_type": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": ["virtualization", "custom_attributes.vm_type"],
                "description": "Virtualization platform (VMware, Hyper-V, etc.)",
            },
            "cpu_cores": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": ["cpu_cores", "custom_attributes.cpu_cores"],
                "description": "Number of CPU cores allocated",
            },
            "memory_gb": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": ["memory_gb", "custom_attributes.memory"],
                "description": "Memory allocation in GB",
            },
            "storage_gb": {
                "category": "infrastructure",
                "priority": 2,
                "asset_fields": ["storage_gb", "custom_attributes.storage"],
                "description": "Storage capacity in GB",
            },
            "environment": {
                "category": "infrastructure",
                "priority": 1,
                "asset_fields": ["environment", "custom_attributes.environment"],
                "description": "Deployment environment "
                "(production, staging, development, etc.)",
                "required": True,
            },
            # Application Attributes (4)
            "technology_stack": {
                "category": "application",
                "priority": 1,
                "asset_fields": ["technology_stack", "custom_attributes.tech_stack"],
                "description": "Programming languages, frameworks, runtime",
            },
            "application_architecture": {
                "category": "application",
                "priority": 1,
                "asset_fields": [
                    "architecture_pattern",
                    "custom_attributes.architecture",
                ],
                "description": "Architecture pattern (monolith, microservices, etc.)",
            },
            "integration_points": {
                "category": "application",
                "priority": 1,
                "asset_fields": ["integrations", "custom_attributes.integrations"],
                "description": "External systems and APIs integrated",
            },
            "data_volume": {
                "category": "application",
                "priority": 2,
                "asset_fields": ["data_size_gb", "custom_attributes.data_volume"],
                "description": "Data volume in GB",
            },
            # Business Attributes (4)
            "business_criticality": {
                "category": "business",
                "priority": 1,
                "asset_fields": [
                    "criticality",
                    "custom_attributes.business_criticality",
                ],
                "description": "Business impact level (critical, high, medium, low)",
                "required": True,
            },
            "change_tolerance": {
                "category": "business",
                "priority": 1,
                "asset_fields": [
                    "risk_tolerance",
                    "custom_attributes.change_tolerance",
                ],
                "description": "Tolerance for change and downtime",
            },
            "compliance_requirements": {
                "category": "business",
                "priority": 1,
                "asset_fields": [
                    "compliance",
                    "custom_attributes.compliance_requirements",
                ],
                "description": "Regulatory compliance needs (HIPAA, SOC2, etc.)",
            },
            "stakeholder_impact": {
                "category": "business",
                "priority": 2,
                "asset_fields": ["user_count", "custom_attributes.stakeholder_count"],
                "description": "Number of impacted users/stakeholders",
            },
            # Technical Debt Attributes (4)
            "code_quality_score": {
                "category": "technical_debt",
                "priority": 2,
                "asset_fields": [
                    "code_quality",
                    "custom_attributes.code_quality_score",
                ],
                "description": "Code quality metrics (if available)",
            },
            "security_vulnerabilities": {
                "category": "technical_debt",
                "priority": 1,
                "asset_fields": [
                    "security_issues",
                    "custom_attributes.vulnerabilities",
                ],
                "description": "Known security vulnerabilities",
            },
            "end_of_life_technology": {
                "category": "technical_debt",
                "priority": 1,
                "asset_fields": ["eol_tech", "custom_attributes.eol_components"],
                "description": "End-of-life technologies in use",
            },
            "documentation_quality": {
                "category": "technical_debt",
                "priority": 3,
                "asset_fields": [
                    "documentation",
                    "custom_attributes.documentation_quality",
                ],
                "description": "Quality of technical documentation",
            },
            # Dependency Attributes (4)
            "upstream_dependencies": {
                "category": "dependencies",
                "priority": 1,
                "asset_fields": ["dependencies", "custom_attributes.upstream_deps"],
                "description": "Systems this application depends on",
            },
            "downstream_dependents": {
                "category": "dependencies",
                "priority": 1,
                "asset_fields": ["dependents", "custom_attributes.downstream_deps"],
                "description": "Systems that depend on this application",
            },
            "database_type": {
                "category": "dependencies",
                "priority": 1,
                "asset_fields": ["database_type", "custom_attributes.database"],
                "description": "Database type and version",
            },
            "external_services": {
                "category": "dependencies",
                "priority": 2,
                "asset_fields": [
                    "external_services",
                    "custom_attributes.third_party_services",
                ],
                "description": "External services and vendors used",
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
                    "application_architecture",
                    "integration_points",
                    "code_quality_score",
                    "end_of_life_technology",
                    "documentation_quality",
                ],
            },
            "virtual_machine": {
                "categories": ["infrastructure"],
                "excluded_attrs": [
                    "technology_stack",
                    "application_architecture",
                    "integration_points",
                    "code_quality_score",
                    "end_of_life_technology",
                    "documentation_quality",
                ],
            },
            "application": {
                "categories": ["application", "business", "technical_debt"],
                "excluded_attrs": [
                    "cpu_architecture",
                    "cpu_cores",
                    "memory_allocation",
                    "memory_gb",
                    "storage_capacity",
                    "storage_gb",
                    "network_configuration",
                    "virtualization_type",
                ],
            },
            "database": {
                "categories": ["dependencies", "infrastructure", "business"],
                "excluded_attrs": [
                    "technology_stack",
                    "application_architecture",
                    "cpu_architecture",
                    "virtualization_type",
                    "code_quality_score",
                    "end_of_life_technology",
                    "documentation_quality",
                ],
                "priority_attrs": [
                    "database_type",
                    "data_volume",
                    "storage_gb",
                    "storage_capacity",
                    "business_criticality",
                    "compliance_requirements",
                ],
            },
            "network": {
                "categories": ["infrastructure", "dependencies"],
                "excluded_attrs": [
                    "technology_stack",
                    "application_architecture",
                    "code_quality_score",
                    "end_of_life_technology",
                    "documentation_quality",
                    "data_volume",
                ],
            },
            "load_balancer": {
                "categories": ["infrastructure", "dependencies"],
                "excluded_attrs": [
                    "technology_stack",
                    "application_architecture",
                    "code_quality_score",
                    "end_of_life_technology",
                    "documentation_quality",
                    "data_volume",
                ],
            },
            "storage": {
                "categories": ["infrastructure"],
                "excluded_attrs": [
                    "technology_stack",
                    "application_architecture",
                    "integration_points",
                    "code_quality_score",
                    "end_of_life_technology",
                    "documentation_quality",
                ],
                "priority_attrs": ["storage_capacity", "storage_gb", "data_volume"],
            },
            "container": {
                "categories": [
                    "application",
                    "infrastructure",
                    "dependencies",
                    "business",
                ],
                "excluded_attrs": ["virtualization_type"],
            },
            "security_group": {
                "categories": ["infrastructure", "business"],
                "excluded_attrs": [
                    "technology_stack",
                    "application_architecture",
                    "code_quality_score",
                    "end_of_life_technology",
                    "documentation_quality",
                    "cpu_cores",
                    "memory_gb",
                    "storage_gb",
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
