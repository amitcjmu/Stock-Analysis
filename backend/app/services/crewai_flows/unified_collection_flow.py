"""
Unified Collection Flow - CrewAI Implementation

This module implements the main CollectionFlow using CrewAI Flow patterns,
following the same architecture as UnifiedDiscoveryFlow with PostgreSQL-only persistence.

The Collection Flow handles adaptive data collection for migration readiness and:
1. Detects platforms in the environment
2. Performs automated data collection using platform adapters
3. Analyzes gaps in collected data
4. Generates adaptive questionnaires for manual collection
5. Synthesizes and validates all collected data

Flow Phases:
- INITIALIZATION: Setup flow state and load configuration
- PLATFORM_DETECTION: Detect and identify platforms in the environment
- AUTOMATED_COLLECTION: Automated data collection via adapters
- GAP_ANALYSIS: Analyze data completeness and quality gaps
- QUESTIONNAIRE_GENERATION: Generate adaptive questionnaires for gaps
- MANUAL_COLLECTION: Collect data through manual processes
- DATA_VALIDATION: Validate all collected data
- FINALIZATION: Prepare data for Discovery Flow handoff

Each phase includes pause points for user input and collaboration.
"""

import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# CrewAI Flow imports - REQUIRED for real agent execution
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from crewai.flow.flow import listen, start, or_
    CREWAI_FLOW_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI Flow imports successful for CollectionFlow - REAL AGENTS ENABLED")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ CrewAI Flow not available for CollectionFlow: {e}")
    logger.error("❌ CRITICAL: Cannot proceed without real CrewAI agents")
    raise ImportError(f"CrewAI is required for real agent execution in CollectionFlow: {e}")

# Import models and dependencies
from app.models.collection_flow import (
    CollectionFlowState, CollectionPhase, CollectionStatus, AutomationTier,
    PlatformType, DataDomain, CollectionFlowError, AdaptiveQuestionnaire
)
from app.core.context import RequestContext
from app.services.crewai_flows.flow_state_manager import FlowStateManager
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore

# Import collection services
from app.services.collection_flow import (
    CollectionFlowStateService,
    TierDetectionService,
    DataTransformationService,
    QualityAssessmentService,
    AuditLoggingService
)
from app.services.ai_analysis import (
    AIValidationService,
    BusinessContextAnalyzer,
    ConfidenceScorer,
    GapAnalysisAgent,
    AdaptiveQuestionnaireGenerator
)
from app.services.manual_collection import (
    AdaptiveFormService,
    BulkDataService,
    QuestionnaireValidationService as ValidationService,
    TemplateService,
    ProgressTrackingService,
    DataIntegrationService
)

# Import handlers and utilities
from app.services.crewai_flows.handlers.unified_flow_management import UnifiedFlowManagement
from app.services.crewai_flows.handlers.enhanced_error_handler import enhanced_error_handler
from app.services.crewai_flows.persistence.checkpoint_manager import checkpoint_manager
from app.services.crewai_flows.monitoring.flow_health_monitor import flow_health_monitor
from app.services.crewai_flows.utils.retry_utils import retry_decorator, RetryConfig, retry_with_backoff


class FlowContext:
    """Flow context container for Collection Flow execution."""
    
    def __init__(self, flow_id: str, client_account_id: str, engagement_id: str, 
                 user_id: Optional[str] = None, db_session=None):
        self.flow_id = flow_id
        self.client_account_id = client_account_id  
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.db_session = db_session


class UnifiedCollectionFlow(Flow[CollectionFlowState]):
    """
    Unified Collection Flow with PostgreSQL-only persistence.
    
    This CrewAI Flow orchestrates the adaptive data collection process,
    integrating automated and manual collection methods with intelligent gap analysis.
    
    Follows the same patterns as UnifiedDiscoveryFlow:
    - PostgreSQL-only state management
    - Multi-tenant context preservation  
    - Pause/resume functionality at each phase
    - True CrewAI agents for intelligence
    - Error handling and recovery
    """
    
    def __init__(self, crewai_service, context: RequestContext, automation_tier: str = "tier_2", **kwargs):
        """Initialize unified collection flow"""
        logger.info("🚀 Initializing Unified Collection Flow with CrewAI Agents")
        
        # Store core attributes BEFORE calling super().__init__() 
        # because CrewAI Flow.__init__ may access properties
        self.crewai_service = crewai_service
        self.context = context
        self.automation_tier = AutomationTier(automation_tier)
        self._flow_id = kwargs.get('flow_id') or str(uuid.uuid4())
        self._master_flow_id = kwargs.get('master_flow_id')
        self._discovery_flow_id = kwargs.get('discovery_flow_id')
        
        # Initialize base CrewAI Flow after setting attributes
        super().__init__()
        
        # Initialize flow context
        self.flow_context = FlowContext(
            flow_id=self._flow_id,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            user_id=str(context.user_id) if context.user_id else None,
            db_session=kwargs.get('db_session')
        )
        
        # Initialize flow state - CrewAI Flow manages state internally
        # We'll use _flow_state for our internal state management
        self._flow_state = CollectionFlowState(
            flow_id=self._flow_id,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            user_id=str(context.user_id) if context.user_id else None,
            discovery_flow_id=self._discovery_flow_id,
            automation_tier=self.automation_tier,
            current_phase=CollectionPhase.INITIALIZATION,
            status=CollectionStatus.INITIALIZING
        )
        
        # Initialize services
        self._initialize_services()
        
        # Initialize state manager
        self.state_manager = FlowStateManager(
            flow_type="collection",
            flow_id=self._flow_id,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            db_session=self.flow_context.db_session
        )
        
        # Initialize unified flow management  
        self.unified_flow_management = UnifiedFlowManagement(self._flow_state)
        
        # Store configuration
        self.config = kwargs.get('config', {})
        self.environment_config = self.config.get('environment_config', {})
        self.client_requirements = self.config.get('client_requirements', {})
        
        logger.info(f"✅ Collection Flow initialized - Flow ID: {self._flow_id}")
    
    @property
    def flow_id(self):
        """Get the flow ID"""
        return self._flow_id
    
    @property
    def state(self):
        """Get the flow state - always return our managed state"""
        # Always return the internal flow state if available
        if hasattr(self, '_flow_state') and self._flow_state:
            return self._flow_state
        
        # If we don't have _flow_state yet, create a default with proper IDs
        # This should only happen during initialization
        flow_id = getattr(self, '_flow_id', str(uuid.uuid4()))
        client_account_id = ""
        engagement_id = ""
        user_id = ""
        
        if hasattr(self, 'context') and self.context:
            client_account_id = str(self.context.client_account_id) if self.context.client_account_id else ""
            engagement_id = str(self.context.engagement_id) if self.context.engagement_id else ""
            user_id = str(self.context.user_id) if self.context.user_id else ""
        
        default_state = CollectionFlowState(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            automation_tier=getattr(self, 'automation_tier', AutomationTier.TIER_2),
            current_phase=CollectionPhase.INITIALIZATION,
            status=CollectionStatus.INITIALIZING
        )
        
        # Store it as _flow_state for consistency
        self._flow_state = default_state
        return self._flow_state
    
    def _initialize_services(self):
        """Initialize all required services"""
        db_session = self.flow_context.db_session
        
        # Initialize Phase 1 & 2 services
        self.state_service = CollectionFlowStateService(db_session, self.context)
        self.tier_detection = TierDetectionService(db_session, self.context)
        self.data_transformation = DataTransformationService(db_session, self.context)
        self.quality_assessment = QualityAssessmentService()
        self.audit_logging = AuditLoggingService(db_session, self.context)
        
        # Initialize AI analysis services
        self.ai_validation = AIValidationService()
        self.business_analyzer = BusinessContextAnalyzer()
        self.confidence_scoring = ConfidenceScorer()
        self.gap_analysis_agent = GapAnalysisAgent()
        self.questionnaire_generator = AdaptiveQuestionnaireGenerator()
        
        # Initialize manual collection services
        self.adaptive_form_service = AdaptiveFormService(db_session, self.context)
        self.bulk_data_service = BulkDataService(db_session, self.context)
        self.validation_service = ValidationService()
        self.template_service = TemplateService(db_session, self.context)
        self.progress_tracking = ProgressTrackingService(db_session, self.context)
        self.data_integration = DataIntegrationService(db_session, self.context)
    
    @start()
    async def initialize_collection(self):
        """Initialize the collection flow"""
        try:
            logger.info("🔄 Starting Collection Flow initialization")
            
            # Update state
            self.state.status = CollectionStatus.INITIALIZING
            self.state.current_phase = CollectionPhase.INITIALIZATION
            self.state.updated_at = datetime.utcnow()
            
            # Initialize flow in database
            await self.state_service.initialize_collection_flow(
                flow_id=self._flow_id,
                automation_tier=self.automation_tier.value,
                configuration={
                    "client_requirements": self.client_requirements,
                    "environment_config": self.environment_config,
                    "master_flow_id": self._master_flow_id,
                    "discovery_flow_id": self._discovery_flow_id
                }
            )
            
            # Persist initial state
            await self.state_manager.save_state(self.state.to_dict())
            
            # Log initialization
            await self.audit_logging.log_flow_event(
                flow_id=self._flow_id,
                event_type="flow_initialized",
                event_data={
                    "automation_tier": self.automation_tier.value,
                    "environment_config": self.environment_config
                }
            )
            
            # Update phase
            self.state.current_phase = CollectionPhase.PLATFORM_DETECTION
            self.state.next_phase = CollectionPhase.AUTOMATED_COLLECTION
            self.state.progress = 5.0
            
            # Update database status to prevent blocking
            if self.flow_context.db_session:
                try:
                    from sqlalchemy import update
                    from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
                    
                    stmt = update(CollectionFlow).where(
                        CollectionFlow.id == uuid.UUID(self._flow_id)
                    ).values(
                        status=CollectionFlowStatus.PLATFORM_DETECTION.value,
                        current_phase=CollectionPhase.PLATFORM_DETECTION.value,
                        progress_percentage=5.0,
                        updated_at=datetime.utcnow()
                    )
                    await self.flow_context.db_session.execute(stmt)
                    await self.flow_context.db_session.commit()
                    logger.info(f"✅ Updated flow {self._flow_id} status from INITIALIZED to PLATFORM_DETECTION")
                except Exception as e:
                    logger.error(f"Failed to update flow status in database: {e}")
                    # Continue even if database update fails
            
            return {
                "phase": "initialization",
                "status": "completed",
                "next_phase": "platform_detection",
                "flow_id": self._flow_id
            }
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            self.state.add_error("initialization", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Initialization failed: {e}")
    
    @listen("initialization")
    async def detect_platforms(self, initialization_result):
        """Phase 1: Detect platforms in the environment"""
        try:
            logger.info("🔍 Starting platform detection phase")
            
            # Update state
            self.state.status = CollectionStatus.DETECTING_PLATFORMS
            self.state.current_phase = CollectionPhase.PLATFORM_DETECTION
            self.state.updated_at = datetime.utcnow()
            
            # Perform tier analysis
            tier_analysis = await self.tier_detection.analyze_environment_tier(
                environment_config=self.environment_config,
                automation_tier=self.automation_tier.value
            )
            
            # Create platform detection crew
            from app.services.crewai_flows.crews.collection.platform_detection_crew import create_platform_detection_crew
            
            crew = create_platform_detection_crew(
                crewai_service=self.crewai_service,
                environment_config=self.environment_config,
                tier_assessment=tier_analysis,
                context={
                    "client_requirements": self.client_requirements,
                    "automation_tier": self.automation_tier.value
                }
            )
            
            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "environment_config": self.environment_config,
                    "tier_analysis": tier_analysis
                }
            )
            
            # Process results
            detected_platforms = crew_result.get("platforms", [])
            adapter_recommendations = crew_result.get("recommended_adapters", [])
            
            # Store in state
            self.state.detected_platforms = detected_platforms
            self.state.collection_config["adapter_recommendations"] = adapter_recommendations
            self.state.phase_results["platform_detection"] = {
                "platforms": detected_platforms,
                "tier_analysis": tier_analysis,
                "adapter_recommendations": adapter_recommendations
            }
            
            # Calculate quality score
            quality_score = await self.quality_assessment.assess_platform_detection_quality(
                detected_platforms=detected_platforms,
                tier_analysis=tier_analysis
            )
            
            # Update progress
            self.state.progress = 15.0
            self.state.next_phase = CollectionPhase.AUTOMATED_COLLECTION
            
            # Persist state
            await self.state_manager.save_state(self.state.to_dict())
            
            # Check if pause required
            if self._requires_user_approval("platform_detection"):
                self.state.pause_points.append("platform_detection_approval")
                await self.unified_flow_management.pause_flow(
                    reason="Platform detection completed - user approval required",
                    phase="platform_detection"
                )
            
            return {
                "phase": "platform_detection",
                "status": "completed",
                "platforms_detected": len(detected_platforms),
                "quality_score": quality_score,
                "next_phase": "automated_collection"
            }
            
        except Exception as e:
            logger.error(f"❌ Platform detection failed: {e}")
            self.state.add_error("platform_detection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Platform detection failed: {e}")
    
    @listen("platform_detection")
    async def automated_collection(self, platform_result):
        """Phase 2: Automated data collection"""
        try:
            logger.info("🤖 Starting automated collection phase")
            
            # Update state
            self.state.status = CollectionStatus.COLLECTING_DATA
            self.state.current_phase = CollectionPhase.AUTOMATED_COLLECTION
            self.state.updated_at = datetime.utcnow()
            
            # Get detected platforms
            detected_platforms = self.state.detected_platforms
            adapter_recommendations = self.state.collection_config.get("adapter_recommendations", [])
            
            # Create automated collection crew
            from app.services.crewai_flows.crews.collection.automated_collection_crew import create_automated_collection_crew
            
            crew = create_automated_collection_crew(
                crewai_service=self.crewai_service,
                platforms=detected_platforms,
                tier_assessments=self.state.phase_results.get("platform_detection", {}).get("tier_analysis", {}),
                context={
                    "available_adapters": self._get_available_adapters(),
                    "collection_timeout_minutes": 60,
                    "quality_thresholds": {"minimum": 0.8}
                }
            )
            
            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "platforms": detected_platforms,
                    "adapter_configs": adapter_recommendations
                }
            )
            
            # Process collected data
            collected_data = crew_result.get("collected_data", [])
            collection_metrics = crew_result.get("collection_metrics", {})
            
            # Transform data
            transformed_data = await self.data_transformation.transform_collected_data(
                raw_data=collected_data,
                platforms=detected_platforms,
                normalization_rules=self.client_requirements.get("normalization_rules", {})
            )
            
            # Store in state
            self.state.collected_data = transformed_data
            self.state.collection_results = {
                "raw_data": collected_data,
                "transformed_data": transformed_data,
                "metrics": collection_metrics
            }
            self.state.phase_results["automated_collection"] = crew_result
            
            # Calculate quality score
            quality_scores = await self.quality_assessment.assess_collection_quality(
                collected_data=transformed_data,
                expected_platforms=detected_platforms,
                automation_tier=self.automation_tier.value
            )
            self.state.collection_quality_score = quality_scores.get("overall_quality", 0.0)
            
            # Update progress
            self.state.progress = 40.0
            self.state.next_phase = CollectionPhase.GAP_ANALYSIS
            
            # Persist state
            await self.state_manager.save_state(self.state.to_dict())
            
            return {
                "phase": "automated_collection",
                "status": "completed",
                "data_collected": len(transformed_data),
                "quality_score": self.state.collection_quality_score,
                "next_phase": "gap_analysis"
            }
            
        except Exception as e:
            logger.error(f"❌ Automated collection failed: {e}")
            self.state.add_error("automated_collection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Automated collection failed: {e}")
    
    @listen("automated_collection")
    async def analyze_gaps(self, collection_result):
        """Phase 3: Gap analysis"""
        try:
            logger.info("🔎 Starting gap analysis phase")
            
            # Update state
            self.state.status = CollectionStatus.ANALYZING_GAPS
            self.state.current_phase = CollectionPhase.GAP_ANALYSIS
            self.state.updated_at = datetime.utcnow()
            
            # Get collected data
            collected_data = self.state.collected_data
            collection_gaps = self.state.phase_results.get("automated_collection", {}).get("identified_gaps", [])
            
            # Perform AI gap analysis
            gap_analysis_result = await self.gap_analysis_agent.analyze_data_gaps(
                collected_data=collected_data,
                existing_gaps=collection_gaps,
                sixr_requirements=self.client_requirements.get("sixr_requirements", {}),
                automation_tier=self.automation_tier.value
            )
            
            # Create gap analysis crew
            from app.services.crewai_flows.crews.collection.gap_analysis_crew import create_gap_analysis_crew
            
            crew = create_gap_analysis_crew(
                crewai_service=self.crewai_service,
                collected_data=collected_data,
                sixr_requirements=self.client_requirements.get("sixr_requirements", {}),
                context={
                    "automation_tier": self.automation_tier.value,
                    "existing_gaps": collection_gaps
                }
            )
            
            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "collected_data": collected_data,
                    "ai_analysis": gap_analysis_result
                }
            )
            
            # Process results
            identified_gaps = crew_result.get("data_gaps", [])
            gap_categories = crew_result.get("gap_categories", {})
            sixr_impact = crew_result.get("sixr_impact_analysis", {})
            
            # Store in state
            self.state.gap_analysis_results = {
                "identified_gaps": identified_gaps,
                "gap_categories": gap_categories,
                "sixr_impact": sixr_impact,
                "recommendations": crew_result.get("recommendations", [])
            }
            self.state.phase_results["gap_analysis"] = crew_result
            
            # Update progress
            self.state.progress = 55.0
            
            # Determine next phase based on gaps
            if not identified_gaps or self.automation_tier == AutomationTier.TIER_1:
                self.state.next_phase = CollectionPhase.DATA_VALIDATION
            else:
                self.state.next_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
            
            # Persist state
            await self.state_manager.save_state(self.state.to_dict())
            
            return {
                "phase": "gap_analysis",
                "status": "completed",
                "gaps_identified": len(identified_gaps),
                "sixr_impact_score": sixr_impact.get("overall_impact_score", 0.0),
                "next_phase": self.state.next_phase.value
            }
            
        except Exception as e:
            logger.error(f"❌ Gap analysis failed: {e}")
            self.state.add_error("gap_analysis", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Gap analysis failed: {e}")
    
    @listen("gap_analysis")
    async def generate_questionnaires(self, gap_result):
        """Phase 4: Generate adaptive questionnaires"""
        # Skip if no gaps or tier 1
        if gap_result["gaps_identified"] == 0 or self.automation_tier == AutomationTier.TIER_1:
            return await self.validate_data(gap_result)
        
        try:
            logger.info("📝 Starting questionnaire generation phase")
            
            # Update state
            self.state.status = CollectionStatus.GENERATING_QUESTIONNAIRES
            self.state.current_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
            self.state.updated_at = datetime.utcnow()
            
            # Get gap analysis results
            identified_gaps = self.state.gap_analysis_results.get("identified_gaps", [])
            
            # Generate questionnaires
            questionnaires = await self.questionnaire_generator.generate_questionnaires(
                data_gaps=identified_gaps,
                business_context=self.client_requirements.get("business_context", {}),
                automation_tier=self.automation_tier.value
            )
            
            # Create adaptive forms
            form_configs = []
            for questionnaire in questionnaires:
                form_config = await self.adaptive_form_service.create_adaptive_form(
                    questionnaire_data=questionnaire,
                    gap_context=identified_gaps,
                    template_preferences=self.client_requirements.get("form_preferences", {})
                )
                form_configs.append(form_config)
            
            # Save questionnaires to database
            saved_questionnaires = await self._save_questionnaires_to_db(questionnaires)
            
            # Store in state
            self.state.questionnaires = saved_questionnaires
            self.state.phase_results["questionnaire_generation"] = {
                "questionnaires": saved_questionnaires,
                "form_configs": form_configs
            }
            
            # Update progress
            self.state.progress = 70.0
            self.state.next_phase = CollectionPhase.MANUAL_COLLECTION
            
            # Persist state
            await self.state_manager.save_state(self.state.to_dict())
            
            # Pause for user input
            self.state.pause_points.append("manual_collection_required")
            await self.unified_flow_management.pause_flow(
                reason="Questionnaires generated - manual collection required",
                phase="questionnaire_generation"
            )
            
            return {
                "phase": "questionnaire_generation",
                "status": "completed",
                "questionnaires_generated": len(questionnaires),
                "next_phase": "manual_collection",
                "requires_user_input": True
            }
            
        except Exception as e:
            logger.error(f"❌ Questionnaire generation failed: {e}")
            self.state.add_error("questionnaire_generation", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Questionnaire generation failed: {e}")
    
    @listen("questionnaire_generation")
    async def manual_collection(self, questionnaire_result):
        """Phase 5: Manual data collection"""
        try:
            logger.info("👤 Starting manual collection phase")
            
            # Update state
            self.state.status = CollectionStatus.MANUAL_COLLECTION
            self.state.current_phase = CollectionPhase.MANUAL_COLLECTION
            self.state.updated_at = datetime.utcnow()
            
            # Get questionnaires and gaps
            questionnaires = self.state.questionnaires
            identified_gaps = self.state.gap_analysis_results.get("identified_gaps", [])
            
            # Create manual collection crew
            from app.services.crewai_flows.crews.collection.manual_collection_crew import create_manual_collection_crew
            
            crew = create_manual_collection_crew(
                crewai_service=self.crewai_service,
                questionnaires=questionnaires,
                data_gaps=identified_gaps,
                context={
                    "existing_data": self.state.collected_data,
                    "user_inputs": self.state.user_inputs
                }
            )
            
            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "questionnaires": questionnaires,
                    "user_responses": self.state.user_inputs.get("manual_responses", {})
                }
            )
            
            # Process responses
            responses = crew_result.get("responses", [])
            validation_results = crew_result.get("validation", {})
            
            # Validate responses
            validated_responses = await self.validation_service.validate_questionnaire_responses(
                responses=responses,
                validation_rules=self.client_requirements.get("validation_rules", {}),
                gap_context=identified_gaps
            )
            
            # Store in state
            self.state.manual_responses = validated_responses
            self.state.phase_results["manual_collection"] = {
                "responses": validated_responses,
                "validation_results": validation_results,
                "remaining_gaps": crew_result.get("unresolved_gaps", [])
            }
            
            # Update progress
            self.state.progress = 85.0
            self.state.next_phase = CollectionPhase.DATA_VALIDATION
            
            # Persist state
            await self.state_manager.save_state(self.state.to_dict())
            
            return {
                "phase": "manual_collection",
                "status": "completed",
                "responses_collected": len(validated_responses),
                "validation_pass_rate": validation_results.get("pass_rate", 0.0),
                "next_phase": "data_validation"
            }
            
        except Exception as e:
            logger.error(f"❌ Manual collection failed: {e}")
            self.state.add_error("manual_collection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Manual collection failed: {e}")
    
    @listen(or_("manual_collection", "gap_analysis"))
    async def validate_data(self, previous_result):
        """Phase 6: Data validation and synthesis"""
        try:
            logger.info("✅ Starting data validation phase")
            
            # Update state
            self.state.status = CollectionStatus.VALIDATING_DATA
            self.state.current_phase = CollectionPhase.DATA_VALIDATION
            self.state.updated_at = datetime.utcnow()
            
            # Gather all data
            automated_data = self.state.collected_data
            manual_data = self.state.manual_responses
            
            # Integrate data
            integrated_data = await self.data_integration.integrate_collection_data(
                automated_data=automated_data,
                manual_data=manual_data,
                integration_rules=self.client_requirements.get("integration_rules", {}),
                conflict_resolution=self.client_requirements.get("conflict_resolution", "priority_based")
            )
            
            # Create data synthesis crew
            from app.services.crewai_flows.crews.collection.data_synthesis_crew import create_data_synthesis_crew
            
            crew = create_data_synthesis_crew(
                crewai_service=self.crewai_service,
                automated_data=automated_data,
                manual_data=manual_data,
                context={
                    "validation_rules": self.client_requirements.get("validation_rules", {}),
                    "automation_tier": self.automation_tier.value
                }
            )
            
            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "integrated_data": integrated_data
                }
            )
            
            # Generate quality report
            quality_report = await self.quality_assessment.generate_final_quality_report(
                synthesized_data=integrated_data,
                phase_results=self.state.phase_results,
                automation_tier=self.automation_tier.value
            )
            
            # Calculate SIXR readiness
            sixr_readiness_score = await self.business_analyzer.calculate_sixr_readiness(
                synthesized_data=integrated_data,
                quality_report=quality_report,
                sixr_requirements=self.client_requirements.get("sixr_requirements", {})
            )
            
            # Store validation results
            self.state.validation_results = {
                "synthesized_data": integrated_data,
                "quality_report": quality_report,
                "sixr_readiness": sixr_readiness_score,
                "validation_summary": crew_result
            }
            
            # Update final scores
            self.state.collection_quality_score = quality_report.get("overall_quality_score", 0.0)
            self.state.confidence_score = await self.confidence_scoring.calculate_final_confidence(
                synthesized_data=integrated_data,
                quality_report=quality_report,
                phase_results=self.state.phase_results
            )
            
            # Update progress
            self.state.progress = 95.0
            self.state.next_phase = CollectionPhase.FINALIZATION
            
            # Persist state
            await self.state_manager.save_state(self.state.to_dict())
            
            return {
                "phase": "data_validation",
                "status": "completed",
                "data_quality_score": self.state.collection_quality_score,
                "sixr_readiness_score": sixr_readiness_score,
                "next_phase": "finalization"
            }
            
        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            self.state.add_error("data_validation", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Data validation failed: {e}")
    
    @listen("data_validation")
    async def finalize_collection(self, validation_result):
        """Phase 7: Finalize collection and prepare for handoff"""
        try:
            logger.info("🏁 Starting collection finalization")
            
            # Update state
            self.state.status = CollectionStatus.COMPLETED
            self.state.current_phase = CollectionPhase.FINALIZATION
            self.state.completed_at = datetime.utcnow()
            self.state.updated_at = datetime.utcnow()
            
            # Prepare assessment package
            assessment_package = {
                "flow_id": self._flow_id,
                "client_account_id": self.state.client_account_id,
                "engagement_id": self.state.engagement_id,
                "collection_summary": {
                    "automation_tier": self.automation_tier.value,
                    "collection_quality_score": self.state.collection_quality_score,
                    "confidence_score": self.state.confidence_score,
                    "platforms_collected": len(self.state.detected_platforms),
                    "gap_analysis_complete": bool(self.state.gap_analysis_results)
                },
                "collected_data": self.state.validation_results.get("synthesized_data", {}),
                "gap_analysis": self.state.gap_analysis_results,
                "sixr_readiness": self.state.validation_results.get("sixr_readiness", 0.0),
                "completed_at": self.state.completed_at.isoformat()
            }
            
            # Determine assessment readiness
            self.state.assessment_ready = validation_result["sixr_readiness_score"] >= 0.75
            
            # Update final state
            self.state.progress = 100.0
            self.state.next_phase = None
            
            # Complete flow in database
            await self.state_service.complete_collection_flow(
                flow_id=self._flow_id,
                final_results=assessment_package,
                execution_time_ms=int((self.state.completed_at - self.state.created_at).total_seconds() * 1000)
            )
            
            # Persist final state
            await self.state_manager.save_state(self.state.to_dict())
            
            # Log completion
            await self.audit_logging.log_flow_event(
                flow_id=self._flow_id,
                event_type="flow_completed",
                event_data={
                    "quality_score": self.state.collection_quality_score,
                    "confidence_score": self.state.confidence_score,
                    "assessment_ready": self.state.assessment_ready
                }
            )
            
            # Notify master flow if linked
            if self._master_flow_id:
                await self.unified_flow_management.notify_phase_completion(
                    phase="collection",
                    results=assessment_package
                )
            
            return {
                "phase": "finalization",
                "status": "completed",
                "flow_completed": True,
                "assessment_ready": self.state.assessment_ready,
                "assessment_package": assessment_package
            }
            
        except Exception as e:
            logger.error(f"❌ Finalization failed: {e}")
            self.state.add_error("finalization", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Finalization failed: {e}")
    
    def _requires_user_approval(self, phase: str) -> bool:
        """Check if phase requires user approval"""
        approval_phases = self.client_requirements.get("approval_required_phases", [])
        return phase in approval_phases
    
    def _get_available_adapters(self) -> Dict[str, Any]:
        """Get available platform adapters"""
        # This would interface with the adapter registry
        from app.services.collection_flow.adapters import adapter_registry
        return {
            adapter_type: adapter_registry.get_adapter(adapter_type)
            for adapter_type in adapter_registry.list_adapters()
        }
    
    async def resume_flow(self, user_inputs: Optional[Dict[str, Any]] = None):
        """Resume flow after pause"""
        if user_inputs:
            self.state.user_inputs.update(user_inputs)
            self.state.last_user_interaction = datetime.utcnow()
        
        # Resume based on current phase
        phase_handlers = {
            CollectionPhase.INITIALIZATION: self.initialize_collection,
            CollectionPhase.PLATFORM_DETECTION: self.detect_platforms,
            CollectionPhase.AUTOMATED_COLLECTION: self.automated_collection,
            CollectionPhase.GAP_ANALYSIS: self.analyze_gaps,
            CollectionPhase.QUESTIONNAIRE_GENERATION: self.generate_questionnaires,
            CollectionPhase.MANUAL_COLLECTION: self.manual_collection,
            CollectionPhase.DATA_VALIDATION: self.validate_data,
            CollectionPhase.FINALIZATION: self.finalize_collection
        }
        
        handler = phase_handlers.get(self.state.current_phase)
        if handler:
            # Get previous phase result
            previous_phase = self._get_previous_phase(self.state.current_phase)
            previous_result = self.state.phase_results.get(previous_phase.value, {})
            return await handler(previous_result)
        
        raise CollectionFlowError(f"No handler for phase: {self.state.current_phase}")
    
    def _get_previous_phase(self, current_phase: CollectionPhase) -> Optional[CollectionPhase]:
        """Get the previous phase in sequence"""
        phase_order = [
            CollectionPhase.INITIALIZATION,
            CollectionPhase.PLATFORM_DETECTION,
            CollectionPhase.AUTOMATED_COLLECTION,
            CollectionPhase.GAP_ANALYSIS,
            CollectionPhase.QUESTIONNAIRE_GENERATION,
            CollectionPhase.MANUAL_COLLECTION,
            CollectionPhase.DATA_VALIDATION,
            CollectionPhase.FINALIZATION
        ]
        
        try:
            current_index = phase_order.index(current_phase)
            if current_index > 0:
                return phase_order[current_index - 1]
        except ValueError:
            pass
        
        return None
    
    async def _save_questionnaires_to_db(self, questionnaires: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Save generated questionnaires to database"""
        try:
            if not self.flow_context.db_session:
                logger.warning("No database session available for saving questionnaires")
                return questionnaires
            
            saved_questionnaires = []
            
            for questionnaire_data in questionnaires:
                # Extract questionnaire metadata from the generated data
                metadata = questionnaire_data.get("questionnaire", {}).get("metadata", {})
                sections = questionnaire_data.get("questionnaire", {}).get("sections", [])
                
                # Create questionnaire instance
                questionnaire = AdaptiveQuestionnaire(
                    client_account_id=uuid.UUID(self.flow_context.client_account_id),
                    engagement_id=uuid.UUID(self.flow_context.engagement_id),
                    collection_flow_id=uuid.UUID(self.flow_id),
                    title=metadata.get("title", "Adaptive Data Collection Questionnaire"),
                    description=metadata.get("description", "AI-generated questionnaire for gap resolution"),
                    template_name=metadata.get("id", f"questionnaire-{self.flow_id}"),
                    template_type="adaptive_collection",
                    version=metadata.get("version", "1.0"),
                    applicable_tiers=[self.automation_tier.value],
                    question_set=questionnaire_data.get("questionnaire", {}),
                    questions=self._extract_questions_from_sections(sections),
                    question_count=metadata.get("total_questions", 0),
                    estimated_completion_time=metadata.get("estimated_duration_minutes", 20),
                    target_gaps=questionnaire_data.get("questionnaire", {}).get("target_gaps", []),
                    gap_categories=self._extract_gap_categories(sections),
                    platform_types=self.state.detected_platforms,
                    data_domains=["collection", "migration_readiness"],
                    scoring_rules=questionnaire_data.get("questionnaire", {}).get("completion_criteria", {}),
                    validation_rules=questionnaire_data.get("questionnaire", {}).get("adaptive_logic", {}),
                    completion_status="pending",
                    is_template=False  # This is an instance, not a template
                )
                
                # Save to database
                self.flow_context.db_session.add(questionnaire)
                
                # Add ID to questionnaire data for reference
                questionnaire_data["db_id"] = str(questionnaire.id)
                saved_questionnaires.append(questionnaire_data)
            
            # Commit all questionnaires
            await self.flow_context.db_session.commit()
            
            logger.info(f"✅ Saved {len(saved_questionnaires)} questionnaires to database for flow {self.flow_id}")
            
            return saved_questionnaires
            
        except Exception as e:
            logger.error(f"Failed to save questionnaires to database: {e}")
            if self.flow_context.db_session:
                await self.flow_context.db_session.rollback()
            # Return original questionnaires even if save fails
            return questionnaires
    
    def _extract_questions_from_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all questions from questionnaire sections"""
        questions = []
        for section in sections:
            questions.extend(section.get("questions", []))
        return questions
    
    def _extract_gap_categories(self, sections: List[Dict[str, Any]]) -> List[str]:
        """Extract gap categories from questionnaire sections"""
        categories = set()
        for section in sections:
            for question in section.get("questions", []):
                gap_resolution = question.get("gap_resolution", {})
                if gap_resolution.get("addresses_gap"):
                    categories.add(gap_resolution["addresses_gap"])
        return list(categories)


def create_unified_collection_flow(
    crewai_service,
    context: RequestContext,
    automation_tier: str = "tier_2",
    **kwargs
) -> UnifiedCollectionFlow:
    """Factory function to create a unified collection flow"""
    return UnifiedCollectionFlow(
        crewai_service=crewai_service,
        context=context,
        automation_tier=automation_tier,
        **kwargs
    )