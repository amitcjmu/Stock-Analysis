"""
Engagement Management API - Comprehensive Engagement and Session Management
Admin endpoints for managing engagements, migration planning, and session coordination.
"""

import logging
import math
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc, func

from app.core.database import get_db
from app.core.context import get_current_context
from app.core.rbac_middleware import require_admin_access
from app.schemas.admin_schemas import (
    EngagementCreate, EngagementUpdate, EngagementResponse,
    SessionCreate, SessionUpdate, SessionResponse,
    EngagementSearchFilters, SessionSearchFilters,
    EngagementDashboardStats, SessionDashboardStats,
    BulkEngagementImport, BulkOperationResponse,
    AdminPaginationParams, PaginatedResponse, AdminSuccessResponse, AdminErrorResponse
)

# Import models and services with fallback
try:
    from app.models.client_account import ClientAccount, Engagement
    from app.models.data_import_session import DataImportSession
    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = Engagement = DataImportSession = None

try:
    from app.services.session_management_service import create_session_management_service
    SESSION_SERVICE_AVAILABLE = True
except ImportError:
    SESSION_SERVICE_AVAILABLE = False
    create_session_management_service = None

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/engagements", tags=["Engagement Management"])

# =========================
# Engagement CRUD Operations
# =========================

@router.post("/", response_model=AdminSuccessResponse)
async def create_engagement(
    engagement_data: EngagementCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Create a new engagement with migration planning context.
    Requires admin privileges.
    """
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Verify client account exists
        client_query = select(ClientAccount).where(
            and_(
                ClientAccount.id == engagement_data.client_account_id,
                ClientAccount.is_active == True
            )
        )
        result = await db.execute(client_query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client account not found or inactive")
        
        # Check if engagement name already exists for this client
        existing_query = select(Engagement).where(
            and_(
                Engagement.client_account_id == engagement_data.client_account_id,
                Engagement.name == engagement_data.engagement_name
            )
        )
        result = await db.execute(existing_query)
        existing_engagement = result.scalar_one_or_none()
        
        if existing_engagement:
            raise HTTPException(
                status_code=400,
                detail=f"Engagement '{engagement_data.engagement_name}' already exists for this client"
            )
        
        # Generate slug from name
        slug = engagement_data.engagement_name.lower().replace(' ', '-').replace('_', '-')
        
        # Create new engagement
        engagement = Engagement(
            name=engagement_data.engagement_name,
            slug=slug,
            description=engagement_data.engagement_description,
            client_account_id=engagement_data.client_account_id,
            engagement_type='migration',
            status='active',
            created_by=admin_user if admin_user and admin_user != "admin_user" else None
        )
        
        db.add(engagement)
        await db.commit()
        await db.refresh(engagement)
        
        # Convert to response format
        response_data = await _convert_engagement_to_response(engagement, db)
        
        logger.info(f"Engagement created: {engagement_data.engagement_name} for client {engagement_data.client_account_id} by admin {admin_user}")
        
        return AdminSuccessResponse(
            message=f"Engagement '{engagement_data.engagement_name}' created successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating engagement: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create engagement: {str(e)}")

@router.get("/{engagement_id}", response_model=AdminSuccessResponse)
async def get_engagement(
    engagement_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get detailed engagement information."""
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Get engagement
        query = select(Engagement).where(Engagement.id == engagement_id)
        result = await db.execute(query)
        engagement = result.scalar_one_or_none()
        
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        # Convert to response format
        response_data = await _convert_engagement_to_response(engagement, db)
        
        return AdminSuccessResponse(
            message="Engagement retrieved successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve engagement: {str(e)}")

@router.put("/{engagement_id}", response_model=AdminSuccessResponse)
async def update_engagement(
    engagement_id: str,
    update_data: EngagementUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Update engagement information."""
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Get existing engagement
        query = select(Engagement).where(Engagement.id == engagement_id)
        result = await db.execute(query)
        engagement = result.scalar_one_or_none()
        
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        # Update fields that are provided
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == "migration_scope" and value:
                setattr(engagement, field, value.value)
            elif field == "target_cloud_provider" and value:
                setattr(engagement, field, value.value)
            elif field == "current_phase" and value:
                setattr(engagement, field, value.value)
            else:
                setattr(engagement, field, value)
        
        engagement.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(engagement)
        
        # Convert to response format
        response_data = await _convert_engagement_to_response(engagement, db)
        
        logger.info(f"Engagement updated: {engagement_id} by admin {admin_user}")
        
        return AdminSuccessResponse(
            message="Engagement updated successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update engagement: {str(e)}")

@router.delete("/{engagement_id}", response_model=AdminSuccessResponse)
async def delete_engagement(
    engagement_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Delete engagement (soft delete by setting is_active=False).
    Requires admin privileges and handles associated sessions.
    """
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Get engagement
        engagement_query = select(Engagement).where(Engagement.id == engagement_id)
        result = await db.execute(engagement_query)
        engagement = result.scalar_one_or_none()
        
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        # Check for active sessions
        if DataImportSession:
            sessions_query = select(func.count(DataImportSession.id)).where(
                and_(
                    DataImportSession.engagement_id == engagement_id,
                    DataImportSession.status == "active"
                )
            )
            result = await db.execute(sessions_query)
            active_sessions = result.scalar()
            
            if active_sessions > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete engagement with {active_sessions} active sessions. Please complete or archive sessions first."
                )
        
        # Soft delete (set inactive)
        engagement.is_active = False
        engagement.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Engagement deleted: {engagement_id} by admin {admin_user}")
        
        return AdminSuccessResponse(
            message=f"Engagement '{engagement.name}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete engagement: {str(e)}")

# =========================
# Engagement Search and Listing
# =========================

@router.get("/", response_model=PaginatedResponse)
async def list_engagements(
    pagination: AdminPaginationParams = Depends(),
    filters: EngagementSearchFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    List engagements with search, filtering, and pagination.
    Supports comprehensive migration planning filtering.
    """
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Build base query
        query = select(Engagement)
        
        # Apply filters
        conditions = []
        
        if filters.client_account_id:
            conditions.append(Engagement.client_account_id == filters.client_account_id)
        
        if filters.engagement_name:
            conditions.append(Engagement.name.ilike(f"%{filters.engagement_name}%"))
        
        if filters.migration_scope:
            conditions.append(Engagement.migration_scope == filters.migration_scope.value)
        
        if filters.target_cloud_provider:
            conditions.append(Engagement.target_cloud_provider == filters.target_cloud_provider.value)
        
        if filters.current_phase:
            conditions.append(Engagement.current_phase == filters.current_phase.value)
        
        if filters.engagement_manager:
            conditions.append(Engagement.engagement_manager.ilike(f"%{filters.engagement_manager}%"))
        
        if filters.planned_start_after:
            conditions.append(Engagement.planned_start_date >= filters.planned_start_after)
        
        if filters.planned_start_before:
            conditions.append(Engagement.planned_start_date <= filters.planned_start_before)
        
        if filters.is_active is not None:
            conditions.append(Engagement.is_active == filters.is_active)
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count for pagination
        count_query = select(func.count(Engagement.id)).where(and_(*conditions) if conditions else True)
        count_result = await db.execute(count_query)
        total_items = count_result.scalar()
        
        # Apply sorting
        if pagination.sort_order.lower() == "desc":
            order_by = desc(getattr(Engagement, pagination.sort_by, Engagement.created_at))
        else:
            order_by = asc(getattr(Engagement, pagination.sort_by, Engagement.created_at))
        
        query = query.order_by(order_by)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)
        
        # Execute query
        result = await db.execute(query)
        engagements = result.scalars().all()
        
        # Convert to response format
        engagement_responses = []
        for engagement in engagements:
            engagement_response = await _convert_engagement_to_response(engagement, db)
            engagement_responses.append(engagement_response)
        
        # Calculate pagination metadata
        total_pages = math.ceil(total_items / pagination.page_size)
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1
        
        return PaginatedResponse(
            items=engagement_responses,
            total_items=total_items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing engagements: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list engagements: {str(e)}")

# =========================
# Session Management (Sub-resource)
# =========================

@router.post("/{engagement_id}/sessions", response_model=AdminSuccessResponse)
async def create_session(
    engagement_id: str,
    session_data: SessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Create a new session for an engagement."""
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Session models not available")
        
        # Verify engagement exists
        engagement_query = select(Engagement).where(Engagement.id == engagement_id)
        result = await db.execute(engagement_query)
        engagement = result.scalar_one_or_none()
        
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        if SESSION_SERVICE_AVAILABLE:
            # Use session management service
            session_service = create_session_management_service(db)
            
            # Prepare session data
            session_creation_data = {
                "engagement_id": engagement_id,
                "session_name": session_data.session_name,
                "session_description": session_data.session_description,
                "session_type": session_data.session_type,
                "import_preferences": session_data.import_preferences,
                "agent_settings": session_data.agent_settings
            }
            
            result = await session_service.create_session(session_creation_data)
            
            if result["status"] == "error":
                raise HTTPException(status_code=400, detail=result["message"])
            
            session_id = result["session_id"]
            
            # Get the created session for response
            session_query = select(DataImportSession).where(DataImportSession.id == session_id)
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()
            
            response_data = await _convert_session_to_response(session)
            
        else:
            # Fallback direct creation
            if not DataImportSession:
                raise HTTPException(status_code=503, detail="Session models not available")
            
            # Generate session name if not provided
            session_name = session_data.session_name
            if not session_name:
                session_name = f"{engagement.engagement_name}-session-{datetime.utcnow().strftime('%Y%m%d-%H%M')}"
            
            session = DataImportSession(
                session_name=session_name,
                session_description=session_data.session_description,
                engagement_id=engagement_id,
                session_type=session_data.session_type,
                import_preferences=session_data.import_preferences,
                agent_settings=session_data.agent_settings
            )
            
            db.add(session)
            await db.commit()
            await db.refresh(session)
            
            response_data = await _convert_session_to_response(session)
        
        logger.info(f"Session created: {session_data.session_name or 'auto-generated'} for engagement {engagement_id} by admin {admin_user}")
        
        return AdminSuccessResponse(
            message="Session created successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/{engagement_id}/sessions", response_model=PaginatedResponse)
async def list_engagement_sessions(
    engagement_id: str,
    pagination: AdminPaginationParams = Depends(),
    filters: SessionSearchFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """List sessions for a specific engagement."""
    try:
        if not CLIENT_MODELS_AVAILABLE or not DataImportSession:
            raise HTTPException(status_code=503, detail="Session models not available")
        
        # Build base query
        query = select(DataImportSession).where(DataImportSession.engagement_id == engagement_id)
        
        # Apply filters
        conditions = [DataImportSession.engagement_id == engagement_id]
        
        if filters.session_type:
            conditions.append(DataImportSession.session_type == filters.session_type)
        
        if filters.status:
            conditions.append(DataImportSession.status == filters.status)
        
        if filters.created_after:
            conditions.append(DataImportSession.created_at >= filters.created_after)
        
        if filters.created_before:
            conditions.append(DataImportSession.created_at <= filters.created_before)
        
        # Apply all conditions
        query = query.where(and_(*conditions))
        
        # Get total count for pagination
        count_query = select(func.count(DataImportSession.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total_items = count_result.scalar()
        
        # Apply sorting
        if pagination.sort_order.lower() == "desc":
            order_by = desc(getattr(DataImportSession, pagination.sort_by, DataImportSession.created_at))
        else:
            order_by = asc(getattr(DataImportSession, pagination.sort_by, DataImportSession.created_at))
        
        query = query.order_by(order_by)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)
        
        # Execute query
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        # Convert to response format
        session_responses = []
        for session in sessions:
            session_response = await _convert_session_to_response(session)
            session_responses.append(session_response)
        
        # Calculate pagination metadata
        total_pages = math.ceil(total_items / pagination.page_size)
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1
        
        return PaginatedResponse(
            items=session_responses,
            total_items=total_items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sessions for engagement {engagement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

# =========================
# Dashboard and Analytics
# =========================

@router.get("/dashboard/stats", response_model=EngagementDashboardStats)
async def get_engagement_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get engagement dashboard statistics and analytics."""
    try:
        if not CLIENT_MODELS_AVAILABLE:
            return EngagementDashboardStats(
                total_engagements=0,
                active_engagements=0,
                engagements_by_phase={},
                engagements_by_scope={},
                completion_rate_average=0.0,
                budget_utilization_average=0.0,
                recent_engagement_activity=[]
            )
        
        # Total and active engagements
        total_query = select(func.count(Engagement.id))
        total_result = await db.execute(total_query)
        total_engagements = total_result.scalar()
        
        active_query = select(func.count(Engagement.id)).where(Engagement.is_active == True)
        active_result = await db.execute(active_query)
        active_engagements = active_result.scalar()
        
        # Engagements by phase (using status field)
        phase_query = select(
            Engagement.status,
            func.count(Engagement.id).label('count')
        ).where(Engagement.is_active == True).group_by(Engagement.status)
        phase_result = await db.execute(phase_query)
        engagements_by_phase = {row.status: row.count for row in phase_result}
        
        # Engagements by scope (simplified - return demo data)
        engagements_by_scope = {
            'migration': 3,
            'modernization': 2,
            'assessment': 1
        }
        
        # Average completion rate (simplified - return demo data)
        completion_rate_average = 65.5
        
        # Budget utilization (simplified calculation)
        budget_utilization_average = 65.5  # Demo value
        
        # Recent activity (last 10)
        recent_query = select(Engagement).where(
            Engagement.is_active == True
        ).order_by(desc(Engagement.updated_at)).limit(10)
        recent_result = await db.execute(recent_query)
        recent_engagements = recent_result.scalars().all()
        
        # Convert recent engagements to response format
        recent_engagement_responses = []
        for engagement in recent_engagements:
            engagement_response = await _convert_engagement_to_response(engagement, db)
            recent_engagement_responses.append(engagement_response)
        
        return EngagementDashboardStats(
            total_engagements=total_engagements,
            active_engagements=active_engagements,
            engagements_by_phase=engagements_by_phase,
            engagements_by_scope=engagements_by_scope,
            completion_rate_average=completion_rate_average,
            budget_utilization_average=budget_utilization_average,
            recent_engagement_activity=recent_engagement_responses
        )
        
    except Exception as e:
        logger.error(f"Error getting engagement dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

# =========================
# Utility Functions
# =========================

async def _convert_engagement_to_response(engagement: Engagement, db: AsyncSession) -> EngagementResponse:
    """Convert Engagement model to response format with additional statistics."""
    
    # Get session and asset counts
    total_sessions = 0
    total_assets = 0
    
    if DataImportSession:
        sessions_query = select(func.count(DataImportSession.id)).where(
            DataImportSession.engagement_id == engagement.id
        )
        sessions_result = await db.execute(sessions_query)
        total_sessions = sessions_result.scalar() or 0
        
        # Assets would be counted from CMDB or other asset tables
        # This is a placeholder for now
        total_assets = 0
    
    return EngagementResponse(
        id=str(engagement.id),
        engagement_name=engagement.name,
        client_account_id=str(engagement.client_account_id),
        engagement_description=engagement.description or '',
        migration_scope='migration',  # Default value
        target_cloud_provider='aws',  # Default value
        planned_start_date=engagement.start_date,
        planned_end_date=engagement.target_completion_date,
        estimated_budget=0.0,  # Field not in model
        estimated_asset_count=0,  # Field not in model
        actual_start_date=engagement.start_date,
        actual_end_date=engagement.actual_completion_date,
        actual_budget=0.0,  # Field not in model
        engagement_manager='',  # Field not in model
        technical_lead='',  # Field not in model
        team_preferences=engagement.team_preferences or {},
        agent_configuration={},  # Field not in model
        discovery_preferences={},  # Field not in model
        assessment_criteria={},  # Field not in model
        current_phase=engagement.status,
        completion_percentage=0.0,  # Field not in model
        current_session_id=str(engagement.current_session_id) if engagement.current_session_id else None,
        created_at=engagement.created_at,
        updated_at=engagement.updated_at,
        is_active=engagement.is_active,
        total_sessions=total_sessions,
        total_assets=total_assets
    )

async def _convert_session_to_response(session: DataImportSession) -> SessionResponse:
    """Convert DataImportSession model to response format."""
    
    return SessionResponse(
        id=str(session.id),
        engagement_id=str(session.engagement_id),
        session_name=session.session_name,
        session_description=session.session_description,
        session_type=session.session_type,
        status=session.status,
        import_preferences=session.import_preferences or {},
        agent_settings=session.agent_settings or {},
        completion_percentage=session.completion_percentage or 0.0,
        total_records_processed=session.total_records_processed or 0,
        total_assets_discovered=session.total_assets_discovered or 0,
        total_errors=session.total_errors or 0,
        error_details=session.error_details,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at
    )

# =========================
# Health Check
# =========================

@router.get("/health")
async def engagement_management_health():
    """Health check for engagement management service."""
    return {
        "status": "healthy",
        "service": "engagement-management",
        "version": "1.0.0",
        "capabilities": {
            "engagement_crud": True,
            "migration_planning": True,
            "session_management": True,
            "search_filtering": True,
            "dashboard_analytics": True,
            "client_models_available": CLIENT_MODELS_AVAILABLE,
            "session_service_available": SESSION_SERVICE_AVAILABLE
        }
    } 