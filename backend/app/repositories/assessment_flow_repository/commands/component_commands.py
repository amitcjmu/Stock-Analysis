"""
Component Commands - Application components and tech debt management
"""
import logging
from typing import List

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import ApplicationComponent, ComponentTreatment, TechDebtAnalysis
from app.models.assessment_flow_state import ApplicationComponent as ApplicationComponentState
from app.models.assessment_flow_state import ComponentTreatment as ComponentTreatmentState
from app.models.assessment_flow_state import TechDebtItem

logger = logging.getLogger(__name__)


class ComponentCommands:
    """Commands for application components and tech debt management"""
    
    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id
    
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