"""
Base definitions for Critical Attributes Assessment Tool

Contains the core 22 critical attributes definition and mapping configurations
for 6R migration strategy decisions.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Import CrewAI tools with fallback
try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


class CriticalAttributesDefinition:
    """Defines and validates the 22 critical attributes for 6R decisions"""

    INFRASTRUCTURE_ATTRIBUTES = [
        "operating_system_version",
        "cpu_memory_storage_specs",
        "network_configuration",
        "virtualization_platform",
        "performance_baseline",
        "availability_requirements",
    ]

    APPLICATION_ATTRIBUTES = [
        "technology_stack",
        "architecture_pattern",
        "integration_dependencies",
        "data_volume_characteristics",
        "user_load_patterns",
        "business_logic_complexity",
        "configuration_complexity",
        "security_compliance_requirements",
    ]

    BUSINESS_CONTEXT_ATTRIBUTES = [
        "business_criticality_score",
        "change_tolerance",
        "compliance_constraints",
        "stakeholder_impact",
    ]

    TECHNICAL_DEBT_ATTRIBUTES = [
        "code_quality_metrics",
        "security_vulnerabilities",
        "eol_technology_assessment",
        "documentation_quality",
    ]

    @classmethod
    def get_all_attributes(cls) -> List[str]:
        """Get all 22 critical attributes"""
        return (
            cls.INFRASTRUCTURE_ATTRIBUTES
            + cls.APPLICATION_ATTRIBUTES
            + cls.BUSINESS_CONTEXT_ATTRIBUTES
            + cls.TECHNICAL_DEBT_ATTRIBUTES
        )

    @classmethod
    def get_attribute_mapping(cls) -> Dict[str, Dict[str, Any]]:
        """Map critical attributes to asset model fields and detection patterns"""
        return {
            # Infrastructure Attributes
            "operating_system_version": {
                "asset_fields": ["operating_system", "os_version"],
                "patterns": ["os", "operating_system", "platform", "os_ver"],
                "required": True,
                "category": "infrastructure",
            },
            "cpu_memory_storage_specs": {
                "asset_fields": ["cpu_cores", "memory_gb", "storage_gb"],
                "patterns": ["cpu", "memory", "ram", "storage", "disk", "cores"],
                "required": True,
                "category": "infrastructure",
            },
            "network_configuration": {
                "asset_fields": ["ip_address", "fqdn", "mac_address"],
                "patterns": ["network", "ip", "subnet", "vlan", "nic"],
                "required": False,
                "category": "infrastructure",
            },
            "virtualization_platform": {
                "asset_fields": ["custom_attributes.virtualization_platform"],
                "patterns": ["hypervisor", "vmware", "hyper-v", "kvm", "virtual"],
                "required": False,
                "category": "infrastructure",
            },
            "performance_baseline": {
                "asset_fields": [
                    "cpu_utilization_percent",
                    "memory_utilization_percent",
                    "disk_iops",
                    "network_throughput_mbps",
                ],
                "patterns": ["utilization", "performance", "baseline", "metrics"],
                "required": False,
                "category": "infrastructure",
            },
            "availability_requirements": {
                "asset_fields": ["custom_attributes.availability_requirements"],
                "patterns": ["availability", "sla", "uptime", "rto", "rpo"],
                "required": True,
                "category": "infrastructure",
            },
            # Application Attributes
            "technology_stack": {
                "asset_fields": ["technology_stack", "custom_attributes.tech_stack"],
                "patterns": [
                    "stack",
                    "framework",
                    "runtime",
                    "language",
                    "platform",
                ],
                "required": True,
                "category": "application",
            },
            "architecture_pattern": {
                "asset_fields": ["custom_attributes.architecture_pattern"],
                "patterns": [
                    "architecture",
                    "pattern",
                    "monolithic",
                    "microservices",
                    "tier",
                ],
                "required": True,
                "category": "application",
            },
            "integration_dependencies": {
                "asset_fields": ["dependencies", "related_assets"],
                "patterns": ["dependency", "integration", "api", "service", "endpoint"],
                "required": True,
                "category": "application",
            },
            "data_volume_characteristics": {
                "asset_fields": ["custom_attributes.data_volume"],
                "patterns": ["data_volume", "database_size", "storage_usage", "data"],
                "required": False,
                "category": "application",
            },
            "user_load_patterns": {
                "asset_fields": ["custom_attributes.user_load"],
                "patterns": ["users", "load", "concurrent", "traffic", "requests"],
                "required": False,
                "category": "application",
            },
            "business_logic_complexity": {
                "asset_fields": ["custom_attributes.complexity"],
                "patterns": ["complexity", "business_logic", "rules", "workflow"],
                "required": True,
                "category": "application",
            },
            "configuration_complexity": {
                "asset_fields": ["custom_attributes.config_complexity"],
                "patterns": ["configuration", "settings", "parameters", "env"],
                "required": False,
                "category": "application",
            },
            "security_compliance_requirements": {
                "asset_fields": ["custom_attributes.compliance"],
                "patterns": ["compliance", "security", "pci", "hipaa", "gdpr", "sox"],
                "required": True,
                "category": "application",
            },
            # Business Context Attributes
            "business_criticality_score": {
                "asset_fields": ["business_criticality", "criticality"],
                "patterns": ["criticality", "priority", "importance", "tier"],
                "required": True,
                "category": "business",
            },
            "change_tolerance": {
                "asset_fields": ["custom_attributes.change_tolerance"],
                "patterns": [
                    "change_window",
                    "maintenance",
                    "tolerance",
                    "flexibility",
                ],
                "required": False,
                "category": "business",
            },
            "compliance_constraints": {
                "asset_fields": ["custom_attributes.compliance_constraints"],
                "patterns": ["regulatory", "compliance", "constraint", "requirement"],
                "required": True,
                "category": "business",
            },
            "stakeholder_impact": {
                "asset_fields": ["business_owner", "technical_owner", "department"],
                "patterns": ["owner", "stakeholder", "department", "team"],
                "required": True,
                "category": "business",
            },
            # Technical Debt Attributes
            "code_quality_metrics": {
                "asset_fields": ["custom_attributes.code_quality"],
                "patterns": ["code_quality", "technical_debt", "code_coverage"],
                "required": False,
                "category": "technical_debt",
            },
            "security_vulnerabilities": {
                "asset_fields": ["custom_attributes.vulnerabilities"],
                "patterns": ["vulnerability", "cve", "security_issue", "patch"],
                "required": True,
                "category": "technical_debt",
            },
            "eol_technology_assessment": {
                "asset_fields": ["custom_attributes.eol_assessment"],
                "patterns": ["eol", "end_of_life", "deprecated", "obsolete", "legacy"],
                "required": True,
                "category": "technical_debt",
            },
            "documentation_quality": {
                "asset_fields": ["custom_attributes.documentation_quality"],
                "patterns": ["documentation", "docs", "readme", "wiki", "runbook"],
                "required": False,
                "category": "technical_debt",
            },
        }
