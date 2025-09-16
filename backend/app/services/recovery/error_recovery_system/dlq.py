"""
Dead Letter Queue for error recovery system.

Manages failed operations that cannot be automatically recovered.
"""

import asyncio
from collections import deque
from datetime import datetime
from typing import Any, Dict, List

from app.core.logging import get_logger

from .models import RecoveryOperation

logger = get_logger(__name__)


class DeadLetterQueue:
    """Dead letter queue for failed operations that cannot be recovered"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.items: deque = deque(maxlen=max_size)
        self.lock = asyncio.Lock()

    async def add_item(self, operation: RecoveryOperation, final_error: str):
        """Add a failed operation to the dead letter queue"""
        async with self.lock:
            dead_letter_item = {
                "operation_id": operation.operation_id,
                "operation_data": operation.to_dict(),
                "final_error": final_error,
                "added_at": datetime.utcnow().isoformat(),
                "retry_attempts_made": operation.retry_count,
            }

            self.items.append(dead_letter_item)

        logger.error(
            f"Added operation {operation.operation_id} to dead letter queue "
            f"after {operation.retry_count} attempts: {final_error}"
        )

    async def get_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get items from the dead letter queue"""
        async with self.lock:
            return list(self.items)[-limit:] if limit else list(self.items)

    async def remove_item(self, operation_id: str) -> bool:
        """Remove an item from the dead letter queue"""
        async with self.lock:
            for i, item in enumerate(self.items):
                if item["operation_id"] == operation_id:
                    del self.items[i]
                    return True
            return False

    async def clear(self) -> int:
        """Clear all items from the dead letter queue"""
        async with self.lock:
            count = len(self.items)
            self.items.clear()
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get dead letter queue statistics"""
        return {
            "total_items": len(self.items),
            "max_size": self.max_size,
            "utilization": len(self.items) / self.max_size * 100,
        }
