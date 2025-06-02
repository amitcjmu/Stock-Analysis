# Admin module for client and engagement management endpoints

# Import admin routers
try:
    from . import client_management
    from . import engagement_management
    CLIENT_MANAGEMENT_AVAILABLE = True
    ENGAGEMENT_MANAGEMENT_AVAILABLE = True
except ImportError as e:
    CLIENT_MANAGEMENT_AVAILABLE = False
    ENGAGEMENT_MANAGEMENT_AVAILABLE = False
    print(f"⚠️ Admin management modules not fully available: {e}")

__all__ = ["client_management", "engagement_management"] 