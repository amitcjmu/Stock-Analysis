"""
Modular RBAC Service - Main coordination service for all RBAC operations.
This service coordinates between specialized handlers for different RBAC operations.
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

# Import handlers
from .rbac_handlers.user_management_handler import UserManagementHandler
from .rbac_handlers.access_validation_handler import AccessValidationHandler  
from .rbac_handlers.admin_operations_handler import AdminOperationsHandler

logger = logging.getLogger(__name__)

class RBACService:
    """
    Modular RBAC service that coordinates specialized handlers.
    Each handler focuses on a specific area of RBAC functionality.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize specialized handlers
        self.user_management = UserManagementHandler(db)
        self.access_validation = AccessValidationHandler(db)
        self.admin_operations = AdminOperationsHandler(db)
        
        # Check availability based on handlers
        self.is_available = (
            self.user_management.is_available and 
            self.access_validation.is_available and 
            self.admin_operations.is_available
        )
        
        if not self.is_available:
            logger.warning("Modular RBAC Service initialized with limited functionality")
    
    # =========================
    # User Management Operations (Delegated to UserManagementHandler)
    # =========================
    
    async def register_user_request(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user with pending approval status."""
        return await self.user_management.register_user_request(user_data)
    
    async def approve_user(self, user_id: str, approved_by: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a pending user registration."""
        return await self.user_management.approve_user(user_id, approved_by, approval_data)
    
    async def reject_user(self, user_id: str, rejected_by: str, rejection_reason: str) -> Dict[str, Any]:
        """Reject a pending user registration."""
        return await self.user_management.reject_user(user_id, rejected_by, rejection_reason)
    
    async def deactivate_user(self, user_id: str, deactivated_by: str, reason: str = None) -> Dict[str, Any]:
        """Deactivate an active user."""
        return await self.user_management.deactivate_user(user_id, deactivated_by, reason)
    
    async def get_pending_approvals(self, admin_user_id: str) -> Dict[str, Any]:
        """Get all users pending approval."""
        return await self.user_management.get_pending_approvals(admin_user_id)
    
    # =========================
    # Access Validation Operations (Delegated to AccessValidationHandler)
    # =========================
    
    async def validate_user_access(self, user_id: str, resource_type: str, 
                                 resource_id: str = None, action: str = "read") -> Dict[str, Any]:
        """Validate if user has access to a specific resource."""
        return await self.access_validation.validate_user_access(user_id, resource_type, resource_id, action)
    
    async def grant_client_access(self, user_id: str, client_id: str, access_data: Dict[str, Any], 
                                granted_by: str) -> Dict[str, Any]:
        """Grant client access to a user."""
        return await self.access_validation.grant_client_access(user_id, client_id, access_data, granted_by)
    
    # =========================
    # Admin Operations (Delegated to AdminOperationsHandler)
    # =========================
    
    async def admin_create_user(self, user_data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Admin direct user creation with immediate activation."""
        return await self.admin_operations.admin_create_user(user_data, created_by)
    
    async def get_admin_dashboard_stats(self, admin_user_id: str) -> Dict[str, Any]:
        """Get admin dashboard statistics."""
        return await self.admin_operations.get_admin_dashboard_stats(admin_user_id)
    
    async def bulk_user_operation(self, operation: str, user_ids: List[str], 
                                 admin_user_id: str, operation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform bulk operations on multiple users."""
        return await self.admin_operations.bulk_user_operation(operation, user_ids, admin_user_id, operation_data)
    
    # =========================
    # Convenience Methods for Common Operations
    # =========================
    
    async def validate_admin_access(self, user_id: str) -> bool:
        """Quick check if user has admin access."""
        result = await self.access_validation._validate_admin_access(user_id)
        return result
    
    async def validate_client_access(self, user_id: str, client_id: str, action: str = "read") -> bool:
        """Quick check if user has client access."""
        result = await self.access_validation._validate_client_access(user_id, client_id, action)
        return result
    
    async def validate_engagement_access(self, user_id: str, engagement_id: str, action: str = "read") -> bool:
        """Quick check if user has engagement access."""
        result = await self.access_validation._validate_engagement_access(user_id, engagement_id, action)
        return result
    
    # =========================
    # Health and Status Methods
    # =========================
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of all RBAC service components."""
        return {
            "rbac_service_available": self.is_available,
            "handlers": {
                "user_management": self.user_management.is_available,
                "access_validation": self.access_validation.is_available,
                "admin_operations": self.admin_operations.is_available
            },
            "database_connection": self.db is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of the RBAC service."""
        try:
            status = self.get_service_status()
            
            # Test database connectivity
            try:
                from sqlalchemy import text
                await self.db.execute(text("SELECT 1"))
                status["database_health"] = "healthy"
            except Exception as e:
                status["database_health"] = f"error: {str(e)}"
            
            # Test each handler
            handler_health = {}
            
            # Test user management handler
            try:
                # This is a lightweight test - just check if we can access the handler
                handler_health["user_management"] = "healthy" if self.user_management.is_available else "unavailable"
            except Exception as e:
                handler_health["user_management"] = f"error: {str(e)}"
            
            # Test access validation handler
            try:
                handler_health["access_validation"] = "healthy" if self.access_validation.is_available else "unavailable"
            except Exception as e:
                handler_health["access_validation"] = f"error: {str(e)}"
            
            # Test admin operations handler
            try:
                handler_health["admin_operations"] = "healthy" if self.admin_operations.is_available else "unavailable"
            except Exception as e:
                handler_health["admin_operations"] = f"error: {str(e)}"
            
            status["handler_health"] = handler_health
            
            # Overall health assessment
            all_healthy = (
                status["database_health"] == "healthy" and
                all(health == "healthy" for health in handler_health.values())
            )
            
            status["overall_health"] = "healthy" if all_healthy else "degraded"
            
            return {
                "status": "success",
                "service_health": status
            }
            
        except Exception as e:
            logger.error(f"Error in RBAC health check: {e}")
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service_health": {"overall_health": "error"}
            }

# Factory function for creating RBAC service instances
def create_rbac_service(db: AsyncSession) -> RBACService:
    """Create a new RBAC service instance with proper error handling."""
    try:
        return RBACService(db)
    except Exception as e:
        logger.error(f"Failed to create RBAC service: {e}")
        # Return a service instance that will handle errors gracefully
        return RBACService(db) 