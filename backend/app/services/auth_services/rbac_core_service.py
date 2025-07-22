"""
RBAC Core Service
Contains core RBAC utilities, role management, and system initialization functions.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rbac import UserRole
from app.services.rbac_service import create_rbac_service

logger = logging.getLogger(__name__)


class RBACCoreService:
    """Core RBAC service for system utilities and role management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def ensure_basic_roles_exist(self) -> None:
        """
        Ensure basic user roles exist in the system.
        This is called during system initialization.
        """
        try:
            rbac_service = create_rbac_service(self.db)
            
            # Define basic roles that should exist
            basic_roles = [
                {
                    "role_type": "platform_admin",
                    "role_name": "Platform Administrator", 
                    "description": "Full platform administrative access",
                    "permissions": {
                        "can_read_all_data": True,
                        "can_write_all_data": True,
                        "can_delete_data": True,
                        "can_manage_users": True,
                        "can_approve_users": True,
                        "can_access_admin_console": True,
                        "can_view_audit_logs": True,
                        "can_manage_clients": True,
                        "can_manage_engagements": True,
                        "can_access_llm_usage": True
                    }
                },
                {
                    "role_type": "client_admin",
                    "role_name": "Client Administrator",
                    "description": "Administrative access within client scope",
                    "permissions": {
                        "can_read_client_data": True,
                        "can_write_client_data": True,
                        "can_delete_client_data": False,
                        "can_manage_client_users": True,
                        "can_approve_client_users": True,
                        "can_access_client_console": True,
                        "can_view_client_logs": True,
                        "can_manage_client_engagements": True,
                        "can_access_client_reports": True
                    }
                },
                {
                    "role_type": "analyst",
                    "role_name": "Migration Analyst",
                    "description": "Can analyze data and create reports",
                    "permissions": {
                        "can_read_data": True,
                        "can_write_data": True,
                        "can_delete_data": False,
                        "can_run_analysis": True,
                        "can_view_reports": True,
                        "can_export_data": True,
                        "can_create_engagements": False,
                        "can_modify_configurations": False
                    }
                },
                {
                    "role_type": "viewer",
                    "role_name": "Read-Only Viewer",
                    "description": "Read-only access to data and reports",
                    "permissions": {
                        "can_read_data": True,
                        "can_write_data": False,
                        "can_delete_data": False,
                        "can_run_analysis": False,
                        "can_view_reports": True,
                        "can_export_data": True,
                        "can_create_engagements": False,
                        "can_modify_configurations": False
                    }
                }
            ]
            
            # Create roles if they don't exist
            for role_data in basic_roles:
                await rbac_service.ensure_role_exists(role_data)
            
            logger.info("Basic roles ensured in system")
            
        except Exception as e:
            logger.error(f"Error ensuring basic roles exist: {e}")
            # Don't raise exception - this is a background initialization
    
    def get_role_permissions(self, role_type: str) -> Dict[str, bool]:
        """
        Get the permissions dictionary for a specific role type.
        """
        permissions = {
            "platform_admin": {
                "can_read_all_data": True,
                "can_write_all_data": True,
                "can_delete_data": True,
                "can_manage_users": True,
                "can_approve_users": True,
                "can_access_admin_console": True,
                "can_view_audit_logs": True,
                "can_manage_clients": True,
                "can_manage_engagements": True,
                "can_access_llm_usage": True
            },
            "client_admin": {
                "can_read_client_data": True,
                "can_write_client_data": True,
                "can_delete_client_data": False,
                "can_manage_client_users": True,
                "can_approve_client_users": True,
                "can_access_client_console": True,
                "can_view_client_logs": True,
                "can_manage_client_engagements": True,
                "can_access_client_reports": True
            },
            "analyst": {
                "can_read_data": True,
                "can_write_data": True,
                "can_delete_data": False,
                "can_run_analysis": True,
                "can_view_reports": True,
                "can_export_data": True,
                "can_create_engagements": False,
                "can_modify_configurations": False
            },
            "viewer": {
                "can_read_data": True,
                "can_write_data": False,
                "can_delete_data": False,
                "can_run_analysis": False,
                "can_view_reports": True,
                "can_export_data": True,
                "can_create_engagements": False,
                "can_modify_configurations": False
            }
        }
        
        return permissions.get(role_type, permissions["viewer"])
    
    async def validate_role_hierarchy(self, assigner_role: str, assignee_role: str) -> bool:
        """
        Validate that a user with assigner_role can assign assignee_role.
        Implements role hierarchy validation.
        """
        try:
            role_hierarchy = {
                "platform_admin": ["platform_admin", "client_admin", "analyst", "viewer"],
                "client_admin": ["analyst", "viewer"],
                "analyst": [],
                "viewer": []
            }
            
            allowed_roles = role_hierarchy.get(assigner_role, [])
            return assignee_role in allowed_roles
            
        except Exception as e:
            logger.error(f"Error validating role hierarchy: {e}")
            return False
    
    async def get_user_effective_permissions(self, user_id: str) -> Dict[str, bool]:
        """
        Get the effective permissions for a user based on all their roles.
        Combines permissions from multiple roles.
        """
        try:
            # Get all active roles for the user
            user_roles_query = select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.is_active == True
            )
            result = await self.db.execute(user_roles_query)
            user_roles = result.scalars().all()
            
            # Combine permissions from all roles
            effective_permissions = {}
            
            for role in user_roles:
                role_permissions = self.get_role_permissions(role.role_type)
                
                # Merge permissions (OR operation - if any role has permission, user has it)
                for permission, value in role_permissions.items():
                    if permission not in effective_permissions:
                        effective_permissions[permission] = value
                    else:
                        effective_permissions[permission] = effective_permissions[permission] or value
            
            return effective_permissions
            
        except Exception as e:
            logger.error(f"Error getting effective permissions for user {user_id}: {e}")
            return {}
    
    async def check_user_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        """
        try:
            effective_permissions = await self.get_user_effective_permissions(user_id)
            return effective_permissions.get(permission, False)
            
        except Exception as e:
            logger.error(f"Error checking permission {permission} for user {user_id}: {e}")
            return False
    
    async def get_role_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about role distribution in the system.
        """
        try:
            # Query role distribution
            role_stats_query = select(UserRole.role_type).where(UserRole.is_active == True)
            result = await self.db.execute(role_stats_query)
            role_types = result.scalars().all()
            
            # Count roles
            role_counts = {}
            for role_type in role_types:
                role_counts[role_type] = role_counts.get(role_type, 0) + 1
            
            return {
                "total_active_roles": len(role_types),
                "role_distribution": role_counts,
                "available_role_types": ["platform_admin", "client_admin", "analyst", "viewer"]
            }
            
        except Exception as e:
            logger.error(f"Error getting role statistics: {e}")
            return {
                "total_active_roles": 0,
                "role_distribution": {},
                "available_role_types": ["platform_admin", "client_admin", "analyst", "viewer"]
            } 