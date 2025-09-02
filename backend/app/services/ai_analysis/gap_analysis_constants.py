"""
Gap Analysis Constants and Utilities

This module contains constants, data structures, and utility functions for gap analysis.
Extracted from gap_analysis_agent.py to maintain the 400-line file limit.
"""

from typing import Any, Dict, List
from datetime import datetime, timezone

# Critical attributes framework for 6R migration analysis
CRITICAL_ATTRIBUTES_FRAMEWORK = {
    "infrastructure": {
        "primary": [
            "hostname",
            "environment",
            "os_type",
            "os_version",
            "cpu_cores",
            "memory_gb",
            "storage_gb",
            "network_zone",
        ],
        "business_impact": "high",
        "6r_relevance": ["rehost", "replatform", "refactor"],
    },
    "application": {
        "primary": [
            "application_name",
            "application_type",
            "technology_stack",
            "criticality_level",
            "data_classification",
            "compliance_scope",
        ],
        "business_impact": "critical",
        "6r_relevance": ["refactor", "repurchase", "retire"],
    },
    "operational": {
        "primary": [
            "owner",
            "cost_center",
            "backup_strategy",
            "monitoring_status",
            "patch_level",
            "last_scan_date",
        ],
        "business_impact": "medium",
        "6r_relevance": ["retain", "rehost", "replatform"],
    },
    "dependencies": {
        "primary": [
            "application_dependencies",
            "database_dependencies",
            "integration_points",
            "data_flows",
        ],
        "business_impact": "critical",
        "6r_relevance": ["refactor", "replatform", "repurchase"],
    },
}


def get_gap_analysis_metadata(
    client_account_id: str, engagement_id: str, uses_persistent_agents: bool = True
) -> Dict[str, Any]:
    """Get standardized metadata for gap analysis results.

    Args:
        client_account_id: Tenant client account ID
        engagement_id: Engagement ID
        uses_persistent_agents: Whether persistent agents were used

    Returns:
        Metadata dictionary
    """
    return {
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "tenant_context": f"{client_account_id}/{engagement_id}",
        "uses_persistent_agents": uses_persistent_agents,
    }


def create_error_result(
    service_name: str,
    error_code: str,
    error_message: str,
    client_account_id: str,
    engagement_id: str,
) -> Dict[str, Any]:
    """Create a standardized error result for gap analysis.

    Args:
        service_name: Name of the service that failed
        error_code: Error code
        error_message: Error message
        client_account_id: Tenant client account ID
        engagement_id: Engagement ID

    Returns:
        Error result dictionary
    """
    return {
        "service_name": service_name,
        "status": "error",
        "error_code": error_code,
        "error": error_message,
        "gap_analysis": {"summary": {"error": True}},
        "metadata": get_gap_analysis_metadata(client_account_id, engagement_id),
    }


def build_task_prompt(task_type: str, inputs: Dict[str, Any]) -> str:
    """Build a prompt for gap analysis tasks.

    Args:
        task_type: Type of task (gap_identification, business_assessment, quality_validation)
        inputs: Task inputs

    Returns:
        Task prompt string
    """
    if task_type == "gap_identification":
        return f"""
        Analyze the collected data and identify gaps in critical attributes:

        Data: {inputs.get('collected_data', [])}
        Existing Gaps: {inputs.get('existing_gaps', [])}
        6R Requirements: {inputs.get('sixr_requirements', {})}

        Focus on:
        1. Missing critical attributes for 6R analysis
        2. Data quality issues
        3. Completeness assessment

        Provide structured gap analysis with categories and priorities.
        """
    elif task_type == "business_assessment":
        return f"""
        Assess the business impact of identified data gaps:

        Gaps: {inputs.get('collected_data', [])}
        Business Context: {inputs.get('sixr_requirements', {})}

        Evaluate:
        1. Business criticality of missing data
        2. Impact on migration decisions
        3. Priority for gap resolution

        Provide business impact scoring and recommendations.
        """
    elif task_type == "quality_validation":
        return f"""
        Validate the quality and completeness of gap analysis:

        Analysis Results: {inputs.get('collected_data', [])}
        Requirements: {inputs.get('sixr_requirements', {})}

        Check for:
        1. Analysis completeness
        2. Logical consistency
        3. Actionable recommendations

        Provide quality assessment and validation results.
        """
    else:
        return f"Unknown task type: {task_type}"


def get_attribute_categories() -> List[str]:
    """Get list of attribute categories from the framework.

    Returns:
        List of category names
    """
    return list(CRITICAL_ATTRIBUTES_FRAMEWORK.keys())


def get_primary_attributes_for_category(category: str) -> List[str]:
    """Get primary attributes for a specific category.

    Args:
        category: Category name

    Returns:
        List of primary attributes
    """
    return CRITICAL_ATTRIBUTES_FRAMEWORK.get(category, {}).get("primary", [])


def get_business_impact_for_category(category: str) -> str:
    """Get business impact level for a specific category.

    Args:
        category: Category name

    Returns:
        Business impact level
    """
    return CRITICAL_ATTRIBUTES_FRAMEWORK.get(category, {}).get(
        "business_impact", "unknown"
    )


def get_sixr_relevance_for_category(category: str) -> List[str]:
    """Get 6R relevance strategies for a specific category.

    Args:
        category: Category name

    Returns:
        List of relevant 6R strategies
    """
    return CRITICAL_ATTRIBUTES_FRAMEWORK.get(category, {}).get("6r_relevance", [])
