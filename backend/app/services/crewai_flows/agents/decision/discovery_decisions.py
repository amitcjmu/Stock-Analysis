"""
Discovery Flow Phase Transition Decisions

Contains decision logic specific to discovery flow phases.
"""

import logging
from typing import Any, Dict

from .base import AgentDecision, PhaseAction
from .utils import ConfidenceCalculator

logger = logging.getLogger(__name__)


class DiscoveryDecisionLogic:
    """Discovery-specific decision logic for phase transitions"""

    @staticmethod
    def make_discovery_decision(
        current_phase: str, analysis: Dict[str, Any]
    ) -> AgentDecision:
        """Discovery-specific decision logic (original logic)"""
        # Phase-specific decision logic
        if current_phase == "data_import":
            return DiscoveryDecisionLogic._decide_after_import(analysis)
        elif current_phase == "field_mapping":
            return DiscoveryDecisionLogic._decide_after_mapping(analysis)
        elif current_phase == "data_cleansing":
            return DiscoveryDecisionLogic._decide_after_cleansing(analysis)
        elif current_phase == "asset_creation":
            return DiscoveryDecisionLogic._decide_after_asset_creation(analysis)
        elif current_phase == "asset_inventory":
            return DiscoveryDecisionLogic._decide_after_asset_inventory(analysis)
        else:
            # Default progression
            from app.services.crewai_flows.agents.decision.utils import DecisionUtils

            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=DecisionUtils.get_next_phase(current_phase, "discovery"),
                confidence=0.8,
                reasoning=f"Phase {current_phase} completed successfully",
                metadata=analysis,
            )

    @staticmethod
    def _decide_after_import(analysis: Dict[str, Any]) -> AgentDecision:
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

    @staticmethod
    def _decide_after_mapping(analysis: Dict[str, Any]) -> AgentDecision:
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

    @staticmethod
    def _decide_after_cleansing(analysis: Dict[str, Any]) -> AgentDecision:
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

        # Successful cleansing - proceed to asset inventory (Issue #907)
        # CC: Changed from asset_creation to asset_inventory to support preview/approval workflow
        proceed_confidence = ConfidenceCalculator.weighted_average(
            {
                "cleansing_success_rate": success_rate,
                "failure_rate_acceptable": 1.0 if failure_rate <= 0.1 else 0.0,
                "records_processed_sufficient": 1.0 if records_processed > 0 else 0.0,
                "asset_inventory_readiness": 1.0 if success_rate > 0.8 else 0.5,
                "data_quality_improved": cleansing_impact.get("quality_improvement", 0),
            }
        )

        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase="asset_inventory",  # CC FIX: Changed from asset_creation (Issue #907)
            confidence=proceed_confidence,
            reasoning="Data cleansing completed successfully. "
            "Proceeding to asset inventory phase for preview and approval before database creation.",
            metadata=cleansing_impact,
        )

    @staticmethod
    def _decide_after_asset_creation(analysis: Dict[str, Any]) -> AgentDecision:
        """Decision logic after asset creation phase"""
        # Check if assets were actually created
        has_assets = DiscoveryDecisionLogic._check_assets_created(analysis)
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

    @staticmethod
    def _check_assets_created(analysis: Dict[str, Any]) -> bool:
        """Check if assets were actually created in the database"""
        from app.services.crewai_flows.agents.decision.utils import DecisionUtils

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

    @staticmethod
    def _decide_after_asset_inventory(analysis: Dict[str, Any]) -> AgentDecision:
        """
        Decision logic after asset_inventory phase.

        Per ADR-027: asset_inventory is the TERMINAL phase of Discovery v3.0.0.
        Discovery flow ends here. dependency_analysis and tech_debt_assessment
        have been moved to Assessment flow.

        This phase uses DecisionUtils.get_next_phase() to delegate to FlowTypeConfig
        registry, which will return None for the terminal phase, properly ending the flow.
        """
        from app.services.crewai_flows.agents.decision.utils import DecisionUtils

        asset_inventory_results = analysis.get("asset_inventory_results", {})
        assets_created_count = asset_inventory_results.get("assets_created", 0)

        # Calculate completion confidence based on asset creation success
        completion_confidence = ConfidenceCalculator.weighted_average(
            {
                "phase_completed_successfully": 1.0,
                "assets_in_inventory": 1.0 if assets_created_count > 0 else 0.5,
                "discovery_objectives_met": 1.0,
                "terminal_phase_reached": 1.0,  # This is the final phase
            }
        )

        # Get next phase from registry (will be None for terminal phase)
        # This properly delegates to FlowTypeConfig which knows the phase sequence
        next_phase = DecisionUtils.get_next_phase("asset_inventory", "discovery")

        # Discovery flow is COMPLETED - this is the terminal phase per ADR-027
        return AgentDecision(
            action=PhaseAction.PROCEED,
            next_phase=next_phase,  # Will be None or "completed" from registry
            confidence=completion_confidence,
            reasoning=(
                f"Asset inventory phase completed. Created {assets_created_count} assets. "
                "Discovery v3.0.0 flow is now complete (per ADR-027: asset_inventory is the terminal phase). "
                "Dependency analysis and tech debt assessment have moved to Assessment flow."
            ),
            metadata={
                "assets_created_count": assets_created_count,
                "discovery_phase": "completed",
                "next_recommended_flow": "assessment",
                "adr_reference": "ADR-027: Discovery Phase Consolidation",
            },
        )
