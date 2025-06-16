"""
CrewAI Discovery Flow - Modular Architecture
Main flow orchestration following CrewAI best practices with proper modular design.

Corrected Flow Sequence:
1. Field Mapping Crew - Foundation (understand data structure FIRST)
2. Data Cleansing Crew - Quality assurance based on field mappings  
3. Inventory Building Crew - Multi-domain asset classification
4. App-Server Dependency Crew - Hosting relationship mapping
5. App-App Dependency Crew - Integration dependency analysis
6. Technical Debt Crew - 6R strategy preparation
7. Discovery Integration - Final consolidation for Assessment Flow

Architecture follows CrewAI best practices with modular design:
- Manager agents for hierarchical coordination
- Shared memory for cross-crew learning
- Knowledge bases for domain expertise
- Agent collaboration for cross-domain insights
- Planning integration with success criteria
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# CrewAI imports with full functionality
from crewai.flow.flow import Flow, listen, start
from crewai.planning import PlanningMixin

# Local modular imports
from .models.flow_state import DiscoveryFlowState
from .handlers.initialization_handler import InitializationHandler
from .handlers.crew_execution_handler import CrewExecutionHandler
from .handlers.callback_handler import CallbackHandler
from .handlers.session_handler import SessionHandler
from .handlers.error_handler import ErrorHandler
from .handlers.status_handler import StatusHandler

logger = logging.getLogger(__name__)

class DiscoveryFlowRedesigned(Flow[DiscoveryFlowState], PlanningMixin):
    """
    Discovery Flow with Corrected Architecture following CrewAI Best Practices
    
    This implementation addresses the critical design flaws:
    1. ✅ Correct Flow Sequence: Field mapping FIRST, then data processing
    2. ✅ Specialized Crews: Domain experts for each analysis area
    3. ✅ Manager Agents: Hierarchical coordination for complex crews
    4. ✅ Shared Memory: Cross-crew learning and knowledge sharing
    5. ✅ Knowledge Bases: Domain-specific expertise integration
    6. ✅ Agent Collaboration: Cross-domain insights and coordination
    7. ✅ Planning Integration: Comprehensive planning with success criteria
    """
    
    def __init__(self, crewai_service, context, **kwargs):
        # Store initialization parameters
        self._init_session_id = kwargs.get('session_id', str(uuid.uuid4()))
        self._init_client_account_id = kwargs.get('client_account_id', context.client_account_id)
        self._init_engagement_id = kwargs.get('engagement_id', context.engagement_id)
        self._init_user_id = kwargs.get('user_id', context.user_id or "anonymous")
        self._init_raw_data = kwargs.get('raw_data', [])
        self._init_metadata = kwargs.get('metadata', {})
        
        # Initialize Flow and Planning
        super().__init__()
        
        # Store services
        self.crewai_service = crewai_service
        self.context = context
        
        # Initialize handlers
        self.initialization_handler = InitializationHandler(crewai_service, context)
        self.crew_execution_handler = CrewExecutionHandler(crewai_service)
        self.callback_handler = CallbackHandler()
        self.session_handler = SessionHandler()
        self.error_handler = ErrorHandler()
        self.status_handler = StatusHandler()
        
        # Setup components through handlers
        self._setup_components()
        
        logger.info(f"Discovery Flow Redesigned initialized: {self.fingerprint.uuid_str}")
    
    def _setup_components(self):
        """Setup all flow components through handlers"""
        # Initialize shared resources
        self.shared_memory = self.initialization_handler.setup_shared_memory()
        self.knowledge_bases = self.initialization_handler.setup_knowledge_bases()
        
        # Setup fingerprint and sessions
        self.fingerprint = self.initialization_handler.setup_fingerprint(
            self._init_session_id, 
            self._init_client_account_id, 
            self._init_engagement_id,
            self._init_raw_data
        )
        
        # Setup database sessions and callbacks
        self.session_handler.setup_database_sessions()
        self.callback_handler.setup_callbacks()
        
        # Planning capabilities
        self.planning_enabled = True
        self.planning_llm = self.crewai_service.llm if hasattr(self.crewai_service, 'llm') else None
    
    @start()
    def initialize_discovery_flow(self):
        """Initialize with comprehensive planning"""
        logger.info("🚀 Initializing Discovery Flow with Corrected Architecture")
        
        # Initialize flow state through handler
        initialization_result = self.initialization_handler.initialize_flow_state(
            session_id=self._init_session_id,
            client_account_id=self._init_client_account_id,
            engagement_id=self._init_engagement_id,
            user_id=self._init_user_id,
            raw_data=self._init_raw_data,
            metadata=self._init_metadata,
            fingerprint=self.fingerprint.uuid_str,
            shared_memory=self.shared_memory
        )
        
        # Set the state
        for key, value in initialization_result.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        
        logger.info(f"✅ Discovery Flow initialized with {len(self.state.raw_data)} records")
        return {
            "status": "initialized_with_planning",
            "session_id": self.state.session_id,
            "discovery_plan": self.state.overall_plan,
            "crew_coordination": self.state.crew_coordination,
            "next_phase": "field_mapping"
        }
    
    # CORRECTED FLOW SEQUENCE: Field Mapping FIRST
    @listen(initialize_discovery_flow)
    def execute_field_mapping_crew(self, previous_result):
        """Execute Field Mapping Crew - FOUNDATION PHASE"""
        logger.info("🔍 Executing Field Mapping Crew - Foundation Phase")
        
        try:
            result = self.crew_execution_handler.execute_field_mapping_crew(
                state=self.state,
                crewai_service=self.crewai_service
            )
            
            # Update state with results
            self.state.field_mappings = result.get("field_mappings", {})
            self.state.current_phase = "field_mapping"
            self.state.crew_status["field_mapping"] = result.get("crew_status", {})
            
            # Validate success criteria
            success_criteria_met = self._validate_phase_success("field_mapping")
            self.state.phase_completion["field_mapping"] = success_criteria_met
            
            # Store shared memory reference for subsequent crews
            if hasattr(self, 'shared_memory'):
                self.state.shared_memory_reference = self.shared_memory
            
            logger.info(f"✅ Field Mapping Crew completed - Success criteria met: {success_criteria_met}")
            return {
                "status": "field_mapping_completed",
                "field_mappings": self.state.field_mappings,
                "success_criteria_met": success_criteria_met,
                "next_phase": "data_cleansing"
            }
            
        except Exception as e:
            logger.error(f"❌ Field Mapping Crew failed: {e}")
            return self.error_handler.handle_crew_error("field_mapping", e, self.state)
    
    @listen(execute_field_mapping_crew)
    def execute_data_cleansing_crew(self, previous_result):
        """Execute Data Cleansing Crew - QUALITY ASSURANCE PHASE"""
        logger.info("🧹 Executing Data Cleansing Crew - Quality Assurance Phase")
        
        try:
            result = self.crew_execution_handler.execute_data_cleansing_crew(
                state=self.state
            )
            
            # Update state with validation
            result = self._update_crew_with_validation("data_cleansing", result)
            
            logger.info(f"✅ Data Cleansing Crew completed - Success criteria met: {result.get('success_criteria_met', False)}")
            return {
                "status": "data_cleansing_completed", 
                "data_quality_score": self.state.data_quality_metrics.get("overall_score", 0),
                "success_criteria_met": result.get("success_criteria_met", False),
                "next_phase": "inventory_building"
            }
            
        except Exception as e:
            logger.error(f"❌ Data Cleansing Crew failed: {e}")
            return self.error_handler.handle_crew_error("data_cleansing", e, self.state)
    
    @listen(execute_data_cleansing_crew)
    def execute_inventory_building_crew(self, previous_result):
        """Execute Inventory Building Crew - MULTI-DOMAIN CLASSIFICATION"""
        logger.info("📋 Executing Inventory Building Crew - Multi-Domain Classification")
        
        try:
            result = self.crew_execution_handler.execute_inventory_building_crew(
                state=self.state
            )
            
            # Update state with results
            self.state.asset_inventory = result.get("asset_inventory", {})
            self.state.current_phase = "inventory_building"
            self.state.crew_status["inventory_building"] = result.get("crew_status", {})
            
            logger.info("✅ Inventory Building Crew completed successfully")
            return {
                "status": "inventory_building_completed",
                "asset_inventory": self.state.asset_inventory,
                "next_phase": "app_server_dependencies"
            }
            
        except Exception as e:
            logger.error(f"❌ Inventory Building Crew failed: {e}")
            return self.error_handler.handle_crew_error("inventory_building", e, self.state)
    
    @listen(execute_inventory_building_crew)
    def execute_app_server_dependency_crew(self, previous_result):
        """Execute App-Server Dependency Crew - HOSTING RELATIONSHIP MAPPING"""
        logger.info("🔗 Executing App-Server Dependency Crew - Hosting Relationships")
        
        try:
            result = self.crew_execution_handler.execute_app_server_dependency_crew(
                state=self.state
            )
            
            # Update state with results
            self.state.app_server_dependencies = result.get("app_server_dependencies", {})
            self.state.current_phase = "app_server_dependencies"
            self.state.crew_status["app_server_dependencies"] = result.get("crew_status", {})
            
            logger.info("✅ App-Server Dependency Crew completed successfully")
            return {
                "status": "app_server_dependencies_completed",
                "dependencies": self.state.app_server_dependencies,
                "next_phase": "app_app_dependencies"
            }
            
        except Exception as e:
            logger.error(f"❌ App-Server Dependency Crew failed: {e}")
            return self.error_handler.handle_crew_error("app_server_dependencies", e, self.state)
    
    @listen(execute_app_server_dependency_crew)
    def execute_app_app_dependency_crew(self, previous_result):
        """Execute App-App Dependency Crew - INTEGRATION DEPENDENCY ANALYSIS"""
        logger.info("🔄 Executing App-App Dependency Crew - Integration Analysis")
        
        try:
            result = self.crew_execution_handler.execute_app_app_dependency_crew(
                state=self.state
            )
            
            # Update state with results
            self.state.app_app_dependencies = result.get("app_app_dependencies", {})
            self.state.current_phase = "app_app_dependencies"
            self.state.crew_status["app_app_dependencies"] = result.get("crew_status", {})
            
            logger.info("✅ App-App Dependency Crew completed successfully")
            return {
                "status": "app_app_dependencies_completed",
                "dependencies": self.state.app_app_dependencies,
                "next_phase": "technical_debt"
            }
            
        except Exception as e:
            logger.error(f"❌ App-App Dependency Crew failed: {e}")
            return self.error_handler.handle_crew_error("app_app_dependencies", e, self.state)
    
    @listen(execute_app_app_dependency_crew)
    def execute_technical_debt_crew(self, previous_result):
        """Execute Technical Debt Crew - 6R STRATEGY PREPARATION"""
        logger.info("⚡ Executing Technical Debt Crew - 6R Strategy Preparation")
        
        try:
            result = self.crew_execution_handler.execute_technical_debt_crew(
                state=self.state
            )
            
            # Update state with results
            self.state.technical_debt_assessment = result.get("technical_debt_assessment", {})
            self.state.current_phase = "technical_debt"
            self.state.crew_status["technical_debt"] = result.get("crew_status", {})
            
            logger.info("✅ Technical Debt Crew completed successfully")
            return {
                "status": "technical_debt_completed",
                "assessment": self.state.technical_debt_assessment,
                "next_phase": "discovery_integration"
            }
            
        except Exception as e:
            logger.error(f"❌ Technical Debt Crew failed: {e}")
            return self.error_handler.handle_crew_error("technical_debt", e, self.state)
    
    @listen(execute_technical_debt_crew)
    def execute_discovery_integration(self, previous_result):
        """Final Discovery Integration - ASSESSMENT FLOW PREPARATION"""
        logger.info("🎯 Executing Discovery Integration - Assessment Flow Preparation")
        
        try:
            result = self.crew_execution_handler.execute_discovery_integration(
                state=self.state
            )
            
            # Update state with final results
            self.state.discovery_summary = result.get("discovery_summary", {})
            self.state.assessment_flow_package = result.get("assessment_flow_package", {})
            self.state.completed_at = datetime.utcnow().isoformat()
            self.state.current_phase = "completed"
            
            logger.info("✅ Discovery Flow completed successfully - Ready for Assessment Flow")
            return {
                "status": "discovery_completed",
                "discovery_summary": self.state.discovery_summary,
                "assessment_flow_package": self.state.assessment_flow_package,
                "ready_for_6r_analysis": True
            }
            
        except Exception as e:
            logger.error(f"❌ Discovery Integration failed: {e}")
            return self.error_handler.handle_crew_error("discovery_integration", e, self.state)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get comprehensive flow status"""
        return self.status_handler.get_current_status(self.state, self.knowledge_bases)
    
    def get_callback_metrics(self) -> Dict[str, Any]:
        """Get comprehensive callback and monitoring metrics"""
        return self.callback_handler.get_callback_metrics()
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current database session status"""
        return self.session_handler.get_session_status()
    
    async def cleanup_all_sessions(self):
        """Clean up all database sessions"""
        await self.session_handler.cleanup_all_sessions()
    
    async def execute_with_session(self, crew_name: str, operation):
        """Execute crew operation with proper session management"""
        return await self.session_handler.execute_with_session(crew_name, operation)

    def _validate_phase_success(self, phase_name: str) -> bool:
        """Validate success criteria for a specific phase"""
        try:
            criteria = self.state.success_criteria.get(phase_name, {})
            
            if phase_name == "field_mapping":
                mappings = self.state.field_mappings.get("mappings", {})
                confidence_scores = self.state.field_mappings.get("confidence_scores", {})
                unmapped_fields = self.state.field_mappings.get("unmapped_fields", [])
                
                # Check confidence threshold
                avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
                confidence_met = avg_confidence >= criteria.get("field_mappings_confidence", 0.8)
                
                # Check unmapped fields threshold
                total_fields = len(mappings) + len(unmapped_fields)
                unmapped_ratio = len(unmapped_fields) / total_fields if total_fields > 0 else 0
                unmapped_met = unmapped_ratio <= criteria.get("unmapped_fields_threshold", 0.1)
                
                validation_passed = self.state.field_mappings.get("validation_results", {}).get("valid", False)
                
                return confidence_met and unmapped_met and validation_passed
                
            elif phase_name == "data_cleansing":
                quality_score = self.state.data_quality_metrics.get("overall_score", 0)
                standardization = self.state.data_quality_metrics.get("standardization_complete", False)
                validation = self.state.data_quality_metrics.get("validation_passed", False)
                
                score_met = quality_score >= criteria.get("data_quality_score", 0.85)
                return score_met and standardization and validation
                
            elif phase_name == "inventory_building":
                metadata = self.state.asset_inventory.get("classification_metadata", {})
                total_classified = metadata.get("total_classified", 0)
                classification_complete = total_classified > 0
                
                # Check if we have assets in multiple domains
                servers = len(self.state.asset_inventory.get("servers", []))
                apps = len(self.state.asset_inventory.get("applications", []))
                devices = len(self.state.asset_inventory.get("devices", []))
                cross_domain = (servers > 0) + (apps > 0) + (devices > 0) >= 2
                
                return classification_complete and cross_domain
                
            elif phase_name == "app_server_dependencies":
                relationships = self.state.app_server_dependencies.get("hosting_relationships", [])
                topology = self.state.app_server_dependencies.get("topology_insights", {})
                
                relationships_mapped = len(relationships) > 0
                topology_validated = topology.get("total_relationships", 0) >= 0
                
                return relationships_mapped and topology_validated
                
            elif phase_name == "app_app_dependencies":
                patterns = self.state.app_app_dependencies.get("communication_patterns", [])
                api_deps = self.state.app_app_dependencies.get("api_dependencies", [])
                complexity = self.state.app_app_dependencies.get("integration_complexity", {})
                
                patterns_mapped = len(patterns) >= 0  # Can be empty for simple environments
                api_identified = len(api_deps) >= 0   # Can be empty for simple environments
                analysis_complete = "total_integrations" in complexity
                
                return patterns_mapped and api_identified and analysis_complete
                
            elif phase_name == "technical_debt":
                debt_scores = self.state.technical_debt_assessment.get("debt_scores", {})
                recommendations = self.state.technical_debt_assessment.get("modernization_recommendations", [])
                six_r_prep = self.state.technical_debt_assessment.get("six_r_preparation", {})
                
                assessment_complete = "overall" in debt_scores
                recommendations_ready = len(recommendations) > 0
                six_r_ready = six_r_prep.get("ready", False)
                
                return assessment_complete and recommendations_ready and six_r_ready
                
            return False
            
        except Exception as e:
            logger.error(f"Error validating success criteria for {phase_name}: {e}")
            return False

    def _update_crew_with_validation(self, phase_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Update crew result with success criteria validation"""
        try:
            # Update state based on result
            if phase_name == "data_cleansing":
                self.state.cleaned_data = result.get("cleaned_data", [])
                self.state.data_quality_metrics = result.get("data_quality_metrics", {})
            elif phase_name == "inventory_building":
                self.state.asset_inventory = result.get("asset_inventory", {})
            elif phase_name == "app_server_dependencies":
                self.state.app_server_dependencies = result.get("app_server_dependencies", {})
            elif phase_name == "app_app_dependencies":
                self.state.app_app_dependencies = result.get("app_app_dependencies", {})
            elif phase_name == "technical_debt":
                self.state.technical_debt_assessment = result.get("technical_debt_assessment", {})
            
            # Update tracking
            self.state.current_phase = phase_name
            self.state.crew_status[phase_name] = result.get("crew_status", {})
            
            # Validate success criteria
            success_criteria_met = self._validate_phase_success(phase_name)
            self.state.phase_completion[phase_name] = success_criteria_met
            
            # Store shared memory reference
            if hasattr(self, 'shared_memory'):
                self.state.shared_memory_reference = self.shared_memory
            
            # Update result with validation
            result["success_criteria_met"] = success_criteria_met
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating crew result for {phase_name}: {e}")
            return result 