"""
Unified Collection Flow - CrewAI Implementation

This module implements the main CollectionFlow using CrewAI Flow patterns,
following the same architecture as UnifiedDiscoveryFlow with PostgreSQL-only
persistence.

The Collection Flow handles adaptive data collection for migration readiness and:
1. Detects platforms in the environment
2. Performs automated data collection using platform adapters
3. Analyzes gaps in collected data
4. Generates adaptive questionnaires for manual collection
5. Synthesizes and validates all collected data

Flow Phases:
- INITIALIZATION: Setup flow state and load configuration
- PLATFORM_DETECTION: Detect and identify platforms in the environment
- AUTOMATED_COLLECTION: Automated data collection via adapters
- GAP_ANALYSIS: Analyze data completeness and quality gaps
- QUESTIONNAIRE_GENERATION: Generate adaptive questionnaires for gaps
- MANUAL_COLLECTION: Collect data through manual processes
- DATA_VALIDATION: Validate all collected data
- FINALIZATION: Prepare data for Discovery Flow handoff

Each phase includes pause points for user input and collaboration.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

# CrewAI Flow imports - REQUIRED for real agent execution
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from crewai.flow.flow import listen, or_, start

    CREWAI_FLOW_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info(
        "✅ CrewAI Flow imports successful for CollectionFlow - REAL AGENTS ENABLED"
    )
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ CrewAI Flow not available for CollectionFlow: {e}")
    logger.error("❌ CRITICAL: Cannot proceed without real CrewAI agents")
    raise ImportError(
        f"CrewAI is required for real agent execution in CollectionFlow: {e}"
    )

# Import models and dependencies
from app.core.context import RequestContext  # noqa: E402
from app.models.collection_flow import (  # noqa: E402
    AutomationTier,
    CollectionFlowError,
    CollectionFlowState,
    CollectionPhase,
    CollectionStatus,
)
from app.services.crewai_flows.flow_state_manager import FlowStateManager  # noqa: E402

# Import handlers and utilities
from app.services.crewai_flows.handlers.unified_flow_management import (  # noqa: E402
    UnifiedFlowManagement,
)

# Import modularized components
from app.services.crewai_flows.unified_collection_flow_modules import (  # noqa: E402
    AutomatedCollectionHandler,
    FinalizationHandler,
    FlowContext,
    GapAnalysisHandler,
    InitializationHandler,
    ManualCollectionHandler,
    PlatformDetectionHandler,
    QuestionnaireGenerationHandler,
    ServiceInitializer,
    ValidationHandler,
    get_previous_phase,
)


class UnifiedCollectionFlow(Flow[CollectionFlowState]):
    """
    Unified Collection Flow with PostgreSQL-only persistence.

    This CrewAI Flow orchestrates the adaptive data collection process,
    integrating automated and manual collection methods with intelligent gap analysis.

    Follows the same patterns as UnifiedDiscoveryFlow:
    - PostgreSQL-only state management
    - Multi-tenant context preservation
    - Pause/resume functionality at each phase
    - True CrewAI agents for intelligence
    - Error handling and recovery
    """

    def __init__(
        self,
        crewai_service,
        context: RequestContext,
        automation_tier: str = "tier_2",
        **kwargs,
    ):
        """Initialize unified collection flow"""
        logger.info("🚀 Initializing Unified Collection Flow with CrewAI Agents")

        # Store core attributes BEFORE calling super().__init__()
        # because CrewAI Flow.__init__ may access properties
        self.crewai_service = crewai_service
        self.context = context
        self.automation_tier = AutomationTier(automation_tier)
        self._flow_id = kwargs.get("flow_id") or str(uuid.uuid4())
        self._master_flow_id = kwargs.get("master_flow_id")
        self._discovery_flow_id = kwargs.get("discovery_flow_id")

        # Initialize base CrewAI Flow after setting attributes
        super().__init__()

        # Initialize flow context
        self.flow_context = FlowContext(
            flow_id=self._flow_id,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            user_id=str(context.user_id) if context.user_id else None,
            db_session=kwargs.get("db_session"),
        )

        # Initialize flow state - CrewAI Flow manages state internally
        # We'll use _flow_state for our internal state management
        self._flow_state = CollectionFlowState(
            flow_id=self._flow_id,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            user_id=str(context.user_id) if context.user_id else None,
            discovery_flow_id=self._discovery_flow_id,
            automation_tier=self.automation_tier,
            current_phase=CollectionPhase.INITIALIZATION,
            status=CollectionStatus.INITIALIZING,
        )

        # Initialize services
        self.services = ServiceInitializer(self.flow_context.db_session, context)

        # Initialize state manager
        self.state_manager = FlowStateManager(self.flow_context.db_session, context)

        # Initialize unified flow management
        self.unified_flow_management = UnifiedFlowManagement(self._flow_state)

        # Store configuration
        self.config = kwargs.get("config", {})
        self.environment_config = self.config.get("environment_config", {})
        self.client_requirements = self.config.get("client_requirements", {})

        # Initialize phase handlers
        self._init_phase_handlers()

        logger.info(f"✅ Collection Flow initialized - Flow ID: {self._flow_id}")

    def _init_phase_handlers(self):
        """Initialize all phase handlers"""
        self.initialization_handler = InitializationHandler(
            self.flow_context,
            self.state_manager,
            self.services,
            self.unified_flow_management,
        )
        self.platform_detection_handler = PlatformDetectionHandler(
            self.flow_context,
            self.state_manager,
            self.services,
            self.unified_flow_management,
            self.crewai_service,
        )
        self.automated_collection_handler = AutomatedCollectionHandler(
            self.flow_context, self.state_manager, self.services, self.crewai_service
        )
        self.gap_analysis_handler = GapAnalysisHandler(
            self.flow_context, self.state_manager, self.services, self.crewai_service
        )
        self.questionnaire_generation_handler = QuestionnaireGenerationHandler(
            self.flow_context,
            self.state_manager,
            self.services,
            self.unified_flow_management,
        )
        self.manual_collection_handler = ManualCollectionHandler(
            self.flow_context, self.state_manager, self.services, self.crewai_service
        )
        self.validation_handler = ValidationHandler(
            self.flow_context, self.state_manager, self.services, self.crewai_service
        )
        self.finalization_handler = FinalizationHandler(
            self.flow_context,
            self.state_manager,
            self.services,
            self.unified_flow_management,
        )

    @property
    def flow_id(self):
        """Get the flow ID"""
        return self._flow_id

    @property
    def state(self):
        """Get the flow state - always return our managed state"""
        # Always return the internal flow state if available
        if hasattr(self, "_flow_state") and self._flow_state:
            return self._flow_state

        # If we don't have _flow_state yet, create a default with proper IDs
        # This should only happen during initialization
        flow_id = getattr(self, "_flow_id", str(uuid.uuid4()))
        client_account_id = ""
        engagement_id = ""
        user_id = ""

        if hasattr(self, "context") and self.context:
            client_account_id = (
                str(self.context.client_account_id)
                if self.context.client_account_id
                else ""
            )
            engagement_id = (
                str(self.context.engagement_id) if self.context.engagement_id else ""
            )
            user_id = str(self.context.user_id) if self.context.user_id else ""

        default_state = CollectionFlowState(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
            automation_tier=getattr(self, "automation_tier", AutomationTier.TIER_2),
            current_phase=CollectionPhase.INITIALIZATION,
            status=CollectionStatus.INITIALIZING,
        )

        # Store it as _flow_state for consistency
        self._flow_state = default_state
        return self._flow_state

    @start()
    async def initialize_collection(self):
        """Initialize the collection flow"""
        config = {
            "client_requirements": self.client_requirements,
            "environment_config": self.environment_config,
            "master_flow_id": self._master_flow_id,
            "discovery_flow_id": self._discovery_flow_id,
        }
        return await self.initialization_handler.initialize_collection(
            self.state, config
        )

    @listen("initialization")
    async def detect_platforms(self, initialization_result):
        """Phase 1: Detect platforms in the environment"""
        config = {
            "client_requirements": self.client_requirements,
            "environment_config": self.environment_config,
        }
        return await self.platform_detection_handler.detect_platforms(
            self.state, config, initialization_result
        )

    @listen("platform_detection")
    async def automated_collection(self, platform_result):
        """Phase 2: Automated data collection"""
        config = {
            "client_requirements": self.client_requirements,
            "environment_config": self.environment_config,
        }
        return await self.automated_collection_handler.automated_collection(
            self.state, config, platform_result
        )

    @listen("automated_collection")
    async def analyze_gaps(self, collection_result):
        """Phase 3: Gap analysis"""
        config = {
            "client_requirements": self.client_requirements,
            "environment_config": self.environment_config,
        }
        return await self.gap_analysis_handler.analyze_gaps(
            self.state, config, collection_result
        )

    @listen("gap_analysis")
    async def generate_questionnaires(self, gap_result):
        """Phase 4: Generate adaptive questionnaires"""
        config = {
            "client_requirements": self.client_requirements,
            "environment_config": self.environment_config,
        }
        result = await self.questionnaire_generation_handler.generate_questionnaires(
            self.state, config, gap_result
        )
        # If handler returns None, skip to validation
        if result is None:
            return await self.validate_data(gap_result)
        return result

    @listen("questionnaire_generation")
    async def manual_collection(self, questionnaire_result):
        """Phase 5: Manual data collection"""
        config = {
            "client_requirements": self.client_requirements,
            "environment_config": self.environment_config,
        }
        return await self.manual_collection_handler.manual_collection(
            self.state, config, questionnaire_result
        )

    @listen(or_("manual_collection", "gap_analysis"))
    async def validate_data(self, previous_result):
        """Phase 6: Data validation and synthesis"""
        config = {
            "client_requirements": self.client_requirements,
            "environment_config": self.environment_config,
        }
        return await self.validation_handler.validate_data(
            self.state, config, previous_result
        )

    @listen("data_validation")
    async def finalize_collection(self, validation_result):
        """Phase 7: Finalize collection and prepare for handoff"""
        config = {
            "client_requirements": self.client_requirements,
            "environment_config": self.environment_config,
            "master_flow_id": self._master_flow_id,
            "discovery_flow_id": self._discovery_flow_id,
        }
        return await self.finalization_handler.finalize_collection(
            self.state, config, validation_result
        )

    async def resume_flow(self, user_inputs: Optional[Dict[str, Any]] = None):
        """Resume flow after pause"""
        if user_inputs:
            self.state.user_inputs.update(user_inputs)
            self.state.last_user_interaction = datetime.utcnow()

        # Resume based on current phase
        phase_handlers = {
            CollectionPhase.INITIALIZATION: self.initialize_collection,
            CollectionPhase.PLATFORM_DETECTION: self.detect_platforms,
            CollectionPhase.AUTOMATED_COLLECTION: self.automated_collection,
            CollectionPhase.GAP_ANALYSIS: self.analyze_gaps,
            CollectionPhase.QUESTIONNAIRE_GENERATION: self.generate_questionnaires,
            CollectionPhase.MANUAL_COLLECTION: self.manual_collection,
            CollectionPhase.DATA_VALIDATION: self.validate_data,
            CollectionPhase.FINALIZATION: self.finalize_collection,
        }

        handler = phase_handlers.get(self.state.current_phase)
        if handler:
            # Get previous phase result
            previous_phase = get_previous_phase(self.state.current_phase)
            previous_result = (
                self.state.phase_results.get(previous_phase.value, {})
                if previous_phase
                else {}
            )
            return await handler(previous_result)

        raise CollectionFlowError(f"No handler for phase: {self.state.current_phase}")


def create_unified_collection_flow(
    crewai_service, context: RequestContext, automation_tier: str = "tier_2", **kwargs
) -> UnifiedCollectionFlow:
    """Factory function to create a unified collection flow"""
    return UnifiedCollectionFlow(
        crewai_service=crewai_service,
        context=context,
        automation_tier=automation_tier,
        **kwargs,
    )


# Re-export for backward compatibility
__all__ = [
    "UnifiedCollectionFlow",
    "create_unified_collection_flow",
    "FlowContext",  # Export FlowContext for backward compatibility
]
