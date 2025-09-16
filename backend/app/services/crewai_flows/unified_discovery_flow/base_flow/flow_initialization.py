"""
Flow Initialization - Initial Flow Setup Methods

Contains the @start method and early phase execution methods.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Import necessary decorators
try:
    from crewai.flow.flow import listen, start
except ImportError as e:
    logger.error(f"❌ CrewAI Flow decorators not available: {e}")
    raise ImportError(f"CrewAI flow decorators required: {e}")


class FlowInitializationMethods:
    """Mixin class containing flow initialization methods"""

    @start()
    async def initialize_discovery(self):
        """Initialize the discovery flow"""
        from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

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
