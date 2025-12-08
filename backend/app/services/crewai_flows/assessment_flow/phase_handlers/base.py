"""
Base class for Assessment Flow Phase Handlers.

This module contains the AssessmentPhaseHandlers base class that other
handler modules extend with specific phase handling logic.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select

from app.models.assessment_flow.core_models import (
    AssessmentFlow,
    EngagementArchitectureStandard,
)

logger = logging.getLogger(__name__)


class AssessmentPhaseHandlers:
    """Base class containing shared functionality for assessment phase handlers."""

    def __init__(self, flow_instance):
        """Initialize phase handlers with flow instance.

        Args:
            flow_instance: The UnifiedAssessmentFlow instance containing:
                - flow_id: Assessment flow ID
                - state: Assessment flow state
                - db: Database session
                - context: Request context with tenant info
                - flow_state_manager: State persistence manager
                - data_helper: Data loading helper
        """
        self.flow = flow_instance

    # Shared helper methods

    def _calculate_average_debt_score(self, tech_debt_results: Dict[str, Any]) -> float:
        """Calculate average technical debt score across applications."""
        if not tech_debt_results:
            return 0.0

        scores = [
            result.get("overall_score", 0.0) for result in tech_debt_results.values()
        ]
        return sum(scores) / len(scores)

    async def _apply_architecture_modifications(self, user_input: Dict[str, Any]):
        """Apply user modifications to architecture standards."""
        # TODO: Placeholder implementation - replace with actual modification logic
        # This should apply user-provided modifications to architecture standards
        # and validate the changes before committing
        pass

    def _validate_architecture_standards(self) -> Dict[str, Any]:
        """Validate architecture standards completeness."""
        # TODO: Placeholder implementation - replace with actual validation logic
        # This should check completeness of standards against requirements
        return {"is_valid": True, "missing_standards": [], "recommendations": []}

    async def _analyze_app_technical_debt(self, app: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical debt for a single application."""
        # TODO: Placeholder implementation - replace with actual tech debt analysis
        # This should integrate with code analysis tools and metrics collection
        return {
            "overall_score": 6.5,
            "categories": {"maintainability": 7.0, "security": 6.0, "performance": 6.5},
            "critical_issues": [
                "Legacy authentication system",
                "Outdated dependencies",
            ],
            "remediation_effort": "medium",
        }

    async def _load_engagement_standards_from_db(self) -> List[Dict[str, Any]]:
        """
        Load engagement architecture standards from the database.

        ADR-039: Required for validate_technology_compliance() to check
        technology versions against engagement-specific standards.

        Returns:
            List of engagement standards with supported_versions for compliance checking
        """
        try:
            db = self.flow.db
            engagement_id = UUID(str(self.flow.context.engagement_id))
            client_account_id = UUID(str(self.flow.context.client_account_id))

            # Query engagement standards with multi-tenant scoping
            stmt = select(EngagementArchitectureStandard).where(
                EngagementArchitectureStandard.engagement_id == engagement_id,
                EngagementArchitectureStandard.client_account_id == client_account_id,
            )
            result = await db.execute(stmt)
            standards = result.scalars().all()

            if not standards:
                logger.info(
                    f"No engagement standards found for engagement {engagement_id}, "
                    f"using default patterns"
                )
                # Return empty list - validate_technology_compliance handles missing standards
                return []

            # Convert to list of dicts matching validate_technology_compliance format
            standards_list = []
            for std in standards:
                std_dict = {
                    "requirement_type": std.requirement_type,
                    "standard_name": std.standard_name,
                    "description": std.description,
                    "mandatory": std.is_mandatory,
                    "priority": std.priority,
                    "business_impact": std.business_impact,
                    "supported_versions": std.supported_versions or {},
                    "requirement_details": std.requirement_details or {},
                    "minimum_requirements": std.minimum_requirements or {},
                }
                standards_list.append(std_dict)

            logger.info(
                f"Loaded {len(standards_list)} engagement standards for compliance validation"
            )
            return standards_list

        except Exception as e:
            logger.error(f"Failed to load engagement standards: {str(e)}")
            # Return empty list to gracefully degrade - compliance check will note "no standard defined"
            return []

    async def _persist_phase_results_to_database(
        self,
        phase: str,
        phase_data: Dict[str, Any],
    ) -> None:
        """
        Persist phase results to the AssessmentFlow.phase_results JSONB column.

        ADR-039: Ensures compliance validation and other phase data is stored
        in the database for downstream consumption and UI visibility.

        Args:
            phase: The phase name (e.g., "architecture_minimums")
            phase_data: The data to store for this phase
        """
        try:
            db = self.flow.db
            flow_id = self.flow.flow_id

            # Query the AssessmentFlow record - use master_flow_id since that's what MFO uses
            stmt = select(AssessmentFlow).where(
                AssessmentFlow.master_flow_id == UUID(str(flow_id)),
                AssessmentFlow.client_account_id
                == UUID(str(self.flow.context.client_account_id)),
                AssessmentFlow.engagement_id
                == UUID(str(self.flow.context.engagement_id)),
            )
            result = await db.execute(stmt)
            assessment_flow = result.scalar_one_or_none()

            if not assessment_flow:
                # Fallback: try querying by id (child flow scenario)
                stmt = select(AssessmentFlow).where(
                    AssessmentFlow.id == UUID(str(flow_id)),
                    AssessmentFlow.client_account_id
                    == UUID(str(self.flow.context.client_account_id)),
                    AssessmentFlow.engagement_id
                    == UUID(str(self.flow.context.engagement_id)),
                )
                result = await db.execute(stmt)
                assessment_flow = result.scalar_one_or_none()

            if not assessment_flow:
                logger.warning(
                    f"AssessmentFlow not found for flow_id {flow_id}, "
                    f"skipping phase_results persistence"
                )
                return

            # Update phase_results JSONB
            phase_results = assessment_flow.phase_results or {}
            phase_results[phase] = phase_data
            assessment_flow.phase_results = phase_results

            # Commit the update
            await db.commit()

            logger.info(
                f"✅ Phase results persisted to database for phase '{phase}' "
                f"(flow_id: {flow_id})"
            )

        except Exception as e:
            logger.error(f"Failed to persist phase results to database: {str(e)}")
            # Don't raise - this is a non-critical operation that shouldn't fail the phase
            # The in-memory state still has the data
