"""
Repository for governance and approval workflows.

This module provides data access methods for approval requests
and migration exceptions in the governance process.
"""

import logging
from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.governance import ApprovalRequests, MigrationExceptions
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class ApprovalRequestRepository(ContextAwareRepository[ApprovalRequests]):
    """Repository for approval requests."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        super().__init__(db, ApprovalRequests, client_account_id, engagement_id)

    async def get_pending_requests(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> List[ApprovalRequests]:
        """
        Get pending approval requests.

        Args:
            entity_type: Optional entity type filter
            entity_id: Optional entity ID filter

        Returns:
            List of pending approval requests
        """
        filters = {"status": "PENDING"}

        if entity_type:
            filters["entity_type"] = entity_type
        if entity_id:
            filters["entity_id"] = entity_id

        return await self.get_by_filters(**filters)

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
    ) -> List[ApprovalRequests]:
        """
        Get approval requests for a specific entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of approval requests for the entity
        """
        return await self.get_by_filters(entity_type=entity_type, entity_id=entity_id)

    async def get_by_approver(
        self,
        approver_id: str,
        status: Optional[str] = None,
    ) -> List[ApprovalRequests]:
        """
        Get approval requests by approver.

        Args:
            approver_id: Approver user ID
            status: Optional status filter

        Returns:
            List of approval requests for the approver
        """
        filters = {"approver_id": approver_id}
        if status:
            filters["status"] = status

        return await self.get_by_filters(**filters)

    async def create_request(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
        notes: Optional[str] = None,
        commit: bool = True,
    ) -> ApprovalRequests:
        """
        Create a new approval request.

        Args:
            entity_type: Type of entity requiring approval
            entity_id: ID of entity requiring approval
            notes: Optional notes for the request
            commit: Whether to commit the transaction

        Returns:
            Created approval request
        """
        from datetime import datetime

        return await self.create(
            commit=commit,
            entity_type=entity_type,
            entity_id=entity_id,
            status="PENDING",
            notes=notes,
            requested_at=datetime.utcnow(),
        )

    async def approve_request(
        self,
        request_id: str,
        approver_id: str,
        notes: Optional[str] = None,
        commit: bool = True,
    ) -> Optional[ApprovalRequests]:
        """
        Approve a request.

        Args:
            request_id: Request ID
            approver_id: Approver user ID
            notes: Optional approval notes
            commit: Whether to commit the transaction

        Returns:
            Updated approval request if found
        """
        from datetime import datetime

        return await self.update(
            request_id,
            commit=commit,
            status="APPROVED",
            approver_id=approver_id,
            notes=notes,
            decided_at=datetime.utcnow(),
        )

    async def reject_request(
        self,
        request_id: str,
        approver_id: str,
        notes: Optional[str] = None,
        commit: bool = True,
    ) -> Optional[ApprovalRequests]:
        """
        Reject a request.

        Args:
            request_id: Request ID
            approver_id: Approver user ID
            notes: Optional rejection notes
            commit: Whether to commit the transaction

        Returns:
            Updated approval request if found
        """
        from datetime import datetime

        return await self.update(
            request_id,
            commit=commit,
            status="REJECTED",
            approver_id=approver_id,
            notes=notes,
            decided_at=datetime.utcnow(),
        )

    async def get_with_exceptions(self, request_id: str) -> Optional[ApprovalRequests]:
        """
        Get approval request with related exceptions loaded.

        Args:
            request_id: Request ID

        Returns:
            Approval request with exceptions loaded
        """
        query = (
            select(ApprovalRequests)
            .options(selectinload(ApprovalRequests.migration_exceptions))
            .where(ApprovalRequests.id == request_id)
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class MigrationExceptionRepository(ContextAwareRepository[MigrationExceptions]):
    """Repository for migration exceptions."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        super().__init__(db, MigrationExceptions, client_account_id, engagement_id)

    async def get_by_scope(
        self,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[MigrationExceptions]:
        """
        Get exceptions by scope.

        Args:
            application_id: Optional application ID filter
            asset_id: Optional asset ID filter
            status: Optional status filter

        Returns:
            List of migration exceptions for the specified scope
        """
        filters = {}

        if application_id:
            filters["application_id"] = application_id
        if asset_id:
            filters["asset_id"] = asset_id
        if status:
            filters["status"] = status

        return await self.get_by_filters(**filters)

    async def get_open_exceptions(
        self,
        exception_type: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> List[MigrationExceptions]:
        """
        Get open migration exceptions.

        Args:
            exception_type: Optional exception type filter
            risk_level: Optional risk level filter

        Returns:
            List of open migration exceptions
        """
        filters = {"status": "OPEN"}

        if exception_type:
            filters["exception_type"] = exception_type
        if risk_level:
            filters["risk_level"] = risk_level

        return await self.get_by_filters(**filters)

    async def get_high_risk_exceptions(self) -> List[MigrationExceptions]:
        """
        Get high and critical risk exceptions.

        Returns:
            List of high/critical risk exceptions
        """
        query = select(MigrationExceptions).where(
            MigrationExceptions.risk_level.in_(["high", "critical"])
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_exception(
        self,
        exception_type: str,
        rationale: str,
        risk_level: str,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        approval_request_id: Optional[str] = None,
        commit: bool = True,
    ) -> MigrationExceptions:
        """
        Create a new migration exception.

        Args:
            exception_type: Type of exception
            rationale: Business/technical justification
            risk_level: Risk level assessment
            application_id: Optional application ID
            asset_id: Optional asset ID
            approval_request_id: Optional linked approval request
            commit: Whether to commit the transaction

        Returns:
            Created migration exception
        """
        return await self.create(
            commit=commit,
            exception_type=exception_type,
            rationale=rationale,
            risk_level=risk_level,
            application_id=application_id,
            asset_id=asset_id,
            approval_request_id=approval_request_id,
            status="OPEN",
        )

    async def close_exception(
        self,
        exception_id: str,
        commit: bool = True,
    ) -> Optional[MigrationExceptions]:
        """
        Close a migration exception.

        Args:
            exception_id: Exception ID
            commit: Whether to commit the transaction

        Returns:
            Updated migration exception if found
        """
        return await self.update(exception_id, commit=commit, status="CLOSED")

    async def reopen_exception(
        self,
        exception_id: str,
        commit: bool = True,
    ) -> Optional[MigrationExceptions]:
        """
        Reopen a migration exception.

        Args:
            exception_id: Exception ID
            commit: Whether to commit the transaction

        Returns:
            Updated migration exception if found
        """
        return await self.update(exception_id, commit=commit, status="OPEN")

    async def get_with_approval(
        self, exception_id: str
    ) -> Optional[MigrationExceptions]:
        """
        Get exception with approval request loaded.

        Args:
            exception_id: Exception ID

        Returns:
            Migration exception with approval request loaded
        """
        query = (
            select(MigrationExceptions)
            .options(joinedload(MigrationExceptions.approval_request))
            .where(MigrationExceptions.id == exception_id)
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_exceptions_requiring_approval(self) -> List[MigrationExceptions]:
        """
        Get exceptions that require approval but don't have approval requests.

        Returns:
            List of exceptions requiring approval
        """
        query = select(MigrationExceptions).where(
            and_(
                MigrationExceptions.status == "OPEN",
                MigrationExceptions.approval_request_id.is_(None),
                or_(
                    MigrationExceptions.exception_type.in_(
                        ["custom_approach", "skip_migration"]
                    ),
                    MigrationExceptions.risk_level.in_(["high", "critical"]),
                ),
            )
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        return result.scalars().all()
