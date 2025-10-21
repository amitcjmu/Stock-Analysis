"""
Phase Results Persistence for Assessment Flows

Handles saving assessment phase execution results to database.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.assessment_flow import AssessmentFlow

logger = get_logger(__name__)


class PhaseResultsPersistence:
    """
    Persist assessment phase results to database.

    Saves phase execution results to phase_results JSONB field with proper
    tenant scoping and atomic transactions.

    Per ADR-024: CrewAI memory disabled, use TenantMemoryManager.
    """

    def __init__(self, db: AsyncSession, client_account_id: UUID, engagement_id: UUID):
        """
        Initialize phase results persistence.

        Args:
            db: Database session
            client_account_id: Client account ID for tenant scoping
            engagement_id: Engagement ID for tenant scoping
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def save_phase_results(
        self,
        flow_id: str,
        phase_name: str,
        results: Dict[str, Any],
    ) -> None:
        """
        Save phase execution results to phase_results JSONB field.

        Args:
            flow_id: Assessment flow ID (UUID as string)
            phase_name: Name of the phase that executed
            results: Phase execution results dictionary

        Raises:
            ValueError: If flow not found
            RuntimeError: If save operation fails
        """
        try:
            # Get current phase_results with tenant scoping
            stmt = select(AssessmentFlow.phase_results).where(
                AssessmentFlow.id == UUID(flow_id),
                AssessmentFlow.client_account_id == self.client_account_id,
                AssessmentFlow.engagement_id == self.engagement_id,
            )
            result = await self.db.execute(stmt)
            current_phase_results = result.scalar_one_or_none()

            if current_phase_results is None:
                # Flow not found or has null phase_results - create initial state
                current_phase_results = {}
                logger.warning(
                    f"Flow {flow_id} not found or has null phase_results - "
                    f"creating initial state"
                )

            # Update with new phase results
            current_phase_results[phase_name] = {
                **results,
                "persisted_at": datetime.utcnow().isoformat(),
            }

            # Save back to database with tenant scoping
            update_stmt = (
                update(AssessmentFlow)
                .where(
                    AssessmentFlow.id == UUID(flow_id),
                    AssessmentFlow.client_account_id == self.client_account_id,
                    AssessmentFlow.engagement_id == self.engagement_id,
                )
                .values(phase_results=current_phase_results)
            )

            await self.db.execute(update_stmt)
            await self.db.commit()

            logger.info(f"💾 Saved results for phase '{phase_name}' to flow {flow_id}")

        except Exception as e:
            logger.error(f"Failed to save phase results: {e}")
            await self.db.rollback()
            raise RuntimeError(f"Failed to save phase results: {e}") from e

    async def get_phase_results(self, flow_id: str, phase_name: str) -> Dict[str, Any]:
        """
        Retrieve phase results from phase_results field.

        Args:
            flow_id: Assessment flow ID (UUID as string)
            phase_name: Name of the phase to retrieve

        Returns:
            Phase results dictionary or empty dict if not found
        """
        try:
            stmt = select(AssessmentFlow.phase_results).where(
                AssessmentFlow.id == UUID(flow_id),
                AssessmentFlow.client_account_id == self.client_account_id,
                AssessmentFlow.engagement_id == self.engagement_id,
            )
            result = await self.db.execute(stmt)
            phase_results = result.scalar_one_or_none()

            if not phase_results:
                return {}

            return phase_results.get(phase_name, {})

        except Exception as e:
            logger.error(f"Failed to get phase results: {e}")
            return {}

    async def get_all_phase_results(self, flow_id: str) -> Dict[str, Any]:
        """
        Retrieve all phase results from phase_results field.

        Args:
            flow_id: Assessment flow ID (UUID as string)

        Returns:
            Dictionary of all phase results
        """
        try:
            stmt = select(AssessmentFlow.phase_results).where(
                AssessmentFlow.id == UUID(flow_id),
                AssessmentFlow.client_account_id == self.client_account_id,
                AssessmentFlow.engagement_id == self.engagement_id,
            )
            result = await self.db.execute(stmt)
            phase_results = result.scalar_one_or_none()

            if not phase_results:
                return {}

            return phase_results

        except Exception as e:
            logger.error(f"Failed to get all phase results: {e}")
            return {}
