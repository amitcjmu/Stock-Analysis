"""
Architecture Standards Crew - Fallback Implementation

This module provides the fallback implementation for the Architecture Standards Crew
when CrewAI is not available. It generates basic architecture standards and compliance
analysis using predefined templates and heuristics.

The fallback mode provides:
- Basic architecture standards based on industry best practices
- Simple compliance analysis with baseline scores
- Standard upgrade recommendations
- Lower confidence scores to indicate degraded mode

This ensures the system can continue to function even when CrewAI is unavailable,
providing graceful degradation rather than complete failure.

References:
- Original file: architecture_standards_crew.py (lines 490-597)
- Pattern source: component_analysis_crew/fallback.py
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def execute_fallback_architecture_standards(
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Fallback implementation for architecture standards analysis.

    This function generates basic architecture standards and compliance analysis
    when CrewAI is not available. It uses predefined templates and simple heuristics
    to provide a degraded but functional experience.

    Args:
        context: Dictionary containing:
            - engagement_context: Engagement-level context
            - selected_applications: List of application IDs
            - application_metadata: Metadata for each application
            - existing_standards: Previously defined standards
            - business_constraints: Known business constraints
            - risk_tolerance: Risk tolerance level

    Returns:
        Dictionary containing:
            - engagement_standards: List of architecture standards
            - application_compliance: Compliance analysis per application
            - exceptions: List of architecture exceptions
            - upgrade_recommendations: Recommended upgrade paths
            - technical_debt_scores: Technical debt scores per application
            - crew_confidence: Confidence score (lower in fallback mode)
            - recommendations: General recommendations
            - execution_mode: 'fallback' to indicate degraded mode
    """
    logger.info("Executing Architecture Standards analysis in fallback mode")

    # Generate basic architecture standards based on industry best practices
    engagement_standards = [
        {
            "type": "technology_version",
            "name": "Java Version Standard",
            "description": "Minimum Java version requirement for enterprise applications",
            "rationale": "Java 11+ required for long-term support and security patches",
            "is_mandatory": True,
            "technology_specifications": {
                "minimum_version": "11",
                "recommended_version": "17",
                "eol_versions": ["8", "7", "6"],
            },
            "implementation_guidance": [
                "Upgrade applications running Java 8 or earlier",
                "Use OpenJDK or Oracle JDK with commercial support",
                "Validate compatibility with existing frameworks",
            ],
        },
        {
            "type": "security_standard",
            "name": "API Security Standard",
            "description": "Security requirements for REST and GraphQL APIs",
            "rationale": "Ensure consistent security posture across all API endpoints",
            "is_mandatory": True,
            "technology_specifications": {
                "authentication": "OAuth 2.0 or OIDC",
                "authorization": "RBAC with fine-grained permissions",
                "encryption": "TLS 1.2+ for all communications",
            },
            "implementation_guidance": [
                "Implement API gateway for centralized security",
                "Use JWT tokens with proper validation",
                "Enable rate limiting and throttling",
            ],
        },
        {
            "type": "architecture_pattern",
            "name": "Microservices Communication",
            "description": "Standards for inter-service communication",
            "rationale": "Ensure reliable and scalable service-to-service communication",
            "is_mandatory": False,
            "technology_specifications": {
                "sync_communication": "REST with OpenAPI specifications",
                "async_communication": "Event-driven with message queues",
                "data_formats": "JSON with schema validation",
            },
            "implementation_guidance": [
                "Use circuit breaker pattern for resilience",
                "Implement distributed tracing",
                "Design for eventual consistency",
            ],
        },
        {
            "type": "technology_version",
            "name": ".NET Version Standard",
            "description": "Minimum .NET version requirement",
            "rationale": ".NET 6+ required for long-term support and cross-platform capabilities",
            "is_mandatory": True,
            "technology_specifications": {
                "minimum_version": "6",
                "recommended_version": "8",
                "eol_versions": ["Framework 4.8", "Core 3.1"],
            },
            "implementation_guidance": [
                "Migrate from .NET Framework to .NET 6+",
                "Adopt cross-platform deployment capabilities",
                "Leverage performance improvements in newer versions",
            ],
        },
    ]

    # Generate basic compliance analysis for each application
    application_compliance = {}
    for app_id in context.get("selected_applications", []):
        application_compliance[app_id] = {
            "overall_score": 65.0,  # Baseline score in fallback mode
            "technology_compliance": {
                "java_version": {
                    "status": "needs_upgrade",
                    "current": "8",
                    "required": "11+",
                    "severity": "high",
                },
                "dotnet_version": {
                    "status": "needs_assessment",
                    "current": "unknown",
                    "required": "6+",
                    "severity": "medium",
                },
                "security_frameworks": {
                    "status": "partial",
                    "coverage": "70%",
                    "severity": "medium",
                },
            },
            "upgrade_recommendations": [
                {
                    "priority": "high",
                    "item": "Upgrade Java version to 11 or higher",
                    "effort": "medium",
                    "estimated_hours": 40,
                },
                {
                    "priority": "medium",
                    "item": "Implement comprehensive API security",
                    "effort": "high",
                    "estimated_hours": 80,
                },
            ],
            "estimated_effort_hours": 120,
            "compliance_timeline": "3-6 months",
        }

    # Calculate technical debt scores (0-10 scale, higher = more debt)
    technical_debt_scores = {
        app_id: 6.5  # Baseline debt score
        for app_id in context.get("selected_applications", [])
    }

    return {
        "engagement_standards": engagement_standards,
        "application_compliance": application_compliance,
        "exceptions": [],  # No exceptions in basic fallback mode
        "upgrade_recommendations": {
            "immediate_actions": [
                "Java version upgrades for all Java-based applications",
                "Security vulnerability assessments",
            ],
            "short_term": [
                "API security improvements",
                "Authentication and authorization standardization",
            ],
            "long_term": [
                "Architecture pattern adoption",
                "Cloud-native capabilities enhancement",
            ],
        },
        "technical_debt_scores": technical_debt_scores,
        "crew_confidence": 0.6,  # Lower confidence in fallback mode
        "recommendations": [
            "Implement comprehensive architecture governance framework",
            "Establish regular compliance review cycles",
            "Invest in developer training on modern architecture patterns",
            "Create architecture decision record (ADR) process",
        ],
        "execution_mode": "fallback",
        "fallback_reason": "CrewAI not available - using template-based analysis",
    }


# Export fallback function
__all__ = ["execute_fallback_architecture_standards"]
