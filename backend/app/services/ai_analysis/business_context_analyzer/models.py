"""
Business Context Analysis Models - B2.4
ADCS AI Analysis & Intelligence Service

Data models for business context analysis and questionnaire targeting.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from .enums import MigrationDriverType, StakeholderRole


@dataclass
class BusinessContext:
    """Comprehensive business context for questionnaire targeting"""
    organization_profile: Dict[str, Any]
    migration_drivers: List[MigrationDriverType]
    stakeholder_landscape: Dict[StakeholderRole, Dict[str, Any]]
    regulatory_environment: Dict[str, Any]
    technical_maturity: Dict[str, Any]
    cultural_factors: Dict[str, Any]
    resource_constraints: Dict[str, Any]
    success_criteria: Dict[str, Any]


@dataclass
class QuestionnaireTarget:
    """Target definition for questionnaire delivery"""
    target_stakeholders: List[StakeholderRole]
    priority_level: str  # critical, high, medium, low
    complexity_level: str  # basic, intermediate, advanced
    estimated_effort_minutes: int
    business_justification: str
    success_metrics: List[str]