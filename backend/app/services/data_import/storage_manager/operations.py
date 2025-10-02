"""
Storage Manager Core Operations - Facade

This module serves as a thin facade that composes all storage operation mixins
into a unified ImportStorageOperations class. The actual implementations are
delegated to specialized mixin modules:

- ImportCommandsMixin: Write operations (create, update, link)
- ImportQueriesMixin: Read operations (get, retrieve)
- RawRecordOperationsMixin: Raw record management
- FieldMappingOperationsMixin: Field mapping operations

This architecture maintains backward compatibility while keeping each module
under 400 lines and this facade under 100 lines.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .import_commands import ImportCommandsMixin
from .import_queries import ImportQueriesMixin
from .mapping_operations import FieldMappingOperationsMixin
from .record_operations import RawRecordOperationsMixin


class ImportStorageOperations(
    ImportCommandsMixin,
    ImportQueriesMixin,
    RawRecordOperationsMixin,
    FieldMappingOperationsMixin,
):
    """
    Unified operations class for import storage management.

    This class inherits specialized operations from multiple mixins:
    - ImportCommandsMixin: Create and update operations for imports
    - ImportQueriesMixin: Query operations for retrieving import data
    - RawRecordOperationsMixin: Raw record storage and management
    - FieldMappingOperationsMixin: Field mapping creation and management

    All methods are delegated to the respective mixin implementations,
    maintaining a clean separation of concerns while providing a single
    entry point for all storage operations.

    Example:
        ops = ImportStorageOperations(db, client_account_id)
        import_record = await ops.store_import_data(...)
        import_data = await ops.get_import_data(import_id)
    """

    def __init__(self, db: AsyncSession, client_account_id: str):
        """
        Initialize the ImportStorageOperations facade.

        Args:
            db: The database session for all operations
            client_account_id: The client account ID for multi-tenant isolation
        """
        self.db = db
        self.client_account_id = client_account_id


# Backward compatibility: Maintain the original class name in module namespace
__all__ = ["ImportStorageOperations"]
