"""
State Queries - State construction helper methods

GAP-4 FIX: Implements actual database queries for application components,
tech debt analysis, and 6R decisions. These were previously stubbed with
incorrect comments claiming the tables lacked assessment_flow_id columns.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import (
    ApplicationArchitectureOverride,
    EngagementArchitectureStandard,
)
from app.models.assessment_flow.analysis_models import (
    SixRDecision,
    TechDebtAnalysis,
)
from app.models.assessment_flow.component_models import (
    ApplicationComponent,
    ComponentTreatment,
)
from app.models.assessment_flow_state import (
    ApplicationArchitectureOverride as ApplicationArchitectureOverrideState,
)
from app.models.assessment_flow_state import ArchitectureRequirement

logger = logging.getLogger(__name__)


class StateQueries:
    """Helper queries for state construction"""

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id

    async def get_architecture_standards(
        self, engagement_id: str
    ) -> List[ArchitectureRequirement]:
        """Get architecture standards for engagement"""

        result = await self.db.execute(
            select(EngagementArchitectureStandard).where(
                EngagementArchitectureStandard.engagement_id == engagement_id
            )
        )
        standards = result.scalars().all()

        return [
            ArchitectureRequirement(
                requirement_type=std.requirement_type,
                description=std.description,
                mandatory=std.is_mandatory,  # Fixed: Use is_mandatory from database
                supported_versions=std.supported_versions,
                requirement_details=std.requirement_details,
                created_at=std.created_at,
                updated_at=std.updated_at,
            )
            for std in standards
        ]

    async def get_application_overrides(
        self, flow_id: str
    ) -> Dict[str, List[ApplicationArchitectureOverrideState]]:
        """Get application architecture overrides grouped by app"""

        result = await self.db.execute(
            select(ApplicationArchitectureOverride).where(
                ApplicationArchitectureOverride.assessment_flow_id == flow_id
            )
        )
        overrides = result.scalars().all()

        grouped = {}
        for override in overrides:
            app_id = str(override.application_id)
            if app_id not in grouped:
                grouped[app_id] = []

            grouped[app_id].append(
                ApplicationArchitectureOverrideState(
                    application_id=override.application_id,
                    standard_id=override.standard_id,
                    override_type=override.override_type,
                    override_details=override.override_details,
                    rationale=override.rationale,
                    approved_by=override.approved_by,
                    created_at=override.created_at,
                )
            )

        return grouped

    async def get_application_components(self, flow_id: str) -> Dict[str, List[Any]]:
        """Get application components grouped by application_id.

        GAP-4 FIX: Implements actual query against application_components table.
        The ApplicationComponent model DOES have assessment_flow_id FK.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dict mapping application_id to list of component dicts
        """
        try:
            flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

            result = await self.db.execute(
                select(ApplicationComponent).where(
                    ApplicationComponent.assessment_flow_id == flow_uuid
                )
            )
            components = result.scalars().all()

            # Group components by application_id
            grouped: Dict[str, List[Any]] = {}
            for comp in components:
                app_id = str(comp.application_id)
                if app_id not in grouped:
                    grouped[app_id] = []

                grouped[app_id].append(
                    {
                        "id": str(comp.id),
                        "component_name": comp.component_name,
                        "component_type": comp.component_type,
                        "description": comp.description,
                        "current_technology": comp.current_technology,
                        "version": comp.version,
                        "configuration": comp.configuration or {},
                        "dependencies": comp.dependencies or [],
                        "complexity_score": comp.complexity_score,
                        "business_criticality": comp.business_criticality,
                        "technical_debt_score": comp.technical_debt_score,
                        "migration_readiness": comp.migration_readiness,
                        "recommended_approach": comp.recommended_approach,
                        "estimated_effort": comp.estimated_effort,
                        "assessment_status": comp.assessment_status,
                        "assessment_progress": comp.assessment_progress,
                    }
                )

            logger.debug(
                f"Retrieved {len(components)} components for flow {flow_id}, "
                f"grouped into {len(grouped)} applications"
            )
            return grouped

        except Exception as e:
            logger.error(f"Error fetching application components: {e}")
            return {}

    async def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get tech debt analysis and scores grouped by application_id.

        GAP-4 FIX: Implements actual query against tech_debt_analyses table.
        The TechDebtAnalysis model DOES have assessment_flow_id FK.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dict with 'analysis' (app_id -> list of debt items) and
            'scores' (app_id -> aggregated scores)
        """
        try:
            flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

            result = await self.db.execute(
                select(TechDebtAnalysis).where(
                    TechDebtAnalysis.assessment_flow_id == flow_uuid
                )
            )
            debt_items = result.scalars().all()

            # Group analysis by application_id
            analysis: Dict[str, List[Any]] = {}
            scores: Dict[str, Dict[str, Any]] = {}

            for debt in debt_items:
                app_id = str(debt.application_id)

                # Initialize structures for this app
                if app_id not in analysis:
                    analysis[app_id] = []
                    scores[app_id] = {
                        "total_debt_score": 0.0,
                        "total_impact_score": 0.0,
                        "total_effort_score": 0.0,
                        "item_count": 0,
                        "severity_counts": {
                            "critical": 0,
                            "high": 0,
                            "medium": 0,
                            "low": 0,
                        },
                    }

                # Add analysis item
                analysis[app_id].append(
                    {
                        "id": str(debt.id),
                        "debt_type": debt.debt_type,
                        "debt_category": debt.debt_category,
                        "severity": debt.severity,
                        "description": debt.description,
                        "root_cause": debt.root_cause,
                        "impact_analysis": debt.impact_analysis or {},
                        "debt_score": debt.debt_score,
                        "impact_score": debt.impact_score,
                        "effort_score": debt.effort_score,
                        "priority_score": debt.priority_score,
                        "remediation_strategy": debt.remediation_strategy,
                        "estimated_effort": debt.estimated_effort,
                        "recommended_timeline": debt.recommended_timeline,
                        "status": debt.status,
                        "confidence_level": debt.confidence_level,
                    }
                )

                # Aggregate scores
                scores[app_id]["item_count"] += 1
                if debt.debt_score:
                    scores[app_id]["total_debt_score"] += debt.debt_score
                if debt.impact_score:
                    scores[app_id]["total_impact_score"] += debt.impact_score
                if debt.effort_score:
                    scores[app_id]["total_effort_score"] += debt.effort_score

                # Count by severity
                severity = (debt.severity or "medium").lower()
                if severity in scores[app_id]["severity_counts"]:
                    scores[app_id]["severity_counts"][severity] += 1

            # Calculate average scores
            for app_id, score_data in scores.items():
                count = score_data["item_count"]
                if count > 0:
                    score_data["avg_debt_score"] = (
                        score_data["total_debt_score"] / count
                    )
                    score_data["avg_impact_score"] = (
                        score_data["total_impact_score"] / count
                    )
                    score_data["avg_effort_score"] = (
                        score_data["total_effort_score"] / count
                    )

            logger.debug(
                f"Retrieved {len(debt_items)} tech debt items for flow {flow_id}, "
                f"grouped into {len(analysis)} applications"
            )
            return {"analysis": analysis, "scores": scores}

        except Exception as e:
            logger.error(f"Error fetching tech debt analysis: {e}")
            return {"analysis": {}, "scores": {}}

    async def get_sixr_decisions(self, flow_id: str) -> Dict[str, Any]:
        """Get 6R decisions grouped by application_id.

        GAP-4 FIX: Implements actual query against sixr_decisions table.
        The SixRDecision model DOES have assessment_flow_id FK.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dict mapping application_id to decision dict (or list if multiple components)
        """
        try:
            flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

            result = await self.db.execute(
                select(SixRDecision).where(SixRDecision.assessment_flow_id == flow_uuid)
            )
            decisions = result.scalars().all()

            # Group decisions by application_id
            # For applications with multiple component-level decisions, store as list
            grouped: Dict[str, Any] = {}

            for decision in decisions:
                app_id = str(decision.application_id)

                decision_dict = {
                    "id": str(decision.id),
                    "application_id": app_id,
                    "component_id": (
                        str(decision.component_id) if decision.component_id else None
                    ),
                    "sixr_strategy": decision.sixr_strategy,
                    "decision_rationale": decision.decision_rationale,
                    "alternative_strategies": decision.alternative_strategies or [],
                    "analysis_details": decision.analysis_details or {},
                    "confidence_score": decision.confidence_score,
                    "risk_assessment": decision.risk_assessment or {},
                    "implementation_approach": decision.implementation_approach,
                    "estimated_effort": decision.estimated_effort,
                    "estimated_duration": decision.estimated_duration,
                    "estimated_cost": decision.estimated_cost,
                    "dependencies": decision.dependencies or [],
                    "constraints": decision.constraints or [],
                    "assumptions": decision.assumptions or [],
                    "success_criteria": decision.success_criteria or [],
                    "business_value": decision.business_value,
                    "business_priority": decision.business_priority,
                    "decision_status": decision.decision_status,
                    "approval_status": decision.approval_status,
                    "decided_by": decision.decided_by,
                    "decision_date": (
                        decision.decision_date.isoformat()
                        if decision.decision_date
                        else None
                    ),
                }

                # If this is an app-level decision (no component_id), store directly
                # If there's already a decision for this app, convert to list
                if app_id not in grouped:
                    grouped[app_id] = decision_dict
                elif isinstance(grouped[app_id], list):
                    grouped[app_id].append(decision_dict)
                else:
                    # Convert to list when we encounter multiple decisions per app
                    grouped[app_id] = [grouped[app_id], decision_dict]

            logger.debug(
                f"Retrieved {len(decisions)} 6R decisions for flow {flow_id}, "
                f"covering {len(grouped)} applications"
            )
            return grouped

        except Exception as e:
            logger.error(f"Error fetching 6R decisions: {e}")
            return {}

    async def get_component_treatments(self, flow_id: str) -> Dict[str, List[Any]]:
        """Get component treatments grouped by application_id.

        GAP-4 FIX: Additional method for retrieving component-level treatments.
        The ComponentTreatment model has assessment_flow_id FK.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dict mapping application_id to list of treatment dicts
        """
        try:
            flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

            # Join with ApplicationComponent to get application_id
            result = await self.db.execute(
                select(ComponentTreatment, ApplicationComponent)
                .join(
                    ApplicationComponent,
                    ComponentTreatment.component_id == ApplicationComponent.id,
                )
                .where(ComponentTreatment.assessment_flow_id == flow_uuid)
            )
            rows = result.all()

            # Group treatments by application_id
            grouped: Dict[str, List[Any]] = {}

            for treatment, component in rows:
                app_id = str(component.application_id)

                if app_id not in grouped:
                    grouped[app_id] = []

                grouped[app_id].append(
                    {
                        "id": str(treatment.id),
                        "component_id": str(treatment.component_id),
                        "component_name": component.component_name,
                        "component_type": component.component_type,
                        "treatment_type": treatment.treatment_type,
                        "strategy": treatment.strategy,
                        "approach": treatment.approach,
                        "analysis": treatment.analysis,
                        "reasoning": treatment.reasoning,
                        "assumptions": treatment.assumptions or [],
                        "confidence_score": treatment.confidence_score,
                        "risk_assessment": treatment.risk_assessment or {},
                        "risk_level": treatment.risk_level,
                        "implementation_plan": treatment.implementation_plan or {},
                        "prerequisites": treatment.prerequisites or [],
                        "success_criteria": treatment.success_criteria or [],
                    }
                )

            logger.debug(
                f"Retrieved {len(rows)} component treatments for flow {flow_id}, "
                f"grouped into {len(grouped)} applications"
            )
            return grouped

        except Exception as e:
            logger.error(f"Error fetching component treatments: {e}")
            return {}
