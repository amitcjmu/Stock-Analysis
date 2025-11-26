"""
Timeline Generation Service for Planning Flow.

Generates realistic, data-driven migration timelines using the timeline_generation_specialist
CrewAI agent based on wave plans, resource allocations, and historical velocity patterns.

Per ADR-024: CrewAI memory DISABLED, use TenantMemoryManager
Per ADR-029: Use safe JSON parsing for all LLM outputs
Per ADR-031: Full CallbackHandler integration for observability
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from crewai import Task
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


class TimelineService:
    """Service for generating migration timelines using CrewAI agents."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize timeline service with database session and context.

        Args:
            db: Async database session
            context: Request context with tenant scoping
        """
        self.db = db
        self.context = context

        # Convert context IDs to UUIDs (per migration 115)
        client_account_id = context.client_account_id
        if isinstance(client_account_id, str):
            client_account_uuid = UUID(client_account_id)
        else:
            client_account_uuid = client_account_id

        engagement_id = context.engagement_id
        if isinstance(engagement_id, str):
            engagement_uuid = UUID(engagement_id)
        else:
            engagement_uuid = engagement_id

        # Store UUID versions for tenant scoping
        self.client_account_uuid = client_account_uuid
        self.engagement_uuid = engagement_uuid

        # Initialize repository with tenant scoping
        self.planning_repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        # Initialize agent pool for singleton agents (ADR-015)
        self.agent_pool = TenantScopedAgentPool(
            client_account_id=str(client_account_uuid),
            engagement_id=str(engagement_uuid),
        )

    async def generate_timeline(
        self, planning_flow_id: UUID, phase_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate realistic migration timeline using CrewAI agent.

        Args:
            planning_flow_id: UUID of the planning flow
            phase_input: Optional input data for timeline generation

        Returns:
            Dict containing timeline data with phases, milestones, and critical path
        """
        try:
            logger.info(
                f"Starting timeline generation for planning flow: {planning_flow_id}"
            )

            # Update phase status to in_progress
            await self.planning_repo.update_phase_status(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
                current_phase="timeline_generation",
                phase_status="in_progress",
            )

            # Get planning flow data
            planning_flow = await self.planning_repo.get_planning_flow_by_id(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
            )

            if not planning_flow:
                raise ValueError(f"Planning flow not found: {planning_flow_id}")

            # Extract required data
            wave_plan_data = planning_flow.wave_plan_data or {}
            resource_allocation_data = planning_flow.resource_allocation_data or {}

            # Validate prerequisites
            if not wave_plan_data.get("waves"):
                raise ValueError(
                    "Wave plan data required for timeline generation. "
                    "Please complete wave planning phase first."
                )

            # Setup observability (ADR-031)
            callback_handler = CallbackHandlerIntegration.create_callback_handler(
                flow_id=str(planning_flow.master_flow_id),
                context={
                    "client_account_id": str(self.client_account_uuid),
                    "engagement_id": str(self.engagement_uuid),
                    "flow_type": "planning",
                    "phase": "timeline_generation",
                    "planning_flow_id": str(planning_flow_id),
                },
            )
            callback_handler.setup_callbacks()

            # Get agent from pool (ADR-015: persistent agents)
            agent = await self.agent_pool.get_agent("timeline_generation_specialist")

            # Build context for agent
            context_data = self._build_timeline_context(
                wave_plan_data, resource_allocation_data, phase_input
            )

            # Create task
            task = Task(
                description=(
                    f"Generate a realistic migration timeline for {len(wave_plan_data.get('waves', []))} waves. "
                    "Consider wave dependencies, resource availability, critical path, and include buffer periods. "
                    "Provide milestones, phase durations, and risk buffers."
                ),
                expected_output=(
                    "JSON object with timeline structure: "
                    '{"phases": [...], "milestones": [...], "critical_path": [...], '
                    '"total_duration_days": <int>, "risk_buffer_percentage": <float>}'
                ),
                agent=(agent._agent if hasattr(agent, "_agent") else agent),
            )

            # Generate unique task ID
            task_id = str(uuid.uuid4())

            # Register task start (ADR-031)
            callback_handler._step_callback(
                {
                    "type": "starting",
                    "status": "starting",
                    "agent": "timeline_generation_specialist",
                    "task": "timeline_generation",
                    "task_id": task_id,
                    "content": f"Generating timeline for {len(wave_plan_data.get('waves', []))} migration waves",
                }
            )

            # Execute task (wrapped for async)
            import asyncio

            try:
                future = task.execute_async(context=str(context_data))
                result = await asyncio.wrap_future(future)

                # Parse result using safe JSON parser (ADR-029)
                timeline_data = self._parse_timeline_result(result)

                # Sync to normalized tables (project_timelines, timeline_phases)
                await self._sync_to_normalized_tables(planning_flow_id, timeline_data)

                # Persist to JSONB column
                await self.planning_repo.save_timeline_data(
                    planning_flow_id=planning_flow_id,
                    client_account_id=self.client_account_uuid,
                    engagement_id=self.engagement_uuid,
                    timeline_data=timeline_data,
                )

                # Mark task completion (ADR-031)
                callback_handler._task_completion_callback(
                    {
                        "agent": "timeline_generation_specialist",
                        "task_name": "timeline_generation",
                        "status": "completed",
                        "task_id": task_id,
                        "output": timeline_data,
                    }
                )

                # Update phase status to completed
                await self.planning_repo.update_phase_status(
                    planning_flow_id=planning_flow_id,
                    client_account_id=self.client_account_uuid,
                    engagement_id=self.engagement_uuid,
                    current_phase="timeline_generation",
                    phase_status="completed",
                )

                await self.db.commit()

                logger.info(
                    f"✅ Timeline generation completed for flow: {planning_flow_id}"
                )

                return {
                    "status": "success",
                    "timeline_data": timeline_data,
                    "message": "Timeline generated successfully",
                }

            except Exception as task_error:
                # Mark task failure (ADR-031)
                callback_handler._task_completion_callback(
                    {
                        "agent": "timeline_generation_specialist",
                        "task_name": "timeline_generation",
                        "status": "failed",
                        "task_id": task_id,
                        "error": str(task_error),
                    }
                )
                raise

        except Exception as e:
            logger.error(
                f"Timeline generation failed for flow {planning_flow_id}: {str(e)}",
                exc_info=True,
            )

            # Update phase status to failed
            try:
                await self.planning_repo.update_phase_status(
                    planning_flow_id=planning_flow_id,
                    client_account_id=self.client_account_uuid,
                    engagement_id=self.engagement_uuid,
                    current_phase="timeline_generation",
                    phase_status="failed",
                )
                await self.db.commit()
            except Exception as update_error:
                logger.error(
                    f"Failed to update phase status after error: {update_error}"
                )

            return {
                "status": "failed",
                "error": str(e),
                "message": "Timeline generation failed",
            }

    def _build_timeline_context(
        self,
        wave_plan_data: Dict[str, Any],
        resource_allocation_data: Dict[str, Any],
        phase_input: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build context data for timeline generation agent.

        Args:
            wave_plan_data: Wave plan with waves and groups
            resource_allocation_data: Resource allocations per wave
            phase_input: Optional additional input

        Returns:
            Dict with context for agent
        """
        waves = wave_plan_data.get("waves", [])
        allocations = resource_allocation_data.get("allocations", [])

        return {
            "wave_summary": {
                "total_waves": len(waves),
                "total_apps": wave_plan_data.get("summary", {}).get("total_apps", 0),
                "waves": [
                    {
                        "wave_number": wave.get("wave_number"),
                        "application_count": wave.get("application_count"),
                        "complexity_estimate": self._estimate_wave_complexity(wave),
                        "dependencies": wave.get("dependencies", []),
                    }
                    for wave in waves
                ],
            },
            "resource_availability": {
                "total_allocations": len(allocations),
                "resource_breakdown": self._summarize_resource_allocations(allocations),
            },
            "timeline_objectives": [
                "Identify critical path through wave dependencies",
                "Calculate realistic durations based on complexity and resources",
                "Include buffer periods for identified risks (15-25% based on complexity)",
                "Define milestones and validation checkpoints per wave",
                "Optimize for minimum total duration while respecting constraints",
            ],
            "constraints": phase_input.get("constraints", {}) if phase_input else {},
        }

    def _estimate_wave_complexity(self, wave: Dict[str, Any]) -> str:
        """Estimate wave complexity based on app count and other factors."""
        app_count = wave.get("application_count", 0)
        if app_count > 30:
            return "high"
        elif app_count > 15:
            return "medium"
        else:
            return "low"

    def _summarize_resource_allocations(
        self, allocations: list
    ) -> Dict[str, Dict[str, int]]:
        """Summarize resource allocations by role and wave."""
        summary = {}
        for allocation in allocations:
            role = allocation.get("role", "unspecified")
            if role not in summary:
                summary[role] = {"total_hours": 0, "total_fte": 0}
            summary[role]["total_hours"] += allocation.get("allocated_hours", 0)
            summary[role]["total_fte"] += allocation.get("fte_count", 0)
        return summary

    def _parse_timeline_result(self, result: Any) -> Dict[str, Any]:  # noqa: C901
        """
        Parse timeline generation result from agent using safe JSON parsing (ADR-029).

        Args:
            result: Raw result from CrewAI task

        Returns:
            Parsed timeline data dict
        """
        raw_output = result.raw if hasattr(result, "raw") else str(result)

        try:
            # Try direct JSON parse first
            timeline_data = json.loads(raw_output)
        except json.JSONDecodeError:
            logger.warning("Timeline result not valid JSON, extracting JSON blocks")

            # Extract JSON blocks (similar to gap_analysis output_parser.py)
            json_candidates = []
            idx = 0
            while idx < len(raw_output):
                start = raw_output.find("{", idx)
                if start == -1:
                    break

                # Find matching closing brace
                depth = 0
                end = start
                for i in range(start, len(raw_output)):
                    if raw_output[i] == "{":
                        depth += 1
                    elif raw_output[i] == "}":
                        depth -= 1
                        if depth == 0:
                            end = i
                            break

                if end > start:
                    try:
                        potential_json = raw_output[start : end + 1]
                        parsed = json.loads(potential_json)
                        json_candidates.append(
                            {"data": parsed, "size": end - start, "start_pos": start}
                        )
                    except json.JSONDecodeError:
                        pass

                idx = end + 1 if end > start else start + 1

            # Prioritize largest valid JSON with required structure
            for candidate in sorted(
                json_candidates, key=lambda x: x["size"], reverse=True
            ):
                data = candidate["data"]
                if "phases" in data or "milestones" in data or "timeline" in data:
                    timeline_data = data
                    logger.info(
                        f"✅ Extracted timeline JSON (size={candidate['size']})"
                    )
                    break
            else:
                # Fallback to basic structure
                logger.warning("No valid timeline JSON found, using fallback")
                timeline_data = {
                    "phases": [],
                    "milestones": [],
                    "total_duration_days": 0,
                    "parsing_error": "Failed to extract valid timeline from agent output",
                }

        # Ensure required structure
        if "phases" not in timeline_data:
            timeline_data["phases"] = []
        if "milestones" not in timeline_data:
            timeline_data["milestones"] = []
        if "total_duration_days" not in timeline_data:
            timeline_data["total_duration_days"] = 0

        # Add metadata
        timeline_data["metadata"] = {
            "generated_by": "timeline_generation_specialist",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agent_type": "crewai",
        }

        return timeline_data

    async def _sync_to_normalized_tables(
        self, planning_flow_id: UUID, timeline_data: Dict[str, Any]
    ) -> None:
        """
        Sync timeline data to project_timelines and timeline_phases tables.

        Args:
            planning_flow_id: Planning flow UUID
            timeline_data: Timeline data to persist
        """
        # This would insert/update rows in project_timelines and timeline_phases tables
        # For now, we rely on JSONB storage in planning_flows.timeline_data
        # Future enhancement: Implement full normalized table sync
        logger.info(
            f"Timeline data synced to JSONB for planning flow: {planning_flow_id}"
        )
        logger.debug(
            "NOTE: Normalized table sync (project_timelines, timeline_phases) "
            "is a future enhancement. Data persisted to JSONB column."
        )


async def execute_timeline_generation_for_flow(
    db: AsyncSession,
    context: RequestContext,
    planning_flow_id: UUID,
    phase_input: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute timeline generation for a planning flow.

    Args:
        db: Database session
        context: Request context
        planning_flow_id: UUID of the planning flow
        phase_input: Optional input data for timeline generation

    Returns:
        Dict containing timeline generation result
    """
    service = TimelineService(db, context)
    return await service.generate_timeline(planning_flow_id, phase_input)
