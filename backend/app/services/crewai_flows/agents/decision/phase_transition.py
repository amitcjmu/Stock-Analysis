"""
Phase Transition Decision Agent

Agent responsible for making intelligent decisions about phase transitions
based on data quality, business context, and flow objectives.
"""

import logging
from typing import Any, Dict

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from .base import AgentDecision, BaseDecisionAgent, PhaseAction
from .utils import ConfidenceCalculator, DecisionUtils

logger = logging.getLogger(__name__)


class PhaseTransitionAgent(BaseDecisionAgent):
    """Agent that decides phase transitions based on data analysis and business context"""

    def __init__(self):
        super().__init__(
            role="Flow Orchestration Strategist",
            goal="Determine optimal phase transitions based on data quality, business context, and flow objectives",
            backstory="""You are an expert in workflow optimization with deep understanding of:
            - Data quality assessment and validation
            - Business process optimization
            - Risk management and decision theory
            - Migration best practices

            You make intelligent decisions about when to proceed, pause for human input,
            or skip phases based on comprehensive analysis of the current situation.""",
        )

    async def analyze_phase_transition(
        self, current_phase: str, results: Any, state: UnifiedDiscoveryFlowState
    ) -> AgentDecision:
        """Analyze and decide on phase transition"""
        logger.info(f"🤖 Analyzing phase transition from: {current_phase}")

        # Analyze current state
        analysis = self._analyze_current_state(current_phase, results, state)

        # Make decision based on analysis
        decision = self._make_transition_decision(current_phase, analysis)

        logger.info(
            f"📊 Decision: {decision.action.value} -> {decision.next_phase} (confidence: {decision.confidence})"
        )

        return decision

    def _analyze_current_state(
        self, phase: str, results: Any, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Comprehensive state analysis"""
        analysis = {
            "phase": phase,
            "has_errors": DecisionUtils.check_for_errors(state),
            "data_quality": DecisionUtils.assess_data_quality(state),
            "completeness": DecisionUtils.assess_completeness(phase, state),
            "complexity": DecisionUtils.assess_complexity(state),
            "risk_factors": DecisionUtils.identify_risk_factors(state),
        }

        # Phase-specific analysis
        if phase == "data_import":
            analysis["import_metrics"] = self._analyze_import_metrics(results, state)
        elif phase == "field_mapping":
            analysis["mapping_quality"] = self._analyze_mapping_quality(state)
        elif phase == "data_cleansing":
            analysis["cleansing_impact"] = self._analyze_cleansing_impact(
                results, state
            )
        elif phase == "asset_creation":
            analysis["asset_creation_results"] = self._analyze_asset_creation(
                results, state
            )

        return analysis

    def _make_transition_decision(
        self, current_phase: str, analysis: Dict[str, Any]
    ) -> AgentDecision:
        """Make decision based on analysis"""

        # Check for critical errors first
        if analysis["has_errors"]:
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.95,
                reasoning=f"Critical errors detected in {current_phase} phase that prevent continuation",
                metadata={"errors": analysis.get("errors", [])},
            )

        # Phase-specific decision logic
        if current_phase == "data_import":
            return self._decide_after_import(analysis)
        elif current_phase == "field_mapping":
            return self._decide_after_mapping(analysis)
        elif current_phase == "data_cleansing":
            return self._decide_after_cleansing(analysis)
        elif current_phase == "asset_creation":
            return self._decide_after_asset_creation(analysis)
        else:
            # Default progression
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=DecisionUtils.get_next_phase(current_phase),
                confidence=0.8,
                reasoning=f"Phase {current_phase} completed successfully",
                metadata=analysis,
            )

    def _decide_after_import(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after data import phase"""
        metrics = analysis.get("import_metrics", {})
        data_quality = analysis.get("data_quality", 0)

        # Calculate confidence based on data quality and import success
        import_success_rate = metrics.get("success_rate", 0)
        completeness = analysis.get("completeness", 0)

        if data_quality < 0.3:
            # High confidence in failure decision when data quality is very poor
            failure_confidence = ConfidenceCalculator.weighted_average(
                {
                    "data_quality_severity": 1.0
                    - data_quality,  # Higher severity = higher confidence
                    "import_metrics_support": 1.0 if import_success_rate < 0.5 else 0.0,
                    "completeness_check": 1.0 if completeness < 0.3 else 0.0,
                }
            )
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=failure_confidence,
                reasoning="Data quality is too poor to proceed with migration. "
                "Source data needs to be cleaned or re-exported.",
                metadata={
                    "data_quality_score": data_quality,
                    "import_success_rate": import_success_rate,
                    "recommendations": [
                        "Review source data export process",
                        "Check for data corruption",
                        "Validate export format",
                    ],
                },
            )

        # CRITICAL: Always proceed to field_mapping after data_import
        # Field mapping is required for all subsequent phases to work properly
        proceed_confidence = ConfidenceCalculator.weighted_average(
            {
                "data_quality_adequate": 1.0 if data_quality >= 0.3 else 0.0,
                "import_success": 1.0 if import_success_rate >= 0.7 else 0.5,
                "field_mapping_necessity": 1.0,  # Always necessary
                "completeness_sufficient": 1.0 if completeness >= 0.5 else 0.7,
            }
        )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="field_mapping",
            confidence=proceed_confidence,
            reasoning="Proceeding to field mapping phase. Field mappings are required "
            "for all subsequent phases including asset creation and inventory. "
            "This ensures proper data transformation and validation.",
            metadata={
                "data_quality_score": data_quality,
                "import_metrics": metrics,
                "required_for_phases": [
                    "data_cleansing",
                    "asset_creation",
                    "asset_inventory",
                ],
            },
        )

    def _decide_after_mapping(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after field mapping phase"""
        mapping_quality = analysis.get("mapping_quality", {})
        mapping_confidence = mapping_quality.get("confidence", 0)
        missing_critical = mapping_quality.get("missing_critical_fields", [])

        # Dynamic threshold based on data characteristics
        required_confidence = ConfidenceCalculator.calculate_threshold(
            base_threshold=0.7,
            risk_factors=analysis.get("risk_factors", []),
            data_quality=analysis.get("data_quality", 0.5),
            complexity=analysis.get("complexity", 0),
        )

        if missing_critical:
            # High confidence in pause decision when critical fields are missing
            pause_confidence = ConfidenceCalculator.weighted_average(
                {
                    "critical_fields_missing": 1.0,
                    "mapping_completeness": 1.0
                    - (
                        len(missing_critical)
                        / max(1, mapping_quality.get("total_fields", 1))
                    ),
                    "business_impact": 1.0,  # Critical fields always have high business impact
                    "human_intervention_needed": 1.0,
                }
            )
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="field_mapping",
                confidence=pause_confidence,
                reasoning=f"Critical fields are not mapped: {', '.join(missing_critical)}. "
                "Human intervention required.",
                metadata={
                    "missing_fields": missing_critical,
                    "user_action": "map_critical_fields",
                },
            )

        if mapping_confidence < required_confidence:
            # Confidence in pause decision based on mapping quality gap
            confidence_gap = required_confidence - mapping_confidence
            pause_confidence = ConfidenceCalculator.weighted_average(
                {
                    "mapping_quality_insufficient": (
                        1.0 if confidence_gap > 0.2 else 0.5
                    ),
                    "confidence_gap_severity": min(
                        1.0, confidence_gap * 2
                    ),  # Scale gap to 0-1
                    "risk_of_errors": 1.0 - mapping_confidence,
                    "human_review_value": 0.8,
                }
            )
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="field_mapping",
                confidence=pause_confidence,
                reasoning=(
                    f"Mapping confidence ({mapping_confidence:.1%}) is below required threshold "
                    f"({required_confidence:.1%}). Human review recommended."
                ),
                metadata={
                    "current_confidence": mapping_confidence,
                    "required_confidence": required_confidence,
                    "confidence_gap": confidence_gap,
                    "user_action": "review_mappings",
                },
            )

        # High confidence - proceed automatically
        proceed_confidence = ConfidenceCalculator.weighted_average(
            {
                "mapping_quality_high": (
                    1.0 if mapping_confidence >= required_confidence else 0.0
                ),
                "no_critical_missing": 1.0 if len(missing_critical) == 0 else 0.0,
                "data_cleansing_readiness": 1.0 if mapping_confidence > 0.7 else 0.5,
                "field_coverage": mapping_quality.get("field_coverage", 0.8),
            }
        )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="data_cleansing",
            confidence=proceed_confidence,
            reasoning=f"Field mappings have high confidence ({mapping_confidence:.1%}). "
            "Proceeding to data cleansing.",
            metadata=mapping_quality,
        )

    def _decide_after_cleansing(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after data cleansing phase"""
        cleansing_impact = analysis.get("cleansing_impact", {})
        failure_rate = cleansing_impact.get("failure_rate", 0)
        success_rate = 1.0 - failure_rate
        records_processed = cleansing_impact.get("records_processed", 0)

        if failure_rate > 0.1:  # More than 10% failures
            # Calculate confidence based on failure severity and impact
            pause_confidence = ConfidenceCalculator.weighted_average(
                {
                    "failure_rate_high": 1.0,
                    "failure_severity": min(
                        1.0, failure_rate * 2
                    ),  # Scale failure rate
                    "records_at_risk": min(
                        1.0, (failure_rate * records_processed) / 100
                    ),
                    "human_intervention_needed": 0.9,
                }
            )
            return AgentDecision(
                action=PhaseAction.PAUSE,
                next_phase="data_cleansing",
                confidence=pause_confidence,
                reasoning=f"High cleansing failure rate ({failure_rate:.1%}). "
                "Manual review of failed records required.",
                metadata={
                    "failure_rate": failure_rate,
                    "failed_records": cleansing_impact.get("failed_records", []),
                    "user_action": "review_failures",
                },
            )

        # Successful cleansing - proceed to asset creation
        proceed_confidence = ConfidenceCalculator.weighted_average(
            {
                "cleansing_success_rate": success_rate,
                "failure_rate_acceptable": 1.0 if failure_rate <= 0.1 else 0.0,
                "records_processed_sufficient": 1.0 if records_processed > 0 else 0.0,
                "asset_creation_readiness": 1.0 if success_rate > 0.8 else 0.5,
                "data_quality_improved": cleansing_impact.get("quality_improvement", 0),
            }
        )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="asset_creation",
            confidence=proceed_confidence,
            reasoning="Data cleansing completed successfully. "
            "Proceeding to asset creation phase to build initial asset inventory.",
            metadata=cleansing_impact,
        )

    def _decide_after_asset_creation(self, analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after asset creation phase"""

        # Check if assets were actually created
        has_assets = self._check_assets_created(analysis)
        asset_creation_results = analysis.get("asset_creation_results", {})
        assets_created_count = asset_creation_results.get("assets_created", 0)
        creation_success_rate = asset_creation_results.get("success_rate", 0)

        if not has_assets:
            # Calculate confidence for retry based on failure analysis
            retry_confidence = ConfidenceCalculator.weighted_average(
                {
                    "no_assets_created": 1.0 if assets_created_count == 0 else 0.0,
                    "creation_failure_clear": (
                        1.0 if creation_success_rate == 0 else 0.5
                    ),
                    "retry_likely_to_succeed": analysis.get("data_quality", 0),
                    "database_connection_ok": 1.0,  # Assume database is working
                }
            )
            return AgentDecision(
                action=PhaseAction.RETRY,
                next_phase="asset_creation",
                confidence=retry_confidence,
                reasoning="No assets were created during asset creation phase. "
                "Retrying asset creation to ensure inventory is populated.",
                metadata={
                    "retry_reason": "no_assets_created",
                    "user_action": "verify_data_quality",
                    "assets_created_count": assets_created_count,
                    "creation_success_rate": creation_success_rate,
                },
            )

        # Assets successfully created - proceed to asset inventory
        proceed_confidence = ConfidenceCalculator.weighted_average(
            {
                "assets_created_successfully": 1.0 if assets_created_count > 0 else 0.0,
                "creation_success_rate_good": (
                    1.0 if creation_success_rate > 0.8 else 0.5
                ),
                "inventory_phase_ready": 1.0 if has_assets else 0.0,
                "data_quality_supports_analysis": analysis.get("data_quality", 0),
            }
        )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="asset_inventory",
            confidence=proceed_confidence,
            reasoning="Assets successfully created from cleansed data. "
            "Proceeding to asset inventory phase for detailed analysis.",
            metadata={
                "assets_created": True,
                "assets_created_count": assets_created_count,
                "creation_success_rate": creation_success_rate,
                "next_phase_purpose": "detailed_asset_analysis",
            },
        )

    # Helper methods for analysis

    def _analyze_import_metrics(
        self, results: Any, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Analyze data import metrics"""
        raw_data = DecisionUtils.get_state_attribute(state, "raw_data", [])
        return {
            "total_records": len(raw_data),
            "field_count": (
                len(raw_data[0]) if raw_data and isinstance(raw_data[0], dict) else 0
            ),
            "import_duration": (
                results.get("duration", 0) if isinstance(results, dict) else 0
            ),
            "success_rate": 0.9,  # Would calculate from actual import results
        }

    def _analyze_mapping_quality(
        self, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Analyze field mapping quality"""
        field_mappings = DecisionUtils.get_state_attribute(state, "field_mappings", {})

        if not field_mappings:
            return {"confidence": 0, "missing_critical_fields": []}

        # Identify which fields are actually critical based on data
        critical_fields = DecisionUtils.identify_critical_fields(state)
        mapped_fields = set(field_mappings.keys())
        missing_critical = [f for f in critical_fields if f not in mapped_fields]

        confidence = DecisionUtils.get_state_attribute(
            state, "field_mapping_confidence", 0.5
        )

        return {
            "confidence": confidence,
            "total_fields": len(field_mappings),
            "critical_fields": critical_fields,
            "missing_critical_fields": missing_critical,
            "field_coverage": (
                len(mapped_fields) / len(critical_fields) if critical_fields else 1.0
            ),
        }

    def _analyze_cleansing_impact(
        self, results: Any, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Analyze data cleansing impact"""
        if not isinstance(results, dict):
            return {"failure_rate": 0, "records_processed": 0}

        total_records = results.get("total_records", 0)
        failed_records = results.get("failed_records", 0)

        failure_rate = failed_records / total_records if total_records > 0 else 0

        return {
            "failure_rate": failure_rate,
            "records_processed": total_records,
            "records_cleaned": results.get("records_cleaned", 0),
            "quality_improvement": results.get("quality_improvement", 0),
            "failed_records": results.get("failed_record_details", []),
        }

    def _analyze_asset_creation(
        self, results: Any, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Analyze asset creation results"""
        if not isinstance(results, dict):
            return {"assets_created": 0, "success_rate": 0}

        return {
            "assets_created": results.get("assets_created", 0),
            "success_rate": results.get("success_rate", 0),
            "creation_errors": results.get("errors", []),
        }

    def _check_assets_created(self, analysis: Dict[str, Any]) -> bool:
        """Check if assets were actually created in the database"""
        # Check if asset creation results indicate success
        asset_creation_results = analysis.get("asset_creation_results", {})
        assets_created = asset_creation_results.get("assets_created", 0)

        # Also check if there are any assets in the state
        state = analysis.get("state", {})
        asset_inventory = DecisionUtils.get_state_attribute(
            state, "asset_inventory", {}
        )
        state_assets = asset_inventory.get("assets", []) if asset_inventory else []

        # Return True if either database shows assets created OR state has assets
        return assets_created > 0 or len(state_assets) > 0

    async def get_decision(self, agent_context: Dict[str, Any]) -> AgentDecision:
        """
        Get phase transition decision from agent context.
        This method is called by the execution engine to determine next steps.
        """
        try:
            # Extract key components from agent context
            current_phase = agent_context.get("current_phase", "")
            phase_result = agent_context.get("phase_result", {})
            flow_state = agent_context.get("flow_state")

            logger.info(
                f"🤖 PhaseTransitionAgent.get_decision called for phase: {current_phase}"
            )

            if not flow_state:
                logger.warning("⚠️ No flow state provided in agent context")
                return AgentDecision(
                    action=PhaseAction.FAIL,
                    next_phase="",
                    confidence=0.9,
                    reasoning="No flow state available for decision making",
                    metadata={"error": "missing_flow_state"},
                )

            # Convert flow_state to UnifiedDiscoveryFlowState if needed
            if isinstance(flow_state, dict):
                from app.models.unified_discovery_flow_state import (
                    UnifiedDiscoveryFlowState,
                )

                try:
                    state = UnifiedDiscoveryFlowState(**flow_state)
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to convert flow_state dict to UnifiedDiscoveryFlowState: {e}"
                    )
                    # Create minimal state for decision making
                    state = UnifiedDiscoveryFlowState()
                    state.current_phase = current_phase
            else:
                state = flow_state

            # Use the existing analyze_phase_transition method
            decision = await self.analyze_phase_transition(
                current_phase, phase_result, state
            )

            logger.info(
                f"✅ PhaseTransitionAgent decision: {decision.action.value} -> {decision.next_phase}"
            )
            return decision

        except Exception as e:
            logger.error(f"❌ PhaseTransitionAgent.get_decision failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Return safe fallback decision
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.8,
                reasoning=f"Decision making failed due to error: {str(e)}",
                metadata={"error": str(e), "fallback": True},
            )

    async def get_post_execution_decision(
        self, agent_context: Dict[str, Any]
    ) -> AgentDecision:
        """
        Get post-execution decision after a phase has completed.
        This method is called after phase execution to determine next steps.
        """
        try:
            # Extract key components from agent context
            phase_name = agent_context.get("phase_name", "")
            phase_result = agent_context.get("phase_result", {})
            flow_state = agent_context.get("flow_state")

            logger.info(
                f"🤖 PhaseTransitionAgent.get_post_execution_decision called for phase: {phase_name}"
            )

            if not flow_state:
                logger.warning(
                    "⚠️ No flow state provided in agent context for post-execution decision"
                )
                return AgentDecision(
                    action=PhaseAction.FAIL,
                    next_phase="",
                    confidence=0.9,
                    reasoning="No flow state available for post-execution decision making",
                    metadata={"error": "missing_flow_state"},
                )

            # Convert flow_state to UnifiedDiscoveryFlowState if needed
            if isinstance(flow_state, dict):
                from app.models.unified_discovery_flow_state import (
                    UnifiedDiscoveryFlowState,
                )

                try:
                    state = UnifiedDiscoveryFlowState(**flow_state)
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to convert flow_state dict to UnifiedDiscoveryFlowState: {e}"
                    )
                    # Create minimal state for decision making
                    state = UnifiedDiscoveryFlowState()
                    state.current_phase = phase_name
            else:
                state = flow_state

            # Analyze the phase result and determine next steps
            analysis = self._analyze_current_state(phase_name, phase_result, state)

            # Check if phase was successful based on result
            phase_successful = phase_result.get("status") == "completed"

            if not phase_successful:
                # Phase failed, decide on retry or failure
                error_info = phase_result.get("error", "Unknown error")
                return AgentDecision(
                    action=(
                        PhaseAction.RETRY
                        if "timeout" in str(error_info).lower()
                        else PhaseAction.FAIL
                    ),
                    next_phase=phase_name,
                    confidence=0.8,
                    reasoning=f"Phase {phase_name} failed: {error_info}",
                    metadata={"error": error_info, "phase_result": phase_result},
                )

            # Phase successful, determine next phase
            decision = self._make_transition_decision(phase_name, analysis)

            logger.info(
                f"✅ PhaseTransitionAgent post-execution decision: {decision.action.value} -> {decision.next_phase}"
            )
            return decision

        except Exception as e:
            logger.error(
                f"❌ PhaseTransitionAgent.get_post_execution_decision failed: {e}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Return safe fallback decision
            return AgentDecision(
                action=PhaseAction.FAIL,
                next_phase="",
                confidence=0.8,
                reasoning=f"Post-execution decision making failed due to error: {str(e)}",
                metadata={"error": str(e), "fallback": True},
            )
