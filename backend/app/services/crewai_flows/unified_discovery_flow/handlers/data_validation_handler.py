"""
Data validation phase handler.
Handles the data import validation phase of the unified discovery flow.
"""

import logging
from datetime import datetime

from .communication_utils import CommunicationUtils
from .state_utils import StateUtils

logger = logging.getLogger(__name__)


class DataValidationHandler:
    """Handles data validation phase operations."""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance."""
        self.flow = flow_instance
        self.logger = logger
        self.communication = CommunicationUtils(flow_instance)
        self.state_utils = StateUtils(flow_instance)

    async def execute_data_import_validation(self):
        """Execute the data import validation phase"""
        self.logger.info(
            f"🔍 [ECHO] Data validation phase triggered for flow {self.flow._flow_id}"
        )

        # CC: Record phase start time and transition
        start_time = datetime.utcnow()
        await self.state_utils.add_phase_transition("data_validation", "processing")

        try:
            # Update flow status and sync to state
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import (
                    PostgresFlowStateStore,
                )

                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(
                        self.flow._flow_id, "processing_data_validation"
                    )
                    self.logger.info(
                        "✅ [ECHO] Updated flow status to 'processing_data_validation'"
                    )

            # Load raw data into flow state if not already loaded
            if hasattr(self.flow.state, "raw_data") and not self.flow.state.raw_data:
                await self.flow._load_raw_data_from_database(self.flow.state)

            # Execute data validation using the executor pattern
            if not self.flow.data_validation_phase:
                self.logger.error("❌ Data validation phase executor not initialized")
                # Try to initialize it now
                if hasattr(self.flow, "_initialize_phase_executors_with_state"):
                    self.flow._initialize_phase_executors_with_state()

            if not self.flow.data_validation_phase:
                raise RuntimeError(
                    "Data validation phase executor is not initialized. This is a critical error."
                )

            validation_result = await self.flow.data_validation_phase.execute(
                None  # No previous result for the first phase
            )

            # Send agent insight
            await self.communication.send_phase_insight(
                phase="data_validation",
                title="Data Validation Completed",
                description="Data validation phase has been completed successfully",
                progress=20,
                data=validation_result,
            )

            # Update state with validation results
            self.flow.state.validation_results = validation_result.get(
                "validation_results", {}
            )

            # Transition to field mapping phase after successful data validation
            if validation_result.get("is_valid", False):
                self.flow.state.current_phase = "field_mapping"
                self.logger.info(
                    "✅ Transitioned to field_mapping phase after successful data validation"
                )

            # CC: Record phase completion time and transition
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.state_utils.record_phase_execution_time(
                "data_validation", execution_time_ms
            )
            await self.state_utils.add_phase_transition(
                "data_validation",
                "completed",
                {
                    "execution_time_ms": execution_time_ms,
                    "results_count": len(
                        validation_result.get("validation_results", {})
                    ),
                },
            )

            # Trigger mapping application phase if available
            if (
                hasattr(self.flow, "mapping_application_phase")
                and self.flow.mapping_application_phase
            ):
                return await self._execute_mapping_application(validation_result)
            else:
                self.logger.info(
                    "ℹ️ [ECHO] No mapping application phase available, skipping"
                )
                return validation_result

        except Exception as e:
            self.logger.error(f"❌ Data validation phase failed: {e}")
            await self.communication.send_phase_error("data_validation", str(e))
            raise

    async def _execute_mapping_application(self, validation_result):
        """Execute mapping application as part of data validation."""
        try:
            self.logger.info(
                f"🔗 [ECHO] Executing mapping application for flow {self.flow._flow_id}"
            )

            # Update flow status
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import (
                    PostgresFlowStateStore,
                )

                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(
                        self.flow._flow_id, "processing_mapping_application"
                    )

            # Execute mapping application using the executor pattern
            mapping_result = await self.flow.mapping_application_phase.execute(
                validation_result  # Pass validation result from previous phase
            )

            # Send agent insight
            await self.communication.send_phase_insight(
                phase="mapping_application",
                title="Mapping Application Completed",
                description="Mapping application phase has been completed successfully",
                progress=50,
                data=mapping_result,
            )

            # Update state with mapping results
            self.flow.state.mapping_results = mapping_result.get("mapping_results", {})

            return mapping_result

        except Exception as e:
            self.logger.error(f"❌ Mapping application phase failed: {e}")
            await self.communication.send_phase_error("mapping_application", str(e))
            raise
