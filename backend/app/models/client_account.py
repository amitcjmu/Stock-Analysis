"""
Client Account models for multi-tenant data segregation.

This module has been modularized. The models are now in separate files
for better maintainability and to keep file length under the 400-line limit.

Import the models from the modular structure to maintain backward compatibility.
"""

# Import all models from the modular structure for backward compatibility
from .client_account.base import ClientAccount
from .client_account.engagement import Engagement
from .client_account.user import User
from .client_account.associations import UserAccountAssociation

# Export all models to maintain existing API
__all__ = [
    "ClientAccount",
    "Engagement",
    "User",
    "UserAccountAssociation",
]
