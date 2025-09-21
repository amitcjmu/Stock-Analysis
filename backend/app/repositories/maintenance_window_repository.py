"""
Repository for maintenance windows and blackout periods management.

This module provides data access methods for scheduled maintenance windows
and blackout periods at various scopes.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance_windows import BlackoutPeriods, MaintenanceWindows
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class MaintenanceWindowRepository(ContextAwareRepository[MaintenanceWindows]):
    """Repository for maintenance windows."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        super().__init__(db, MaintenanceWindows, client_account_id, engagement_id)

    async def get_by_scope(
        self,
        scope_type: str,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> List[MaintenanceWindows]:
        """
        Get maintenance windows by scope.

        Args:
            scope_type: Scope type (tenant, application, asset)
            application_id: Application ID for application scope
            asset_id: Asset ID for asset scope

        Returns:
            List of maintenance windows for the specified scope
        """
        filters = {"scope_type": scope_type}

        if scope_type == "application" and application_id:
            filters["application_id"] = application_id
        elif scope_type == "asset" and asset_id:
            filters["asset_id"] = asset_id

        return await self.get_by_filters(**filters)

    async def get_active_windows(
        self,
        check_time: Optional[datetime] = None,
        scope_type: Optional[str] = None,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> List[MaintenanceWindows]:
        """
        Get currently active maintenance windows.

        Args:
            check_time: Time to check against (defaults to now)
            scope_type: Optional scope type filter
            application_id: Optional application ID filter
            asset_id: Optional asset ID filter

        Returns:
            List of currently active maintenance windows
        """
        if not check_time:
            check_time = datetime.utcnow()

        # Build base query for active windows
        query = select(MaintenanceWindows).where(
            and_(
                MaintenanceWindows.start_time <= check_time,
                MaintenanceWindows.end_time >= check_time,
            )
        )

        # Apply context filters
        query = self._apply_context_filter(query)

        # Apply scope filters
        scope_filters = []
        if scope_type:
            scope_filters.append(MaintenanceWindows.scope_type == scope_type)
        if application_id:
            scope_filters.append(MaintenanceWindows.application_id == application_id)
        if asset_id:
            scope_filters.append(MaintenanceWindows.asset_id == asset_id)

        if scope_filters:
            query = query.where(and_(*scope_filters))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_upcoming_windows(
        self,
        days_ahead: int = 30,
        scope_type: Optional[str] = None,
    ) -> List[MaintenanceWindows]:
        """
        Get upcoming maintenance windows within specified days.

        Args:
            days_ahead: Number of days to look ahead
            scope_type: Optional scope type filter

        Returns:
            List of upcoming maintenance windows
        """
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=days_ahead)

        query = select(MaintenanceWindows).where(
            and_(
                MaintenanceWindows.start_time >= start_time,
                MaintenanceWindows.start_time <= end_time,
            )
        )

        # Apply context filters
        query = self._apply_context_filter(query)

        if scope_type:
            query = query.where(MaintenanceWindows.scope_type == scope_type)

        query = query.order_by(MaintenanceWindows.start_time)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def check_conflicts(
        self,
        start_time: datetime,
        end_time: datetime,
        scope_type: str,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        exclude_id: Optional[str] = None,
    ) -> List[MaintenanceWindows]:
        """
        Check for conflicting maintenance windows.

        Args:
            start_time: Proposed start time
            end_time: Proposed end time
            scope_type: Scope type
            application_id: Optional application ID
            asset_id: Optional asset ID
            exclude_id: Optional window ID to exclude from conflict check

        Returns:
            List of conflicting maintenance windows
        """
        # Find overlapping windows
        query = select(MaintenanceWindows).where(
            and_(
                MaintenanceWindows.scope_type == scope_type,
                ~and_(
                    or_(
                        MaintenanceWindows.end_time <= start_time,
                        MaintenanceWindows.start_time >= end_time,
                    )
                ),
            )
        )

        # Apply context filters
        query = self._apply_context_filter(query)

        # Apply scope-specific filters
        if application_id:
            query = query.where(MaintenanceWindows.application_id == application_id)
        if asset_id:
            query = query.where(MaintenanceWindows.asset_id == asset_id)

        # Exclude specific window from conflict check
        if exclude_id:
            query = query.where(MaintenanceWindows.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_window(
        self,
        name: str,
        start_time: datetime,
        end_time: datetime,
        scope_type: str,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        recurring: bool = False,
        timezone: Optional[str] = None,
        commit: bool = True,
    ) -> MaintenanceWindows:
        """
        Create a new maintenance window.

        Args:
            name: Window name
            start_time: Start time
            end_time: End time
            scope_type: Scope type (tenant, application, asset)
            application_id: Application ID for application scope
            asset_id: Asset ID for asset scope
            recurring: Whether window is recurring
            timezone: Timezone identifier
            commit: Whether to commit the transaction

        Returns:
            Created maintenance window
        """
        # Validate scope-specific requirements
        if scope_type == "application" and not application_id:
            raise ValueError("Application ID required for application scope")
        if scope_type == "asset" and not asset_id:
            raise ValueError("Asset ID required for asset scope")

        return await self.create(
            commit=commit,
            name=name,
            start_time=start_time,
            end_time=end_time,
            scope_type=scope_type,
            application_id=application_id,
            asset_id=asset_id,
            recurring=recurring,
            timezone=timezone,
        )


class BlackoutPeriodRepository(ContextAwareRepository[BlackoutPeriods]):
    """Repository for blackout periods."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        super().__init__(db, BlackoutPeriods, client_account_id, engagement_id)

    async def get_by_scope(
        self,
        scope_type: str,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> List[BlackoutPeriods]:
        """
        Get blackout periods by scope.

        Args:
            scope_type: Scope type (tenant, application, asset)
            application_id: Application ID for application scope
            asset_id: Asset ID for asset scope

        Returns:
            List of blackout periods for the specified scope
        """
        filters = {"scope_type": scope_type}

        if scope_type == "application" and application_id:
            filters["application_id"] = application_id
        elif scope_type == "asset" and asset_id:
            filters["asset_id"] = asset_id

        return await self.get_by_filters(**filters)

    async def get_active_blackouts(
        self,
        check_date: Optional[date] = None,
        scope_type: Optional[str] = None,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> List[BlackoutPeriods]:
        """
        Get currently active blackout periods.

        Args:
            check_date: Date to check against (defaults to today)
            scope_type: Optional scope type filter
            application_id: Optional application ID filter
            asset_id: Optional asset ID filter

        Returns:
            List of currently active blackout periods
        """
        if not check_date:
            check_date = date.today()

        # Build base query for active blackouts
        query = select(BlackoutPeriods).where(
            and_(
                BlackoutPeriods.start_date <= check_date,
                BlackoutPeriods.end_date >= check_date,
            )
        )

        # Apply context filters
        query = self._apply_context_filter(query)

        # Apply scope filters
        scope_filters = []
        if scope_type:
            scope_filters.append(BlackoutPeriods.scope_type == scope_type)
        if application_id:
            scope_filters.append(BlackoutPeriods.application_id == application_id)
        if asset_id:
            scope_filters.append(BlackoutPeriods.asset_id == asset_id)

        if scope_filters:
            query = query.where(and_(*scope_filters))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_upcoming_blackouts(
        self,
        days_ahead: int = 90,
        scope_type: Optional[str] = None,
    ) -> List[BlackoutPeriods]:
        """
        Get upcoming blackout periods within specified days.

        Args:
            days_ahead: Number of days to look ahead
            scope_type: Optional scope type filter

        Returns:
            List of upcoming blackout periods
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        query = select(BlackoutPeriods).where(
            and_(
                BlackoutPeriods.start_date >= start_date,
                BlackoutPeriods.start_date <= end_date,
            )
        )

        # Apply context filters
        query = self._apply_context_filter(query)

        if scope_type:
            query = query.where(BlackoutPeriods.scope_type == scope_type)

        query = query.order_by(BlackoutPeriods.start_date)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def check_conflicts(
        self,
        start_date: date,
        end_date: date,
        scope_type: str,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        exclude_id: Optional[str] = None,
    ) -> List[BlackoutPeriods]:
        """
        Check for conflicting blackout periods.

        Args:
            start_date: Proposed start date
            end_date: Proposed end date
            scope_type: Scope type
            application_id: Optional application ID
            asset_id: Optional asset ID
            exclude_id: Optional blackout ID to exclude from conflict check

        Returns:
            List of conflicting blackout periods
        """
        # Find overlapping blackouts
        query = select(BlackoutPeriods).where(
            and_(
                BlackoutPeriods.scope_type == scope_type,
                ~and_(
                    or_(
                        BlackoutPeriods.end_date < start_date,
                        BlackoutPeriods.start_date > end_date,
                    )
                ),
            )
        )

        # Apply context filters
        query = self._apply_context_filter(query)

        # Apply scope-specific filters
        if application_id:
            query = query.where(BlackoutPeriods.application_id == application_id)
        if asset_id:
            query = query.where(BlackoutPeriods.asset_id == asset_id)

        # Exclude specific blackout from conflict check
        if exclude_id:
            query = query.where(BlackoutPeriods.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_blackout(
        self,
        start_date: date,
        end_date: date,
        scope_type: str,
        reason: Optional[str] = None,
        application_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        commit: bool = True,
    ) -> BlackoutPeriods:
        """
        Create a new blackout period.

        Args:
            start_date: Start date
            end_date: End date
            scope_type: Scope type (tenant, application, asset)
            reason: Reason for blackout
            application_id: Application ID for application scope
            asset_id: Asset ID for asset scope
            commit: Whether to commit the transaction

        Returns:
            Created blackout period
        """
        # Validate scope-specific requirements
        if scope_type == "application" and not application_id:
            raise ValueError("Application ID required for application scope")
        if scope_type == "asset" and not asset_id:
            raise ValueError("Asset ID required for asset scope")

        return await self.create(
            commit=commit,
            start_date=start_date,
            end_date=end_date,
            scope_type=scope_type,
            reason=reason,
            application_id=application_id,
            asset_id=asset_id,
        )
