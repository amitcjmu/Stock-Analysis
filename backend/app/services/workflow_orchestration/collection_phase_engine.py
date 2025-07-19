"""
Collection Flow Phase Execution Engine
Team C1 - Task C1.1

This engine orchestrates the execution of Collection Flow phases, integrating all Phase 1 and Phase 2
components to execute the complete Collection Flow lifecycle.

Phases:
1. Platform Detection - Detect and identify target platforms
2. Automated Collection - Automated data collection using adapters
3. Gap Analysis - Analyze missing data and quality issues  
4. Manual Collection - Collect data through questionnaires and manual processes
5. Synthesis - Synthesize and validate all collected data
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.core.exceptions import FlowError, InvalidFlowStateError

# Import Phase 1 & 2 components
from app.services.collection_flow import (
    CollectionFlowStateService,
    TierDetectionService,
    DataTransformationService,
    QualityAssessmentService,
    AuditLoggingService,
    adapter_registry
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

# Import flow orchestration components
from app.services.flow_orchestration import FlowExecutionEngine
try:
    from app.services.crewai_flows.crews.collection import (
        PlatformDetectionCrew,
        AutomatedCollectionCrew,
        GapAnalysisCrew,
        ManualCollectionCrew,
        DataSynthesisCrew
    )
    CREWAI_CREWS_AVAILABLE = True
except ImportError:
    CREWAI_CREWS_AVAILABLE = False
    # Create dummy classes for type hints
    PlatformDetectionCrew = AutomatedCollectionCrew = GapAnalysisCrew = None
    ManualCollectionCrew = DataSynthesisCrew = None

logger = get_logger(__name__)


class CollectionPhaseStatus(Enum):
    """Status of collection phases"""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    SKIPPED = "skipped"


class AutomationTier(Enum):
    """Automation tier levels"""
    TIER_1 = "tier_1"  # Full automation
    TIER_2 = "tier_2"  # High automation with minimal manual
    TIER_3 = "tier_3"  # Moderate automation with manual collection
    TIER_4 = "tier_4"  # Manual-heavy with some automation


@dataclass
class PhaseResult:
    """Result of a phase execution"""
    phase_name: str
    status: CollectionPhaseStatus
    start_time: datetime
    end_time: Optional[datetime]
    execution_time_ms: Optional[int]
    output_data: Dict[str, Any]
    quality_score: Optional[float]
    confidence_score: Optional[float]
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionContext:
    """Context for phase execution"""
    flow_id: str
    automation_tier: AutomationTier
    client_requirements: Dict[str, Any]
    environment_config: Dict[str, Any]
    quality_thresholds: Dict[str, float]
    timeout_config: Dict[str, int]


class CollectionPhaseExecutionEngine:
    """
    Collection Flow Phase Execution Engine
    
    Orchestrates the complete Collection Flow lifecycle by executing phases in sequence,
    managing state transitions, and coordinating between all integrated components.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the Collection Phase Execution Engine"""
        self.db = db
        self.context = context
        
        # Initialize Phase 1 & 2 services
        self.state_service = CollectionFlowStateService(db, context)
        self.tier_detection = TierDetectionService()
        self.data_transformation = DataTransformationService()
        self.quality_assessment = QualityAssessmentService()
        self.audit_logging = AuditLoggingService(db, context)
        
        # Initialize AI analysis services
        self.ai_validation = AIValidationService()
        self.business_analyzer = BusinessContextAnalyzer()
        self.confidence_scoring = ConfidenceScorer()
        self.gap_analysis_agent = GapAnalysisAgent()
        self.questionnaire_generator = AdaptiveQuestionnaireGenerator()
        
        # Initialize manual collection services
        self.adaptive_form_service = AdaptiveFormService(db, context)
        self.bulk_data_service = BulkDataService(db, context)
        self.validation_service = ValidationService()
        self.template_service = TemplateService(db, context)
        self.progress_tracking = ProgressTrackingService(db, context)
        self.data_integration = DataIntegrationService(db, context)
        
        # Initialize flow execution engine for CrewAI integration
        self.flow_engine = FlowExecutionEngine(
            db=db,
            context=context,
            master_repo=None,  # Will be set when needed
            flow_registry=None,  # Will be set when needed
            handler_registry=None,  # Will be set when needed
            validator_registry=None  # Will be set when needed
        )
        
        # Phase execution tracking
        self.phase_results: Dict[str, PhaseResult] = {}
        self.execution_context: Optional[ExecutionContext] = None
        
        logger.info("✅ Collection Phase Execution Engine initialized")
    
    async def execute_collection_flow(
        self,
        flow_id: str,
        automation_tier: str = "tier_2",
        client_requirements: Optional[Dict[str, Any]] = None,
        environment_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete Collection Flow with all phases
        
        Args:
            flow_id: Unique identifier for the collection flow
            automation_tier: Level of automation (tier_1 to tier_4)
            client_requirements: Client-specific requirements and preferences
            environment_config: Environment configuration for discovery
            
        Returns:
            Complete execution results with all phase outputs
        """
        execution_start = datetime.utcnow()
        
        try:
            # Initialize execution context
            self.execution_context = ExecutionContext(
                flow_id=flow_id,
                automation_tier=AutomationTier(automation_tier),
                client_requirements=client_requirements or {},
                environment_config=environment_config or {},
                quality_thresholds=self._get_quality_thresholds(automation_tier),
                timeout_config=self._get_timeout_config(automation_tier)
            )
            
            # Initialize flow state
            await self.state_service.initialize_collection_flow(
                flow_id=flow_id,
                automation_tier=automation_tier,
                configuration={
                    "client_requirements": client_requirements,
                    "environment_config": environment_config,
                    "quality_thresholds": self.execution_context.quality_thresholds
                }
            )
            
            logger.info(f"🚀 Starting Collection Flow execution: {flow_id} ({automation_tier})")
            
            # Execute phases in sequence
            phase_sequence = [
                ("platform_detection", self._execute_platform_detection_phase),
                ("automated_collection", self._execute_automated_collection_phase),
                ("gap_analysis", self._execute_gap_analysis_phase),
                ("manual_collection", self._execute_manual_collection_phase),
                ("synthesis", self._execute_synthesis_phase)
            ]
            
            for phase_name, phase_executor in phase_sequence:
                try:
                    # Check if phase should be skipped based on automation tier
                    if self._should_skip_phase(phase_name, automation_tier):
                        logger.info(f"⏭️ Skipping phase {phase_name} for {automation_tier}")
                        self.phase_results[phase_name] = PhaseResult(
                            phase_name=phase_name,
                            status=CollectionPhaseStatus.SKIPPED,
                            start_time=datetime.utcnow(),
                            end_time=datetime.utcnow(),
                            execution_time_ms=0,
                            output_data={},
                            quality_score=None,
                            confidence_score=None,
                            metadata={"skip_reason": f"Not required for {automation_tier}"}
                        )
                        continue
                    
                    # Execute phase
                    logger.info(f"🔄 Executing phase: {phase_name}")
                    phase_result = await phase_executor()
                    self.phase_results[phase_name] = phase_result
                    
                    # Update flow state
                    await self.state_service.update_phase_status(
                        flow_id=flow_id,
                        phase_name=phase_name,
                        status=phase_result.status.value,
                        output_data=phase_result.output_data,
                        quality_score=phase_result.quality_score,
                        confidence_score=phase_result.confidence_score
                    )
                    
                    # Log audit event
                    await self.audit_logging.log_phase_completion(
                        flow_id=flow_id,
                        phase_name=phase_name,
                        status=phase_result.status.value,
                        execution_time_ms=phase_result.execution_time_ms,
                        quality_score=phase_result.quality_score
                    )
                    
                    # Check if phase failed and handle accordingly
                    if phase_result.status == CollectionPhaseStatus.FAILED:
                        error_msg = f"Phase {phase_name} failed: {phase_result.error_message}"
                        logger.error(error_msg)
                        
                        # Determine if flow should continue or stop
                        if self._is_critical_phase(phase_name):
                            raise FlowError(f"Critical phase failed: {phase_name}")
                        else:
                            logger.warning(f"⚠️ Non-critical phase failed, continuing: {phase_name}")
                    
                    logger.info(f"✅ Phase completed: {phase_name} ({phase_result.status.value})")
                    
                except Exception as e:
                    logger.error(f"❌ Phase execution error: {phase_name} - {str(e)}")
                    self.phase_results[phase_name] = PhaseResult(
                        phase_name=phase_name,
                        status=CollectionPhaseStatus.FAILED,
                        start_time=datetime.utcnow(),
                        end_time=datetime.utcnow(),
                        execution_time_ms=0,
                        output_data={},
                        quality_score=None,
                        confidence_score=None,
                        error_message=str(e)
                    )
                    
                    if self._is_critical_phase(phase_name):
                        raise
            
            # Calculate overall execution metrics
            execution_end = datetime.utcnow()
            total_execution_time = int((execution_end - execution_start).total_seconds() * 1000)
            
            # Generate final results
            final_results = await self._generate_final_results(total_execution_time)
            
            # Update final flow state
            await self.state_service.complete_collection_flow(
                flow_id=flow_id,
                final_results=final_results,
                execution_time_ms=total_execution_time
            )
            
            logger.info(f"✅ Collection Flow completed: {flow_id} ({total_execution_time}ms)")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Collection Flow execution failed: {flow_id} - {str(e)}")
            
            # Update flow state with failure
            await self.state_service.fail_collection_flow(
                flow_id=flow_id,
                error_message=str(e),
                phase_results=self.phase_results
            )
            
            raise FlowError(f"Collection Flow execution failed: {str(e)}")
    
    async def _execute_platform_detection_phase(self) -> PhaseResult:
        """Execute Phase 1: Platform Detection"""
        start_time = datetime.utcnow()
        
        try:
            # Use tier detection service to analyze environment
            tier_analysis = await self.tier_detection.analyze_environment_tier(
                environment_config=self.execution_context.environment_config,
                automation_tier=self.execution_context.automation_tier.value
            )
            
            # Create platform detection crew for AI-assisted detection
            crew_input = {
                "environment_config": self.execution_context.environment_config,
                "automation_tier": self.execution_context.automation_tier.value,
                "tier_analysis": tier_analysis
            }
            
            # Execute crew-based platform detection
            crew_result = await self._execute_crew_phase(
                crew_type="platform_detection",
                crew_input=crew_input,
                timeout_seconds=self.execution_context.timeout_config.get("platform_detection", 600)
            )
            
            # Process and validate results
            detected_platforms = crew_result.get("platforms", [])
            adapter_recommendations = crew_result.get("recommended_adapters", [])
            
            # Validate platform detection quality
            quality_score = await self.quality_assessment.assess_platform_detection_quality(
                detected_platforms=detected_platforms,
                tier_analysis=tier_analysis
            )
            
            confidence_score = await self.confidence_scoring.calculate_platform_confidence(
                platforms=detected_platforms,
                tier_analysis=tier_analysis
            )
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="platform_detection",
                status=CollectionPhaseStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={
                    "detected_platforms": detected_platforms,
                    "adapter_recommendations": adapter_recommendations,
                    "tier_analysis": tier_analysis,
                    "platform_metadata": crew_result.get("platform_metadata", {})
                },
                quality_score=quality_score,
                confidence_score=confidence_score,
                metadata={
                    "crew_execution_time": crew_result.get("execution_time_ms"),
                    "platforms_count": len(detected_platforms),
                    "adapters_recommended": len(adapter_recommendations)
                }
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="platform_detection",
                status=CollectionPhaseStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={},
                quality_score=None,
                confidence_score=None,
                error_message=str(e)
            )
    
    async def _execute_automated_collection_phase(self) -> PhaseResult:
        """Execute Phase 2: Automated Collection"""
        start_time = datetime.utcnow()
        
        try:
            # Get platform detection results
            platform_result = self.phase_results.get("platform_detection")
            if not platform_result or platform_result.status != CollectionPhaseStatus.COMPLETED:
                raise InvalidFlowStateError("Platform detection must complete successfully before automated collection")
            
            detected_platforms = platform_result.output_data.get("detected_platforms", [])
            adapter_recommendations = platform_result.output_data.get("adapter_recommendations", [])
            
            # Prepare adapters based on recommendations
            prepared_adapters = []
            for adapter_rec in adapter_recommendations:
                adapter = adapter_registry.get_adapter(adapter_rec["adapter_type"])
                if adapter:
                    prepared_adapters.append({
                        "adapter": adapter,
                        "platform": adapter_rec["platform"],
                        "config": adapter_rec.get("config", {})
                    })
            
            # Execute automated collection crew
            crew_input = {
                "platforms": detected_platforms,
                "adapter_configs": [prep["config"] for prep in prepared_adapters],
                "automation_tier": self.execution_context.automation_tier.value,
                "quality_thresholds": self.execution_context.quality_thresholds
            }
            
            crew_result = await self._execute_crew_phase(
                crew_type="automated_collection",
                crew_input=crew_input,
                timeout_seconds=self.execution_context.timeout_config.get("automated_collection", 3600)
            )
            
            # Process collected data
            collected_data = crew_result.get("collected_data", [])
            collection_metrics = crew_result.get("metrics", {})
            
            # Transform and normalize collected data
            transformed_data = await self.data_transformation.transform_collected_data(
                raw_data=collected_data,
                platforms=detected_platforms,
                normalization_rules=self.execution_context.client_requirements.get("normalization_rules", {})
            )
            
            # Assess collection quality
            quality_scores = await self.quality_assessment.assess_collection_quality(
                collected_data=transformed_data,
                expected_platforms=detected_platforms,
                automation_tier=self.execution_context.automation_tier.value
            )
            
            confidence_score = await self.confidence_scoring.calculate_collection_confidence(
                collected_data=transformed_data,
                quality_scores=quality_scores,
                collection_metrics=collection_metrics
            )
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="automated_collection",
                status=CollectionPhaseStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={
                    "collected_data": transformed_data,
                    "collection_metrics": collection_metrics,
                    "quality_scores": quality_scores,
                    "collection_gaps": crew_result.get("identified_gaps", [])
                },
                quality_score=quality_scores.get("overall_quality", 0.0),
                confidence_score=confidence_score,
                metadata={
                    "adapters_used": len(prepared_adapters),
                    "data_points_collected": len(transformed_data),
                    "collection_success_rate": collection_metrics.get("success_rate", 0.0)
                }
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="automated_collection",
                status=CollectionPhaseStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={},
                quality_score=None,
                confidence_score=None,
                error_message=str(e)
            )
    
    async def _execute_gap_analysis_phase(self) -> PhaseResult:
        """Execute Phase 3: Gap Analysis"""
        start_time = datetime.utcnow()
        
        try:
            # Get previous phase results
            collection_result = self.phase_results.get("automated_collection")
            if not collection_result:
                raise InvalidFlowStateError("Automated collection must complete before gap analysis")
            
            collected_data = collection_result.output_data.get("collected_data", [])
            collection_gaps = collection_result.output_data.get("collection_gaps", [])
            
            # Execute AI-powered gap analysis
            gap_analysis_result = await self.gap_analysis_agent.analyze_data_gaps(
                collected_data=collected_data,
                existing_gaps=collection_gaps,
                sixr_requirements=self.execution_context.client_requirements.get("sixr_requirements", {}),
                automation_tier=self.execution_context.automation_tier.value
            )
            
            # Execute gap analysis crew for comprehensive analysis
            crew_input = {
                "collected_data": collected_data,
                "sixr_requirements": self.execution_context.client_requirements.get("sixr_requirements", {}),
                "automation_tier": self.execution_context.automation_tier.value,
                "existing_gaps": collection_gaps
            }
            
            crew_result = await self._execute_crew_phase(
                crew_type="gap_analysis",
                crew_input=crew_input,
                timeout_seconds=self.execution_context.timeout_config.get("gap_analysis", 900)
            )
            
            # Combine AI and crew analysis results
            identified_gaps = crew_result.get("data_gaps", [])
            gap_categories = crew_result.get("gap_categories", {})
            sixr_impact = crew_result.get("sixr_impact_analysis", {})
            resolution_recommendations = crew_result.get("recommendations", [])
            
            # Assess gap analysis quality
            quality_score = await self.quality_assessment.assess_gap_analysis_quality(
                identified_gaps=identified_gaps,
                gap_categories=gap_categories,
                sixr_impact=sixr_impact
            )
            
            confidence_score = await self.confidence_scoring.calculate_gap_analysis_confidence(
                gaps=identified_gaps,
                analysis_depth=gap_categories,
                ai_analysis=gap_analysis_result
            )
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="gap_analysis",
                status=CollectionPhaseStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={
                    "identified_gaps": identified_gaps,
                    "gap_categories": gap_categories,
                    "sixr_impact": sixr_impact,
                    "resolution_recommendations": resolution_recommendations,
                    "ai_analysis": gap_analysis_result
                },
                quality_score=quality_score,
                confidence_score=confidence_score,
                metadata={
                    "total_gaps": len(identified_gaps),
                    "critical_gaps": len([g for g in identified_gaps if g.get("criticality") == "high"]),
                    "sixr_impact_score": sixr_impact.get("overall_impact_score", 0.0)
                }
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="gap_analysis",
                status=CollectionPhaseStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={},
                quality_score=None,
                confidence_score=None,
                error_message=str(e)
            )
    
    async def _execute_manual_collection_phase(self) -> PhaseResult:
        """Execute Phase 4: Manual Collection"""
        start_time = datetime.utcnow()
        
        try:
            # Get gap analysis results
            gap_result = self.phase_results.get("gap_analysis")
            if not gap_result:
                raise InvalidFlowStateError("Gap analysis must complete before manual collection")
            
            identified_gaps = gap_result.output_data.get("identified_gaps", [])
            resolution_recommendations = gap_result.output_data.get("resolution_recommendations", [])
            
            # Check if manual collection is needed
            if not identified_gaps or self.execution_context.automation_tier == AutomationTier.TIER_1:
                logger.info("⏭️ No gaps identified or full automation tier - skipping manual collection")
                return PhaseResult(
                    phase_name="manual_collection",
                    status=CollectionPhaseStatus.SKIPPED,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    execution_time_ms=0,
                    output_data={},
                    quality_score=None,
                    confidence_score=None,
                    metadata={"skip_reason": "No gaps requiring manual collection"}
                )
            
            # Generate questionnaires for identified gaps
            questionnaires = await self.questionnaire_generator.generate_questionnaires(
                data_gaps=identified_gaps,
                business_context=self.execution_context.client_requirements.get("business_context", {}),
                automation_tier=self.execution_context.automation_tier.value
            )
            
            # Create adaptive forms using manual collection services
            form_configs = []
            for questionnaire in questionnaires:
                form_config = await self.adaptive_form_service.create_adaptive_form(
                    questionnaire_data=questionnaire,
                    gap_context=identified_gaps,
                    template_preferences=self.execution_context.client_requirements.get("form_preferences", {})
                )
                form_configs.append(form_config)
            
            # Execute manual collection crew
            crew_input = {
                "data_gaps": identified_gaps,
                "templates": questionnaires,
                "existing_data": self.phase_results.get("automated_collection", {}).get("output_data", {}).get("collected_data", [])
            }
            
            crew_result = await self._execute_crew_phase(
                crew_type="manual_collection",
                crew_input=crew_input,
                timeout_seconds=self.execution_context.timeout_config.get("manual_collection", 7200)
            )
            
            # Process questionnaire responses
            responses = crew_result.get("responses", [])
            validation_results = crew_result.get("validation", {})
            
            # Validate responses using validation service
            validated_responses = await self.validation_service.validate_questionnaire_responses(
                responses=responses,
                validation_rules=self.execution_context.client_requirements.get("validation_rules", {}),
                gap_context=identified_gaps
            )
            
            # Track progress using progress tracking service
            progress_metrics = await self.progress_tracking.calculate_collection_progress(
                total_gaps=len(identified_gaps),
                completed_responses=len(validated_responses),
                validation_results=validation_results
            )
            
            # Calculate confidence scores
            confidence_score = await self.confidence_scoring.calculate_manual_collection_confidence(
                responses=validated_responses,
                validation_results=validation_results,
                progress_metrics=progress_metrics
            )
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="manual_collection",
                status=CollectionPhaseStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={
                    "questionnaire_responses": validated_responses,
                    "validation_results": validation_results,
                    "confidence_scores": crew_result.get("confidence", {}),
                    "remaining_gaps": crew_result.get("unresolved_gaps", []),
                    "form_configs": form_configs,
                    "progress_metrics": progress_metrics
                },
                quality_score=validation_results.get("overall_quality", 0.0),
                confidence_score=confidence_score,
                metadata={
                    "total_responses": len(validated_responses),
                    "validation_pass_rate": validation_results.get("pass_rate", 0.0),
                    "gaps_resolved": len(identified_gaps) - len(crew_result.get("unresolved_gaps", []))
                }
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="manual_collection",
                status=CollectionPhaseStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={},
                quality_score=None,
                confidence_score=None,
                error_message=str(e)
            )
    
    async def _execute_synthesis_phase(self) -> PhaseResult:
        """Execute Phase 5: Data Synthesis"""
        start_time = datetime.utcnow()
        
        try:
            # Gather all collected data from previous phases
            automated_data = self.phase_results.get("automated_collection", {}).get("output_data", {}).get("collected_data", [])
            manual_data = self.phase_results.get("manual_collection", {}).get("output_data", {}).get("questionnaire_responses", [])
            
            # Integrate all data using data integration service
            integrated_data = await self.data_integration.integrate_collection_data(
                automated_data=automated_data,
                manual_data=manual_data,
                integration_rules=self.execution_context.client_requirements.get("integration_rules", {}),
                conflict_resolution=self.execution_context.client_requirements.get("conflict_resolution", "priority_based")
            )
            
            # Execute data synthesis crew
            crew_input = {
                "automated_data": automated_data,
                "manual_data": manual_data,
                "validation_rules": self.execution_context.client_requirements.get("validation_rules", {}),
                "automation_tier": self.execution_context.automation_tier.value
            }
            
            crew_result = await self._execute_crew_phase(
                crew_type="data_synthesis",
                crew_input=crew_input,
                timeout_seconds=self.execution_context.timeout_config.get("synthesis", 1200)
            )
            
            # Generate final quality report
            quality_report = await self.quality_assessment.generate_final_quality_report(
                synthesized_data=integrated_data,
                phase_results=self.phase_results,
                automation_tier=self.execution_context.automation_tier.value
            )
            
            # Calculate SIXR readiness score
            sixr_readiness_score = await self.business_analyzer.calculate_sixr_readiness(
                synthesized_data=integrated_data,
                quality_report=quality_report,
                sixr_requirements=self.execution_context.client_requirements.get("sixr_requirements", {})
            )
            
            # Generate collection summary
            collection_summary = await self._generate_collection_summary(
                synthesized_data=integrated_data,
                quality_report=quality_report,
                sixr_readiness_score=sixr_readiness_score
            )
            
            # Final confidence assessment
            confidence_score = await self.confidence_scoring.calculate_final_confidence(
                synthesized_data=integrated_data,
                quality_report=quality_report,
                phase_results=self.phase_results
            )
            
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="synthesis",
                status=CollectionPhaseStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={
                    "synthesized_data": integrated_data,
                    "quality_report": quality_report,
                    "sixr_readiness": sixr_readiness_score,
                    "collection_summary": collection_summary
                },
                quality_score=quality_report.get("overall_quality_score", 0.0),
                confidence_score=confidence_score,
                metadata={
                    "total_data_points": len(integrated_data),
                    "automated_data_points": len(automated_data),
                    "manual_data_points": len(manual_data),
                    "data_completeness": quality_report.get("completeness_score", 0.0)
                }
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return PhaseResult(
                phase_name="synthesis",
                status=CollectionPhaseStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time_ms=execution_time,
                output_data={},
                quality_score=None,
                confidence_score=None,
                error_message=str(e)
            )
    
    async def _execute_crew_phase(
        self,
        crew_type: str,
        crew_input: Dict[str, Any],
        timeout_seconds: int
    ) -> Dict[str, Any]:
        """Execute a CrewAI crew for a specific phase"""
        try:
            # Import and execute the appropriate crew
            if crew_type == "platform_detection":
                from app.services.crewai_flows.crews.collection.platform_detection_crew import create_platform_detection_crew
                crew = create_platform_detection_crew()
            elif crew_type == "automated_collection":
                from app.services.crewai_flows.crews.collection.automated_collection_crew import create_automated_collection_crew
                crew = create_automated_collection_crew()
            elif crew_type == "gap_analysis":
                from app.services.crewai_flows.crews.collection.gap_analysis_crew import create_gap_analysis_crew
                crew = create_gap_analysis_crew()
            elif crew_type == "manual_collection":
                from app.services.crewai_flows.crews.collection.manual_collection_crew import create_manual_collection_crew
                crew = create_manual_collection_crew()
            elif crew_type == "data_synthesis":
                from app.services.crewai_flows.crews.collection.data_synthesis_crew import create_data_synthesis_crew
                crew = create_data_synthesis_crew()
            else:
                raise ValueError(f"Unknown crew type: {crew_type}")
            
            # Execute crew with timeout
            start_time = datetime.utcnow()
            result = await asyncio.wait_for(
                crew.kickoff(inputs=crew_input),
                timeout=timeout_seconds
            )
            end_time = datetime.utcnow()
            
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Return normalized result
            return {
                "execution_time_ms": execution_time_ms,
                "success": True,
                **result
            }
            
        except asyncio.TimeoutError:
            raise FlowError(f"Crew execution timeout: {crew_type} ({timeout_seconds}s)")
        except Exception as e:
            raise FlowError(f"Crew execution failed: {crew_type} - {str(e)}")
    
    def _should_skip_phase(self, phase_name: str, automation_tier: str) -> bool:
        """Determine if a phase should be skipped based on automation tier"""
        skip_rules = {
            AutomationTier.TIER_1: ["manual_collection"],  # Full automation
            AutomationTier.TIER_2: [],  # Minimal manual
            AutomationTier.TIER_3: [],  # Moderate manual
            AutomationTier.TIER_4: []   # Manual-heavy
        }
        
        tier = AutomationTier(automation_tier)
        return phase_name in skip_rules.get(tier, [])
    
    def _is_critical_phase(self, phase_name: str) -> bool:
        """Determine if a phase is critical for flow continuation"""
        critical_phases = ["platform_detection", "synthesis"]
        return phase_name in critical_phases
    
    def _get_quality_thresholds(self, automation_tier: str) -> Dict[str, float]:
        """Get quality thresholds based on automation tier"""
        thresholds = {
            "tier_1": {"overall": 0.95, "platform_detection": 0.95, "collection": 0.95, "synthesis": 0.95},
            "tier_2": {"overall": 0.85, "platform_detection": 0.85, "collection": 0.85, "synthesis": 0.85},
            "tier_3": {"overall": 0.75, "platform_detection": 0.75, "collection": 0.75, "synthesis": 0.75},
            "tier_4": {"overall": 0.60, "platform_detection": 0.60, "collection": 0.60, "synthesis": 0.60}
        }
        return thresholds.get(automation_tier, thresholds["tier_2"])
    
    def _get_timeout_config(self, automation_tier: str) -> Dict[str, int]:
        """Get timeout configuration based on automation tier"""
        return {
            "platform_detection": 600,   # 10 minutes
            "automated_collection": 3600,  # 60 minutes
            "gap_analysis": 900,          # 15 minutes
            "manual_collection": 7200,    # 2 hours
            "synthesis": 1200             # 20 minutes
        }
    
    async def _generate_final_results(self, total_execution_time: int) -> Dict[str, Any]:
        """Generate final execution results"""
        return {
            "flow_id": self.execution_context.flow_id,
            "automation_tier": self.execution_context.automation_tier.value,
            "execution_time_ms": total_execution_time,
            "phase_results": {name: result.__dict__ for name, result in self.phase_results.items()},
            "overall_status": self._calculate_overall_status(),
            "overall_quality_score": self._calculate_overall_quality(),
            "overall_confidence_score": self._calculate_overall_confidence(),
            "data_summary": self._generate_data_summary(),
            "recommendations": self._generate_recommendations(),
            "next_steps": self._generate_next_steps()
        }
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall flow status based on phase results"""
        completed_phases = sum(1 for result in self.phase_results.values() 
                             if result.status == CollectionPhaseStatus.COMPLETED)
        failed_phases = sum(1 for result in self.phase_results.values() 
                           if result.status == CollectionPhaseStatus.FAILED)
        
        if failed_phases > 0:
            return "completed_with_failures"
        elif completed_phases == len(self.phase_results):
            return "completed"
        else:
            return "partially_completed"
    
    def _calculate_overall_quality(self) -> float:
        """Calculate overall quality score across all phases"""
        quality_scores = [result.quality_score for result in self.phase_results.values() 
                         if result.quality_score is not None]
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_overall_confidence(self) -> float:
        """Calculate overall confidence score across all phases"""
        confidence_scores = [result.confidence_score for result in self.phase_results.values() 
                           if result.confidence_score is not None]
        return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    
    def _generate_data_summary(self) -> Dict[str, Any]:
        """Generate summary of collected data"""
        automated_data = self.phase_results.get("automated_collection", {}).get("output_data", {}).get("collected_data", [])
        manual_data = self.phase_results.get("manual_collection", {}).get("output_data", {}).get("questionnaire_responses", [])
        synthesized_data = self.phase_results.get("synthesis", {}).get("output_data", {}).get("synthesized_data", [])
        
        return {
            "automated_data_points": len(automated_data),
            "manual_data_points": len(manual_data),
            "synthesized_data_points": len(synthesized_data),
            "total_platforms_detected": len(self.phase_results.get("platform_detection", {}).get("output_data", {}).get("detected_platforms", [])),
            "gaps_identified": len(self.phase_results.get("gap_analysis", {}).get("output_data", {}).get("identified_gaps", [])),
            "gaps_resolved": len(self.phase_results.get("gap_analysis", {}).get("output_data", {}).get("identified_gaps", [])) - 
                           len(self.phase_results.get("manual_collection", {}).get("output_data", {}).get("remaining_gaps", []))
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on execution results"""
        recommendations = []
        
        # Quality-based recommendations
        overall_quality = self._calculate_overall_quality()
        if overall_quality < 0.8:
            recommendations.append("Consider improving data collection quality through additional validation")
        
        # Gap-based recommendations
        remaining_gaps = self.phase_results.get("manual_collection", {}).get("output_data", {}).get("remaining_gaps", [])
        if remaining_gaps:
            recommendations.append(f"Address {len(remaining_gaps)} remaining data gaps for complete coverage")
        
        # Automation tier recommendations
        if self.execution_context.automation_tier in [AutomationTier.TIER_3, AutomationTier.TIER_4]:
            recommendations.append("Consider upgrading automation tier for improved efficiency")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps for flow continuation"""
        next_steps = []
        
        # Check SIXR readiness
        sixr_readiness = self.phase_results.get("synthesis", {}).get("output_data", {}).get("sixr_readiness", 0.0)
        if sixr_readiness >= 0.75:
            next_steps.append("Data is ready for Discovery Flow - initiate handoff")
        else:
            next_steps.append("Improve data quality before proceeding to Discovery Flow")
        
        # Manual collection follow-up
        remaining_gaps = self.phase_results.get("manual_collection", {}).get("output_data", {}).get("remaining_gaps", [])
        if remaining_gaps:
            next_steps.append("Schedule follow-up manual collection for remaining gaps")
        
        return next_steps
    
    async def _generate_collection_summary(
        self,
        synthesized_data: List[Dict[str, Any]],
        quality_report: Dict[str, Any],
        sixr_readiness_score: float
    ) -> Dict[str, Any]:
        """Generate comprehensive collection summary"""
        return {
            "execution_summary": {
                "automation_tier": self.execution_context.automation_tier.value,
                "phases_executed": len(self.phase_results),
                "successful_phases": len([r for r in self.phase_results.values() if r.status == CollectionPhaseStatus.COMPLETED]),
                "total_execution_time_ms": sum(r.execution_time_ms or 0 for r in self.phase_results.values())
            },
            "data_summary": self._generate_data_summary(),
            "quality_summary": {
                "overall_quality": quality_report.get("overall_quality_score", 0.0),
                "completeness": quality_report.get("completeness_score", 0.0),
                "accuracy": quality_report.get("accuracy_score", 0.0),
                "consistency": quality_report.get("consistency_score", 0.0)
            },
            "sixr_readiness": {
                "readiness_score": sixr_readiness_score,
                "ready_for_discovery": sixr_readiness_score >= 0.75,
                "improvement_areas": quality_report.get("improvement_areas", [])
            },
            "recommendations": self._generate_recommendations(),
            "next_steps": self._generate_next_steps()
        }