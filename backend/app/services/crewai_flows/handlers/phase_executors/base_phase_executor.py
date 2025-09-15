"""
Base Phase Executor
Base class for all discovery phase executors.
Provides common functionality and fallback mechanisms.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    # Flow import will be used when needed
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
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute phase using CrewAI crew"""
        pass

    async def execute_fallback(self) -> Dict[str, Any]:
        """NO FALLBACK - This method should never be called"""
        phase_name = self.get_phase_name()
        logger.error(
            f"❌ execute_fallback called for {phase_name} - NO FALLBACK ALLOWED"
        )
        raise RuntimeError(
            f"Fallback execution attempted for {phase_name}. All phases must use CrewAI agents."
        )

    async def execute(self, previous_result) -> Dict[str, Any]:
        """Main execution method - template pattern with PostgreSQL persistence"""
        phase_name = self.get_phase_name()
        logger.info(f"🔍 Starting {phase_name} execution")

        # Send phase start notification via agent-ui-bridge
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge

            flow_id = getattr(self.state, "flow_id", None)

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
                    "progress": self.get_progress_percentage(),
                },
                page=f"flow_{flow_id}",
                flow_id=flow_id,
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
                    crew_results=None,  # No results yet, just phase transition
                )
            except Exception as e:
                logger.warning(f"⚠️ State sync failed during phase start: {e}")

        try:
            # CREWAI MODE: Check if we should disable CrewAI (fast mode)
            import os

            from app.core.config import settings

            use_fast_mode = (
                settings.CREWAI_FAST_MODE
                or os.getenv("USE_FAST_DISCOVERY_MODE", "false").lower() == "true"
            )

            # Use CrewAI by default unless explicitly disabled
            if not use_fast_mode and CREWAI_FLOW_AVAILABLE:
                crew = self.crew_manager.create_crew_on_demand(
                    phase_name, **self._get_crew_context()
                )

                if crew:
                    logger.info(
                        f"🤖 Using CrewAI crew for {phase_name} (real agents active)"
                    )
                    crew_input = self._prepare_crew_input()

                    # Add timeout for crew execution (if specified)
                    import asyncio

                    try:
                        # Set timeout based on phase complexity
                        phase_timeout = self._get_phase_timeout()
                        if phase_timeout is not None:
                            results = await asyncio.wait_for(
                                self.execute_with_crew(crew_input),
                                timeout=phase_timeout,
                            )
                        else:
                            # No timeout for agentic activities
                            logger.info(
                                f"⏱️ No timeout set for {phase_name} - agentic activity"
                            )
                            results = await self.execute_with_crew(crew_input)
                    except asyncio.TimeoutError:
                        # NO FALLBACK - Timeout is a real issue that needs to be fixed
                        logger.error(
                            f"⏱️ Crew execution timed out after {phase_timeout}s - NO FALLBACK"
                        )
                        raise RuntimeError(
                            f"CrewAI crew execution timed out for {phase_name}. This needs to be fixed."
                        )
                else:
                    # NO FALLBACK - Crew creation failure is a real issue
                    logger.error(f"{phase_name} crew not available - NO FALLBACK")
                    raise RuntimeError(
                        f"CrewAI crew creation failed for {phase_name}. This needs to be fixed."
                    )
            else:
                # NO FALLBACK - CrewAI should always be available
                logger.error("CrewAI not available or fast mode enabled - NO FALLBACK")
                raise RuntimeError(
                    f"CrewAI is not available for {phase_name}. This is a critical dependency."
                )

            # Store results and update state
            await self._store_results(results)
            self.state.mark_phase_complete(phase_name, results)
            self.state.update_progress()

            # Sync phase completion to PostgreSQL (if bridge available)
            if self.flow_bridge:
                try:
                    await self.flow_bridge.sync_state_update(
                        self.state, phase_name, crew_results=results
                    )
                except Exception as e:
                    logger.warning(f"⚠️ State sync failed during phase completion: {e}")

            # Send phase completion notification via agent-ui-bridge
            try:
                from app.services.agent_ui_bridge import agent_ui_bridge

                flow_id = getattr(self.state, "flow_id", None)

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
                        "results_summary": results.get(
                            "summary", "Phase completed successfully"
                        ),
                    },
                    page=f"flow_{flow_id}",
                    flow_id=flow_id,
                )
            except Exception as e:
                logger.warning(f"Failed to send phase completion notification: {e}")

            logger.info(f"✅ {phase_name} completed successfully")
            # Return the actual results dict instead of just a string
            return results

        except Exception as e:
            logger.error(f"❌ {phase_name} execution failed: {e}")
            self.state.add_error(phase_name, str(e))

            # Sync error state to PostgreSQL (if bridge available)
            if self.flow_bridge:
                try:
                    await self.flow_bridge.sync_state_update(
                        self.state,
                        phase_name,
                        crew_results={"error": str(e), "status": "failed"},
                    )
                except Exception as sync_error:
                    logger.warning(
                        f"⚠️ State sync failed during error handling: {sync_error}"
                    )

            # Return error result dict
            return {"error": str(e), "status": "failed", "phase": phase_name}

    def _get_crew_context(self) -> Dict[str, Any]:
        """Get context data for crew creation - override in subclasses"""
        return {"shared_memory": getattr(self.state, "shared_memory_reference", None)}

    def _get_phase_timeout(self) -> Optional[int]:
        """Get timeout in seconds for this phase - override in subclasses for custom timeouts"""
        return 20  # Default 20 second timeout for UI interactions

    @abstractmethod
    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for crew execution"""
        pass

    @abstractmethod
    async def _store_results(self, results: Dict[str, Any]):
        """Store execution results in state"""
        pass

    def _process_crew_result(self, crew_result) -> Dict[str, Any]:
        """Process raw crew result into standardized format"""
        if hasattr(crew_result, "raw") and crew_result.raw:
            return {"raw_result": crew_result.raw, "processed": True}
        elif isinstance(crew_result, dict):
            return crew_result
        else:
            return {"raw_result": str(crew_result), "processed": False}
