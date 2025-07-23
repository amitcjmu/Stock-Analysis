"""
Phase Controller Module

Manages phase-by-phase execution of the Discovery Flow instead of relying on
automatic @listen chains. This allows for proper pause/resume functionality
and prevents the rate limiting issues caused by concurrent phase execution.
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FlowPhase(Enum):
    """Enumeration of discovery flow phases"""

    INITIALIZATION = "initialization"
    DATA_IMPORT_VALIDATION = "data_import_validation"
    FIELD_MAPPING_SUGGESTIONS = "field_mapping_suggestions"
    FIELD_MAPPING_APPROVAL = "field_mapping_approval"
    DATA_CLEANSING = "data_cleansing"
    ASSET_INVENTORY = "asset_inventory"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    TECH_DEBT_ASSESSMENT = "tech_debt_assessment"
    FINALIZATION = "finalization"


class PhaseExecutionResult:
    """Result of phase execution"""

    def __init__(
        self,
        phase: FlowPhase,
        status: str,
        data: Dict[str, Any] = None,
        requires_user_input: bool = False,
        next_phase: Optional[FlowPhase] = None,
    ):
        self.phase = phase
        self.status = status
        self.data = data or {}
        self.requires_user_input = requires_user_input
        self.next_phase = next_phase
        self.timestamp = None


class PhaseController:
    """
    Controls phase-by-phase execution of the Discovery Flow.

    This replaces the automatic @listen chain execution with explicit phase control,
    allowing for proper pauses between phases for user input.
    """

    def __init__(self, discovery_flow):
        """
        Initialize phase controller with reference to the discovery flow.

        Args:
            discovery_flow: UnifiedDiscoveryFlow instance to control
        """
        self.discovery_flow = discovery_flow
        self.current_phase = None
        self.phase_results = {}
        self.execution_halted = False

        # Define phase execution order
        self.phase_sequence = [
            FlowPhase.INITIALIZATION,
            FlowPhase.DATA_IMPORT_VALIDATION,
            FlowPhase.FIELD_MAPPING_SUGGESTIONS,
            FlowPhase.FIELD_MAPPING_APPROVAL,  # User input required
            FlowPhase.DATA_CLEANSING,
            FlowPhase.ASSET_INVENTORY,
            FlowPhase.DEPENDENCY_ANALYSIS,
            FlowPhase.TECH_DEBT_ASSESSMENT,
            FlowPhase.FINALIZATION,
        ]

        # Map phases to their execution methods
        self.phase_methods = {
            FlowPhase.INITIALIZATION: self._execute_initialization,
            FlowPhase.DATA_IMPORT_VALIDATION: self._execute_data_import_validation,
            FlowPhase.FIELD_MAPPING_SUGGESTIONS: self._execute_field_mapping_suggestions,
            FlowPhase.FIELD_MAPPING_APPROVAL: self._execute_field_mapping_approval,
            FlowPhase.DATA_CLEANSING: self._execute_data_cleansing,
            FlowPhase.ASSET_INVENTORY: self._execute_asset_inventory,
            FlowPhase.DEPENDENCY_ANALYSIS: self._execute_dependency_analysis,
            FlowPhase.TECH_DEBT_ASSESSMENT: self._execute_tech_debt_assessment,
            FlowPhase.FINALIZATION: self._execute_finalization,
        }

    async def start_flow_execution(self) -> PhaseExecutionResult:
        """
        Start flow execution from the beginning.

        Returns:
            PhaseExecutionResult: Result of the first phase or pause point
        """
        logger.info("🎯 Starting controlled phase-by-phase flow execution")
        self.current_phase = FlowPhase.INITIALIZATION
        self.execution_halted = False

        return await self.execute_current_phase()

    async def resume_flow_execution(
        self, from_phase: FlowPhase, user_input: Dict[str, Any] = None
    ) -> PhaseExecutionResult:
        """
        Resume flow execution from a specific phase.

        Args:
            from_phase: Phase to resume from
            user_input: User input data (for approval phases)

        Returns:
            PhaseExecutionResult: Result of the resumed execution
        """
        logger.info(f"🔄 Resuming flow execution from phase: {from_phase.value}")

        if user_input:
            logger.info(f"📝 User input provided: {list(user_input.keys())}")
            self.phase_results[from_phase] = PhaseExecutionResult(
                phase=from_phase, status="user_input_provided", data=user_input
            )

        # For field mapping approval, move directly to data cleansing
        if (
            from_phase == FlowPhase.FIELD_MAPPING_APPROVAL
            and user_input
            and user_input.get("user_approval")
        ):
            logger.info("✅ Field mapping approved - moving to data cleansing phase")
            self.current_phase = FlowPhase.DATA_CLEANSING
        else:
            self.current_phase = from_phase

        self.execution_halted = False

        return await self.execute_current_phase()

    async def execute_current_phase(self) -> PhaseExecutionResult:
        """
        Execute the current phase.

        Returns:
            PhaseExecutionResult: Result of phase execution
        """
        if not self.current_phase:
            raise ValueError("No current phase set")

        if self.execution_halted:
            logger.warning("⏸️ Execution is halted - cannot execute phase")
            return PhaseExecutionResult(
                phase=self.current_phase,
                status="execution_halted",
                requires_user_input=True,
            )

        logger.info(f"🚀 Executing phase: {self.current_phase.value}")

        try:
            # Get previous result for input to current phase
            previous_result = self._get_previous_phase_result()

            # Execute the phase method
            phase_method = self.phase_methods[self.current_phase]
            result = await phase_method(previous_result)

            # Store result
            self.phase_results[self.current_phase] = result

            logger.info(
                f"✅ Phase {self.current_phase.value} completed with status: {result.status}"
            )

            # Check if we need to pause for user input
            if result.requires_user_input:
                logger.info(
                    f"⏸️ Phase {self.current_phase.value} requires user input - pausing flow"
                )
                self.execution_halted = True
                return result

            # Move to next phase if available
            if result.next_phase:
                self.current_phase = result.next_phase
                logger.info(f"➡️ Moving to next phase: {self.current_phase.value}")

                # Continue execution of next phase
                return await self.execute_current_phase()
            else:
                # Flow completed
                logger.info("🏁 Flow execution completed")
                return result

        except Exception as e:
            logger.error(f"❌ Phase {self.current_phase.value} failed: {e}")
            return PhaseExecutionResult(
                phase=self.current_phase, status="failed", data={"error": str(e)}
            )

    def _get_previous_phase_result(self) -> Any:
        """Get the result from the previous phase"""
        current_index = self.phase_sequence.index(self.current_phase)
        if current_index == 0:
            return None  # First phase has no previous result

        previous_phase = self.phase_sequence[current_index - 1]
        previous_result = self.phase_results.get(previous_phase)

        if previous_result:
            return previous_result.data
        return None

    def _get_next_phase(self) -> Optional[FlowPhase]:
        """Get the next phase in sequence"""
        try:
            current_index = self.phase_sequence.index(self.current_phase)
            if current_index < len(self.phase_sequence) - 1:
                return self.phase_sequence[current_index + 1]
            return None
        except ValueError:
            return None

    # Phase execution methods (delegate to discovery flow methods)

    async def _execute_initialization(self, previous_result) -> PhaseExecutionResult:
        """Execute initialization phase"""
        result = await self.discovery_flow.initialize_discovery()

        return PhaseExecutionResult(
            phase=FlowPhase.INITIALIZATION,
            status="completed" if result == "initialization_completed" else "failed",
            data={"result": result},
            next_phase=(
                FlowPhase.DATA_IMPORT_VALIDATION
                if result == "initialization_completed"
                else None
            ),
        )

    async def _execute_data_import_validation(
        self, previous_result
    ) -> PhaseExecutionResult:
        """Execute data import validation phase"""
        result = await self.discovery_flow.execute_data_import_validation_agent(
            previous_result
        )

        return PhaseExecutionResult(
            phase=FlowPhase.DATA_IMPORT_VALIDATION,
            status=(
                "completed"
                if result not in ["discovery_failed", "data_validation_failed"]
                else "failed"
            ),
            data={"result": result},
            next_phase=(
                FlowPhase.FIELD_MAPPING_SUGGESTIONS
                if result not in ["discovery_failed", "data_validation_failed"]
                else None
            ),
        )

    async def _execute_field_mapping_suggestions(
        self, previous_result
    ) -> PhaseExecutionResult:
        """Execute field mapping suggestions generation"""
        result = await self.discovery_flow.generate_field_mapping_suggestions(
            previous_result
        )

        return PhaseExecutionResult(
            phase=FlowPhase.FIELD_MAPPING_SUGGESTIONS,
            status="completed",
            data={"result": result},
            next_phase=FlowPhase.FIELD_MAPPING_APPROVAL,  # Always move to approval
        )

    async def _execute_field_mapping_approval(
        self, previous_result
    ) -> PhaseExecutionResult:
        """Execute field mapping approval (pause for user input)"""
        result = await self.discovery_flow.pause_for_field_mapping_approval(
            previous_result
        )

        return PhaseExecutionResult(
            phase=FlowPhase.FIELD_MAPPING_APPROVAL,
            status="waiting_for_approval",
            data={"result": result},
            requires_user_input=True,  # This will pause the flow
            next_phase=FlowPhase.DATA_CLEANSING,  # Next phase after approval
        )

    async def _execute_data_cleansing(self, previous_result) -> PhaseExecutionResult:
        """Execute data cleansing phase"""
        # Check if we're resuming with user approval
        if isinstance(previous_result, dict) and previous_result.get(
            "approved_mappings"
        ):
            # Apply approved mappings first
            await self.discovery_flow.apply_approved_field_mappings(
                "field_mapping_approved"
            )
            result = await self.discovery_flow.execute_data_cleansing_agent(
                "field_mapping_approved"
            )
        else:
            result = await self.discovery_flow.execute_data_cleansing_agent(
                previous_result
            )

        return PhaseExecutionResult(
            phase=FlowPhase.DATA_CLEANSING,
            status="completed" if result != "data_cleansing_failed" else "failed",
            data={"result": result},
            next_phase=(
                FlowPhase.ASSET_INVENTORY if result != "data_cleansing_failed" else None
            ),
        )

    async def _execute_asset_inventory(self, previous_result) -> PhaseExecutionResult:
        """Execute asset inventory phase"""
        result = await self.discovery_flow.create_discovery_assets_from_cleaned_data(
            previous_result
        )

        return PhaseExecutionResult(
            phase=FlowPhase.ASSET_INVENTORY,
            status="completed" if result != "asset_inventory_failed" else "failed",
            data={"result": result},
            next_phase=(
                FlowPhase.DEPENDENCY_ANALYSIS
                if result != "asset_inventory_failed"
                else None
            ),
        )

    async def _execute_dependency_analysis(
        self, previous_result
    ) -> PhaseExecutionResult:
        """Execute dependency analysis phase"""
        # This will run parallel analysis (dependencies + tech debt)
        result = await self.discovery_flow.execute_parallel_analysis_agents(
            previous_result
        )

        return PhaseExecutionResult(
            phase=FlowPhase.DEPENDENCY_ANALYSIS,
            status="completed" if result == "parallel_analysis_completed" else "failed",
            data={"result": result},
            next_phase=(
                FlowPhase.TECH_DEBT_ASSESSMENT
                if result == "parallel_analysis_completed"
                else None
            ),
        )

    async def _execute_tech_debt_assessment(
        self, previous_result
    ) -> PhaseExecutionResult:
        """Execute tech debt assessment phase (already done in parallel)"""
        # This phase is completed as part of parallel analysis
        return PhaseExecutionResult(
            phase=FlowPhase.TECH_DEBT_ASSESSMENT,
            status="completed",
            data={"result": "tech_debt_completed"},
            next_phase=FlowPhase.FINALIZATION,
        )

    async def _execute_finalization(self, previous_result) -> PhaseExecutionResult:
        """Execute finalization phase"""
        result = await self.discovery_flow.check_user_approval_needed(previous_result)

        return PhaseExecutionResult(
            phase=FlowPhase.FINALIZATION,
            status=(
                "completed"
                if result == "discovery_completed"
                else "waiting_for_approval"
            ),
            data={"result": result},
            requires_user_input=result == "awaiting_user_approval_in_attribute_mapping",
        )

    def get_flow_status(self) -> Dict[str, Any]:
        """Get current flow status"""
        return {
            "current_phase": self.current_phase.value if self.current_phase else None,
            "execution_halted": self.execution_halted,
            "completed_phases": [phase.value for phase in self.phase_results.keys()],
            "total_phases": len(self.phase_sequence),
            "progress_percentage": (len(self.phase_results) / len(self.phase_sequence))
            * 100,
        }

    def is_waiting_for_user_input(self) -> bool:
        """Check if flow is currently waiting for user input"""
        return self.execution_halted and self.current_phase in [
            FlowPhase.FIELD_MAPPING_APPROVAL,
            FlowPhase.FINALIZATION,
        ]
