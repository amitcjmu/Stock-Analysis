"""
Phase Handlers Module

This module contains all the phase handling methods extracted from the base_flow.py
to improve maintainability and code organization.
"""

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class PhaseHandlers:
    """
    Handles all phase-specific operations for the UnifiedDiscoveryFlow
    """
    
    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        self.flow = flow_instance
        self.logger = logger
    
    async def execute_data_import_validation(self):
        """Execute the data import validation phase"""
        self.logger.info(f"🔍 [ECHO] Data validation phase triggered for flow {self.flow._flow_id}")
        
        try:
            # Update flow status and sync to state
            if hasattr(self.flow, 'flow_bridge') and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                
                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(self.flow._flow_id, "processing_data_validation")
                    self.logger.info("✅ [ECHO] Updated flow status to 'processing_data_validation'")
            
            # Load raw data into flow state if not already loaded
            if hasattr(self.flow.state, 'raw_data') and not self.flow.state.raw_data:
                await self.flow._load_raw_data_from_database(self.flow.state)
            
            # Execute data validation using the executor pattern
            validation_result = await self.flow.data_validation_phase.execute(
                state=self.flow.state,
                agents={
                    'data_validation_agent': self.flow.data_validation_agent
                },
                flow_bridge=self.flow.flow_bridge
            )
            
            # Send agent insight
            await self._send_phase_insight(
                phase="data_validation",
                title="Data Validation Completed",
                description="Data validation phase has been completed successfully",
                progress=20,
                data=validation_result
            )
            
            # Update state with validation results
            self.flow.state.validation_results = validation_result.get('validation_results', {})
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"❌ Data validation phase failed: {e}")
            await self._send_phase_error("data_validation", str(e))
            raise
    
    async def generate_field_mapping_suggestions(self, data_validation_agent_result):
        """Generate field mapping suggestions based on validation results"""
        self.logger.info(f"🗺️ [ECHO] Field mapping phase triggered for flow {self.flow._flow_id}")
        
        try:
            # Update flow status
            if hasattr(self.flow, 'flow_bridge') and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                
                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(self.flow._flow_id, "processing_field_mapping")
            
            # Execute field mapping using the executor pattern
            mapping_result = await self.flow.field_mapping_phase.execute(
                state=self.flow.state,
                agents={
                    'attribute_mapping_agent': self.flow.attribute_mapping_agent
                },
                flow_bridge=self.flow.flow_bridge,
                previous_result=data_validation_agent_result
            )
            
            # Send agent insight
            await self._send_phase_insight(
                phase="field_mapping",
                title="Field Mapping Suggestions Generated",
                description="Field mapping suggestions have been generated and are ready for review",
                progress=40,
                data=mapping_result
            )
            
            # Update state with mapping suggestions
            self.flow.state.field_mappings = mapping_result.get('field_mappings', {})
            self.flow.state.needs_approval = True
            
            return mapping_result
            
        except Exception as e:
            self.logger.error(f"❌ Field mapping phase failed: {e}")
            await self._send_phase_error("field_mapping", str(e))
            raise
    
    async def apply_approved_field_mappings(self, field_mapping_approval_result):
        """Apply approved field mappings"""
        self.logger.info(f"✅ [ECHO] Applying approved field mappings for flow {self.flow._flow_id}")
        
        try:
            # Update flow status
            if hasattr(self.flow, 'flow_bridge') and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                
                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(self.flow._flow_id, "applying_field_mappings")
            
            # Apply mappings using the state manager
            if hasattr(self.flow, 'state_manager'):
                mapping_application_result = await self.flow.state_manager.apply_field_mappings(
                    self.flow.state,
                    field_mapping_approval_result
                )
            else:
                # Fallback direct application
                mapping_application_result = {
                    'status': 'success',
                    'message': 'Field mappings applied successfully',
                    'applied_mappings': field_mapping_approval_result.get('approved_mappings', {})
                }
                
                # Update state
                if 'approved_mappings' in field_mapping_approval_result:
                    self.flow.state.applied_field_mappings = field_mapping_approval_result['approved_mappings']
            
            # Send agent insight
            await self._send_phase_insight(
                phase="mapping_application",
                title="Field Mappings Applied",
                description="Approved field mappings have been successfully applied to the data",
                progress=50,
                data=mapping_application_result
            )
            
            return mapping_application_result
            
        except Exception as e:
            self.logger.error(f"❌ Field mapping application failed: {e}")
            await self._send_phase_error("mapping_application", str(e))
            raise
    
    async def execute_data_cleansing(self, mapping_application_result):
        """Execute data cleansing phase"""
        self.logger.info(f"🧹 [ECHO] Data cleansing phase triggered for flow {self.flow._flow_id}")
        
        try:
            # Update flow status
            if hasattr(self.flow, 'flow_bridge') and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                
                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(self.flow._flow_id, "processing_data_cleansing")
            
            # Execute data cleansing using the executor pattern
            cleansing_result = await self.flow.data_cleansing_phase.execute(
                state=self.flow.state,
                agents={
                    'data_cleansing_agent': self.flow.data_cleansing_agent
                },
                flow_bridge=self.flow.flow_bridge,
                previous_result=mapping_application_result
            )
            
            # Send agent insight
            await self._send_phase_insight(
                phase="data_cleansing",
                title="Data Cleansing Completed",
                description="Data cleansing phase has been completed successfully",
                progress=70,
                data=cleansing_result
            )
            
            # Update state with cleansed data
            self.flow.state.cleansed_data = cleansing_result.get('cleansed_data', {})
            
            return cleansing_result
            
        except Exception as e:
            self.logger.error(f"❌ Data cleansing phase failed: {e}")
            await self._send_phase_error("data_cleansing", str(e))
            raise
    
    async def create_discovery_assets(self, data_cleansing_result):
        """Create discovery assets from cleansed data"""
        self.logger.info(f"📦 [ECHO] Creating discovery assets for flow {self.flow._flow_id}")
        
        try:
            # Update flow status
            if hasattr(self.flow, 'flow_bridge') and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                
                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(self.flow._flow_id, "creating_discovery_assets")
            
            # Execute asset creation using the executor pattern
            asset_creation_result = await self.flow.asset_inventory_phase.execute(
                state=self.flow.state,
                agents={
                    'asset_inventory_agent': self.flow.asset_inventory_agent
                },
                flow_bridge=self.flow.flow_bridge,
                previous_result=data_cleansing_result
            )
            
            # Send agent insight
            await self._send_phase_insight(
                phase="asset_creation",
                title="Discovery Assets Created",
                description="Discovery assets have been created from cleansed data",
                progress=80,
                data=asset_creation_result
            )
            
            # Update state with created assets
            self.flow.state.discovery_assets = asset_creation_result.get('discovery_assets', [])
            
            return asset_creation_result
            
        except Exception as e:
            self.logger.error(f"❌ Asset creation phase failed: {e}")
            await self._send_phase_error("asset_creation", str(e))
            raise
    
    async def execute_parallel_analysis(self, asset_promotion_result):
        """Execute parallel analysis phases"""
        self.logger.info(f"🔄 [ECHO] Starting parallel analysis for flow {self.flow._flow_id}")
        
        try:
            # Update flow status
            if hasattr(self.flow, 'flow_bridge') and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                
                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(self.flow._flow_id, "processing_parallel_analysis")
            
            # Execute dependency analysis and tech debt assessment in parallel
            import asyncio
            
            dependency_task = self.flow.dependency_analysis_phase.execute(
                state=self.flow.state,
                agents={
                    'dependency_analysis_agent': self.flow.dependency_analysis_agent
                },
                flow_bridge=self.flow.flow_bridge,
                previous_result=asset_promotion_result
            )
            
            tech_debt_task = self.flow.tech_debt_assessment_phase.execute(
                state=self.flow.state,
                agents={
                    'tech_debt_analysis_agent': self.flow.tech_debt_analysis_agent
                },
                flow_bridge=self.flow.flow_bridge,
                previous_result=asset_promotion_result
            )
            
            # Wait for both tasks to complete
            dependency_result, tech_debt_result = await asyncio.gather(
                dependency_task,
                tech_debt_task,
                return_exceptions=True
            )
            
            # Process results
            analysis_result = {
                'dependency_analysis': dependency_result if not isinstance(dependency_result, Exception) else {'error': str(dependency_result)},
                'tech_debt_assessment': tech_debt_result if not isinstance(tech_debt_result, Exception) else {'error': str(tech_debt_result)},
                'status': 'completed'
            }
            
            # Send agent insight
            await self._send_phase_insight(
                phase="parallel_analysis",
                title="Parallel Analysis Completed",
                description="Dependency analysis and tech debt assessment have been completed",
                progress=90,
                data=analysis_result
            )
            
            # Update state with analysis results
            self.flow.state.dependency_analysis = analysis_result['dependency_analysis']
            self.flow.state.tech_debt_assessment = analysis_result['tech_debt_assessment']
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ Parallel analysis phase failed: {e}")
            await self._send_phase_error("parallel_analysis", str(e))
            raise
    
    async def _send_phase_insight(self, phase: str, title: str, description: str, progress: int, data: Dict[str, Any]):
        """Send phase insight via agent-ui-bridge"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel
            
            insight = {
                "agent_id": f"unified_discovery_{phase}",
                "agent_name": f"Discovery {phase.replace('_', ' ').title()} Agent",
                "insight_type": "phase_completion",
                "title": title,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": phase,
                    "progress": progress,
                    "flow_id": self.flow._flow_id,
                    **data
                }
            }
            
            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.HIGH,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id
            )
            
            self.logger.info(f"📡 [ECHO] Sent {phase} phase insight via agent-ui-bridge")
            
        except Exception as e:
            self.logger.warning(f"⚠️ [ECHO] Failed to send {phase} phase insight: {e}")
    
    async def _send_phase_error(self, phase: str, error_message: str):
        """Send phase error insight via agent-ui-bridge"""
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            from app.services.models.agent_communication import ConfidenceLevel
            
            insight = {
                "agent_id": f"unified_discovery_{phase}",
                "agent_name": f"Discovery {phase.replace('_', ' ').title()} Agent",
                "insight_type": "error",
                "title": f"{phase.replace('_', ' ').title()} Phase Failed",
                "description": f"Error in {phase} phase: {error_message}",
                "timestamp": datetime.now().isoformat(),
                "supporting_data": {
                    "phase": phase,
                    "error": error_message,
                    "flow_id": self.flow._flow_id
                }
            }
            
            agent_ui_bridge.add_agent_insight(
                agent_id=insight["agent_id"],
                agent_name=insight["agent_name"],
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                confidence=ConfidenceLevel.LOW,
                supporting_data=insight["supporting_data"],
                page=f"flow_{self.flow._flow_id}",
                flow_id=self.flow._flow_id
            )
            
            self.logger.info(f"📡 [ECHO] Sent {phase} phase error via agent-ui-bridge")
            
        except Exception as e:
            self.logger.warning(f"⚠️ [ECHO] Failed to send {phase} phase error: {e}")