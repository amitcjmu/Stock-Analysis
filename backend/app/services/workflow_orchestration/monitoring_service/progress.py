"""
Progress Tracking Module
Team C1 - Task C1.6

Handles workflow progress tracking, milestones, and completion estimation.
"""

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

from .models import ProgressMilestone, WorkflowProgress

logger = get_logger(__name__)


class ProgressTracker:
    """Tracks workflow progress and milestones"""

    def __init__(self):
        self.workflow_progress: Dict[str, WorkflowProgress] = {}
        self.milestone_definitions: Dict[str, ProgressMilestone] = {}

        # Initialize default milestones
        self._initialize_default_milestones()

    def _initialize_default_milestones(self):
        """Initialize default progress milestones"""
        default_milestones = [
            {
                "name": "Workflow Initialization",
                "description": "Workflow has been initialized and started",
                "phase": None,
                "weight": 0.05,
                "criteria": {"status": "initializing"},
            },
            {
                "name": "Platform Detection Started",
                "description": "Platform detection phase has begun",
                "phase": "platform_detection",
                "weight": 0.1,
                "criteria": {"phase_status": "running"},
            },
            {
                "name": "Platform Detection Completed",
                "description": "Platform detection phase completed successfully",
                "phase": "platform_detection",
                "weight": 0.2,
                "criteria": {"phase_status": "completed"},
            },
            {
                "name": "Automated Collection Started",
                "description": "Automated collection phase has begun",
                "phase": "automated_collection",
                "weight": 0.3,
                "criteria": {"phase_status": "running"},
            },
            {
                "name": "Automated Collection Completed",
                "description": "Automated collection phase completed",
                "phase": "automated_collection",
                "weight": 0.5,
                "criteria": {"phase_status": "completed"},
            },
            {
                "name": "Gap Analysis Completed",
                "description": "Gap analysis phase completed",
                "phase": "gap_analysis",
                "weight": 0.65,
                "criteria": {"phase_status": "completed"},
            },
            {
                "name": "Manual Collection Completed",
                "description": "Manual collection phase completed",
                "phase": "manual_collection",
                "weight": 0.8,
                "criteria": {"phase_status": "completed"},
            },
            {
                "name": "Data Synthesis Completed",
                "description": "Data synthesis phase completed",
                "phase": "synthesis",
                "weight": 0.95,
                "criteria": {"phase_status": "completed"},
            },
            {
                "name": "Workflow Completed",
                "description": "Workflow has been completed successfully",
                "phase": None,
                "weight": 1.0,
                "criteria": {"status": "completed"},
            },
        ]

        for milestone_data in default_milestones:
            milestone_id = f"default-{milestone_data['name'].lower().replace(' ', '-')}"
            milestone = ProgressMilestone(
                milestone_id=milestone_id,
                name=milestone_data["name"],
                description=milestone_data["description"],
                phase=milestone_data["phase"],
                completion_criteria=milestone_data["criteria"],
                weight=milestone_data["weight"],
                dependencies=[],
                estimated_duration_ms=None,
                metadata={"default": True},
            )
            self.milestone_definitions[milestone_id] = milestone

    async def initialize_workflow_progress(
        self, workflow_id: str, custom_milestones: List[Dict[str, Any]]
    ):
        """Initialize progress tracking for a workflow"""
        progress = WorkflowProgress(
            workflow_id=workflow_id,
            overall_progress=0.0,
            phase_progress={},
            completed_milestones=[],
            current_milestone=None,
            estimated_completion=None,
            time_remaining_ms=None,
            velocity_metrics={},
            bottlenecks=[],
            quality_gates_status={},
            last_updated=datetime.utcnow(),
        )
        self.workflow_progress[workflow_id] = progress

        # Add custom milestones if provided
        for custom_milestone in custom_milestones:
            await self._add_custom_milestone(workflow_id, custom_milestone)

    async def get_workflow_progress(
        self, workflow_id: str, include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive workflow progress information

        Args:
            workflow_id: ID of the workflow
            include_details: Whether to include detailed progress data

        Returns:
            Comprehensive progress information
        """
        try:
            # Get workflow progress
            progress = self.workflow_progress.get(workflow_id)
            if not progress:
                # Initialize if not exists
                await self.initialize_workflow_progress(workflow_id, [])
                progress = self.workflow_progress.get(workflow_id)

            if not progress:
                raise ValueError(
                    f"Unable to track progress for workflow: {workflow_id}"
                )

            # Get current workflow status from orchestrator
            workflow_status = await self._get_workflow_status_from_orchestrator(
                workflow_id
            )

            # Update progress based on current status
            updated_progress = await self._update_progress_from_status(
                progress, workflow_status
            )

            progress_data = {
                "workflow_id": workflow_id,
                "overall_progress": updated_progress.overall_progress,
                "phase_progress": updated_progress.phase_progress,
                "current_milestone": updated_progress.current_milestone,
                "estimated_completion": (
                    updated_progress.estimated_completion.isoformat()
                    if updated_progress.estimated_completion
                    else None
                ),
                "time_remaining_ms": updated_progress.time_remaining_ms,
                "last_updated": updated_progress.last_updated.isoformat(),
                "status_summary": {
                    "completed_milestones": len(updated_progress.completed_milestones),
                    "total_milestones": len(self.milestone_definitions),
                    "current_phase": self._get_current_phase_from_status(
                        workflow_status
                    ),
                    "overall_status": workflow_status.get("status", "unknown"),
                },
            }

            # Add detailed information if requested
            if include_details:
                progress_data.update(
                    {
                        "completed_milestones": updated_progress.completed_milestones,
                        "velocity_metrics": updated_progress.velocity_metrics,
                        "bottlenecks": updated_progress.bottlenecks,
                        "quality_gates_status": updated_progress.quality_gates_status,
                        "milestone_details": [
                            asdict(milestone)
                            for milestone in self.milestone_definitions.values()
                        ],
                    }
                )

            return progress_data

        except Exception as e:
            logger.error(f"❌ Failed to get workflow progress: {e}")
            raise

    async def update_progress_tracking(self):
        """Update progress tracking for all workflows"""
        for workflow_id, progress in self.workflow_progress.items():
            try:
                # Get current workflow status
                workflow_status = await self._get_workflow_status_from_orchestrator(
                    workflow_id
                )

                # Update progress
                await self._update_progress_from_status(progress, workflow_status)

            except Exception as e:
                logger.warning(
                    f"Failed to update progress for workflow {workflow_id}: {e}"
                )

    async def _add_custom_milestone(
        self, workflow_id: str, milestone_data: Dict[str, Any]
    ):
        """Add a custom milestone for a workflow"""
        milestone_id = f"custom-{workflow_id}-{milestone_data.get('name', 'unnamed').lower().replace(' ', '-')}"

        milestone = ProgressMilestone(
            milestone_id=milestone_id,
            name=milestone_data.get("name", "Custom Milestone"),
            description=milestone_data.get("description", ""),
            phase=milestone_data.get("phase"),
            completion_criteria=milestone_data.get("criteria", {}),
            weight=milestone_data.get("weight", 0.1),
            dependencies=milestone_data.get("dependencies", []),
            estimated_duration_ms=milestone_data.get("estimated_duration_ms"),
            metadata={
                "custom": True,
                "workflow_id": workflow_id,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        self.milestone_definitions[milestone_id] = milestone

    async def _get_workflow_status_from_orchestrator(
        self, workflow_id: str
    ) -> Dict[str, Any]:
        """Get workflow status from the orchestrator"""
        # This would integrate with the actual orchestrator
        # For now, return a mock status
        return {
            "status": "running",
            "phase_results": {
                "platform_detection": {"status": "completed"},
                "automated_collection": {"status": "running"},
                "gap_analysis": {"status": "pending"},
                "manual_collection": {"status": "pending"},
                "synthesis": {"status": "pending"},
            },
        }

    async def _update_progress_from_status(
        self, progress: WorkflowProgress, status: Dict[str, Any]
    ) -> WorkflowProgress:
        """Update progress based on workflow status"""
        # Simple progress calculation
        workflow_status = status.get("status", "unknown")
        phase_results = status.get("phase_results", {})

        if workflow_status == "completed":
            progress.overall_progress = 1.0
            progress.current_milestone = "default-workflow-completed"
        elif workflow_status == "running":
            # Calculate based on completed phases
            completed_phases = len(
                [p for p in phase_results.values() if p.get("status") == "completed"]
            )
            total_phases = 5  # Standard number of phases
            progress.overall_progress = min(0.95, completed_phases / total_phases)

            # Update current milestone based on active phase
            current_phase = self._get_current_phase_from_status(status)
            if current_phase:
                progress.current_milestone = (
                    f"default-{current_phase.replace('_', '-')}-started"
                )

        # Update phase progress
        for phase, result in phase_results.items():
            phase_status = result.get("status", "pending")
            if phase_status == "completed":
                progress.phase_progress[phase] = 1.0
            elif phase_status == "running":
                progress.phase_progress[phase] = 0.5  # Assume 50% when running
            else:
                progress.phase_progress[phase] = 0.0

        # Update completed milestones based on progress
        self._update_completed_milestones(progress)

        # Update velocity metrics
        progress.velocity_metrics = await self._calculate_velocity_metrics(progress)

        # Update bottlenecks
        progress.bottlenecks = await self._identify_bottlenecks(progress, status)

        progress.last_updated = datetime.utcnow()
        return progress

    def _get_current_phase_from_status(self, status: Dict[str, Any]) -> Optional[str]:
        """Extract current phase from workflow status"""
        phase_results = status.get("phase_results", {})
        for phase, result in phase_results.items():
            if result.get("status") == "running":
                return phase
        return None

    def _update_completed_milestones(self, progress: WorkflowProgress):
        """Update completed milestones based on current progress"""
        completed_milestones = []

        for milestone in self.milestone_definitions.values():
            if milestone.weight <= progress.overall_progress:
                completed_milestones.append(milestone.milestone_id)

        progress.completed_milestones = completed_milestones

    async def _calculate_velocity_metrics(
        self, progress: WorkflowProgress
    ) -> Dict[str, float]:
        """Calculate velocity metrics for progress tracking"""
        # Simplified velocity calculation
        return {
            "average_velocity": 0.1,  # Progress per hour
            "current_velocity": 0.15,
            "velocity_trend": 1.05,  # 5% improvement
        }

    async def _identify_bottlenecks(
        self, progress: WorkflowProgress, status: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify potential bottlenecks in workflow progress"""
        bottlenecks = []

        # Check for phases that are taking too long
        phase_results = status.get("phase_results", {})
        for phase, result in phase_results.items():
            if result.get("status") == "running":
                # If a phase has been running for too long, flag as bottleneck
                bottlenecks.append(
                    {
                        "type": "phase_duration",
                        "phase": phase,
                        "description": f"Phase {phase} has been running for extended time",
                        "severity": "medium",
                        "recommendations": [f"Review {phase} phase performance"],
                    }
                )

        # Check overall progress velocity
        if progress.overall_progress < 0.1:
            bottlenecks.append(
                {
                    "type": "slow_start",
                    "description": "Workflow progress is slower than expected",
                    "severity": "low",
                    "recommendations": [
                        "Check workflow initialization",
                        "Review resource allocation",
                    ],
                }
            )

        return bottlenecks
