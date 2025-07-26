"""
Engagement CRUD Handler - Core engagement operations
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.models.client_account import Engagement
from app.schemas.admin_schemas import AdminSuccessResponse, EngagementResponse
from dateutil import parser as date_parser
from fastapi import HTTPException
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EngagementCRUDHandler:
    """Handler for engagement CRUD operations"""

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
            return await EngagementCRUDHandler._convert_engagement_to_response(
                engagement
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating engagement: {e}", exc_info=True)
            raise HTTPException(
                status_code=400, detail=f"Failed to create engagement: {str(e)}"
            )

    @staticmethod
    async def list_engagements(
        db: AsyncSession,
        client_account_id: Optional[str],
        pagination: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all engagements for a client with pagination."""
        try:
            page = pagination.get("page", 1)
            page_size = pagination.get("page_size", 20)

            # Check if user is platform admin
            is_platform_admin = False
            if user_id:
                try:
                    from app.models.rbac import RoleType, UserRole

                    admin_check = await db.execute(
                        select(UserRole).where(
                            and_(
                                UserRole.user_id == user_id,
                                UserRole.role_type == RoleType.PLATFORM_ADMIN,
                                UserRole.is_active == True,  # noqa: E712
                            )
                        )
                    )
                    admin_role = admin_check.scalar_one_or_none()
                    is_platform_admin = admin_role is not None

                    if is_platform_admin:
                        logger.info(
                            f"Platform admin {user_id} - showing all engagements"
                        )
                except Exception as e:
                    logger.warning(f"Could not check admin status: {e}")

            query = select(Engagement).where(
                Engagement.is_active == True  # noqa: E712
            )  # Filter out soft-deleted
            # Only filter by client_account_id if it's provided (not None) AND user is not platform admin
            if client_account_id is not None and not is_platform_admin:
                query = query.where(Engagement.client_account_id == client_account_id)

            # Build the count query with the same conditions
            count_query = (
                select(func.count())
                .select_from(Engagement)
                .where(Engagement.is_active == True)  # noqa: E712
            )
            if client_account_id is not None and not is_platform_admin:
                count_query = count_query.where(
                    Engagement.client_account_id == client_account_id
                )

            total_items_result = await db.execute(count_query)
            total_items = total_items_result.scalar_one()

            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await db.execute(query)
            engagements = result.scalars().all()

            engagement_responses = []
            for eng in engagements:
                # Properly convert database model to response schema
                engagement_responses.append(
                    await EngagementCRUDHandler._convert_engagement_to_response(eng)
                )

            total_pages = (total_items + page_size - 1) // page_size

            return {
                "items": engagement_responses,
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }
        except Exception as e:
            logger.error(
                f"Error listing engagements for client {client_account_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred while listing engagements: {str(e)}",
            )

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard statistics for engagements."""
        try:
            # Total engagements (only active ones)
            total_query = select(func.count()).where(
                Engagement.is_active == True  # noqa: E712
            )
            total_engagements = (await db.execute(total_query)).scalar_one()

            # Active engagements (redundant now since we only count active ones)
            active_query = select(func.count()).where(
                Engagement.is_active == True  # noqa: E712
            )
            active_engagements = (await db.execute(active_query)).scalar_one()

            # Engagements by type (only active ones)
            type_query = (
                select(Engagement.engagement_type, func.count())
                .where(Engagement.is_active == True)  # noqa: E712
                .group_by(Engagement.engagement_type)
            )
            engagements_by_type = {
                row[0]: row[1] for row in (await db.execute(type_query)).all() if row[0]
            }

            # Engagements by status (only active ones)
            status_query = (
                select(Engagement.status, func.count())
                .where(Engagement.is_active == True)  # noqa: E712
                .group_by(Engagement.status)
            )
            engagements_by_status = {
                row[0]: row[1]
                for row in (await db.execute(status_query)).all()
                if row[0]
            }

            # Average engagement duration (only active ones)
            duration_query = select(
                func.avg(
                    func.extract(
                        "epoch",
                        Engagement.actual_completion_date - Engagement.start_date,
                    )
                    / (60 * 60 * 24)
                )
            ).where(
                Engagement.is_active == True,  # noqa: E712
                Engagement.actual_completion_date.isnot(None),
                Engagement.start_date.isnot(None),
            )
            avg_duration_result = (
                await db.execute(duration_query)
            ).scalar_one_or_none()
            avg_engagement_duration_days = (
                round(avg_duration_result, 2) if avg_duration_result else 0.0
            )

            # Recent engagements (last 30 days, only active ones)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_query = (
                select(Engagement)
                .where(
                    Engagement.is_active == True,  # noqa: E712
                    Engagement.created_at >= thirty_days_ago,
                )
                .order_by(Engagement.created_at.desc())
                .limit(5)
            )
            recent_engagements = (await db.execute(recent_query)).scalars().all()

            # Convert recent engagements to response format
            recent_engagement_responses = []
            for eng in recent_engagements:
                recent_engagement_responses.append(
                    await EngagementCRUDHandler._convert_engagement_to_response(eng)
                )

            return {
                "total_engagements": total_engagements,
                "active_engagements": active_engagements,
                "engagements_by_type": engagements_by_type,
                "engagements_by_status": engagements_by_status,
                "avg_engagement_duration_days": avg_engagement_duration_days,
                "recent_engagements": recent_engagement_responses,
            }
        except Exception as e:
            logger.error(
                f"Error getting engagement dashboard stats: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve dashboard stats: {str(e)}"
            )

    @staticmethod
    async def get_engagement(
        engagement_id: str, db: AsyncSession
    ) -> EngagementResponse:
        """Get engagement by ID."""
        try:
            query = select(Engagement).where(
                Engagement.id == engagement_id,
                Engagement.is_active
                == True,  # noqa: E712  # Only return active engagements
            )
            result = await db.execute(query)
            engagement = result.scalar_one_or_none()

            if not engagement:
                raise HTTPException(status_code=404, detail="Engagement not found")

            return await EngagementCRUDHandler._convert_engagement_to_response(
                engagement
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving engagement {engagement_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve engagement: {str(e)}"
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
                Engagement.is_active
                == True,  # noqa: E712  # Only allow updating active engagements
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

            # Direct field mapping - handle the most important fields
            for field, value in update_dict.items():
                if field == "engagement_name" and value:
                    engagement.name = value
                elif field == "engagement_description" and value:
                    engagement.description = value
                elif field == "target_cloud_provider" and value:
                    engagement.engagement_type = value
                elif field == "migration_phase" and value:
                    engagement.status = value
                elif field == "current_phase" and value:
                    engagement.status = value
                elif field == "engagement_manager" and value:
                    engagement.client_contact_name = value
                elif field == "technical_lead" and value:
                    # Store technical lead in settings
                    current_settings = engagement.settings or {}
                    if not isinstance(current_settings, dict):
                        current_settings = {}
                    current_settings["technical_lead"] = value
                    engagement.settings = current_settings
                elif field in ["start_date", "planned_start_date"] and value:
                    parsed_date = parse_date_string(value)
                    if parsed_date:
                        engagement.start_date = parsed_date
                elif field in ["end_date", "planned_end_date"] and value:
                    parsed_date = parse_date_string(value)
                    if parsed_date:
                        engagement.target_completion_date = parsed_date
                elif field == "budget" and value is not None:
                    # Store budget in settings
                    current_settings = engagement.settings or {}
                    if not isinstance(current_settings, dict):
                        current_settings = {}
                    current_settings["estimated_budget"] = float(value)
                    engagement.settings = current_settings
                elif field == "budget_currency" and value:
                    # Store budget currency in settings
                    current_settings = engagement.settings or {}
                    if not isinstance(current_settings, dict):
                        current_settings = {}
                    current_settings["budget_currency"] = value
                    engagement.settings = current_settings
                elif field == "migration_scope" and value:
                    # Simple migration scope handling
                    current_scope = engagement.migration_scope or {}
                    if not isinstance(current_scope, dict):
                        current_scope = {}
                    current_scope["scope_type"] = value
                    engagement.migration_scope = current_scope
                elif field == "client_account_id" and value:
                    engagement.client_account_id = value
                elif hasattr(engagement, field):
                    # Direct field exists on model
                    setattr(engagement, field, value)

            # Update the updated_at timestamp
            engagement.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(engagement)

            response_data = await EngagementCRUDHandler._convert_engagement_to_response(
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
                # Delete records in proper order based on actual foreign key relationships

                # 1. Delete records that reference data_imports
                await db.execute(
                    text(
                        """
                    DELETE FROM raw_import_records
                    WHERE data_import_id IN (
                        SELECT id FROM data_imports
                        WHERE engagement_id = :engagement_id
                    )
                """
                    ),
                    {"engagement_id": engagement_id},
                )

                await db.execute(
                    text(
                        """
                    DELETE FROM import_field_mappings
                    WHERE data_import_id IN (
                        SELECT id FROM data_imports
                        WHERE engagement_id = :engagement_id
                    )
                """
                    ),
                    {"engagement_id": engagement_id},
                )

                # 2. Delete data_imports for this engagement
                await db.execute(
                    text(
                        """
                    DELETE FROM data_imports
                    WHERE engagement_id = :engagement_id
                """
                    ),
                    {"engagement_id": engagement_id},
                )

                # 3. Delete other records that directly reference the engagement
                tables_to_clean = [
                    "access_audit_log",
                    "assessments",
                    "asset_embeddings",
                    "assets",
                    "cmdb_sixr_analyses",
                    "data_imports",
                    "engagement_access",
                    "feedback",
                    "feedback_summaries",
                    "llm_usage_logs",
                    "llm_usage_summary",
                    "mapping_learning_patterns",
                    "migration_waves",
                    "sixr_analyses",
                    "wave_plans",
                ]

                for table in tables_to_clean:
                    try:
                        await db.execute(
                            text(
                                f"""
                            DELETE FROM {table}
                            WHERE engagement_id = :engagement_id
                        """  # nosec B608 - table names are hardcoded, not user input
                            ),
                            {"engagement_id": engagement_id},
                        )
                    except Exception as table_error:
                        logger.warning(
                            f"Could not delete from {table}: {table_error}"  # nosec B608
                        )
                        # Continue with other tables

                # 4. Handle user-related references (set to NULL instead of delete)
                await db.execute(
                    text(
                        """
                    UPDATE users
                    SET default_engagement_id = NULL
                    WHERE default_engagement_id = :engagement_id
                """
                    ),
                    {"engagement_id": engagement_id},
                )

                await db.execute(
                    text(
                        """
                    UPDATE user_roles
                    SET scope_engagement_id = NULL
                    WHERE scope_engagement_id = :engagement_id
                """
                    ),
                    {"engagement_id": engagement_id},
                )

                # 5. Finally delete the engagement itself
                await db.delete(engagement)
                await db.commit()

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
                    engagement.is_active = False
                    engagement.status = "deleted"
                    await db.commit()

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
    async def _convert_engagement_to_response(
        engagement: Engagement,
    ) -> EngagementResponse:
        """Convert Engagement model to EngagementResponse schema with proper field mapping."""
        try:
            # Handle migration_scope - convert to string if it's a dict
            migration_scope = engagement.migration_scope
            if isinstance(migration_scope, dict):
                # Convert dict to a readable string representation
                scope_parts = []
                if migration_scope.get("target_clouds"):
                    scope_parts.append(
                        f"Clouds: {', '.join(migration_scope['target_clouds'])}"
                    )
                if migration_scope.get("migration_strategies"):
                    scope_parts.append(
                        f"Strategies: {', '.join(migration_scope['migration_strategies'])}"
                    )
                if migration_scope.get("business_units"):
                    scope_parts.append(
                        f"Units: {', '.join(migration_scope['business_units'])}"
                    )
                if migration_scope.get("scope_type"):
                    scope_parts.append(f"Type: {migration_scope['scope_type']}")
                migration_scope = (
                    "; ".join(scope_parts) if scope_parts else "Full Migration"
                )
            elif not migration_scope:
                migration_scope = "Full Migration"

            # Extract budget information from settings
            settings = engagement.settings or {}
            estimated_budget = settings.get("estimated_budget", 0.0)
            settings.get("budget_currency", "USD")

            return EngagementResponse(
                id=str(engagement.id),
                engagement_name=engagement.name,  # Map 'name' to 'engagement_name'
                client_account_id=str(engagement.client_account_id),
                engagement_description=engagement.description,
                migration_scope=migration_scope,
                target_cloud_provider=engagement.engagement_type or "aws",
                planned_start_date=engagement.start_date,
                planned_end_date=engagement.target_completion_date,
                estimated_budget=estimated_budget,
                actual_start_date=engagement.start_date,  # Use start_date as actual_start_date
                actual_end_date=engagement.actual_completion_date,
                engagement_manager=engagement.client_contact_name or "Not Assigned",
                technical_lead=settings.get(
                    "technical_lead", engagement.client_contact_name or "Not Assigned"
                ),
                team_preferences=engagement.team_preferences or {},
                agent_configuration=settings.get("agent_configuration", {}),
                discovery_preferences=settings.get("discovery_preferences", {}),
                assessment_criteria=settings.get("assessment_criteria", {}),
                current_phase=engagement.status or "planning",
                completion_percentage=0.0,  # Default to 0.0
                current_flow_id=None,  # Default to None
                created_at=engagement.created_at,
                updated_at=engagement.updated_at,
                is_active=engagement.is_active,
                total_flows=0,  # Default to 0
                total_assets=0,  # Default to 0
            )
        except Exception as e:
            logger.error(f"Error converting engagement to response: {e}")
            # Return a minimal valid response to prevent complete failure
            return EngagementResponse(
                id=str(engagement.id),
                engagement_name=engagement.name or "Unknown Engagement",
                client_account_id=str(engagement.client_account_id),
                engagement_description=engagement.description or "",
                migration_scope="Full Migration",
                target_cloud_provider="aws",
                current_phase="planning",
                completion_percentage=0.0,
                created_at=engagement.created_at or datetime.utcnow(),
                is_active=engagement.is_active,
            )
