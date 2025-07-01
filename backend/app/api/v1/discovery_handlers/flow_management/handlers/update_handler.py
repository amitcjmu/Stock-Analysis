"""
Update Handler

Handles flow update operations including phase execution and continuation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from ..validators.flow_validator import FlowValidator
from ..services.flow_service import FlowService

logger = logging.getLogger(__name__)


class UpdateHandler:
    """Handles flow update operations"""
    
    def __init__(self, db: AsyncSession, flow_repo: DiscoveryFlowRepository):
        """Initialize with database session and flow repository"""
        self.db = db
        self.flow_repo = flow_repo
        self.flow_validator = FlowValidator(flow_repo)
        self.flow_service = FlowService(db)
    
    async def continue_flow(self, flow_id: str) -> Dict[str, Any]:
        """Continue flow to the next phase"""
        try:
            logger.info(f"▶️ Continuing flow: {flow_id}")
            
            # Get flow from database
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            if not flow:
                logger.warning(f"Flow not found: {flow_id}")
                return {
                    "status": "error",
                    "message": f"Flow {flow_id} not found"
                }
            
            # Validate and determine next phase
            next_phase = await self.flow_validator.validate_and_get_next_phase(flow)
            
            if next_phase == "completed":
                # Flow is complete
                flow.status = "completed"
                await self.db.commit()
                
                return {
                    "status": "completed",
                    "message": "All phases completed successfully",
                    "flow_id": flow_id,
                    "next_phase": None,
                    "progress": 100.0
                }
            
            # Update flow to next phase
            flow.current_phase = next_phase
            flow.status = "active"
            flow.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"✅ Flow continued to phase: {next_phase}")
            
            return {
                "status": "success",
                "message": f"Flow continued to {next_phase}",
                "flow_id": flow_id,
                "next_phase": next_phase,
                "progress": self._calculate_progress(flow)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to continue flow: {e}")
            return {
                "status": "error",
                "message": f"Failed to continue flow: {str(e)}"
            }
    
    async def complete_flow(self, flow_id: str) -> Dict[str, Any]:
        """Mark flow as completed"""
        try:
            logger.info(f"✅ Completing flow: {flow_id}")
            
            # Get flow
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            if not flow:
                return {
                    "status": "error",
                    "message": f"Flow {flow_id} not found"
                }
            
            # Update flow status
            flow.status = "completed"
            flow.updated_at = datetime.utcnow()
            
            # Mark all phases as complete
            flow.data_import_completed = True
            flow.attribute_mapping_completed = True
            flow.data_cleansing_completed = True
            flow.inventory_completed = True
            flow.dependencies_completed = True
            flow.tech_debt_completed = True
            
            await self.db.commit()
            
            return {
                "flow_id": flow_id,
                "status": "completed",
                "completion_time": datetime.now().isoformat(),
                "final_phase": "tech_debt_analysis"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to complete flow: {e}")
            raise
    
    def _calculate_progress(self, flow) -> float:
        """Calculate flow progress percentage"""
        phases = [
            flow.data_import_completed,
            flow.attribute_mapping_completed,
            flow.data_cleansing_completed,
            flow.inventory_completed,
            flow.dependencies_completed,
            flow.tech_debt_completed
        ]
        
        completed = sum(1 for phase in phases if phase)
        return (completed / len(phases)) * 100.0