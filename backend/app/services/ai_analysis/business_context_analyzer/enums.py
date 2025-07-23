"""
Business Context Analysis Enums - B2.4
ADCS AI Analysis & Intelligence Service

Enum definitions for business context analysis and questionnaire targeting.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

from enum import Enum


class BusinessDomain(str, Enum):
    """Business domains for context analysis"""

    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    GOVERNMENT = "government"
    EDUCATION = "education"
    ENERGY = "energy"
    TELECOMMUNICATIONS = "telecommunications"
    GENERAL = "general"


class OrganizationSize(str, Enum):
    """Organization size categories"""

    STARTUP = "startup"  # < 50 employees
    SMALL = "small"  # 50-249 employees
    MEDIUM = "medium"  # 250-999 employees
    LARGE = "large"  # 1000-4999 employees
    ENTERPRISE = "enterprise"  # 5000+ employees


class StakeholderRole(str, Enum):
    """Stakeholder roles for questionnaire targeting"""

    INFRASTRUCTURE_ENGINEER = "infrastructure_engineer"
    APPLICATION_ARCHITECT = "application_architect"
    BUSINESS_OWNER = "business_owner"
    SECURITY_OFFICER = "security_officer"
    COMPLIANCE_MANAGER = "compliance_manager"
    OPERATIONS_MANAGER = "operations_manager"
    DATABASE_ADMINISTRATOR = "database_administrator"
    NETWORK_ADMINISTRATOR = "network_administrator"
    PROJECT_MANAGER = "project_manager"
    C_LEVEL_EXECUTIVE = "c_level_executive"


class MigrationDriverType(str, Enum):
    """Types of migration drivers"""

    COST_OPTIMIZATION = "cost_optimization"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    END_OF_LIFE = "end_of_life"
    SCALABILITY = "scalability"
    SECURITY_ENHANCEMENT = "security_enhancement"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    VENDOR_CONSOLIDATION = "vendor_consolidation"
    DISASTER_RECOVERY = "disaster_recovery"
