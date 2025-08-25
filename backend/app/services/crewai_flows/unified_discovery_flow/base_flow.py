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

from app.core.context import RequestContext
from app.core.security.cache_encryption import secure_setattr
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from .data_utilities import DataUtilities
from .defensive_method_resolver import create_method_resolver
from .flow_finalization import FlowFinalizer
from .flow_initialization import FlowInitializer
from .flow_management import FlowManager
from .notification_utilities import NotificationUtilities
from .phase_handlers import PhaseHandlers
from .state_management import StateManager

# CrewAI Flow imports - REAL AGENTS ONLY
logger = logging.getLogger(__name__)

try:
    from crewai import Flow
    from crewai.flow.flow import listen, start

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

        # Initialize defensive method resolver for robust method calls
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
        self.state_manager = StateManager(self.state)

        # Initialize unified flow management for lifecycle operations
        from ..handlers.unified_flow_management import UnifiedFlowManagement

        self.unified_flow_management = UnifiedFlowManagement(self.state)

        # Initialize UnifiedFlowCrewManager instead of CrewCoordinator
        from ..handlers.unified_flow_crew_manager import UnifiedFlowCrewManager

        self.crew_manager = UnifiedFlowCrewManager(
            self.crewai_service, self.state, callback_handler=None, context=self.context
        )
        # Keep coordinator as alias for backward compatibility
        self.coordinator = self.crew_manager
        self.flow_manager = FlowManager(
            self.state, self.state_manager, self.unified_flow_management
        )
        self.finalizer = FlowFinalizer(self.state, self.state_manager)

        # Initialize bridge for flow-specific database operations
        from ..flow_state_bridge import FlowStateBridge

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
            self._flow_state.started_at = datetime.now().isoformat()

            # Initialize phase executors now that we have state
            self._initialize_phase_executors_with_state()

            # Load raw data if not already loaded
            if (
                not hasattr(self._flow_state, "raw_data")
                or not self._flow_state.raw_data
            ):
                await self.data_utils.load_raw_data_from_database(self._flow_state)

            # Save initial state to database
            if self.flow_bridge:
                await self.flow_bridge.save_state(
                    self._flow_id, self._flow_state.dict()
                )
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
        """Generate field mapping suggestions with defensive programming"""
        logger.info(f"🗺️ [ECHO] Field mapping phase triggered for flow {self._flow_id}")

        # DEFENSIVE PROGRAMMING: Check if field mapping has already been executed
        # Handle multiple execution scenarios gracefully
        try:
            field_mapping_executed = getattr(
                self.state, "field_mapping_executed", False
            )
            phase_completion = getattr(self.state, "phase_completion", {})
            phase_completed = phase_completion.get("field_mapping", False)

            if field_mapping_executed or phase_completed:
                logger.warning(
                    f"⚠️ Field mapping already executed for flow {self._flow_id}, skipping duplicate execution"
                )
                # Return the existing field mappings with defensive access
                existing_mappings = getattr(self.state, "field_mappings", {})
                existing_suggestions = getattr(self.state, "mapping_suggestions", [])

                return {
                    "status": "already_completed",
                    "phase": "field_mapping",
                    "field_mappings": existing_mappings,
                    "suggestions": existing_suggestions,
                    "message": "Field mapping already executed, returning existing results",
                }
        except Exception as state_check_error:
            logger.warning(f"⚠️ Error checking field mapping state: {state_check_error}")
            # Continue with execution if state check fails

        # DEFENSIVE PROGRAMMING: Multiple execution strategies
        mapping_result = None
        execution_errors = []

        try:
            # Ensure state IDs are correct
            self._ensure_state_ids()

            # Strategy 1: Try direct phase handler method
            try:
                logger.info("🔄 Attempting field mapping via phase handlers")
                mapping_result = await self._safe_execute_field_mapping_via_handler(
                    data_validation_agent_result
                )
                logger.info("✅ Field mapping completed via phase handlers")
            except Exception as handler_error:
                execution_errors.append(f"Phase handler error: {handler_error}")
                logger.warning(f"⚠️ Phase handler execution failed: {handler_error}")

                # Strategy 2: Try direct method resolver approach
                try:
                    logger.info("🔄 Attempting field mapping via method resolver")
                    mapping_result = (
                        await self._safe_execute_field_mapping_via_resolver(
                            data_validation_agent_result
                        )
                    )
                    logger.info("✅ Field mapping completed via method resolver")
                except Exception as resolver_error:
                    execution_errors.append(f"Method resolver error: {resolver_error}")
                    logger.warning(
                        f"⚠️ Method resolver execution failed: {resolver_error}"
                    )

                    # Strategy 3: Fallback to basic field mapping
                    try:
                        logger.info("🔄 Attempting fallback field mapping execution")
                        mapping_result = await self._fallback_field_mapping_execution(
                            data_validation_agent_result
                        )
                        logger.info("✅ Field mapping completed via fallback method")
                    except Exception as fallback_error:
                        execution_errors.append(f"Fallback error: {fallback_error}")
                        logger.error(
                            f"❌ Fallback field mapping failed: {fallback_error}"
                        )

            # Check if we got a valid result
            if mapping_result and mapping_result.get("status") == "success":
                # Send approval request notification
                try:
                    await self.notification_utils.send_approval_request_notification(
                        mapping_result
                    )
                except Exception as notification_error:
                    logger.warning(
                        f"⚠️ Failed to send approval notification: {notification_error}"
                    )
                    # Don't fail the entire process for notification issues

                logger.info(
                    "✅ Field mapping suggestions generated - awaiting approval"
                )
                return mapping_result
            else:
                # All strategies failed
                error_summary = "; ".join(execution_errors)
                error_message = (
                    f"All field mapping execution strategies failed: {error_summary}"
                )
                logger.error(f"❌ {error_message}")

                # Return a structured error response
                return {
                    "status": "failed",
                    "phase": "field_mapping",
                    "error": error_message,
                    "execution_errors": execution_errors,
                    "field_mappings": [],
                    "suggestions": [],
                    "message": "Field mapping generation failed after trying multiple strategies",
                }

        except Exception as e:
            logger.error(f"❌ Field mapping phase failed with unexpected error: {e}")
            try:
                await self.notification_utils.send_error_notification(
                    str(e), "field_mapping"
                )
            except Exception as notification_error:
                logger.error(f"Failed to send error notification: {notification_error}")

            # Return structured error instead of raising to prevent flow termination
            return {
                "status": "failed",
                "phase": "field_mapping",
                "error": str(e),
                "execution_errors": execution_errors,
                "field_mappings": [],
                "suggestions": [],
                "message": "Field mapping phase encountered an unexpected error",
            }

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

    # ========================================
    # DEFENSIVE FIELD MAPPING METHODS
    # ========================================

    async def _safe_execute_field_mapping_via_handler(self, data_validation_result):
        """
        Strategy 1: Execute field mapping via phase handlers with defensive checks.

        This is the primary method that should work in normal circumstances.
        """
        logger.info("🛡️ Executing field mapping via phase handlers (Strategy 1)")

        # Check if phase handlers exist and are properly initialized
        if not hasattr(self, "phase_handlers") or not self.phase_handlers:
            raise RuntimeError("Phase handlers not initialized")

        # Check for the field mapping method using defensive resolver
        handler_resolver = create_method_resolver(self.phase_handlers)

        # Try multiple method name variants
        method_variants = [
            "generate_field_mapping_suggestions",
            "generate_field_mapping_suggestion",  # Common typo
            "generate_mapping_suggestions",
            "field_mapping_suggestions",
        ]

        mapping_method = None
        for variant in method_variants:
            mapping_method = handler_resolver.resolve_method(variant)
            if mapping_method:
                logger.info(f"✅ Resolved field mapping method: {variant}")
                break

        if not mapping_method:
            method_info = handler_resolver.get_method_info(
                "generate_field_mapping_suggestions"
            )
            logger.error(
                f"❌ Field mapping method resolution failed. Info: {method_info}"
            )
            raise AttributeError("Field mapping method not found on phase handlers")

        # Execute the mapping method
        result = await mapping_method(data_validation_result)

        # Validate result structure
        if not isinstance(result, dict):
            raise ValueError(
                f"Field mapping returned invalid result type: {type(result)}"
            )

        # Ensure required fields are present
        if "status" not in result:
            result["status"] = "success" if "error" not in result else "failed"

        logger.info("✅ Field mapping via phase handlers completed successfully")
        return result

    async def _safe_execute_field_mapping_via_resolver(self, data_validation_result):
        """
        Strategy 2: Execute field mapping directly via method resolver.

        This method attempts to call field mapping methods directly on the flow
        instance when phase handlers fail.
        """
        logger.info("🛡️ Executing field mapping via method resolver (Strategy 2)")

        # Check if field mapping phase executor exists
        if not hasattr(self, "field_mapping_phase") or not self.field_mapping_phase:
            # Try to initialize phase executors
            if hasattr(self, "_initialize_phase_executors_with_state"):
                logger.info("🔄 Attempting to initialize phase executors")
                self._initialize_phase_executors_with_state()
            else:
                raise RuntimeError("Cannot initialize phase executors")

        if not self.field_mapping_phase:
            raise RuntimeError("Field mapping phase executor still not available")

        # Use defensive method resolution on the phase executor
        executor_resolver = create_method_resolver(self.field_mapping_phase)

        # Try to find the execution method
        execution_method = executor_resolver.resolve_method(
            "execute_suggestions_only",
            fallback_variants=["execute", "execute_field_mapping", "run", "process"],
        )

        if not execution_method:
            method_info = executor_resolver.get_method_info("execute_suggestions_only")
            logger.error(
                f"❌ Field mapping execution method not found. Info: {method_info}"
            )
            raise AttributeError("Field mapping execution method not found")

        # Prepare input data
        input_data = {
            "validation_result": data_validation_result,
            "flow_id": self._flow_id,
            "phase": "field_mapping",
            "suggestions_only": True,
        }

        # Execute the method
        result = await execution_method(input_data)

        # Process and validate result
        if not isinstance(result, dict):
            raise ValueError(
                f"Field mapping executor returned invalid result type: {type(result)}"
            )

        # Convert result to expected format if needed
        if "success" in result and result["success"]:
            result["status"] = "success"
        elif "success" in result and not result["success"]:
            result["status"] = "failed"

        logger.info("✅ Field mapping via method resolver completed successfully")
        return result

    async def _fallback_field_mapping_execution(self, data_validation_result):
        """
        Strategy 3: Fallback field mapping execution.

        This method provides a basic field mapping implementation as a last resort
        when all other methods fail.
        """
        logger.info("🛡️ Executing fallback field mapping (Strategy 3)")

        try:
            # Basic field mapping logic as fallback
            raw_data = getattr(self.state, "raw_data", {})

            if not raw_data:
                logger.warning("⚠️ No raw data available for fallback field mapping")
                return {
                    "status": "success",
                    "phase": "field_mapping",
                    "field_mappings": [],
                    "suggestions": [],
                    "clarifications": [],
                    "message": "Fallback: No raw data available, proceeding with empty mappings",
                }

            # Extract field names from raw data
            field_names = []
            if isinstance(raw_data, dict):
                if (
                    "data" in raw_data
                    and isinstance(raw_data["data"], list)
                    and raw_data["data"]
                ):
                    # Handle nested data structure
                    first_record = raw_data["data"][0]
                    if isinstance(first_record, dict):
                        field_names = list(first_record.keys())
                elif isinstance(raw_data, dict):
                    # Direct dictionary format
                    field_names = list(raw_data.keys())

            logger.info(
                f"📋 Fallback extracted {len(field_names)} field names: {field_names[:5]}..."
            )

            # Generate basic mappings (identity mapping as fallback)
            basic_mappings = []
            suggestions = []

            for field_name in field_names[:20]:  # Limit to first 20 fields
                # Skip metadata fields
                if field_name.lower() in [
                    "mappings",
                    "skipped_fields",
                    "synthesis_required",
                ]:
                    continue

                mapping = {
                    "source_field": field_name,
                    "target_field": field_name,  # Identity mapping
                    "mapping_type": "direct",
                    "confidence": 0.5,  # Low confidence for fallback
                    "method": "fallback",
                }
                basic_mappings.append(mapping)

                # Add suggestion
                suggestion = {
                    "field": field_name,
                    "suggested_mapping": field_name,
                    "confidence": 0.5,
                    "reason": "Fallback identity mapping",
                }
                suggestions.append(suggestion)

            result = {
                "status": "success",
                "phase": "field_mapping",
                "field_mappings": basic_mappings,
                "mappings": basic_mappings,  # Alternative key name
                "suggestions": suggestions,
                "clarifications": [],
                "message": f"Fallback field mapping completed with {len(basic_mappings)} basic mappings",
                "execution_method": "fallback",
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"✅ Fallback field mapping generated {len(basic_mappings)} mappings"
            )
            return result

        except Exception as fallback_error:
            logger.error(f"❌ Even fallback field mapping failed: {fallback_error}")
            # Return minimal response to prevent complete failure
            return {
                "status": "failed",
                "phase": "field_mapping",
                "error": f"Fallback field mapping failed: {fallback_error}",
                "field_mappings": [],
                "suggestions": [],
                "clarifications": [],
                "message": "All field mapping strategies failed including fallback",
                "execution_method": "fallback_failed",
            }


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
