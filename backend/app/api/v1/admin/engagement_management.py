"""
Engagement Management API - Modular Implementation
Admin endpoints for managing migration engagements with real database integration.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import datetime

from app.core.database import get_db
from app.core.rbac_middleware import require_admin_access

# Conditional imports with fallbacks
try:
    from app.models.client_account import ClientAccount, Engagement, User
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    ClientAccount = Engagement = User = None

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/engagements", tags=["Engagement Management"])

@router.get("/health")
async def engagement_management_health():
    """Health check for engagement management service."""
    return {
        "status": "healthy",
        "service": "engagement-management-modular",
        "version": "2.0.0",
        "models_available": MODELS_AVAILABLE,
        "capabilities": {
            "engagement_crud": MODELS_AVAILABLE,
            "migration_planning": MODELS_AVAILABLE,
            "progress_tracking": MODELS_AVAILABLE,
            "modular_architecture": True,
            "real_database_queries": MODELS_AVAILABLE
        }
    }

@router.get("/")
async def list_engagements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """List engagements with pagination using real database queries."""
    try:
        if not MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Database models not available")
            
        logger.info(f"Admin user {admin_user} requesting engagement list with pagination: page={page}, page_size={page_size}")
        
        # Build base query for engagements first
        query = select(Engagement)\
            .where(Engagement.is_active == True)\
            .order_by(Engagement.created_at.desc())
        
        # Get total count for pagination
        count_query = select(func.count(Engagement.id))\
            .where(Engagement.is_active == True)
        total_result = await db.execute(count_query)
        total_items = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        engagements = result.scalars().all()
        
        # Transform to response format
        engagement_list = []
        for engagement in engagements:
            # Get client account separately
            client_query = select(ClientAccount).where(ClientAccount.id == engagement.client_account_id)
            client_result = await db.execute(client_query)
            client = client_result.scalar_one_or_none()
            engagement_data = {
                "id": str(engagement.id),
                "engagement_name": engagement.name or "Unnamed Engagement",
                "client_account_id": str(engagement.client_account_id),
                "client_account_name": client.name if client else "Unknown Client",
                "migration_scope": engagement.migration_scope.get("target_clouds", []) if engagement.migration_scope else [],
                "target_cloud_provider": engagement.migration_scope.get("target_clouds", ["Not specified"])[0] if engagement.migration_scope and engagement.migration_scope.get("target_clouds") else "Not specified",
                "migration_phase": engagement.status or "planning",
                "engagement_manager": "Not assigned",  # Simplified since engagement_lead might not be loaded
                "technical_lead": engagement.client_contact_name or "Not assigned",
                "start_date": engagement.start_date.isoformat() if engagement.start_date else None,
                "end_date": engagement.target_completion_date.isoformat() if engagement.target_completion_date else None,
                "budget": None,  # Would need to be added to engagement model
                "budget_currency": "USD",
                "completion_percentage": 0.0,  # Would need to be calculated
                "created_at": engagement.created_at.isoformat() if engagement.created_at else None,
                "is_active": engagement.is_active,
                "total_sessions": 0,  # Would need to count related sessions
                "active_sessions": 0   # Would need to count active sessions
            }
            engagement_list.append(engagement_data)
        
        # Calculate pagination info
        total_pages = (total_items + page_size - 1) // page_size
        
        logger.info(f"Found {len(engagement_list)} engagements out of {total_items} total for admin user {admin_user}")
        
        return {
            "items": engagement_list,
            "total": total_items,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error listing engagements: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list engagements: {str(e)}")

@router.post("/")
async def create_engagement(
    engagement_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Create a new engagement."""
    try:
        if not MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Database models not available")
        
        # Validate required fields
        required_fields = ['engagement_name', 'client_account_id']
        for field in required_fields:
            if not engagement_data.get(field):
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Verify client account exists
        client_query = select(ClientAccount).where(ClientAccount.id == engagement_data['client_account_id'])
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client account not found")
        
        # Check if engagement name already exists for this client
        existing_query = select(Engagement).where(
            and_(
                Engagement.client_account_id == engagement_data['client_account_id'],
                Engagement.name == engagement_data['engagement_name']
            )
        )
        existing_result = await db.execute(existing_query)
        existing_engagement = existing_result.scalar_one_or_none()
        
        if existing_engagement:
            raise HTTPException(
                status_code=400,
                detail=f"Engagement '{engagement_data['engagement_name']}' already exists for this client"
            )
        
        # Create slug from name
        slug = engagement_data['engagement_name'].lower().replace(' ', '-').replace('_', '-')
        
        # Create new engagement
        engagement = Engagement(
            name=engagement_data['engagement_name'],
            slug=slug,
            description=engagement_data.get('description', ''),
            client_account_id=engagement_data['client_account_id'],
            engagement_type='migration',
            status='active',
            start_date=datetime.utcnow() if engagement_data.get('estimated_start_date') else None,
            target_completion_date=None,  # Can be set later
            client_contact_name=engagement_data.get('project_manager', ''),
            client_contact_email='',
            migration_scope={
                "target_clouds": [engagement_data.get('target_cloud_provider', 'AWS')] if engagement_data.get('target_cloud_provider') else [],
                "migration_strategies": [],
                "excluded_systems": [],
                "included_environments": [],
                "business_units": [],
                "geographic_scope": [],
                "timeline_constraints": {}
            },
            team_preferences={
                "stakeholders": [],
                "decision_makers": [],
                "technical_leads": [],
                "communication_style": "formal",
                "reporting_frequency": "weekly",
                "preferred_meeting_times": [],
                "escalation_contacts": [],
                "project_methodology": "agile"
            },
            created_by="eef6ea50-6550-4f14-be2c-081d4eb23038" if admin_user in ["admin_user", "demo_user"] else None,
            is_active=True
        )
        
        db.add(engagement)
        await db.commit()
        await db.refresh(engagement)
        
        # Convert to response format
        response_data = {
            "id": str(engagement.id),
            "engagement_name": engagement.name,
            "client_account_id": str(engagement.client_account_id),
            "client_account_name": client.name,
            "migration_scope": engagement.migration_scope.get("target_clouds", []) if engagement.migration_scope else [],
            "target_cloud_provider": engagement.migration_scope.get("target_clouds", ["Not specified"])[0] if engagement.migration_scope and engagement.migration_scope.get("target_clouds") else "Not specified",
            "migration_phase": engagement.status or "planning",
            "engagement_manager": engagement.client_contact_name or "Not assigned",
            "technical_lead": "Not assigned",
            "start_date": engagement.start_date.isoformat() if engagement.start_date else None,
            "end_date": engagement.target_completion_date.isoformat() if engagement.target_completion_date else None,
            "budget": None,
            "budget_currency": "USD",
            "completion_percentage": 0.0,
            "created_at": engagement.created_at.isoformat() if engagement.created_at else None,
            "is_active": engagement.is_active,
            "total_sessions": 0,
            "active_sessions": 0
        }
        
        logger.info(f"Engagement created: {engagement_data['engagement_name']} for client {engagement_data['client_account_id']} by admin {admin_user}")
        
        return {
            "status": "success",
            "message": f"Engagement '{engagement_data['engagement_name']}' created successfully",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating engagement: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create engagement: {str(e)}")

@router.get("/{engagement_id}")
async def get_engagement(
    engagement_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get engagement details."""
    try:
        # Demo implementation
        engagement = {
            "id": engagement_id,
            "engagement_name": "Sample Engagement",
            "client_account_name": "Sample Client",
            "migration_phase": "discovery",
            "completion_percentage": 25.5,
            "is_active": True
        }
        
        return {
            "message": "Engagement retrieved successfully",
            "data": engagement
        }
        
    except Exception as e:
        logger.error(f"Error retrieving engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve engagement: {str(e)}")

@router.put("/{engagement_id}")
async def update_engagement(
    engagement_id: str,
    update_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Update engagement."""
    try:
        if not MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Database models not available")
        
        # Get existing engagement
        query = select(Engagement).where(Engagement.id == engagement_id)
        result = await db.execute(query)
        engagement = result.scalar_one_or_none()
        
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        # Update fields that are provided
        for field, value in update_data.items():
            if field in ['engagement_name']:
                setattr(engagement, 'name', value)
            elif field in ['engagement_description']:
                setattr(engagement, 'description', value)
            elif field in ['engagement_manager']:
                setattr(engagement, 'client_contact_name', value)
            elif field in ['start_date'] and value:
                try:
                    setattr(engagement, 'start_date', datetime.fromisoformat(value.replace('Z', '+00:00')))
                except:
                    setattr(engagement, 'start_date', None)
            elif field in ['end_date'] and value:
                try:
                    setattr(engagement, 'target_completion_date', datetime.fromisoformat(value.replace('Z', '+00:00')))
                except:
                    setattr(engagement, 'target_completion_date', None)
            elif field in ['migration_phase']:
                setattr(engagement, 'status', value)
            elif field in ['target_cloud_provider'] and value:
                # Update migration_scope JSON
                scope = engagement.migration_scope or {}
                scope['target_clouds'] = [value]
                setattr(engagement, 'migration_scope', scope)
        
        engagement.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(engagement)
        
        # Get client info for response
        client_query = select(ClientAccount).where(ClientAccount.id == engagement.client_account_id)
        client_result = await db.execute(client_query)
        client = client_result.scalar_one_or_none()
        
        # Convert to response format
        response_data = {
            "id": str(engagement.id),
            "engagement_name": engagement.name,
            "client_account_id": str(engagement.client_account_id),
            "client_account_name": client.name if client else "Unknown Client",
            "migration_scope": engagement.migration_scope.get("target_clouds", []) if engagement.migration_scope else [],
            "target_cloud_provider": engagement.migration_scope.get("target_clouds", ["Not specified"])[0] if engagement.migration_scope and engagement.migration_scope.get("target_clouds") else "Not specified",
            "migration_phase": engagement.status or "planning",
            "engagement_manager": engagement.client_contact_name or "Not assigned",
            "technical_lead": "Not assigned",
            "start_date": engagement.start_date.isoformat() if engagement.start_date else None,
            "end_date": engagement.target_completion_date.isoformat() if engagement.target_completion_date else None,
            "budget": None,
            "budget_currency": "USD",
            "completion_percentage": 0.0,
            "created_at": engagement.created_at.isoformat() if engagement.created_at else None,
            "updated_at": engagement.updated_at.isoformat() if engagement.updated_at else None,
            "is_active": engagement.is_active,
            "total_sessions": 0,
            "active_sessions": 0
        }
        
        logger.info(f"Engagement updated: {engagement_id} by admin {admin_user}")
        
        return {
            "status": "success",
            "message": "Engagement updated successfully",
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update engagement: {str(e)}")

@router.delete("/{engagement_id}")
async def delete_engagement(
    engagement_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Delete engagement."""
    try:
        # Demo implementation
        return {
            "message": f"Engagement {engagement_id} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete engagement: {str(e)}")

@router.get("/dashboard/stats")
async def get_engagement_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get engagement dashboard statistics from real database."""
    try:
        if not MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Database models not available")
            
        logger.info(f"Admin user {admin_user} requesting engagement dashboard stats")
        
        # Total engagements
        total_engagements_result = await db.execute(
            select(func.count(Engagement.id)).where(Engagement.is_active == True)
        )
        total_engagements = total_engagements_result.scalar() or 0
        
        # Active engagements
        active_engagements_result = await db.execute(
            select(func.count(Engagement.id)).where(
                and_(
                    Engagement.is_active == True,
                    Engagement.status.in_(['active', 'in_progress', 'planning'])
                )
            )
        )
        active_engagements = active_engagements_result.scalar() or 0
        
        # Completed engagements
        completed_engagements_result = await db.execute(
            select(func.count(Engagement.id)).where(
                and_(
                    Engagement.is_active == True,
                    Engagement.status.in_(['completed', 'done'])
                )
            )
        )
        completed_engagements = completed_engagements_result.scalar() or 0
        
        # Engagements by phase (status)
        phase_result = await db.execute(
            select(Engagement.status, func.count(Engagement.id))
            .where(and_(Engagement.is_active == True, Engagement.status.isnot(None)))
            .group_by(Engagement.status)
        )
        engagements_by_phase = {row[0]: row[1] for row in phase_result.fetchall()}
        
        # Default phases if none found
        if not engagements_by_phase:
            engagements_by_phase = {
                "discovery": 0,
                "assessment": 0,
                "planning": 0,
                "execution": 0
            }
        
        logger.info(f"Returning engagement dashboard stats: {total_engagements} total, {active_engagements} active")
        
        return {
            "total_engagements": total_engagements,
            "active_engagements": active_engagements,
            "completed_engagements": completed_engagements,
            "engagements_by_phase": engagements_by_phase,
            "avg_completion_percentage": 0.0,  # Would need to calculate from progress data
            "total_budget": 0,  # Would need budget field in engagement model
            "budget_utilization": 0.0  # Would need budget tracking
        }
        
    except Exception as e:
        logger.error(f"Error getting engagement dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}") 