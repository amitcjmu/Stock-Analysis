"""
Unified Assessment Flow - Streamlined CrewAI Implementation

This module implements the main AssessmentFlow using CrewAI Flow patterns,
with phase handling delegated to modular helper classes for better maintainability.

The Assessment Flow evaluates applications selected from Discovery inventory and:
1. Captures architecture requirements at engagement level
2. Analyzes technical debt for each application component
3. Determines component-level 6R strategies
4. Generates comprehensive "App on a page" assessments
5. Provides input for Planning Flow wave grouping

Flow Phases:
- INITIALIZATION: Load selected applications and initialize flow state
- ARCHITECTURE_MINIMUMS: Capture/verify engagement architecture standards
- TECH_DEBT_ANALYSIS: Analyze components and technical debt
- COMPONENT_SIXR_STRATEGIES: Determine 6R strategy for each component
- APP_ON_PAGE_GENERATION: Generate comprehensive application assessments
- FINALIZATION: Mark applications ready for planning

Each phase includes pause points for user input and collaboration.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# Import database types for type hints
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Import models and dependencies (placed early per lint rules)
from app.core.context import RequestContext
from app.models.assessment_flow import (
    AssessmentFlowError,
    AssessmentFlowState,
    AssessmentFlowStatus,
    AssessmentPhase,
)
from app.services.crewai_flows.flow_state_manager import FlowStateManager
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore

# Import helper modules for modular organization
from .assessment_flow import (
    AssessmentDataAccessHelper,
    AssessmentPhaseHandlers,
)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from crewai.flow.flow import listen, start

    CREWAI_FLOW_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI Flow imports successful for AssessmentFlow")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI Flow not available for AssessmentFlow: {e}")

    # Fallback implementations
    class Flow:
        def __init__(self):
            self.state = None

        def __class_getitem__(cls, item):
            return cls

        def kickoff(self):
            return {}

    def listen(condition):
        def decorator(func):
            return func

        return decorator

    def start():
        def decorator(func):
            return func

        return decorator


class FlowContext:
    """Context information for the assessment flow."""

    def __init__(
        self,
        engagement_id: str,
        client_account_id: str,
        user_id: str,
        selected_applications: List[str] = None,
        flow_configuration: Dict[str, Any] = None,
    ):
        self.engagement_id = engagement_id
        self.client_account_id = client_account_id
        self.user_id = user_id
        self.selected_applications = selected_applications or []
        self.flow_configuration = flow_configuration or {}


class UnifiedAssessmentFlow(Flow[AssessmentFlowState]):
    """
    Unified Assessment Flow implementation using CrewAI Flow patterns.

    This flow evaluates applications selected from Discovery and generates
    comprehensive assessments including 6R strategies and technical debt analysis.
    """

    def __init__(
        self,
        context: RequestContext,
        db: "AsyncSession",  # FIX #812: Required for PostgresFlowStateStore
        flow_configuration: Dict[str, Any] = None,
        selected_applications: List[str] = None,
        master_flow_id: Optional[str] = None,
    ):
        # Validate required parameters (Qodo Bot feedback)
        if db is None:
            raise ValueError(
                "db session is required for UnifiedAssessmentFlow initialization"
            )
        if context is None:
            raise ValueError(
                "context is required for UnifiedAssessmentFlow initialization"
            )

        # Use master_flow_id if provided to preserve orchestration identity
        self.flow_id = str(master_flow_id) if master_flow_id else str(uuid.uuid4())
        self.context = context
        self.db = db  # FIX #812: Store db session for state persistence
        self.flow_configuration = flow_configuration or {}
        self.selected_applications = selected_applications or []
        self.master_flow_id = master_flow_id

        # Initialize flow state and components first
        self._initialize_components()

        # Initialize helper classes after state is ready
        self.data_helper = AssessmentDataAccessHelper(context, self.flow_id)
        self.phase_handlers = AssessmentPhaseHandlers(self)

        logger.info(
            f"✅ UnifiedAssessmentFlow initialized with flow_id: {self.flow_id}"
        )

    @property
    def flow_id(self):
        """Get the flow ID."""
        return self._flow_id

    @flow_id.setter
    def flow_id(self, value):
        """Set the flow ID."""
        self._flow_id = value

    def _initialize_components(self):
        """Initialize all flow components."""
        try:
            # Initialize state store
            # FIX #812: Pass db session and context to PostgresFlowStateStore
            # This was causing all assessment flows to crash during initialization
            self.state_store = PostgresFlowStateStore(db=self.db, context=self.context)

            # Initialize flow state manager
            self.flow_state_manager = FlowStateManager(
                store=self.state_store, context=self.context
            )

            # Initialize flow state
            self.state = AssessmentFlowState(
                flow_id=self.flow_id,
                engagement_id=self.context.engagement_id,
                client_account_id=self.context.client_account_id,
                master_flow_id=self.master_flow_id,
                status=AssessmentFlowStatus.INITIALIZED,
                current_phase=AssessmentPhase.INITIALIZATION,
            )

            # Store initial configuration
            self.state.configuration = self.flow_configuration
            self.state.metadata = {
                "created_by": self.context.user_id,
                "selected_applications": self.selected_applications,
                "flow_type": "assessment",
                "version": "2.0",
            }

            logger.info(f"✅ Flow components initialized for {self.flow_id}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize flow components: {str(e)}")
            raise AssessmentFlowError(f"Flow initialization failed: {str(e)}")

    @start()
    async def initialize_assessment(self):
        """Phase 1: Initialize the assessment flow."""
        return await self.phase_handlers.handle_initialization()

    @listen("user_confirms_architecture_standards")
    async def capture_architecture_minimums(self, previous_result):
        """Phase 2: Capture and validate architecture requirements."""
        return await self.phase_handlers.handle_architecture_minimums(previous_result)

    @listen("architecture_minimums_captured")
    async def analyze_technical_debt(self, previous_result):
        """Phase 3: Analyze technical debt across all applications."""
        return await self.phase_handlers.handle_technical_debt_analysis(previous_result)

    @listen("tech_debt_analysis_reviewed")
    async def determine_component_sixr_strategies(self, previous_result):
        """Phase 4: Determine 6R strategies for each component."""
        return await self.phase_handlers.handle_sixr_strategies(previous_result)

    @listen("sixr_strategies_reviewed")
    async def generate_app_on_page(self, previous_result):
        """Phase 5: Generate comprehensive "App on a Page" assessments."""
        return await self.phase_handlers.handle_app_on_page_generation(previous_result)

    @listen("app_on_page_generated")
    async def finalize_assessment(self, previous_result):
        """Phase 6: Finalize assessment and prepare for planning."""
        return await self.phase_handlers.handle_finalization(previous_result)

    async def resume_from_phase(
        self,
        target_phase: AssessmentPhase,
        user_input: Dict[str, Any] = None,
        force_restart: bool = False,
    ) -> Dict[str, Any]:
        """Resume or restart the flow from a specific phase."""
        logger.info(f"🔄 Resuming assessment flow from phase: {target_phase.value}")

        try:
            # Load existing state if not forcing restart
            if not force_restart:
                saved_state = await self.flow_state_manager.get_state(self.flow_id)
                if saved_state:
                    self.state = AssessmentFlowState.from_dict(saved_state)

            # Update state for resumption
            self.state.transition_to_phase(target_phase)
            self.state.status = AssessmentFlowStatus.PROCESSING

            # Route to appropriate phase method
            phase_methods = {
                AssessmentPhase.INITIALIZATION: self.initialize_assessment,
                AssessmentPhase.ARCHITECTURE_MINIMUMS: lambda: self.capture_architecture_minimums(
                    {"user_input": user_input}
                ),
                AssessmentPhase.TECH_DEBT_ANALYSIS: lambda: self.analyze_technical_debt(
                    {}
                ),
                AssessmentPhase.COMPONENT_SIXR_STRATEGIES: lambda: self.determine_component_sixr_strategies(
                    {"user_input": user_input}
                ),
                AssessmentPhase.APP_ON_PAGE_GENERATION: lambda: self.generate_app_on_page(
                    {}
                ),
                AssessmentPhase.FINALIZATION: lambda: self.finalize_assessment({}),
            }

            phase_method = phase_methods.get(target_phase)
            if phase_method:
                return await phase_method()
            else:
                raise AssessmentFlowError(f"Unknown phase: {target_phase}")

        except Exception as e:
            logger.error(f"❌ Failed to resume from phase {target_phase}: {str(e)}")
            raise


# Factory function
def create_unified_assessment_flow(
    context: RequestContext,
    db: "AsyncSession",  # FIX #812: Required for PostgresFlowStateStore
    flow_configuration: Dict[str, Any] = None,
    selected_applications: List[str] = None,
    master_flow_id: Optional[str] = None,
) -> UnifiedAssessmentFlow:
    """
    Create a new UnifiedAssessmentFlow instance.

    Args:
        context: Request context with engagement and user information
        db: Database session for state persistence
        flow_configuration: Flow-specific configuration
        selected_applications: List of application IDs to assess
        master_flow_id: ID of the master flow for MFO integration

    Returns:
        Configured UnifiedAssessmentFlow instance
    """
    logger.info("🏗️  Creating new UnifiedAssessmentFlow")

    return UnifiedAssessmentFlow(
        context=context,
        db=db,
        flow_configuration=flow_configuration,
        selected_applications=selected_applications,
        master_flow_id=master_flow_id,
    )
