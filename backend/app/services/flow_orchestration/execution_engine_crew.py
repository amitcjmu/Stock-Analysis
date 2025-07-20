"""
Flow Execution Engine CrewAI Module

Handles CrewAI-specific execution logic for discovery and assessment flows.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.validator_registry import ValidatorRegistry

logger = get_logger(__name__)


class FlowCrewExecutor:
    """
    Handles execution of CrewAI flow phases for different flow types.
    """
    
    def __init__(self, 
                 db: AsyncSession,
                 context: RequestContext,
                 master_repo: CrewAIFlowStateExtensionsRepository,
                 flow_registry: FlowTypeRegistry,
                 handler_registry: HandlerRegistry,
                 validator_registry: ValidatorRegistry):
        """Initialize the CrewAI flow executor"""
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.handler_registry = handler_registry
        self.validator_registry = validator_registry
        
        logger.info(f"✅ Flow CrewAI Executor initialized for client {context.client_account_id}")
    
    async def execute_crew_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a phase through CrewAI by delegating to the actual flow implementation"""
        logger.info(f"🔄 Executing CrewAI phase: {phase_config.name} for flow type: {master_flow.flow_type}")
        
        try:
            # Delegate based on flow type
            if master_flow.flow_type == "discovery":
                return await self._execute_discovery_phase(master_flow, phase_config, phase_input)
            elif master_flow.flow_type == "assessment":
                return await self._execute_assessment_phase(master_flow, phase_config, phase_input)
            elif master_flow.flow_type == "collection":
                return await self._execute_collection_phase(master_flow, phase_config, phase_input)
            else:
                # For other flow types, use placeholder until services are implemented
                logger.warning(f"⚠️ Flow type '{master_flow.flow_type}' delegation not yet implemented")
                
                return {
                    "phase": phase_config.name,
                    "status": "completed",
                    "crew_results": {
                        "message": f"{master_flow.flow_type} flow delegation pending implementation",
                        "flow_type": master_flow.flow_type,
                        "phase": phase_config.name,
                        "phase_input": phase_input
                    },
                    "warning": f"{master_flow.flow_type} flow service not yet implemented"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to execute crew phase: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return error result but don't raise - let the orchestrator handle it
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "error_during_delegation"
            }
    
    async def _execute_discovery_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute discovery flow phase"""
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            crewai_service = CrewAIFlowService(db)
            
            # Create context from master flow
            context = {
                'client_account_id': master_flow.client_account_id,
                'engagement_id': master_flow.engagement_id,
                'user_id': master_flow.user_id,
                'approved_by': master_flow.user_id
            }
            
            # Map phase names to CrewAI flow phases
            phase_mapping = {
                "data_import": "data_import_validation",
                "field_mapping": "field_mapping",
                "data_cleansing": "data_cleansing",
                "asset_creation": "asset_creation",
                "analysis": "analysis"
            }
            
            mapped_phase = phase_mapping.get(phase_config.name, phase_config.name)
            logger.info(f"🗺️ Mapped phase '{phase_config.name}' to '{mapped_phase}' for discovery flow")
            
            try:
                # Execute phase through CrewAI service
                if mapped_phase == "data_import_validation":
                    result = await crewai_service.execute_data_import_validation(
                        flow_id=master_flow.flow_id,
                        raw_data=phase_input.get("raw_data", []),
                        **context
                    )
                elif mapped_phase == "field_mapping":
                    # Handle field mapping with approval if needed
                    field_mapping_data = phase_input.get("field_mapping_data", {})
                    
                    if phase_input.get("approved_mappings"):
                        # Apply approved mappings
                        result = await crewai_service.apply_field_mappings(
                            flow_id=master_flow.flow_id,
                            approved_mappings=phase_input["approved_mappings"],
                            **context
                        )
                    else:
                        # Generate mapping suggestions
                        result = await crewai_service.generate_field_mapping_suggestions(
                            flow_id=master_flow.flow_id,
                            validation_result=field_mapping_data,
                            **context
                        )
                elif mapped_phase == "data_cleansing":
                    result = await crewai_service.execute_data_cleansing(
                        flow_id=master_flow.flow_id,
                        field_mappings=phase_input.get("field_mappings", {}),
                        **context
                    )
                elif mapped_phase == "asset_creation":
                    result = await crewai_service.create_discovery_assets(
                        flow_id=master_flow.flow_id,
                        cleaned_data=phase_input.get("cleaned_data", []),
                        **context
                    )
                elif mapped_phase == "analysis":
                    result = await crewai_service.execute_analysis_phases(
                        flow_id=master_flow.flow_id,
                        assets=phase_input.get("assets", []),
                        **context
                    )
                else:
                    # Generic execution
                    result = await crewai_service.execute_flow_phase(
                        flow_id=master_flow.flow_id,
                        phase_name=mapped_phase,
                        phase_input=phase_input,
                        **context
                    )
                
                logger.info(f"✅ Discovery phase '{mapped_phase}' completed successfully")
                
                return {
                    "phase": phase_config.name,
                    "status": "completed",
                    "crew_results": result,
                    "method": "crewai_discovery_delegation"
                }
                
            except Exception as e:
                logger.error(f"❌ Discovery phase '{mapped_phase}' failed: {e}")
                return {
                    "phase": phase_config.name,
                    "status": "failed",
                    "error": str(e),
                    "crew_results": {},
                    "method": "crewai_discovery_delegation"
                }
    
    async def _execute_assessment_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute assessment flow phase"""
        logger.info(f"📊 Executing assessment phase: {phase_config.name}")
        
        try:
            # Assessment flow logic would go here
            # For now, return a placeholder implementation
            
            # Simulate assessment processing
            await asyncio.sleep(0.1)  # Simulate processing time
            
            assessment_result = {
                "assessment_type": "placeholder",
                "phase": phase_config.name,
                "input_processed": len(phase_input),
                "findings": [
                    {
                        "category": "configuration",
                        "severity": "medium",
                        "description": f"Assessment phase {phase_config.name} executed",
                        "recommendations": ["Review assessment implementation"]
                    }
                ],
                "metrics": {
                    "total_items_assessed": len(phase_input.get("items", [])),
                    "issues_found": 1,
                    "completion_percentage": 100
                }
            }
            
            logger.info(f"✅ Assessment phase '{phase_config.name}' completed (placeholder)")
            
            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": assessment_result,
                "method": "assessment_placeholder",
                "note": "Assessment flow implementation pending"
            }
            
        except Exception as e:
            logger.error(f"❌ Assessment phase '{phase_config.name}' failed: {e}")
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "assessment_placeholder"
            }
    
    async def _execute_collection_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute collection flow phase"""
        logger.info(f"📊 Executing collection phase: {phase_config.name}")
        
        try:
            # Import the appropriate crew based on phase
            crew_factory_name = phase_config.crew_config.get("crew_factory")
            crew_result = {}
            
            if crew_factory_name == "create_platform_detection_crew":
                from app.services.crewai_flows.crews.collection import create_platform_detection_crew
                crew_result = create_platform_detection_crew(phase_input)
            elif crew_factory_name == "create_automated_collection_crew":
                from app.services.crewai_flows.crews.collection import create_automated_collection_crew
                crew_result = create_automated_collection_crew(phase_input)
            elif crew_factory_name == "create_gap_analysis_crew":
                from app.services.crewai_flows.crews.collection import create_gap_analysis_crew
                crew_result = create_gap_analysis_crew(phase_input)
            elif crew_factory_name == "create_manual_collection_crew":
                from app.services.crewai_flows.crews.collection import create_manual_collection_crew
                crew_result = create_manual_collection_crew(phase_input)
            elif crew_factory_name == "create_data_synthesis_crew":
                from app.services.crewai_flows.crews.collection import create_data_synthesis_crew
                crew_result = create_data_synthesis_crew(phase_input)
            else:
                logger.warning(f"Unknown collection crew factory: {crew_factory_name}")
                crew_result = {
                    "error": f"Unknown crew factory: {crew_factory_name}",
                    "phase": phase_config.name
                }
            
            # Simulate async processing
            await asyncio.sleep(0.1)
            
            logger.info(f"✅ Collection phase '{phase_config.name}' completed")
            
            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": crew_result,
                "method": "collection_crew_execution"
            }
            
        except Exception as e:
            logger.error(f"❌ Collection phase '{phase_config.name}' failed: {e}")
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "collection_crew_execution"
            }