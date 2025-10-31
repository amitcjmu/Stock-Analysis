"""
Shared utilities for context establishment endpoints.

Contains constants, conditional imports, and shared helpers.
"""

import logging

# Demo data constants
DEMO_CLIENT_ID = "11111111-1111-1111-1111-111111111111"

# Make client_account import conditional to avoid deployment failures
try:
    from app.models import ClientAccess, ClientAccount, Engagement, UserRole

    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError:
    CLIENT_ACCOUNT_AVAILABLE = False
    ClientAccount = None
    Engagement = None
    ClientAccess = None
    UserRole = None


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for context establishment modules.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
