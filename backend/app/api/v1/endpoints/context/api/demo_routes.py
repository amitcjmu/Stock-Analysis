"""
Demo Context Routes

Provides endpoints for fetching demo context data.
This allows the frontend to dynamically load demo IDs instead of using hardcoded values.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user_optional
from app.core.database import get_db
from app.core.seed_data_config import DemoDataConfig
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/demo", 
    summary="Get demo context",
    description="Fetch demo client, engagement, and users that have 'def0-def0-def0' pattern in their UUIDs"
)
async def get_demo_context(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get demo context data (client, engagement, users).
    
    This endpoint is used by the frontend during app initialization to dynamically
    fetch demo IDs instead of using hardcoded values. This prevents foreign key
    errors when the database is rebuilt or deployed to new environments.
    
    The demo data is identified by UUIDs containing 'def0-def0-def0' pattern.
    """
    try:
        # Find demo client (UUID contains 'def0-def0-def0')
        demo_client = None
        clients = await db.execute(
            "SELECT * FROM client_accounts WHERE id::text LIKE '%def0-def0-def0%' LIMIT 1"
        )
        client_row = clients.fetchone()
        
        if not client_row:
            logger.warning("No demo client found in database")
            raise HTTPException(status_code=404, detail="Demo client not found")
        
        demo_client = {
            "id": str(client_row.id),
            "name": client_row.name,
            "slug": client_row.slug,
            "description": client_row.description
        }
        
        # Find demo engagement for this client
        demo_engagement = None
        engagements = await db.execute(
            "SELECT * FROM engagements WHERE client_account_id = :client_id AND id::text LIKE '%def0-def0-def0%' LIMIT 1",
            {"client_id": client_row.id}
        )
        engagement_row = engagements.fetchone()
        
        if not engagement_row:
            logger.warning(f"No demo engagement found for client {client_row.id}")
            raise HTTPException(status_code=404, detail="Demo engagement not found")
        
        demo_engagement = {
            "id": str(engagement_row.id),
            "name": engagement_row.name,
            "slug": engagement_row.slug,
            "description": engagement_row.description,
            "client_account_id": str(engagement_row.client_account_id)
        }
        
        # Find demo users
        demo_users = []
        users = await db.execute(
            """
            SELECT u.id, u.email, up.role, up.first_name, up.last_name
            FROM users u
            JOIN user_profiles up ON u.id = up.user_id
            WHERE u.id::text LIKE '%def0-def0-def0%'
            LIMIT 10
            """
        )
        
        for user_row in users:
            demo_users.append({
                "id": str(user_row.id),
                "email": user_row.email,
                "role": user_row.role,
                "first_name": user_row.first_name,
                "last_name": user_row.last_name
            })
        
        logger.info(f"Demo context fetched successfully: client={demo_client['name']}, engagement={demo_engagement['name']}, users={len(demo_users)}")
        
        return {
            "client": demo_client,
            "engagement": demo_engagement,
            "users": demo_users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching demo context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch demo context: {str(e)}")


@router.get("/demo/validate",
    summary="Validate demo IDs",
    description="Check if given IDs are demo IDs (contain 'def0-def0-def0' pattern)"
)
async def validate_demo_ids(
    client_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Validate if the given IDs are demo IDs.
    
    Returns validation status for each provided ID.
    """
    results = {}
    
    if client_id:
        results["client_id"] = {
            "value": client_id,
            "is_demo": DemoDataConfig.is_demo_uuid(client_id)
        }
    
    if engagement_id:
        results["engagement_id"] = {
            "value": engagement_id,
            "is_demo": DemoDataConfig.is_demo_uuid(engagement_id)
        }
    
    if user_id:
        results["user_id"] = {
            "value": user_id,
            "is_demo": DemoDataConfig.is_demo_uuid(user_id)
        }
    
    return results