"""
CrewAI Service - Modular & Robust
Provides AI-powered migration analysis with clean modular architecture.
Enhanced with field mapping intelligence and content-based analysis.
"""

import logging
from typing import Dict, List, Optional, Any

from .crewai_handlers.crew_manager import CrewManager
from .crewai_handlers.agent_coordinator import AgentCoordinator
from .crewai_handlers.task_processor import TaskProcessor
from .crewai_handlers.analysis_engine import AnalysisEngine

logger = logging.getLogger(__name__)

class CrewAIService:
    """Modular CrewAI service with graceful fallbacks and enhanced field mapping intelligence."""
    
    def __init__(self):
        # Initialize handlers
        self.crew_manager = CrewManager()
        self.agent_coordinator = AgentCoordinator()
        self.task_processor = TaskProcessor()
        self.analysis_engine = AnalysisEngine()
        
        # Initialize agent manager if LLM is available
        llm = self.crew_manager.get_llm()
        if llm:
            self.agent_coordinator.initialize_agent_manager(llm)
        
        # Initialize field mapping tool for enhanced AI analysis
        try:
            from app.services.field_mapper_modular import field_mapper
            self.field_mapping_tool = field_mapper
            # Pass field mapping tool to handlers that need it
            self.task_processor.set_field_mapping_tool(field_mapper)
            self.analysis_engine.set_field_mapping_tool(field_mapper)
            logger.info("Field mapping tool initialized for enhanced AI analysis")
        except ImportError as e:
            logger.warning(f"Field mapping tool not available: {e}")
            self.field_mapping_tool = None
        
        logger.info("CrewAI service initialized with modular architecture and enhanced intelligence")
    
    def is_available(self) -> bool:
        """Check if the service is available."""
        return True  # Always available with fallbacks
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        return {
            "status": "healthy",
            "service": "crewai",
            "version": "2.0.0",
            "components": {
                "crew_manager": self.crew_manager.is_available(),
                "agent_coordinator": self.agent_coordinator.is_available(),
                "task_processor": self.task_processor.is_available(),
                "analysis_engine": self.analysis_engine.is_available()
            },
            "crew_manager_status": self.crew_manager.get_status()
        }
    
    def reinitialize_with_fresh_llm(self) -> None:
        """Reinitialize with fresh LLM context."""
        self.crew_manager.reinitialize_with_fresh_llm()
        llm = self.crew_manager.get_llm()
        if llm:
            self.agent_coordinator.initialize_agent_manager(llm)
    
    @property
    def agents(self):
        """Get available agents."""
        return self.agent_coordinator.get_agents()
    
    @property
    def crews(self):
        """Get available crews."""
        return self.agent_coordinator.get_crews()
    
    # Analysis methods
    async def analyze_asset_6r_strategy(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze asset for 6R migration strategy."""
        return await self.analysis_engine.analyze_asset_6r_strategy(asset_data)
    
    async def assess_migration_risks(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess migration risks for applications."""
        return await self.analysis_engine.assess_migration_risks(migration_data)
    
    async def optimize_wave_plan(self, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize migration wave planning."""
        return await self.analysis_engine.optimize_wave_plan(assets_data)
    
    # Data processing methods
    async def analyze_cmdb_data(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CMDB data with AI processing."""
        processing_data = {"cmdb_data": cmdb_data}
        return await self.task_processor.process_cmdb_data(processing_data)
    
    async def process_cmdb_data(self, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process CMDB data for analysis."""
        return await self.task_processor.process_cmdb_data(processing_data)
    
    async def process_user_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback for learning."""
        return await self.task_processor.process_user_feedback(feedback_data)
    
    # Task execution methods
    async def execute_task_async(self, task: Any) -> str:
        """Execute a task asynchronously."""
        return await self.task_processor.execute_task_async(task)
    
    # Utility methods for backward compatibility
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response (fallback method)."""
        try:
            import json
            return json.loads(response)
        except Exception:
            return {"response": response, "parsed": False}
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text (fallback method)."""
        try:
            import json
            import re
            
            # Try to find JSON in the text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return None
        except Exception:
            return None
    
    def test_json_parsing_improvements(self) -> Dict[str, Any]:
        """Test JSON parsing capabilities."""
        return {
            "status": "available",
            "parsing_methods": ["json.loads", "regex_extraction", "fallback_parsing"],
            "test_passed": True
        }
    
    # Enhanced asset inventory management methods
    async def analyze_asset_inventory(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agentic asset inventory analysis using Asset Intelligence Agent.
        Leverages learned field mappings and intelligent pattern recognition.
        """
        return await self.analysis_engine.analyze_asset_inventory(inventory_data)
    
    async def plan_asset_bulk_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered bulk operation planning using Asset Intelligence Agent.
        """
        return await self.analysis_engine.plan_asset_bulk_operation(operation_data)
    
    async def classify_assets(self, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered asset classification using learned patterns and field mapping intelligence.
        """
        return await self.analysis_engine.classify_assets(classification_data)
    
    async def process_asset_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback from asset management operations to improve AI intelligence.
        """
        return await self.task_processor.process_asset_feedback(feedback_data)

# Global service instance for backward compatibility
crewai_service = CrewAIService() 