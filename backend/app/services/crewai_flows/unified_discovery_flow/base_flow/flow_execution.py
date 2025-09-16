"""
Flow Execution - Main Flow Phase Execution Methods

Contains the middle and later phase execution methods.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Import necessary decorators
try:
    from crewai.flow.flow import listen
except ImportError as e:
    logger.error(f"❌ CrewAI Flow decorators not available: {e}")
    raise ImportError(f"CrewAI flow decorators required: {e}")


class FlowExecutionMethods:
    """Mixin class containing main flow execution methods"""

    @listen("execute_data_import_validation_agent")
    async def generate_field_mapping_suggestions(  # noqa: C901
        self, data_validation_agent_result
    ):
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

    @listen("generate_field_mapping_suggestions")
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

    @listen("pause_for_field_mapping_approval")
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

    @listen("apply_approved_field_mappings")
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

    @listen("execute_data_cleansing_agent")
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

    @listen("create_discovery_assets_from_cleaned_data")
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
                "promotion_timestamp": datetime.utcnow().isoformat(),
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

    @listen("promote_discovery_assets_to_assets")
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
