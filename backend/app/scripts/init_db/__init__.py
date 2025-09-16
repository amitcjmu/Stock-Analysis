"""
Database initialization module.

This module provides backward compatibility with the original init_db.py script
while organizing the code into focused, modular components.

BACKWARD COMPATIBILITY:
All public functions from the original init_db.py are preserved and exported.
"""

# Import all major functions to preserve backward compatibility
from .base import (
    ADMIN_USER_ID,
    DEMO_CLIENT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_SESSION_ID,
    DEMO_USER_ID,
    generate_mock_embedding,
    logger,
)
from .main import initialize_mock_data, main
from .migrations import check_mock_data_exists
from .schema import (
    create_mock_assets,
    create_mock_client_account,
    create_mock_engagement,
    create_mock_migration_waves,
    create_mock_sixr_analysis,
    create_mock_tags,
    create_mock_users,
)
from .seed_data import MOCK_DATA

# Export all public functions for backward compatibility
__all__ = [
    # Constants
    "DEMO_CLIENT_ID",
    "DEMO_ENGAGEMENT_ID",
    "DEMO_SESSION_ID",
    "DEMO_USER_ID",
    "ADMIN_USER_ID",
    "MOCK_DATA",
    "logger",
    # Utility functions
    "generate_mock_embedding",
    "check_mock_data_exists",
    # Schema creation functions
    "create_mock_client_account",
    "create_mock_users",
    "create_mock_engagement",
    "create_mock_tags",
    "create_mock_assets",
    "create_mock_sixr_analysis",
    "create_mock_migration_waves",
    # Main functions
    "initialize_mock_data",
    "main",
]
