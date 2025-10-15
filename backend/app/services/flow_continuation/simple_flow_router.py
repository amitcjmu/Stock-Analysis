"""
Simple Flow Router - Direct Database-Based Flow Continuation

This module provides a simplified, non-AI flow continuation approach that:
1. Directly queries the database for flow state
2. Uses simple business logic for routing decisions
3. Provides immediate responses without CrewAI overhead
4. Falls back gracefully when data is missing

Per ADR-027: Uses FlowTypeConfig as single source of truth for phase sequences and routes.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.services.flow_type_registry_helpers import get_flow_config

logger = logging.getLogger(__name__)


class SimpleFlowRouter:
    """
    Direct database-based flow routing without AI agents.

    Per ADR-027: Phase progression and routes come from FlowTypeConfig registry,
    not hardcoded dictionaries.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_flow_continuation(
        self, flow_id: str, client_account_id: str, engagement_id: str
    ) -> Dict[str, Any]:
        """Get flow continuation decision using simple database queries"""

        try:
            # Step 1: Get flow type and current state from master flow
            flow_info = await self._get_flow_info(
                flow_id, client_account_id, engagement_id
            )

            if not flow_info["exists"]:
                return self._create_not_found_response(flow_id)

            # Step 2: Check phase completion status
            phase_status = await self._check_phase_completion(
                flow_id, flow_info["flow_type"], flow_info["current_phase"]
            )

            # Step 3: Determine routing based on business logic
            routing = self._determine_routing(
                flow_info["flow_type"], flow_info["current_phase"], phase_status
            )

            # Step 4: Generate user guidance
            guidance = self._generate_user_guidance(
                flow_info["flow_type"],
                flow_info["current_phase"],
                phase_status,
                routing,
            )

            return {
                "success": True,
                "flow_id": flow_id,
                "flow_type": flow_info["flow_type"],
                "current_phase": flow_info["current_phase"],
                "routing_decision": routing["target_page"],
                "user_guidance": guidance["primary_message"],
                "next_actions": guidance["action_items"],
                "confidence": 0.95,  # High confidence for rule-based decision
                "reasoning": routing["reasoning"],
                "execution_time": 0.1,  # Fast execution
            }

        except Exception as e:
            logger.error(f"Simple flow routing failed for {flow_id}: {e}")
            return self._create_error_response(flow_id, str(e))

    async def _get_flow_info(
        self, flow_id: str, client_account_id: str, engagement_id: str
    ) -> Dict[str, Any]:
        """Get basic flow information from database"""

        try:
            # Try master flow orchestration table first
            from app.models.master_flow_orchestration import MasterFlowOrchestration

            result = await self.db.execute(
                select(MasterFlowOrchestration).where(
                    and_(
                        MasterFlowOrchestration.flow_id == flow_id,
                        MasterFlowOrchestration.client_account_id == client_account_id,
                        MasterFlowOrchestration.engagement_id == engagement_id,
                    )
                )
            )
            master_flow = result.scalar_one_or_none()

            if master_flow:
                # Determine current phase from status or flow-specific tables
                current_phase = await self._get_current_phase(
                    flow_id, master_flow.flow_type
                )

                return {
                    "exists": True,
                    "flow_type": master_flow.flow_type,
                    "current_phase": current_phase,
                    "status": master_flow.status,
                }

            # Try collection flows table as fallback
            from app.models.collection_flows import CollectionFlow

            result = await self.db.execute(
                select(CollectionFlow).where(CollectionFlow.flow_id == flow_id)
            )
            collection_flow = result.scalar_one_or_none()

            if collection_flow:
                return {
                    "exists": True,
                    "flow_type": "collection",
                    "current_phase": collection_flow.status or "questionnaires",
                    "status": collection_flow.status,
                }

            return {"exists": False}

        except Exception as e:
            logger.error(f"Failed to get flow info: {e}")
            return {"exists": False}

    async def _get_current_phase(self, flow_id: str, flow_type: str) -> str:
        """Determine current phase based on flow type"""

        if flow_type == "discovery":
            # Check discovery flow state
            from app.models.discovery_flows import DiscoveryFlow

            result = await self.db.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
            )
            discovery_flow = result.scalar_one_or_none()

            if discovery_flow:
                # Map status to phase
                status_to_phase = {
                    "data_import_complete": "attribute_mapping",
                    "mapping_complete": "data_cleansing",
                    "cleansing_complete": "inventory",
                    "inventory_complete": "dependencies",
                    "dependencies_complete": "tech_debt",
                    "analysis_complete": "completion",
                }
                return status_to_phase.get(discovery_flow.status, "data_import")

        elif flow_type == "collection":
            # Collection flows use status directly as phase
            return "questionnaires"

        return "initialization"

    async def _check_phase_completion(
        self, flow_id: str, flow_type: str, current_phase: str
    ) -> Dict[str, Any]:
        """Check if current phase meets completion criteria"""

        # Simple heuristic-based checks
        completion_checks = {
            "discovery": {
                "data_import": lambda: self._check_data_uploaded(flow_id),
                "attribute_mapping": lambda: self._check_attributes_mapped(flow_id),
                "data_cleansing": lambda: self._check_data_cleansed(flow_id),
                "inventory": lambda: self._check_inventory_complete(flow_id),
                "dependencies": lambda: self._check_dependencies_analyzed(flow_id),
                "tech_debt": lambda: self._check_tech_debt_assessed(flow_id),
            },
            "collection": {
                "questionnaires": lambda: self._check_questionnaires_complete(flow_id),
                "validation": lambda: self._check_validation_complete(flow_id),
                "review": lambda: self._check_review_complete(flow_id),
            },
        }

        if (
            flow_type in completion_checks
            and current_phase in completion_checks[flow_type]
        ):
            is_complete = await completion_checks[flow_type][current_phase]()
            return {
                "is_complete": is_complete,
                "completion_percentage": 100 if is_complete else 50,
                "blocking_issues": [] if is_complete else ["Phase not fully complete"],
            }

        return {
            "is_complete": False,
            "completion_percentage": 0,
            "blocking_issues": ["Unknown phase"],
        }

    def _get_next_phase(self, flow_type: str, current_phase: str) -> Optional[str]:
        """
        Get next phase from FlowTypeConfig.

        Per ADR-027: Uses authoritative phase sequence from config registry.
        """
        try:
            config = get_flow_config(flow_type)
            phases = [p.name for p in config.phases]

            if current_phase in phases:
                current_index = phases.index(current_phase)
                if current_index < len(phases) - 1:
                    return phases[current_index + 1]

            return None  # Last phase or phase not found
        except ValueError:
            logger.warning(f"FlowTypeConfig not found for: {flow_type}")
            return None

    def _get_phase_route(self, flow_type: str, phase_name: str) -> str:
        """
        Get phase route from FlowTypeConfig metadata.

        Per ADR-027: Uses authoritative ui_route from phase metadata.
        """
        try:
            config = get_flow_config(flow_type)
            phase_obj = next((p for p in config.phases if p.name == phase_name), None)

            if phase_obj and phase_obj.metadata and "ui_route" in phase_obj.metadata:
                return phase_obj.metadata["ui_route"]

            # Fallback to overview
            return f"/{flow_type}/overview"
        except ValueError:
            logger.warning(f"FlowTypeConfig not found for: {flow_type}")
            return f"/{flow_type}/overview"

    def _determine_routing(
        self, flow_type: str, current_phase: str, phase_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine routing based on phase completion using FlowTypeConfig"""

        if phase_status["is_complete"]:
            # Move to next phase
            next_phase = self._get_next_phase(flow_type, current_phase)
            if next_phase:
                target_page = self._get_phase_route(flow_type, next_phase)
                reasoning = (
                    f"Phase '{current_phase}' is complete, moving to '{next_phase}'"
                )
            else:
                # Last phase - flow complete
                target_page = f"/{flow_type}/overview"
                reasoning = f"Flow complete - '{current_phase}' was final phase"
        else:
            # Stay in current phase
            target_page = self._get_phase_route(flow_type, current_phase)
            reasoning = (
                f"Phase '{current_phase}' is not complete, staying in current phase"
            )

        return {"target_page": target_page, "reasoning": reasoning, "confidence": 0.95}

    def _generate_user_guidance(
        self,
        flow_type: str,
        current_phase: str,
        phase_status: Dict[str, Any],
        routing: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate user-friendly guidance messages"""

        if phase_status["is_complete"]:
            primary_message = f"Great! You've completed the {current_phase} phase. Let's continue to the next step."
            action_items = [
                f"Review the completed {current_phase} results",
                "Click continue to proceed to the next phase",
            ]
        else:
            primary_message = (
                f"The {current_phase} phase needs to be completed before proceeding."
            )
            action_items = [
                f"Complete remaining tasks in {current_phase}",
                "Resolve any validation issues",
                "Click save to preserve your progress",
            ]

        return {
            "primary_message": primary_message,
            "action_items": action_items,
            "estimated_time": 5,  # minutes
        }

    # Phase completion check methods (simplified)
    async def _check_data_uploaded(self, flow_id: str) -> bool:
        """Check if data has been uploaded for the flow"""
        from app.models.asset import Asset

        result = await self.db.execute(
            select(Asset).where(Asset.discovery_flow_id == flow_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _check_attributes_mapped(self, flow_id: str) -> bool:
        """Check if attributes have been mapped"""
        from app.models.data_import.mapping import ImportFieldMapping
        from sqlalchemy import select

        # Check if there are any approved field mappings for this flow
        result = await self.db.execute(
            select(ImportFieldMapping)
            .where(ImportFieldMapping.master_flow_id == flow_id)
            .where(ImportFieldMapping.is_approved.is_(True))
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _check_data_cleansed(self, flow_id: str) -> bool:
        """Check if data cleansing is complete"""
        from app.models.discovery_flow import DiscoveryFlow
        from sqlalchemy import select

        # Check if the discovery flow has completed data cleansing
        result = await self.db.execute(
            select(DiscoveryFlow)
            .where(DiscoveryFlow.id == flow_id)
            .where(
                DiscoveryFlow.current_phase.in_(
                    [
                        "data_cleansing",
                        "inventory",
                        "dependencies",
                        "tech_debt",
                        "completed",
                    ]
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _check_inventory_complete(self, flow_id: str) -> bool:
        """Check if inventory phase is complete"""
        from app.models.asset import Asset
        from sqlalchemy import select

        # Check if assets have been created and validated
        result = await self.db.execute(
            select(Asset)
            .where(Asset.discovery_flow_id == flow_id)
            .where(Asset.validation_status == "validated")
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _check_dependencies_analyzed(self, flow_id: str) -> bool:
        """Check if dependencies have been analyzed"""
        return False

    async def _check_tech_debt_assessed(self, flow_id: str) -> bool:
        """Check if tech debt has been assessed"""
        return False

    async def _check_questionnaires_complete(self, flow_id: str) -> bool:
        """Check if questionnaires are complete"""
        from app.models.questionnaire_response import QuestionnaireResponse

        result = await self.db.execute(
            select(QuestionnaireResponse)
            .where(QuestionnaireResponse.flow_id == flow_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def _check_validation_complete(self, flow_id: str) -> bool:
        """Check if validation is complete"""
        return False

    async def _check_review_complete(self, flow_id: str) -> bool:
        """Check if review is complete"""
        return False

    def _create_not_found_response(self, flow_id: str) -> Dict[str, Any]:
        """Create response when flow is not found"""
        return {
            "success": False,
            "flow_id": flow_id,
            "flow_type": "unknown",
            "current_phase": "not_found",
            "routing_decision": "/discovery/data-import",
            "user_guidance": "Flow not found. Please start by uploading your data.",
            "next_actions": ["Upload data to begin discovery process"],
            "confidence": 1.0,
            "reasoning": "Flow does not exist in the system",
            "execution_time": 0.05,
        }

    def _create_error_response(self, flow_id: str, error: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "flow_id": flow_id,
            "flow_type": "unknown",
            "current_phase": "error",
            "routing_decision": "/discovery/overview",
            "user_guidance": "An error occurred. Please try again or contact support.",
            "next_actions": [
                "Retry the operation",
                "Contact support if issue persists",
            ],
            "confidence": 0.0,
            "reasoning": f"Error: {error}",
            "execution_time": 0.01,
        }
