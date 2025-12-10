"""
Engagement command operations (write operations)
"""

import logging
from datetime import datetime
from typing import Any, Dict

from dateutil import parser as date_parser
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_account import Engagement
from app.schemas.admin_schemas import AdminSuccessResponse, EngagementResponse

from .queries import EngagementQueries
from .utils import (
    _perform_cascade_deletion,
    _perform_soft_delete,
    _process_field_updates,
)

logger = logging.getLogger(__name__)


class EngagementCommands:
    """Handler for engagement write operations"""

    @staticmethod
    async def create_engagement(
        db: AsyncSession, engagement_data: Dict[str, Any], created_by: str
    ) -> EngagementResponse:
        """Create a new engagement.

        Args:
            db: Database session
            engagement_data: Engagement data to create
            created_by: ID of the user creating the engagement

        Returns:
            EngagementResponse: The created engagement
        """
        try:
            # Map admin schema fields to database model fields
            engagement_name = engagement_data.get("engagement_name", "")
            slug = (
                engagement_name.lower().replace(" ", "-").replace("_", "-")[:100]
                if engagement_name
                else "engagement"
            )

            # Convert date strings to datetime objects
            start_date = None
            if engagement_data.get("planned_start_date"):
                try:
                    start_date = date_parser.parse(
                        engagement_data["planned_start_date"]
                    )
                except (ValueError, TypeError):
                    start_date = None

            target_completion_date = None
            if engagement_data.get("planned_end_date"):
                try:
                    target_completion_date = date_parser.parse(
                        engagement_data["planned_end_date"]
                    )
                except (ValueError, TypeError):
                    target_completion_date = None

            mapped_data = {
                "name": engagement_name,
                "slug": slug,
                "description": engagement_data.get("engagement_description"),
                "client_account_id": engagement_data.get("client_account_id"),
                "engagement_type": engagement_data.get(
                    "target_cloud_provider", "migration"
                ),
                "status": "planning",  # Default status
                "start_date": start_date,
                "target_completion_date": target_completion_date,
                "client_contact_name": engagement_data.get("engagement_manager"),
                "client_contact_email": None,  # Not provided in admin schema
                "migration_scope": {
                    "scope_type": engagement_data.get(
                        "migration_scope", "full_datacenter"
                    ),
                    "target_clouds": [
                        engagement_data.get("target_cloud_provider", "aws")
                    ],
                    "migration_strategies": [],
                    "excluded_systems": [],
                    "included_environments": [],
                    "business_units": [],
                    "geographic_scope": [],
                    "timeline_constraints": {},
                },
                "team_preferences": engagement_data.get("team_preferences", {}),
                "settings": {
                    "estimated_budget": engagement_data.get("estimated_budget"),
                    "estimated_asset_count": engagement_data.get(
                        "estimated_asset_count"
                    ),
                    "technical_lead": engagement_data.get("technical_lead"),
                    "agent_configuration": engagement_data.get(
                        "agent_configuration", {}
                    ),
                    "discovery_preferences": engagement_data.get(
                        "discovery_preferences", {}
                    ),
                    "assessment_criteria": engagement_data.get(
                        "assessment_criteria", {}
                    ),
                },
            }

            # Create new engagement
            engagement = Engagement(
                **mapped_data, created_by=created_by, is_active=True
            )

            db.add(engagement)
            await db.commit()
            await db.refresh(engagement)

            # Convert to response model
            return await EngagementQueries._convert_engagement_to_response(engagement)

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating engagement: {e}", exc_info=True)
            raise HTTPException(
                status_code=400, detail=f"Failed to create engagement: {str(e)}"
            )

    @staticmethod
    async def update_engagement(
        engagement_id: str,
        update_data: Any,  # EngagementUpdate schema
        db: AsyncSession,
        admin_user: str,
    ) -> Dict[str, Any]:
        """Update engagement."""
        try:
            query = select(Engagement).where(
                Engagement.id == engagement_id,
                Engagement.is_active,  # noqa: E712  # Only allow updating active engagements
            )
            result = await db.execute(query)
            engagement = result.scalar_one_or_none()

            if not engagement:
                raise HTTPException(
                    status_code=404, detail="Engagement not found or has been deleted"
                )

            # Update fields from the update_data
            update_dict = (
                update_data.dict(exclude_unset=True)
                if hasattr(update_data, "dict")
                else update_data
            )

            # Handle date parsing
            def parse_date_string(date_str):
                if not date_str:
                    return None
                try:
                    # Try parsing different date formats
                    from dateutil import parser as date_parser

                    return date_parser.parse(date_str)
                except (ValueError, TypeError):
                    return None

            # Process field updates using helper functions
            _process_field_updates(engagement, update_dict, parse_date_string)

            # Update the updated_at timestamp
            engagement.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(engagement)

            response_data = await EngagementQueries._convert_engagement_to_response(
                engagement
            )

            logger.info(f"Engagement updated: {engagement_id} by admin {admin_user}")

            return AdminSuccessResponse(
                message="Engagement updated successfully", data=response_data
            )

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating engagement {engagement_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to update engagement: {str(e)}"
            )

    @staticmethod
    async def delete_engagement(
        engagement_id: str, db: AsyncSession, admin_user: str
    ) -> Dict[str, Any]:
        """Delete engagement with proper cascade handling for foreign key constraints."""
        try:
            from app.schemas.admin_schemas import AdminSuccessResponse

            query = select(Engagement).where(Engagement.id == engagement_id)
            result = await db.execute(query)
            engagement = result.scalar_one_or_none()

            if not engagement:
                raise HTTPException(status_code=404, detail="Engagement not found")

            engagement_name = engagement.name

            # Handle cascade deletion of related records to avoid foreign key constraints
            try:
                await _perform_cascade_deletion(db, engagement_id, engagement)

                logger.info(
                    f"Engagement deleted with cascade cleanup: {engagement_name} by admin {admin_user}"
                )

                return AdminSuccessResponse(
                    message=f"Engagement '{engagement_name}' deleted successfully"
                )

            except Exception as cascade_error:
                await db.rollback()
                logger.error(
                    f"Error during cascade deletion for engagement {engagement_id}: {cascade_error}"
                )

                # If cascade deletion fails, try soft delete instead
                try:
                    await _perform_soft_delete(db, engagement)

                    logger.info(
                        f"Engagement soft-deleted due to constraints: {engagement_name} by admin {admin_user}"
                    )

                    return AdminSuccessResponse(
                        message=f"Engagement '{engagement_name}' deactivated (soft delete due to data dependencies)"
                    )

                except Exception as soft_delete_error:
                    await db.rollback()
                    logger.error(
                        f"Error during soft delete for engagement {engagement_id}: {soft_delete_error}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to delete engagement: Unable to delete due to data dependencies. "
                        "Please contact administrator.",
                    )

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting engagement {engagement_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to delete engagement: {str(e)}"
            )

    @staticmethod
    async def bulk_delete_engagements(
        engagement_ids: list, db: AsyncSession, admin_user: str
    ) -> Dict[str, Any]:
        """Bulk delete multiple engagements."""
        from app.schemas.admin_schemas import AdminSuccessResponse

        deleted_count = 0
        failed_count = 0
        errors = []

        for engagement_id in engagement_ids:
            try:
                result = await EngagementCommands.delete_engagement(
                    engagement_id, db, admin_user
                )
                if "deleted successfully" in result.message:
                    deleted_count += 1
                else:
                    # Soft deleted
                    deleted_count += 1
            except HTTPException as e:
                failed_count += 1
                errors.append(f"Engagement {engagement_id}: {e.detail}")
            except Exception as e:
                failed_count += 1
                errors.append(f"Engagement {engagement_id}: {str(e)}")

        message = (
            f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed"
        )
        if errors:
            message += f". Errors: {'; '.join(errors[:5])}"
            if len(errors) > 5:
                message += f" (+{len(errors) - 5} more)"

        return AdminSuccessResponse(
            message=message,
            data={
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "errors": errors,
            },
        )
