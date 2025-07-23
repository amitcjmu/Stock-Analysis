"""
State Management Module

Handles all state-related operations for the Unified Discovery Flow,
including state updates, validation, and persistence coordination.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from .flow_config import FlowConfig, PhaseNames

logger = logging.getLogger(__name__)


class StateManager:
    """Manages flow state updates and validation"""

    def __init__(self, state: UnifiedDiscoveryFlowState, flow_bridge=None):
        """
        Initialize state manager

        Args:
            state: The flow state object
            flow_bridge: Optional flow state bridge for PostgreSQL persistence
        """
        self.state = state
        self.flow_bridge = flow_bridge
        self._state_lock = asyncio.Lock()

    async def update_phase_status(
        self, phase_name: str, status: str, result: Optional[Dict[str, Any]] = None
    ):
        """
        Update the status of a specific phase

        Args:
            phase_name: Name of the phase
            status: New status (e.g., 'completed', 'failed', 'in_progress')
            result: Optional result data from the phase
        """
        async with self._state_lock:
            # Update phase completion tracking
            if status == "completed":
                self.state.phase_completion[phase_name] = True
                self.state.completed_phases.append(phase_name)

                # Store phase results
                if result:
                    self._store_phase_result(phase_name, result)

            # Update current phase
            if status == "in_progress":
                self.state.current_phase = phase_name

            # Update timestamps
            self.state.updated_at = datetime.utcnow().isoformat()

            logger.info(f"✅ Phase '{phase_name}' status updated to: {status}")

    def _store_phase_result(self, phase_name: str, result: Dict[str, Any]):
        """Store phase-specific results in appropriate state fields"""
        phase_mappings = {
            PhaseNames.DATA_IMPORT_VALIDATION: self._store_validation_results,
            PhaseNames.FIELD_MAPPING: self._store_field_mapping_results,
            PhaseNames.DATA_CLEANSING: self._store_cleansing_results,
            PhaseNames.ASSET_INVENTORY: self._store_inventory_results,
            PhaseNames.DEPENDENCY_ANALYSIS: self._store_dependency_results,
            PhaseNames.TECH_DEBT_ASSESSMENT: self._store_tech_debt_results,
        }

        handler = phase_mappings.get(phase_name)
        if handler:
            handler(result)

    def _store_validation_results(self, result: Dict[str, Any]):
        """Store data validation results"""
        self.state.data_validation_results = result.get("validation_results", {})
        self.state.data_quality_score = result.get("quality_score", 0.0)

        # Update raw data
        if "validated_data" in result:
            self.state.raw_data = result["validated_data"]

    def _store_field_mapping_results(self, result: Dict[str, Any]):
        """Store field mapping results"""
        self.state.field_mappings = result.get("mappings", {})
        self.state.field_mapping_confidence = result.get("confidence", 0.0)

    def _store_cleansing_results(self, result: Dict[str, Any]):
        """Store data cleansing results"""
        self.state.data_cleansing_results = result.get("cleansing_report", {})

        # Update cleaned data
        if "cleaned_data" in result:
            self.state.cleaned_data = result["cleaned_data"]

    def _store_inventory_results(self, result: Dict[str, Any]):
        """Store asset inventory results"""
        self.state.asset_inventory = result.get("inventory", {})
        self.state.asset_inventory["total_assets"] = len(result.get("assets", []))

    def _store_dependency_results(self, result: Dict[str, Any]):
        """Store dependency analysis results"""
        self.state.dependencies = result.get("dependencies", {})

    def _store_tech_debt_results(self, result: Dict[str, Any]):
        """Store technical debt analysis results"""
        self.state.technical_debt = result.get("tech_debt", {})

    def add_error(self, phase: str, error: str):
        """Add an error to the state"""
        error_entry = {
            "phase": phase,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Safe attribute access for CrewAI state
        if hasattr(self.state, "errors"):
            self.state.errors.append(error_entry)
        logger.error(f"❌ Error in phase '{phase}': {error}")

    def add_warning(self, phase: str, warning: str):
        """Add a warning to the state"""
        warning_entry = {
            "phase": phase,
            "warning": warning,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.warnings.append(warning_entry)
        logger.warning(f"⚠️ Warning in phase '{phase}': {warning}")

    def add_agent_insight(self, agent_name: str, insight: str, confidence: float = 0.8):
        """Add an agent insight to the state"""
        insight_entry = {
            "agent": agent_name,
            "insight": insight,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.state.agent_insights.append(insight_entry)
        logger.info(f"💡 Agent insight from '{agent_name}': {insight}")

    async def safe_update_flow_state(self):
        """Safely update flow state with PostgreSQL persistence and discovery_flows table"""
        # First sync to flow state persistence (for recovery)
        if self.flow_bridge:
            try:
                await self.flow_bridge.sync_state_update(
                    self.state, self.state.current_phase, crew_results={}
                )
                logger.info("✅ Flow state synchronized to PostgreSQL")
            except Exception as e:
                logger.warning(f"⚠️ Failed to sync flow state: {e}")

        # Then update discovery_flows table (source of truth for discovery flows)
        try:
            from app.core.context import RequestContext
            from app.core.database import AsyncSessionLocal
            from app.repositories.discovery_flow_repository import \
                DiscoveryFlowRepository

            async with AsyncSessionLocal() as db:
                # Ensure all IDs are strings and not empty
                client_account_id = (
                    str(getattr(self.state, "client_account_id", "")) or ""
                )
                engagement_id = str(getattr(self.state, "engagement_id", "")) or ""
                user_id = str(getattr(self.state, "user_id", "")) or ""
                flow_id = str(getattr(self.state, "flow_id", "")) or ""

                RequestContext(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id=user_id,
                    flow_id=flow_id,
                )

                repo = DiscoveryFlowRepository(
                    db,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id=user_id,
                )

                # First check if the flow exists, create if not
                flow_id = getattr(self.state, "flow_id", None)
                if flow_id:
                    existing_flow = await repo.get_by_flow_id(flow_id)
                    if not existing_flow:
                        logger.info(f"🆕 Creating discovery flow record for {flow_id}")
                        # Get master flow ID from state metadata
                        master_flow_id = getattr(
                            self.state, "master_flow_id", None
                        ) or self.state.metadata.get("master_flow_id")
                        logger.info(
                            f"🔍 Master flow ID for discovery flow: {master_flow_id}"
                        )
                        logger.info(f"🔍 State metadata: {self.state.metadata}")

                        await repo.flow_commands.create_discovery_flow(
                            flow_id=flow_id,
                            master_flow_id=master_flow_id,
                            flow_type="primary",
                            description=f"Discovery Flow {flow_id[:8]}",
                            initial_state_data={
                                "status": getattr(self.state, "status", "initialized"),
                                "current_phase": getattr(
                                    self.state, "current_phase", "initialization"
                                ),
                                "progress_percentage": getattr(
                                    self.state, "progress_percentage", 0.0
                                ),
                            },
                            user_id=user_id,
                            raw_data=getattr(self.state, "raw_data", []),
                            metadata=getattr(self.state, "metadata", {}),
                        )
                        logger.info(f"✅ Discovery flow record created for {flow_id}")

                    # Now update the flow
                    await repo.flow_commands.update_flow_status(
                        flow_id=flow_id,
                        status=self.state.status,
                        progress_percentage=self.state.progress_percentage,
                    )
                else:
                    logger.warning("⚠️ Cannot create/update flow - flow_id is missing")

                # Update current phase data if needed
                current_phase = getattr(self.state, "current_phase", None)
                if current_phase and flow_id:
                    phase_data = self._get_phase_data()
                    if phase_data:
                        await repo.flow_commands.update_phase_completion(
                            flow_id=flow_id,
                            phase=current_phase,
                            data=phase_data,
                            completed=self.state.phase_completion.get(
                                current_phase, False
                            ),
                            agent_insights=getattr(self.state, "agent_insights", []),
                        )
                elif not flow_id:
                    logger.warning(
                        "⚠️ Cannot update phase completion - flow_id is missing"
                    )

                logger.info("✅ Discovery flows table updated")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update discovery_flows table: {e}")

    def _get_phase_data(self) -> Dict[str, Any]:
        """Get phase-specific data for storage"""
        phase = self.state.current_phase

        if phase == PhaseNames.FIELD_MAPPING:
            return {
                "field_mappings": getattr(self.state, "field_mappings", {}),
                "confidence": getattr(self.state, "field_mapping_confidence", 0),
                "awaiting_user_approval": getattr(
                    self.state, "awaiting_user_approval", False
                ),
            }
        elif phase == PhaseNames.DATA_CLEANSING:
            return {
                "cleaned_data": getattr(self.state, "cleaned_data", []),
                "data_quality_score": getattr(self.state, "data_quality_score", 0),
            }
        elif phase == PhaseNames.ASSET_INVENTORY:
            return {"asset_inventory": getattr(self.state, "asset_inventory", {})}
        # Add more phases as needed

        return {}

    def calculate_progress(self) -> float:
        """Calculate overall flow progress percentage"""
        total_phases = len(FlowConfig.PHASE_ORDER)
        phase_completion = getattr(self.state, "phase_completion", {})
        completed_phases = len(
            [p for p in FlowConfig.PHASE_ORDER if phase_completion.get(p, False)]
        )

        # Base progress from completed phases
        base_progress = (completed_phases / total_phases) * 100

        # If we have a current phase that's in progress, add partial progress
        current_phase = getattr(self.state, "current_phase", None)
        if current_phase and not phase_completion.get(current_phase, False):
            # Add partial progress for current phase (50% of a phase's worth)
            phase_progress = (
                1 / total_phases
            ) * 50  # Half progress for in-progress phase
            base_progress += phase_progress

        # Also check for specific phase completion flags
        # Check if data_import phase is completed in phase_completion dict
        if phase_completion.get("data_import", False):
            # Ensure at least one phase worth of progress for data import
            min_progress = (1 / total_phases) * 100
            base_progress = max(base_progress, min_progress)

        return round(base_progress, 1)

    def get_next_phase(self) -> Optional[str]:
        """Get the next phase to execute"""
        for phase in FlowConfig.PHASE_ORDER:
            if not self.state.phase_completion.get(phase, False):
                return phase
        return None

    def is_user_approval_needed(self) -> bool:
        """Check if user approval is needed based on current state"""
        # Check if we're in field mapping phase and need approval
        if self.state.current_phase == PhaseNames.FIELD_MAPPING:
            # Check confidence thresholds
            if (
                self.state.field_mapping_confidence
                < FlowConfig.DEFAULT_CONFIDENCE_THRESHOLD
            ):
                return True

            # Check if any required fields need review
            for field in FlowConfig.USER_APPROVAL_REQUIRED_FIELDS:
                if field in [
                    "field_mappings",
                    "data_quality_threshold",
                    "asset_classification_confidence",
                ]:
                    return True

        return False

    def prepare_approval_context(self) -> Dict[str, Any]:
        """Prepare context for user approval"""
        return {
            "flow_id": self.state.flow_id,
            "current_phase": self.state.current_phase,
            "field_mappings": self.state.field_mappings,
            "confidence_scores": {
                "field_mapping": self.state.field_mapping_confidence,
                "data_quality": self.state.data_quality_score,
            },
            "discovered_assets": self.state.total_assets,
            "warnings": self.state.warnings,
            "agent_insights": self.state.agent_insights,
            "required_reviews": self._get_required_reviews(),
        }

    def _get_required_reviews(self) -> List[Dict[str, Any]]:
        """Get list of items requiring user review"""
        reviews = []

        # Field mappings with low confidence
        if (
            self.state.field_mapping_confidence
            < FlowConfig.DEFAULT_CONFIDENCE_THRESHOLD
        ):
            reviews.append(
                {
                    "type": "field_mapping",
                    "reason": "Low confidence score",
                    "confidence": self.state.field_mapping_confidence,
                    "items": self.state.field_mappings,
                }
            )

        # Data quality issues
        if self.state.data_quality_score < FlowConfig.DEFAULT_DATA_QUALITY_THRESHOLD:
            reviews.append(
                {
                    "type": "data_quality",
                    "reason": "Below quality threshold",
                    "score": self.state.data_quality_score,
                    "issues": self.state.data_validation_results.get("issues", []),
                }
            )

        return reviews

    def create_flow_summary(self) -> Dict[str, Any]:
        """Create a comprehensive summary of the flow"""
        # Safe attribute access for CrewAI StateWithId compatibility
        return {
            "flow_id": getattr(self.state, "flow_id", None),
            "status": getattr(self.state, "status", "unknown"),
            "progress": self.calculate_progress(),
            "current_phase": getattr(self.state, "current_phase", "unknown"),
            "completed_phases": getattr(self.state, "completed_phases", []),
            "total_assets": getattr(self.state, "total_assets", 0),
            "errors": len(getattr(self.state, "errors", [])),
            "warnings": len(getattr(self.state, "warnings", [])),
            "agent_insights": len(getattr(self.state, "agent_insights", [])),
            "timestamps": {
                "started": getattr(self.state, "created_at", None),
                "updated": getattr(self.state, "updated_at", None),
            },
        }
