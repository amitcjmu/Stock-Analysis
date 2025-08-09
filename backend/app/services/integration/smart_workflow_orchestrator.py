"""
Smart Workflow Orchestrator for ADCS End-to-End Integration

This service orchestrates the complete Collection → Discovery → Assessment workflow,
providing intelligent routing, state management, and seamless integration between phases.

Generated with CC for ADCS end-to-end integration.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.assessment_flow import AssessmentFlow
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow
from app.models.discovery_flow import DiscoveryFlow
from app.monitoring.metrics import track_performance
from app.services.ai_analysis.confidence_scoring import ConfidenceScorer
from app.services.ai_analysis.gap_analysis_agent import GapAnalysisAgent
from app.services.assessment_flow_service import AssessmentManager
from app.services.discovery_flow_service import DiscoveryFlowService

logger = get_logger(__name__)


class WorkflowPhase(Enum):
    """Workflow phases in the smart pipeline"""

    COLLECTION = "collection"
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    COMPLETED = "completed"


class WorkflowTransition(Enum):
    """Valid workflow transitions"""

    COLLECTION_TO_DISCOVERY = "collection_to_discovery"
    DISCOVERY_TO_ASSESSMENT = "discovery_to_assessment"
    ASSESSMENT_TO_COMPLETED = "assessment_to_completed"
    # Recovery transitions
    DISCOVERY_TO_COLLECTION = "discovery_to_collection"
    ASSESSMENT_TO_DISCOVERY = "assessment_to_discovery"


class SmartWorkflowContext:
    """Context object that travels through the workflow phases"""

    def __init__(
        self,
        engagement_id: UUID,
        user_id: UUID,
        client_id: UUID,
        workflow_config: Dict[str, Any] = None,
    ):
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.client_id = client_id
        self.workflow_config = workflow_config or {}
        self.created_at = datetime.utcnow()
        self.current_phase = WorkflowPhase.COLLECTION
        self.phase_history: List[Dict[str, Any]] = []
        self.data_quality_metrics: Dict[str, float] = {}
        self.confidence_scores: Dict[str, float] = {}
        self.error_log: List[Dict[str, Any]] = []

    def add_phase_entry(
        self, phase: WorkflowPhase, status: str, metadata: Dict[str, Any] = None
    ):
        """Add an entry to the phase history"""
        entry = {
            "phase": phase.value,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.phase_history.append(entry)

    def get_current_phase_data(self) -> Dict[str, Any]:
        """Get data for the current phase"""
        return {
            "phase": self.current_phase.value,
            "engagement_id": str(self.engagement_id),
            "user_id": str(self.user_id),
            "client_id": str(self.client_id),
            "confidence_scores": self.confidence_scores,
            "data_quality_metrics": self.data_quality_metrics,
        }


class SmartWorkflowOrchestrator:
    """
    Orchestrates the complete Collection → Discovery → Assessment workflow
    with intelligent transitions and quality gates
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.confidence_scorer = ConfidenceScorer()
        self.gap_analyzer = GapAnalysisAgent()
        self.discovery_service = DiscoveryFlowService(db, context)
        self.assessment_service = AssessmentManager(db, context)

        # Quality thresholds for phase transitions
        self.quality_thresholds = {
            "collection_to_discovery": {
                "min_confidence": 0.70,
                "min_data_completeness": 0.60,
                "max_critical_gaps": 5,
            },
            "discovery_to_assessment": {
                "min_confidence": 0.80,
                "min_data_completeness": 0.75,
                "max_critical_gaps": 2,
            },
        }

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
            collection_flow = await self._get_collection_flow(
                session, context.engagement_id
            )

            if collection_flow and collection_flow.status == "completed":
                # Collection already completed, analyze quality
                quality_metrics = await self._analyze_collection_quality(
                    session, collection_flow
                )
                context.data_quality_metrics.update(quality_metrics)
                context.add_phase_entry(
                    WorkflowPhase.COLLECTION,
                    "completed",
                    {"quality_metrics": quality_metrics},
                )

                # Check if ready for discovery
                if await self._is_ready_for_discovery(context):
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
        if not await self._validate_quality_gates(context, "collection_to_discovery"):
            raise ValueError(
                "Collection quality gates not met for discovery transition"
            )

        # Initialize discovery flow if needed
        async with AsyncSessionLocal() as session:
            discovery_flow = await self._get_or_create_discovery_flow(session, context)
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
            discovery_flow = await self._get_discovery_flow(
                session, context.engagement_id
            )

            if discovery_flow:
                # Check discovery completion status
                if discovery_flow.status == "completed":
                    # Analyze discovery quality and prepare for assessment
                    quality_metrics = await self._analyze_discovery_quality(
                        session, discovery_flow
                    )
                    context.data_quality_metrics.update(quality_metrics)
                    context.add_phase_entry(
                        WorkflowPhase.DISCOVERY,
                        "completed",
                        {"quality_metrics": quality_metrics},
                    )

                    # Check if ready for assessment
                    if await self._is_ready_for_assessment(context):
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
        if not await self._validate_quality_gates(context, "discovery_to_assessment"):
            raise ValueError(
                "Discovery quality gates not met for assessment transition"
            )

        # Initialize assessment flow if needed
        async with AsyncSessionLocal() as session:
            assessment_flow = await self._get_or_create_assessment_flow(
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
            assessment_flow = await self._get_assessment_flow(
                session, context.engagement_id
            )

            if assessment_flow:
                if assessment_flow.status == "completed":
                    # Assessment completed
                    quality_metrics = await self._analyze_assessment_quality(
                        session, assessment_flow
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
        summary = await self._generate_workflow_summary(context)

        context.add_phase_entry(
            WorkflowPhase.COMPLETED, "completed", {"summary": summary}
        )

        context.current_phase = WorkflowPhase.COMPLETED
        return context

    async def _validate_quality_gates(
        self, context: SmartWorkflowContext, transition: str
    ) -> bool:
        """Validate quality gates for phase transitions"""

        thresholds = self.quality_thresholds.get(transition, {})
        metrics = context.data_quality_metrics

        # Check confidence score
        min_confidence = thresholds.get("min_confidence", 0.0)
        current_confidence = metrics.get("overall_confidence", 0.0)
        if current_confidence < min_confidence:
            logger.warning(
                f"Confidence score {current_confidence} below threshold {min_confidence}",
                extra={"engagement_id": str(context.engagement_id)},
            )
            return False

        # Check data completeness
        min_completeness = thresholds.get("min_data_completeness", 0.0)
        current_completeness = metrics.get("data_completeness", 0.0)
        if current_completeness < min_completeness:
            logger.warning(
                f"Data completeness {current_completeness} below threshold {min_completeness}",
                extra={"engagement_id": str(context.engagement_id)},
            )
            return False

        # Check critical gaps
        max_gaps = thresholds.get("max_critical_gaps", float("inf"))
        current_gaps = metrics.get("critical_gaps_count", 0)
        if current_gaps > max_gaps:
            logger.warning(
                f"Critical gaps count {current_gaps} exceeds threshold {max_gaps}",
                extra={"engagement_id": str(context.engagement_id)},
            )
            return False

        return True

    async def _is_ready_for_discovery(self, context: SmartWorkflowContext) -> bool:
        """Check if collection data is ready for discovery phase"""
        return await self._validate_quality_gates(context, "collection_to_discovery")

    async def _is_ready_for_assessment(self, context: SmartWorkflowContext) -> bool:
        """Check if discovery data is ready for assessment phase"""
        # Run validator and require minimum readiness before proceeding
        try:
            from app.services.integration.data_flow_validator import DataFlowValidator

            validator = DataFlowValidator()
            result = await validator.validate_end_to_end_data_flow(
                engagement_id=context.engagement_id,
                validation_scope={"collection", "discovery"},
            )
            # Require decent collection/discovery scores before Assessment
            collection_score = result.phase_scores.get("collection", 0.0)
            discovery_score = result.phase_scores.get("discovery", 0.0)
            min_threshold = float(context.config.get("assessment_gate_threshold", 0.7))
            return (
                collection_score >= min_threshold and discovery_score >= min_threshold
            )
        except Exception:
            # Fallback to legacy gate if validator unavailable
            return await self._validate_quality_gates(
                context, "discovery_to_assessment"
            )

    async def _get_collection_flow(
        self, session: AsyncSession, engagement_id: UUID
    ) -> Optional[CollectionFlow]:
        """Get collection flow for engagement"""
        result = await session.execute(
            select(CollectionFlow).where(CollectionFlow.engagement_id == engagement_id)
        )
        return result.scalar_one_or_none()

    async def _get_discovery_flow(
        self, session: AsyncSession, engagement_id: UUID
    ) -> Optional[DiscoveryFlow]:
        """Get discovery flow for engagement"""
        result = await session.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.engagement_id == engagement_id)
        )
        return result.scalar_one_or_none()

    async def _get_assessment_flow(
        self, session: AsyncSession, engagement_id: UUID
    ) -> Optional[AssessmentFlow]:
        """Get assessment flow for engagement"""
        result = await session.execute(
            select(AssessmentFlow).where(AssessmentFlow.engagement_id == engagement_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_discovery_flow(
        self, session: AsyncSession, context: SmartWorkflowContext
    ) -> DiscoveryFlow:
        """Get or create discovery flow"""
        discovery_flow = await self._get_discovery_flow(session, context.engagement_id)

        if not discovery_flow:
            # Create new discovery flow
            discovery_flow = DiscoveryFlow(
                engagement_id=context.engagement_id,
                user_id=context.user_id,
                client_id=context.client_id,
                status="initiated",
                current_phase="data_import_validation",
                metadata={"initiated_by": "smart_workflow"},
            )
            session.add(discovery_flow)
            await session.commit()
            await session.refresh(discovery_flow)

        return discovery_flow

    async def _get_or_create_assessment_flow(
        self, session: AsyncSession, context: SmartWorkflowContext
    ) -> AssessmentFlow:
        """Get or create assessment flow"""
        assessment_flow = await self._get_assessment_flow(
            session, context.engagement_id
        )

        if not assessment_flow:
            # Create new assessment flow
            assessment_flow = AssessmentFlow(
                engagement_id=context.engagement_id,
                user_id=context.user_id,
                client_id=context.client_id,
                status="initiated",
                current_phase="strategy_analysis",
                metadata={"initiated_by": "smart_workflow"},
            )
            session.add(assessment_flow)
            await session.commit()
            await session.refresh(assessment_flow)

        return assessment_flow

    async def _analyze_collection_quality(
        self, session: AsyncSession, collection_flow: CollectionFlow
    ) -> Dict[str, float]:
        """Analyze collection data quality"""
        # Get collected assets
        assets = await session.execute(
            select(Asset)
            .where(Asset.engagement_id == collection_flow.engagement_id)
            .options(selectinload(Asset.dependencies))
        )
        asset_list = assets.scalars().all()

        if not asset_list:
            return {
                "overall_confidence": 0.0,
                "data_completeness": 0.0,
                "critical_gaps_count": 10,
            }

        # Calculate confidence scores
        confidence_scores = []
        for asset in asset_list:
            score = await self.confidence_scorer.calculate_asset_confidence(asset)
            confidence_scores.append(score)

        # Calculate metrics
        overall_confidence = sum(confidence_scores) / len(confidence_scores)
        data_completeness = await self._calculate_data_completeness(asset_list)
        critical_gaps = await self._count_critical_gaps(asset_list)

        return {
            "overall_confidence": overall_confidence,
            "data_completeness": data_completeness,
            "critical_gaps_count": critical_gaps,
            "asset_count": len(asset_list),
        }

    async def _analyze_discovery_quality(
        self, session: AsyncSession, discovery_flow: DiscoveryFlow
    ) -> Dict[str, float]:
        """Analyze discovery data quality"""
        # Get enriched assets
        assets = await session.execute(
            select(Asset)
            .where(Asset.engagement_id == discovery_flow.engagement_id)
            .options(selectinload(Asset.dependencies))
        )
        asset_list = assets.scalars().all()

        if not asset_list:
            return {
                "overall_confidence": 0.0,
                "data_completeness": 0.0,
                "critical_gaps_count": 5,
            }

        # Calculate enhanced metrics after discovery
        confidence_scores = []
        for asset in asset_list:
            score = await self.confidence_scorer.calculate_asset_confidence(asset)
            confidence_scores.append(score)

        overall_confidence = sum(confidence_scores) / len(confidence_scores)
        data_completeness = await self._calculate_data_completeness(asset_list)
        critical_gaps = await self._count_critical_gaps(asset_list)

        return {
            "overall_confidence": overall_confidence,
            "data_completeness": data_completeness,
            "critical_gaps_count": critical_gaps,
            "discovery_enrichment": overall_confidence
            * 1.1,  # Discovery should improve confidence
        }

    async def _analyze_assessment_quality(
        self, session: AsyncSession, assessment_flow: AssessmentFlow
    ) -> Dict[str, float]:
        """Analyze assessment data quality"""
        # Assessment quality based on completed analysis
        return {
            "overall_confidence": 0.95,  # Assessment should have high confidence
            "data_completeness": 0.90,
            "critical_gaps_count": 0,
            "assessment_coverage": 1.0,
        }

    async def _calculate_data_completeness(self, assets: List[Asset]) -> float:
        """Calculate data completeness score"""
        if not assets:
            return 0.0

        total_fields = 0
        completed_fields = 0

        for asset in assets:
            # Check critical fields
            fields = [
                asset.name,
                asset.type,
                asset.environment,
                asset.business_criticality,
                asset.technical_fit_score,
            ]

            total_fields += len(fields)
            completed_fields += sum(1 for field in fields if field is not None)

        return completed_fields / total_fields if total_fields > 0 else 0.0

    async def _count_critical_gaps(self, assets: List[Asset]) -> int:
        """Count critical data gaps"""
        gaps = 0

        for asset in assets:
            # Critical gaps
            if not asset.business_criticality:
                gaps += 1
            if not asset.technical_fit_score:
                gaps += 1
            if not asset.dependencies:
                gaps += 1

        return gaps

    async def _generate_workflow_summary(
        self, context: SmartWorkflowContext
    ) -> Dict[str, Any]:
        """Generate comprehensive workflow summary"""
        return {
            "engagement_id": str(context.engagement_id),
            "total_duration": (datetime.utcnow() - context.created_at).total_seconds(),
            "phases_completed": len(
                [
                    entry
                    for entry in context.phase_history
                    if entry["status"] == "completed"
                ]
            ),
            "final_confidence": context.data_quality_metrics.get(
                "overall_confidence", 0.0
            ),
            "final_completeness": context.data_quality_metrics.get(
                "data_completeness", 0.0
            ),
            "workflow_success": True,
        }

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
            # Check all flows
            collection_flow = await self._get_collection_flow(session, engagement_id)
            discovery_flow = await self._get_discovery_flow(session, engagement_id)
            assessment_flow = await self._get_assessment_flow(session, engagement_id)

            # Determine current phase and overall status
            current_phase = WorkflowPhase.COLLECTION
            overall_status = "pending"

            if assessment_flow and assessment_flow.status == "completed":
                current_phase = WorkflowPhase.COMPLETED
                overall_status = "completed"
            elif assessment_flow:
                current_phase = WorkflowPhase.ASSESSMENT
                overall_status = assessment_flow.status
            elif discovery_flow and discovery_flow.status == "completed":
                current_phase = WorkflowPhase.ASSESSMENT
                overall_status = "ready_for_assessment"
            elif discovery_flow:
                current_phase = WorkflowPhase.DISCOVERY
                overall_status = discovery_flow.status
            elif collection_flow and collection_flow.status == "completed":
                current_phase = WorkflowPhase.DISCOVERY
                overall_status = "ready_for_discovery"
            elif collection_flow:
                current_phase = WorkflowPhase.COLLECTION
                overall_status = collection_flow.status

            return {
                "engagement_id": str(engagement_id),
                "current_phase": current_phase.value,
                "overall_status": overall_status,
                "flows": {
                    "collection": {
                        "exists": collection_flow is not None,
                        "status": collection_flow.status if collection_flow else None,
                        "id": str(collection_flow.id) if collection_flow else None,
                    },
                    "discovery": {
                        "exists": discovery_flow is not None,
                        "status": discovery_flow.status if discovery_flow else None,
                        "id": str(discovery_flow.id) if discovery_flow else None,
                    },
                    "assessment": {
                        "exists": assessment_flow is not None,
                        "status": assessment_flow.status if assessment_flow else None,
                        "id": str(assessment_flow.id) if assessment_flow else None,
                    },
                },
            }
