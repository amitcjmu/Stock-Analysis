"""
Decision Commands - 6R decision management
"""
import logging
from datetime import datetime
from typing import List

from sqlalchemy import and_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentFlow, SixRDecision
from app.models.assessment_flow_state import SixRDecision as SixRDecisionState

logger = logging.getLogger(__name__)


class DecisionCommands:
    """Commands for 6R decision management"""
    
    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id
    
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