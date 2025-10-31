"""
Collection Agent Questionnaire Bootstrap
Fallback questionnaire generation when agent generation fails or is disabled.
"""

from typing import Dict, Any


def get_bootstrap_questionnaire(agent_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a fallback bootstrap questionnaire based on agent context.

    This function provides a structured questionnaire when agent generation
    fails or is disabled, ensuring the system can still collect essential data.

    Args:
        agent_context: Context data from build_agent_context including assets,
                      gaps, and tenant information

    Returns:
        Dictionary containing questionnaire data with title, description,
        questions, target_gaps, and validation_rules
    """
    # Extract relevant information from context
    existing_assets = agent_context.get("assets", [])

    # Create bootstrap questionnaire structure
    questionnaire_data = {
        "title": "Asset-Aware Data Collection",
        "description": "Collect essential data for selected assets",
        "questions": [
            {
                "field_id": "selected_assets",
                "question_text": "Select assets to collect data for",
                "field_type": "asset_selector",
                "required": True,
                "category": "asset_selection",
                "multiple": True,
                "metadata": {"existing_assets": existing_assets},
            },
            {
                "field_id": "application_name",
                "question_text": "Application Name",
                "field_type": "text",
                "required": True,
                "category": "basic",
                "help_text": "Enter the primary name for this application",
            },
            {
                "field_id": "business_criticality",
                "question_text": "Business Criticality",
                "field_type": "select",
                "required": True,
                "category": "basic",
                "options": ["Low", "Medium", "High", "Critical"],
                "help_text": "Select the business impact level if this system is unavailable",
            },
            {
                "field_id": "operating_system",
                "question_text": "What is the Operating System?",
                "field_type": "select",
                "required": True,
                "category": "infrastructure",
                "options": [
                    "Windows Server 2022",
                    "Windows Server 2019",
                    "Windows Server 2016",
                    "Red Hat Enterprise Linux 8",
                    "Red Hat Enterprise Linux 7",
                    "Ubuntu 22.04 LTS",
                    "Ubuntu 20.04 LTS",
                    "CentOS 8",
                    "SUSE Linux Enterprise Server",
                    "Oracle Linux",
                    "IBM AIX 7.2",
                    "IBM AIX 7.1",
                    "HP-UX",
                    "Oracle Solaris",
                    "IBM z/OS (Mainframe)",
                    "Other",
                ],
                "help_text": "Primary operating system for this application/server",
            },
            {
                "field_id": "technology_stack",
                "question_text": "What is the Technology Stack?",
                "field_type": "multiselect",
                "required": False,
                "category": "technical",
                "options": [
                    "Java",
                    ".NET Framework",
                    ".NET Core",
                    "Python",
                    "Node.js",
                    "PHP",
                    "Ruby",
                    "Go",
                    "Rust",
                    "C++",
                    "Oracle Database",
                    "SQL Server",
                    "MySQL",
                    "PostgreSQL",
                    "MongoDB",
                    "Redis",
                    "Elasticsearch",
                    "Other",
                ],
                "help_text": "Select all programming languages and databases used",
            },
            {
                "field_id": "deployment_environment",
                "question_text": "Deployment Environment",
                "field_type": "select",
                "required": True,
                "category": "infrastructure",
                "options": [
                    "On-Premises",
                    "AWS",
                    "Azure",
                    "Google Cloud",
                    "Hybrid",
                    "Multi-Cloud",
                    "Other",
                ],
                "help_text": "Primary hosting environment for this application",
            },
            {
                "field_id": "data_classification",
                "question_text": "Data Classification",
                "field_type": "select",
                "required": False,
                "category": "security",
                "options": ["Public", "Internal", "Confidential", "Restricted"],
                "help_text": "Highest level of data sensitivity handled by this application",
            },
        ],
        "target_gaps": _create_target_gaps_from_context(agent_context),
        "validation_rules": {
            "required_fields": [
                "selected_assets",
                "application_name",
                "business_criticality",
            ],
            "conditional_required": {
                "technical_stack": "If Other is selected, specify in comments",
                "deployment_environment": "If Other is selected, specify in comments",
            },
        },
    }

    return questionnaire_data


def _create_target_gaps_from_context(
    agent_context: Dict[str, Any],
) -> list[Dict[str, Any]]:
    """
    Create target gaps based on the agent context.

    Args:
        agent_context: Context data including assets and identified gaps

    Returns:
        List of gap dictionaries with gap, priority, and category information
    """
    target_gaps = []

    # Extract gaps from assets
    for asset in agent_context.get("assets", []):
        asset_gaps = asset.get("gaps", [])
        for gap in asset_gaps:
            target_gaps.append(
                {
                    "gap": gap,
                    "priority": "high",
                    "category": "data_collection",
                    "asset_id": asset.get("id"),
                    "asset_name": asset.get("name", "Unknown"),
                }
            )

    # Add default gaps if none found
    if not target_gaps:
        target_gaps = [
            {
                "gap": "Asset selection required",
                "priority": "critical",
                "category": "asset_selection",
                "description": "User must select assets to proceed with data collection",
            },
            {
                "gap": "Basic information incomplete",
                "priority": "high",
                "category": "basic_info",
                "description": "Essential application metadata needs to be collected",
            },
            {
                "gap": "Technical details missing",
                "priority": "medium",
                "category": "technical_info",
                "description": "Technical stack and deployment information needed",
            },
        ]

    # Limit to first 5 gaps to avoid overwhelming the user
    return target_gaps[:5]
