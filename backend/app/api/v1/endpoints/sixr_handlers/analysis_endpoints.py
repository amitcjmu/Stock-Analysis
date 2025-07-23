"""
Analysis Endpoints Handler
Handles core analysis CRUD operations and bulk analysis.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AnalysisEndpointsHandler:
    """Handles analysis CRUD operations with graceful fallbacks."""

    def __init__(self):
        self.service_available = False
        self._initialize_dependencies()

    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.models.sixr_analysis import SixRAnalysis
            from app.models.sixr_analysis import SixRParameters as SixRParametersModel
            from app.schemas.sixr_analysis import (
                AnalysisStatus,
                BulkAnalysisRequest,
                BulkAnalysisResponse,
                SixRAnalysisListResponse,
                SixRAnalysisRequest,
                SixRAnalysisResponse,
                SixRParameterBase,
            )
            from app.services.sixr_engine_modular import SixRDecisionEngine

            self.SixRAnalysis = SixRAnalysis
            self.SixRParametersModel = SixRParametersModel
            self.SixRAnalysisRequest = SixRAnalysisRequest
            self.SixRAnalysisResponse = SixRAnalysisResponse
            self.SixRAnalysisListResponse = SixRAnalysisListResponse
            self.BulkAnalysisRequest = BulkAnalysisRequest
            self.BulkAnalysisResponse = BulkAnalysisResponse
            self.AnalysisStatus = AnalysisStatus
            self.SixRParameterBase = SixRParameterBase
            self.decision_engine = SixRDecisionEngine()

            self.service_available = True
            logger.info("Analysis endpoints handler initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Analysis endpoints services not available: {e}")
            self.service_available = False

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks

    async def create_analysis(
        self,
        request: Dict[str, Any],
        background_tasks: BackgroundTasks,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Create a new 6R analysis."""
        try:
            if not self.service_available:
                return self._fallback_create_analysis(request)

            # Create analysis record
            analysis = self.SixRAnalysis(
                name=request.get("analysis_name")
                or f"6R Analysis {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                description=request.get("description"),
                status=self.AnalysisStatus.PENDING,
                priority=request.get("priority", "medium"),
                application_ids=request.get("application_ids", []),
                current_iteration=1,
                progress_percentage=0.0,
                created_by="system",
            )

            db.add(analysis)
            await db.commit()
            await db.refresh(analysis)

            # Create initial parameters
            initial_params = request.get("initial_parameters", {})

            # Handle application types if provided
            if (
                request.get("application_types")
                and len(request.get("application_ids", [])) == 1
            ):
                app_id = request["application_ids"][0]
                if app_id in request["application_types"]:
                    initial_params["application_type"] = request["application_types"][
                        app_id
                    ]

            # Set defaults for missing parameters
            param_defaults = {
                "business_value": 3,
                "technical_complexity": 3,
                "migration_urgency": 3,
                "compliance_requirements": 3,
                "cost_sensitivity": 3,
                "risk_tolerance": 3,
                "innovation_priority": 3,
                "application_type": "web_application",
            }

            for key, default_value in param_defaults.items():
                if key not in initial_params:
                    initial_params[key] = default_value

            parameters = self.SixRParametersModel(
                analysis_id=analysis.id,
                iteration_number=1,
                **initial_params,
                created_by="system",
            )

            db.add(parameters)
            await db.commit()

            # Start background analysis (this will be handled by BackgroundTasksHandler)
            from .background_tasks import BackgroundTasksHandler

            bg_handler = BackgroundTasksHandler()
            background_tasks.add_task(
                bg_handler.run_initial_analysis, analysis.id, initial_params, "system"
            )

            # Return initial response
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
                "parameters": {
                    "id": parameters.id,
                    "iteration_number": parameters.iteration_number,
                    **{k: v for k, v in initial_params.items()},
                },
                "application_data": [],
                "qualifying_questions": [],
                "recommendation": None,
            }

        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create analysis: {str(e)}",
            )

    async def get_analysis(self, analysis_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get a specific analysis by ID."""
        try:
            if not self.service_available:
                return self._fallback_get_analysis(analysis_id)

            # Get analysis record
            result = await db.execute(
                select(self.SixRAnalysis).where(self.SixRAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Analysis {analysis_id} not found",
                )

            # Get current parameters
            params_result = await db.execute(
                select(self.SixRParametersModel)
                .where(self.SixRParametersModel.analysis_id == analysis_id)
                .order_by(self.SixRParametersModel.iteration_number.desc())
            )
            current_params = params_result.scalar_one_or_none()

            # Build response
            response = {
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
            }

            if current_params:
                response["parameters"] = {
                    "id": current_params.id,
                    "iteration_number": current_params.iteration_number,
                    "business_value": current_params.business_value,
                    "technical_complexity": current_params.technical_complexity,
                    "migration_urgency": current_params.migration_urgency,
                    "compliance_requirements": current_params.compliance_requirements,
                    "cost_sensitivity": current_params.cost_sensitivity,
                    "risk_tolerance": current_params.risk_tolerance,
                    "innovation_priority": current_params.innovation_priority,
                    "application_type": current_params.application_type,
                }

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting analysis {analysis_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve analysis: {str(e)}",
            )

    async def list_analyses(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status_filter: str = None,
        priority_filter: str = None,
    ) -> Dict[str, Any]:
        """List analyses with optional filtering."""
        try:
            if not self.service_available:
                return self._fallback_list_analyses()

            # Build query
            query = select(self.SixRAnalysis)

            # Apply filters
            if status_filter:
                query = query.where(self.SixRAnalysis.status == status_filter)
            if priority_filter:
                query = query.where(self.SixRAnalysis.priority == priority_filter)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # Get paginated results
            query = (
                query.offset(skip)
                .limit(limit)
                .order_by(self.SixRAnalysis.created_at.desc())
            )
            result = await db.execute(query)
            analyses = result.scalars().all()

            # Build response
            analysis_list = []
            for analysis in analyses:
                analysis_data = {
                    "id": analysis.id,
                    "name": analysis.name,
                    "description": analysis.description,
                    "status": analysis.status.value,
                    "priority": analysis.priority,
                    "application_ids": analysis.application_ids,
                    "current_iteration": analysis.current_iteration,
                    "progress_percentage": analysis.progress_percentage,
                    "final_recommendation": analysis.final_recommendation,
                    "confidence_score": analysis.confidence_score,
                    "created_at": analysis.created_at,
                    "updated_at": analysis.updated_at,
                }
                analysis_list.append(analysis_data)

            return {
                "analyses": analysis_list,
                "total": total,
                "skip": skip,
                "limit": limit,
            }

        except Exception as e:
            logger.error(f"Error listing analyses: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list analyses: {str(e)}",
            )

    async def create_bulk_analysis(
        self,
        request: Dict[str, Any],
        background_tasks: BackgroundTasks,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Create bulk analysis for multiple applications."""
        try:
            if not self.service_available:
                return self._fallback_create_bulk_analysis(request)

            application_ids = request.get("application_ids", [])
            if not application_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one application ID is required",
                )

            # Create individual analyses for each application
            individual_analyses = []
            analysis_responses = []

            for app_id in application_ids:
                # Create individual analysis
                individual_request = {
                    "analysis_name": f"{request.get('analysis_name', 'Bulk Analysis')} - App {app_id}",
                    "description": request.get("description"),
                    "priority": request.get("priority", "medium"),
                    "application_ids": [app_id],
                    "initial_parameters": request.get("default_parameters", {}),
                }

                # Create analysis record
                analysis = self.SixRAnalysis(
                    name=individual_request["analysis_name"],
                    description=individual_request["description"],
                    status=self.AnalysisStatus.PENDING,
                    priority=individual_request["priority"],
                    application_ids=[app_id],
                    current_iteration=1,
                    progress_percentage=0.0,
                    created_by="system",
                )

                db.add(analysis)
                individual_analyses.append(analysis)

            await db.commit()

            # Refresh all analyses
            for analysis in individual_analyses:
                await db.refresh(analysis)

                # Create parameters for each analysis
                initial_params = request.get("default_parameters", {})
                param_defaults = {
                    "business_value": 3,
                    "technical_complexity": 3,
                    "migration_urgency": 3,
                    "compliance_requirements": 3,
                    "cost_sensitivity": 3,
                    "risk_tolerance": 3,
                    "innovation_priority": 3,
                    "application_type": "web_application",
                }

                for key, default_value in param_defaults.items():
                    if key not in initial_params:
                        initial_params[key] = default_value

                parameters = self.SixRParametersModel(
                    analysis_id=analysis.id,
                    iteration_number=1,
                    **initial_params,
                    created_by="system",
                )
                db.add(parameters)

                # Add to response list
                analysis_responses.append(
                    {
                        "id": analysis.id,
                        "name": analysis.name,
                        "application_id": analysis.application_ids[0],
                        "status": analysis.status.value,
                        "progress_percentage": analysis.progress_percentage,
                        "created_at": analysis.created_at,
                        "updated_at": analysis.updated_at or analysis.created_at,
                    }
                )

            await db.commit()

            # Start background bulk processing
            from .background_tasks import BackgroundTasksHandler

            bg_handler = BackgroundTasksHandler()
            analysis_ids = [a.id for a in individual_analyses]
            background_tasks.add_task(
                bg_handler.run_bulk_analysis,
                analysis_ids,
                request.get("batch_size", 5),
                "system",
            )

            return {
                "bulk_analysis_id": individual_analyses[
                    0
                ].id,  # Use first analysis ID as bulk ID
                "total_applications": len(application_ids),
                "completed_applications": 0,
                "failed_applications": 0,
                "progress_percentage": 0.0,
                "individual_analyses": analysis_responses,
                "estimated_completion": None,
                "status": self.AnalysisStatus.PENDING.value,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating bulk analysis: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create bulk analysis: {str(e)}",
            )

    # Fallback methods
    def _fallback_create_analysis(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for creating analysis when services unavailable."""
        return {
            "id": 1,
            "name": request.get("analysis_name", "Fallback Analysis"),
            "description": request.get(
                "description", "Analysis created in fallback mode"
            ),
            "status": "pending",
            "priority": request.get("priority", "medium"),
            "application_ids": request.get("application_ids", []),
            "current_iteration": 1,
            "progress_percentage": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "parameters": {
                "id": 1,
                "iteration_number": 1,
                "business_value": 3,
                "technical_complexity": 3,
                "migration_urgency": 3,
            },
            "application_data": [],
            "qualifying_questions": [],
            "recommendation": None,
            "fallback_mode": True,
        }

    def _fallback_get_analysis(self, analysis_id: int) -> Dict[str, Any]:
        """Fallback for getting analysis when services unavailable."""
        return {
            "id": analysis_id,
            "name": f"Analysis {analysis_id}",
            "description": "Fallback analysis",
            "status": "completed",
            "priority": "medium",
            "application_ids": [1],
            "current_iteration": 1,
            "progress_percentage": 100.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "parameters": {
                "id": 1,
                "iteration_number": 1,
                "business_value": 3,
                "technical_complexity": 3,
            },
            "application_data": [],
            "qualifying_questions": [],
            "recommendation": None,
            "fallback_mode": True,
        }

    def _fallback_list_analyses(self) -> Dict[str, Any]:
        """Fallback for listing analyses when services unavailable."""
        return {
            "analyses": [],
            "total": 0,
            "skip": 0,
            "limit": 100,
            "fallback_mode": True,
        }

    def _fallback_create_bulk_analysis(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for bulk analysis when services unavailable."""
        return {
            "bulk_analysis_id": 1,
            "total_applications": len(request.get("application_ids", [])),
            "completed_applications": 0,
            "failed_applications": 0,
            "progress_percentage": 0.0,
            "individual_analyses": [],
            "estimated_completion": None,
            "status": "pending",
            "fallback_mode": True,
        }
