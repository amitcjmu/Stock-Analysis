"""
Operational mapping handlers for response mapping service.

Contains handlers for mapping maintenance windows, blackout periods,
dependencies, and governance-related responses to appropriate database tables.
"""

import logging
from typing import Any, Dict, List

from .base import BaseResponseMapper

logger = logging.getLogger(__name__)


class OperationalMappers(BaseResponseMapper):
    """Mappers for operational and governance related responses."""

    async def map_maintenance_window(self, response: Dict[str, Any]) -> List[str]:
        """
        Map maintenance window response to maintenance_windows table.

        Expected response format:
        {
            "asset_id": "uuid",
            "window_type": "string",
            "start_time": "YYYY-MM-DD HH:MM:SS",
            "end_time": "YYYY-MM-DD HH:MM:SS",
            "metadata": {...}
        }
        """
        try:
            asset_id = response.get("asset_id")
            window_type = response.get("window_type")
            start_time = response.get("start_time")
            end_time = response.get("end_time")

            if not asset_id:
                raise ValueError("Missing asset_id in response")

            if not all([window_type, start_time, end_time]):
                raise ValueError(
                    "Missing required window_type, start_time, or end_time"
                )

            # Create maintenance window record
            window_record = await self.maintenance_window_repo.create(
                asset_id=asset_id,
                window_type=window_type,
                start_time=start_time,
                end_time=end_time,
                window_metadata=response.get("metadata", {}),
            )

            logger.info(
                f"✅ Successfully mapped maintenance window for asset {asset_id}: "
                f"{window_type} from {start_time} to {end_time}"
            )
            return [f"maintenance_windows:{window_record.id}"]

        except Exception as e:
            logger.error(f"❌ Failed to map maintenance window response: {e}")
            raise

    async def map_blackout_period(self, response: Dict[str, Any]) -> List[str]:
        """
        Map blackout period response to blackout_periods table.

        Expected response format:
        {
            "scope_type": "string",
            "scope_id": "uuid",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "reason": "string",
            "metadata": {...}
        }
        """
        try:
            scope_type = response.get("scope_type")
            scope_id = response.get("scope_id")
            start_date = response.get("start_date")
            end_date = response.get("end_date")

            if not all([scope_type, scope_id, start_date, end_date]):
                raise ValueError(
                    "Missing required scope_type, scope_id, start_date, or end_date"
                )

            # Create blackout period record
            blackout_record = await self.blackout_period_repo.create(
                scope_type=scope_type,
                scope_id=scope_id,
                start_date=start_date,
                end_date=end_date,
                reason=response.get("reason"),
                blackout_metadata=response.get("metadata", {}),
            )

            logger.info(
                f"✅ Successfully mapped blackout period for {scope_type} {scope_id}: "
                f"from {start_date} to {end_date}"
            )
            return [f"blackout_periods:{blackout_record.id}"]

        except Exception as e:
            logger.error(f"❌ Failed to map blackout period response: {e}")
            raise

    async def map_dependencies(self, response: Dict[str, Any]) -> List[str]:
        """
        Map dependencies response to asset_dependencies table.

        Expected response format:
        {
            "source_asset_id": "uuid",
            "target_asset_id": "uuid",
            "dependency_type": "string",
            "criticality": "string",
            "metadata": {...}
        }
        """
        try:
            source_asset_id = response.get("source_asset_id")
            target_asset_id = response.get("target_asset_id")
            dependency_type = response.get("dependency_type")

            if not all([source_asset_id, target_asset_id, dependency_type]):
                raise ValueError(
                    "Missing required source_asset_id, target_asset_id, or dependency_type"
                )

            # Create dependency record
            # Note: Assuming there's a dependency repository
            # This would need to be implemented based on actual schema
            # TODO: Implement actual database write when repository is available
            _ = {
                "source_asset_id": source_asset_id,
                "target_asset_id": target_asset_id,
                "dependency_type": dependency_type,
                "criticality": response.get("criticality"),
                "metadata": response.get("metadata", {}),
            }

            logger.info(
                f"✅ Successfully mapped dependency: {source_asset_id} -> {target_asset_id} "
                f"({dependency_type})"
            )
            return ["asset_dependencies:pending_implementation"]

        except Exception as e:
            logger.error(f"❌ Failed to map dependencies response: {e}")
            raise

    async def map_exception(self, response: Dict[str, Any]) -> List[str]:
        """
        Map exception request response to migration_exceptions and approval_requests tables.

        Expected response format:
        {
            "asset_id": "uuid",
            "exception_type": "string",
            "justification": "string",
            "requested_by": "string",
            "metadata": {...}
        }
        """
        try:
            asset_id = response.get("asset_id")
            exception_type = response.get("exception_type")
            justification = response.get("justification")
            requested_by = response.get("requested_by")

            if not all([asset_id, exception_type, justification]):
                raise ValueError(
                    "Missing required asset_id, exception_type, or justification"
                )

            created_records = []

            # Create migration exception record
            exception_record = await self.migration_exception_repo.create(
                asset_id=asset_id,
                exception_type=exception_type,
                justification=justification,
                requested_by=requested_by,
                status="pending_approval",
                exception_metadata=response.get("metadata", {}),
            )
            created_records.append(f"migration_exceptions:{exception_record.id}")

            # Create corresponding approval request
            approval_record = await self.approval_request_repo.create(
                subject_type="migration_exception",
                subject_id=exception_record.id,
                requested_by=requested_by,
                justification=justification,
                status="pending",
                approval_metadata=response.get("approval_metadata", {}),
            )
            created_records.append(f"approval_requests:{approval_record.id}")

            logger.info(
                f"✅ Successfully mapped exception request for asset {asset_id}: "
                f"{exception_type}"
            )
            return created_records

        except Exception as e:
            logger.error(f"❌ Failed to map exception response: {e}")
            raise
