"""
Field Mapping Executor - Backward Compatibility Wrapper

This file maintains backward compatibility with existing code while using
the new modular field mapping executor implementation. The original complex
1207-line implementation has been modularized into specialized components
for better maintainability and reduced complexity.

The modular implementation is located at:
/backend/app/services/field_mapping_executor/

This wrapper ensures ZERO breaking changes while leveraging the new
architecture that provides:
- Reduced cyclomatic complexity (each module <400 lines, complexity <10)
- Better separation of concerns
- Improved testability
- Enhanced maintainability
- Cleaner error handling

For new code, consider importing directly from:
from app.services.field_mapping_executor import FieldMappingExecutor
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import the modular implementation
from app.services.field_mapping_executor import (
    FieldMappingExecutor as ModularFieldMappingExecutor,
)
from app.services.field_mapping_executor import (
    FieldMappingExecutorError,
    MappingParseError,
    ValidationError,
    CrewExecutionError,
    TransformationError,
)

# Import base executor for inheritance compatibility
from .base_phase_executor import BasePhaseExecutor

# Import modularized utilities
from .field_mapping_utils import (
    CREWAI_FLOW_AVAILABLE,
    get_supported_flow_types,
    validate_input,
    get_execution_context,
    prepare_crew_input_from_state,
    store_results_in_state,
)
from .field_mapping_converters import (
    convert_crew_input_to_state,
    convert_result_to_crew_format,
    convert_flow_state_to_crew_input,
)
from .field_mapping_fallback import execute_with_crew_fallback

logger = logging.getLogger(__name__)


class FieldMappingExecutor(BasePhaseExecutor):
    """
    Backward compatibility wrapper for the modular FieldMappingExecutor.

    This class maintains the exact same interface as the original implementation
    while using the new modular architecture under the hood. It ensures zero
    breaking changes for existing code.

    The modular implementation provides:
    - Specialized parsers for different response formats
    - Comprehensive validation with multiple strategies
    - Intelligent mapping engine with similarity calculations
    - Robust transformation and database persistence
    - Business rules engine with clarification generation
    - Structured response formatting

    All functionality is preserved while significantly reducing complexity
    and improving maintainability.
    """

    def __init__(self, state, crew_manager, flow_bridge=None):
        """Initialize with backward compatibility support."""
        super().__init__(state, crew_manager, flow_bridge)

        # Extract context from state for modular executor
        client_account_id = getattr(state, "client_account_id", None)
        engagement_id = getattr(state, "engagement_id", None)

        # Initialize the modular executor with proper error handling
        # The modular executor will be used through our wrapper methods
        try:
            # Try to initialize with the fixed modular executor
            self._modular_executor = ModularFieldMappingExecutor(
                storage_manager=getattr(self, "storage_manager", None),
                agent_pool=getattr(self, "agent_pool", None),
                client_account_id=client_account_id or "unknown",
                engagement_id=engagement_id or "unknown",
            )
            logger.info("Successfully initialized modular executor")
        except Exception as e:
            logger.error(f"Could not initialize modular executor: {e}", exc_info=True)
            # Set to None and handle execution through fallback
            self._modular_executor = None

        logger.info(
            f"FieldMappingExecutor (compatibility wrapper) initialized for client {client_account_id}"
        )

    def get_phase_name(self) -> str:
        """Get the name of this phase - maintains compatibility."""
        return "attribute_mapping"

    def get_progress_percentage(self) -> float:
        """Get the progress percentage when this phase completes."""
        return 16.7  # 1/6 phases

    def _get_phase_timeout(self) -> Optional[int]:
        """Override timeout for field mapping - needs more time for LLM processing."""
        return 300  # 5 minutes for standard crew with multiple agents

    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute field mapping using CrewAI crew - compatibility wrapper.

        This method maintains the original interface while using the modular
        implementation for actual execution.
        """
        try:
            logger.info(
                f"Executing field mapping with crew for engagement {self.engagement_id}"
            )

            # Create a mock state object from crew_input
            mock_state = convert_crew_input_to_state(crew_input, self.state)

            # Get async database session with proper lifecycle management
            from app.db.session import get_db

            # SECURITY FIX: Proper async context management for database sessions
            # Support both async and sync generators with defensive handling
            db_session_generator = get_db()
            db_session = None

            try:
                # Handle async generator
                if hasattr(db_session_generator, "__anext__"):
                    db_session = await db_session_generator.__anext__()
                # Handle sync generator as fallback
                elif hasattr(db_session_generator, "__next__"):
                    db_session = next(db_session_generator)
                else:
                    raise RuntimeError(
                        "Database session generator not properly configured"
                    )

                # Execute using modular implementation if available
                if self._modular_executor:
                    result = await self._modular_executor.execute_phase(
                        mock_state, db_session
                    )
                    # Convert result back to expected format
                    return convert_result_to_crew_format(result, self.get_phase_name())
                else:
                    # Fallback execution when modular executor is not available
                    logger.warning(
                        "Modular executor not available, using direct crew execution"
                    )
                    result = await execute_with_crew_fallback(
                        crew_input,
                        self.crew_manager,
                        self.get_phase_name(),
                        self._get_phase_timeout(),
                    )
                    return result

            finally:
                # SECURITY FIX: Ensure generator is properly closed in finally block
                if db_session:
                    try:
                        if hasattr(db_session, "close"):
                            # Handle async session close
                            if hasattr(db_session.close, "__await__"):
                                await db_session.close()
                            else:
                                db_session.close()
                    except Exception as close_error:
                        logger.warning(f"Error closing database session: {close_error}")

                # Close the generator to prevent connection leaks
                try:
                    if hasattr(db_session_generator, "aclose"):
                        await db_session_generator.aclose()
                    elif hasattr(db_session_generator, "close"):
                        db_session_generator.close()
                except Exception as gen_close_error:
                    logger.warning(
                        f"Error closing database generator: {gen_close_error}"
                    )

        except Exception as e:
            logger.error(f"Field mapping execution failed: {str(e)}")
            # Return compatible error format
            return {
                "success": False,
                "error": str(e),
                "phase_name": self.get_phase_name(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def execute_field_mapping(
        self, flow_state: Any, db_session: Any
    ) -> Dict[str, Any]:
        """
        Direct execution method - maintains original interface.

        This method provides backward compatibility for code that calls
        execute_field_mapping directly instead of using the crew interface.

        SECURITY FIX: Validates db_session before use to prevent errors.
        """
        try:
            logger.info(
                f"Executing field mapping directly for flow {getattr(flow_state, 'flow_id', 'unknown')}"
            )

            # SECURITY FIX: Validate db_session before DB operations
            if not db_session:
                raise ValueError(
                    "Database session is required for field mapping execution"
                )

            # Check if session is still active
            if hasattr(db_session, "is_active") and not db_session.is_active:
                raise ValueError("Database session is not active")

            # Use modular executor directly if available
            if self._modular_executor:
                result = await self._modular_executor.execute_phase(
                    flow_state, db_session
                )
            else:
                # Fallback to basic execution if modular executor not available
                logger.warning(
                    "Modular executor not available for direct execution, using basic execution"
                )
                # Convert flow_state to crew_input format and use fallback
                crew_input = convert_flow_state_to_crew_input(flow_state)
                result = await execute_with_crew_fallback(
                    crew_input,
                    self.crew_manager,
                    self.get_phase_name(),
                    self._get_phase_timeout(),
                )

            logger.info("Field mapping completed successfully")
            return result

        except Exception as e:
            logger.error(f"Direct field mapping execution failed: {str(e)}")
            raise FieldMappingExecutorError(
                f"Field mapping execution failed: {str(e)}"
            ) from e

    # Additional compatibility methods
    def get_supported_flow_types(self) -> List[str]:
        """Return the flow types supported by this executor."""
        return get_supported_flow_types()

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for field mapping."""
        return await validate_input(input_data)

    def get_execution_context(self) -> Dict[str, Any]:
        """Get execution context for field mapping."""
        return get_execution_context(
            self.get_phase_name(),
            self.client_account_id,
            self.engagement_id,
            self._get_phase_timeout(),
        )

    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for crew execution - required by BasePhaseExecutor."""
        return prepare_crew_input_from_state(self.state)

    async def _store_results(self, results: Dict[str, Any]):
        """Store execution results in state - required by BasePhaseExecutor."""
        store_results_in_state(self.state, results)

    async def execute_suggestions_only(
        self, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field mapping in suggestions-only mode for re-analysis."""
        try:
            logger.info("Executing field mapping in suggestions-only mode")

            # Prepare crew input with current state data
            crew_input = self._prepare_crew_input()

            # Override with any provided input data
            crew_input.update(input_data)

            # Execute field mapping with crew
            result = await self.execute_with_crew(crew_input)

            if result and result.get("success", True):
                logger.info("Field mapping suggestions generated successfully")
                return result
            else:
                logger.error(
                    f"Field mapping suggestions failed: {result.get('error', 'Unknown error')}"
                )
                return {
                    "success": False,
                    "error": result.get("error", "Field mapping suggestions failed"),
                    "mappings": [],
                    "clarifications": [],
                }

        except Exception as e:
            logger.error(f"Field mapping suggestions execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "mappings": [],
                "clarifications": [],
            }


# Export original class name for complete backward compatibility
__all__ = [
    "FieldMappingExecutor",
    "FieldMappingExecutorError",
    "MappingParseError",
    "ValidationError",
    "CrewExecutionError",
    "TransformationError",
    "CREWAI_FLOW_AVAILABLE",
]

# Legacy aliases for backward compatibility
AttributeMappingExecutor = FieldMappingExecutor
MappingExecutor = FieldMappingExecutor
