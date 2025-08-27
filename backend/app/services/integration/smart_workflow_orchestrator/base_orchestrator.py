"""
Base Smart Workflow Orchestrator

This module contains the main SmartWorkflowOrchestrator class that coordinates
the complete Collection → Discovery → Assessment workflow.

Generated with CC for ADCS end-to-end integration.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.monitoring.metrics import track_performance
from app.services.assessment_flow_service import AssessmentManager
from app.services.discovery_flow_service import DiscoveryFlowService

from .flow_manager import FlowManager
from .quality_analyzer import QualityAnalyzer
from .workflow_types import SmartWorkflowContext, WorkflowPhase

logger = get_logger(__name__)


class SmartWorkflowOrchestrator:
    """
    Orchestrates the complete Collection → Discovery → Assessment workflow
    with intelligent transitions and quality gates
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.quality_analyzer = QualityAnalyzer()
        self.flow_manager = FlowManager()
        self.discovery_service = DiscoveryFlowService(db, context)
        self.assessment_service = AssessmentManager(db, context)

    @track_performance("workflow.orchestration.execute")
    async def execute_smart_workflow(
        self,
        engagement_id: UUID,
        user_id: UUID,
        client_id: UUID,
        workflow_config: Dict[str, Any] = None,
    ) -> SmartWorkflowContext:
        """
        Execute the complete smart workflow with intelligent orchestration
        """
        context = SmartWorkflowContext(
            engagement_id=engagement_id,
            user_id=user_id,
            client_id=client_id,
            workflow_config=workflow_config,
        )

        logger.info(
            "Starting smart workflow execution",
            extra={
                "engagement_id": str(engagement_id),
                "user_id": str(user_id),
                "client_id": str(client_id),
                "workflow_config": workflow_config,
            },
        )

        try:
            # Phase 1: Collection (may already be completed)
            context = await self._handle_collection_phase(context)

            # Phase 2: Discovery
            if context.current_phase == WorkflowPhase.COLLECTION:
                context = await self._transition_to_discovery(context)

            context = await self._handle_discovery_phase(context)

            # Phase 3: Assessment
            if context.current_phase == WorkflowPhase.DISCOVERY:
                context = await self._transition_to_assessment(context)

            context = await self._handle_assessment_phase(context)

            # Mark workflow as completed
            if context.current_phase == WorkflowPhase.ASSESSMENT:
                context = await self._complete_workflow(context)

            logger.info(
                "Smart workflow execution completed",
                extra={
                    "engagement_id": str(engagement_id),
                    "final_phase": context.current_phase.value,
                    "duration": (
                        datetime.utcnow() - context.created_at
                    ).total_seconds(),
                },
            )

            return context

        except Exception as e:
            await self._handle_workflow_error(context, e)
            raise

    async def _handle_collection_phase(
        self, context: SmartWorkflowContext
    ) -> SmartWorkflowContext:
        """Handle or verify collection phase completion"""

        logger.info(
            "Handling collection phase",
            extra={"engagement_id": str(context.engagement_id)},
        )

        async with AsyncSessionLocal() as session:
            # Check if collection is already completed
            collection_flow = await self.flow_manager.get_collection_flow(
                session, context.engagement_id
            )

            if collection_flow and collection_flow.status == "completed":
                # Collection already completed, analyze quality
                quality_metrics = (
                    await self.quality_analyzer.analyze_collection_quality(
                        session, collection_flow
                    )
                )
                context.data_quality_metrics.update(quality_metrics)
                context.add_phase_entry(
                    WorkflowPhase.COLLECTION,
                    "completed",
                    {"quality_metrics": quality_metrics},
                )

                # Check if ready for discovery
                if await self.quality_analyzer.is_ready_for_discovery(context):
                    context.current_phase = WorkflowPhase.DISCOVERY

            else:
                # Collection not completed, may need manual intervention
                context.add_phase_entry(
                    WorkflowPhase.COLLECTION,
                    "pending",
                    {"reason": "Collection flow not completed"},
                )

        return context

    async def _transition_to_discovery(
        self, context: SmartWorkflowContext
    ) -> SmartWorkflowContext:
        """Transition from collection to discovery phase"""

        logger.info(
            "Transitioning to discovery phase",
            extra={"engagement_id": str(context.engagement_id)},
        )

        # Validate collection quality gates
        if not await self.quality_analyzer.validate_quality_gates(
            context, "collection_to_discovery"
        ):
            raise ValueError(
                "Collection quality gates not met for discovery transition"
            )

        # Initialize discovery flow if needed
        async with AsyncSessionLocal() as session:
            discovery_flow = await self.flow_manager.get_or_create_discovery_flow(
                session, context
            )
            context.add_phase_entry(
                WorkflowPhase.DISCOVERY,
                "initiated",
                {"discovery_flow_id": str(discovery_flow.id)},
            )

        context.current_phase = WorkflowPhase.DISCOVERY
        return context

    async def _handle_discovery_phase(
        self, context: SmartWorkflowContext
    ) -> SmartWorkflowContext:
        """Handle discovery phase execution"""

        logger.info(
            "Handling discovery phase",
            extra={"engagement_id": str(context.engagement_id)},
        )

        async with AsyncSessionLocal() as session:
            discovery_flow = await self.flow_manager.get_discovery_flow(
                session, context.engagement_id
            )

            if discovery_flow:
                # Check discovery completion status
                if discovery_flow.status == "completed":
                    # Analyze discovery quality and prepare for assessment
                    quality_metrics = (
                        await self.quality_analyzer.analyze_discovery_quality(
                            session, discovery_flow
                        )
                    )
                    context.data_quality_metrics.update(quality_metrics)
                    context.add_phase_entry(
                        WorkflowPhase.DISCOVERY,
                        "completed",
                        {"quality_metrics": quality_metrics},
                    )

                    # Check if ready for assessment
                    if await self.quality_analyzer.is_ready_for_assessment(context):
                        context.current_phase = WorkflowPhase.ASSESSMENT

                elif discovery_flow.status in ["in_progress", "running"]:
                    # Discovery in progress
                    context.add_phase_entry(
                        WorkflowPhase.DISCOVERY,
                        "in_progress",
                        {"discovery_flow_id": str(discovery_flow.id)},
                    )

        return context

    async def _transition_to_assessment(
        self, context: SmartWorkflowContext
    ) -> SmartWorkflowContext:
        """Transition from discovery to assessment phase"""

        logger.info(
            "Transitioning to assessment phase",
            extra={"engagement_id": str(context.engagement_id)},
        )

        # Validate discovery quality gates
        if not await self.quality_analyzer.validate_quality_gates(
            context, "discovery_to_assessment"
        ):
            raise ValueError(
                "Discovery quality gates not met for assessment transition"
            )

        # Initialize assessment flow if needed
        async with AsyncSessionLocal() as session:
            assessment_flow = await self.flow_manager.get_or_create_assessment_flow(
                session, context
            )
            context.add_phase_entry(
                WorkflowPhase.ASSESSMENT,
                "initiated",
                {"assessment_flow_id": str(assessment_flow.id)},
            )

        context.current_phase = WorkflowPhase.ASSESSMENT
        return context

    async def _handle_assessment_phase(
        self, context: SmartWorkflowContext
    ) -> SmartWorkflowContext:
        """Handle assessment phase execution"""

        logger.info(
            "Handling assessment phase",
            extra={"engagement_id": str(context.engagement_id)},
        )

        async with AsyncSessionLocal() as session:
            assessment_flow = await self.flow_manager.get_assessment_flow(
                session, context.engagement_id
            )

            if assessment_flow:
                if assessment_flow.status == "completed":
                    # Assessment completed
                    quality_metrics = (
                        await self.quality_analyzer.analyze_assessment_quality(
                            session, assessment_flow
                        )
                    )
                    context.data_quality_metrics.update(quality_metrics)
                    context.add_phase_entry(
                        WorkflowPhase.ASSESSMENT,
                        "completed",
                        {"quality_metrics": quality_metrics},
                    )

                elif assessment_flow.status in ["in_progress", "running"]:
                    # Assessment in progress
                    context.add_phase_entry(
                        WorkflowPhase.ASSESSMENT,
                        "in_progress",
                        {"assessment_flow_id": str(assessment_flow.id)},
                    )

        return context

    async def _complete_workflow(
        self, context: SmartWorkflowContext
    ) -> SmartWorkflowContext:
        """Complete the workflow and generate final summary"""

        logger.info(
            "Completing workflow", extra={"engagement_id": str(context.engagement_id)}
        )

        # Generate workflow completion summary
        summary = await self.quality_analyzer.generate_workflow_summary(context)

        context.add_phase_entry(
            WorkflowPhase.COMPLETED, "completed", {"summary": summary}
        )

        context.current_phase = WorkflowPhase.COMPLETED
        return context

    async def _handle_workflow_error(
        self, context: SmartWorkflowContext, error: Exception
    ):
        """Handle workflow errors with comprehensive logging"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "current_phase": context.current_phase.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

        context.error_log.append(error_info)

        logger.error(
            "Smart workflow error",
            extra={
                "engagement_id": str(context.engagement_id),
                "error_info": error_info,
            },
        )

    @track_performance("workflow.status.get")
    async def get_workflow_status(self, engagement_id: UUID) -> Dict[str, Any]:
        """Get current workflow status for an engagement"""

        async with AsyncSessionLocal() as session:
            return await self.flow_manager.get_workflow_status(session, engagement_id)
