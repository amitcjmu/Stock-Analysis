"""
Import Transaction Manager Module

Handles transaction management including:
- Atomic transaction handling and rollback
- Multi-step operation coordination
- Error recovery and cleanup
- Transaction state tracking
"""

import logging
from typing import Any, AsyncContextManager, Optional, Dict
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import DatabaseError

logger = get_logger(__name__)


class ImportTransactionManager:
    """
    Manages database transactions for import operations.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._transaction_active = False
        self._rollback_performed = False
        
    @asynccontextmanager
    async def transaction(self) -> AsyncContextManager[None]:
        """
        Context manager for handling database transactions.
        
        Ensures atomic operations with proper rollback on failure.
        """
        if self._transaction_active:
            logger.warning("Transaction already active, using existing transaction")
            yield
            return
            
        self._transaction_active = True
        self._rollback_performed = False
        
        try:
            logger.info("🔄 Starting import transaction")
            
            # Transaction is automatically started by SQLAlchemy
            yield
            
            # Commit the transaction
            await self.db.commit()
            logger.info("✅ Import transaction committed successfully")
            
        except Exception as e:
            logger.error(f"❌ Transaction failed, rolling back: {e}")
            await self._safe_rollback()
            raise DatabaseError(f"Transaction failed: {str(e)}")
            
        finally:
            self._transaction_active = False
    
    async def _safe_rollback(self) -> None:
        """
        Safely rollback the current transaction.
        """
        if self._rollback_performed:
            logger.warning("Rollback already performed, skipping")
            return
            
        try:
            await self.db.rollback()
            self._rollback_performed = True
            logger.info("✅ Transaction rolled back successfully")
        except Exception as rollback_error:
            logger.error(f"❌ Failed to rollback transaction: {rollback_error}")
            raise DatabaseError(f"Failed to rollback transaction: {str(rollback_error)}")
    
    async def flush(self) -> None:
        """
        Flush changes to the database without committing.
        """
        try:
            await self.db.flush()
            logger.debug("✅ Database session flushed")
        except Exception as e:
            logger.error(f"❌ Failed to flush database session: {e}")
            raise DatabaseError(f"Failed to flush session: {str(e)}")
    
    async def commit(self) -> None:
        """
        Commit the current transaction.
        """
        try:
            await self.db.commit()
            logger.info("✅ Transaction committed manually")
        except Exception as e:
            logger.error(f"❌ Failed to commit transaction: {e}")
            await self._safe_rollback()
            raise DatabaseError(f"Failed to commit transaction: {str(e)}")
    
    async def rollback(self) -> None:
        """
        Rollback the current transaction.
        """
        await self._safe_rollback()
    
    @asynccontextmanager
    async def savepoint(self, name: str) -> AsyncContextManager[None]:
        """
        Context manager for handling savepoints within transactions.
        
        Args:
            name: Name of the savepoint
        """
        try:
            logger.info(f"🔄 Creating savepoint: {name}")
            
            # Create savepoint
            await self.db.execute(f"SAVEPOINT {name}")
            
            yield
            
            # Release savepoint (implicit success)
            await self.db.execute(f"RELEASE SAVEPOINT {name}")
            logger.info(f"✅ Savepoint {name} released successfully")
            
        except Exception as e:
            logger.error(f"❌ Savepoint {name} failed, rolling back: {e}")
            
            try:
                await self.db.execute(f"ROLLBACK TO SAVEPOINT {name}")
                logger.info(f"✅ Rolled back to savepoint {name}")
            except Exception as rollback_error:
                logger.error(f"❌ Failed to rollback to savepoint {name}: {rollback_error}")
                
            raise DatabaseError(f"Savepoint {name} failed: {str(e)}")
    
    async def refresh(self, obj: Any) -> None:
        """
        Refresh an object from the database.
        
        Args:
            obj: Object to refresh
        """
        try:
            await self.db.refresh(obj)
            logger.debug(f"✅ Object refreshed: {type(obj).__name__}")
        except Exception as e:
            logger.error(f"❌ Failed to refresh object: {e}")
            raise DatabaseError(f"Failed to refresh object: {str(e)}")
    
    def is_transaction_active(self) -> bool:
        """
        Check if a transaction is currently active.
        
        Returns:
            bool: True if transaction is active
        """
        return self._transaction_active
    
    def was_rollback_performed(self) -> bool:
        """
        Check if a rollback was performed.
        
        Returns:
            bool: True if rollback was performed
        """
        return self._rollback_performed
    
    async def execute_with_retry(
        self, 
        operation: callable, 
        max_retries: int = 3,
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: The operation to execute
            max_retries: Maximum number of retry attempts
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🔄 Executing operation (attempt {attempt + 1}/{max_retries + 1})")
                result = await operation(*args, **kwargs)
                logger.info(f"✅ Operation succeeded on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ Operation failed on attempt {attempt + 1}: {e}")
                
                if attempt < max_retries:
                    # Try to rollback before retry
                    try:
                        await self._safe_rollback()
                    except Exception:
                        pass  # Ignore rollback errors during retry
                else:
                    logger.error(f"❌ Operation failed after {max_retries + 1} attempts")
                    break
        
        # All retries exhausted
        if last_exception:
            raise DatabaseError(f"Operation failed after {max_retries + 1} attempts: {str(last_exception)}")
        else:
            raise DatabaseError(f"Operation failed after {max_retries + 1} attempts")
    
    async def validate_transaction_state(self) -> Dict[str, Any]:
        """
        Validate the current transaction state.
        
        Returns:
            Dict containing transaction state information
        """
        try:
            # Check if we're in a transaction
            in_transaction = self.db.in_transaction()
            
            return {
                "in_transaction": in_transaction,
                "transaction_active": self._transaction_active,
                "rollback_performed": self._rollback_performed,
                "is_valid": in_transaction == self._transaction_active
            }
            
        except Exception as e:
            logger.error(f"Failed to validate transaction state: {e}")
            return {
                "in_transaction": False,
                "transaction_active": self._transaction_active,
                "rollback_performed": self._rollback_performed,
                "is_valid": False,
                "error": str(e)
            }