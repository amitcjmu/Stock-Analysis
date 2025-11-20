"""
Pydantic schemas for assessment info endpoints.
"""

from pydantic import BaseModel, Field


class ComplexityMetricsUpdate(BaseModel):
    """Request body for complexity metrics update."""

    complexity_score: int = Field(
        ..., ge=1, le=10, description="Complexity score from 1-10"
    )
    architecture_type: str = Field(
        ..., description="Architecture type (Monolithic, Microservices, etc.)"
    )
    customization_level: str = Field(
        ..., description="Customization level (Low, Medium, High)"
    )
