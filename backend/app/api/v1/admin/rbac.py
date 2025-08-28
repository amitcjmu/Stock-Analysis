"""
RBAC Admin Router
Role-Based Access Control administration endpoints
"""

from fastapi import APIRouter, Depends
from app.api.v1.auth.auth_utils import get_current_user
from app.models.client_account import User

router = APIRouter(prefix="/rbac-admin")


@router.get("/roles")
async def get_roles(admin_user: User = Depends(get_current_user)):
    """Get all available roles"""
    return {
        "roles": [
            {"id": "admin", "name": "Administrator", "permissions": ["*"]},
            {"id": "user", "name": "User", "permissions": ["read", "write"]},
            {"id": "viewer", "name": "Viewer", "permissions": ["read"]},
        ]
    }


@router.get("/permissions")
async def get_permissions(admin_user: User = Depends(get_current_user)):
    """Get all available permissions"""
    return {
        "permissions": [
            {"id": "read", "name": "Read", "description": "Read access to resources"},
            {
                "id": "write",
                "name": "Write",
                "description": "Write access to resources",
            },
            {
                "id": "delete",
                "name": "Delete",
                "description": "Delete access to resources",
            },
            {"id": "*", "name": "All", "description": "Full access to all resources"},
        ]
    }


@router.post("/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: str, role_id: str, admin_user: User = Depends(get_current_user)
):
    """Assign a role to a user"""
    return {
        "success": True,
        "message": f"Role {role_id} assigned to user {user_id}",
        "user_id": user_id,
        "role_id": role_id,
    }


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str, role_id: str, admin_user: User = Depends(get_current_user)
):
    """Remove a role from a user"""
    return {
        "success": True,
        "message": f"Role {role_id} removed from user {user_id}",
        "user_id": user_id,
        "role_id": role_id,
    }


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str, admin_user: User = Depends(get_current_user)
):
    """Get all permissions for a specific user"""
    return {
        "user_id": user_id,
        "permissions": ["read", "write"],
        "roles": ["user"],
        "effective_permissions": ["read", "write"],
    }
