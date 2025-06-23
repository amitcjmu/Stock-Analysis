"""
Base Phase Executor
Base class for all discovery phase executors.
Provides common functionality and fallback mechanisms.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    logger.warning("CrewAI Flow not available")


class BasePhaseExecutor(ABC):
    """
    Base class for all discovery phase executors.
    Provides common execution patterns and fallback mechanisms.
    Now integrated with Flow State Bridge for PostgreSQL persistence.
    """
    
    def __init__(self, state, crew_manager, flow_bridge: Optional[Any] = None):
        """Initialize phase executor with state, crew manager, and flow bridge"""
        self.state = state
        self.crew_manager = crew_manager
        self.flow_bridge = flow_bridge  # FlowStateBridge for PostgreSQL persistence
    
    @abstractmethod
    def get_phase_name(self) -> str:
        """Get the name of this phase"""
        pass
    
    @abstractmethod
    def get_progress_percentage(self) -> float:
        """Get the progress percentage when this phase completes"""
        pass
    
    @abstractmethod
    def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute phase using CrewAI crew"""
        pass
    
    @abstractmethod
    def execute_fallback(self) -> Dict[str, Any]:
        """Execute phase using fallback logic when crew is not available"""
        pass
    
    async def execute(self, previous_result) -> str:
        """Main execution method - template pattern with PostgreSQL persistence"""
        phase_name = self.get_phase_name()
        logger.info(f"🔍 Starting {phase_name} execution")
        
        # Update state
        self.state.current_phase = phase_name
        self.state.progress_percentage = self.get_progress_percentage()
        
        # Sync state update to PostgreSQL (if bridge available)
        if self.flow_bridge:
            try:
                await self.flow_bridge.sync_state_update(
                    self.state, 
                    phase_name, 
                    crew_results=None  # No results yet, just phase transition
                )
            except Exception as e:
                logger.warning(f"⚠️ State sync failed during phase start: {e}")
        
        try:
            # Try CrewAI execution first
            if CREWAI_FLOW_AVAILABLE:
                crew = self.crew_manager.create_crew_on_demand(
                    phase_name,
                    **self._get_crew_context()
                )
                
                if crew:
                    crew_input = self._prepare_crew_input()
                    results = await self.execute_with_crew(crew_input)
                else:
                    logger.warning(f"{phase_name} crew not available - using fallback")
                    results = await self.execute_fallback()
            else:
                logger.warning(f"CrewAI not available for {phase_name} - using fallback")
                results = await self.execute_fallback()
            
            # Store results and update state
            self._store_results(results)
            self.state.mark_phase_complete(phase_name, results)
            self.state.update_progress()
            
            # Sync phase completion to PostgreSQL (if bridge available)
            if self.flow_bridge:
                try:
                    await self.flow_bridge.sync_state_update(
                        self.state, 
                        phase_name, 
                        crew_results=results
                    )
                except Exception as e:
                    logger.warning(f"⚠️ State sync failed during phase completion: {e}")
            
            logger.info(f"✅ {phase_name} completed successfully")
            return f"{phase_name}_completed"
            
        except Exception as e:
            logger.error(f"❌ {phase_name} execution failed: {e}")
            self.state.add_error(phase_name, str(e))
            
            # Sync error state to PostgreSQL (if bridge available)
            if self.flow_bridge:
                try:
                    await self.flow_bridge.sync_state_update(
                        self.state, 
                        phase_name, 
                        crew_results={"error": str(e), "status": "failed"}
                    )
                except Exception as sync_error:
                    logger.warning(f"⚠️ State sync failed during error handling: {sync_error}")
            
            return f"{phase_name}_failed"
    
    def _get_crew_context(self) -> Dict[str, Any]:
        """Get context data for crew creation - override in subclasses"""
        return {
            "shared_memory": getattr(self.state, 'shared_memory_reference', None)
        }
    
    @abstractmethod
    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for crew execution"""
        pass
    
    @abstractmethod
    def _store_results(self, results: Dict[str, Any]):
        """Store execution results in state"""
        pass
    
    def _process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Process raw crew result into standardized format"""
        if hasattr(crew_result, 'raw') and crew_result.raw:
            return {"raw_result": crew_result.raw, "processed": True}
        elif isinstance(crew_result, dict):
            return crew_result
        else:
            return {"raw_result": str(crew_result), "processed": False}
    
    # Make execute_with_crew and execute_fallback async
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute phase using CrewAI crew - now async"""
        # Default implementation - override in subclasses
        return {"status": "not_implemented", "phase": self.get_phase_name()}
    
    async def execute_fallback(self) -> Dict[str, Any]:
        """Execute phase using fallback logic - now async"""
        # Default implementation - override in subclasses
        return {"status": "fallback_executed", "phase": self.get_phase_name()} 