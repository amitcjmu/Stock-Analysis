"""
Target environment planning endpoints for migration planning.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

router = APIRouter()


@router.get("/target")
async def get_target_environment(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Get target environment planning data with environments, metrics, and recommendations.

    Data sources (priority order):
    1. Assessment Flow phase_results['infrastructure_analysis'] and ['readiness_summary']
    2. Empty state if no assessment completed

    Returns:
        Target environment data with:
        - environments: List of target cloud environments
        - metrics: Aggregated metrics across environments
        - recommendations: System recommendations for optimization
    """
    from app.models.assessment_flow import AssessmentFlow
    from sqlalchemy import select, desc
    from uuid import UUID

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    # Convert to UUIDs (per migration 115) - NEVER use integers for tenant IDs
    client_account_uuid = (
        (
            UUID(client_account_id)
            if isinstance(client_account_id, str)
            else client_account_id
        )
        if client_account_id
        else None
    )

    engagement_uuid = (
        (UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id)
        if engagement_id
        else None
    )

    if not client_account_uuid or not engagement_uuid:
        # Return empty state if tenant context missing
        return {
            "environments": [],
            "metrics": {
                "environments_count": 0,
                "average_readiness": 0.0,
                "compliance_rate": 0.0,
                "total_monthly_cost": 0.0,
            },
            "recommendations": [],
        }

    # Query for latest completed assessment flow (tenant-scoped)
    stmt = (
        select(AssessmentFlow)
        .where(
            AssessmentFlow.client_account_id == client_account_uuid,
            AssessmentFlow.engagement_id == engagement_uuid,
            AssessmentFlow.status.in_(["completed", "accepted"]),
        )
        .order_by(desc(AssessmentFlow.updated_at))
        .limit(1)
    )

    result = await db.execute(stmt)
    assessment_flow = result.scalar_one_or_none()

    if not assessment_flow or not assessment_flow.phase_results:
        # Return empty state if no assessment completed
        return {
            "environments": [],
            "metrics": {
                "environments_count": 0,
                "average_readiness": 0.0,
                "compliance_rate": 0.0,
                "total_monthly_cost": 0.0,
            },
            "recommendations": [],
        }

    # Extract data from assessment phase results
    phase_results = assessment_flow.phase_results or {}

    # Infrastructure analysis phase contains target environment recommendations
    infrastructure_data = phase_results.get("infrastructure_analysis", {})
    readiness_data = assessment_flow.readiness_summary or {}

    # Build target environments from assessment data
    environments = []

    # Extract cloud provider preferences from infrastructure analysis
    cloud_recommendations = infrastructure_data.get("cloud_recommendations", [])

    if cloud_recommendations:
        for idx, rec in enumerate(
            cloud_recommendations[:3]
        ):  # Limit to top 3 recommendations
            provider = rec.get("provider", "AWS")
            confidence = rec.get("confidence_score", 0.0)
            readiness_score = int(confidence * 100) if confidence else 50

            # Extract compliance info from assessment
            compliance_frameworks = rec.get("compliance_frameworks", [])
            compliance_items = [
                {
                    "framework": fw.get("name", "Unknown"),
                    "status": fw.get("status", "In Progress"),
                    "gaps": fw.get("gaps", []),
                }
                for fw in compliance_frameworks
            ]

            # Extract cost estimates
            cost_data = rec.get("cost_estimate", {})

            env = {
                "id": f"env-{provider.lower()}-{idx}",
                "name": f"{provider} {'Production' if idx == 0 else 'Secondary' if idx == 1 else 'DR'}",
                "type": provider,
                "status": (
                    "Planning"
                    if readiness_score < 50
                    else "In Progress" if readiness_score < 80 else "Ready"
                ),
                "readiness": readiness_score,
                "components": [
                    {
                        "name": "Compute",
                        "status": (
                            "In Progress" if readiness_score > 30 else "Not Started"
                        ),
                        "dependencies": ["Networking"],
                    },
                    {
                        "name": "Storage",
                        "status": (
                            "In Progress" if readiness_score > 40 else "Not Started"
                        ),
                        "dependencies": ["Security"],
                    },
                    {
                        "name": "Networking",
                        "status": "Complete" if readiness_score > 70 else "In Progress",
                        "dependencies": [],
                    },
                ],
                "compliance": compliance_items
                or [
                    {
                        "framework": "SOC2",
                        "status": "In Progress",
                        "gaps": ["Encryption configuration pending"],
                    }
                ],
                "costs": {
                    "estimated_monthly": cost_data.get(
                        "monthly_estimate", 10000.0 * (idx + 1)
                    ),
                    "actual_monthly": None,
                    "savings_potential": cost_data.get(
                        "savings_potential", 2000.0 * (idx + 1)
                    ),
                },
            }
            environments.append(env)

    # If no cloud recommendations, provide default based on readiness summary
    if not environments and readiness_data:
        default_env = {
            "id": "env-default-0",
            "name": "Primary Cloud Environment",
            "type": "AWS",  # Default to AWS
            "status": "Planning",
            "readiness": int(readiness_data.get("avg_completeness_score", 0.0) * 100),
            "components": [
                {
                    "name": "Compute",
                    "status": "Not Started",
                    "dependencies": ["Networking"],
                },
                {
                    "name": "Storage",
                    "status": "Not Started",
                    "dependencies": ["Security"],
                },
                {"name": "Networking", "status": "Not Started", "dependencies": []},
            ],
            "compliance": [{"framework": "SOC2", "status": "In Progress", "gaps": []}],
            "costs": {
                "estimated_monthly": 15000.0,
                "actual_monthly": None,
                "savings_potential": 3000.0,
            },
        }
        environments.append(default_env)

    # Calculate aggregated metrics
    if environments:
        avg_readiness = sum(env["readiness"] for env in environments) / len(
            environments
        )
        total_cost = sum(env["costs"]["estimated_monthly"] for env in environments)

        # Calculate compliance rate
        total_frameworks = sum(len(env["compliance"]) for env in environments)
        compliant_frameworks = sum(
            len([c for c in env["compliance"] if c["status"] == "Compliant"])
            for env in environments
        )
        compliance_rate = (
            (compliant_frameworks / total_frameworks * 100)
            if total_frameworks > 0
            else 0.0
        )
    else:
        avg_readiness = 0.0
        total_cost = 0.0
        compliance_rate = 0.0

    # Extract recommendations from agent insights
    agent_insights = assessment_flow.agent_insights or []
    recommendations = []

    for insight in agent_insights[:5]:  # Top 5 recommendations
        if isinstance(insight, dict):
            rec = {
                "category": insight.get("category", "Optimization"),
                "description": insight.get(
                    "recommendation", insight.get("message", "No description")
                ),
                "priority": insight.get("priority", "Medium"),
            }
            recommendations.append(rec)

    # Add default recommendations if none from insights
    if not recommendations:
        recommendations = [
            {
                "category": "Cost Optimization",
                "description": "Review workload patterns for Reserved Instance opportunities",
                "priority": "Medium",
            }
        ]

    return {
        "environments": environments,
        "metrics": {
            "environments_count": len(environments),
            "average_readiness": round(avg_readiness, 1),
            "compliance_rate": round(compliance_rate, 1),
            "total_monthly_cost": round(total_cost, 2),
        },
        "recommendations": recommendations,
    }
