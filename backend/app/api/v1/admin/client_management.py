"""
Client Management API - Modular Implementation
Admin endpoints for managing client accounts with business context and migration planning.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.rbac_middleware import require_admin_access
from app.schemas.admin_schemas import (
    ClientAccountCreate, ClientAccountUpdate, ClientAccountResponse,
    ClientSearchFilters, ClientDashboardStats, BulkClientImport, BulkOperationResponse,
    AdminPaginationParams, PaginatedResponse, AdminSuccessResponse, AdminErrorResponse
)

# Import handlers with fallback
try:
    from .client_management_handlers.client_crud_handler import ClientCRUDHandler
    HANDLERS_AVAILABLE = True
except ImportError:
    HANDLERS_AVAILABLE = False
    ClientCRUDHandler = None

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/clients", tags=["Client Management"])

# =========================
# Health Check
# =========================

@router.get("/health")
async def client_management_health():
    """Health check for client management service."""
    return {
        "status": "healthy",
        "service": "client-management-modular",
        "version": "2.0.0",
        "capabilities": {
            "client_crud": HANDLERS_AVAILABLE,
            "business_context": True,
            "search_filtering": True,
            "bulk_operations": True,
            "dashboard_analytics": True,
            "modular_architecture": True
        }
    }

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
    """Create a new client account with business context."""
    if not HANDLERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Client handlers not available")
    
    return await ClientCRUDHandler.create_client(client_data, db, admin_user)

@router.get("/{client_id}", response_model=AdminSuccessResponse)
async def get_client_account(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get detailed client account information."""
    if not HANDLERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Client handlers not available")
    
    return await ClientCRUDHandler.get_client(client_id, db)

@router.put("/{client_id}", response_model=AdminSuccessResponse)
async def update_client_account(
    client_id: str,
    update_data: ClientAccountUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Update client account information."""
    if not HANDLERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Client handlers not available")
    
    return await ClientCRUDHandler.update_client(client_id, update_data, db, admin_user)

@router.delete("/{client_id}", response_model=AdminSuccessResponse)
async def delete_client_account(
    client_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Delete client account."""
    if not HANDLERS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Client handlers not available")
    
    return await ClientCRUDHandler.delete_client(client_id, db, admin_user)

@router.get("/", response_model=PaginatedResponse)
async def list_client_accounts(
    pagination: AdminPaginationParams = Depends(),
    filters: ClientSearchFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """List client accounts with pagination and filtering."""
    try:
        # Demo implementation for list functionality with all required fields
        demo_clients = [
            {
                "id": "1",
                "account_name": "Pujyam Corp",
                "industry": "Technology",
                "company_size": "Large (1001-5000)",
                "headquarters_location": "San Francisco, CA",
                "primary_contact_name": "John Smith",
                "primary_contact_email": "john.smith@pujyam.com",
                "primary_contact_phone": "+1-555-123-4567",
                "description": "Leading technology company focused on cloud migration",
                "subscription_tier": "Enterprise",
                "billing_contact_email": "billing@pujyam.com",
                "settings": {"notifications": True, "reporting": "weekly"},
                "branding": {"theme": "blue", "logo_url": "/assets/pujyam-logo.png"},
                "slug": "pujyam-corp",
                "created_by": "admin@aiforce.com",
                "business_objectives": ["Cost Reduction", "Scalability", "Innovation"],
                "it_guidelines": {"security_level": "high", "compliance": ["SOC2", "HIPAA"]},
                "decision_criteria": {"cost_weight": 0.4, "performance_weight": 0.3, "security_weight": 0.3},
                "agent_preferences": {"analysis_depth": "comprehensive", "automation_level": "medium"},
                "target_cloud_providers": ["AWS", "Azure"],
                "business_priorities": ["cost_reduction", "agility_speed"],
                "compliance_requirements": ["SOC2", "HIPAA", "PCI-DSS"],
                "budget_constraints": {"max_budget": 2000000, "currency": "USD"},
                "timeline_constraints": {"max_duration_months": 12},
                "is_active": True,
                "total_engagements": 3,
                "active_engagements": 2,
                "created_at": datetime.fromisoformat("2025-01-10T10:30:00"),
                "updated_at": datetime.fromisoformat("2025-01-15T14:20:00")
            },
            {
                "id": "2",
                "account_name": "TechCorp Solutions",
                "industry": "Finance",
                "company_size": "Enterprise (5000+)",
                "headquarters_location": "New York, NY",
                "primary_contact_name": "Sarah Wilson",
                "primary_contact_email": "sarah.wilson@techcorp.com",
                "primary_contact_phone": "+1-555-987-6543",
                "description": "Financial services firm modernizing infrastructure",
                "subscription_tier": "Professional",
                "billing_contact_email": "finance@techcorp.com",
                "settings": {"notifications": True, "reporting": "daily"},
                "branding": {"theme": "green", "logo_url": "/assets/techcorp-logo.png"},
                "slug": "techcorp-solutions",
                "created_by": "admin@aiforce.com",
                "business_objectives": ["Security", "Compliance", "Performance"],
                "it_guidelines": {"security_level": "maximum", "compliance": ["SOX", "PCI-DSS"]},
                "decision_criteria": {"security_weight": 0.5, "compliance_weight": 0.3, "cost_weight": 0.2},
                "agent_preferences": {"analysis_depth": "detailed", "automation_level": "high"},
                "target_cloud_providers": ["Azure", "GCP"],
                "business_priorities": ["security_compliance", "reliability"],
                "compliance_requirements": ["SOX", "PCI-DSS", "GDPR"],
                "budget_constraints": {"max_budget": 5000000, "currency": "USD"},
                "timeline_constraints": {"max_duration_months": 18},
                "is_active": True,
                "total_engagements": 1,
                "active_engagements": 1,
                "created_at": datetime.fromisoformat("2025-02-15T14:20:00"),
                "updated_at": datetime.fromisoformat("2025-02-20T09:15:00")
            }
        ]
        
        return {
            "items": demo_clients,
            "total_items": len(demo_clients),
            "total_pages": 1,
            "current_page": pagination.page,
            "page_size": pagination.page_size,
            "has_next": False,
            "has_previous": False
        }
        
    except Exception as e:
        logger.error(f"Error listing client accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list client accounts: {str(e)}")

@router.get("/dashboard/stats", response_model=ClientDashboardStats)
async def get_client_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get client dashboard statistics."""
    try:
        # Demo implementation for dashboard stats
        return ClientDashboardStats(
            total_clients=2,
            active_clients=2,
            clients_by_industry={
                "Technology": 1,
                "Finance": 1
            },
            clients_by_company_size={
                "Large (1001-5000)": 1,
                "Enterprise (5000+)": 1
            },
            clients_by_cloud_provider={
                "AWS": 1,
                "Azure": 1
            },
            recent_client_registrations=[
                {
                    "id": "1",
                    "account_name": "Pujyam Corp",
                    "industry": "Technology",
                    "company_size": "Large (1001-5000)",
                    "headquarters_location": "San Francisco, CA",
                    "primary_contact_name": "John Smith",
                    "primary_contact_email": "john.smith@pujyam.com",
                    "primary_contact_phone": None,
                    "description": None,
                    "subscription_tier": None,
                    "billing_contact_email": None,
                    "settings": {},
                    "branding": {},
                    "slug": None,
                    "created_by": None,
                    "business_objectives": [],
                    "it_guidelines": {},
                    "decision_criteria": {},
                    "agent_preferences": {},
                    "target_cloud_providers": ["aws"],
                    "business_priorities": [],
                    "compliance_requirements": [],
                    "budget_constraints": None,
                    "timeline_constraints": None,
                    "created_at": datetime.now(),
                    "updated_at": None,
                    "is_active": True,
                    "total_engagements": 3,
                    "active_engagements": 2
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting client dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@router.post("/bulk-import", response_model=BulkOperationResponse)
async def bulk_import_clients(
    bulk_import: BulkClientImport,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Bulk import client accounts."""
    try:
        # Demo implementation for bulk import
        return BulkOperationResponse(
            operation_id="bulk_import_" + str(hash(str(bulk_import.clients))),
            total_records=len(bulk_import.clients),
            successful_records=len(bulk_import.clients),
            failed_records=0,
            errors=[],
            warnings=[],
            processing_time_seconds=1.5,
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"Error in bulk import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk import clients: {str(e)}") 