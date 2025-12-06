"""
Synchronous wrappers for async operations

Provides sync execution wrappers for use in synchronous contexts.
"""

import asyncio
import concurrent.futures
from typing import Optional

import nest_asyncio


def run_async_in_sync_context(coroutine):
    """
    Run an async coroutine in a sync context.

    Handles running event loops and uses ThreadPoolExecutor when necessary.
    """
    nest_asyncio.apply()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coroutine)
                return future.result()
        else:
            return asyncio.run(coroutine)
    except RuntimeError:
        return asyncio.run(coroutine)


class SyncWrapperMixin:
    """Mixin providing synchronous wrappers for async methods"""

    def execute_sync(
        self,
        asset_id: str,
        catalog_version_id: Optional[str] = None,
        tenant_version_id: Optional[str] = None,
        technology: Optional[str] = None,
        version: Optional[str] = None,
        confidence_score: float = 0.9,
        matched_by: str = "agent",
    ) -> str:
        """Synchronous wrapper for execute_async"""
        # OBSERVABILITY: tracking not needed - Agent tool internal execution
        return run_async_in_sync_context(
            self.execute_async(
                asset_id,
                catalog_version_id,
                tenant_version_id,
                technology,
                version,
                confidence_score,
                matched_by,
            )
        )

    def get_asset_products_sync(self, asset_id: str) -> str:
        """Synchronous wrapper for get_asset_products_async"""
        return run_async_in_sync_context(self.get_asset_products_async(asset_id))
