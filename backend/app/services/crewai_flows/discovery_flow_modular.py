"""
Modular Discovery Flow - Enhanced for Platform Requirements
Multi-tenant aware, agentic-first discovery with proper delegation control
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DiscoveryFlowModular:
    """
    Modular Discovery Flow Service - Enhanced Enterprise Multi-Tenant
    
    Sequential Discovery Process:
    1. Field Mapping Crew (Enhanced with AI intelligence)
    2. Data Cleansing Crew (based on field mappings)
    3. Inventory Building Crew (classification into servers/apps/devices)
    4. App-Server Dependencies Crew (hosting relationships)
    5. App-App Dependencies Crew (integration relationships)
    6. Technical Debt Crew (modernization assessment)
    """
    
    def __init__(self, crewai_service):
        self.crewai_service = crewai_service
        
        # Import handlers conditionally to avoid circular imports
        self.learning_handler = None
        self.planning_handler = None
        self.execution_handler = None
        self.collaboration_handler = None
        
        # Field Mapping Crew instance
        self.field_mapping_crew = None
        
        # Component status
        self.components_initialized = False
        
        logger.info("🏗️ Modular Discovery Flow service initialized")
    
    def _initialize_handlers(self):
        """Initialize handler instances"""
        if self.components_initialized:
            return
        
        try:
            # Import handlers
            from app.services.crewai_flows.handlers.learning_management_handler import LearningManagementHandler
            from app.services.crewai_flows.handlers.planning_coordination_handler import PlanningCoordinationHandler
            from app.services.crewai_flows.handlers.flow_execution_handler import FlowExecutionHandler
            from app.services.crewai_flows.handlers.collaboration_tracking_handler import CollaborationTrackingHandler
            
            # Initialize handlers
            self.learning_handler = LearningManagementHandler(self.crewai_service)
            self.planning_handler = PlanningCoordinationHandler(self.crewai_service)
            self.execution_handler = FlowExecutionHandler(self.crewai_service)
            self.collaboration_handler = CollaborationTrackingHandler(self.crewai_service)
            
            # Import Field Mapping Crew
            from app.services.crewai_flows.crews.field_mapping_crew import FieldMappingCrew
            self.field_mapping_crew = FieldMappingCrew(self.crewai_service)
            
            self.components_initialized = True
            logger.info("✅ All modular handlers initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize handlers: {e}")
            raise
    
    async def execute_discovery_flow(self, data: List[Dict[str, Any]], context: Any) -> Dict[str, Any]:
        """Execute complete discovery flow with modular architecture"""
        try:
            logger.info(f"🚀 Starting Modular Discovery Flow - Records: {len(data)}")
            
            # Initialize handlers
            self._initialize_handlers()
            
            # Initialize flow components
            await self._initialize_flow_components(context)
            
            # Setup multi-tenant context
            client_account_id = getattr(context, 'client_account_id', '')
            engagement_id = getattr(context, 'engagement_id', '')
            session_id = getattr(context, 'session_id', '')
            user_id = getattr(context, 'user_id', '')
            
            # Initialize proper flow state management
            from app.services.crewai_flows.discovery_flow_state_manager import flow_state_manager
            
            flow_state = await flow_state_manager.initialize_flow_state(
                session_id=session_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                raw_data=data
            )
            
            # Update context with flow state data
            context.flow_state = flow_state
            context.current_phase = flow_state["current_phase"]
            context.phase_completion = flow_state["phase_completion"]
            context.crew_status = flow_state["crew_status"]
            
            # Step 1: Field Mapping Crew (Enhanced)
            field_mapping_result = await self._execute_field_mapping_crew(data, context)
            if field_mapping_result.get("status") == "clarification_needed":
                return field_mapping_result
            
            # Update flow state after field mapping
            flow_state = await flow_state_manager.update_phase_completion(
                session_id, "field_mapping", field_mapping_result
            )
            context.field_mappings = flow_state["field_mappings"]
            
            # Step 2: Data Cleansing Crew
            data_cleansing_result = self.execution_handler.execute_data_cleansing_crew(
                field_mappings=context.field_mappings,
                raw_data=flow_state["raw_data"],
                context=context
            )
            
            # Update flow state after data cleansing
            flow_state = await flow_state_manager.update_phase_completion(
                session_id, "data_cleansing", data_cleansing_result
            )
            context.cleaned_data = flow_state["cleaned_data"]
            
            # Step 3: Inventory Building Crew
            inventory_result = self.execution_handler.execute_inventory_building_crew(
                cleaned_data=context.cleaned_data,
                field_mappings=context.field_mappings,
                context=context
            )
            
            # Update flow state after inventory building
            flow_state = await flow_state_manager.update_phase_completion(
                session_id, "inventory_building", inventory_result
            )
            context.asset_inventory = flow_state["asset_inventory"]
            
            # Persist assets to database after inventory building
            database_result = await flow_state_manager.persist_assets_to_database(session_id)
            logger.info(f"✅ Database persistence: {database_result}")
            
            # Step 4: App-Server Dependencies Crew
            app_server_result = self.execution_handler.execute_app_server_dependency_crew(
                asset_inventory=context.asset_inventory,
                context=context
            )
            
            # Update flow state after app-server dependencies
            flow_state = await flow_state_manager.update_phase_completion(
                session_id, "app_server_dependencies", app_server_result
            )
            context.app_server_dependencies = flow_state["app_server_dependencies"]
            
            # Step 5: App-App Dependencies Crew
            app_app_result = self.execution_handler.execute_app_app_dependency_crew(
                asset_inventory=context.asset_inventory,
                app_server_dependencies=context.app_server_dependencies,
                context=context
            )
            
            # Update flow state after app-app dependencies
            flow_state = await flow_state_manager.update_phase_completion(
                session_id, "app_app_dependencies", app_app_result
            )
            context.app_app_dependencies = flow_state["app_app_dependencies"]
            
            # Step 6: Technical Debt Crew
            technical_debt_result = self.execution_handler.execute_technical_debt_crew(
                asset_inventory=context.asset_inventory,
                dependencies={
                    "app_server": context.app_server_dependencies,
                    "app_app": context.app_app_dependencies
                },
                context=context
            )
            
            # Update flow state after technical debt
            flow_state = await flow_state_manager.update_phase_completion(
                session_id, "technical_debt", technical_debt_result
            )
            
            # Step 7: Discovery Integration
            integration_result = self.execution_handler.execute_discovery_integration(context)
            
            # Store learning insights from the complete flow
            await self._store_flow_learning_insights(context)
            
            # Generate comprehensive flow report
            flow_report = await self._generate_flow_completion_report(context, integration_result)
            
            logger.info("✅ Modular Discovery Flow completed successfully")
            
            return {
                "status": "discovery_completed",
                "integration_result": integration_result,
                "flow_report": flow_report,
                "phase_completion": context.phase_completion,
                "crew_status": context.crew_status
            }
            
        except Exception as e:
            logger.error(f"❌ Modular Discovery Flow failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _initialize_flow_components(self, context: Any):
        """Initialize all flow components"""
        if not self.learning_handler:
            return
        
        try:
            # Setup learning components
            client_account_id = getattr(context, 'client_account_id', '')
            engagement_id = getattr(context, 'engagement_id', '')
            
            metadata = {
                "session_id": getattr(context, 'session_id', ''),
                "client_account_id": client_account_id,
                "engagement_id": engagement_id
            }
            
            # Initialize components
            self.learning_handler.setup_learning_components(client_account_id, engagement_id, metadata)
            self.planning_handler.setup_planning_components()
            self.collaboration_handler.setup_collaboration_components()
            
            logger.info("✅ All flow components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize flow components: {e}")
            # Don't raise - continue with reduced functionality
    
    async def _execute_field_mapping_crew(self, data: List[Dict[str, Any]], context: Any) -> Dict[str, Any]:
        """Execute Field Mapping Crew with enhanced intelligence"""
        try:
            logger.info("🗂️ Starting Enhanced Field Mapping Crew execution...")
            
            # Track collaboration if available
            collab_event_id = ""
            if self.collaboration_handler:
                collab_event_id = self.collaboration_handler.track_crew_collaboration(
                    crew_name="field_mapping",
                    collaboration_type="intra_crew",
                    participants=["CMDB Field Mapping Coordination Manager", "CMDB Schema Structure Analysis Expert", 
                               "IT Asset Attribute Mapping Specialist", "Enterprise Knowledge Management Coordinator"]
                )
            
            # Execute field mapping crew
            result = await self.field_mapping_crew.execute_crew(data, context)
            
            # End collaboration tracking
            if self.collaboration_handler and collab_event_id:
                self.collaboration_handler.end_collaboration_event(
                    collab_event_id, 
                    {"status": "completed", "result_status": result.get("status")}
                )
            
            # Validate and update with success criteria
            updated_result = self.execution_handler.update_crew_with_validation("field_mapping", result, context)
            
            # Store learning insights
            if result.get("status") == "field_mapping_completed":
                confidence_score = self._calculate_field_mapping_confidence(result.get("field_mappings", {}))
                await self._store_field_mapping_insights(result.get("field_mappings", {}), confidence_score, context)
            
            logger.info(f"✅ Enhanced Field Mapping Crew completed - Status: {result.get('status')}")
            return updated_result
            
        except Exception as e:
            logger.error(f"❌ Enhanced Field Mapping Crew failed: {e}")
            return {"status": "field_mapping_failed", "error": str(e)}
    
    async def _store_field_mapping_insights(self, field_mappings: Dict[str, Any], 
                                          confidence_score: float, context: Any):
        """Store field mapping insights for learning"""
        if not self.learning_handler:
            return
        
        try:
            insight_data = {
                "mapping_patterns": field_mappings.get("mappings", {}),
                "confidence_scores": field_mappings.get("confidence_scores", {}),
                "unmapped_fields": field_mappings.get("unmapped_fields", []),
                "semantic_analysis": field_mappings.get("semantic_analysis", {}),
                "validation_results": field_mappings.get("validation_results", {})
            }
            
            client_account_id = getattr(context, 'client_account_id', '')
            engagement_id = getattr(context, 'engagement_id', '')
            
            stored = self.learning_handler.store_learning_insight(
                data_category="field_mapping_patterns",
                insight_data=insight_data,
                confidence_score=confidence_score,
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
            
            if stored:
                logger.info(f"📚 Field mapping insights stored - Confidence: {confidence_score:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to store field mapping insights: {e}")
    
    async def _store_flow_learning_insights(self, context: Any):
        """Store comprehensive learning insights from the complete flow"""
        if not self.learning_handler:
            return
        
        try:
            # Collect insights from all completed phases
            flow_insights = {
                "field_mapping_quality": self._calculate_field_mapping_confidence(getattr(context, 'field_mappings', {})),
                "data_quality_improvement": getattr(context, 'data_quality_metrics', {}).get("overall_score", 0.0),
                "asset_classification_success": self._calculate_classification_success(getattr(context, 'asset_inventory', {})),
                "dependency_discovery_completeness": self._calculate_dependency_completeness(context),
                "technical_debt_assessment_depth": self._calculate_assessment_depth(getattr(context, 'technical_debt_assessment', {})),
                "overall_flow_effectiveness": self._calculate_overall_effectiveness(context)
            }
            
            client_account_id = getattr(context, 'client_account_id', '')
            engagement_id = getattr(context, 'engagement_id', '')
            
            # Store comprehensive flow learning
            stored = self.learning_handler.store_learning_insight(
                data_category="discovery_flow_patterns",
                insight_data=flow_insights,
                confidence_score=flow_insights["overall_flow_effectiveness"],
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
            
            if stored:
                logger.info(f"🎓 Discovery flow learning insights stored - Effectiveness: {flow_insights['overall_flow_effectiveness']:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to store flow learning insights: {e}")
    
    async def _generate_flow_completion_report(self, context: Any, integration_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive flow completion report"""
        try:
            # Get collaboration metrics
            collaboration_metrics = {}
            if self.collaboration_handler:
                collaboration_metrics = self.collaboration_handler.get_collaboration_metrics()
            
            # Get learning effectiveness
            learning_metrics = {}
            if self.learning_handler:
                learning_metrics = self.learning_handler.get_learning_effectiveness_metrics(
                    client_account_id=getattr(context, 'client_account_id', ''),
                    engagement_id=getattr(context, 'engagement_id', '')
                )
            
            # Get memory analytics
            memory_analytics = {}
            if self.learning_handler:
                memory_analytics = self.learning_handler.get_memory_analytics_report(
                    report_type="summary",
                    session_id=getattr(context, 'session_id', ''),
                    engagement_id=getattr(context, 'engagement_id', ''),
                    current_phase="discovery_integration",
                    phase_completion=getattr(context, 'phase_completion', {})
                )
            
            flow_report = {
                "flow_execution": {
                    "total_phases": 6,
                    "completed_phases": sum(1 for completed in getattr(context, 'phase_completion', {}).values() if completed),
                    "success_rate": self._calculate_overall_effectiveness(context),
                    "execution_timestamp": datetime.utcnow().isoformat()
                },
                "performance_metrics": {
                    "field_mapping_confidence": self._calculate_field_mapping_confidence(getattr(context, 'field_mappings', {})),
                    "data_quality_score": getattr(context, 'data_quality_metrics', {}).get("overall_score", 0.0),
                    "asset_classification_success": self._calculate_classification_success(getattr(context, 'asset_inventory', {})),
                    "dependency_completeness": self._calculate_dependency_completeness(context),
                    "technical_debt_coverage": self._calculate_assessment_depth(getattr(context, 'technical_debt_assessment', {}))
                },
                "collaboration_effectiveness": collaboration_metrics,
                "learning_analytics": learning_metrics,
                "memory_performance": memory_analytics,
                "integration_results": integration_result,
                "recommendations": self._generate_improvement_recommendations(context)
            }
            
            return flow_report
            
        except Exception as e:
            logger.error(f"Failed to generate flow completion report: {e}")
            return {"error": str(e), "report_generated": False}
    
    def _calculate_field_mapping_confidence(self, field_mappings: Dict[str, Any]) -> float:
        """Calculate average confidence for field mappings"""
        try:
            confidence_scores = field_mappings.get("confidence_scores", {})
            if not confidence_scores:
                return 0.0
            return sum(confidence_scores.values()) / len(confidence_scores)
        except Exception:
            return 0.0
    
    def _calculate_classification_success(self, asset_inventory: Dict[str, Any]) -> float:
        """Calculate asset classification success rate"""
        try:
            servers = len(asset_inventory.get("servers", []))
            apps = len(asset_inventory.get("applications", []))
            devices = len(asset_inventory.get("devices", []))
            total = servers + apps + devices
            
            if total == 0:
                return 0.0
            
            # Success is having assets in multiple categories
            categories_with_assets = sum(1 for count in [servers, apps, devices] if count > 0)
            return min(categories_with_assets / 3.0, 1.0)
        except Exception:
            return 0.0
    
    def _calculate_dependency_completeness(self, context: Any) -> float:
        """Calculate dependency discovery completeness"""
        try:
            app_server_deps = len(getattr(context, 'app_server_dependencies', {}).get("hosting_relationships", []))
            app_app_deps = len(getattr(context, 'app_app_dependencies', {}).get("communication_patterns", []))
            
            # Base completeness on presence of both types of dependencies
            has_app_server = app_server_deps > 0
            has_app_app = app_app_deps >= 0
            
            return (has_app_server + has_app_app) / 2.0
        except Exception:
            return 0.0
    
    def _calculate_assessment_depth(self, technical_debt_assessment: Dict[str, Any]) -> float:
        """Calculate technical debt assessment depth"""
        try:
            debt_scores = technical_debt_assessment.get("debt_scores", {})
            recommendations = technical_debt_assessment.get("modernization_recommendations", [])
            six_r_prep = technical_debt_assessment.get("six_r_preparation", {})
            
            has_debt_analysis = len(debt_scores) > 0
            has_recommendations = len(recommendations) > 0
            has_six_r = six_r_prep.get("ready", False)
            
            return (has_debt_analysis + has_recommendations + has_six_r) / 3.0
        except Exception:
            return 0.0
    
    def _calculate_overall_effectiveness(self, context: Any) -> float:
        """Calculate overall flow effectiveness"""
        try:
            phase_completion = getattr(context, 'phase_completion', {})
            completed_phases = sum(1 for completed in phase_completion.values() if completed)
            total_phases = 6
            
            return completed_phases / total_phases
        except Exception:
            return 0.0
    
    def _generate_improvement_recommendations(self, context: Any) -> List[Dict[str, Any]]:
        """Generate improvement recommendations based on flow results"""
        recommendations = []
        
        try:
            # Check field mapping quality
            field_mapping_confidence = self._calculate_field_mapping_confidence(getattr(context, 'field_mappings', {}))
            if field_mapping_confidence < 0.8:
                recommendations.append({
                    "area": "field_mapping",
                    "recommendation": "Improve field mapping confidence through enhanced semantic analysis",
                    "priority": "high",
                    "current_score": field_mapping_confidence
                })
            
            # Check data quality
            data_quality = getattr(context, 'data_quality_metrics', {}).get("overall_score", 0.0)
            if data_quality < 0.85:
                recommendations.append({
                    "area": "data_quality",
                    "recommendation": "Enhance data cleansing and validation procedures",
                    "priority": "medium",
                    "current_score": data_quality
                })
            
            # Check asset classification
            classification_success = self._calculate_classification_success(getattr(context, 'asset_inventory', {}))
            if classification_success < 0.7:
                recommendations.append({
                    "area": "asset_classification",
                    "recommendation": "Improve asset classification rules and patterns",
                    "priority": "medium",
                    "current_score": classification_success
                })
            
            # Check dependency discovery
            dependency_completeness = self._calculate_dependency_completeness(context)
            if dependency_completeness < 0.6:
                recommendations.append({
                    "area": "dependency_discovery",
                    "recommendation": "Enhance dependency analysis and relationship mapping",
                    "priority": "medium",
                    "current_score": dependency_completeness
                })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    # Public API methods for external access
    
    async def get_flow_status(self, session_id: str) -> Dict[str, Any]:
        """Get current flow execution status"""
        try:
            return {
                "session_id": session_id,
                "status": "running",
                "current_phase": "field_mapping",
                "phase_completion": {},
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get flow status: {e}")
            return {"error": str(e)}
    
    async def process_user_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback for learning improvement"""
        if self.learning_handler:
            return self.learning_handler.process_user_feedback(feedback_data)
        return {"processed": False, "reason": "learning_handler_unavailable"}
    
    async def get_learning_analytics(self, client_account_id: str = "", engagement_id: str = "") -> Dict[str, Any]:
        """Get learning analytics for the discovery flow"""
        if self.learning_handler:
            return self.learning_handler.get_learning_effectiveness_metrics(client_account_id, engagement_id)
        return {"available": False, "reason": "learning_handler_unavailable"}
    
    async def get_collaboration_report(self) -> Dict[str, Any]:
        """Get collaboration effectiveness report"""
        if self.collaboration_handler:
            return self.collaboration_handler.get_collaboration_effectiveness_report()
        return {"available": False, "reason": "collaboration_handler_unavailable"}
    
    async def optimize_flow_performance(self) -> Dict[str, Any]:
        """Optimize flow performance using AI intelligence"""
        try:
            optimization_result = {
                "optimized": True,
                "performance_improvement": "estimated",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Memory optimization
            if self.learning_handler:
                memory_optimization = self.learning_handler.optimize_memory_performance()
                optimization_result["memory_optimization"] = memory_optimization
            
            # Collaboration cleanup
            if self.collaboration_handler:
                collaboration_cleanup = self.collaboration_handler.cleanup_collaboration_tracking()
                optimization_result["collaboration_cleanup"] = collaboration_cleanup
            
            logger.info("🚀 Flow performance optimization completed")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Failed to optimize flow performance: {e}")
            return {"optimized": False, "error": str(e)} 