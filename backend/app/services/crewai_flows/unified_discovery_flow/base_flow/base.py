"""
Base Flow Class - Core UnifiedDiscoveryFlow Implementation

Contains the core UnifiedDiscoveryFlow class with initialization and property definitions.
"""

import logging
import uuid

from app.core.context import RequestContext
from app.core.security.cache_encryption import secure_setattr
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# CrewAI Flow imports - REAL AGENTS ONLY
try:
    from crewai import Flow

    CREWAI_FLOW_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ CrewAI Flow not available: {e}")
    logger.error("❌ CRITICAL: Cannot proceed without real CrewAI agents")
    raise ImportError(f"CrewAI is required for real agent execution: {e}")

# Import mixins
from .flow_initialization import FlowInitializationMethods
from .flow_execution import FlowExecutionMethods
from .phase_handlers import PhaseHandlerMethods
from .state_management import StateManagementMethods

logger = logging.getLogger(__name__)

# Verify we're not using pseudo-agents
if not CREWAI_FLOW_AVAILABLE:
    raise RuntimeError(
        "❌ CRITICAL: Pseudo-agent fallback detected - real CrewAI required"
    )

logger.info("✅ CrewAI Flow imports successful - REAL AGENTS ENABLED")


class UnifiedDiscoveryFlow(
    Flow,
    FlowInitializationMethods,
    FlowExecutionMethods,
    PhaseHandlerMethods,
    StateManagementMethods,
):
    """
    Unified Discovery Flow with PostgreSQL-only persistence.
    Single source of truth for all discovery flow operations.

    This modularized version splits the monolithic flow into:
    - Configuration (flow_config.py)
    - State management (state_management.py)
    - Crew coordination (crew_coordination.py)
    - Phase handlers (phase_handlers.py)
    - Data utilities (data_utilities.py)
    - Notification utilities (notification_utilities.py)
    """

    def __init__(self, crewai_service, context: RequestContext, **kwargs):
        """Initialize unified discovery flow with agent-first architecture"""

        # Initialize flow_id early to avoid attribute errors
        self._flow_id = kwargs.get("flow_id") or str(uuid.uuid4())

        # PHASE 2 FIX: Store master_flow_id if provided
        self._master_flow_id = kwargs.get("master_flow_id")
        if self._master_flow_id:
            logger.info(
                f"🔗 UnifiedDiscoveryFlow initialized with master_flow_id: {self._master_flow_id}"
            )

        # Store context and service BEFORE calling super().__init__()
        # This is critical because the base class initialization may access properties
        self.crewai_service = crewai_service
        self.context = context

        # Initialize base CrewAI Flow - REAL AGENTS ONLY
        super().__init__()
        logger.info("✅ CrewAI Flow base class initialized - real agents active")

        logger.info(
            "🚀 Initializing Unified Discovery Flow with Agent-First Architecture"
        )

        # Use initializer for setup
        from ..flow_initialization import FlowInitializer

        self.initializer = FlowInitializer(crewai_service, context, **kwargs)
        self._init_context = self.initializer.init_context

        # Initialize flow state - CrewAI Flow manages state internally
        # CrewAI Flow base class manages state - we'll configure it in initialize_discovery
        logger.info("🔄 Flow state will be managed by CrewAI Flow base class")

        # Initialize components
        self._initialize_components()

        # Initialize phase handlers
        self._initialize_phases()

        # Initialize modular utilities
        self._initialize_utilities()

        # Initialize defensive method resolver for robust method calls
        from ..defensive_method_resolver import create_method_resolver

        self._method_resolver = create_method_resolver(self)
        logger.info("🛡️ Defensive method resolver initialized")

        # Flow ID already set in __init__
        logger.info(f"✅ Unified Discovery Flow initialized - Flow ID: {self._flow_id}")

    @property
    def flow_id(self):
        """Get the flow ID"""
        return self._flow_id

    @property
    def master_flow_id(self):
        """Get the master flow ID"""
        return getattr(self, "_master_flow_id", None)

    @property
    def state(self):
        """Get the flow state - always return our managed state"""
        # Always return the internal flow state if available
        if hasattr(self, "_flow_state") and self._flow_state:
            return self._flow_state

        # If we don't have _flow_state yet, create a default with proper IDs
        # This should only happen during initialization
        default_state = UnifiedDiscoveryFlowState()
        if hasattr(self, "_flow_id"):
            default_state.flow_id = self._flow_id
        if hasattr(self, "context") and self.context:
            default_state.client_account_id = (
                str(self.context.client_account_id)
                if self.context.client_account_id
                else ""
            )
            default_state.engagement_id = (
                str(self.context.engagement_id) if self.context.engagement_id else ""
            )
            default_state.user_id = (
                str(self.context.user_id) if self.context.user_id else ""
            )

        # Store it as _flow_state for consistency
        self._flow_state = default_state
        return self._flow_state

    def _ensure_state_ids(self):
        """Ensure state has all required IDs - call this at the start of each phase"""
        # Check if state exists
        if not hasattr(self, "state") or not self.state:
            logger.warning("⚠️ State not available in _ensure_state_ids - skipping")
            return

        # Force set the IDs every time, don't just check if they're missing
        old_flow_id = getattr(self.state, "flow_id", None)
        self.state.flow_id = self._flow_id

        if old_flow_id != self._flow_id:
            logger.info(
                f"🔧 Flow ID updated in state: {old_flow_id} -> {self._flow_id}"
            )

        if self.context:
            self.state.client_account_id = (
                str(self.context.client_account_id)
                if self.context.client_account_id
                else ""
            )
            self.state.engagement_id = (
                str(self.context.engagement_id) if self.context.engagement_id else ""
            )
            self.state.user_id = (
                str(self.context.user_id) if self.context.user_id else ""
            )

    def _initialize_components(self):
        """Initialize core components"""
        # Initialize managers
        from ..state_management import StateManager

        self.state_manager = StateManager(self.state)

        # Initialize unified flow management for lifecycle operations
        from ...handlers.unified_flow_management import UnifiedFlowManagement

        self.unified_flow_management = UnifiedFlowManagement(self.state)

        # Initialize UnifiedFlowCrewManager instead of CrewCoordinator
        from ...handlers.unified_flow_crew_manager import UnifiedFlowCrewManager

        self.crew_manager = UnifiedFlowCrewManager(
            self.crewai_service, self.state, callback_handler=None, context=self.context
        )
        # Keep coordinator as alias for backward compatibility
        self.coordinator = self.crew_manager

        from ..flow_management import FlowManager
        from ..flow_finalization import FlowFinalizer

        self.flow_manager = FlowManager(
            self.state, self.state_manager, self.unified_flow_management
        )
        self.finalizer = FlowFinalizer(self.state, self.state_manager)

        # Initialize bridge for flow-specific database operations
        from ...flow_state_bridge import FlowStateBridge

        self.flow_bridge = FlowStateBridge(self.context)

        # Get agents from the service
        agents = self.crewai_service.get_agents()

        # Store agents for easy access
        self.orchestrator = agents["orchestrator"]
        self.data_validation_agent = agents["data_validation_agent"]
        self.attribute_mapping_agent = agents["attribute_mapping_agent"]
        self.data_cleansing_agent = agents["data_cleansing_agent"]
        self.asset_inventory_agent = agents["asset_inventory_agent"]
        self.dependency_analysis_agent = agents["dependency_analysis_agent"]
        self.tech_debt_analysis_agent = agents["tech_debt_analysis_agent"]

    def _initialize_phases(self):
        """Initialize phase handlers"""
        # Import phase executors
        from ..handlers.phase_executors import (
            AssetInventoryExecutor,
            DataCleansingExecutor,
            DataImportValidationExecutor,
            DependencyAnalysisExecutor,
            FieldMappingExecutor,
            TechDebtExecutor,
        )

        # Keep the existing UnifiedFlowCrewManager - don't overwrite it
        # self.crew_manager is already initialized in _initialize_components()

        # Note: We'll initialize the actual phase executors later when state is available
        # For now, store the executor classes
        self._phase_executor_classes = {
            "data_validation_phase": DataImportValidationExecutor,
            "field_mapping_phase": FieldMappingExecutor,
            "data_cleansing_phase": DataCleansingExecutor,
            "asset_inventory_phase": AssetInventoryExecutor,
            "dependency_analysis_phase": DependencyAnalysisExecutor,
            "tech_debt_assessment_phase": TechDebtExecutor,
        }

        # Create placeholder phases that will be initialized with state later
        self.data_validation_phase = None
        self.field_mapping_phase = None
        self.data_cleansing_phase = None
        self.asset_inventory_phase = None
        self.dependency_analysis_phase = None
        self.tech_debt_assessment_phase = None

    def _initialize_phase_executors_with_state(self):
        """Initialize phase executors with the actual state once it's available"""
        if not hasattr(self, "_flow_state") or not self._flow_state:
            raise RuntimeError("Cannot initialize phase executors without state")

        if not hasattr(self, "crew_manager") or not self.crew_manager:
            raise RuntimeError("Cannot initialize phase executors without crew manager")

        # Initialize all phase executors with state using a mapping
        phase_mappings = {
            "data_validation_phase": "data_validation_phase",
            "field_mapping_phase": "field_mapping_phase",
            "data_cleansing_phase": "data_cleansing_phase",
            "asset_inventory_phase": "asset_inventory_phase",
            "dependency_analysis_phase": "dependency_analysis_phase",
            "tech_debt_assessment_phase": "tech_debt_assessment_phase",
        }

        # Initialize each phase executor with common parameters
        for attr_name, phase_key in phase_mappings.items():
            if phase_key not in self._phase_executor_classes:
                raise RuntimeError(f"Phase executor class not found for {phase_key}")

            executor_class = self._phase_executor_classes[phase_key]
            executor_instance = executor_class(
                self._flow_state, self.crew_manager, self.flow_bridge
            )
            secure_setattr(self, attr_name, executor_instance)

        logger.info("✅ Phase executors initialized with state and crew manager")

    def _initialize_utilities(self):
        """Initialize modular utility classes"""
        from ..phase_handlers import PhaseHandlers
        from ..data_utilities import DataUtilities
        from ..notification_utilities import NotificationUtilities

        self.phase_handlers = PhaseHandlers(self)
        self.data_utils = DataUtilities(self)
        self.notification_utils = NotificationUtilities(self)
