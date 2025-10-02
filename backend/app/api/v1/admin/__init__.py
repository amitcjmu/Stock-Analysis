"""
Admin API endpoints package.
Contains all administration-related API handlers including user management, platform administration, and enhanced RBAC.
"""

# Admin module for client and engagement management endpoints

# Import admin routers
try:
    from . import (
        client_management,
        engagement_management,
        session_comparison,
        memory_management,
    )

    CLIENT_MANAGEMENT_AVAILABLE = True
    ENGAGEMENT_MANAGEMENT_AVAILABLE = True
    SESSION_COMPARISON_AVAILABLE = True
    MEMORY_MANAGEMENT_AVAILABLE = True
except ImportError as e:
    CLIENT_MANAGEMENT_AVAILABLE = False
    ENGAGEMENT_MANAGEMENT_AVAILABLE = False
    SESSION_COMPARISON_AVAILABLE = False
    MEMORY_MANAGEMENT_AVAILABLE = False
    print(f"⚠️ Admin management modules not fully available: {e}")

__all__ = [
    "client_management",
    "engagement_management",
    "session_comparison",
    "memory_management",
]
