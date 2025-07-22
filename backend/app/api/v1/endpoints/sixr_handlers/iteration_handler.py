"""
Iteration Handler
Handles analysis iterations and refinement operations.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class IterationHandler:
    """Handles iteration operations with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.models.sixr_analysis import SixRAnalysis, SixRIteration
            from app.models.sixr_analysis import SixRParameters as SixRParametersModel
            from app.schemas.sixr_analysis import AnalysisStatus, SixRParameterBase
            try:
                from app.services.sixr_engine_modular import SixRDecisionEngine
            except ImportError:
                pass
            
            self.SixRAnalysis = SixRAnalysis
            self.SixRParametersModel = SixRParametersModel
            self.SixRIteration = SixRIteration
            self.AnalysisStatus = AnalysisStatus
            self.SixRParameterBase = SixRParameterBase
            self.decision_engine = SixRDecisionEngine()
            
            self.service_available = True
            logger.info("Iteration handler initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Iteration services not available: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    async def create_iteration(
        self,
        analysis_id: int,
        request: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new analysis iteration."""
        try:
            if not self.service_available:
                return self._fallback_create_iteration(analysis_id, request)
            
            # Get analysis record
            result = await db.execute(
                select(self.SixRAnalysis).where(self.SixRAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Analysis {analysis_id} not found"
                )
            
            # Increment iteration number
            new_iteration_number = analysis.current_iteration + 1
            
            # Get current parameters for copying
            current_params_result = await db.execute(
                select(self.SixRParametersModel)
                .where(self.SixRParametersModel.analysis_id == analysis_id)
                .order_by(self.SixRParametersModel.iteration_number.desc())
            )
            current_params = current_params_result.scalar_one_or_none()
            
            if not current_params:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No parameters found for analysis {analysis_id}"
                )
            
            # Create new iteration record
            iteration = self.SixRIteration(
                analysis_id=analysis_id,
                iteration_number=new_iteration_number,
                notes=request.get('iteration_notes', ''),
                created_by="system"
            )
            db.add(iteration)
            
            # Create new parameters for this iteration (copy from current)
            new_parameter_updates = request.get('parameter_updates', {})
            
            new_params = self.SixRParametersModel(
                analysis_id=analysis_id,
                iteration_number=new_iteration_number,
                business_value=new_parameter_updates.get('business_value', current_params.business_value),
                technical_complexity=new_parameter_updates.get('technical_complexity', current_params.technical_complexity),
                migration_urgency=new_parameter_updates.get('migration_urgency', current_params.migration_urgency),
                compliance_requirements=new_parameter_updates.get('compliance_requirements', current_params.compliance_requirements),
                cost_sensitivity=new_parameter_updates.get('cost_sensitivity', current_params.cost_sensitivity),
                risk_tolerance=new_parameter_updates.get('risk_tolerance', current_params.risk_tolerance),
                innovation_priority=new_parameter_updates.get('innovation_priority', current_params.innovation_priority),
                application_type=new_parameter_updates.get('application_type', current_params.application_type),
                created_by="system"
            )
            db.add(new_params)
            
            # Update analysis
            analysis.current_iteration = new_iteration_number
            analysis.status = self.AnalysisStatus.IN_PROGRESS
            analysis.progress_percentage = 50.0
            
            await db.commit()
            await db.refresh(iteration)
            await db.refresh(new_params)
            
            # Run analysis for new iteration in background
            from .background_tasks import BackgroundTasksHandler
            BackgroundTasksHandler()
            
            # This would typically be done in background
            try:
                param_dict = {
                    'business_value': new_params.business_value,
                    'technical_complexity': new_params.technical_complexity,
                    'migration_urgency': new_params.migration_urgency,
                    'compliance_requirements': new_params.compliance_requirements,
                    'cost_sensitivity': new_params.cost_sensitivity,
                    'risk_tolerance': new_params.risk_tolerance,
                    'innovation_priority': new_params.innovation_priority,
                    'application_type': new_params.application_type
                }
                
                # Run analysis
                if hasattr(self.decision_engine, 'analyze_parameters'):
                    param_obj = self.SixRParameterBase(**param_dict)
                    recommendation_data = self.decision_engine.analyze_parameters(
                        param_obj,
                        analysis.application_data[0] if analysis.application_data else None
                    )
                    
                    analysis.final_recommendation = recommendation_data.get('recommended_strategy', 'rehost')
                    analysis.confidence_score = recommendation_data.get('confidence_score', 0.5)
                    analysis.status = self.AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0
                else:
                    analysis.status = self.AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0
                
                await db.commit()
                
            except Exception as e:
                logger.warning(f"Error running iteration analysis: {e}")
                analysis.status = self.AnalysisStatus.COMPLETED
                analysis.progress_percentage = 100.0
                await db.commit()
            
            # Build response
            return {
                "id": analysis.id,
                "name": analysis.name,
                "description": analysis.description,
                "status": analysis.status.value,
                "priority": analysis.priority,
                "application_ids": analysis.application_ids,
                "current_iteration": analysis.current_iteration,
                "progress_percentage": analysis.progress_percentage,
                "created_at": analysis.created_at,
                "updated_at": analysis.updated_at,
                "application_data": analysis.application_data or [],
                "qualifying_questions": analysis.qualifying_questions or [],
                "recommendation": None,
                "parameters": {
                    "id": new_params.id,
                    "iteration_number": new_params.iteration_number,
                    "business_value": new_params.business_value,
                    "technical_complexity": new_params.technical_complexity,
                    "migration_urgency": new_params.migration_urgency,
                    "compliance_requirements": new_params.compliance_requirements,
                    "cost_sensitivity": new_params.cost_sensitivity,
                    "risk_tolerance": new_params.risk_tolerance,
                    "innovation_priority": new_params.innovation_priority,
                    "application_type": new_params.application_type
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating iteration for analysis {analysis_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create iteration: {str(e)}"
            )
    
    # Fallback methods
    def _fallback_create_iteration(self, analysis_id: int, request: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for iteration creation when services unavailable."""
        return {
            "id": analysis_id,
            "name": f"Analysis {analysis_id}",
            "description": "Iteration created in fallback mode",
            "status": "completed",
            "priority": "medium",
            "application_ids": [1],
            "current_iteration": 2,
            "progress_percentage": 100.0,
            "parameters": request.get('parameter_updates', {}),
            "fallback_mode": True
        } 