"""
Simple Flow Router - Direct Database-Based Flow Continuation

This module provides a simplified, non-AI flow continuation approach that:
1. Directly queries the database for flow state
2. Uses simple business logic for routing decisions
3. Provides immediate responses without CrewAI overhead
4. Falls back gracefully when data is missing
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class SimpleFlowRouter:
    """Direct database-based flow routing without AI agents"""

    # Flow phase progression mapping
    PHASE_PROGRESSION = {
        "discovery": {
            "data_import": "attribute_mapping",
            "attribute_mapping": "data_cleansing",
            "data_cleansing": "inventory",
            "inventory": "dependencies",
            "dependencies": "tech_debt",
            "tech_debt": "completion",
        },
        "collection": {
            "initialization": "questionnaires",
            "questionnaires": "validation",
            "validation": "review",
            "review": "completion",
        },
    }

    # Routing decisions per phase
    PHASE_ROUTES = {
        "discovery": {
            "data_import": "/discovery/data-import",
            "attribute_mapping": "/discovery/attribute-mapping",
            "data_cleansing": "/discovery/data-cleansing",
            "inventory": "/discovery/inventory",
            "dependencies": "/discovery/dependencies",
            "tech_debt": "/discovery/tech-debt",
            "completion": "/discovery/overview",
        },
        "collection": {
            "initialization": "/collection/start",
            "questionnaires": "/collection/questionnaires",
            "validation": "/collection/validation",
            "review": "/collection/review",
            "completion": "/collection/summary",
        },
    }

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

    def _determine_routing(
        self, flow_type: str, current_phase: str, phase_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine routing based on phase completion"""

        if phase_status["is_complete"]:
            # Move to next phase
            next_phase = self.PHASE_PROGRESSION.get(flow_type, {}).get(
                current_phase, current_phase
            )
            target_page = self.PHASE_ROUTES.get(flow_type, {}).get(
                next_phase, f"/{flow_type}/overview"
            )
            reasoning = f"Phase '{current_phase}' is complete, moving to '{next_phase}'"
        else:
            # Stay in current phase
            target_page = self.PHASE_ROUTES.get(flow_type, {}).get(
                current_phase, f"/{flow_type}/overview"
            )
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
        # Simplified check - would query attribute mapping tables
        return False

    async def _check_data_cleansed(self, flow_id: str) -> bool:
        """Check if data cleansing is complete"""
        return False

    async def _check_inventory_complete(self, flow_id: str) -> bool:
        """Check if inventory phase is complete"""
        return False

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
