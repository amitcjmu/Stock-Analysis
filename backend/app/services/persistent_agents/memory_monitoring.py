"""
Memory Monitoring Module

This module contains memory monitoring and statistics functionality extracted from
tenant_scoped_agent_pool.py to reduce file length and improve maintainability.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
import threading
from datetime import datetime, timedelta

# Make psutil optional - not critical for core functionality
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "psutil not available - memory monitoring disabled. Install with: pip install psutil"
    )


logger = logging.getLogger(__name__)


class MemoryMonitoring:
    """Handles memory monitoring and automatic cleanup for agent pools"""

    _monitoring_thread = None
    _monitoring_active = False

    @classmethod
    def get_current_memory_usage(cls) -> float:
        """Get current memory usage percentage"""
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil not available - returning 0% memory usage")
            return 0.0

        try:
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0

    @classmethod
    def schedule_automatic_cleanup(cls):
        """Schedule automatic cleanup to run every 6 hours"""

        def run_cleanup():
            while cls._monitoring_active:
                try:
                    # Run async cleanup in background thread with proper event loop handling
                    import asyncio

                    # Import here to avoid circular imports
                    from .tenant_scoped_agent_pool import TenantScopedAgentPool

                    # Create a new event loop for this background thread
                    # This is the proper way to handle async code in background threads
                    loop = asyncio.new_event_loop()
                    try:
                        # Set the event loop for this thread
                        asyncio.set_event_loop(loop)

                        # Run the async cleanup function
                        loop.run_until_complete(
                            TenantScopedAgentPool.cleanup_idle_pools()
                        )

                        logger.info("✅ Automatic agent pool cleanup completed")

                    finally:
                        # Always close the loop to prevent resource leaks
                        loop.close()
                        # Clear the event loop for this thread
                        asyncio.set_event_loop(None)

                except Exception as e:
                    logger.error(f"❌ Automatic cleanup failed: {e}")

                # Wait 6 hours (21600 seconds) before next cleanup
                for _ in range(216):  # Check every minute for 6 hours
                    if not cls._monitoring_active:
                        break
                    threading.Event().wait(60)  # Wait 1 minute

        if not cls._monitoring_active:
            cls._monitoring_active = True
            cls._monitoring_thread = threading.Thread(target=run_cleanup, daemon=True)
            cls._monitoring_thread.start()
            logger.info("🔄 Started automatic agent pool cleanup scheduler")

    @classmethod
    def start_memory_monitoring(cls):
        """Start memory monitoring and automatic cleanup"""
        if cls._monitoring_active:
            logger.info("Memory monitoring already active")
            return

        logger.info("🔍 Starting memory monitoring and automatic cleanup")
        cls.schedule_automatic_cleanup()

        # Register cleanup on exit
        import atexit

        atexit.register(cls.stop_memory_monitoring)

    @classmethod
    def stop_memory_monitoring(cls):
        """Stop memory monitoring"""
        cls._monitoring_active = False
        if cls._monitoring_thread and cls._monitoring_thread.is_alive():
            logger.info("🛑 Stopping memory monitoring")
            cls._monitoring_thread.join(timeout=5)

    @classmethod
    async def cleanup_idle_pools(cls, max_idle_hours: int = 24):
        """Clean up idle agent pools to free memory"""
        try:
            # Import here to avoid circular imports
            from .tenant_scoped_agent_pool import TenantScopedAgentPool

            cleanup_threshold = datetime.now() - timedelta(hours=max_idle_hours)
            pools_cleaned = 0

            # Create a copy of pool keys to avoid dict modification during iteration
            pool_keys = list(TenantScopedAgentPool._agent_pools.keys())

            for pool_key in pool_keys:
                pool_data = TenantScopedAgentPool._agent_pools.get(pool_key)
                if not pool_data:
                    continue

                pool_last_used = pool_data.get("last_used")
                if pool_last_used and pool_last_used < cleanup_threshold:
                    # Remove the idle pool
                    del TenantScopedAgentPool._agent_pools[pool_key]
                    pools_cleaned += 1

                    client_id, engagement_id = pool_key
                    logger.info(
                        f"🗑️ Cleaned up idle agent pool for client={client_id}, "
                        f"engagement={engagement_id} (idle for {max_idle_hours}+ hours)"
                    )

            if pools_cleaned > 0:
                memory_usage = cls.get_current_memory_usage()
                logger.info(
                    f"✅ Cleanup completed: {pools_cleaned} idle pools removed. "
                    f"Memory usage: {memory_usage:.1f}%"
                )
            else:
                logger.info("ℹ️ No idle pools found for cleanup")

        except Exception as e:
            logger.error(f"❌ Pool cleanup failed: {e}")


async def validate_agent_pool_health() -> dict:
    """Validate health of all agent pools"""
    try:
        # Import here to avoid circular imports
        from .tenant_scoped_agent_pool import TenantScopedAgentPool

        stats = await TenantScopedAgentPool.get_pool_statistics()

        total_pools = len(stats)
        healthy_pools = sum(1 for stat in stats if stat.agents)
        memory_usage = MemoryMonitoring.get_current_memory_usage()

        return {
            "status": "healthy" if healthy_pools == total_pools else "degraded",
            "total_pools": total_pools,
            "healthy_pools": healthy_pools,
            "memory_usage_percent": memory_usage,
            "timestamp": datetime.now().isoformat(),
            "pools": [
                {
                    "client_account_id": stat.client_account_id,
                    "engagement_id": stat.engagement_id,
                    "agent_count": stat.agent_count,
                    "total_executions": stat.total_executions,
                }
                for stat in stats
            ],
        }
    except Exception as e:
        logger.error(f"❌ Agent pool health validation failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
