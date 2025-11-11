"""
Base FlowCommands class with shared utilities.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FlowCommands:
    """Commands for core assessment flow operations"""

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id
