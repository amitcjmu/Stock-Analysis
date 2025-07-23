"""
Database transaction utilities.
Provides transaction management patterns and error handling.
"""

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncContextManager, Callable, Optional, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class TransactionConfig:
    """Configuration for database transactions."""

    auto_commit: bool = True
    rollback_on_error: bool = True
    log_transactions: bool = True
    transaction_timeout: Optional[int] = None
    savepoint_name: Optional[str] = None


class DatabaseTransaction:
    """
    Database transaction wrapper with enhanced error handling and logging.
    """

    def __init__(
        self, session: AsyncSession, config: Optional[TransactionConfig] = None
    ):
        self.session = session
        self.config = config or TransactionConfig()
        self.start_time: Optional[datetime] = None
        self.is_active = False
        self.has_error = False
        self.error_message: Optional[str] = None

    async def __aenter__(self) -> "DatabaseTransaction":
        """Enter transaction context."""
        self.start_time = datetime.utcnow()
        self.is_active = True

        if self.config.log_transactions:
            logger.debug("Starting database transaction")

        # Begin transaction (AsyncSession starts transactions automatically)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context with error handling."""
        duration = (
            (datetime.utcnow() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )

        try:
            if exc_type is not None:
                # Exception occurred
                self.has_error = True
                self.error_message = str(exc_val) if exc_val else "Unknown error"

                if self.config.rollback_on_error:
                    await self.session.rollback()
                    if self.config.log_transactions:
                        logger.error(
                            f"Transaction rolled back due to error: {self.error_message} "
                            f"(duration: {duration:.2f}s)"
                        )
                else:
                    if self.config.log_transactions:
                        logger.warning(
                            f"Transaction completed with error but not rolled back: {self.error_message}"
                        )
            else:
                # No exception, commit if configured
                if self.config.auto_commit:
                    await self.session.commit()
                    if self.config.log_transactions:
                        logger.debug(
                            f"Transaction committed successfully (duration: {duration:.2f}s)"
                        )
                else:
                    if self.config.log_transactions:
                        logger.debug(
                            f"Transaction completed without auto-commit (duration: {duration:.2f}s)"
                        )

        except SQLAlchemyError as e:
            logger.error(f"Error during transaction cleanup: {e}")
            try:
                await self.session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")

        finally:
            self.is_active = False

    async def commit(self) -> None:
        """Manually commit the transaction."""
        if not self.is_active:
            raise RuntimeError("Transaction is not active")

        try:
            await self.session.commit()
            if self.config.log_transactions:
                logger.debug("Transaction committed manually")
        except SQLAlchemyError as e:
            self.has_error = True
            self.error_message = str(e)
            logger.error(f"Error committing transaction: {e}")
            raise

    async def rollback(self) -> None:
        """Manually rollback the transaction."""
        if not self.is_active:
            raise RuntimeError("Transaction is not active")

        try:
            await self.session.rollback()
            if self.config.log_transactions:
                logger.debug("Transaction rolled back manually")
        except SQLAlchemyError as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise

    async def savepoint(self, name: Optional[str] = None) -> str:
        """Create a savepoint within the transaction."""
        if not self.is_active:
            raise RuntimeError("Transaction is not active")

        savepoint_name = name or f"sp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            await self.session.execute(f"SAVEPOINT {savepoint_name}")
            if self.config.log_transactions:
                logger.debug(f"Savepoint created: {savepoint_name}")
            return savepoint_name
        except SQLAlchemyError as e:
            logger.error(f"Error creating savepoint {savepoint_name}: {e}")
            raise

    async def rollback_to_savepoint(self, savepoint_name: str) -> None:
        """Rollback to a specific savepoint."""
        if not self.is_active:
            raise RuntimeError("Transaction is not active")

        try:
            await self.session.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
            if self.config.log_transactions:
                logger.debug(f"Rolled back to savepoint: {savepoint_name}")
        except SQLAlchemyError as e:
            logger.error(f"Error rolling back to savepoint {savepoint_name}: {e}")
            raise


class TransactionManager:
    """
    Transaction manager for database operations.
    """

    @staticmethod
    @asynccontextmanager
    async def transaction(
        session: AsyncSession, config: Optional[TransactionConfig] = None
    ) -> AsyncContextManager[DatabaseTransaction]:
        """
        Create a database transaction context.

        Args:
            session: Database session
            config: Transaction configuration

        Yields:
            DatabaseTransaction: Transaction wrapper
        """
        transaction = DatabaseTransaction(session, config)
        async with transaction:
            yield transaction

    @staticmethod
    async def execute_in_transaction(
        session: AsyncSession,
        operation: Callable[[AsyncSession], Any],
        config: Optional[TransactionConfig] = None,
    ) -> Any:
        """
        Execute an operation within a transaction.

        Args:
            session: Database session
            operation: Operation to execute
            config: Transaction configuration

        Returns:
            Result of the operation
        """
        async with TransactionManager.transaction(session, config):
            return await operation(session)

    @staticmethod
    async def bulk_operation(
        session: AsyncSession,
        operations: list[Callable[[AsyncSession], Any]],
        config: Optional[TransactionConfig] = None,
    ) -> list[Any]:
        """
        Execute multiple operations in a single transaction.

        Args:
            session: Database session
            operations: List of operations to execute
            config: Transaction configuration

        Returns:
            List of operation results
        """
        results = []

        async with TransactionManager.transaction(session, config):
            for operation in operations:
                result = await operation(session)
                results.append(result)

        return results


# Convenience functions and decorators
@asynccontextmanager
async def transaction_scope(
    session: AsyncSession, auto_commit: bool = True, rollback_on_error: bool = True
) -> AsyncContextManager[DatabaseTransaction]:
    """
    Simple transaction scope context manager.

    Args:
        session: Database session
        auto_commit: Whether to auto-commit on success
        rollback_on_error: Whether to rollback on error

    Yields:
        DatabaseTransaction: Transaction wrapper
    """
    config = TransactionConfig(
        auto_commit=auto_commit, rollback_on_error=rollback_on_error
    )

    async with TransactionManager.transaction(session, config) as tx:
        yield tx


async def rollback_on_error(
    session: AsyncSession, operation: Callable[[AsyncSession], T]
) -> T:
    """
    Execute operation with automatic rollback on error.

    Args:
        session: Database session
        operation: Operation to execute

    Returns:
        Result of the operation
    """
    try:
        result = await operation(session)
        await session.commit()
        return result
    except Exception as e:
        await session.rollback()
        logger.error(f"Operation failed, rolled back: {e}")
        raise


async def commit_or_rollback(
    session: AsyncSession, operation: Callable[[AsyncSession], T]
) -> T:
    """
    Execute operation and commit or rollback based on success.

    Args:
        session: Database session
        operation: Operation to execute

    Returns:
        Result of the operation
    """
    try:
        result = await operation(session)
        await session.commit()
        logger.debug("Operation completed successfully, committed")
        return result
    except Exception as e:
        await session.rollback()
        logger.error(f"Operation failed, rolled back: {e}")
        raise


# Batch operation utilities
async def execute_batch(
    session: AsyncSession,
    operations: list[Callable[[AsyncSession], Any]],
    batch_size: int = 100,
    continue_on_error: bool = False,
) -> list[Any]:
    """
    Execute operations in batches with transaction management.

    Args:
        session: Database session
        operations: List of operations to execute
        batch_size: Number of operations per batch
        continue_on_error: Whether to continue on individual operation errors

    Returns:
        List of operation results
    """
    results = []
    errors = []

    for i in range(0, len(operations), batch_size):
        batch = operations[i : i + batch_size]

        try:
            async with transaction_scope(session):
                batch_results = []

                for operation in batch:
                    try:
                        result = await operation(session)
                        batch_results.append(result)
                    except Exception as e:
                        if continue_on_error:
                            errors.append(e)
                            batch_results.append(None)
                        else:
                            raise

                results.extend(batch_results)
                logger.debug(
                    f"Batch {i//batch_size + 1} completed: {len(batch)} operations"
                )

        except Exception as e:
            logger.error(f"Batch {i//batch_size + 1} failed: {e}")
            if not continue_on_error:
                raise

    if errors:
        logger.warning(f"Batch execution completed with {len(errors)} errors")

    return results
