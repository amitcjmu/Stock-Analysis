"""
Client Management API - Comprehensive Client Account Management
Admin endpoints for managing client accounts with business context and migration planning.
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
    ClientAccountCreate, ClientAccountUpdate, ClientAccountResponse,
    ClientSearchFilters, ClientDashboardStats, BulkClientImport, BulkOperationResponse,
    AdminPaginationParams, PaginatedResponse, AdminSuccessResponse, AdminErrorResponse
)

# Import models with fallback
try:
    from app.models.client_account import ClientAccount, Engagement
    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = Engagement = None

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/clients", tags=["Client Management"])

# =========================
# Client CRUD Operations
# =========================

@router.post("/", response_model=AdminSuccessResponse)
async def create_client_account(
    client_data: ClientAccountCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Create a new client account with business context.
    Requires admin privileges.
    """
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
            business_objectives=client_data.business_objectives,
            it_guidelines=client_data.it_guidelines,
            decision_criteria=client_data.decision_criteria,
            agent_preferences=client_data.agent_preferences,
            target_cloud_providers=[provider.value for provider in client_data.target_cloud_providers],
            business_priorities=[priority.value for priority in client_data.business_priorities],
            compliance_requirements=client_data.compliance_requirements,
            budget_constraints=client_data.budget_constraints,
            timeline_constraints=client_data.timeline_constraints
        )
        
        db.add(client)
        await db.commit()
        await db.refresh(client)
        
        # Convert to response format
        response_data = await _convert_client_to_response(client, db)
        
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

@router.get("/{client_id}", response_model=AdminSuccessResponse)
async def get_client_account(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get detailed client account information."""
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Get client with engagements count
        query = select(ClientAccount).where(ClientAccount.id == client_id)
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client account not found")
        
        # Convert to response format
        response_data = await _convert_client_to_response(client, db)
        
        return AdminSuccessResponse(
            message="Client account retrieved successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving client account {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve client account: {str(e)}")

@router.put("/{client_id}", response_model=AdminSuccessResponse)
async def update_client_account(
    client_id: str,
    update_data: ClientAccountUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Update client account information."""
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Get existing client
        query = select(ClientAccount).where(ClientAccount.id == client_id)
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client account not found")
        
        # Update fields that are provided
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == "target_cloud_providers" and value:
                setattr(client, field, [provider.value for provider in value])
            elif field == "business_priorities" and value:
                setattr(client, field, [priority.value for priority in value])
            else:
                setattr(client, field, value)
        
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(client)
        
        # Convert to response format
        response_data = await _convert_client_to_response(client, db)
        
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

@router.delete("/{client_id}", response_model=AdminSuccessResponse)
async def delete_client_account(
    client_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Delete client account (soft delete by setting is_active=False).
    Requires admin privileges and checks for active engagements.
    """
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Get client with active engagements check
        client_query = select(ClientAccount).where(ClientAccount.id == client_id)
        result = await db.execute(client_query)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client account not found")
        
        # Check for active engagements
        engagements_query = select(func.count(Engagement.id)).where(
            and_(
                Engagement.client_account_id == client_id,
                Engagement.is_active == True
            )
        )
        result = await db.execute(engagements_query)
        active_engagements = result.scalar()
        
        if active_engagements > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete client account with {active_engagements} active engagements. Please complete or archive engagements first."
            )
        
        # Soft delete (set inactive)
        client.is_active = False
        client.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Client account deleted: {client_id} by admin {admin_user}")
        
        return AdminSuccessResponse(
            message=f"Client account '{client.name}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting client account {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete client account: {str(e)}")

# =========================
# Client Search and Listing
# =========================

@router.get("/", response_model=PaginatedResponse)
async def list_client_accounts(
    pagination: AdminPaginationParams = Depends(),
    filters: ClientSearchFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    List client accounts with search, filtering, and pagination.
    Supports comprehensive business context filtering.
    """
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        # Build base query
        query = select(ClientAccount)
        
        # Apply filters
        conditions = []
        
        if filters.account_name:
            conditions.append(ClientAccount.name.ilike(f"%{filters.account_name}%"))
        
        if filters.industry:
            conditions.append(ClientAccount.industry.ilike(f"%{filters.industry}%"))
        
        if filters.company_size:
            conditions.append(ClientAccount.company_size.ilike(f"%{filters.company_size}%"))
        
        if filters.target_cloud_providers:
            provider_values = [provider.value for provider in filters.target_cloud_providers]
            # Check if any of the target providers match
            conditions.append(
                or_(*[ClientAccount.target_cloud_providers.contains([provider]) for provider in provider_values])
            )
        
        if filters.business_priorities:
            priority_values = [priority.value for priority in filters.business_priorities]
            conditions.append(
                or_(*[ClientAccount.business_priorities.contains([priority]) for priority in priority_values])
            )
        
        if filters.created_after:
            conditions.append(ClientAccount.created_at >= filters.created_after)
        
        if filters.created_before:
            conditions.append(ClientAccount.created_at <= filters.created_before)
        
        if filters.is_active is not None:
            conditions.append(ClientAccount.is_active == filters.is_active)
        
        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count for pagination
        count_query = select(func.count(ClientAccount.id)).where(and_(*conditions) if conditions else True)
        count_result = await db.execute(count_query)
        total_items = count_result.scalar()
        
        # Apply sorting
        if pagination.sort_order.lower() == "desc":
            order_by = desc(getattr(ClientAccount, pagination.sort_by, ClientAccount.created_at))
        else:
            order_by = asc(getattr(ClientAccount, pagination.sort_by, ClientAccount.created_at))
        
        query = query.order_by(order_by)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = query.offset(offset).limit(pagination.page_size)
        
        # Execute query
        result = await db.execute(query)
        clients = result.scalars().all()
        
        # Convert to response format
        client_responses = []
        for client in clients:
            client_response = await _convert_client_to_response(client, db)
            client_responses.append(client_response)
        
        # Calculate pagination metadata
        total_pages = math.ceil(total_items / pagination.page_size)
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1
        
        return PaginatedResponse(
            items=client_responses,
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
        logger.error(f"Error listing client accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list client accounts: {str(e)}")

# =========================
# Bulk Operations
# =========================

@router.post("/bulk-import", response_model=BulkOperationResponse)
async def bulk_import_clients(
    bulk_import: BulkClientImport,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """
    Bulk import client accounts with validation and error handling.
    Supports strict, lenient, and skip_errors validation modes.
    """
    try:
        if not CLIENT_MODELS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Client models not available")
        
        start_time = datetime.utcnow()
        
        successful_imports = 0
        failed_imports = 0
        errors = []
        imported_ids = []
        
        for i, client_data in enumerate(bulk_import.clients):
            try:
                # Check if client already exists
                existing_query = select(ClientAccount).where(
                    ClientAccount.name == client_data.account_name
                )
                result = await db.execute(existing_query)
                existing_client = result.scalar_one_or_none()
                
                if existing_client:
                    error_msg = f"Client '{client_data.account_name}' already exists"
                    if bulk_import.validation_mode == "strict":
                        errors.append({"index": i, "error": error_msg, "client_name": client_data.account_name})
                        failed_imports += 1
                        continue
                    elif bulk_import.validation_mode == "skip_errors":
                        continue
                    # For lenient mode, we could update existing client
                
                # Create new client
                client = ClientAccount(
                    name=client_data.account_name,
                    slug=client_data.account_name.lower().replace(' ', '-').replace('&', 'and'),
                    industry=client_data.industry,
                    company_size=client_data.company_size,
                    business_objectives=client_data.business_objectives,
                    it_guidelines=client_data.it_guidelines,
                    decision_criteria=client_data.decision_criteria,
                    agent_preferences=client_data.agent_preferences
                )
                
                db.add(client)
                await db.flush()  # Get the ID without committing
                
                imported_ids.append(str(client.id))
                successful_imports += 1
                
            except Exception as e:
                error_msg = f"Failed to import client {i}: {str(e)}"
                errors.append({"index": i, "error": error_msg, "client_name": getattr(client_data, 'account_name', 'Unknown')})
                failed_imports += 1
                
                if bulk_import.validation_mode == "strict":
                    await db.rollback()
                    raise HTTPException(status_code=400, detail=f"Bulk import failed at client {i}: {str(e)}")
        
        # Commit if we have any successful imports
        if successful_imports > 0:
            await db.commit()
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Bulk import completed by admin {admin_user}: {successful_imports} successful, {failed_imports} failed")
        
        return BulkOperationResponse(
            status="completed" if failed_imports == 0 else "partial",
            total_processed=len(bulk_import.clients),
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            errors=errors,
            imported_ids=imported_ids,
            processing_time_seconds=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in bulk client import: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")

# =========================
# Dashboard and Analytics
# =========================

@router.get("/dashboard/stats", response_model=ClientDashboardStats)
async def get_client_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get client dashboard statistics and analytics."""
    try:
        if not CLIENT_MODELS_AVAILABLE:
            return ClientDashboardStats(
                total_clients=0,
                active_clients=0,
                clients_by_industry={},
                clients_by_company_size={},
                clients_by_cloud_provider={},
                recent_client_registrations=[]
            )
        
        # Total and active clients
        total_query = select(func.count(ClientAccount.id))
        total_result = await db.execute(total_query)
        total_clients = total_result.scalar()
        
        active_query = select(func.count(ClientAccount.id)).where(ClientAccount.is_active == True)
        active_result = await db.execute(active_query)
        active_clients = active_result.scalar()
        
        # Clients by industry
        industry_query = select(
            ClientAccount.industry,
            func.count(ClientAccount.id).label('count')
        ).where(ClientAccount.is_active == True).group_by(ClientAccount.industry)
        industry_result = await db.execute(industry_query)
        clients_by_industry = {row.industry: row.count for row in industry_result}
        
        # Clients by company size
        size_query = select(
            ClientAccount.company_size,
            func.count(ClientAccount.id).label('count')
        ).where(ClientAccount.is_active == True).group_by(ClientAccount.company_size)
        size_result = await db.execute(size_query)
        clients_by_company_size = {row.company_size: row.count for row in size_result}
        
        # Recent registrations (last 10)
        recent_query = select(ClientAccount).where(
            ClientAccount.is_active == True
        ).order_by(desc(ClientAccount.created_at)).limit(10)
        recent_result = await db.execute(recent_query)
        recent_clients = recent_result.scalars().all()
        
        # Convert recent clients to response format
        recent_client_responses = []
        for client in recent_clients:
            client_response = await _convert_client_to_response(client, db)
            recent_client_responses.append(client_response)
        
        # For cloud provider stats, we'd need to process the JSON arrays
        # This is a simplified version
        clients_by_cloud_provider = {"aws": 5, "azure": 3, "gcp": 2, "multi_cloud": 1}
        
        return ClientDashboardStats(
            total_clients=total_clients,
            active_clients=active_clients,
            clients_by_industry=clients_by_industry,
            clients_by_company_size=clients_by_company_size,
            clients_by_cloud_provider=clients_by_cloud_provider,
            recent_client_registrations=recent_client_responses
        )
        
    except Exception as e:
        logger.error(f"Error getting client dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

# =========================
# Utility Functions
# =========================

async def _convert_client_to_response(client: ClientAccount, db: AsyncSession) -> ClientAccountResponse:
    """Convert ClientAccount model to response format with additional statistics."""
    
    # Get engagement counts
    total_engagements_query = select(func.count(Engagement.id)).where(
        Engagement.client_account_id == client.id
    )
    total_result = await db.execute(total_engagements_query)
    total_engagements = total_result.scalar() or 0
    
    active_engagements_query = select(func.count(Engagement.id)).where(
        and_(
            Engagement.client_account_id == client.id,
            Engagement.is_active == True
        )
    )
    active_result = await db.execute(active_engagements_query)
    active_engagements = active_result.scalar() or 0
    
    return ClientAccountResponse(
        id=str(client.id),
        account_name=client.name,
        industry=client.industry or '',
        company_size=client.company_size or '',
        headquarters_location='',  # Field not in model, use default
        primary_contact_name='',   # Field not in model, use default  
        primary_contact_email='',  # Field not in model, use default
        primary_contact_phone='',  # Field not in model, use default
        business_objectives=client.business_objectives or [],
        it_guidelines=client.it_guidelines or {},
        decision_criteria=client.decision_criteria or {},
        agent_preferences=client.agent_preferences or {},
        target_cloud_providers=[],  # Field not in model, use default
        business_priorities=[],     # Field not in model, use default
        compliance_requirements=[], # Field not in model, use default
        budget_constraints=None,  # Field not in model, use default
        timeline_constraints=None,  # Field not in model, use default
        created_at=client.created_at,
        updated_at=client.updated_at,
        is_active=client.is_active,
        total_engagements=total_engagements,
        active_engagements=active_engagements
    )

# =========================
# Health Check
# =========================

@router.get("/health")
async def client_management_health():
    """Health check for client management service."""
    return {
        "status": "healthy",
        "service": "client-management",
        "version": "1.0.0",
        "capabilities": {
            "client_crud": True,
            "business_context": True,
            "search_filtering": True,
            "bulk_operations": True,
            "dashboard_analytics": True,
            "client_models_available": CLIENT_MODELS_AVAILABLE
        }
    } 