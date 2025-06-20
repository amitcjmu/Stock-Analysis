"""
Engagement CRUD Handler - Core engagement operations
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.client_account import Engagement
from app.schemas.admin_schemas import EngagementResponse
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class EngagementCRUDHandler:
    """Handler for engagement CRUD operations"""
    
    @staticmethod
    async def create_engagement(
        db: AsyncSession,
        engagement_data: Dict[str, Any],
        created_by: str
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
            engagement_name = engagement_data.get('engagement_name', '')
            slug = engagement_name.lower().replace(' ', '-').replace('_', '-')[:100] if engagement_name else 'engagement'
            
            # Convert date strings to datetime objects
            start_date = None
            if engagement_data.get('planned_start_date'):
                try:
                    start_date = date_parser.parse(engagement_data['planned_start_date'])
                except (ValueError, TypeError):
                    start_date = None
            
            target_completion_date = None
            if engagement_data.get('planned_end_date'):
                try:
                    target_completion_date = date_parser.parse(engagement_data['planned_end_date'])
                except (ValueError, TypeError):
                    target_completion_date = None
            
            mapped_data = {
                'name': engagement_name,
                'slug': slug,
                'description': engagement_data.get('engagement_description'),
                'client_account_id': engagement_data.get('client_account_id'),
                'engagement_type': engagement_data.get('target_cloud_provider', 'migration'),
                'status': 'planning',  # Default status
                'start_date': start_date,
                'target_completion_date': target_completion_date,
                'client_contact_name': engagement_data.get('engagement_manager'),
                'client_contact_email': None,  # Not provided in admin schema
                'migration_scope': {
                    'scope_type': engagement_data.get('migration_scope', 'full_datacenter'),
                    'target_clouds': [engagement_data.get('target_cloud_provider', 'aws')],
                    'migration_strategies': [],
                    'excluded_systems': [],
                    'included_environments': [],
                    'business_units': [],
                    'geographic_scope': [],
                    'timeline_constraints': {}
                },
                'team_preferences': engagement_data.get('team_preferences', {}),
                'settings': {
                    'estimated_budget': engagement_data.get('estimated_budget'),
                    'estimated_asset_count': engagement_data.get('estimated_asset_count'),
                    'technical_lead': engagement_data.get('technical_lead'),
                    'agent_configuration': engagement_data.get('agent_configuration', {}),
                    'discovery_preferences': engagement_data.get('discovery_preferences', {}),
                    'assessment_criteria': engagement_data.get('assessment_criteria', {})
                }
            }
            
            # Create new engagement
            engagement = Engagement(
                **mapped_data,
                created_by=created_by,
                is_active=True
            )
            
            db.add(engagement)
            await db.commit()
            await db.refresh(engagement)
            
            # Convert to response model
            return await EngagementCRUDHandler._convert_engagement_to_response(engagement)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating engagement: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create engagement: {str(e)}"
            )

    @staticmethod
    async def list_engagements(
        db: AsyncSession,
        client_account_id: str,
        pagination: Dict[str, Any]
    ) -> Dict[str, Any]:
        """List all engagements for a client with pagination."""
        try:
            page = pagination.get('page', 1)
            page_size = pagination.get('page_size', 20)

            query = select(Engagement)
            # Only filter by client_account_id if it's provided (not None)
            if client_account_id:
                 query = query.where(Engagement.client_account_id == client_account_id)
            
            total_items_query = select(func.count()).select_from(query.alias())
            total_items_result = await db.execute(total_items_query)
            total_items = total_items_result.scalar_one()

            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await db.execute(query)
            engagements = result.scalars().all()

            engagement_responses = []
            for eng in engagements:
                # Properly convert database model to response schema
                engagement_responses.append(await EngagementCRUDHandler._convert_engagement_to_response(eng))
            
            total_pages = (total_items + page_size - 1) // page_size
            
            return {
                "items": engagement_responses,
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        except Exception as e:
            logger.error(f"Error listing engagements for client {client_account_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred while listing engagements.")

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard statistics for engagements."""
        try:
            # Total engagements
            total_query = select(func.count()).select_from(Engagement)
            total_engagements = (await db.execute(total_query)).scalar_one()

            # Active engagements
            active_query = select(func.count()).where(Engagement.is_active == True)
            active_engagements = (await db.execute(active_query)).scalar_one()

            # Engagements by type
            type_query = select(Engagement.engagement_type, func.count()).group_by(Engagement.engagement_type)
            engagements_by_type = {
                row[0]: row[1] for row in (await db.execute(type_query)).all() if row[0]
            }

            # Engagements by status
            status_query = select(Engagement.status, func.count()).group_by(Engagement.status)
            engagements_by_status = {
                row[0]: row[1] for row in (await db.execute(status_query)).all() if row[0]
            }
            
            # Average engagement duration
            duration_query = select(
                func.avg(
                    func.extract('epoch', Engagement.actual_completion_date - Engagement.start_date) / (60*60*24)
                )
            ).where(
                Engagement.actual_completion_date.isnot(None),
                Engagement.start_date.isnot(None)
            )
            avg_duration_result = (await db.execute(duration_query)).scalar_one_or_none()
            avg_engagement_duration_days = round(avg_duration_result, 2) if avg_duration_result else 0.0

            # Recent engagements (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_query = select(Engagement).where(Engagement.created_at >= thirty_days_ago).order_by(Engagement.created_at.desc()).limit(5)
            recent_engagements = (await db.execute(recent_query)).scalars().all()
            
            # Convert recent engagements to response format
            recent_engagement_responses = []
            for eng in recent_engagements:
                recent_engagement_responses.append(await EngagementCRUDHandler._convert_engagement_to_response(eng))

            return {
                "total_engagements": total_engagements,
                "active_engagements": active_engagements,
                "engagements_by_type": engagements_by_type,
                "engagements_by_status": engagements_by_status,
                "avg_engagement_duration_days": avg_engagement_duration_days,
                "recent_engagements": recent_engagement_responses,
            }
        except Exception as e:
            logger.error(f"Error getting engagement dashboard stats: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard stats: {str(e)}")

    @staticmethod
    async def _convert_engagement_to_response(engagement: Engagement) -> EngagementResponse:
        """Convert Engagement model to EngagementResponse schema with proper field mapping."""
        try:
            # Handle migration_scope - convert to string if it's a dict
            migration_scope = engagement.migration_scope
            if isinstance(migration_scope, dict):
                # Convert dict to a readable string representation
                scope_parts = []
                if migration_scope.get('target_clouds'):
                    scope_parts.append(f"Clouds: {', '.join(migration_scope['target_clouds'])}")
                if migration_scope.get('migration_strategies'):
                    scope_parts.append(f"Strategies: {', '.join(migration_scope['migration_strategies'])}")
                if migration_scope.get('business_units'):
                    scope_parts.append(f"Units: {', '.join(migration_scope['business_units'])}")
                migration_scope = "; ".join(scope_parts) if scope_parts else "Full Migration"
            elif not migration_scope:
                migration_scope = "Full Migration"

            return EngagementResponse(
                id=str(engagement.id),
                engagement_name=engagement.name,  # Map 'name' to 'engagement_name'
                client_account_id=str(engagement.client_account_id),
                engagement_description=engagement.description,
                migration_scope=migration_scope,
                target_cloud_provider=engagement.engagement_type or "aws",
                planned_start_date=engagement.start_date,
                planned_end_date=engagement.target_completion_date,
                actual_start_date=engagement.start_date,  # Use start_date as actual_start_date
                actual_end_date=engagement.actual_completion_date,
                engagement_manager=engagement.client_contact_name or "Not Assigned",
                technical_lead=engagement.client_contact_name or "Not Assigned",
                team_preferences=engagement.team_preferences or {},
                agent_configuration={},  # Default empty dict
                discovery_preferences={},  # Default empty dict
                assessment_criteria={},  # Default empty dict
                current_phase=engagement.status or "planning",
                completion_percentage=0.0,  # Default to 0.0
                current_session_id=None,  # Default to None
                created_at=engagement.created_at,
                updated_at=engagement.updated_at,
                is_active=engagement.is_active,
                total_sessions=0,  # Default to 0
                total_assets=0  # Default to 0
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
                is_active=engagement.is_active
            ) 