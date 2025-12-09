"""
Base class and imports for Enhanced RBAC Service.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

# Import enhanced RBAC models
try:
    from app.models.client_account import ClientAccount, Engagement, User
    from app.models.rbac_enhanced import (
        DEFAULT_ROLE_PERMISSIONS,
        AccessAuditLog,
        DataScope,
        DeletedItemType,
        EnhancedUserProfile,
        RoleLevel,
        RolePermissions,
        SoftDeletedItems,
        UserStatus,
    )

    ENHANCED_RBAC_AVAILABLE = True
except ImportError:
    ENHANCED_RBAC_AVAILABLE = False
    EnhancedUserProfile = RolePermissions = SoftDeletedItems = AccessAuditLog = None
    User = ClientAccount = Engagement = None
    RoleLevel = DataScope = UserStatus = DeletedItemType = DEFAULT_ROLE_PERMISSIONS = (
        None
    )

logger = logging.getLogger(__name__)


class EnhancedRBACServiceBase:
    """
    Base class for Enhanced RBAC service.
    Provides database session and availability checking.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.is_available = ENHANCED_RBAC_AVAILABLE

        if not self.is_available:
            logger.warning(
                "Enhanced RBAC models not available - running in fallback mode"
            )
