"""
Flow Specifications - Query specifications and filters
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FlowSpecifications:
    """Query specifications and utility methods for assessment flows"""
    
    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id
    
    async def update_master_flow_status(
        self, 
        flow_id: str, 
        status: str, 
        current_phase: str,
        phase_data: Optional[Dict[str, Any]] = None
    ):
        """Update master flow status and phase data"""
        from app.models.assessment_flow import AssessmentFlow
        from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
        
        try:
            # Get engagement_id for this flow
            result = await self.db.execute(
                select(AssessmentFlow.engagement_id)
                .where(AssessmentFlow.id == flow_id)
            )
            engagement_id = result.scalar()
            
            if engagement_id:
                extensions_repo = CrewAIFlowStateExtensionsRepository(
                    self.db, 
                    str(self.client_account_id), 
                    str(engagement_id)
                )
                
                # Prepare phase data
                update_phase_data = {
                    "current_phase": current_phase,
                    "timestamp": datetime.utcnow().isoformat()
                }
                if phase_data:
                    update_phase_data.update(phase_data)
                
                # Update master flow
                await extensions_repo.update_flow_status(
                    flow_id=str(flow_id),
                    status=status,
                    phase_data=update_phase_data
                )
                
                logger.info(f"Updated master flow status for assessment flow {flow_id}")
                
        except Exception as e:
            logger.error(f"Failed to update master flow status for {flow_id}: {e}")
            # Don't fail the operation if master flow update fails
    
    async def log_agent_collaboration(
        self, 
        flow_id: str, 
        phase: str, 
        insights: List[Dict[str, Any]]
    ):
        """Log agent collaboration to master flow"""
        from app.models.assessment_flow import AssessmentFlow
        from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
        
        try:
            # Get engagement_id for this flow
            result = await self.db.execute(
                select(AssessmentFlow.engagement_id)
                .where(AssessmentFlow.id == flow_id)
            )
            engagement_id = result.scalar()
            
            if engagement_id:
                extensions_repo = CrewAIFlowStateExtensionsRepository(
                    self.db, 
                    str(self.client_account_id), 
                    str(engagement_id)
                )
                
                # Get the master flow record
                master_flow = await extensions_repo.get_by_flow_id(str(flow_id))
                if master_flow:
                    # Log each insight as agent collaboration
                    for insight in insights:
                        agent_name = insight.get("agent", "AssessmentAgent")
                        action = f"phase_{phase}_insight"
                        
                        master_flow.add_agent_collaboration_entry(
                            agent_name=agent_name,
                            action=action,
                            details={
                                "phase": phase,
                                "insight": insight,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                    
                    # Save the updated master flow
                    await self.db.commit()
                    logger.info(f"Logged {len(insights)} agent collaborations to master flow")
                
        except Exception as e:
            logger.error(f"Failed to log agent collaboration for {flow_id}: {e}")
            # Don't fail the operation if master flow update fails