# Auth module for RBAC endpoints 
from fastapi import APIRouter
from .handlers.authentication_handlers import authentication_router
from .handlers.user_management_handlers import user_management_router
from .handlers.admin_handlers import admin_router

auth_router = APIRouter()

auth_router.include_router(authentication_router, tags=["Authentication"])
auth_router.include_router(user_management_router, tags=["User Management"])
auth_router.include_router(admin_router, tags=["Admin User Management"]) 