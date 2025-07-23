"""
Business Context Analysis Domain Configurations - B2.4
ADCS AI Analysis & Intelligence Service

Domain-specific configurations and stakeholder expertise profiles.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

from typing import Any, Dict

from .enums import BusinessDomain, StakeholderRole


class DomainConfigurationManager:
    """Manages domain-specific configurations and stakeholder expertise"""

    @staticmethod
    def get_domain_configurations() -> Dict[BusinessDomain, Dict[str, Any]]:
        """Get business domain-specific configurations"""
        return {
            BusinessDomain.FINANCIAL_SERVICES: {
                "regulatory_focus": ["SOX", "PCI-DSS", "GDPR", "Basel III"],
                "critical_attributes": [
                    "data_classification",
                    "compliance_scope",
                    "security_controls",
                ],
                "stakeholder_priority": [
                    StakeholderRole.COMPLIANCE_MANAGER,
                    StakeholderRole.SECURITY_OFFICER,
                    StakeholderRole.BUSINESS_OWNER,
                ],
                "migration_concerns": [
                    "regulatory_compliance",
                    "data_security",
                    "business_continuity",
                ],
                "question_complexity": "high",
            },
            BusinessDomain.HEALTHCARE: {
                "regulatory_focus": ["HIPAA", "HITECH", "FDA", "GDPR"],
                "critical_attributes": [
                    "patient_data_handling",
                    "compliance_scope",
                    "availability_requirements",
                ],
                "stakeholder_priority": [
                    StakeholderRole.COMPLIANCE_MANAGER,
                    StakeholderRole.SECURITY_OFFICER,
                    StakeholderRole.OPERATIONS_MANAGER,
                ],
                "migration_concerns": [
                    "patient_safety",
                    "data_privacy",
                    "system_availability",
                ],
                "question_complexity": "high",
            },
            BusinessDomain.MANUFACTURING: {
                "regulatory_focus": ["ISO_27001", "NIST", "industry_specific"],
                "critical_attributes": [
                    "operational_impact",
                    "downtime_tolerance",
                    "integration_points",
                ],
                "stakeholder_priority": [
                    StakeholderRole.OPERATIONS_MANAGER,
                    StakeholderRole.INFRASTRUCTURE_ENGINEER,
                    StakeholderRole.BUSINESS_OWNER,
                ],
                "migration_concerns": [
                    "operational_continuity",
                    "system_integration",
                    "cost_control",
                ],
                "question_complexity": "medium",
            },
            BusinessDomain.TECHNOLOGY: {
                "regulatory_focus": ["GDPR", "SOC2", "ISO_27001"],
                "critical_attributes": [
                    "scalability",
                    "performance",
                    "technology_stack",
                ],
                "stakeholder_priority": [
                    StakeholderRole.APPLICATION_ARCHITECT,
                    StakeholderRole.INFRASTRUCTURE_ENGINEER,
                    StakeholderRole.SECURITY_OFFICER,
                ],
                "migration_concerns": [
                    "technical_excellence",
                    "scalability",
                    "innovation",
                ],
                "question_complexity": "medium",
            },
            BusinessDomain.GOVERNMENT: {
                "regulatory_focus": ["FedRAMP", "FISMA", "NIST", "GDPR"],
                "critical_attributes": [
                    "security_clearance",
                    "compliance_scope",
                    "data_sovereignty",
                ],
                "stakeholder_priority": [
                    StakeholderRole.SECURITY_OFFICER,
                    StakeholderRole.COMPLIANCE_MANAGER,
                    StakeholderRole.INFRASTRUCTURE_ENGINEER,
                ],
                "migration_concerns": [
                    "security_compliance",
                    "data_sovereignty",
                    "transparency",
                ],
                "question_complexity": "high",
            },
            BusinessDomain.GENERAL: {
                "regulatory_focus": ["GDPR", "SOC2", "basic_compliance"],
                "critical_attributes": [
                    "business_criticality",
                    "cost_impact",
                    "operational_impact",
                ],
                "stakeholder_priority": [
                    StakeholderRole.BUSINESS_OWNER,
                    StakeholderRole.INFRASTRUCTURE_ENGINEER,
                    StakeholderRole.OPERATIONS_MANAGER,
                ],
                "migration_concerns": [
                    "cost_effectiveness",
                    "risk_management",
                    "business_value",
                ],
                "question_complexity": "medium",
            },
        }

    @staticmethod
    def get_stakeholder_expertise() -> Dict[StakeholderRole, Dict[str, Any]]:
        """Get stakeholder expertise profiles"""
        return {
            StakeholderRole.INFRASTRUCTURE_ENGINEER: {
                "expertise_areas": [
                    "server_configuration",
                    "network_architecture",
                    "storage_systems",
                    "virtualization",
                    "cloud_platforms",
                    "performance_monitoring",
                ],
                "question_types": ["technical", "operational", "performance"],
                "complexity_comfort": "high",
                "typical_knowledge_gaps": [
                    "business_impact",
                    "compliance_requirements",
                ],
                "optimal_session_length": 30,
                "preferred_question_format": "technical_detail",
            },
            StakeholderRole.APPLICATION_ARCHITECT: {
                "expertise_areas": [
                    "application_design",
                    "technology_stack",
                    "integration_patterns",
                    "data_architecture",
                    "security_design",
                    "scalability",
                ],
                "question_types": ["architectural", "technical", "integration"],
                "complexity_comfort": "high",
                "typical_knowledge_gaps": [
                    "operational_procedures",
                    "business_processes",
                ],
                "optimal_session_length": 45,
                "preferred_question_format": "architectural_diagram",
            },
            StakeholderRole.BUSINESS_OWNER: {
                "expertise_areas": [
                    "business_processes",
                    "user_requirements",
                    "business_value",
                    "cost_impact",
                    "operational_procedures",
                    "stakeholder_needs",
                ],
                "question_types": ["business", "functional", "strategic"],
                "complexity_comfort": "low",
                "typical_knowledge_gaps": [
                    "technical_architecture",
                    "infrastructure_details",
                ],
                "optimal_session_length": 20,
                "preferred_question_format": "business_language",
            },
            StakeholderRole.SECURITY_OFFICER: {
                "expertise_areas": [
                    "security_controls",
                    "compliance_requirements",
                    "threat_assessment",
                    "data_classification",
                    "access_management",
                    "audit_trails",
                ],
                "question_types": ["security", "compliance", "risk"],
                "complexity_comfort": "high",
                "typical_knowledge_gaps": ["operational_details", "business_processes"],
                "optimal_session_length": 35,
                "preferred_question_format": "security_framework",
            },
            StakeholderRole.COMPLIANCE_MANAGER: {
                "expertise_areas": [
                    "regulatory_requirements",
                    "audit_processes",
                    "documentation",
                    "risk_management",
                    "policy_compliance",
                    "reporting",
                ],
                "question_types": ["compliance", "regulatory", "documentation"],
                "complexity_comfort": "medium",
                "typical_knowledge_gaps": [
                    "technical_implementation",
                    "infrastructure",
                ],
                "optimal_session_length": 25,
                "preferred_question_format": "compliance_checklist",
            },
            StakeholderRole.OPERATIONS_MANAGER: {
                "expertise_areas": [
                    "operational_procedures",
                    "service_management",
                    "incident_response",
                    "change_management",
                    "monitoring",
                    "maintenance",
                ],
                "question_types": ["operational", "procedural", "management"],
                "complexity_comfort": "medium",
                "typical_knowledge_gaps": [
                    "detailed_technical_specs",
                    "architectural_design",
                ],
                "optimal_session_length": 30,
                "preferred_question_format": "operational_workflow",
            },
        }

    @staticmethod
    def get_complexity_thresholds() -> Dict[str, Dict[str, Any]]:
        """Get complexity thresholds for different contexts"""
        return {
            "question_complexity": {
                "basic": {
                    "max_questions_per_section": 8,
                    "max_total_questions": 20,
                    "technical_depth": "surface",
                    "business_context_required": False,
                },
                "intermediate": {
                    "max_questions_per_section": 12,
                    "max_total_questions": 35,
                    "technical_depth": "moderate",
                    "business_context_required": True,
                },
                "advanced": {
                    "max_questions_per_section": 20,
                    "max_total_questions": 60,
                    "technical_depth": "detailed",
                    "business_context_required": True,
                },
            },
            "stakeholder_capacity": {
                "low": {"max_session_minutes": 15, "max_questions": 10},
                "medium": {"max_session_minutes": 30, "max_questions": 25},
                "high": {"max_session_minutes": 60, "max_questions": 50},
            },
        }
