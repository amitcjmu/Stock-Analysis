"""
Field Mapping Phase

Handles the attribute/field mapping phase of the discovery flow.
Now uses FieldMappingDecisionAgent for intelligent decision-making instead of hardcoded rules.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Decision agent for intelligent field mapping decisions
from app.services.crewai_flows.agents.decision_agents import FieldMappingDecisionAgent, PhaseAction
from app.services.agent_ui_bridge import agent_ui_bridge
from ..flow_config import PhaseNames

logger = logging.getLogger(__name__)


class FieldMappingPhase:
    """Handles field mapping phase execution with intelligent agent-based decisions"""
    
    def __init__(self, state, crew_manager, init_context: Dict[str, Any], flow_bridge=None):
        """
        Initialize field mapping phase
        
        Args:
            state: The flow state object
            crew_manager: The UnifiedFlowCrewManager instance for real CrewAI execution
            init_context: Initial context for agent execution
            flow_bridge: Optional flow bridge for state persistence
        """
        self.state = state
        self.crew_manager = crew_manager
        self._init_context = init_context
        self.flow_bridge = flow_bridge
        # Initialize the decision agent
        self.decision_agent = FieldMappingDecisionAgent()
    
    async def execute(self, previous_result: str) -> str:
        """
        Execute the field mapping phase
        
        Args:
            previous_result: Result from the previous phase
            
        Returns:
            Phase result status
        """
        if previous_result in ["data_validation_skipped", "data_validation_failed"]:
            logger.warning("⚠️ Proceeding with attribute mapping despite validation issues")
        
        logger.info("🤖 Starting Attribute Mapping with Agent-First Architecture")
        self.state.current_phase = PhaseNames.FIELD_MAPPING
        
        # Update database immediately when phase starts
        await self._update_flow_state()
        
        # Send real-time update
        await self._send_phase_start_update()
        
        try:
            # Prepare crew data for real CrewAI execution
            crew_data = self._prepare_crew_data()
            
            # Execute real CrewAI field mapping crew
            logger.info("🤖 Executing real CrewAI field mapping crew")
            crew = self.crew_manager.create_crew_on_demand("attribute_mapping")
            
            if not crew:
                raise RuntimeError("Failed to create field mapping crew")
            
            # Execute the crew with real CrewAI
            crew_result = crew.kickoff()
            
            # Process crew results into expected format
            mapping_result = self._process_crew_results(crew_result)
            
            # Store results in state
            self._process_mapping_results(mapping_result)
            
            # Use FieldMappingDecisionAgent to determine next steps
            decision = await self.decision_agent.analyze_phase_transition(
                current_phase="field_mapping",
                results=mapping_result,
                state=self.state
            )
            
            logger.info(f"🤖 Decision Agent recommendation: {decision.action.value} (confidence: {decision.confidence:.1%})")
            logger.info(f"📋 Reasoning: {decision.reasoning}")
            
            # Audit trail for agent decision
            await self._log_agent_decision(decision, mapping_result)
            
            # Process decision
            if decision.action == PhaseAction.PROCEED:
                # Send completion update
                await self._send_completion_update(mapping_result, decision)
                
                # Persist state with agent insights and progress
                await self._update_flow_state()
                
                logger.info(f"✅ Attribute mapping completed and approved (confidence: {mapping_result.confidence_score:.1f}%)")
                return "field_mapping_completed"
                
            elif decision.action == PhaseAction.PAUSE:
                # Need user review
                await self._send_review_needed_update(mapping_result, decision)
                
                # Store decision metadata for UI
                self.state.user_clarifications.append({
                    "phase": "field_mapping",
                    "action_required": decision.metadata.get("user_action", "review_mappings"),
                    "reason": decision.reasoning,
                    "threshold": decision.metadata.get("threshold", 0.0),
                    "current_confidence": mapping_result.confidence_score,
                    "critical_fields": decision.metadata.get("critical_fields", []),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Update state
                await self._update_flow_state()
                
                logger.info(f"⏸️ Field mapping requires user review: {decision.reasoning}")
                return "field_mapping_requires_review"
                
            elif decision.action == PhaseAction.FAIL:
                # Critical failure
                self.state.add_error("attribute_mapping", decision.reasoning)
                await self._send_error_update(decision.reasoning)
                await self._update_flow_state()
                return "attribute_mapping_failed"
                
            else:
                # Other actions (SKIP, RETRY)
                logger.info(f"📊 Handling decision action: {decision.action.value}")
                await self._update_flow_state()
                return f"field_mapping_{decision.action.value}"
            
        except Exception as e:
            logger.error(f"❌ Attribute mapping agent failed: {e}")
            self.state.add_error("attribute_mapping", f"Agent execution failed: {str(e)}")
            
            # Send error update
            await self._send_error_update(str(e))
            
            # Update database even on failure
            await self._update_flow_state()
            
            return "attribute_mapping_failed"
    
    def _prepare_crew_data(self) -> Dict[str, Any]:
        """Prepare data for CrewAI crew execution"""
        return {
            'raw_data': self.state.raw_data,
            'source_columns': list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
            'validation_results': self.state.data_validation_results,
            'flow_metadata': {
                'flow_id': self.state.flow_id,
                'client_account_id': self.state.client_account_id,
                'engagement_id': self.state.engagement_id
            }
        }
    
    def _process_crew_results(self, crew_result) -> Any:
        """Process CrewAI crew results into expected format"""
        # Convert CrewAI crew result to expected mapping result format
        class MappingResult:
            def __init__(self, crew_output):
                self.data = self._extract_mappings(crew_output)
                self.confidence_score = self._extract_confidence(crew_output)
                self.insights_generated = []
                self.clarifications_requested = []
            
            def _extract_mappings(self, output):
                """Extract field mappings from crew output"""
                # Parse the crew output for field mappings
                # This will need to match the format expected by the crew
                mappings = {}
                
                # Extract mappings from crew output
                if hasattr(output, 'raw_output'):
                    # Parse the raw output for mapping information
                    # This is a placeholder - actual implementation depends on crew output format
                    pass
                elif isinstance(output, dict):
                    mappings = output.get('mappings', {})
                
                return {"mappings": mappings}
            
            def _extract_confidence(self, output):
                """Extract confidence score from crew output"""
                if hasattr(output, 'raw_output'):
                    # Extract from raw output
                    return 0.85  # Placeholder
                elif isinstance(output, dict):
                    return output.get('confidence', 0.85)
                return 0.85
        
        return MappingResult(crew_result)
    
    def _process_mapping_results(self, mapping_result):
        """Process and store mapping results in state"""
        # Store agent results and confidence
        self.state.field_mappings = mapping_result.data.get('mappings', {})
        self.state.agent_confidences['attribute_mapping'] = mapping_result.confidence_score
        
        # Store confidence for decision agent
        self.state.field_mapping_confidence = mapping_result.confidence_score
        
        # Collect insights and clarifications
        if mapping_result.insights_generated:
            self.state.agent_insights.extend([
                insight.model_dump() for insight in mapping_result.insights_generated
            ])
        
        if mapping_result.clarifications_requested:
            self.state.user_clarifications.extend([
                req.model_dump() for req in mapping_result.clarifications_requested
            ])
        
        # Update phase completion
        self.state.phase_completion['attribute_mapping'] = True
        self.state.progress_percentage = 40.0
    
    async def _update_flow_state(self):
        """Update flow state in database"""
        if self.flow_bridge:
            try:
                await self.flow_bridge.update_flow_state(self.state)
            except Exception as e:
                logger.warning(f"⚠️ Failed to update flow state: {e}")
    
    async def _send_phase_start_update(self):
        """Send real-time update when phase starts"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="attribute_mapping_agent",
                agent_name="Attribute Mapping Agent",
                insight_type="processing",
                page=f"flow_{self.state.flow_id}",
                title="Starting Field Mapping Analysis",
                description="Analyzing source columns and determining optimal field mappings",
                supporting_data={
                    'phase': 'attribute_mapping',
                    'source_columns': list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
                    'progress_percentage': 30.0,
                    'start_time': datetime.utcnow().isoformat()
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send phase start update: {e}")
    
    async def _send_completion_update(self, mapping_result, decision):
        """Send completion update with results and decision"""
        try:
            mapped_fields = len(mapping_result.data.get('mappings', {}))
            agent_ui_bridge.add_agent_insight(
                agent_id="attribute_mapping_agent",
                agent_name="Attribute Mapping Agent",
                insight_type="success",
                page=f"flow_{self.state.flow_id}",
                title="Field Mapping Completed",
                description=f"Successfully mapped {mapped_fields} fields with {mapping_result.confidence_score:.1f}% confidence. {decision.reasoning}",
                supporting_data={
                    'phase': 'attribute_mapping',
                    'progress_percentage': 40.0,
                    'mapped_fields': mapped_fields,
                    'confidence_score': mapping_result.confidence_score,
                    'mappings': mapping_result.data,
                    'decision': decision.to_dict(),
                    'completion_time': datetime.utcnow().isoformat()
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send completion update: {e}")
    
    async def _send_review_needed_update(self, mapping_result, decision):
        """Send update when user review is needed"""
        try:
            mapped_fields = len(mapping_result.data.get('mappings', {}))
            agent_ui_bridge.add_agent_insight(
                agent_id="field_mapping_decision_agent",
                agent_name="Field Mapping Decision Agent",
                insight_type="warning",
                page=f"flow_{self.state.flow_id}",
                title="User Review Required",
                description=decision.reasoning,
                supporting_data={
                    'phase': 'attribute_mapping',
                    'mapped_fields': mapped_fields,
                    'confidence_score': mapping_result.confidence_score,
                    'required_threshold': decision.metadata.get('threshold', 0.0),
                    'critical_fields': decision.metadata.get('critical_fields', []),
                    'missing_critical': decision.metadata.get('mapping_analysis', {}).get('missing_critical_fields', []),
                    'user_action': decision.metadata.get('user_action', 'review_mappings'),
                    'decision': decision.to_dict(),
                    'timestamp': datetime.utcnow().isoformat()
                },
                confidence="medium"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send review needed update: {e}")
    
    async def _send_error_update(self, error_message: str):
        """Send error update when phase fails"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="attribute_mapping_agent",
                agent_name="Attribute Mapping Agent",
                insight_type="error",
                page=f"flow_{self.state.flow_id}",
                title="Field Mapping Failed",
                description=f"Mapping failed: {error_message}",
                supporting_data={
                    'phase': 'attribute_mapping',
                    'error_type': 'agent_execution_failure',
                    'error_message': error_message,
                    'failure_time': datetime.utcnow().isoformat()
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send error update: {e}")
    
    async def _log_agent_decision(self, decision: Any, mapping_result: Any):
        """Log agent decision to audit trail"""
        try:
            # Get flow audit logger if available
            if hasattr(self.state, 'flow_id') and self.flow_bridge:
                from app.services.flow_orchestration.audit_logger import (
                    FlowAuditLogger, AuditCategory, AuditLevel
                )
                
                # Get the crew metadata
                crew_metadata = {}
                if hasattr(self.crew_manager, 'get_audit_metadata'):
                    crew_metadata = self.crew_manager.get_audit_metadata()
                
                # Create audit event metadata
                audit_metadata = {
                    "agent": "FieldMappingDecisionAgent",
                    "current_phase": "field_mapping",
                    "recommended_action": decision.action.value,
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning,
                    "decision_metadata": decision.metadata,
                    "mapping_confidence": mapping_result.confidence_score,
                    "mapped_fields": len(mapping_result.data.get('mappings', {})),
                    "crew_info": crew_metadata,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Log via agent UI bridge for visibility
                agent_ui_bridge.add_agent_insight(
                    agent_id="field_mapping_decision_agent",
                    agent_name="Field Mapping Decision Agent",
                    insight_type="decision",
                    page=f"flow_{self.state.flow_id}",
                    title="Agent Decision Logged",
                    description=f"Decision: {decision.action.value} with {decision.confidence:.1%} confidence",
                    supporting_data={
                        "category": "AGENT_DECISION",
                        "audit_metadata": audit_metadata
                    },
                    confidence="high"
                )
                
                logger.info(f"✅ Agent decision logged to audit trail")
        except Exception as e:
            logger.warning(f"⚠️ Could not log agent decision to audit trail: {e}")