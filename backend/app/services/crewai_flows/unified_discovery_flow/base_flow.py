"""
Base Flow Module - Modularized Version

The main UnifiedDiscoveryFlow class that orchestrates all phases.
This modularized version extracts large methods into separate utility classes
for better maintainability and code organization.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

# CrewAI Flow imports - REAL AGENTS ONLY
logger = logging.getLogger(__name__)

try:
    from crewai import Flow
    from crewai.flow.flow import listen, start
    from crewai.flow.persistence import persist

    CREWAI_FLOW_AVAILABLE = True
    logger.info("✅ CrewAI Flow imports successful - REAL AGENTS ENABLED")
except ImportError as e:
    logger.error(f"❌ CrewAI Flow not available: {e}")
    logger.error("❌ CRITICAL: Cannot proceed without real CrewAI agents")
    raise ImportError(f"CrewAI is required for real agent execution: {e}")

# Verify we're not using pseudo-agents
if not CREWAI_FLOW_AVAILABLE:
    raise RuntimeError(
        "❌ CRITICAL: Pseudo-agent fallback detected - real CrewAI required"
    )

# Import state and configuration
from app.core.context import RequestContext
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# Import enhanced error handling and monitoring
# Import handlers for flow management
from .crew_coordination import CrewCoordinator
from .data_utilities import DataUtilities
from .flow_finalization import FlowFinalizer
from .flow_initialization import FlowInitializer
from .flow_management import FlowManager
from .notification_utilities import NotificationUtilities
# Import modular utilities
from .phase_handlers import PhaseHandlers
from .state_management import StateManager


class UnifiedDiscoveryFlow(Flow):
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
        self.state_manager = StateManager(self.state)

        # Initialize unified flow management for lifecycle operations
        from ..handlers.unified_flow_management import UnifiedFlowManagement

        self.unified_flow_management = UnifiedFlowManagement(self.state)

        self.coordinator = CrewCoordinator(self.crewai_service, self.context)
        self.flow_manager = FlowManager(
            self.state, self.state_manager, self.unified_flow_management
        )
        self.finalizer = FlowFinalizer(self.state, self.state_manager)

        # Initialize bridge for flow-specific database operations
        from ..bridges.flow_state_bridge import FlowStateBridge

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
        # Create agents dict for phase initialization
        agents = {
            "data_validation_agent": self.data_validation_agent,
            "attribute_mapping_agent": self.attribute_mapping_agent,
            "data_cleansing_agent": self.data_cleansing_agent,
            "asset_inventory_agent": self.asset_inventory_agent,
            "dependency_analysis_agent": self.dependency_analysis_agent,
            "tech_debt_analysis_agent": self.tech_debt_analysis_agent,
        }

        # Initialize phases (will use state when available)
        phases = self.initializer.initialize_phases(None, agents, self.flow_bridge)

        self.data_validation_phase = phases["data_validation_phase"]
        self.field_mapping_phase = phases["field_mapping_phase"]
        self.data_cleansing_phase = phases["data_cleansing_phase"]
        self.asset_inventory_phase = phases["asset_inventory_phase"]
        self.dependency_analysis_phase = phases["dependency_analysis_phase"]
        self.tech_debt_assessment_phase = phases["tech_debt_assessment_phase"]

    def _initialize_utilities(self):
        """Initialize modular utility classes"""
        self.phase_handlers = PhaseHandlers(self)
        self.data_utils = DataUtilities(self)
        self.notification_utils = NotificationUtilities(self)

    # ========================================
    # CREWAI FLOW METHODS (@start and @listen)
    # ========================================

    @start()
    async def initialize_discovery(self):
        """Initialize the discovery flow"""
        logger.info(
            f"🎯 [ECHO] Starting Unified Discovery Flow - @start method called for flow {self._flow_id}"
        )

        # Update status to running immediately
        await self.notification_utils.update_flow_status("processing")

        # Send real-time update via agent-ui-bridge
        await self.notification_utils.send_flow_start_notification()

        try:
            # Initialize state using CrewAI Flow's built-in state management
            existing_state = None
            if hasattr(self, "_flow_id") and self._flow_id and self.flow_bridge:
                logger.info(
                    f"🔍 Checking for existing flow state in database for flow {self._flow_id}"
                )
                try:
                    existing_state = await self.flow_bridge.recover_flow_state(
                        self._flow_id
                    )
                    if existing_state:
                        logger.info(
                            f"🔄 Recovered existing state for flow {self._flow_id}"
                        )
                        self._flow_state = existing_state
                    else:
                        logger.info(
                            f"🆕 No existing state found, creating new state for flow {self._flow_id}"
                        )
                except Exception as recovery_error:
                    logger.warning(
                        f"⚠️ State recovery failed: {recovery_error}, creating new state"
                    )

            # Ensure we have a flow state
            if not hasattr(self, "_flow_state") or not self._flow_state:
                self._flow_state = UnifiedDiscoveryFlowState()
                logger.info("🆕 Created new flow state")

            # Ensure state has proper IDs
            self._ensure_state_ids()

            # Initialize state with basic flow information
            self._flow_state.status = "processing"
            self._flow_state.current_phase = "initialization"
            self._flow_state.initialized_at = datetime.now()

            # Load raw data if not already loaded
            if (
                not hasattr(self._flow_state, "raw_data")
                or not self._flow_state.raw_data
            ):
                await self.data_utils.load_raw_data_from_database(self._flow_state)

            # Save initial state to database
            if self.flow_bridge:
                await self.flow_bridge.save_flow_state(self._flow_id, self._flow_state)
                logger.info("💾 Saved initial flow state to database")

            logger.info(
                "✅ Discovery flow initialization completed - triggering data validation"
            )
            return {
                "status": "initialized",
                "flow_id": self._flow_id,
                "message": "Discovery flow initialized successfully",
                "next_phase": "data_validation",
            }

        except Exception as e:
            logger.error(f"❌ Flow initialization failed: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "initialization"
            )
            raise

    @listen(initialize_discovery)
    async def execute_data_import_validation_agent(self, initialization_result):
        """Execute the data import validation phase"""
        logger.info(
            f"🔍 [ECHO] Data validation phase triggered for flow {self._flow_id}"
        )

        try:
            # Ensure state IDs are correct
            self._ensure_state_ids()

            # Use phase handler for data validation
            validation_result = (
                await self.phase_handlers.execute_data_import_validation()
            )

            logger.info("✅ Data validation completed - triggering field mapping")
            return validation_result

        except Exception as e:
            logger.error(f"❌ Data validation phase failed: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "data_validation"
            )
            raise

    @listen(execute_data_import_validation_agent)
    async def generate_field_mapping_suggestions(self, data_validation_agent_result):
        """Generate field mapping suggestions"""
        logger.info(f"🗺️ [ECHO] Field mapping phase triggered for flow {self._flow_id}")

        try:
            # Ensure state IDs are correct
            self._ensure_state_ids()

            # Use phase handler for field mapping
            mapping_result = (
                await self.phase_handlers.generate_field_mapping_suggestions(
                    data_validation_agent_result
                )
            )

            # Send approval request notification
            await self.notification_utils.send_approval_request_notification(
                mapping_result
            )

            logger.info("✅ Field mapping suggestions generated - awaiting approval")
            return mapping_result

        except Exception as e:
            logger.error(f"❌ Field mapping phase failed: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "field_mapping"
            )
            raise

    @listen(generate_field_mapping_suggestions)
    async def pause_for_field_mapping_approval(self, field_mapping_suggestions_result):
        """Pause for field mapping approval"""
        logger.info(
            f"⏸️ [ECHO] Pausing for field mapping approval for flow {self._flow_id}"
        )

        try:
            # Update status
            await self.notification_utils.update_flow_status("awaiting_approval")

            # Return pause indicator
            return {
                "status": "awaiting_approval",
                "phase": "field_mapping_approval",
                "flow_id": self._flow_id,
                "mapping_suggestions": field_mapping_suggestions_result,
                "message": "Flow paused for field mapping approval",
            }

        except Exception as e:
            logger.error(f"❌ Failed to pause for approval: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "field_mapping_approval"
            )
            raise

    @listen(pause_for_field_mapping_approval)
    async def apply_approved_field_mappings(self, field_mapping_approval_result):
        """Apply approved field mappings"""
        logger.info(
            f"✅ [ECHO] Applying approved field mappings for flow {self._flow_id}"
        )

        try:
            # Ensure state IDs are correct
            self._ensure_state_ids()

            # Use phase handler for mapping application
            mapping_application_result = (
                await self.phase_handlers.apply_approved_field_mappings(
                    field_mapping_approval_result
                )
            )

            logger.info("✅ Field mappings applied - triggering data cleansing")
            return mapping_application_result

        except Exception as e:
            logger.error(f"❌ Field mapping application failed: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "mapping_application"
            )
            raise

    @listen(apply_approved_field_mappings)
    async def execute_data_cleansing_agent(self, mapping_application_result):
        """Execute data cleansing phase"""
        logger.info(
            f"🧹 [ECHO] Data cleansing phase triggered for flow {self._flow_id}"
        )

        try:
            # Ensure state IDs are correct
            self._ensure_state_ids()

            # Use phase handler for data cleansing
            cleansing_result = await self.phase_handlers.execute_data_cleansing(
                mapping_application_result
            )

            logger.info("✅ Data cleansing completed - creating discovery assets")
            return cleansing_result

        except Exception as e:
            logger.error(f"❌ Data cleansing phase failed: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "data_cleansing"
            )
            raise

    @listen(execute_data_cleansing_agent)
    async def create_discovery_assets_from_cleaned_data(self, data_cleansing_result):
        """Create discovery assets from cleaned data"""
        logger.info(f"📦 [ECHO] Creating discovery assets for flow {self._flow_id}")

        try:
            # Ensure state IDs are correct
            self._ensure_state_ids()

            # Use phase handler for asset creation
            asset_creation_result = await self.phase_handlers.create_discovery_assets(
                data_cleansing_result
            )

            logger.info("✅ Discovery assets created - promoting to assets")
            return asset_creation_result

        except Exception as e:
            logger.error(f"❌ Asset creation phase failed: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "asset_creation"
            )
            raise

    @listen(create_discovery_assets_from_cleaned_data)
    async def promote_discovery_assets_to_assets(self, asset_creation_result):
        """Promote discovery assets to full assets"""
        logger.info(
            f"⬆️ [ECHO] Promoting discovery assets to assets for flow {self._flow_id}"
        )

        try:
            # Simple promotion logic - this could be more complex
            asset_promotion_result = {
                "status": "success",
                "promoted_assets": asset_creation_result.get("assets_created", []),
                "promotion_timestamp": datetime.now().isoformat(),
            }

            await self.notification_utils.send_progress_update(
                80, "asset_promotion", "Assets promoted successfully"
            )

            logger.info("✅ Assets promoted - starting parallel analysis")
            return asset_promotion_result

        except Exception as e:
            logger.error(f"❌ Asset promotion failed: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "asset_promotion"
            )
            raise

    @listen(promote_discovery_assets_to_assets)
    async def execute_parallel_analysis_agents(self, asset_promotion_result):
        """Execute parallel analysis phases"""
        logger.info(f"🔄 [ECHO] Starting parallel analysis for flow {self._flow_id}")

        try:
            # Ensure state IDs are correct
            self._ensure_state_ids()

            # Use phase handler for parallel analysis
            analysis_result = await self.phase_handlers.execute_parallel_analysis(
                asset_promotion_result
            )

            # Mark flow as completed
            await self.notification_utils.update_flow_status("completed")

            # Send completion notification
            final_result = {
                "status": "completed",
                "flow_id": self._flow_id,
                "analysis_result": analysis_result,
                "completion_timestamp": datetime.now().isoformat(),
            }

            await self.notification_utils.send_flow_completion_notification(
                final_result
            )

            logger.info("✅ Discovery flow completed successfully")
            return final_result

        except Exception as e:
            logger.error(f"❌ Parallel analysis phase failed: {e}")
            await self.notification_utils.send_error_notification(
                str(e), "parallel_analysis"
            )
            raise

    # ========================================
    # FLOW MANAGEMENT METHODS
    # ========================================

    async def pause_flow(self, reason: Optional[str] = None):
        """Pause the flow"""
        return await self.flow_manager.pause_flow(reason)

    async def resume_flow_from_state(self, resume_context: Dict[str, Any]):
        """Resume flow from saved state"""
        return await self.flow_manager.resume_flow_from_state(resume_context)

    def get_flow_info(self) -> Dict[str, Any]:
        """Get comprehensive flow information"""
        return self.flow_manager.get_flow_info()

    # Delegate data loading to utility class
    async def _load_raw_data_from_database(self, state: UnifiedDiscoveryFlowState):
        """Load raw data from database tables into flow state"""
        return await self.data_utils.load_raw_data_from_database(state)


def create_unified_discovery_flow(
    crewai_service,
    context: RequestContext,
    flow_id: Optional[str] = None,
    master_flow_id: Optional[str] = None,
    **kwargs,
) -> UnifiedDiscoveryFlow:
    """
    Factory function to create a UnifiedDiscoveryFlow instance
    """
    logger.info("🏭 Creating new UnifiedDiscoveryFlow instance")

    # Generate flow_id if not provided
    if not flow_id:
        flow_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated new flow_id: {flow_id}")

    # Create flow instance
    flow = UnifiedDiscoveryFlow(
        crewai_service=crewai_service,
        context=context,
        flow_id=flow_id,
        master_flow_id=master_flow_id,
        **kwargs,
    )

    logger.info(f"✅ UnifiedDiscoveryFlow created successfully - ID: {flow_id}")
    return flow
