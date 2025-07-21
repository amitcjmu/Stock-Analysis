"""
Business Context Analysis Utilities - B2.4
ADCS AI Analysis & Intelligence Service

Utility functions and default creation methods.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

from typing import Dict, Any
from datetime import datetime, timezone

from .enums import BusinessDomain, OrganizationSize, MigrationDriverType
from .models import BusinessContext


class BusinessContextUtilities:
    """Utility functions for business context analysis"""
    
    @staticmethod
    def create_default_business_context() -> BusinessContext:
        """Create default business context on error"""
        return BusinessContext(
            organization_profile={"domain": BusinessDomain.GENERAL, "size": OrganizationSize.MEDIUM},
            migration_drivers=[MigrationDriverType.DIGITAL_TRANSFORMATION],
            stakeholder_landscape={},
            regulatory_environment={"applicable_regulations": []},
            technical_maturity={"cloud_adoption_level": "hybrid"},
            cultural_factors={"change_tolerance": "medium"},
            resource_constraints={"stakeholder_availability": "medium"},
            success_criteria={"data_completeness_target": 80}
        )
    
    @staticmethod
    def create_default_targeting_strategy() -> Dict[str, Any]:
        """Create default targeting strategy on error"""
        return {
            "targeting_strategy": {
                "questionnaire_targets": [],
                "delivery_sequence": [],
                "total_questionnaires": 0,
                "estimated_completion_days": 7
            },
            "stakeholder_optimization": {
                "primary_stakeholders": ["business_owner"],
                "stakeholder_workload": {},
                "capacity_constraints": {"overall_availability": "medium"},
                "escalation_paths": []
            },
            "communication_strategy": {"communication_channels": {"primary": "email"}},
            "success_metrics": {
                "target_response_rate": 75.0,
                "quality_thresholds": {"minimum_completeness": 75.0},
                "timeline_milestones": [],
                "risk_mitigation": []
            },
            "optimization_metadata": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": True
            }
        }