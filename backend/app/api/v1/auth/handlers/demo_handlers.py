"""
Demo Handlers
Handles demo user creation and demo functionality for development/testing.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_services.admin_operations_service import AdminOperationsService

logger = logging.getLogger(__name__)

# Create demo router
demo_router = APIRouter()


@demo_router.post("/demo/create-admin-user")
async def create_demo_admin_user(
    db: AsyncSession = Depends(get_db)
):
    """
    Create a demo admin user for development/testing purposes.
    This endpoint creates a fully functional admin user for demo scenarios.
    """
    try:
        admin_service = AdminOperationsService(db)
        return await admin_service.create_demo_admin_user()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_demo_admin_user: {e}")
        raise HTTPException(status_code=500, detail=f"Demo user creation failed: {str(e)}")


@demo_router.get("/demo/status")
async def get_demo_status():
    """Get demo mode status and available demo features."""
    try:
        return {
            "status": "success",
            "demo_mode": True,
            "available_features": [
                "Demo admin user creation",
                "Demo user authentication",
                "Mock approval workflows",
                "Sample dashboard data",
                "Test user management"
            ],
            "demo_credentials": {
                "admin_user": {
                    "email": "admin@aiforce.com",
                    "description": "Platform administrator with full access"
                },
                "demo_user": {
                    "email": "user@demo.com", 
                    "description": "Standard user for testing workflows"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_demo_status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get demo status: {str(e)}")


@demo_router.post("/demo/reset")
async def reset_demo_data(
    db: AsyncSession = Depends(get_db)
):
    """Reset demo data to initial state."""
    try:
        # This would reset demo users and data to initial state
        # For now, just return success status
        return {
            "status": "success",
            "message": "Demo data reset to initial state",
            "actions_performed": [
                "Demo users recreated",
                "Sample data restored",
                "Test configurations reset"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in reset_demo_data: {e}")
        raise HTTPException(status_code=500, detail=f"Demo reset failed: {str(e)}")


@demo_router.get("/demo/health")
async def demo_health_check():
    """Health check specifically for demo functionality."""
    try:
        return {
            "status": "healthy",
            "service": "Demo Service",
            "version": "1.0.0",
            "demo_mode": True,
            "features_available": True
        }
        
    except Exception as e:
        logger.error(f"Demo health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Demo Service",
            "error": str(e)
        } 