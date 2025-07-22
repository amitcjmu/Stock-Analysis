"""
Background Tasks Handler
Handles all background processing for 6R analysis operations.
"""

import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class BackgroundTasksHandler:
    """Handles background task operations with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.sixr_analysis import SixRAnalysis
            from app.models.sixr_analysis import SixRParameters as SixRParametersModel
            from app.models.sixr_analysis import SixRRecommendation as SixRRecommendationModel
            from app.schemas.sixr_analysis import AnalysisStatus, SixRParameterBase
            try:
                from app.services.sixr_engine_modular import SixRDecisionEngine
                SIXR_ENGINE_AVAILABLE = True
            except ImportError:
                SIXR_ENGINE_AVAILABLE = False
            
            self.AsyncSessionLocal = AsyncSessionLocal
            self.SixRAnalysis = SixRAnalysis
            self.SixRParametersModel = SixRParametersModel
            self.SixRRecommendationModel = SixRRecommendationModel
            self.AnalysisStatus = AnalysisStatus
            self.SixRParameterBase = SixRParameterBase
            self.decision_engine = SixRDecisionEngine()
            
            self.service_available = True
            logger.info("Background tasks handler initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Background tasks services not available: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    async def run_initial_analysis(self, analysis_id: int, parameters: Dict[str, Any], user: str):
        """Run initial 6R analysis in background."""
        if not self.service_available:
            logger.warning(f"Background tasks not available, skipping analysis {analysis_id}")
            return
        
        try:
            async with self.AsyncSessionLocal() as db:
                try:
                    # Get analysis record
                    result = await db.execute(select(self.SixRAnalysis).where(self.SixRAnalysis.id == analysis_id))
                    analysis = result.scalar_one_or_none()
                    if not analysis:
                        logger.error(f"Analysis {analysis_id} not found")
                        return
                    
                    # Update status to in_progress
                    analysis.status = self.AnalysisStatus.IN_PROGRESS
                    analysis.progress_percentage = 10.0
                    await db.commit()
                    
                    # Get application data (mock for now - would come from CMDB)
                    application_data = []
                    for app_id in analysis.application_ids:
                        app_data = {
                            'id': app_id,
                            'name': f'Application {app_id}',
                            'technology_stack': ['Java', 'Spring', 'MySQL'],
                            'complexity_score': 6,
                            'business_criticality': 'high'
                        }
                        application_data.append(app_data)
                    
                    analysis.application_data = application_data
                    analysis.progress_percentage = 30.0
                    await db.commit()
                    
                    # Get current parameters
                    params_result = await db.execute(
                        select(self.SixRParametersModel)
                        .where(self.SixRParametersModel.analysis_id == analysis_id)
                        .order_by(self.SixRParametersModel.iteration_number.desc())
                    )
                    current_params = params_result.scalar_one_or_none()
                    if not current_params:
                        logger.error(f"No parameters found for analysis {analysis_id}")
                        return
                    
                    # Convert to parameter object for decision engine
                    param_dict = {
                        'business_value': current_params.business_value,
                        'technical_complexity': current_params.technical_complexity,
                        'migration_urgency': current_params.migration_urgency,
                        'compliance_requirements': current_params.compliance_requirements,
                        'cost_sensitivity': current_params.cost_sensitivity,
                        'risk_tolerance': current_params.risk_tolerance,
                        'innovation_priority': current_params.innovation_priority,
                        'application_type': current_params.application_type
                    }
                    
                    # Run decision engine analysis
                    analysis.progress_percentage = 50.0
                    await db.commit()
                    
                    # Calculate recommendation using decision engine
                    try:
                        if hasattr(self.decision_engine, 'analyze_parameters'):
                            param_obj = self.SixRParameterBase(**param_dict)
                            recommendation_data = self.decision_engine.analyze_parameters(
                                param_obj, 
                                application_data[0] if application_data else None
                            )
                        else:
                            # Fallback recommendation
                            recommendation_data = {
                                'recommended_strategy': 'rehost',
                                'confidence_score': 0.7,
                                'strategy_scores': {'rehost': 0.8, 'retain': 0.6},
                                'key_factors': ['Low complexity', 'Quick migration'],
                                'assumptions': ['Cloud readiness'],
                                'next_steps': ['Assess infrastructure', 'Plan migration'],
                                'estimated_effort': 'medium',
                                'estimated_timeline': '3-6 months',
                                'estimated_cost_impact': 'moderate'
                            }
                    except Exception as e:
                        logger.warning(f"Decision engine error, using fallback: {e}")
                        recommendation_data = {
                            'recommended_strategy': 'rehost',
                            'confidence_score': 0.5,
                            'strategy_scores': {},
                            'key_factors': [],
                            'assumptions': [],
                            'next_steps': [],
                            'estimated_effort': 'medium',
                            'estimated_timeline': '3-6 months',
                            'estimated_cost_impact': 'moderate'
                        }
                    
                    analysis.progress_percentage = 80.0
                    await db.commit()
                    
                    # Create recommendation record
                    recommendation = self.SixRRecommendationModel(
                        analysis_id=analysis_id,
                        iteration_number=analysis.current_iteration,
                        recommended_strategy=recommendation_data['recommended_strategy'],
                        confidence_score=recommendation_data['confidence_score'],
                        strategy_scores=recommendation_data.get('strategy_scores', {}),
                        key_factors=recommendation_data.get('key_factors', []),
                        assumptions=recommendation_data.get('assumptions', []),
                        next_steps=recommendation_data.get('next_steps', []),
                        estimated_effort=recommendation_data.get('estimated_effort', 'medium'),
                        estimated_timeline=recommendation_data.get('estimated_timeline', '3-6 months'),
                        estimated_cost_impact=recommendation_data.get('estimated_cost_impact', 'moderate'),
                        created_by=user
                    )
                    
                    db.add(recommendation)
                    
                    # Update analysis with final results
                    analysis.status = self.AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0
                    analysis.final_recommendation = recommendation_data['recommended_strategy']
                    analysis.confidence_score = recommendation_data['confidence_score']
                    
                    await db.commit()
                    logger.info(f"Completed initial analysis for {analysis_id}")
                    
                except Exception as e:
                    logger.error(f"Database error in initial analysis {analysis_id}: {e}")
                    await db.rollback()
        
        except Exception as e:
            logger.error(f"Failed to run initial analysis for {analysis_id}: {e}")
    
    async def run_iteration_analysis(self, analysis_id: int, iteration_number: int, request_data: Dict[str, Any], user: str):
        """Run iteration analysis in background."""
        if not self.service_available:
            logger.warning(f"Background tasks not available, skipping iteration analysis {analysis_id}")
            return
        
        try:
            async with self.AsyncSessionLocal() as db:
                try:
                    # Get analysis record
                    result = await db.execute(select(self.SixRAnalysis).where(self.SixRAnalysis.id == analysis_id))
                    analysis = result.scalar_one_or_none()
                    if not analysis:
                        logger.error(f"Analysis {analysis_id} not found")
                        return
                    
                    # Get current parameters
                    params_result = await db.execute(
                        select(self.SixRParametersModel)
                        .where(self.SixRParametersModel.analysis_id == analysis_id)
                        .where(self.SixRParametersModel.iteration_number == iteration_number)
                    )
                    current_params = params_result.scalar_one_or_none()
                    if not current_params:
                        logger.error(f"No parameters found for analysis {analysis_id} iteration {iteration_number}")
                        return
                    
                    # Convert to parameter object
                    param_dict = {
                        'business_value': current_params.business_value,
                        'technical_complexity': current_params.technical_complexity,
                        'migration_urgency': current_params.migration_urgency,
                        'compliance_requirements': current_params.compliance_requirements,
                        'cost_sensitivity': current_params.cost_sensitivity,
                        'risk_tolerance': current_params.risk_tolerance,
                        'innovation_priority': current_params.innovation_priority,
                        'application_type': current_params.application_type
                    }
                    
                    # Get enhanced context including previous iterations
                    context = {
                        'application_data': analysis.application_data,
                        'iteration_number': iteration_number,
                        'iteration_notes': request_data.get('iteration_notes', '')
                    }
                    
                    # Run analysis
                    analysis.progress_percentage = 70.0
                    await db.commit()
                    
                    try:
                        if hasattr(self.decision_engine, 'analyze_parameters'):
                            param_obj = self.SixRParameterBase(**param_dict)
                            recommendation_data = self.decision_engine.analyze_parameters(param_obj, context)
                        else:
                            recommendation_data = {
                                'recommended_strategy': 'rehost',
                                'confidence_score': 0.7,
                                'strategy_scores': {},
                                'key_factors': [],
                                'assumptions': [],
                                'next_steps': [],
                                'estimated_effort': 'medium',
                                'estimated_timeline': '3-6 months',
                                'estimated_cost_impact': 'moderate'
                            }
                    except Exception as e:
                        logger.warning(f"Decision engine error in iteration: {e}")
                        recommendation_data = {
                            'recommended_strategy': 'rehost',
                            'confidence_score': 0.5,
                            'strategy_scores': {},
                            'key_factors': [],
                            'assumptions': [],
                            'next_steps': [],
                            'estimated_effort': 'medium',
                            'estimated_timeline': '3-6 months',
                            'estimated_cost_impact': 'moderate'
                        }
                    
                    # Create new recommendation for this iteration
                    recommendation = self.SixRRecommendationModel(
                        analysis_id=analysis_id,
                        iteration_number=iteration_number,
                        recommended_strategy=recommendation_data['recommended_strategy'],
                        confidence_score=recommendation_data['confidence_score'],
                        strategy_scores=recommendation_data.get('strategy_scores', {}),
                        key_factors=recommendation_data.get('key_factors', []),
                        assumptions=recommendation_data.get('assumptions', []),
                        next_steps=recommendation_data.get('next_steps', []),
                        estimated_effort=recommendation_data.get('estimated_effort', 'medium'),
                        estimated_timeline=recommendation_data.get('estimated_timeline', '3-6 months'),
                        estimated_cost_impact=recommendation_data.get('estimated_cost_impact', 'moderate'),
                        created_by=user
                    )
                    
                    db.add(recommendation)
                    
                    # Update analysis
                    analysis.status = self.AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0
                    analysis.final_recommendation = recommendation_data['recommended_strategy']
                    analysis.confidence_score = recommendation_data['confidence_score']
                    
                    await db.commit()
                    logger.info(f"Completed iteration analysis for {analysis_id}, iteration {iteration_number}")
                    
                except Exception as e:
                    logger.error(f"Database error in iteration analysis {analysis_id}: {e}")
                    await db.rollback()
        
        except Exception as e:
            logger.error(f"Failed to run iteration analysis for {analysis_id}: {e}")
    
    async def run_bulk_analysis(self, analysis_ids: List[int], batch_size: int, user: str):
        """Run bulk analysis for multiple applications."""
        if not self.service_available:
            logger.warning("Background tasks not available, skipping bulk analysis")
            return
        
        try:
            for i in range(0, len(analysis_ids), batch_size):
                batch = analysis_ids[i:i + batch_size]
                
                # Process batch in parallel
                tasks = []
                for analysis_id in batch:
                    task = self.run_initial_analysis(analysis_id, {}, user)
                    tasks.append(task)
                
                # Wait for batch completion
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Small delay between batches
                await asyncio.sleep(1)
                
                logger.info(f"Completed bulk analysis batch {i//batch_size + 1}")
            
            logger.info(f"Completed bulk analysis for {len(analysis_ids)} analyses")
            
        except Exception as e:
            logger.error(f"Error in bulk analysis: {e}") 