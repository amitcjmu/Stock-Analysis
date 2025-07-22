"""
Auth Handlers Package
Handler modules for modularized RBAC endpoints.
"""

from .admin_handlers import admin_router
from .authentication_handlers import authentication_router
from .demo_handlers import demo_router
from .user_management_handlers import user_management_router

__all__ = [
    "authentication_router",
    "user_management_router", 
    "admin_router",
    "demo_router"
] 