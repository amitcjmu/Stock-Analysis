"""
Manual Collection Phase Manager

Handles the orchestration of manual data collection in the collection flow.
This manager coordinates questionnaire generation and response collection.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.collection_flow import AutomationTier, CollectionPhase, CollectionStatus
from app.services.ai_analysis import AdaptiveQuestionnaireGenerator
from app.services.collection_flow import QualityAssessmentService
from app.services.crewai_flows.handlers.enhanced_error_handler import enhanced_error_handler
from app.services.crewai_flows.handlers.unified_flow_management import UnifiedFlowManagement
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff
from app.services.manual_collection import (
    AdaptiveFormService,
    DataIntegrationService,
    ProgressTrackingService,
    QuestionnaireValidationService,
)

logger = logging.getLogger(__name__)


class ManualCollectionManager:
    """
    Manages the manual collection phase of the collection flow.
    
    This manager handles:
    - Questionnaire generation based on gaps
    - Adaptive form creation
    - Manual collection crew execution
    - Response validation and integration
    - Progress tracking
    - Pause/resume for user input
    """
    
    def __init__(self, flow_context, state_manager, audit_service):
        """
        Initialize the manual collection manager.
        
        Args:
            flow_context: Flow context containing flow ID, client, and engagement info
            state_manager: State manager for persisting flow state
            audit_service: Audit logging service
        """
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.audit_service = audit_service
        
        # Initialize services
        self.questionnaire_generator = AdaptiveQuestionnaireGenerator()
        self.adaptive_form_service = AdaptiveFormService(
            flow_context.db_session, flow_context
        )
        self.validation_service = QuestionnaireValidationService()
        self.progress_tracking = ProgressTrackingService(
            flow_context.db_session, flow_context
        )
        self.data_integration = DataIntegrationService(
            flow_context.db_session, flow_context
        )
        self.quality_assessment = QualityAssessmentService()
    
    async def execute(self, flow_state, crewai_service, client_requirements,
                     skip_generation: bool = False) -> Dict[str, Any]:
        """
        Execute the manual collection phase.
        
        Args:
            flow_state: Current collection flow state
            crewai_service: CrewAI service for creating crews
            client_requirements: Client-specific requirements
            skip_generation: Skip questionnaire generation if already done
            
        Returns:
            Dict containing phase execution results
        """
        try:
            logger.info(f"👤 Starting manual collection for flow {self.flow_context.flow_id}")
            
            # Check if we need questionnaire generation
            if not skip_generation and flow_state.current_phase != CollectionPhase.MANUAL_COLLECTION:
                return await self._generate_questionnaires(flow_state, client_requirements)
            
            # Execute manual collection
            return await self._execute_manual_collection(flow_state, crewai_service, client_requirements)
            
        except Exception as e:
            logger.error(f"❌ Manual collection failed: {e}")
            flow_state.add_error("manual_collection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise
    
    async def _generate_questionnaires(self, flow_state, client_requirements) -> Dict[str, Any]:
        """Generate adaptive questionnaires based on gaps"""
        logger.info("📝 Generating adaptive questionnaires")
        
        # Update state
        flow_state.status = CollectionStatus.GENERATING_QUESTIONNAIRES
        flow_state.current_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
        flow_state.updated_at = datetime.utcnow()
        
        # Get gap analysis results
        identified_gaps = flow_state.gap_analysis_results.get("identified_gaps", [])
        
        # Generate questionnaires using AI
        questionnaires = await self.questionnaire_generator.generate_questionnaires(
            data_gaps=identified_gaps,
            business_context=client_requirements.get("business_context", {}),
            automation_tier=flow_state.automation_tier.value
        )
        
        # Create adaptive forms
        form_configs = []
        for questionnaire in questionnaires:
            form_config = await self.adaptive_form_service.create_adaptive_form(
                questionnaire_data=questionnaire,
                gap_context=identified_gaps,
                template_preferences=client_requirements.get("form_preferences", {})
            )
            form_configs.append(form_config)
        
        # Update state
        flow_state.questionnaires = questionnaires
        flow_state.phase_results["questionnaire_generation"] = {
            "questionnaires": questionnaires,
            "form_configs": form_configs,
            "generation_timestamp": datetime.utcnow().isoformat()
        }
        
        # Update progress
        flow_state.progress = 70.0
        flow_state.next_phase = CollectionPhase.MANUAL_COLLECTION
        
        # Persist state
        await self.state_manager.save_state(flow_state.to_dict())
        
        # Log event
        await self.audit_service.log_flow_event(
            flow_id=self.flow_context.flow_id,
            event_type="questionnaires_generated",
            event_data={
                "questionnaire_count": len(questionnaires),
                "form_count": len(form_configs),
                "gap_count": len(identified_gaps)
            }
        )
        
        # Pause for user input
        flow_state.pause_points.append("manual_collection_required")
        unified_flow_management = UnifiedFlowManagement(flow_state)
        await unified_flow_management.pause_flow(
            reason="Questionnaires generated - manual collection required",
            phase="questionnaire_generation"
        )
        
        return {
            "phase": "questionnaire_generation",
            "status": "completed",
            "questionnaires_generated": len(questionnaires),
            "next_phase": "manual_collection",
            "requires_user_input": True,
            "pause_reason": "awaiting_manual_responses"
        }
    
    async def _execute_manual_collection(self, flow_state, crewai_service, 
                                       client_requirements) -> Dict[str, Any]:
        """Execute manual data collection with user responses"""
        logger.info("📋 Executing manual data collection")
        
        # Update state
        flow_state.status = CollectionStatus.MANUAL_COLLECTION
        flow_state.current_phase = CollectionPhase.MANUAL_COLLECTION
        flow_state.updated_at = datetime.utcnow()
        
        # Get questionnaires and user inputs
        questionnaires = flow_state.questionnaires
        user_responses = flow_state.user_inputs.get("manual_responses", {})
        identified_gaps = flow_state.gap_analysis_results.get("identified_gaps", [])
        
        # Create manual collection crew
        crew_results = await self._execute_collection_crew(
            crewai_service, questionnaires, identified_gaps,
            flow_state.collected_data, user_responses
        )
        
        # Process and validate responses
        validated_responses = await self._process_responses(
            crew_results, user_responses, identified_gaps,
            client_requirements
        )
        
        # Update progress tracking
        await self._update_progress_tracking(
            flow_state, validated_responses
        )
        
        # Update flow state
        await self._update_flow_state(
            flow_state, validated_responses, crew_results
        )
        
        # Log phase completion
        await self.audit_service.log_flow_event(
            flow_id=self.flow_context.flow_id,
            event_type="manual_collection_completed",
            event_data={
                "responses_collected": len(validated_responses["responses"]),
                "validation_pass_rate": validated_responses["validation_results"]["pass_rate"],
                "remaining_gaps": len(validated_responses["remaining_gaps"])
            }
        )
        
        return {
            "phase": "manual_collection",
            "status": "completed",
            "responses_collected": len(validated_responses["responses"]),
            "validation_pass_rate": validated_responses["validation_results"]["pass_rate"],
            "next_phase": "data_validation",
            "collection_complete": True
        }
    
    async def resume(self, flow_state, user_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Resume manual collection with user responses.
        
        Args:
            flow_state: Current collection flow state
            user_inputs: User responses to questionnaires
            
        Returns:
            Dict containing resume results
        """
        logger.info(f"🔄 Resuming manual collection for flow {self.flow_context.flow_id}")
        
        if not user_inputs or "manual_responses" not in user_inputs:
            return {
                "phase": "manual_collection",
                "status": "waiting_for_input",
                "message": "Manual responses required to continue",
                "requires_user_input": True
            }
        
        # Store user responses
        flow_state.user_inputs["manual_responses"] = user_inputs["manual_responses"]
        flow_state.last_user_interaction = datetime.utcnow()
        
        # Execute manual collection with responses
        from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow
        collection_flow = UnifiedCollectionFlow(
            crewai_service=None,  # Will be provided by execute method
            context=self.flow_context,
            flow_id=flow_state.flow_id
        )
        
        # Continue with manual collection execution
        return await self._execute_manual_collection(
            flow_state, 
            collection_flow.crewai_service,
            user_inputs.get("client_requirements", {})
        )
    
    async def _execute_collection_crew(self, crewai_service, questionnaires,
                                     data_gaps, existing_data, user_responses) -> Dict[str, Any]:
        """Create and execute the manual collection crew"""
        logger.info("🤖 Creating manual collection crew")
        
        # Import crew creation function
        from app.services.crewai_flows.crews.collection.manual_collection_crew import create_manual_collection_crew
        
        # Create crew with context
        crew = create_manual_collection_crew(
            crewai_service=crewai_service,
            questionnaires=questionnaires,
            data_gaps=data_gaps,
            context={
                "existing_data": existing_data,
                "user_inputs": user_responses,
                "flow_id": self.flow_context.flow_id
            }
        )
        
        # Execute with retry
        logger.info("🚀 Executing manual collection crew")
        crew_result = await retry_with_backoff(
            crew.kickoff,
            inputs={
                "questionnaires": questionnaires,
                "user_responses": user_responses
            }
        )
        
        return crew_result
    
    async def _process_responses(self, crew_results: Dict[str, Any],
                               user_responses: Dict[str, Any],
                               identified_gaps: List[Dict],
                               client_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate manual collection responses"""
        logger.info("🔧 Processing manual collection responses")
        
        # Extract responses from crew results
        responses = crew_results.get("responses", [])
        validation_results = crew_results.get("validation", {})
        
        # Validate responses
        validated_responses = await self.validation_service.validate_questionnaire_responses(
            responses=responses,
            validation_rules=client_requirements.get("validation_rules", {}),
            gap_context=identified_gaps
        )
        
        # Identify remaining gaps
        remaining_gaps = self._identify_remaining_gaps(
            validated_responses, identified_gaps
        )
        
        # Calculate completion metrics
        completion_metrics = self._calculate_completion_metrics(
            validated_responses, identified_gaps
        )
        
        return {
            "responses": validated_responses,
            "validation_results": {
                "pass_rate": validation_results.get("pass_rate", 0.0),
                "validation_details": validation_results,
                "failed_validations": validation_results.get("failed", [])
            },
            "remaining_gaps": remaining_gaps,
            "completion_metrics": completion_metrics,
            "crew_output": crew_results
        }
    
    async def _update_progress_tracking(self, flow_state, validated_responses: Dict[str, Any]):
        """Update progress tracking for manual collection"""
        logger.info("📊 Updating progress tracking")
        
        # Track questionnaire completion
        questionnaire_progress = {
            "total_questionnaires": len(flow_state.questionnaires),
            "completed_questionnaires": len(validated_responses["responses"]),
            "completion_percentage": (len(validated_responses["responses"]) / 
                                    len(flow_state.questionnaires) * 100 
                                    if flow_state.questionnaires else 100)
        }
        
        # Track gap resolution
        gap_progress = {
            "initial_gaps": len(flow_state.gap_analysis_results.get("identified_gaps", [])),
            "remaining_gaps": len(validated_responses["remaining_gaps"]),
            "gaps_resolved": len(flow_state.gap_analysis_results.get("identified_gaps", [])) - 
                           len(validated_responses["remaining_gaps"])
        }
        
        # Update progress service
        await self.progress_tracking.update_collection_progress(
            flow_id=self.flow_context.flow_id,
            phase="manual_collection",
            progress_data={
                "questionnaire_progress": questionnaire_progress,
                "gap_progress": gap_progress,
                "validation_pass_rate": validated_responses["validation_results"]["pass_rate"]
            }
        )
    
    async def _update_flow_state(self, flow_state, validated_responses: Dict[str, Any],
                               crew_results: Dict[str, Any]):
        """Update flow state with manual collection results"""
        logger.info("💾 Updating flow state with manual collection results")
        
        # Store manual responses
        flow_state.manual_responses = validated_responses["responses"]
        
        # Store phase results
        flow_state.phase_results["manual_collection"] = {
            "responses": validated_responses["responses"],
            "validation_results": validated_responses["validation_results"],
            "remaining_gaps": validated_responses["remaining_gaps"],
            "completion_metrics": validated_responses["completion_metrics"],
            "collection_timestamp": datetime.utcnow().isoformat()
        }
        
        # Update progress
        flow_state.progress = 85.0
        flow_state.next_phase = CollectionPhase.DATA_VALIDATION
        
        # Persist state
        await self.state_manager.save_state(flow_state.to_dict())
    
    def _identify_remaining_gaps(self, validated_responses: List[Dict],
                               initial_gaps: List[Dict]) -> List[Dict]:
        """Identify gaps that remain after manual collection"""
        remaining_gaps = []
        
        # Create a map of responses by gap ID
        response_map = {}
        for response in validated_responses:
            gap_id = response.get("gap_id")
            if gap_id:
                response_map[gap_id] = response
        
        # Check each initial gap
        for gap in initial_gaps:
            gap_id = gap.get("id")
            if gap_id not in response_map:
                # Gap not addressed
                remaining_gaps.append(gap)
            else:
                response = response_map[gap_id]
                # Check if response adequately addresses the gap
                if not self._is_gap_resolved(gap, response):
                    gap["partial_resolution"] = True
                    gap["response_quality"] = response.get("quality_score", 0.0)
                    remaining_gaps.append(gap)
        
        return remaining_gaps
    
    def _is_gap_resolved(self, gap: Dict, response: Dict) -> bool:
        """Check if a response adequately resolves a gap"""
        # Check response completeness
        if response.get("completeness", 0.0) < 0.8:
            return False
        
        # Check response quality
        if response.get("quality_score", 0.0) < 0.7:
            return False
        
        # Check if all required fields are present
        required_fields = gap.get("required_fields", [])
        response_fields = response.get("fields", {})
        
        for field in required_fields:
            if field not in response_fields or not response_fields[field]:
                return False
        
        return True
    
    def _calculate_completion_metrics(self, validated_responses: List[Dict],
                                    initial_gaps: List[Dict]) -> Dict[str, float]:
        """Calculate completion metrics for manual collection"""
        if not initial_gaps:
            return {
                "overall_completion": 100.0,
                "quality_score": 100.0,
                "coverage_score": 100.0
            }
        
        # Calculate completion rate
        responses_count = len(validated_responses)
        gaps_count = len(initial_gaps)
        completion_rate = (responses_count / gaps_count * 100) if gaps_count > 0 else 0
        
        # Calculate average quality score
        quality_scores = [r.get("quality_score", 0.0) for r in validated_responses]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Calculate coverage score (how well responses cover gap requirements)
        coverage_scores = []
        for response in validated_responses:
            required = response.get("required_fields_count", 1)
            provided = response.get("provided_fields_count", 0)
            coverage = (provided / required) if required > 0 else 0
            coverage_scores.append(coverage)
        
        avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
        
        return {
            "overall_completion": completion_rate,
            "quality_score": avg_quality * 100,
            "coverage_score": avg_coverage * 100
        }