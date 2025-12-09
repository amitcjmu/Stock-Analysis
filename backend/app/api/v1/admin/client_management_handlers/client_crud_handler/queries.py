"""
Client CRUD Handler - Read Operations
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.admin_schemas import AdminSuccessResponse, ClientAccountResponse

# Import models with fallback
try:
    from app.models.client_account import ClientAccount, Engagement

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = None
    Engagement = None

logger = logging.getLogger(__name__)


class ClientQueryOperations:
    """Handler for client read operations"""

    @staticmethod
    async def get_client(client_id: str, db: AsyncSession) -> AdminSuccessResponse:
        """Get client account by ID"""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(
                    status_code=503, detail="Client models not available"
                )

            query = select(ClientAccount).where(ClientAccount.id == client_id)
            result = await db.execute(query)
            client = result.scalar_one_or_none()

            if not client:
                raise HTTPException(status_code=404, detail="Client account not found")

            response_data = await ClientQueryOperations._convert_client_to_response(
                client, db
            )

            return AdminSuccessResponse(
                message="Client account retrieved successfully", data=response_data
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving client account {client_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve client account: {str(e)}"
            )

    @staticmethod
    async def list_clients(
        db: AsyncSession,
        pagination: Dict[str, Any],
        filters: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all client accounts with pagination and filtering."""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(
                    status_code=503, detail="Client models not available"
                )

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
                        logger.info(f"Platform admin {user_id} - showing all clients")
                except Exception as e:
                    logger.warning(f"Could not check admin status: {e}")

            query = select(ClientAccount)

            # Apply filters (example)
            if filters.get("is_active") is not None:
                query = query.where(ClientAccount.is_active == filters["is_active"])
            if filters.get("account_name"):
                query = query.where(
                    ClientAccount.name.ilike(f"%{filters['account_name']}%")
                )

            # Get total items for pagination
            total_items_query = select(func.count()).select_from(query.alias())
            total_items_result = await db.execute(total_items_query)
            total_items = total_items_result.scalar_one()

            # Apply pagination
            page = pagination.get("page", 1)
            page_size = pagination.get("page_size", 20)
            query = query.offset((page - 1) * page_size).limit(page_size)

            # Execute query
            result = await db.execute(query)
            clients = result.scalars().all()

            # Convert to response format
            client_responses = [
                await ClientQueryOperations._convert_client_to_response(c, db)
                for c in clients
            ]

            total_pages = (total_items + page_size - 1) // page_size

            return {
                "items": client_responses,
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            }

        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            return {"error": "Failed to list client accounts"}

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(
                    status_code=503, detail="Client models not available"
                )

            # Total clients
            total_clients_query = select(func.count()).select_from(ClientAccount)
            total_clients = (await db.execute(total_clients_query)).scalar_one()

            # Active clients (based on is_active field)
            active_clients_query = select(func.count()).where(
                ClientAccount.is_active == True  # noqa: E712
            )  # noqa: E712
            active_clients = (await db.execute(active_clients_query)).scalar_one()

            # Clients by industry (handle None values)
            industry_query = select(ClientAccount.industry, func.count()).group_by(
                ClientAccount.industry
            )
            industry_results = await db.execute(industry_query)
            clients_by_industry = {}
            for industry, count in industry_results:
                # Convert None to "Unknown" for dictionary keys
                key = industry if industry is not None else "Unknown"
                clients_by_industry[key] = count

            # Clients by company size (handle None values)
            size_query = select(ClientAccount.company_size, func.count()).group_by(
                ClientAccount.company_size
            )
            size_results = await db.execute(size_query)
            clients_by_company_size = {}
            for size, count in size_results:
                # Convert None to "Unknown" for dictionary keys
                key = size if size is not None else "Unknown"
                clients_by_company_size[key] = count

            # Placeholder for clients by cloud provider as it's not a direct field
            clients_by_cloud_provider = {"aws": 0, "azure": 0, "gcp": 0}

            # Recent client registrations (last 30 days)
            recent_clients_query = (
                select(ClientAccount)
                .where(
                    ClientAccount.created_at > datetime.utcnow() - timedelta(days=30)
                )
                .order_by(ClientAccount.created_at.desc())
                .limit(5)
            )
            recent_clients_results = await db.execute(recent_clients_query)
            recent_clients = recent_clients_results.scalars().all()

            recent_client_registrations = [
                await ClientQueryOperations._convert_client_to_response(c, db)
                for c in recent_clients
            ]

            # Engagements by status
            status_query = select(Engagement.status, func.count()).group_by(
                Engagement.status
            )
            engagements_by_status = {
                row[0]: row[1]
                for row in (await db.execute(status_query)).all()
                if row[0]
            }

            # Average engagement duration
            duration_query = select(
                func.avg(
                    func.extract(
                        "epoch",
                        Engagement.actual_completion_date - Engagement.start_date,
                    )
                    / (60 * 60 * 24)
                )
            ).where(
                Engagement.actual_completion_date.isnot(None),
                Engagement.start_date.isnot(None),
            )
            average_duration = (await db.execute(duration_query)).scalar_one()

            return {
                "total_clients": total_clients,
                "active_clients": active_clients,
                "clients_by_industry": clients_by_industry,
                "clients_by_company_size": clients_by_company_size,
                "clients_by_cloud_provider": clients_by_cloud_provider,
                "recent_client_registrations": recent_client_registrations,
                "engagements_by_status": engagements_by_status,
                "average_engagement_duration": average_duration,
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to get dashboard stats: {str(e)}"
            )

    @staticmethod
    async def _convert_client_to_response(
        client: Any, db: AsyncSession
    ) -> ClientAccountResponse:
        """Convert a ClientAccount model to a ClientAccountResponse schema with all fields."""

        # Count engagements for this client
        engagement_query = (
            select(func.count())
            .select_from(Engagement)
            .where(Engagement.client_account_id == client.id)
        )
        engagement_result = await db.execute(engagement_query)
        engagement_count = engagement_result.scalar_one()

        # Count active engagements
        active_engagement_query = (
            select(func.count())
            .select_from(Engagement)
            .where(
                and_(
                    Engagement.client_account_id == client.id,
                    Engagement.is_active == True,  # noqa: E712
                )
            )
        )
        active_engagement_result = await db.execute(active_engagement_query)
        active_engagement_count = active_engagement_result.scalar_one()

        # Extract business objectives, IT guidelines, etc. from JSON fields
        business_objectives = client.business_objectives or {}
        it_guidelines = client.it_guidelines or {}
        decision_criteria = client.decision_criteria or {}
        agent_preferences = client.agent_preferences or {}

        # Extract arrays from business objectives
        primary_goals = (
            business_objectives.get("primary_goals", [])
            if isinstance(business_objectives, dict)
            else []
        )
        compliance_requirements = (
            business_objectives.get("compliance_requirements", [])
            if isinstance(business_objectives, dict)
            else []
        )
        business_priorities = (
            business_objectives.get("business_priorities", [])
            if isinstance(business_objectives, dict)
            else []
        )

        # Handle budget_constraints and timeline_constraints with proper type checking
        budget_constraints = (
            business_objectives.get("budget_constraints")
            if isinstance(business_objectives, dict)
            else None
        )
        if budget_constraints is not None and not isinstance(budget_constraints, dict):
            budget_constraints = None  # Convert non-dict values to None

        timeline_constraints = (
            business_objectives.get("timeline_constraints")
            if isinstance(business_objectives, dict)
            else None
        )
        if timeline_constraints is not None and not isinstance(
            timeline_constraints, dict
        ):
            timeline_constraints = None  # Convert non-dict values to None

        # Extract target cloud providers from IT guidelines
        target_cloud_providers = (
            it_guidelines.get("target_cloud_providers", [])
            if isinstance(it_guidelines, dict)
            else []
        )

        return ClientAccountResponse(
            id=str(client.id),
            account_name=client.name,
            slug=client.slug,
            industry=client.industry,
            company_size=client.company_size,
            headquarters_location=client.headquarters_location,
            primary_contact_name=client.primary_contact_name,
            primary_contact_email=client.primary_contact_email,
            primary_contact_phone=client.primary_contact_phone,
            description=client.description,
            subscription_tier=client.subscription_tier,
            billing_contact_email=client.billing_contact_email,
            settings=client.settings,
            branding=client.branding,
            created_by=str(client.created_by) if client.created_by else None,
            business_objectives=primary_goals,
            target_cloud_providers=target_cloud_providers,
            business_priorities=business_priorities,
            compliance_requirements=compliance_requirements,
            it_guidelines=it_guidelines,
            decision_criteria=decision_criteria,
            agent_preferences=agent_preferences,
            budget_constraints=budget_constraints,
            timeline_constraints=timeline_constraints,
            created_at=client.created_at,
            updated_at=client.updated_at,
            is_active=client.is_active,
            total_engagements=engagement_count,
            active_engagements=active_engagement_count,
            engagement_count=engagement_count,
        )
