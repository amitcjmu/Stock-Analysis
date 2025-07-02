"""
Assessment Flow Repository Pattern
Multi-tenant repository with ContextAwareRepository inheritance, complex JSONB queries and efficient state persistence.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.repositories.base import ContextAwareRepository
from app.models.assessment_flow import (
    AssessmentFlow,
    EngagementArchitectureStandard,
    ApplicationArchitectureOverride,
    ApplicationComponent,
    TechDebtAnalysis,
    ComponentTreatment,
    SixRDecision,
    AssessmentLearningFeedback
)
from app.models.assessment_flow_state import (
    AssessmentFlowState,
    SixRStrategy,
    AssessmentPhase,
    AssessmentFlowStatus,
    ArchitectureRequirement,
    ApplicationArchitectureOverride as ApplicationArchitectureOverrideState,
    ApplicationComponent as ApplicationComponentState,
    TechDebtItem,
    ComponentTreatment as ComponentTreatmentState,
    SixRDecision as SixRDecisionState,
    AssessmentLearningFeedback as AssessmentLearningFeedbackState
)

logger = logging.getLogger(__name__)

class AssessmentFlowRepository(ContextAwareRepository):
    """Repository for assessment flow data access with multi-tenant support"""
    
    def __init__(self, db: AsyncSession, client_account_id: int, engagement_id: Optional[int] = None, user_id: Optional[str] = None):
        super().__init__(db, client_account_id, engagement_id, user_id)
    
    # === FLOW MANAGEMENT ===
    
    async def create_assessment_flow(
        self, 
        engagement_id: str,
        selected_application_ids: List[str],
        created_by: Optional[str] = None
    ) -> str:
        """Create new assessment flow with initial state"""
        
        flow_record = AssessmentFlow(
            client_account_id=self.client_account_id,
            engagement_id=engagement_id,
            selected_application_ids=selected_application_ids,
            status=AssessmentFlowStatus.INITIALIZED.value,
            current_phase=AssessmentPhase.INITIALIZATION.value,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(flow_record)
        await self.db.commit()
        await self.db.refresh(flow_record)
        
        logger.info(f"Created assessment flow {flow_record.id} for engagement {engagement_id}")
        return str(flow_record.id)
    
    async def get_assessment_flow_state(self, flow_id: str) -> Optional[AssessmentFlowState]:
        """Get complete assessment flow state with all related data"""
        
        # Get main flow record with eager loading
        result = await self.db.execute(
            select(AssessmentFlow)
            .options(
                selectinload(AssessmentFlow.architecture_standards),
                selectinload(AssessmentFlow.application_overrides),
                selectinload(AssessmentFlow.application_components),
                selectinload(AssessmentFlow.tech_debt_analysis),
                selectinload(AssessmentFlow.component_treatments),
                selectinload(AssessmentFlow.sixr_decisions),
                selectinload(AssessmentFlow.learning_feedback)
            )
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
        )
        flow = result.scalar_one_or_none()
        if not flow:
            return None
        
        # Convert to Pydantic state model
        try:
            # Get architecture standards
            arch_standards = await self._get_architecture_standards(flow.engagement_id)
            
            # Get application overrides grouped by app
            app_overrides = await self._get_application_overrides(flow_id)
            
            # Get application components grouped by app
            app_components = await self._get_application_components(flow_id)
            
            # Get tech debt analysis grouped by app
            tech_debt = await self._get_tech_debt_analysis(flow_id)
            
            # Get 6R decisions
            sixr_decisions = await self._get_sixr_decisions(flow_id)
            
            return AssessmentFlowState(
                flow_id=flow.id,
                client_account_id=flow.client_account_id,
                engagement_id=flow.engagement_id,
                selected_application_ids=[uuid.UUID(app_id) for app_id in flow.selected_application_ids],
                engagement_architecture_standards=arch_standards,
                application_architecture_overrides=app_overrides,
                architecture_captured=flow.architecture_captured,
                application_components=app_components,
                tech_debt_analysis=tech_debt["analysis"],
                component_tech_debt=tech_debt["scores"],
                sixr_decisions=sixr_decisions,
                pause_points=flow.pause_points or [],
                user_inputs=flow.user_inputs or {},
                status=AssessmentFlowStatus(flow.status),
                progress=flow.progress,
                current_phase=AssessmentPhase(flow.current_phase) if flow.current_phase else AssessmentPhase.INITIALIZATION,
                next_phase=AssessmentPhase(flow.next_phase) if flow.next_phase else None,
                phase_results=flow.phase_results or {},
                agent_insights=flow.agent_insights or [],
                apps_ready_for_planning=[uuid.UUID(app_id) for app_id in flow.apps_ready_for_planning],
                created_at=flow.created_at,
                updated_at=flow.updated_at,
                last_user_interaction=flow.last_user_interaction,
                completed_at=flow.completed_at
            )
            
        except Exception as e:
            logger.error(f"Failed to convert flow {flow_id} to state model: {str(e)}")
            raise
    
    async def update_flow_phase(
        self, 
        flow_id: str, 
        current_phase: str,
        next_phase: Optional[str] = None,
        progress: Optional[int] = None,
        status: Optional[str] = None
    ):
        """Update flow phase and progress"""
        
        update_data = {
            "current_phase": current_phase,
            "updated_at": datetime.utcnow()
        }
        
        if next_phase:
            update_data["next_phase"] = next_phase
        if progress is not None:
            update_data["progress"] = progress
        if status:
            update_data["status"] = status
            
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .values(**update_data)
        )
        await self.db.commit()
        
        logger.info(f"Updated flow {flow_id} phase to {current_phase}")
    
    async def save_user_input(
        self, 
        flow_id: str, 
        phase: str, 
        user_input: Dict[str, Any]
    ):
        """Save user input for specific phase"""
        
        # Get current user_inputs
        result = await self.db.execute(
            select(AssessmentFlow.user_inputs)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
        )
        current_inputs = result.scalar() or {}
        current_inputs[phase] = user_input
        
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .values(
                user_inputs=current_inputs,
                last_user_interaction=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
    
    async def save_agent_insights(
        self,
        flow_id: str,
        phase: str,
        insights: List[Dict[str, Any]]
    ):
        """Save agent insights for specific phase"""
        
        # Get current agent insights
        result = await self.db.execute(
            select(AssessmentFlow.agent_insights)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
        )
        current_insights = result.scalar() or []
        
        # Add phase context to insights
        phase_insights = [
            {**insight, "phase": phase, "timestamp": datetime.utcnow().isoformat()}
            for insight in insights
        ]
        current_insights.extend(phase_insights)
        
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .values(
                agent_insights=current_insights,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.commit()
    
    # === ARCHITECTURE STANDARDS MANAGEMENT ===
    
    async def save_architecture_standards(
        self,
        engagement_id: str,
        standards: List[ArchitectureRequirement]
    ):
        """Save or update engagement architecture standards"""
        
        for standard in standards:
            stmt = insert(EngagementArchitectureStandard).values(
                engagement_id=engagement_id,
                requirement_type=standard.requirement_type,
                description=standard.description,
                mandatory=standard.mandatory,
                supported_versions=standard.supported_versions,
                requirement_details=standard.requirement_details,
                created_by=standard.created_by or "system",
                updated_at=datetime.utcnow()
            )
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['engagement_id', 'requirement_type'],
                set_=dict(
                    description=stmt.excluded.description,
                    mandatory=stmt.excluded.mandatory,
                    supported_versions=stmt.excluded.supported_versions,
                    requirement_details=stmt.excluded.requirement_details,
                    updated_at=stmt.excluded.updated_at
                )
            )
            
            await self.db.execute(stmt)
        
        await self.db.commit()
        logger.info(f"Saved {len(standards)} architecture standards for engagement {engagement_id}")
    
    async def save_application_overrides(
        self,
        flow_id: str,
        app_id: str,
        overrides: List[ApplicationArchitectureOverrideState]
    ):
        """Save application architecture overrides"""
        
        # Delete existing overrides for this app in this flow
        await self.db.execute(
            delete(ApplicationArchitectureOverride)
            .where(
                and_(
                    ApplicationArchitectureOverride.assessment_flow_id == flow_id,
                    ApplicationArchitectureOverride.application_id == app_id
                )
            )
        )
        
        # Insert new overrides
        for override in overrides:
            override_record = ApplicationArchitectureOverride(
                assessment_flow_id=flow_id,
                application_id=app_id,
                standard_id=override.standard_id,
                override_type=override.override_type.value,
                override_details=override.override_details,
                rationale=override.rationale,
                approved_by=override.approved_by
            )
            self.db.add(override_record)
        
        await self.db.commit()
    
    # === COMPONENT MANAGEMENT ===
    
    async def save_application_components(
        self,
        flow_id: str,
        app_id: str,
        components: List[ApplicationComponentState]
    ):
        """Save application components for specific app"""
        
        # Delete existing components for this app in this flow
        await self.db.execute(
            delete(ApplicationComponent)
            .where(
                and_(
                    ApplicationComponent.assessment_flow_id == flow_id,
                    ApplicationComponent.application_id == app_id
                )
            )
        )
        
        # Insert new components
        for component in components:
            component_record = ApplicationComponent(
                assessment_flow_id=flow_id,
                application_id=app_id,
                component_name=component.component_name,
                component_type=component.component_type.value,
                technology_stack=component.technology_stack,
                dependencies=component.dependencies
            )
            self.db.add(component_record)
        
        await self.db.commit()
        logger.info(f"Saved {len(components)} components for app {app_id}")
    
    async def save_tech_debt_analysis(
        self,
        flow_id: str,
        app_id: str,
        tech_debt_items: List[TechDebtItem]
    ):
        """Save tech debt analysis for application"""
        
        # Delete existing tech debt for this app
        await self.db.execute(
            delete(TechDebtAnalysis)
            .where(
                and_(
                    TechDebtAnalysis.assessment_flow_id == flow_id,
                    TechDebtAnalysis.application_id == app_id
                )
            )
        )
        
        # Insert new tech debt items
        for item in tech_debt_items:
            debt_record = TechDebtAnalysis(
                assessment_flow_id=flow_id,
                application_id=app_id,
                component_id=item.component_id,
                debt_category=item.category,
                severity=item.severity.value,
                description=item.description,
                remediation_effort_hours=item.remediation_effort_hours,
                impact_on_migration=item.impact_on_migration,
                tech_debt_score=item.tech_debt_score,
                detected_by_agent=item.detected_by_agent,
                agent_confidence=item.agent_confidence
            )
            self.db.add(debt_record)
        
        await self.db.commit()
        logger.info(f"Saved {len(tech_debt_items)} tech debt items for app {app_id}")
    
    async def save_component_treatments(
        self,
        flow_id: str,
        app_id: str,
        treatments: List[ComponentTreatmentState]
    ):
        """Save component treatments for application"""
        
        # Delete existing treatments for this app
        await self.db.execute(
            delete(ComponentTreatment)
            .where(
                and_(
                    ComponentTreatment.assessment_flow_id == flow_id,
                    ComponentTreatment.application_id == app_id
                )
            )
        )
        
        # Get component IDs by name for this app
        component_result = await self.db.execute(
            select(ApplicationComponent.id, ApplicationComponent.component_name)
            .where(
                and_(
                    ApplicationComponent.assessment_flow_id == flow_id,
                    ApplicationComponent.application_id == app_id
                )
            )
        )
        component_map = {name: comp_id for comp_id, name in component_result.fetchall()}
        
        # Insert new treatments
        for treatment in treatments:
            component_id = component_map.get(treatment.component_name)
            treatment_record = ComponentTreatment(
                assessment_flow_id=flow_id,
                application_id=app_id,
                component_id=component_id,
                recommended_strategy=treatment.recommended_strategy.value,
                rationale=treatment.rationale,
                compatibility_validated=treatment.compatibility_validated,
                compatibility_issues=treatment.compatibility_issues
            )
            self.db.add(treatment_record)
        
        await self.db.commit()
        logger.info(f"Saved {len(treatments)} component treatments for app {app_id}")
    
    # === 6R DECISION MANAGEMENT ===
    
    async def save_sixr_decision(
        self,
        flow_id: str,
        decision: SixRDecisionState
    ):
        """Save or update 6R decision for application"""
        
        stmt = insert(SixRDecision).values(
            assessment_flow_id=flow_id,
            application_id=str(decision.application_id),
            application_name=decision.application_name,
            overall_strategy=decision.overall_strategy.value,
            confidence_score=decision.confidence_score,
            rationale=decision.rationale,
            architecture_exceptions=decision.architecture_exceptions,
            tech_debt_score=decision.tech_debt_score,
            risk_factors=decision.risk_factors,
            move_group_hints=decision.move_group_hints,
            estimated_effort_hours=decision.estimated_effort_hours,
            estimated_cost=decision.estimated_cost,
            user_modifications=decision.user_modifications,
            modified_by=decision.modified_by,
            modified_at=decision.modified_at,
            app_on_page_data=decision.app_on_page_data,
            decision_factors=decision.decision_factors,
            ready_for_planning=decision.ready_for_planning,
            updated_at=datetime.utcnow()
        )
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['assessment_flow_id', 'application_id'],
            set_=dict(
                overall_strategy=stmt.excluded.overall_strategy,
                confidence_score=stmt.excluded.confidence_score,
                rationale=stmt.excluded.rationale,
                architecture_exceptions=stmt.excluded.architecture_exceptions,
                tech_debt_score=stmt.excluded.tech_debt_score,
                risk_factors=stmt.excluded.risk_factors,
                move_group_hints=stmt.excluded.move_group_hints,
                user_modifications=stmt.excluded.user_modifications,
                modified_by=stmt.excluded.modified_by,
                modified_at=stmt.excluded.modified_at,
                app_on_page_data=stmt.excluded.app_on_page_data,
                decision_factors=stmt.excluded.decision_factors,
                ready_for_planning=stmt.excluded.ready_for_planning,
                updated_at=stmt.excluded.updated_at
            )
        )
        
        await self.db.execute(stmt)
        
        # Save component treatments
        await self.save_component_treatments(flow_id, str(decision.application_id), decision.component_treatments)
        
        await self.db.commit()
        logger.info(f"Saved 6R decision for app {decision.application_name}")
    
    async def mark_apps_ready_for_planning(
        self,
        flow_id: str,
        app_ids: List[str]
    ):
        """Mark applications as ready for planning flow"""
        
        # Update individual decisions
        await self.db.execute(
            update(SixRDecision)
            .where(
                and_(
                    SixRDecision.assessment_flow_id == flow_id,
                    SixRDecision.application_id.in_(app_ids)
                )
            )
            .values(ready_for_planning=True)
        )
        
        # Update flow apps_ready_for_planning list
        await self.db.execute(
            update(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .values(apps_ready_for_planning=app_ids)
        )
        
        await self.db.commit()
        logger.info(f"Marked {len(app_ids)} apps ready for planning")
    
    # === LEARNING FEEDBACK ===
    
    async def save_learning_feedback(
        self,
        flow_id: str,
        decision_id: str,
        feedback: AssessmentLearningFeedbackState
    ):
        """Save learning feedback for agent improvement"""
        
        feedback_record = AssessmentLearningFeedback(
            assessment_flow_id=flow_id,
            decision_id=decision_id,
            original_strategy=feedback.original_strategy.value,
            override_strategy=feedback.override_strategy.value,
            feedback_reason=feedback.feedback_reason,
            agent_id=feedback.agent_id,
            learned_pattern=feedback.learned_pattern
        )
        
        self.db.add(feedback_record)
        await self.db.commit()
    
    # === QUERY METHODS ===
    
    async def get_flows_by_engagement(self, engagement_id: str, limit: int = 50) -> List[AssessmentFlow]:
        """Get all assessment flows for an engagement"""
        
        result = await self.db.execute(
            select(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.engagement_id == engagement_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .order_by(AssessmentFlow.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_flows_by_status(self, status: str, limit: int = 50) -> List[AssessmentFlow]:
        """Get flows by status"""
        
        result = await self.db.execute(
            select(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.status == status,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .order_by(AssessmentFlow.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search_flows_by_application(self, app_id: str) -> List[AssessmentFlow]:
        """Find flows that include a specific application"""
        
        result = await self.db.execute(
            select(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.selected_application_ids.contains([app_id]),
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
            .order_by(AssessmentFlow.updated_at.desc())
        )
        return result.scalars().all()
    
    async def get_flow_analytics(self, flow_id: str) -> Dict[str, Any]:
        """Get analytics data for a flow"""
        
        # Get basic flow info
        flow_result = await self.db.execute(
            select(AssessmentFlow)
            .where(
                and_(
                    AssessmentFlow.id == flow_id,
                    AssessmentFlow.client_account_id == self.client_account_id
                )
            )
        )
        flow = flow_result.scalar_one_or_none()
        if not flow:
            return {}
        
        # Get strategy distribution
        strategy_result = await self.db.execute(
            select(SixRDecision.overall_strategy, func.count(SixRDecision.id))
            .where(SixRDecision.assessment_flow_id == flow_id)
            .group_by(SixRDecision.overall_strategy)
        )
        strategy_distribution = dict(strategy_result.fetchall())
        
        # Get tech debt severity distribution
        debt_result = await self.db.execute(
            select(TechDebtAnalysis.severity, func.count(TechDebtAnalysis.id))
            .where(TechDebtAnalysis.assessment_flow_id == flow_id)
            .group_by(TechDebtAnalysis.severity)
        )
        debt_distribution = dict(debt_result.fetchall())
        
        # Get component type distribution
        component_result = await self.db.execute(
            select(ApplicationComponent.component_type, func.count(ApplicationComponent.id))
            .where(ApplicationComponent.assessment_flow_id == flow_id)
            .group_by(ApplicationComponent.component_type)
        )
        component_distribution = dict(component_result.fetchall())
        
        return {
            "flow_summary": {
                "id": str(flow.id),
                "status": flow.status,
                "progress": flow.progress,
                "current_phase": flow.current_phase,
                "total_applications": len(flow.selected_application_ids),
                "apps_ready_for_planning": len(flow.apps_ready_for_planning or [])
            },
            "strategy_distribution": strategy_distribution,
            "tech_debt_distribution": debt_distribution,
            "component_distribution": component_distribution,
            "created_at": flow.created_at.isoformat(),
            "updated_at": flow.updated_at.isoformat()
        }
    
    # === PRIVATE HELPER METHODS ===
    
    async def _get_architecture_standards(self, engagement_id: str) -> List[ArchitectureRequirement]:
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
    
    async def _get_application_overrides(self, flow_id: str) -> Dict[str, List[ApplicationArchitectureOverrideState]]:
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
    
    async def _get_application_components(self, flow_id: str) -> Dict[str, List[ApplicationComponentState]]:
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
    
    async def _get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
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
    
    async def _get_sixr_decisions(self, flow_id: str) -> Dict[str, SixRDecisionState]:
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