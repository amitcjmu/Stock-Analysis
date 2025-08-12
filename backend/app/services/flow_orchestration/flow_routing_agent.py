"""
Flow Routing Intelligence Agent

This agent provides intelligent flow routing decisions to handle phase transition failures
and automatically redirect flows from problematic states back to appropriate phases.

CC Enhanced for critical flow routing issue where Discovery Flow fails on attribute mapping
when resuming from incomplete initialization phase.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger

from .flow_state_detector import FlowInitializationIssue, FlowStateDetector

logger = get_logger(__name__)


class FlowRoutingDecision:
    """Represents a flow routing decision made by the agent"""

    def __init__(
        self,
        flow_id: str,
        current_phase: str,
        target_phase: str,
        routing_reason: str,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.flow_id = flow_id
        self.current_phase = current_phase
        self.target_phase = target_phase
        self.routing_reason = routing_reason
        self.confidence = confidence
        self.metadata = metadata or {}
        self.decision_timestamp = datetime.utcnow()


class FlowRoutingAgent:
    """
    Intelligent Flow Routing Agent

    This agent analyzes flow states and makes routing decisions to handle:
    - Incomplete initialization detection and recovery
    - Phase transition failures and recovery
    - Automatic redirection to appropriate phases
    - Flow state consistency maintenance
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.flow_detector = FlowStateDetector(db, context)

        # Routing rules configuration
        self.routing_rules = {
            "incomplete_data_import": {
                "target_phase": "data_import",
                "confidence": 0.95,
                "description": "Route to data import when in field mapping but data import incomplete",
            },
            "missing_raw_data": {
                "target_phase": "data_import",
                "confidence": 0.90,
                "description": "Route to data import when no raw data available",
            },
            "orphaned_field_mappings": {
                "target_phase": "data_import",
                "confidence": 0.85,
                "description": "Route to data import to relink orphaned field mappings",
            },
            "invalid_data_import_reference": {
                "target_phase": "data_import",
                "confidence": 0.88,
                "description": "Route to data import to fix invalid references",
            },
            "status_inconsistency": {
                "target_phase": "current",  # Stay in current phase but sync status
                "confidence": 0.75,
                "description": "Sync status between master and child flows",
            },
        }

        logger.info(
            f"✅ Flow Routing Agent initialized for client {context.client_account_id}"
        )

    async def analyze_and_route_flow(
        self, flow_id: str, requested_phase: str = None
    ) -> FlowRoutingDecision:
        """
        Analyze a flow and determine the appropriate routing decision.

        Args:
            flow_id: The flow ID to analyze
            requested_phase: The phase that was requested (if any)

        Returns:
            FlowRoutingDecision with routing recommendation
        """
        try:
            logger.info(f"🔍 Analyzing flow routing for: {flow_id}")

            # Detect initialization issues
            issues = await self.flow_detector.detect_incomplete_initialization(flow_id)

            if not issues:
                # No issues detected - allow normal flow progression
                return FlowRoutingDecision(
                    flow_id=flow_id,
                    current_phase=requested_phase or "unknown",
                    target_phase=requested_phase or "continue",
                    routing_reason="No issues detected - proceed normally",
                    confidence=1.0,
                    metadata={"issues_detected": 0},
                )

            # Prioritize issues and determine routing
            routing_decision = await self._determine_routing_from_issues(
                flow_id, issues, requested_phase
            )

            logger.info(
                f"🧭 Flow routing decision for {flow_id}: "
                f"{routing_decision.current_phase} → {routing_decision.target_phase} "
                f"(confidence: {routing_decision.confidence:.2f})"
            )

            return routing_decision

        except Exception as e:
            logger.error(f"❌ Error analyzing flow routing for {flow_id}: {e}")
            return FlowRoutingDecision(
                flow_id=flow_id,
                current_phase=requested_phase or "unknown",
                target_phase="error_recovery",
                routing_reason=f"Error during routing analysis: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    async def _determine_routing_from_issues(
        self,
        flow_id: str,
        issues: List[FlowInitializationIssue],
        requested_phase: str = None,
    ) -> FlowRoutingDecision:
        """Determine routing decision based on detected issues"""

        # Get current flow state to understand current phase
        current_phase = await self._get_current_flow_phase(flow_id)

        # Prioritize critical issues first
        critical_issues = [i for i in issues if i.severity == "critical"]
        high_issues = [i for i in issues if i.severity == "high"]

        # Handle critical issues - these require immediate attention
        if critical_issues:
            primary_issue = critical_issues[0]
            return FlowRoutingDecision(
                flow_id=flow_id,
                current_phase=current_phase,
                target_phase="initialization",  # Critical issues require reinitialization
                routing_reason=f"Critical issue detected: {primary_issue.description}",
                confidence=0.95,
                metadata={
                    "primary_issue": primary_issue.__dict__,
                    "total_critical_issues": len(critical_issues),
                    "suggested_action": primary_issue.suggested_action,
                },
            )

        # Handle high severity issues - these can often be fixed with routing
        if high_issues:
            # Find the best routing rule match
            best_match = None
            best_confidence = 0.0

            for issue in high_issues:
                if issue.issue_type in self.routing_rules:
                    rule = self.routing_rules[issue.issue_type]
                    if rule["confidence"] > best_confidence:
                        best_match = (issue, rule)
                        best_confidence = rule["confidence"]

            if best_match:
                issue, rule = best_match
                target_phase = rule["target_phase"]

                # Special handling for "current" target phase
                if target_phase == "current":
                    target_phase = current_phase or "status_sync"

                return FlowRoutingDecision(
                    flow_id=flow_id,
                    current_phase=current_phase,
                    target_phase=target_phase,
                    routing_reason=rule["description"],
                    confidence=rule["confidence"],
                    metadata={
                        "matched_rule": issue.issue_type,
                        "issue_description": issue.description,
                        "suggested_action": issue.suggested_action,
                        "total_high_issues": len(high_issues),
                    },
                )

        # Handle medium/low issues - provide guidance but don't force routing
        if issues:
            primary_issue = issues[0]  # Take first issue as primary
            return FlowRoutingDecision(
                flow_id=flow_id,
                current_phase=current_phase,
                target_phase="investigate",
                routing_reason=f"Non-critical issues detected: {primary_issue.description}",
                confidence=0.6,
                metadata={
                    "primary_issue": primary_issue.__dict__,
                    "total_issues": len(issues),
                    "severity_levels": list(set(i.severity for i in issues)),
                },
            )

        # Fallback - should not reach here given the logic above
        return FlowRoutingDecision(
            flow_id=flow_id,
            current_phase=current_phase,
            target_phase="unknown",
            routing_reason="Unable to determine appropriate routing",
            confidence=0.0,
        )

    async def _get_current_flow_phase(self, flow_id: str) -> str:
        """Get the current phase of a flow"""
        try:
            # Try to get from discovery flow first
            discovery_flow = await self.flow_detector._get_discovery_flow(flow_id)
            if discovery_flow and discovery_flow.current_phase:
                return discovery_flow.current_phase

            # Fallback to master flow
            master_flow = await self.flow_detector._get_master_flow(flow_id)
            if master_flow:
                persistence_data = master_flow.flow_persistence_data or {}
                return persistence_data.get("current_phase", "unknown")

            return "unknown"

        except Exception as e:
            logger.error(f"❌ Error getting current phase for {flow_id}: {e}")
            return "unknown"

    async def should_intercept_phase_transition(
        self, flow_id: str, from_phase: str, to_phase: str
    ) -> Tuple[bool, Optional[FlowRoutingDecision]]:
        """
        Determine if a phase transition should be intercepted and redirected.

        Args:
            flow_id: The flow ID
            from_phase: The current phase
            to_phase: The requested target phase

        Returns:
            Tuple of (should_intercept, routing_decision)
        """
        try:
            logger.info(
                f"🔍 Checking phase transition intercept for {flow_id}: {from_phase} → {to_phase}"
            )

            # Special case: If trying to access field_mapping/attribute_mapping, verify readiness
            if to_phase in ["field_mapping", "attribute_mapping"]:
                issues = await self.flow_detector.detect_incomplete_initialization(
                    flow_id
                )

                # Check for data import related issues
                data_import_issues = [
                    i
                    for i in issues
                    if i.issue_type
                    in [
                        "incomplete_data_import",
                        "missing_raw_data",
                        "invalid_data_import_reference",
                    ]
                ]

                if data_import_issues:
                    # Intercept and redirect to data_import
                    routing_decision = FlowRoutingDecision(
                        flow_id=flow_id,
                        current_phase=from_phase,
                        target_phase="data_import",
                        routing_reason=f"Intercepted {to_phase} request due to incomplete data import",
                        confidence=0.92,
                        metadata={
                            "intercepted_transition": f"{from_phase} → {to_phase}",
                            "issues_preventing_transition": [
                                i.__dict__ for i in data_import_issues
                            ],
                            "interception_reason": "data_import_incomplete",
                        },
                    )

                    logger.info(
                        f"🚫 Intercepting phase transition {flow_id}: {from_phase} → {to_phase} "
                        f"due to {len(data_import_issues)} data import issues"
                    )

                    return True, routing_decision

            # No interception needed
            return False, None

        except Exception as e:
            logger.error(
                f"❌ Error checking phase transition intercept for {flow_id}: {e}"
            )
            # Don't intercept on error to avoid breaking the flow
            return False, None

    async def execute_routing_decision(
        self, routing_decision: FlowRoutingDecision
    ) -> Dict[str, Any]:
        """
        Execute a routing decision by updating the flow state appropriately.

        Args:
            routing_decision: The routing decision to execute

        Returns:
            Dictionary with execution results
        """
        try:
            flow_id = routing_decision.flow_id
            target_phase = routing_decision.target_phase

            logger.info(
                f"🔄 Executing routing decision for {flow_id}: "
                f"routing to {target_phase} (confidence: {routing_decision.confidence:.2f})"
            )

            # Handle different target phases
            if target_phase == "data_import":
                return await self._execute_data_import_routing(routing_decision)
            elif target_phase == "initialization":
                return await self._execute_initialization_routing(routing_decision)
            elif target_phase == "status_sync":
                return await self._execute_status_sync_routing(routing_decision)
            elif target_phase == "investigate":
                return await self._execute_investigation_routing(routing_decision)
            elif target_phase in ["continue", "unknown", "error_recovery"]:
                return await self._execute_no_change_routing(routing_decision)
            else:
                # Generic phase routing
                return await self._execute_generic_phase_routing(routing_decision)

        except Exception as e:
            logger.error(
                f"❌ Error executing routing decision for {routing_decision.flow_id}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "routing_decision": routing_decision.__dict__,
            }

    async def _execute_data_import_routing(
        self, routing_decision: FlowRoutingDecision
    ) -> Dict[str, Any]:
        """Execute routing to data import phase"""
        try:
            flow_id = routing_decision.flow_id

            # Update discovery flow to data_import phase
            from app.repositories.discovery_flow_repository import (
                DiscoveryFlowRepository,
            )

            discovery_repo = DiscoveryFlowRepository(
                self.db,
                self.context.client_account_id,
                self.context.engagement_id,
                self.context.user_id,
            )

            # Reset flow state to data_import phase
            updated_flow = await discovery_repo.update_phase_completion(
                flow_id=flow_id,
                phase="data_import",
                data={"routing_decision": routing_decision.__dict__},
                completed=False,
            )

            if updated_flow:
                logger.info(
                    f"✅ Successfully routed flow {flow_id} to data_import phase"
                )
                return {
                    "success": True,
                    "action": "routed_to_data_import",
                    "flow_id": flow_id,
                    "new_phase": "data_import",
                    "routing_reason": routing_decision.routing_reason,
                    "confidence": routing_decision.confidence,
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update flow phase to data_import",
                    "flow_id": flow_id,
                }

        except Exception as e:
            logger.error(
                f"❌ Error executing data import routing for {routing_decision.flow_id}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "action": "data_import_routing_failed",
            }

    async def _execute_initialization_routing(
        self, routing_decision: FlowRoutingDecision
    ) -> Dict[str, Any]:
        """Execute routing to initialization phase for critical issues"""
        # For critical issues, we need to reinitialize the flow
        return {
            "success": True,
            "action": "require_reinitialization",
            "flow_id": routing_decision.flow_id,
            "routing_reason": routing_decision.routing_reason,
            "confidence": routing_decision.confidence,
            "recommendation": "Flow requires complete reinitialization due to critical issues",
        }

    async def _execute_status_sync_routing(
        self, routing_decision: FlowRoutingDecision
    ) -> Dict[str, Any]:
        """Execute status synchronization between master and child flows"""
        # This would sync statuses between flows
        return {
            "success": True,
            "action": "status_sync_required",
            "flow_id": routing_decision.flow_id,
            "routing_reason": routing_decision.routing_reason,
            "confidence": routing_decision.confidence,
        }

    async def _execute_investigation_routing(
        self, routing_decision: FlowRoutingDecision
    ) -> Dict[str, Any]:
        """Execute investigation routing for non-critical issues"""
        return {
            "success": True,
            "action": "investigation_recommended",
            "flow_id": routing_decision.flow_id,
            "routing_reason": routing_decision.routing_reason,
            "confidence": routing_decision.confidence,
            "metadata": routing_decision.metadata,
        }

    async def _execute_no_change_routing(
        self, routing_decision: FlowRoutingDecision
    ) -> Dict[str, Any]:
        """Execute no-change routing (continue normally)"""
        return {
            "success": True,
            "action": "continue_normally",
            "flow_id": routing_decision.flow_id,
            "routing_reason": routing_decision.routing_reason,
            "confidence": routing_decision.confidence,
        }

    async def _execute_generic_phase_routing(
        self, routing_decision: FlowRoutingDecision
    ) -> Dict[str, Any]:
        """Execute generic phase routing"""
        return {
            "success": True,
            "action": "phase_routing",
            "flow_id": routing_decision.flow_id,
            "target_phase": routing_decision.target_phase,
            "routing_reason": routing_decision.routing_reason,
            "confidence": routing_decision.confidence,
        }

    async def get_routing_recommendations(
        self, flow_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get routing recommendations for multiple flows or all active flows.

        Args:
            flow_ids: Optional list of specific flow IDs to analyze

        Returns:
            Dictionary with routing recommendations
        """
        try:
            if flow_ids is None:
                # Analyze all active flows
                analysis = await self.flow_detector.detect_system_wide_issues()
                flow_ids = [f["flow_id"] for f in analysis.get("critical_flows", [])]

                if not flow_ids:
                    return {
                        "success": True,
                        "message": "No flows require routing intervention",
                        "system_analysis": analysis,
                    }

            recommendations = []

            for flow_id in flow_ids:
                routing_decision = await self.analyze_and_route_flow(flow_id)

                if (
                    routing_decision.confidence > 0.7
                    and routing_decision.target_phase not in ["continue", "unknown"]
                ):
                    recommendations.append(
                        {
                            "flow_id": flow_id,
                            "recommendation": routing_decision.__dict__,
                            "priority": (
                                "high"
                                if routing_decision.confidence > 0.9
                                else "medium"
                            ),
                        }
                    )

            return {
                "success": True,
                "recommendations": recommendations,
                "total_flows_analyzed": len(flow_ids),
                "flows_needing_routing": len(recommendations),
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Error getting routing recommendations: {e}")
            return {"success": False, "error": str(e)}
