"""
Automated Collection Phase Manager

Handles the orchestration of automated data collection in the collection flow.
This manager coordinates with platform adapters to collect data from detected platforms.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from app.models.collection_flow import (
    CollectionPhase, CollectionStatus, DataDomain
)
from app.services.collection_flow import (
    DataTransformationService, QualityAssessmentService
)
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff
from app.services.crewai_flows.handlers.enhanced_error_handler import enhanced_error_handler

logger = logging.getLogger(__name__)


class AutomatedCollectionManager:
    """
    Manages the automated collection phase of the collection flow.
    
    This manager handles:
    - Automated data collection crew creation and execution
    - Platform adapter coordination
    - Data transformation and normalization
    - Collection quality assessment
    - Progress tracking and state updates
    - Error recovery and retry logic
    """
    
    def __init__(self, flow_context, state_manager, audit_service):
        """
        Initialize the automated collection manager.
        
        Args:
            flow_context: Flow context containing flow ID, client, and engagement info
            state_manager: State manager for persisting flow state
            audit_service: Audit logging service
        """
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.audit_service = audit_service
        
        # Initialize services
        self.data_transformation = DataTransformationService()
        self.quality_assessment = QualityAssessmentService()
        
        # Collection configuration
        self.collection_timeout_minutes = 60
        self.batch_size = 100
        self.retry_attempts = 3
    
    async def execute(self, flow_state, crewai_service, client_requirements) -> Dict[str, Any]:
        """
        Execute the automated collection phase.
        
        Args:
            flow_state: Current collection flow state
            crewai_service: CrewAI service for creating crews
            client_requirements: Client-specific requirements
            
        Returns:
            Dict containing phase execution results
        """
        try:
            logger.info(f"🤖 Starting automated collection for flow {self.flow_context.flow_id}")
            
            # Update state to indicate phase start
            flow_state.status = CollectionStatus.COLLECTING_DATA
            flow_state.current_phase = CollectionPhase.AUTOMATED_COLLECTION
            flow_state.updated_at = datetime.utcnow()
            
            # Get platform detection results
            detected_platforms = flow_state.detected_platforms
            adapter_recommendations = flow_state.collection_config.get("adapter_recommendations", [])
            tier_analysis = flow_state.phase_results.get("platform_detection", {}).get("tier_analysis", {})
            
            # Execute collection crew
            collection_results = await self._execute_collection_crew(
                crewai_service, detected_platforms, adapter_recommendations,
                tier_analysis, flow_state.automation_tier
            )
            
            # Transform and process collected data
            processed_data = await self._process_collected_data(
                collection_results, detected_platforms, client_requirements
            )
            
            # Assess collection quality
            quality_metrics = await self._assess_collection_quality(
                processed_data, detected_platforms, flow_state.automation_tier
            )
            
            # Update flow state
            await self._update_flow_state(flow_state, processed_data, quality_metrics)
            
            # Log phase completion
            await self.audit_service.log_flow_event(
                flow_id=self.flow_context.flow_id,
                event_type="automated_collection_completed",
                event_data={
                    "data_collected": len(processed_data["transformed_data"]),
                    "platforms_collected": len(processed_data["platform_results"]),
                    "quality_score": quality_metrics["overall_quality"],
                    "collection_time_ms": processed_data["collection_metrics"].get("total_time_ms")
                }
            )
            
            return {
                "phase": "automated_collection",
                "status": "completed",
                "data_collected": len(processed_data["transformed_data"]),
                "quality_score": quality_metrics["overall_quality"],
                "next_phase": "gap_analysis",
                "identified_gaps": processed_data.get("identified_gaps", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Automated collection failed: {e}")
            flow_state.add_error("automated_collection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise
    
    async def resume(self, flow_state, user_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Resume automated collection after pause.
        
        Args:
            flow_state: Current collection flow state
            user_inputs: Optional user inputs for retry configuration
            
        Returns:
            Dict containing resume results
        """
        logger.info(f"🔄 Resuming automated collection for flow {self.flow_context.flow_id}")
        
        if user_inputs and user_inputs.get("retry_failed_platforms"):
            # Retry collection for failed platforms
            failed_platforms = flow_state.collection_results.get("failed_platforms", [])
            if failed_platforms:
                logger.info(f"🔁 Retrying collection for {len(failed_platforms)} failed platforms")
                # Implementation would retry collection for specific platforms
                pass
        
        # Update progress and move to next phase
        flow_state.progress = 40.0
        flow_state.next_phase = CollectionPhase.GAP_ANALYSIS
        await self.state_manager.save_state(flow_state.to_dict())
        
        return {
            "phase": "automated_collection",
            "status": "resumed",
            "next_phase": "gap_analysis",
            "can_proceed": True
        }
    
    async def _execute_collection_crew(self, crewai_service, detected_platforms,
                                     adapter_recommendations, tier_analysis,
                                     automation_tier) -> Dict[str, Any]:
        """Create and execute the automated collection crew"""
        logger.info("🤖 Creating automated collection crew")
        
        # Import crew creation function
        from app.services.crewai_flows.crews.collection.automated_collection_crew import (
            create_automated_collection_crew
        )
        
        # Get available adapters
        available_adapters = await self._get_available_adapters()
        
        # Create crew with context
        crew = create_automated_collection_crew(
            crewai_service=crewai_service,
            platforms=detected_platforms,
            tier_assessments=tier_analysis,
            context={
                "available_adapters": available_adapters,
                "collection_timeout_minutes": self.collection_timeout_minutes,
                "quality_thresholds": {"minimum": 0.8},
                "batch_size": self.batch_size,
                "flow_id": self.flow_context.flow_id
            }
        )
        
        # Execute with retry and timeout
        logger.info("🚀 Executing automated collection crew")
        
        try:
            crew_result = await asyncio.wait_for(
                retry_with_backoff(
                    crew.kickoff,
                    inputs={
                        "platforms": detected_platforms,
                        "adapter_configs": adapter_recommendations
                    }
                ),
                timeout=self.collection_timeout_minutes * 60
            )
            return crew_result
        except asyncio.TimeoutError:
            logger.error(f"Collection timed out after {self.collection_timeout_minutes} minutes")
            raise
    
    async def _process_collected_data(self, collection_results: Dict[str, Any],
                                    detected_platforms: List[Dict],
                                    client_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process and transform collected data"""
        logger.info("🔧 Processing collected data")
        
        # Extract raw data from collection results
        collected_data = collection_results.get("collected_data", [])
        collection_metrics = collection_results.get("collection_metrics", {})
        platform_results = collection_results.get("platform_results", {})
        
        # Transform data according to client requirements
        transformed_data = await self.data_transformation.transform_collected_data(
            raw_data=collected_data,
            platforms=detected_platforms,
            normalization_rules=client_requirements.get("normalization_rules", {})
        )
        
        # Identify initial gaps
        identified_gaps = self._identify_initial_gaps(
            transformed_data, detected_platforms, platform_results
        )
        
        return {
            "raw_data": collected_data,
            "transformed_data": transformed_data,
            "collection_metrics": collection_metrics,
            "platform_results": platform_results,
            "identified_gaps": identified_gaps
        }
    
    async def _assess_collection_quality(self, processed_data: Dict[str, Any],
                                       detected_platforms: List[Dict],
                                       automation_tier: str) -> Dict[str, Any]:
        """Assess the quality of collected data"""
        logger.info("📊 Assessing collection quality")
        
        quality_scores = await self.quality_assessment.assess_collection_quality(
            collected_data=processed_data["transformed_data"],
            expected_platforms=detected_platforms,
            automation_tier=automation_tier
        )
        
        # Calculate domain coverage
        domain_coverage = self._calculate_domain_coverage(
            processed_data["transformed_data"]
        )
        
        # Assess platform coverage
        platform_coverage = self._calculate_platform_coverage(
            processed_data["platform_results"], detected_platforms
        )
        
        return {
            "overall_quality": quality_scores.get("overall_quality", 0.0),
            "data_completeness": quality_scores.get("completeness", 0.0),
            "data_accuracy": quality_scores.get("accuracy", 0.0),
            "domain_coverage": domain_coverage,
            "platform_coverage": platform_coverage,
            "quality_details": quality_scores
        }
    
    async def _update_flow_state(self, flow_state, processed_data: Dict[str, Any],
                               quality_metrics: Dict[str, Any]):
        """Update flow state with collection results"""
        logger.info("💾 Updating flow state with collection results")
        
        # Update collected data
        flow_state.collected_data = processed_data["transformed_data"]
        flow_state.collection_results = {
            "raw_data": processed_data["raw_data"],
            "transformed_data": processed_data["transformed_data"],
            "metrics": processed_data["collection_metrics"],
            "platform_results": processed_data["platform_results"],
            "identified_gaps": processed_data["identified_gaps"]
        }
        
        # Store phase results
        flow_state.phase_results["automated_collection"] = {
            "collection_summary": {
                "total_items_collected": len(processed_data["transformed_data"]),
                "platforms_succeeded": len([p for p, r in processed_data["platform_results"].items() 
                                           if r.get("status") == "success"]),
                "platforms_failed": len([p for p, r in processed_data["platform_results"].items() 
                                       if r.get("status") == "failed"])
            },
            "quality_metrics": quality_metrics,
            "collection_time": processed_data["collection_metrics"].get("total_time_ms", 0),
            "identified_gaps": processed_data["identified_gaps"]
        }
        
        # Update quality score
        flow_state.collection_quality_score = quality_metrics["overall_quality"]
        
        # Update progress
        flow_state.progress = 40.0
        flow_state.next_phase = CollectionPhase.GAP_ANALYSIS
        
        # Persist state
        await self.state_manager.save_state(flow_state.to_dict())
    
    async def _get_available_adapters(self) -> Dict[str, Any]:
        """Get available platform adapters"""
        from app.services.collection_flow.adapters import adapter_registry
        
        adapters = {}
        for adapter_type in adapter_registry.list_adapters():
            adapter_info = adapter_registry.get_adapter_info(adapter_type)
            if adapter_info:
                adapters[adapter_type] = adapter_info
        
        return adapters
    
    def _identify_initial_gaps(self, transformed_data: List[Dict],
                             detected_platforms: List[Dict],
                             platform_results: Dict[str, Any]) -> List[Dict]:
        """Identify initial data gaps from collection"""
        gaps = []
        
        # Check for failed platform collections
        for platform in detected_platforms:
            platform_name = platform.get("name")
            if platform_name in platform_results:
                result = platform_results[platform_name]
                if result.get("status") == "failed":
                    gaps.append({
                        "type": "platform_collection_failed",
                        "platform": platform_name,
                        "reason": result.get("error", "Unknown error"),
                        "severity": "high"
                    })
        
        # Check for missing critical data domains
        collected_domains = set()
        for item in transformed_data:
            if "domain" in item:
                collected_domains.add(item["domain"])
        
        critical_domains = [DataDomain.APPLICATIONS, DataDomain.INFRASTRUCTURE, DataDomain.DEPENDENCIES]
        for domain in critical_domains:
            if domain.value not in collected_domains:
                gaps.append({
                    "type": "missing_domain",
                    "domain": domain.value,
                    "severity": "medium"
                })
        
        return gaps
    
    def _calculate_domain_coverage(self, transformed_data: List[Dict]) -> Dict[str, float]:
        """Calculate coverage for each data domain"""
        domain_counts = {}
        total_items = len(transformed_data)
        
        if total_items == 0:
            return {domain.value: 0.0 for domain in DataDomain}
        
        # Count items per domain
        for item in transformed_data:
            domain = item.get("domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Calculate coverage percentages
        coverage = {}
        for domain in DataDomain:
            count = domain_counts.get(domain.value, 0)
            coverage[domain.value] = (count / total_items) * 100
        
        return coverage
    
    def _calculate_platform_coverage(self, platform_results: Dict[str, Any],
                                   detected_platforms: List[Dict]) -> float:
        """Calculate percentage of platforms successfully collected"""
        if not detected_platforms:
            return 100.0
        
        successful_platforms = sum(1 for p in detected_platforms
                                 if platform_results.get(p.get("name", ""), {}).get("status") == "success")
        
        return (successful_platforms / len(detected_platforms)) * 100