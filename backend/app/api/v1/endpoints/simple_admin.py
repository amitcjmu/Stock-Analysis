"""
Simple Admin Endpoints
These endpoints match the actual database schema and provide basic admin functionality.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.v1.auth.auth_utils import get_current_user
from app.models.client_account import User, ClientAccount, Engagement

logger = logging.getLogger(__name__)

# Create simple admin router
simple_admin_router = APIRouter(prefix="/simple-admin", tags=["Simple Admin"])


class SimpleClientCreate(BaseModel):
    """Schema for creating a simple client that matches the actual database."""

    name: str
    description: str = ""


class SimpleEngagementCreate(BaseModel):
    """Schema for creating a simple engagement."""

    name: str
    description: str = ""
    client_account_id: str


@simple_admin_router.post("/clients")
async def create_simple_client(
    client_data: SimpleClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a simple client account that matches the actual database schema."""
    try:
        # Check if client already exists
        existing_query = select(ClientAccount).where(
            ClientAccount.name == client_data.name
        )
        result = await db.execute(existing_query)
        existing_client = result.scalar_one_or_none()

        if existing_client:
            raise HTTPException(
                status_code=400,
                detail=f"Client account '{client_data.name}' already exists",
            )

        # Create new client account with only the fields that exist in DB
        client = ClientAccount(
            id=uuid.uuid4(),
            name=client_data.name,
            description=client_data.description,
            is_active=True,
        )

        db.add(client)
        await db.commit()
        await db.refresh(client)

        logger.info(
            f"Simple client account created: {client_data.name} by user {current_user.id}"
        )

        return {
            "status": "success",
            "message": f"Client account '{client_data.name}' created successfully",
            "data": {
                "id": str(client.id),
                "name": client.name,
                "description": client.description,
                "is_active": client.is_active,
                "created_at": (
                    client.created_at.isoformat() if client.created_at else None
                ),
                "updated_at": (
                    client.updated_at.isoformat() if client.updated_at else None
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating simple client account: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create client account: {str(e)}"
        )


@simple_admin_router.post("/engagements")
async def create_simple_engagement(
    engagement_data: SimpleEngagementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a simple engagement for a client."""
    try:
        # Verify client exists
        client_query = select(ClientAccount).where(
            ClientAccount.id == engagement_data.client_account_id
        )
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()

        if not client:
            raise HTTPException(
                status_code=404,
                detail=f"Client account '{engagement_data.client_account_id}' not found",
            )

        # Create new engagement
        engagement = Engagement(
            id=uuid.uuid4(),
            name=engagement_data.name,
            description=engagement_data.description,
            client_account_id=uuid.UUID(engagement_data.client_account_id),
            is_active=True,
        )

        db.add(engagement)
        await db.commit()
        await db.refresh(engagement)

        logger.info(
            f"Simple engagement created: {engagement_data.name} for client {client.name} by user {current_user.id}"
        )

        return {
            "status": "success",
            "message": f"Engagement '{engagement_data.name}' created successfully",
            "data": {
                "id": str(engagement.id),
                "name": engagement.name,
                "description": engagement.description,
                "client_account_id": str(engagement.client_account_id),
                "client_name": client.name,
                "is_active": engagement.is_active,
                "created_at": (
                    engagement.created_at.isoformat() if engagement.created_at else None
                ),
                "updated_at": (
                    engagement.updated_at.isoformat() if engagement.updated_at else None
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating simple engagement: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create engagement: {str(e)}"
        )


@simple_admin_router.get("/clients")
async def list_simple_clients(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """List all client accounts."""
    try:
        query = select(ClientAccount).where(ClientAccount.is_active is True)
        result = await db.execute(query)
        clients = result.scalars().all()

        return {
            "status": "success",
            "data": [
                {
                    "id": str(client.id),
                    "name": client.name,
                    "description": client.description,
                    "is_active": client.is_active,
                    "created_at": (
                        client.created_at.isoformat() if client.created_at else None
                    ),
                    "updated_at": (
                        client.updated_at.isoformat() if client.updated_at else None
                    ),
                }
                for client in clients
            ],
        }

    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list clients: {str(e)}")


@simple_admin_router.get("/engagements")
async def list_simple_engagements(
    client_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List engagements, optionally filtered by client."""
    try:
        query = (
            select(Engagement, ClientAccount)
            .join(ClientAccount, Engagement.client_account_id == ClientAccount.id)
            .where(Engagement.is_active is True)
        )

        if client_id:
            query = query.where(Engagement.client_account_id == client_id)

        result = await db.execute(query)
        engagements_with_clients = result.all()

        return {
            "status": "success",
            "data": [
                {
                    "id": str(engagement.id),
                    "name": engagement.name,
                    "description": engagement.description,
                    "client_account_id": str(engagement.client_account_id),
                    "client_name": client.name,
                    "is_active": engagement.is_active,
                    "created_at": (
                        engagement.created_at.isoformat()
                        if engagement.created_at
                        else None
                    ),
                    "updated_at": (
                        engagement.updated_at.isoformat()
                        if engagement.updated_at
                        else None
                    ),
                }
                for engagement, client in engagements_with_clients
            ],
        }

    except Exception as e:
        logger.error(f"Error listing engagements: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list engagements: {str(e)}"
        )


@simple_admin_router.get("/status")
async def get_admin_status(current_user: User = Depends(get_current_user)):
    """Get simple admin status"""
    return {
        "status": "active",
        "admin": hasattr(current_user, "is_admin") and current_user.is_admin,
        "message": "Simple admin endpoint is operational",
        "user_id": str(current_user.id),
    }
