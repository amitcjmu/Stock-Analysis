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
        
        # Send phase start notification via agent-ui-bridge
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            flow_id = getattr(self.state, 'flow_id', None)
            
            from app.services.models.agent_communication import ConfidenceLevel
            agent_ui_bridge.add_agent_insight(
                agent_id=f"{phase_name}_executor",
                agent_name=f"{phase_name.replace('_', ' ').title()} Phase",
                insight_type="phase_start",
                title=f"Starting {phase_name.replace('_', ' ').title()}",
                description=f"Beginning execution of {phase_name.replace('_', ' ')} phase",
                confidence=ConfidenceLevel.HIGH,
                supporting_data={
                    "phase": phase_name,
                    "status": "starting",
                    "progress": self.get_progress_percentage()
                },
                page=f"flow_{flow_id}",
                flow_id=flow_id
            )
        except Exception as e:
            logger.warning(f"Failed to send phase start notification: {e}")
        
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
            # CREWAI MODE: Check if we should disable CrewAI (fast mode)
            import os
            from app.core.config import settings
            use_fast_mode = settings.CREWAI_FAST_MODE or os.getenv("USE_FAST_DISCOVERY_MODE", "false").lower() == "true"
            
            # Use CrewAI by default unless explicitly disabled
            if not use_fast_mode and CREWAI_FLOW_AVAILABLE:
                crew = self.crew_manager.create_crew_on_demand(
                    phase_name,
                    **self._get_crew_context()
                )
                
                if crew:
                    logger.info(f"🤖 Using CrewAI crew for {phase_name} (real agents active)")
                    crew_input = self._prepare_crew_input()
                    
                    # Add timeout for crew execution
                    import asyncio
                    try:
                        results = await asyncio.wait_for(
                            self.execute_with_crew(crew_input),
                            timeout=20  # 20 second hard timeout
                        )
                    except asyncio.TimeoutError:
                        logger.error(f"⏱️ Crew execution timed out after 20s, using fallback")
                        results = await self.execute_fallback()
                else:
                    logger.warning(f"{phase_name} crew not available - using fallback")
                    results = await self.execute_fallback()
            else:
                # Use fast fallback when explicitly enabled
                logger.info(f"⚡ Using optimized fallback for {phase_name} (fast mode explicitly enabled)")
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
            
            # Send phase completion notification via agent-ui-bridge
            try:
                from app.services.agent_ui_bridge import agent_ui_bridge
                flow_id = getattr(self.state, 'flow_id', None)
                
                from app.services.models.agent_communication import ConfidenceLevel
                agent_ui_bridge.add_agent_insight(
                    agent_id=f"{phase_name}_executor",
                    agent_name=f"{phase_name.replace('_', ' ').title()} Phase",
                    insight_type="phase_complete",
                    title=f"Completed {phase_name.replace('_', ' ').title()}",
                    description=f"Successfully completed {phase_name.replace('_', ' ')} phase",
                    confidence=ConfidenceLevel.HIGH,
                    supporting_data={
                        "phase": phase_name,
                        "status": "completed",
                        "progress": self.state.progress_percentage,
                        "results_summary": results.get("summary", "Phase completed successfully")
                    },
                    page=f"flow_{flow_id}",
                    flow_id=flow_id
                )
            except Exception as e:
                logger.warning(f"Failed to send phase completion notification: {e}")
            
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
        phase_name = self.get_phase_name()
        
        # 🚀 DATA VALIDATION: Check if we have data to process
        # Check for data in order of processing: cleaned_data -> raw_data
        data_to_process = getattr(self.state, 'cleaned_data', None) or getattr(self.state, 'raw_data', [])
        if not data_to_process:
            logger.error(f"❌ No data available for {phase_name} - skipping")
            return {"status": "skipped", "reason": "no_data", "phase": phase_name}
        
        logger.info(f"✅ Processing {len(data_to_process)} assets in {phase_name}")
        
        # Default implementation - override in subclasses
        return {"status": "fallback_executed", "phase": phase_name, "assets_processed": len(data_to_process)} 