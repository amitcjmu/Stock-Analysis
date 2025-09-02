"""
Collection Flow Questionnaire Templates

This module contains questionnaire templates and field definitions for collection flows.
Extracted from collection_crud_questionnaires.py to maintain the 400-line file limit.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


def get_bootstrap_questionnaire_template(
    flow_id: str,
    selected_application_id: Optional[str] = None,
    selected_application_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Get the bootstrap questionnaire template for application selection.

    Args:
        flow_id: Collection flow ID
        selected_application_id: Pre-selected application ID if available
        selected_application_name: Pre-selected application name if available

    Returns:
        Bootstrap questionnaire dictionary
    """
    return {
        "id": f"bootstrap_{flow_id}",
        "flow_id": flow_id,
        "title": "Application Information Collection",
        "description": (
            "Please provide essential information about the application "
            "to enable targeted data collection and analysis."
        ),
        "form_fields": [
            # Application Identity Section
            {
                "field_id": "application_name",
                "question_text": "What is the application name?",
                "field_type": "text",
                "required": True,
                "category": "identity",
                "help_text": "Enter the official application name",
            },
            {
                "field_id": "application_type",
                "question_text": "What type of application is this?",
                "field_type": "select",
                "required": True,
                "category": "identity",
                "options": [
                    "web_application",
                    "mobile_application",
                    "desktop_application",
                    "api_service",
                    "database",
                    "middleware",
                    "batch_job",
                    "microservice",
                    "other",
                ],
            },
            {
                "field_id": "business_purpose",
                "question_text": "What is the primary business purpose?",
                "field_type": "text",
                "required": True,
                "category": "business",
                "help_text": "Describe the main business function this application serves",
            },
            # Technical Architecture Section
            {
                "field_id": "primary_technology",
                "question_text": "What is the primary technology stack?",
                "field_type": "select",
                "required": True,
                "category": "technical",
                "options": [
                    "java",
                    "dotnet",
                    "python",
                    "nodejs",
                    "php",
                    "ruby",
                    "go",
                    "cpp",
                    "other",
                ],
            },
            {
                "field_id": "hosting_environment",
                "question_text": "Where is the application currently hosted?",
                "field_type": "select",
                "required": True,
                "category": "infrastructure",
                "options": [
                    "on_premises",
                    "aws",
                    "azure",
                    "gcp",
                    "hybrid_cloud",
                    "other_cloud",
                    "unknown",
                ],
            },
            {
                "field_id": "database_technology",
                "question_text": "What database technology is used?",
                "field_type": "select",
                "required": False,
                "category": "technical",
                "options": [
                    "mysql",
                    "postgresql",
                    "oracle",
                    "sql_server",
                    "mongodb",
                    "redis",
                    "elasticsearch",
                    "none",
                    "other",
                ],
            },
            # Business Impact Section
            {
                "field_id": "business_criticality",
                "question_text": "What is the business criticality level?",
                "field_type": "select",
                "required": True,
                "category": "business",
                "options": [
                    "mission_critical",
                    "business_important",
                    "operational",
                    "development_test",
                    "low_priority",
                ],
            },
            {
                "field_id": "user_base_size",
                "question_text": "Approximately how many users does this application serve?",
                "field_type": "select",
                "required": False,
                "category": "business",
                "options": [
                    "1-50",
                    "51-500",
                    "501-5000",
                    "5001-50000",
                    "50000+",
                    "unknown",
                ],
            },
            {
                "field_id": "peak_usage_pattern",
                "question_text": "When does peak usage typically occur?",
                "field_type": "select",
                "required": False,
                "category": "business",
                "options": [
                    "business_hours",
                    "24x7",
                    "seasonal",
                    "event_driven",
                    "batch_processing",
                    "unknown",
                ],
            },
            # Integration & Dependencies
            {
                "field_id": "integration_complexity",
                "question_text": "How complex are the application integrations?",
                "field_type": "select",
                "required": False,
                "category": "technical",
                "options": [
                    "minimal",
                    "moderate",
                    "complex",
                    "highly_complex",
                    "unknown",
                ],
            },
            {
                "field_id": "external_dependencies",
                "question_text": "Are there external system dependencies?",
                "field_type": "text",
                "required": False,
                "category": "technical",
                "help_text": "List key external systems or APIs this application depends on",
            },
            # Performance & Scale
            {
                "field_id": "current_performance",
                "question_text": "How would you rate current performance?",
                "field_type": "select",
                "required": False,
                "category": "technical",
                "options": ["excellent", "good", "acceptable", "poor", "unknown"],
            },
            {
                "field_id": "scaling_approach",
                "question_text": "How does the application handle scaling?",
                "field_type": "select",
                "required": False,
                "category": "infrastructure",
                "options": [
                    "auto_scaling",
                    "manual_scaling",
                    "fixed_capacity",
                    "not_applicable",
                ],
            },
            # Compliance & Security Section
            {
                "field_id": "data_classification",
                "question_text": "What is the data classification level?",
                "field_type": "select",
                "required": True,
                "category": "compliance",
                "options": ["public", "internal", "confidential", "restricted"],
            },
            {
                "field_id": "compliance_requirements",
                "question_text": "Are there specific compliance requirements?",
                "field_type": "text",
                "required": False,
                "category": "compliance",
                "help_text": "E.g., GDPR, HIPAA, PCI-DSS, SOX",
            },
            {
                "field_id": "disaster_recovery",
                "question_text": "What is the disaster recovery strategy?",
                "field_type": "select",
                "required": False,
                "category": "compliance",
                "options": [
                    "active_active",
                    "active_passive",
                    "backup_restore",
                    "none",
                    "in_development",
                ],
            },
        ],
        "validation_rules": {
            "required": ["application_name", "application_type"],
        },
        "completion_status": "pending",
        "responses_collected": (
            {
                # Pre-populate with selected application data if available
                "application_name": selected_application_name,
                "_metadata": {
                    "selected_application_id": selected_application_id,
                    "pre_filled_from_asset": bool(selected_application_name),
                },
            }
            if selected_application_name
            else {}
        ),
        "created_at": datetime.utcnow(),
        "completed_at": None,
    }


def get_field_categories() -> Dict[str, List[str]]:
    """Get field categories for organizing questionnaire fields.

    Returns:
        Dictionary mapping category names to lists of field descriptions
    """
    return {
        "identity": ["Application name and type identification"],
        "business": ["Business purpose, criticality, and impact"],
        "technical": ["Technology stack and architecture details"],
        "infrastructure": ["Hosting, scaling, and infrastructure"],
        "compliance": ["Security, data classification, and compliance"],
    }


def validate_questionnaire_field(field: Dict[str, Any]) -> bool:
    """Validate a questionnaire field definition.

    Args:
        field: Field definition dictionary

    Returns:
        True if valid, False otherwise
    """
    required_keys = {"field_id", "question_text", "field_type"}
    return all(key in field for key in required_keys)


def get_field_type_options() -> List[str]:
    """Get available field types for questionnaire fields.

    Returns:
        List of valid field type options
    """
    return ["text", "select", "multi_select", "number", "boolean", "date", "textarea"]
