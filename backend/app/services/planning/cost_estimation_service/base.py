"""
Base class and initialization for Cost Estimation Service.

This module contains the core CostEstimationService class with initialization
and context building logic.

Per ADR-024: CrewAI memory DISABLED, use TenantMemoryManager
Per ADR-015: Use TenantScopedAgentPool for persistent agents
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


class CostEstimationService:
    """Service for generating migration cost estimates using CrewAI agents."""

    # Rate cards (USD per hour) - configurable per engagement
    DEFAULT_RATE_CARDS = {
        "architect": 250.00,
        "senior_developer": 175.00,
        "developer": 125.00,
        "tester": 100.00,
        "dba": 150.00,
        "devops": 160.00,
        "project_manager": 200.00,
        "scrum_master": 150.00,
    }

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize cost estimation service with database session and context.

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

    def _build_cost_context(
        self,
        wave_plan_data: Dict[str, Any],
        resource_allocation_data: Dict[str, Any],
        timeline_data: Dict[str, Any],
        rate_cards: Dict[str, float],
        phase_input: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build context data for cost estimation agent.

        Args:
            wave_plan_data: Wave plan with waves and groups
            resource_allocation_data: Resource allocations per wave
            timeline_data: Timeline with phases and durations
            rate_cards: Hourly rates by role
            phase_input: Optional additional input

        Returns:
            Dict with context for agent
        """
        waves = wave_plan_data.get("waves", [])
        allocations = resource_allocation_data.get("allocations", [])
        total_duration_days = timeline_data.get("total_duration_days", 0)

        # Calculate wave-level resource summary
        wave_resource_summary = []
        for wave in waves:
            wave_allocations = [
                alloc
                for alloc in allocations
                if alloc.get("wave_id") == wave.get("wave_id")
            ]
            wave_resource_summary.append(
                {
                    "wave_number": wave.get("wave_number"),
                    "application_count": wave.get("application_count"),
                    "allocated_resources": len(wave_allocations),
                    "complexity": self._estimate_wave_complexity(wave),
                }
            )

        return {
            "wave_summary": {
                "total_waves": len(waves),
                "total_apps": wave_plan_data.get("summary", {}).get("total_apps", 0),
                "wave_details": wave_resource_summary,
            },
            "resource_allocations": {
                "total_allocations": len(allocations),
                "allocations_by_role": self._group_allocations_by_role(allocations),
                "allocations_by_wave": self._group_allocations_by_wave(allocations),
            },
            "timeline_info": {
                "total_duration_days": total_duration_days,
                "total_duration_months": round(total_duration_days / 30, 1),
                "phases": timeline_data.get("phases", []),
            },
            "rate_cards": rate_cards,
            "cost_calculation_objectives": [
                "Calculate labor costs per wave (role × hours × rate)",
                "Estimate infrastructure costs (cloud resources, tooling, licenses)",
                "Add risk contingency (15-25% based on complexity and criticality)",
                "Provide confidence intervals (low/medium/high scenarios)",
                "Break down costs by category and wave",
            ],
            "additional_parameters": (
                phase_input.get("parameters", {}) if phase_input else {}
            ),
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

    def _group_allocations_by_role(self, allocations: list) -> Dict[str, Any]:
        """Group resource allocations by role."""
        by_role = {}
        for allocation in allocations:
            role = allocation.get("role", "unspecified")
            if role not in by_role:
                by_role[role] = {"count": 0, "total_hours": 0}
            by_role[role]["count"] += 1
            by_role[role]["total_hours"] += allocation.get("allocated_hours", 0)
        return by_role

    def _group_allocations_by_wave(self, allocations: list) -> Dict[str, Any]:
        """Group resource allocations by wave."""
        by_wave = {}
        for allocation in allocations:
            wave_id = allocation.get("wave_id", "unspecified")
            if wave_id not in by_wave:
                by_wave[wave_id] = {"count": 0, "total_hours": 0}
            by_wave[wave_id]["count"] += 1
            by_wave[wave_id]["total_hours"] += allocation.get("allocated_hours", 0)
        return by_wave
