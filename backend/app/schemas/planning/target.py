"""
Target Environment Schemas

Pydantic schemas for target environment planning data.
Matches the frontend TypeScript interface from src/hooks/useTarget.ts
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class TargetComponent(BaseModel):
    """Target environment component details."""

    name: str = Field(..., description="Component name")
    status: Literal["Not Started", "In Progress", "Complete"] = Field(
        ..., description="Component status"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="List of dependency component names"
    )


class TargetCompliance(BaseModel):
    """Target environment compliance information."""

    framework: str = Field(
        ..., description="Compliance framework name (e.g., SOC2, GDPR)"
    )
    status: Literal["Compliant", "In Progress", "Non-Compliant"] = Field(
        ..., description="Compliance status"
    )
    gaps: List[str] = Field(
        default_factory=list, description="List of compliance gaps/issues"
    )


class TargetCosts(BaseModel):
    """Target environment cost estimates."""

    estimated_monthly: float = Field(
        ..., description="Estimated monthly cost in USD", ge=0
    )
    actual_monthly: Optional[float] = Field(
        None, description="Actual monthly cost if available", ge=0
    )
    savings_potential: float = Field(
        default=0, description="Potential monthly savings in USD", ge=0
    )


class TargetEnvironment(BaseModel):
    """Target environment details."""

    id: str = Field(..., description="Unique environment identifier")
    name: str = Field(..., description="Environment name")
    type: Literal["AWS", "Azure", "GCP", "Private Cloud", "Hybrid"] = Field(
        ..., description="Cloud provider or deployment type"
    )
    status: Literal["Planning", "In Progress", "Ready", "Active"] = Field(
        ..., description="Environment readiness status"
    )
    readiness: int = Field(
        ..., description="Readiness percentage (0-100)", ge=0, le=100
    )
    components: List[TargetComponent] = Field(
        default_factory=list, description="Environment components"
    )
    compliance: List[TargetCompliance] = Field(
        default_factory=list, description="Compliance frameworks and status"
    )
    costs: TargetCosts = Field(..., description="Cost estimates and actuals")


class TargetMetrics(BaseModel):
    """Aggregated target environment metrics."""

    environments_count: int = Field(
        ..., description="Total number of environments", ge=0
    )
    average_readiness: float = Field(
        ...,
        description="Average readiness percentage across all environments",
        ge=0,
        le=100,
    )
    compliance_rate: float = Field(
        ..., description="Overall compliance rate percentage", ge=0, le=100
    )
    total_monthly_cost: float = Field(
        ..., description="Total estimated monthly cost across all environments", ge=0
    )


class TargetRecommendation(BaseModel):
    """Target environment recommendation."""

    category: str = Field(..., description="Recommendation category")
    description: str = Field(..., description="Recommendation description")
    priority: Literal["High", "Medium", "Low"] = Field(
        ..., description="Recommendation priority"
    )


class TargetEnvironmentResponse(BaseModel):
    """Complete target environment response."""

    environments: List[TargetEnvironment] = Field(
        default_factory=list, description="List of target environments"
    )
    metrics: TargetMetrics = Field(..., description="Aggregated metrics")
    recommendations: List[TargetRecommendation] = Field(
        default_factory=list, description="System recommendations"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "environments": [
                    {
                        "id": "env-aws-prod",
                        "name": "AWS Production",
                        "type": "AWS",
                        "status": "Planning",
                        "readiness": 75,
                        "components": [
                            {
                                "name": "Compute (EC2/ECS)",
                                "status": "In Progress",
                                "dependencies": ["Networking"],
                            }
                        ],
                        "compliance": [
                            {
                                "framework": "SOC2",
                                "status": "In Progress",
                                "gaps": ["Encryption at rest not configured"],
                            }
                        ],
                        "costs": {
                            "estimated_monthly": 15000.00,
                            "savings_potential": 2500.00,
                        },
                    }
                ],
                "metrics": {
                    "environments_count": 1,
                    "average_readiness": 75.0,
                    "compliance_rate": 60.0,
                    "total_monthly_cost": 15000.00,
                },
                "recommendations": [
                    {
                        "category": "Cost Optimization",
                        "description": "Consider Reserved Instances for stable workloads",
                        "priority": "Medium",
                    }
                ],
            }
        }
