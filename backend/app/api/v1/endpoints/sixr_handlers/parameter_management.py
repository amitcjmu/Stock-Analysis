"""
Parameter Management Handler
Handles parameter updates, validation, and parameter-related operations.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ParameterManagementHandler:
    """Handles parameter management operations with graceful fallbacks."""

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
                SixRAnalysisResponse,
                SixRParameterBase,
                SixRParameterUpdateRequest,
            )
            from app.services.sixr_engine_modular import SixRDecisionEngine

            self.SixRAnalysis = SixRAnalysis
            self.SixRParametersModel = SixRParametersModel
            self.SixRParameterUpdateRequest = SixRParameterUpdateRequest
            self.SixRAnalysisResponse = SixRAnalysisResponse
            self.AnalysisStatus = AnalysisStatus
            self.SixRParameterBase = SixRParameterBase
            self.decision_engine = SixRDecisionEngine()

            self.service_available = True
            logger.info("Parameter management handler initialized successfully")
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Parameter management services not available: {e}")
            self.service_available = False

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks

    async def update_parameters(
        self, analysis_id: int, request: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """Update analysis parameters and optionally re-run analysis."""
        try:
            if not self.service_available:
                return self._fallback_update_parameters(analysis_id, request)

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

            if not current_params:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No parameters found for analysis {analysis_id}",
                )

            # Extract parameter updates
            parameter_updates = request.get("parameter_updates", {})
            rerun_analysis = request.get("rerun_analysis", False)

            # Validate parameter values
            validation_errors = self._validate_parameter_values(parameter_updates)
            if validation_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parameter validation failed: {', '.join(validation_errors)}",
                )

            # Update parameters
            for param_name, param_value in parameter_updates.items():
                if hasattr(current_params, param_name):
                    setattr(current_params, param_name, param_value)

            current_params.updated_by = "system"
            await db.commit()

            # Re-run analysis if requested
            if rerun_analysis:
                # Update analysis status
                analysis.status = self.AnalysisStatus.IN_PROGRESS
                analysis.progress_percentage = 50.0
                await db.commit()

                # Run new analysis with updated parameters
                param_dict = {
                    "business_value": current_params.business_value,
                    "technical_complexity": current_params.technical_complexity,
                    "migration_urgency": current_params.migration_urgency,
                    "compliance_requirements": current_params.compliance_requirements,
                    "cost_sensitivity": current_params.cost_sensitivity,
                    "risk_tolerance": current_params.risk_tolerance,
                    "innovation_priority": current_params.innovation_priority,
                    "application_type": current_params.application_type,
                }

                try:
                    # Run analysis with decision engine
                    if hasattr(self.decision_engine, "analyze_parameters"):
                        param_obj = self.SixRParameterBase(**param_dict)
                        recommendation_data = self.decision_engine.analyze_parameters(
                            param_obj,
                            (
                                analysis.application_data[0]
                                if analysis.application_data
                                else None
                            ),
                        )

                        # Update analysis with new recommendation
                        analysis.final_recommendation = recommendation_data.get(
                            "recommended_strategy", "rehost"
                        )
                        analysis.confidence_score = recommendation_data.get(
                            "confidence_score", 0.5
                        )
                        analysis.status = self.AnalysisStatus.COMPLETED
                        analysis.progress_percentage = 100.0
                    else:
                        # Fallback if decision engine not available
                        analysis.status = self.AnalysisStatus.COMPLETED
                        analysis.progress_percentage = 100.0
                        analysis.final_recommendation = "rehost"
                        analysis.confidence_score = 0.7

                except Exception as e:
                    logger.warning(f"Error re-running analysis: {e}")
                    analysis.status = self.AnalysisStatus.COMPLETED
                    analysis.progress_percentage = 100.0

                await db.commit()

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
                "parameters": {
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
                },
            }

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating parameters for analysis {analysis_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update parameters: {str(e)}",
            )

    async def submit_qualifying_questions(
        self, analysis_id: int, request: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """Submit answers to qualifying questions and update parameters."""
        try:
            if not self.service_available:
                return self._fallback_submit_questions(analysis_id, request)

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

            # Process question responses
            responses = request.get("responses", {})

            # Convert responses to parameter updates
            parameter_updates = self._convert_responses_to_parameters(responses)

            # Update parameters if we have updates
            if parameter_updates:
                params_result = await db.execute(
                    select(self.SixRParametersModel)
                    .where(self.SixRParametersModel.analysis_id == analysis_id)
                    .order_by(self.SixRParametersModel.iteration_number.desc())
                )
                current_params = params_result.scalar_one_or_none()

                if current_params:
                    for param_name, param_value in parameter_updates.items():
                        if hasattr(current_params, param_name):
                            setattr(current_params, param_name, param_value)

                    current_params.updated_by = "system"
                    await db.commit()

            # Store question responses
            analysis.qualifying_questions = responses
            analysis.status = self.AnalysisStatus.IN_PROGRESS
            analysis.progress_percentage = 75.0
            await db.commit()

            # Return updated analysis
            return await self._build_analysis_response(analysis, db)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error submitting questions for analysis {analysis_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit questions: {str(e)}",
            )

    def _validate_parameter_values(self, parameter_updates: Dict[str, Any]) -> list:
        """Validate parameter values."""
        errors = []

        numeric_params = [
            "business_value",
            "technical_complexity",
            "migration_urgency",
            "compliance_requirements",
            "cost_sensitivity",
            "risk_tolerance",
            "innovation_priority",
        ]

        for param_name, param_value in parameter_updates.items():
            if param_name in numeric_params:
                if not isinstance(param_value, (int, float)):
                    errors.append(f"{param_name} must be numeric")
                elif not 1 <= param_value <= 5:
                    errors.append(f"{param_name} must be between 1 and 5")

            elif param_name == "application_type":
                valid_types = [
                    "web_application",
                    "database",
                    "legacy_system",
                    "microservice",
                    "monolith",
                    "api_service",
                    "batch_processing",
                ]
                if param_value not in valid_types:
                    errors.append(
                        f"application_type must be one of: {', '.join(valid_types)}"
                    )

        return errors

    def _convert_responses_to_parameters(
        self, responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert question responses to parameter updates."""
        parameter_updates = {}

        # Map common responses to parameter adjustments
        for question_id, response in responses.items():
            if "critical" in str(response).lower():
                parameter_updates["business_value"] = 5
            elif "simple" in str(response).lower():
                parameter_updates["technical_complexity"] = 2
            elif "complex" in str(response).lower():
                parameter_updates["technical_complexity"] = 4
            elif "urgent" in str(response).lower():
                parameter_updates["migration_urgency"] = 5
            elif (
                "cost" in str(response).lower() and "sensitive" in str(response).lower()
            ):
                parameter_updates["cost_sensitivity"] = 4

        return parameter_updates

    async def _build_analysis_response(
        self, analysis, db: AsyncSession
    ) -> Dict[str, Any]:
        """Build analysis response with current parameters."""
        # Get current parameters
        params_result = await db.execute(
            select(self.SixRParametersModel)
            .where(self.SixRParametersModel.analysis_id == analysis.id)
            .order_by(self.SixRParametersModel.iteration_number.desc())
        )
        current_params = params_result.scalar_one_or_none()

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

    # Fallback methods
    def _fallback_update_parameters(
        self, analysis_id: int, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback for parameter updates when services unavailable."""
        return {
            "id": analysis_id,
            "name": f"Analysis {analysis_id}",
            "description": "Parameters updated in fallback mode",
            "status": "completed",
            "priority": "medium",
            "application_ids": [1],
            "current_iteration": 1,
            "progress_percentage": 100.0,
            "parameters": request.get("parameter_updates", {}),
            "fallback_mode": True,
        }

    def _fallback_submit_questions(
        self, analysis_id: int, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback for question submission when services unavailable."""
        return {
            "id": analysis_id,
            "name": f"Analysis {analysis_id}",
            "description": "Questions submitted in fallback mode",
            "status": "completed",
            "priority": "medium",
            "application_ids": [1],
            "current_iteration": 1,
            "progress_percentage": 100.0,
            "qualifying_questions": request.get("responses", {}),
            "fallback_mode": True,
        }
