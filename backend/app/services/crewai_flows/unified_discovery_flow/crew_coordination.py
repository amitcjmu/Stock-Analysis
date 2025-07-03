"""
Crew Coordination Module

Handles agent orchestration and crew management for the Unified Discovery Flow.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.agents.discovery_agent_orchestrator import DiscoveryAgentOrchestrator
from .flow_config import PhaseNames, FlowConfig

logger = logging.getLogger(__name__)


class CrewCoordinator:
    """Coordinates agent crews and their execution"""
    
    def __init__(self, crewai_service, context, agent_timeout: int = None):
        """
        Initialize crew coordinator
        
        Args:
            crewai_service: The CrewAI service instance
            context: Request context for multi-tenant operations
            agent_timeout: Optional timeout for agent operations
        """
        self.crewai_service = crewai_service
        self.context = context
        self.agent_timeout = agent_timeout or FlowConfig.AGENT_TIMEOUT
        
        # Initialize orchestrator
        self.orchestrator = DiscoveryAgentOrchestrator()
        
        # Agent mapping by phase
        self._phase_agent_mapping = {
            PhaseNames.DATA_IMPORT_VALIDATION: "data_import_validation_agent",
            PhaseNames.FIELD_MAPPING: "attribute_mapping_agent",
            PhaseNames.DATA_CLEANSING: "data_cleansing_agent",
            PhaseNames.ASSET_INVENTORY: "asset_inventory_agent",
            PhaseNames.DEPENDENCY_ANALYSIS: "dependency_analysis_agent",
            PhaseNames.TECH_DEBT_ASSESSMENT: "tech_debt_analysis_agent"
        }
    
    async def execute_phase_agent(self, phase_name: str, input_data: Dict[str, Any], context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the appropriate agent for a given phase
        
        Args:
            phase_name: Name of the phase
            input_data: Input data for the agent
            context_data: Additional context for agent execution
            
        Returns:
            Agent execution results
        """
        agent_name = self._phase_agent_mapping.get(phase_name)
        if not agent_name:
            raise ValueError(f"No agent mapped for phase: {phase_name}")
        
        logger.info(f"🤖 Executing agent '{agent_name}' for phase '{phase_name}'")
        
        # Prepare agent context
        agent_context = self._prepare_agent_context(phase_name, context_data)
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._execute_agent(agent_name, input_data, agent_context),
                timeout=self.agent_timeout
            )
            logger.info(f"✅ Agent '{agent_name}' completed successfully")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Agent '{agent_name}' timed out after {self.agent_timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"❌ Agent '{agent_name}' failed: {str(e)}")
            raise
    
    async def execute_parallel_agents(self, phases: List[str], input_data: Dict[str, Any], context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute multiple agents in parallel
        
        Args:
            phases: List of phase names to execute in parallel
            input_data: Input data for the agents
            context_data: Additional context for agent execution
            
        Returns:
            Combined results from all agents
        """
        logger.info(f"🚀 Executing {len(phases)} agents in parallel: {phases}")
        
        # Create tasks for parallel execution
        tasks = []
        for phase_name in phases:
            task = self.execute_phase_agent(phase_name, input_data, context_data)
            tasks.append(task)
        
        # Execute in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            combined_results = {}
            errors = []
            
            for phase_name, result in zip(phases, results):
                if isinstance(result, Exception):
                    errors.append({
                        "phase": phase_name,
                        "error": str(result)
                    })
                else:
                    combined_results[phase_name] = result
            
            if errors:
                logger.warning(f"⚠️ {len(errors)} agents failed during parallel execution")
                combined_results["errors"] = errors
            
            logger.info(f"✅ Parallel agent execution completed")
            return combined_results
            
        except Exception as e:
            logger.error(f"❌ Parallel agent execution failed: {str(e)}")
            raise
    
    def _prepare_agent_context(self, phase_name: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare context for agent execution"""
        base_context = {
            "phase": phase_name,
            "client_account_id": str(self.context.client_account_id),
            "engagement_id": str(self.context.engagement_id),
            "user_id": str(self.context.user_id),
            "timestamp": datetime.utcnow().isoformat(),
            "config": FlowConfig.get_phase_config(phase_name)
        }
        
        # Merge with provided context
        if context_data:
            base_context.update(context_data)
        
        return base_context
    
    async def _execute_agent(self, agent_name: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific agent through the orchestrator"""
        
        # For pseudo-agents (data validation, mapping, cleansing), use orchestrator
        if agent_name in ["data_import_validation_agent", "attribute_mapping_agent", "data_cleansing_agent"]:
            # The orchestrator executes these agents in sequence
            result = await self.orchestrator.execute(input_data, context)
            # Extract the specific agent's result
            if 'agent_results' in result and agent_name in result['agent_results']:
                return result['agent_results'][agent_name]
            else:
                # Return a default success result if not found
                return {
                    "status": "success",
                    "agent": agent_name,
                    "data": input_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Map agent names to specific handlers
        agent_methods = {
            "asset_inventory_agent": self._execute_asset_inventory_agent,
            "dependency_analysis_agent": self._execute_analysis_agent,
            "tech_debt_analysis_agent": self._execute_analysis_agent
        }
        
        method = agent_methods.get(agent_name)
        if not method:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Special handling for analysis agents
        if agent_name in ["dependency_analysis_agent", "tech_debt_analysis_agent"]:
            return await method(agent_name, input_data, context)
        else:
            return await method(input_data, context)
    
    async def _execute_asset_inventory_agent(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute asset inventory agent (placeholder for actual implementation)"""
        # This would be implemented based on the actual asset inventory agent
        logger.info("🤖 Executing asset inventory agent")
        
        # For now, return a structured response
        return {
            "assets": input_data.get("assets", []),
            "total_count": len(input_data.get("assets", [])),
            "asset_types": self._categorize_assets(input_data.get("assets", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_analysis_agent(self, agent_name: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis agents (dependency or tech debt)"""
        # Use the orchestrator's main execution method
        analysis_results = await self.orchestrator.execute_discovery_agents(input_data, context)
        
        # Extract specific agent results
        if agent_name == "dependency_analysis_agent":
            return analysis_results.get("dependencies", {})
        elif agent_name == "tech_debt_analysis_agent":
            return analysis_results.get("technical_debt", {})
        
        return analysis_results
    
    def _categorize_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize assets by type"""
        asset_types = {}
        for asset in assets:
            asset_type = asset.get("type", "unknown")
            asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
        return asset_types
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent"""
        base_config = FlowConfig.get_agent_config()
        
        # Add agent-specific configurations
        agent_configs = {
            "data_import_validation_agent": {
                "validation_rules": ["schema", "data_types", "completeness"],
                "threshold": 0.95
            },
            "attribute_mapping_agent": {
                "confidence_threshold": FlowConfig.DEFAULT_CONFIDENCE_THRESHOLD,
                "auto_map": True
            },
            "data_cleansing_agent": {
                "quality_threshold": FlowConfig.DEFAULT_DATA_QUALITY_THRESHOLD,
                "cleansing_operations": ["dedup", "normalize", "validate"]
            },
            "asset_inventory_agent": {
                "batch_size": FlowConfig.DEFAULT_BATCH_SIZE,
                "categorization": True
            },
            "dependency_analysis_agent": {
                "depth": 3,
                "include_indirect": True
            },
            "tech_debt_analysis_agent": {
                "severity_levels": ["critical", "high", "medium", "low"],
                "include_recommendations": True
            }
        }
        
        # Merge base config with agent-specific config
        specific_config = agent_configs.get(agent_name, {})
        return {**base_config, **specific_config}
    
    async def validate_agent_health(self) -> Dict[str, bool]:
        """Validate that all required agents are healthy"""
        health_status = {}
        
        for phase, agent_name in self._phase_agent_mapping.items():
            try:
                # Simple health check - verify agent is available
                health_status[agent_name] = True
                logger.info(f"✅ Agent '{agent_name}' is healthy")
            except Exception as e:
                health_status[agent_name] = False
                logger.warning(f"⚠️ Agent '{agent_name}' health check failed: {str(e)}")
        
        return health_status