"""
Planning Flow Service - Business Logic Layer

Service layer for planning flow operations following the seven-layer architecture.
Implements business logic, validation, orchestration, and transaction management
for wave planning, resource allocation, timeline generation, and cost estimation.

Architecture:
- Layer 2 (Service Layer): Business logic and orchestration
- Delegates to Layer 3 (Repository Layer): Data access via PlanningFlowRepository
- Integrates with CrewAI agents for AI-driven planning decisions

Related Issues:
- #689 (Wave Planning Flow - Service Layer)
- #690 (Resource Allocation AI Integration)
- #695 (Timeline Generation Service)

ADRs:
- ADR-012: Flow Status Management Separation (Two-Table Pattern)
- ADR-015: Persistent Multi-Tenant Agent Architecture
- ADR-024: TenantMemoryManager (CrewAI memory DISABLED)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import ValidationError, FlowError
from app.models.planning import PlanningFlow
from app.services.crewai_flows.crews.planning_crew import PlanningCrew

logger = logging.getLogger(__name__)


class PlanningFlowService:
    """
    Service for planning flow business logic.

    Orchestrates wave planning, resource allocation, timeline generation,
    and cost estimation workflows using CrewAI agents and structured data.

    Per ADR-012: Operates on child flow (planning_flows) operational state.
    Master flow lifecycle managed in crewai_flow_state_extensions.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize planning service with database session and request context.

        Args:
            db: Async SQLAlchemy database session
            context: Request context with tenant scoping (client_account_id, engagement_id)
        """
        self.db = db
        self.context = context

        # Repository will be initialized when available (parallel development)
        # from app.repositories.planning_repository import PlanningFlowRepository
        # self.repository = PlanningFlowRepository(
        #     db=self.db,
        #     client_account_id=context.client_account_id,
        #     engagement_id=context.engagement_id
        # )

        # Initialize PlanningCrew for CrewAI agent orchestration
        self.planning_crew = PlanningCrew()

        logger.info(
            f"PlanningFlowService initialized - Client: {context.client_account_id}, "
            f"Engagement: {context.engagement_id}"
        )

    # ========================================
    # FLOW INITIALIZATION
    # ========================================

    async def initialize_planning_flow(
        self,
        master_flow_id: UUID,
        selected_applications: List[UUID],
        planning_config: Optional[Dict[str, Any]] = None,
    ) -> PlanningFlow:
        """
        Initialize new planning flow from assessment results.

        Business Logic:
        1. Validate assessment completion (prerequisite check)
        2. Validate selected applications exist and are assessment-ready
        3. Validate planning configuration against business rules
        4. Create planning flow record with initial phase 'wave_planning'
        5. Store planning configuration and selected applications

        Args:
            master_flow_id: UUID of master flow from MFO
            selected_applications: List of asset UUIDs from assessment flow
            planning_config: Optional planning configuration (max_apps_per_wave, etc.)

        Returns:
            Created PlanningFlow entity

        Raises:
            ValidationError: If prerequisites not met or invalid configuration
            FlowError: If flow creation fails

        Example:
            planning_flow = await service.initialize_planning_flow(
                master_flow_id=UUID("..."),
                selected_applications=[UUID("app1"), UUID("app2")],
                planning_config={
                    "max_apps_per_wave": 5,
                    "wave_duration_limit_days": 90,
                    "sequencing_rules": {"critical_first": True}
                }
            )
        """
        try:
            logger.info(
                f"🚀 Initializing planning flow for master {master_flow_id} "
                f"with {len(selected_applications)} applications"
            )

            # Validate planning configuration
            validated_config = await self.validate_planning_config(
                planning_config or {}
            )

            # Validate selected applications (business rule: at least 1 required)
            if not selected_applications:
                raise ValidationError(
                    "At least one application must be selected for planning",
                    field="selected_applications",
                    value=selected_applications,
                )

            # TODO: When repository is available, uncomment:
            # # Verify applications exist and are assessment-ready
            # await self._validate_assessment_prerequisites(
            #     selected_applications
            # )

            # Create planning flow with atomic transaction
            async with self.db.begin():
                planning_flow = PlanningFlow(
                    client_account_id=self.context.client_account_id,
                    engagement_id=self.context.engagement_id,
                    master_flow_id=master_flow_id,
                    planning_flow_id=uuid4(),
                    current_phase="wave_planning",
                    phase_status="ready",
                    planning_config=validated_config,
                    selected_applications=[
                        str(app_id) for app_id in selected_applications
                    ],
                    wave_plan_data={},
                    resource_allocation_data={},
                    timeline_data={},
                    cost_estimation_data={},
                    agent_execution_log=[],
                    ui_state={
                        "initialized_at": datetime.utcnow().isoformat(),
                        "selected_app_count": len(selected_applications),
                    },
                    validation_errors=[],
                    warnings=[],
                    planning_ready_at=datetime.utcnow(),
                )

                self.db.add(planning_flow)
                await self.db.flush()  # Get ID for logging

                logger.info(
                    f"✅ Planning flow initialized: {planning_flow.planning_flow_id} "
                    f"(Phase: {planning_flow.current_phase})"
                )

                return planning_flow

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize planning flow: {e}", exc_info=True)
            raise FlowError(
                f"Planning flow initialization failed: {str(e)}",
                flow_name="planning",
                flow_id=str(master_flow_id),
            )

    # ========================================
    # PHASE EXECUTION
    # ========================================

    async def execute_wave_planning_phase(
        self,
        planning_flow_id: UUID,
    ) -> Dict[str, Any]:
        """
        Execute wave planning phase using WavePlanningSpecialist agent.

        Business Logic:
        1. Validate planning flow exists and in 'wave_planning' phase
        2. Fetch selected applications with 6R strategies from assessment
        3. Invoke WavePlanningSpecialist agent with planning config
        4. Parse agent output (wave assignments, sequencing, dependencies)
        5. Save wave plan results to wave_plan_data JSONB
        6. Update phase to 'resource_allocation' on success
        7. Log agent execution details

        Args:
            planning_flow_id: UUID of planning flow

        Returns:
            Dict containing wave plan data:
            {
                "waves": [
                    {
                        "wave_number": 1,
                        "wave_name": "Wave 1 - Quick Wins",
                        "applications": [UUID, ...],
                        "start_date": "2025-01-01",
                        "end_date": "2025-03-31",
                        "dependencies": []
                    },
                    ...
                ],
                "total_waves": 3,
                "planning_metadata": {...}
            }

        Raises:
            ValidationError: If flow not in correct phase
            FlowError: If agent execution fails
        """
        try:
            logger.info(f"🎯 Executing wave planning phase for {planning_flow_id}")

            # Get planning flow with tenant scoping
            planning_flow = await self._get_planning_flow(planning_flow_id)

            # Validate phase transition
            if planning_flow.current_phase != "wave_planning":
                raise ValidationError(
                    f"Cannot execute wave planning. Current phase: {planning_flow.current_phase}",
                    field="current_phase",
                    value=planning_flow.current_phase,
                )

            # Update phase status to 'running'
            planning_flow.phase_status = "running"
            await self.db.flush()

            # Execute WavePlanningSpecialist agent via PlanningCrew
            # Convert selected_applications to proper format for crew
            selected_apps_metadata = [
                {"id": app_id} for app_id in planning_flow.selected_applications
            ]

            wave_plan_result = self.planning_crew.execute_wave_planning(
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                selected_applications=selected_apps_metadata,
                planning_config=planning_flow.planning_config,
            )

            # Save wave plan data
            planning_flow.wave_plan_data = wave_plan_result
            planning_flow.agent_execution_log.append(
                {
                    "phase": "wave_planning",
                    "executed_at": datetime.utcnow().isoformat(),
                    "agent": "WavePlanningSpecialist",
                    "status": "completed",
                    "waves_generated": wave_plan_result.get("total_waves", 0),
                }
            )

            # Transition to next phase
            planning_flow.current_phase = "resource_allocation"
            planning_flow.phase_status = "ready"

            await self.db.flush()

            logger.info(
                f"✅ Wave planning completed: {wave_plan_result['total_waves']} waves generated"
            )

            return wave_plan_result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Wave planning phase failed: {e}", exc_info=True)
            raise FlowError(
                f"Wave planning execution failed: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )

    async def execute_resource_allocation_phase(
        self,
        planning_flow_id: UUID,
        manual_override: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute resource allocation phase (AI + manual override).

        Business Logic:
        1. Validate wave plan exists (prerequisite)
        2. Fetch wave plan data from wave_plan_data JSONB
        3. Invoke ResourceAllocationSpecialist agent for AI suggestions
        4. Generate role-based resource allocations per wave
        5. If manual_override=False, save AI suggestions to resource_allocation_data
        6. If manual_override=True, allow user to modify (UI-driven)
        7. Update phase to 'timeline_generation' when finalized
        8. Calculate skill gaps (non-blocking warnings per #690)

        Args:
            planning_flow_id: UUID of planning flow
            manual_override: If True, AI suggestions are advisory only

        Returns:
            Dict containing resource allocation data:
            {
                "allocations": [
                    {
                        "wave_id": UUID,
                        "wave_number": 1,
                        "resources": [
                            {
                                "role_name": "Cloud Architect",
                                "allocated_hours": 160,
                                "hourly_rate": 150.0,
                                "estimated_cost": 24000.0,
                                "is_ai_suggested": True,
                                "ai_confidence_score": 0.85
                            },
                            ...
                        ]
                    }
                ],
                "skill_gaps": [
                    {
                        "skill_name": "Kubernetes",
                        "severity": "medium",
                        "impact": "May require external training"
                    }
                ],
                "total_cost_estimate": 125000.0
            }

        Raises:
            ValidationError: If wave plan not completed
            FlowError: If agent execution fails
        """
        try:
            logger.info(
                f"💼 Executing resource allocation phase for {planning_flow_id} "
                f"(manual_override={manual_override})"
            )

            # Get planning flow
            planning_flow = await self._get_planning_flow(planning_flow_id)

            # Validate prerequisites
            if planning_flow.current_phase != "resource_allocation":
                raise ValidationError(
                    f"Cannot execute resource allocation. Current phase: {planning_flow.current_phase}",
                    field="current_phase",
                    value=planning_flow.current_phase,
                )

            if not planning_flow.wave_plan_data:
                raise ValidationError(
                    "Wave plan must be completed before resource allocation",
                    field="wave_plan_data",
                )

            # Update phase status
            planning_flow.phase_status = "running"
            await self.db.flush()

            # Execute ResourceAllocationSpecialist agent via PlanningCrew
            # Prepare resource pools (placeholder - would come from config or database)
            resource_pools = [
                {"role_name": "Cloud Architect", "hourly_rate": 150.0},
                {"role_name": "DevOps Engineer", "hourly_rate": 125.0},
                {"role_name": "QA Engineer", "hourly_rate": 100.0},
            ]

            allocation_result = self.planning_crew.execute_resource_allocation(
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                wave_plan=planning_flow.wave_plan_data,
                resource_pools=resource_pools,
                planning_config=planning_flow.planning_config,
            )

            # Mark as AI-suggested if not manual override
            allocation_result["is_ai_suggested"] = not manual_override

            # Save allocation data
            planning_flow.resource_allocation_data = allocation_result
            planning_flow.agent_execution_log.append(
                {
                    "phase": "resource_allocation",
                    "executed_at": datetime.utcnow().isoformat(),
                    "agent": "ResourceAllocationSpecialist",
                    "status": "completed",
                    "manual_override": manual_override,
                    "total_cost": allocation_result["total_cost_estimate"],
                }
            )

            # Add skill gap warnings (non-blocking per #690)
            if allocation_result.get("skill_gaps"):
                planning_flow.warnings.extend(
                    [
                        f"Skill gap identified: {gap['skill_name']} - {gap['impact']}"
                        for gap in allocation_result["skill_gaps"]
                    ]
                )

            # Transition to next phase if not manual override
            if not manual_override:
                planning_flow.current_phase = "timeline_generation"
                planning_flow.phase_status = "ready"

            await self.db.flush()

            logger.info(
                f"✅ Resource allocation completed: ${allocation_result['total_cost_estimate']:,.2f}"
            )

            return allocation_result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Resource allocation phase failed: {e}", exc_info=True)
            raise FlowError(
                f"Resource allocation execution failed: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )

    async def execute_timeline_generation_phase(
        self,
        planning_flow_id: UUID,
    ) -> Dict[str, Any]:
        """
        Execute timeline generation phase for Gantt chart visualization.

        Business Logic:
        1. Validate wave plan and resource allocation completed
        2. Generate timeline with phases, milestones, dependencies
        3. Calculate critical path using PERT/CPM algorithms
        4. Assign resources to timeline phases
        5. Save timeline data to timeline_data JSONB
        6. Create ProjectTimeline, TimelinePhase, TimelineMilestone records
        7. Update phase to 'cost_estimation'

        Args:
            planning_flow_id: UUID of planning flow

        Returns:
            Dict containing timeline data with Gantt chart structure

        Raises:
            ValidationError: If prerequisites not met
            FlowError: If timeline generation fails
        """
        try:
            logger.info(
                f"📅 Executing timeline generation phase for {planning_flow_id}"
            )

            # Get planning flow
            planning_flow = await self._get_planning_flow(planning_flow_id)

            # Validate prerequisites
            if planning_flow.current_phase != "timeline_generation":
                raise ValidationError(
                    f"Cannot execute timeline generation. Current phase: {planning_flow.current_phase}",
                    field="current_phase",
                    value=planning_flow.current_phase,
                )

            if not planning_flow.resource_allocation_data:
                raise ValidationError(
                    "Resource allocation must be completed before timeline generation",
                    field="resource_allocation_data",
                )

            # Update phase status
            planning_flow.phase_status = "running"
            await self.db.flush()

            # Execute TimelineGenerationSpecialist agent via PlanningCrew
            timeline_result = self.planning_crew.execute_timeline_generation(
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                wave_plan=planning_flow.wave_plan_data,
                resource_allocation=planning_flow.resource_allocation_data,
                planning_config=planning_flow.planning_config,
            )

            # Save timeline data
            planning_flow.timeline_data = timeline_result
            planning_flow.agent_execution_log.append(
                {
                    "phase": "timeline_generation",
                    "executed_at": datetime.utcnow().isoformat(),
                    "agent": "TimelinePlanningSpecialist",
                    "status": "completed",
                }
            )

            # Transition to next phase
            planning_flow.current_phase = "cost_estimation"
            planning_flow.phase_status = "ready"

            await self.db.flush()

            logger.info("✅ Timeline generation completed")

            return timeline_result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Timeline generation phase failed: {e}", exc_info=True)
            raise FlowError(
                f"Timeline generation execution failed: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )

    async def execute_cost_estimation_phase(
        self,
        planning_flow_id: UUID,
    ) -> Dict[str, Any]:
        """
        Execute cost estimation phase for migration budget planning.

        Business Logic:
        1. Aggregate resource costs from resource_allocation_data
        2. Calculate infrastructure costs (compute, storage, network)
        3. Add license and third-party service costs
        4. Include contingency buffer (configurable, default 15%)
        5. Generate cost breakdown by wave, category, timeline phase
        6. Save cost data to cost_estimation_data JSONB
        7. Update phase to 'synthesis' (final phase)

        Args:
            planning_flow_id: UUID of planning flow

        Returns:
            Dict containing comprehensive cost estimation

        Raises:
            ValidationError: If prerequisites not met
            FlowError: If cost estimation fails
        """
        try:
            logger.info(f"💰 Executing cost estimation phase for {planning_flow_id}")

            # Get planning flow
            planning_flow = await self._get_planning_flow(planning_flow_id)

            # Validate prerequisites
            if planning_flow.current_phase != "cost_estimation":
                raise ValidationError(
                    f"Cannot execute cost estimation. Current phase: {planning_flow.current_phase}",
                    field="current_phase",
                    value=planning_flow.current_phase,
                )

            # Update phase status
            planning_flow.phase_status = "running"
            await self.db.flush()

            # Execute CostEstimationSpecialist agent via PlanningCrew
            cost_result = self.planning_crew.execute_cost_estimation(
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
                wave_plan=planning_flow.wave_plan_data,
                resource_allocation=planning_flow.resource_allocation_data,
                timeline=planning_flow.timeline_data,
                planning_config=planning_flow.planning_config,
            )

            # Save cost data
            planning_flow.cost_estimation_data = cost_result
            planning_flow.agent_execution_log.append(
                {
                    "phase": "cost_estimation",
                    "executed_at": datetime.utcnow().isoformat(),
                    "status": "completed",
                    "total_cost": cost_result["total_estimated_cost"],
                }
            )

            # Transition to synthesis phase
            planning_flow.current_phase = "synthesis"
            planning_flow.phase_status = "ready"

            await self.db.flush()

            logger.info(
                f"✅ Cost estimation completed: ${cost_result['total_estimated_cost']:,.2f}"
            )

            return cost_result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Cost estimation phase failed: {e}", exc_info=True)
            raise FlowError(
                f"Cost estimation execution failed: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )

    async def execute_synthesis_phase(
        self,
        planning_flow_id: UUID,
    ) -> Dict[str, Any]:
        """
        Synthesize all planning results into comprehensive planning report.

        Business Logic:
        1. Validate all phases completed (wave plan, resources, timeline, costs)
        2. Aggregate all planning data into unified structure
        3. Generate executive summary with key metrics
        4. Create recommendations for plan optimization
        5. Generate comprehensive planning report
        6. Update phase to 'completed' and set planning_completed_at timestamp
        7. Mark planning flow ready for export (PDF/Excel/JSON)

        Args:
            planning_flow_id: UUID of planning flow

        Returns:
            Dict containing comprehensive planning report:
            {
                "executive_summary": {...},
                "wave_plan": {...},
                "resource_allocation": {...},
                "timeline": {...},
                "cost_estimation": {...},
                "recommendations": [...],
                "key_metrics": {...}
            }

        Raises:
            ValidationError: If any phase incomplete
            FlowError: If synthesis fails
        """
        try:
            logger.info(f"📊 Executing synthesis phase for {planning_flow_id}")

            # Get planning flow
            planning_flow = await self._get_planning_flow(planning_flow_id)

            # Validate all phases completed
            if planning_flow.current_phase != "synthesis":
                raise ValidationError(
                    f"Cannot execute synthesis. Current phase: {planning_flow.current_phase}",
                    field="current_phase",
                    value=planning_flow.current_phase,
                )

            # Validate all required data exists
            validation_errors = []
            if not planning_flow.wave_plan_data:
                validation_errors.append("Wave plan data missing")
            if not planning_flow.resource_allocation_data:
                validation_errors.append("Resource allocation data missing")
            if not planning_flow.timeline_data:
                validation_errors.append("Timeline data missing")
            if not planning_flow.cost_estimation_data:
                validation_errors.append("Cost estimation data missing")

            if validation_errors:
                raise ValidationError(
                    "Cannot synthesize planning report - incomplete phases",
                    details={"missing_data": validation_errors},
                )

            # Update phase status
            planning_flow.phase_status = "running"
            await self.db.flush()

            # Generate synthesis report
            synthesis_result = {
                "executive_summary": {
                    "total_applications": len(planning_flow.selected_applications),
                    "total_waves": planning_flow.wave_plan_data.get("total_waves", 0),
                    "total_duration_days": self._calculate_total_duration(
                        planning_flow.timeline_data
                    ),
                    "total_cost": planning_flow.cost_estimation_data.get(
                        "total_estimated_cost", 0.0
                    ),
                    "resource_count": len(
                        planning_flow.resource_allocation_data.get("allocations", [])
                    ),
                    "skill_gaps_identified": len(
                        planning_flow.resource_allocation_data.get("skill_gaps", [])
                    ),
                },
                "wave_plan": planning_flow.wave_plan_data,
                "resource_allocation": planning_flow.resource_allocation_data,
                "timeline": planning_flow.timeline_data,
                "cost_estimation": planning_flow.cost_estimation_data,
                "recommendations": await self._generate_recommendations(planning_flow),
                "key_metrics": {
                    "avg_cost_per_app": (
                        planning_flow.cost_estimation_data.get(
                            "total_estimated_cost", 0.0
                        )
                        / len(planning_flow.selected_applications)
                        if planning_flow.selected_applications
                        else 0.0
                    ),
                    "avg_duration_per_wave": (
                        self._calculate_total_duration(planning_flow.timeline_data)
                        / planning_flow.wave_plan_data.get("total_waves", 1)
                    ),
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

            # Mark flow completed
            planning_flow.current_phase = "completed"
            planning_flow.phase_status = "completed"
            planning_flow.planning_completed_at = datetime.utcnow()
            planning_flow.agent_execution_log.append(
                {
                    "phase": "synthesis",
                    "executed_at": datetime.utcnow().isoformat(),
                    "status": "completed",
                }
            )

            await self.db.flush()

            logger.info(
                f"✅ Planning synthesis completed: {synthesis_result['executive_summary']['total_waves']} waves, "
                f"${synthesis_result['executive_summary']['total_cost']:,.2f} total cost"
            )

            return synthesis_result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Synthesis phase failed: {e}", exc_info=True)
            raise FlowError(
                f"Planning synthesis execution failed: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )

    # ========================================
    # STATUS & UPDATES
    # ========================================

    async def get_planning_status(
        self,
        planning_flow_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get current planning flow status and progress.

        Returns comprehensive status including current phase, progress percentage,
        completed phases, agent execution log, and warnings.

        Args:
            planning_flow_id: UUID of planning flow

        Returns:
            Dict containing status information:
            {
                "planning_flow_id": str,
                "current_phase": str,
                "phase_status": str,
                "progress_percentage": float,
                "completed_phases": List[str],
                "warnings": List[str],
                "validation_errors": List[str],
                "planning_started_at": str,
                "planning_completed_at": Optional[str]
            }

        Raises:
            FlowError: If flow not found
        """
        try:
            planning_flow = await self._get_planning_flow(planning_flow_id)

            # Calculate progress based on completed phases
            phase_sequence = [
                "wave_planning",
                "resource_allocation",
                "timeline_generation",
                "cost_estimation",
                "synthesis",
                "completed",
            ]
            current_phase_index = (
                phase_sequence.index(planning_flow.current_phase)
                if planning_flow.current_phase in phase_sequence
                else 0
            )
            progress_percentage = (current_phase_index / len(phase_sequence)) * 100

            # Identify completed phases from agent execution log
            completed_phases = [
                log["phase"]
                for log in planning_flow.agent_execution_log
                if log.get("status") == "completed"
            ]

            return {
                "planning_flow_id": str(planning_flow.planning_flow_id),
                "master_flow_id": str(planning_flow.master_flow_id),
                "current_phase": planning_flow.current_phase,
                "phase_status": planning_flow.phase_status,
                "progress_percentage": progress_percentage,
                "completed_phases": completed_phases,
                "warnings": planning_flow.warnings,
                "validation_errors": planning_flow.validation_errors,
                "planning_started_at": (
                    planning_flow.planning_started_at.isoformat()
                    if planning_flow.planning_started_at
                    else None
                ),
                "planning_completed_at": (
                    planning_flow.planning_completed_at.isoformat()
                    if planning_flow.planning_completed_at
                    else None
                ),
                "selected_applications_count": len(planning_flow.selected_applications),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get planning status: {e}", exc_info=True)
            raise FlowError(
                f"Failed to retrieve planning status: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )

    async def update_wave_plan(
        self,
        planning_flow_id: UUID,
        wave_plan_data: Dict[str, Any],
    ) -> PlanningFlow:
        """
        Update wave plan data (manual override after AI generation).

        Allows users to modify AI-generated wave plans before proceeding to
        resource allocation. Validates wave plan structure and updates
        wave_plan_data JSONB column.

        Args:
            planning_flow_id: UUID of planning flow
            wave_plan_data: Updated wave plan data structure

        Returns:
            Updated PlanningFlow entity

        Raises:
            ValidationError: If wave plan structure invalid
            FlowError: If update fails
        """
        try:
            logger.info(f"📝 Updating wave plan for {planning_flow_id}")

            # Get planning flow
            planning_flow = await self._get_planning_flow(planning_flow_id)

            # Validate wave plan structure
            await self._validate_wave_plan_structure(wave_plan_data)

            # Update wave plan data
            planning_flow.wave_plan_data = wave_plan_data
            planning_flow.agent_execution_log.append(
                {
                    "phase": "wave_planning",
                    "executed_at": datetime.utcnow().isoformat(),
                    "action": "manual_update",
                    "waves_updated": wave_plan_data.get("total_waves", 0),
                }
            )

            await self.db.flush()

            logger.info(
                f"✅ Wave plan updated: {wave_plan_data.get('total_waves', 0)} waves"
            )

            return planning_flow

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update wave plan: {e}", exc_info=True)
            raise FlowError(
                f"Wave plan update failed: {str(e)}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )

    # ========================================
    # VALIDATION
    # ========================================

    async def validate_planning_config(
        self,
        planning_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate planning configuration against business rules.

        Validation Rules (from #689):
        - max_apps_per_wave: integer > 0 (default 5)
        - wave_duration_limit_days: integer > 0 (default 90)
        - sequencing_rules: valid rule structure
        - contingency_percentage: float 0-100 (default 15)

        Args:
            planning_config: Planning configuration dictionary

        Returns:
            Validated configuration with defaults applied

        Raises:
            ValidationError: If configuration invalid
        """
        try:
            # Apply defaults
            validated_config = {
                "max_apps_per_wave": planning_config.get("max_apps_per_wave", 5),
                "wave_duration_limit_days": planning_config.get(
                    "wave_duration_limit_days", 90
                ),
                "sequencing_rules": planning_config.get("sequencing_rules", {}),
                "contingency_percentage": planning_config.get(
                    "contingency_percentage", 15.0
                ),
            }

            # Validate max_apps_per_wave
            if not isinstance(validated_config["max_apps_per_wave"], int):
                raise ValidationError(
                    "max_apps_per_wave must be an integer",
                    field="max_apps_per_wave",
                    value=validated_config["max_apps_per_wave"],
                )
            if validated_config["max_apps_per_wave"] <= 0:
                raise ValidationError(
                    "max_apps_per_wave must be greater than 0",
                    field="max_apps_per_wave",
                    value=validated_config["max_apps_per_wave"],
                )

            # Validate wave_duration_limit_days
            if not isinstance(validated_config["wave_duration_limit_days"], int):
                raise ValidationError(
                    "wave_duration_limit_days must be an integer",
                    field="wave_duration_limit_days",
                    value=validated_config["wave_duration_limit_days"],
                )
            if validated_config["wave_duration_limit_days"] <= 0:
                raise ValidationError(
                    "wave_duration_limit_days must be greater than 0",
                    field="wave_duration_limit_days",
                    value=validated_config["wave_duration_limit_days"],
                )

            # Validate contingency_percentage
            if not isinstance(validated_config["contingency_percentage"], (int, float)):
                raise ValidationError(
                    "contingency_percentage must be a number",
                    field="contingency_percentage",
                    value=validated_config["contingency_percentage"],
                )
            if not (0 <= validated_config["contingency_percentage"] <= 100):
                raise ValidationError(
                    "contingency_percentage must be between 0 and 100",
                    field="contingency_percentage",
                    value=validated_config["contingency_percentage"],
                )

            logger.info(
                f"✅ Planning config validated: max_apps={validated_config['max_apps_per_wave']}, "
                f"duration_limit={validated_config['wave_duration_limit_days']} days"
            )

            return validated_config

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Config validation failed: {e}", exc_info=True)
            raise ValidationError(f"Planning configuration validation failed: {str(e)}")

    async def calculate_wave_capacity(
        self,
        wave_plan_data: Dict[str, Any],
        resource_allocation_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate resource utilization and capacity warnings.

        Analyzes resource allocations against available capacity and generates
        warnings for over-allocation or skill gaps.

        Args:
            wave_plan_data: Wave plan structure with wave definitions
            resource_allocation_data: Resource allocation with hours and costs

        Returns:
            Dict containing capacity analysis:
            {
                "waves": [
                    {
                        "wave_number": 1,
                        "total_allocated_hours": 480,
                        "utilization_percentage": 85.0,
                        "warnings": []
                    }
                ],
                "overall_utilization": 78.0,
                "capacity_warnings": []
            }

        Raises:
            ValidationError: If data structures invalid
        """
        try:
            capacity_analysis = {
                "waves": [],
                "overall_utilization": 0.0,
                "capacity_warnings": [],
            }

            # Analyze each wave
            for wave in wave_plan_data.get("waves", []):
                wave_number = wave["wave_number"]

                # Find matching allocation
                wave_allocation = next(
                    (
                        alloc
                        for alloc in resource_allocation_data.get("allocations", [])
                        if alloc["wave_number"] == wave_number
                    ),
                    None,
                )

                if wave_allocation:
                    total_hours = sum(
                        r["allocated_hours"] for r in wave_allocation["resources"]
                    )

                    # Calculate utilization (placeholder - would use actual capacity data)
                    utilization = min((total_hours / 2000) * 100, 100)

                    wave_capacity = {
                        "wave_number": wave_number,
                        "total_allocated_hours": total_hours,
                        "utilization_percentage": utilization,
                        "warnings": [],
                    }

                    # Add warnings for high utilization
                    if utilization > 90:
                        warning = f"Wave {wave_number} has high resource utilization ({utilization:.1f}%)"
                        wave_capacity["warnings"].append(warning)
                        capacity_analysis["capacity_warnings"].append(warning)

                    capacity_analysis["waves"].append(wave_capacity)

            # Calculate overall utilization
            if capacity_analysis["waves"]:
                capacity_analysis["overall_utilization"] = sum(
                    w["utilization_percentage"] for w in capacity_analysis["waves"]
                ) / len(capacity_analysis["waves"])

            logger.info(
                f"✅ Capacity analysis completed: {capacity_analysis['overall_utilization']:.1f}% overall utilization"
            )

            return capacity_analysis

        except Exception as e:
            logger.error(f"❌ Capacity calculation failed: {e}", exc_info=True)
            raise ValidationError(f"Capacity calculation failed: {str(e)}")

    # ========================================
    # HELPER METHODS
    # ========================================

    async def _get_planning_flow(self, planning_flow_id: UUID) -> PlanningFlow:
        """
        Get planning flow with tenant scoping.

        Args:
            planning_flow_id: UUID of planning flow

        Returns:
            PlanningFlow entity

        Raises:
            FlowError: If flow not found
        """
        # TODO: Use repository when available
        # planning_flow = await self.repository.get_by_planning_flow_id(planning_flow_id)

        # Placeholder query with tenant scoping
        from sqlalchemy import select

        result = await self.db.execute(
            select(PlanningFlow).where(
                PlanningFlow.planning_flow_id == planning_flow_id,
                PlanningFlow.client_account_id == self.context.client_account_id,
                PlanningFlow.engagement_id == self.context.engagement_id,
            )
        )
        planning_flow = result.scalar_one_or_none()

        if not planning_flow:
            raise FlowError(
                f"Planning flow not found: {planning_flow_id}",
                flow_name="planning",
                flow_id=str(planning_flow_id),
            )

        return planning_flow

    async def _validate_wave_plan_structure(
        self, wave_plan_data: Dict[str, Any]
    ) -> None:
        """
        Validate wave plan data structure.

        Args:
            wave_plan_data: Wave plan dictionary

        Raises:
            ValidationError: If structure invalid
        """
        if not isinstance(wave_plan_data, dict):
            raise ValidationError(
                "Wave plan data must be a dictionary", value=type(wave_plan_data)
            )

        if "waves" not in wave_plan_data:
            raise ValidationError("Wave plan must contain 'waves' key")

        if not isinstance(wave_plan_data["waves"], list):
            raise ValidationError(
                "Wave plan 'waves' must be a list", value=type(wave_plan_data["waves"])
            )

        # Validate each wave
        for i, wave in enumerate(wave_plan_data["waves"]):
            if "wave_number" not in wave:
                raise ValidationError(f"Wave {i} missing 'wave_number' field")
            if "wave_name" not in wave:
                raise ValidationError(f"Wave {i} missing 'wave_name' field")
            if "applications" not in wave:
                raise ValidationError(f"Wave {i} missing 'applications' field")

    def _calculate_total_duration(self, timeline_data: Dict[str, Any]) -> int:
        """Calculate total duration in days from timeline data."""
        # Placeholder calculation - would parse actual dates
        return 365

    async def _generate_recommendations(self, planning_flow: PlanningFlow) -> List[str]:
        """Generate optimization recommendations based on planning data."""
        recommendations = []

        # Skill gap recommendations
        skill_gaps = planning_flow.resource_allocation_data.get("skill_gaps", [])
        if skill_gaps:
            recommendations.append(
                f"Address {len(skill_gaps)} skill gaps through training or external hiring"
            )

        # Cost optimization
        total_cost = planning_flow.cost_estimation_data.get("total_estimated_cost", 0)
        if total_cost > 100000:
            recommendations.append(
                "Consider phased approach to spread costs over multiple budget cycles"
            )

        # Timeline optimization
        if planning_flow.wave_plan_data.get("total_waves", 0) > 5:
            recommendations.append(
                "Review wave sequencing for potential parallelization opportunities"
            )

        return recommendations
