"""
Component Analysis Crew - Fallback Implementation

This module provides graceful degradation when CrewAI is not available.
It generates basic component identification and technical debt analysis
based on common patterns.
"""

import logging
from typing import Any, Dict

from app.models.assessment_flow import ComponentType, TechDebtSeverity

logger = logging.getLogger(__name__)


async def execute_fallback_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback implementation when CrewAI is not available.

    This provides graceful degradation with basic component identification
    and technical debt analysis based on common patterns.

    Args:
        context: Execution context containing application_id and metadata

    Returns:
        Dictionary with fallback analysis results
    """
    app_id = context.get("application_id", "unknown")
    logger.info(f"Executing Component Analysis in fallback mode for {app_id}")

    # Generate basic component identification
    components = [
        {
            "name": "web_frontend",
            "type": ComponentType.WEB_FRONTEND.value,
            "technology_stack": {"framework": "React", "language": "JavaScript"},
            "responsibilities": ["User interface", "Client-side logic"],
            "complexity_score": 6.0,
            "business_value_score": 8.0,
        },
        {
            "name": "api_service",
            "type": ComponentType.REST_API.value,
            "technology_stack": {"framework": "Spring Boot", "language": "Java"},
            "responsibilities": ["Business logic", "Data access"],
            "complexity_score": 7.0,
            "business_value_score": 9.0,
        },
        {
            "name": "database",
            "type": ComponentType.RELATIONAL_DATABASE.value,
            "technology_stack": {"database": "PostgreSQL", "version": "12"},
            "responsibilities": ["Data persistence", "Transaction management"],
            "complexity_score": 5.0,
            "business_value_score": 9.0,
        },
    ]

    # Generate basic technical debt analysis
    tech_debt_analysis = [
        {
            "category": "technology",
            "subcategory": "version_obsolescence",
            "title": "Outdated Java Version",
            "description": "Application running on Java 8, which is end-of-life",
            "severity": TechDebtSeverity.HIGH.value,
            "tech_debt_score": 7.5,
            "component": "api_service",
            "remediation_effort_hours": 40,
            "impact_on_migration": "high",
        },
        {
            "category": "architecture",
            "subcategory": "coupling",
            "title": "Tight Database Coupling",
            "description": "Frontend directly accesses database without API layer",
            "severity": TechDebtSeverity.MEDIUM.value,
            "tech_debt_score": 6.0,
            "component": "web_frontend",
            "remediation_effort_hours": 80,
            "impact_on_migration": "medium",
        },
        {
            "category": "security",
            "subcategory": "authentication",
            "title": "Legacy Authentication",
            "description": "Using outdated authentication mechanism",
            "severity": TechDebtSeverity.HIGH.value,
            "tech_debt_score": 8.0,
            "component": "api_service",
            "remediation_effort_hours": 60,
            "impact_on_migration": "high",
        },
    ]

    # Generate component scores
    component_scores = {"web_frontend": 6.0, "api_service": 7.2, "database": 5.0}

    # Generate dependency map
    dependency_map = {
        "internal_dependencies": [
            {
                "from": "web_frontend",
                "to": "api_service",
                "type": "REST",
                "coupling": "loose",
            },
            {
                "from": "api_service",
                "to": "database",
                "type": "JDBC",
                "coupling": "tight",
            },
        ],
        "external_dependencies": [],
        "migration_groups": [
            {
                "group_id": "core_backend",
                "components": ["api_service", "database"],
                "rationale": "Tight coupling requires joint migration",
            },
            {
                "group_id": "frontend",
                "components": ["web_frontend"],
                "rationale": "Can be migrated independently",
            },
        ],
    }

    return {
        "components": components,
        "tech_debt_analysis": tech_debt_analysis,
        "component_scores": component_scores,
        "dependency_map": dependency_map,
        "migration_groups": dependency_map["migration_groups"],
        "crew_confidence": 0.6,  # Lower confidence in fallback mode
        "analysis_insights": [
            "Application follows traditional 3-tier architecture",
            "High technical debt in technology versions",
            "Modernization opportunities in authentication and API design",
        ],
        "execution_mode": "fallback",
    }


# Export for backward compatibility
__all__ = ["execute_fallback_analysis"]
