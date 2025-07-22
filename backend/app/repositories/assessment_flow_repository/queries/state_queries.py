"""
State Queries - State construction helper methods
"""
import logging
import uuid
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import (
    ApplicationArchitectureOverride,
    ApplicationComponent,
    ComponentTreatment,
    EngagementArchitectureStandard,
    SixRDecision,
    TechDebtAnalysis,
)
from app.models.assessment_flow_state import ApplicationArchitectureOverride as ApplicationArchitectureOverrideState
from app.models.assessment_flow_state import ApplicationComponent as ApplicationComponentState
from app.models.assessment_flow_state import ArchitectureRequirement, SixRStrategy, TechDebtItem
from app.models.assessment_flow_state import ComponentTreatment as ComponentTreatmentState
from app.models.assessment_flow_state import SixRDecision as SixRDecisionState

logger = logging.getLogger(__name__)


class StateQueries:
    """Helper queries for state construction"""
    
    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id
    
    async def get_architecture_standards(self, engagement_id: str) -> List[ArchitectureRequirement]:
        """Get architecture standards for engagement"""
        
        result = await self.db.execute(
            select(EngagementArchitectureStandard)
            .where(EngagementArchitectureStandard.engagement_id == engagement_id)
        )
        standards = result.scalars().all()
        
        return [
            ArchitectureRequirement(
                requirement_type=std.requirement_type,
                description=std.description,
                mandatory=std.mandatory,
                supported_versions=std.supported_versions,
                requirement_details=std.requirement_details,
                created_by=std.created_by,
                created_at=std.created_at,
                updated_at=std.updated_at
            )
            for std in standards
        ]
    
    async def get_application_overrides(self, flow_id: str) -> Dict[str, List[ApplicationArchitectureOverrideState]]:
        """Get application architecture overrides grouped by app"""
        
        result = await self.db.execute(
            select(ApplicationArchitectureOverride)
            .where(ApplicationArchitectureOverride.assessment_flow_id == flow_id)
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
                    created_at=override.created_at
                )
            )
        
        return grouped
    
    async def get_application_components(self, flow_id: str) -> Dict[str, List[ApplicationComponentState]]:
        """Get application components grouped by app"""
        
        result = await self.db.execute(
            select(ApplicationComponent)
            .where(ApplicationComponent.assessment_flow_id == flow_id)
        )
        components = result.scalars().all()
        
        grouped = {}
        for component in components:
            app_id = str(component.application_id)
            if app_id not in grouped:
                grouped[app_id] = []
            
            grouped[app_id].append(
                ApplicationComponentState(
                    component_name=component.component_name,
                    component_type=component.component_type,
                    technology_stack=component.technology_stack,
                    dependencies=component.dependencies
                )
            )
        
        return grouped
    
    async def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get tech debt analysis and scores grouped by app"""
        
        result = await self.db.execute(
            select(TechDebtAnalysis)
            .where(TechDebtAnalysis.assessment_flow_id == flow_id)
        )
        debt_items = result.scalars().all()
        
        analysis = {}
        scores = {}
        
        for item in debt_items:
            app_id = str(item.application_id)
            
            # Group tech debt items
            if app_id not in analysis:
                analysis[app_id] = []
            
            analysis[app_id].append(
                TechDebtItem(
                    category=item.debt_category,
                    severity=item.severity,
                    description=item.description,
                    remediation_effort_hours=item.remediation_effort_hours,
                    impact_on_migration=item.impact_on_migration,
                    tech_debt_score=item.tech_debt_score,
                    detected_by_agent=item.detected_by_agent,
                    agent_confidence=item.agent_confidence,
                    component_id=item.component_id
                )
            )
            
            # Calculate component-level scores
            if item.component_id and item.tech_debt_score:
                if app_id not in scores:
                    scores[app_id] = {}
                component_id = str(item.component_id)
                if component_id not in scores[app_id]:
                    scores[app_id][component_id] = 0.0
                scores[app_id][component_id] = max(scores[app_id][component_id], item.tech_debt_score)
        
        return {"analysis": analysis, "scores": scores}
    
    async def get_sixr_decisions(self, flow_id: str) -> Dict[str, SixRDecisionState]:
        """Get 6R decisions for all applications"""
        
        result = await self.db.execute(
            select(SixRDecision)
            .where(SixRDecision.assessment_flow_id == flow_id)
        )
        decisions = result.scalars().all()
        
        # Get component treatments for each app
        treatment_result = await self.db.execute(
            select(ComponentTreatment, ApplicationComponent.component_name)
            .join(ApplicationComponent, ComponentTreatment.component_id == ApplicationComponent.id)
            .where(ComponentTreatment.assessment_flow_id == flow_id)
        )
        treatments_data = treatment_result.fetchall()
        
        # Group treatments by app
        treatments_by_app = {}
        for treatment, component_name in treatments_data:
            app_id = str(treatment.application_id)
            if app_id not in treatments_by_app:
                treatments_by_app[app_id] = []
            
            treatments_by_app[app_id].append(
                ComponentTreatmentState(
                    component_name=component_name,
                    component_type=treatment.component_type,
                    recommended_strategy=SixRStrategy(treatment.recommended_strategy),
                    rationale=treatment.rationale,
                    compatibility_validated=treatment.compatibility_validated,
                    compatibility_issues=treatment.compatibility_issues
                )
            )
        
        # Build decision models
        decision_models = {}
        for decision in decisions:
            app_id = str(decision.application_id)
            
            decision_models[app_id] = SixRDecisionState(
                application_id=uuid.UUID(decision.application_id),
                application_name=decision.application_name,
                component_treatments=treatments_by_app.get(app_id, []),
                overall_strategy=SixRStrategy(decision.overall_strategy),
                confidence_score=decision.confidence_score,
                rationale=decision.rationale,
                architecture_exceptions=decision.architecture_exceptions or [],
                tech_debt_score=decision.tech_debt_score,
                risk_factors=decision.risk_factors or [],
                estimated_effort_hours=decision.estimated_effort_hours,
                estimated_cost=decision.estimated_cost,
                move_group_hints=decision.move_group_hints or [],
                user_modifications=decision.user_modifications,
                modified_by=decision.modified_by,
                modified_at=decision.modified_at,
                app_on_page_data=decision.app_on_page_data,
                decision_factors=decision.decision_factors,
                ready_for_planning=decision.ready_for_planning
            )
        
        return decision_models