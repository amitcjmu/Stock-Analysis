"""
Client CRUD Handler - Core client account operations
"""

import logging
from typing import Dict, Any
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.schemas.admin_schemas import (
    ClientAccountCreate, ClientAccountUpdate, ClientAccountResponse,
    AdminSuccessResponse
)

# Import models with fallback
try:
    from app.models.client_account import ClientAccount, Engagement
    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = None

logger = logging.getLogger(__name__)

class ClientCRUDHandler:
    """Handler for client CRUD operations"""
    
    @staticmethod
    async def create_client(
        client_data: ClientAccountCreate,
        db: AsyncSession,
        admin_user: str
    ) -> AdminSuccessResponse:
        """Create a new client account"""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(status_code=503, detail="Client models not available")
            
            # Check if client already exists
            existing_query = select(ClientAccount).where(
                ClientAccount.name == client_data.account_name
            )
            result = await db.execute(existing_query)
            existing_client = result.scalar_one_or_none()
            
            if existing_client:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Client account '{client_data.account_name}' already exists"
                )
            
            # Create new client account
            client = ClientAccount(
                name=client_data.account_name,
                slug=client_data.account_name.lower().replace(' ', '-').replace('&', 'and'),
                industry=client_data.industry,
                company_size=client_data.company_size,
                headquarters_location=client_data.headquarters_location,
                primary_contact_name=client_data.primary_contact_name,
                primary_contact_email=client_data.primary_contact_email,
                primary_contact_phone=client_data.primary_contact_phone,
                description=client_data.description,
                subscription_tier=client_data.subscription_tier,
                billing_contact_email=client_data.billing_contact_email,
                settings=client_data.settings or {},
                branding=client_data.branding or {},
                business_objectives={
                    "primary_goals": client_data.business_objectives,
                    "compliance_requirements": client_data.compliance_requirements
                },
                it_guidelines=client_data.it_guidelines or {},
                decision_criteria=client_data.decision_criteria or {},
                agent_preferences=client_data.agent_preferences or {}
            )
            
            db.add(client)
            await db.commit()
            await db.refresh(client)
            
            # Convert to response format
            response_data = await ClientCRUDHandler._convert_client_to_response(client, db)
            
            logger.info(f"Client account created: {client_data.account_name} by admin {admin_user}")
            
            return AdminSuccessResponse(
                message=f"Client account '{client_data.account_name}' created successfully",
                data=response_data
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating client account: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create client account: {str(e)}")

    @staticmethod
    async def get_client(client_id: str, db: AsyncSession) -> AdminSuccessResponse:
        """Get client account by ID"""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(status_code=503, detail="Client models not available")
            
            query = select(ClientAccount).where(ClientAccount.id == client_id)
            result = await db.execute(query)
            client = result.scalar_one_or_none()
            
            if not client:
                raise HTTPException(status_code=404, detail="Client account not found")
            
            response_data = await ClientCRUDHandler._convert_client_to_response(client, db)
            
            return AdminSuccessResponse(
                message="Client account retrieved successfully",
                data=response_data
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving client account {client_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve client account: {str(e)}")

    @staticmethod
    async def update_client(
        client_id: str,
        update_data: ClientAccountUpdate,
        db: AsyncSession,
        admin_user: str
    ) -> AdminSuccessResponse:
        """Update client account"""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(status_code=503, detail="Client models not available")
            
            query = select(ClientAccount).where(ClientAccount.id == client_id)
            result = await db.execute(query)
            client = result.scalar_one_or_none()
            
            if not client:
                raise HTTPException(status_code=404, detail="Client account not found")
            
            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                if hasattr(client, field):
                    setattr(client, field, value)
            
            await db.commit()
            await db.refresh(client)
            
            response_data = await ClientCRUDHandler._convert_client_to_response(client, db)
            
            logger.info(f"Client account updated: {client_id} by admin {admin_user}")
            
            return AdminSuccessResponse(
                message="Client account updated successfully",
                data=response_data
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating client account {client_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update client account: {str(e)}")

    @staticmethod
    async def delete_client(
        client_id: str,
        db: AsyncSession,
        admin_user: str
    ) -> AdminSuccessResponse:
        """Delete client account"""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(status_code=503, detail="Client models not available")
            
            query = select(ClientAccount).where(ClientAccount.id == client_id)
            result = await db.execute(query)
            client = result.scalar_one_or_none()
            
            if not client:
                raise HTTPException(status_code=404, detail="Client account not found")
            
            client_name = client.name
            await db.delete(client)
            await db.commit()
            
            logger.info(f"Client account deleted: {client_name} by admin {admin_user}")
            
            return AdminSuccessResponse(
                message=f"Client account '{client_name}' deleted successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting client account {client_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete client account: {str(e)}")

    @staticmethod
    async def list_clients(
        db: AsyncSession,
        pagination: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """List all client accounts with pagination and filtering."""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(status_code=503, detail="Client models not available")

            query = select(ClientAccount)
            
            # Apply filters (example)
            if filters.get('is_active') is not None:
                query = query.where(ClientAccount.is_active == filters['is_active'])
            if filters.get('account_name'):
                query = query.where(ClientAccount.name.ilike(f"%{filters['account_name']}%"))

            # Get total items for pagination
            total_items_query = select(func.count()).select_from(query.alias())
            total_items_result = await db.execute(total_items_query)
            total_items = total_items_result.scalar_one()

            # Apply pagination
            page = pagination.get('page', 1)
            page_size = pagination.get('page_size', 20)
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # Execute query
            result = await db.execute(query)
            clients = result.scalars().all()

            # Convert to response format
            client_responses = [await ClientCRUDHandler._convert_client_to_response(c, db) for c in clients]
            
            total_pages = (total_items + page_size - 1) // page_size
            
            return {
                "items": client_responses,
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }

        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            return {"error": "Failed to list client accounts"}

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard statistics for client accounts."""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(status_code=503, detail="Client models not available")

            # Total clients
            total_clients_query = select(func.count()).select_from(ClientAccount)
            total_clients_result = await db.execute(total_clients_query)
            total_clients = total_clients_result.scalar_one()

            # Active clients
            active_clients_query = select(func.count()).select_from(ClientAccount).where(ClientAccount.is_active == True)
            active_clients_result = await db.execute(active_clients_query)
            active_clients = active_clients_result.scalar_one()

            # Clients by industry
            industry_query = select(ClientAccount.industry, func.count()).group_by(ClientAccount.industry)
            industry_result = await db.execute(industry_query)
            clients_by_industry = {row[0]: row[1] for row in industry_result.all() if row[0]}

            # Clients by company size
            size_query = select(ClientAccount.company_size, func.count()).group_by(ClientAccount.company_size)
            size_result = await db.execute(size_query)
            clients_by_company_size = {row[0]: row[1] for row in size_result.all() if row[0]}
            
            # Recent client registrations (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_clients_query = select(ClientAccount).where(ClientAccount.created_at >= seven_days_ago).order_by(ClientAccount.created_at.desc()).limit(5)
            recent_clients_result = await db.execute(recent_clients_query)
            recent_clients = recent_clients_result.scalars().all()
            
            recent_client_responses = [ClientAccountResponse.model_validate(c, from_attributes=True) for c in recent_clients]

            return {
                "total_clients": total_clients,
                "active_clients": active_clients,
                "clients_by_industry": dict(clients_by_industry),
                "clients_by_company_size": dict(clients_by_company_size),
                "clients_by_cloud_provider": {}, # Placeholder
                "recent_client_registrations": recent_client_responses
            }
        except Exception as e:
            logger.error(f"Error getting client dashboard stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve dashboard stats")

    @staticmethod
    async def _convert_client_to_response(client: Any, db: AsyncSession) -> Dict[str, Any]:
        """Convert client model to response format"""
        if not CLIENT_MODELS_AVAILABLE or not client:
            return {}
        
        # Count engagements
        total_engagements_query = select(func.count()).select_from(Engagement).where(Engagement.client_account_id == client.id)
        total_engagements_result = await db.execute(total_engagements_query)
        total_engagements = total_engagements_result.scalar_one()

        active_engagements_query = select(func.count()).select_from(Engagement).where(
            Engagement.client_account_id == client.id,
            Engagement.is_active == True
        )
        active_engagements_result = await db.execute(active_engagements_query)
        active_engagements = active_engagements_result.scalar_one()
        
        business_objectives = client.business_objectives or {}

        return {
            "id": str(client.id),
            "account_name": client.name,
            "industry": client.industry,
            "company_size": client.company_size,
            "headquarters_location": client.headquarters_location,
            "primary_contact_name": client.primary_contact_name,
            "primary_contact_email": client.primary_contact_email,
            "primary_contact_phone": client.primary_contact_phone,
            "description": client.description,
            "subscription_tier": client.subscription_tier,
            "created_at": client.created_at,
            "updated_at": client.updated_at,
            "is_active": getattr(client, 'is_active', True),
            "total_engagements": total_engagements,
            "active_engagements": active_engagements,
            "business_objectives": business_objectives.get("primary_goals", []),
            "target_cloud_providers": business_objectives.get("target_cloud_providers", []),
            "business_priorities": business_objectives.get("business_priorities", []),
            "compliance_requirements": business_objectives.get("compliance_requirements", [])
        } 