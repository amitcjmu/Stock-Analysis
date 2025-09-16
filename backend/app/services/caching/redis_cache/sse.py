"""
Server-Sent Events (SSE) client registry operations for Redis.

Handles SSE client registration and management with fallback for Upstash.
"""

import json
from datetime import datetime
from typing import List

from app.core.logging import get_logger

from .utils import redis_fallback

logger = get_logger(__name__)


class RedisSSEMixin:
    """Mixin for Redis SSE operations"""

    async def register_sse_client(self, client_id: str, flow_id: str) -> bool:
        """Register SSE client (uses regular key-value, not pub/sub)"""
        if self.client_type == "upstash":
            # Upstash doesn't support pub/sub, use key-value instead
            key = f"sse:client:{client_id}"
            return await self.set(
                key,
                {"flow_id": flow_id, "connected_at": datetime.utcnow().isoformat()},
                ttl=3600,
            )
        else:
            # For Redis with pub/sub support
            try:
                # Store client info
                key = f"sse:client:{client_id}"
                await self.set(
                    key,
                    {"flow_id": flow_id, "connected_at": datetime.utcnow().isoformat()},
                    ttl=3600,
                )

                # Publish connection event
                if hasattr(self.client, "publish"):
                    await self.client.publish(
                        f"sse:flow:{flow_id}",
                        json.dumps(
                            {"event": "client_connected", "client_id": client_id}
                        ),
                    )
                return True
            except Exception as e:
                logger.error(f"Failed to register SSE client: {e}")
                return False

    @redis_fallback
    async def unregister_sse_client(self, client_id: str) -> bool:
        """Unregister SSE client"""
        key = f"sse:client:{client_id}"
        return await self.delete(key)

    @redis_fallback
    async def get_sse_clients(self, flow_id: str) -> List[str]:
        """Get all SSE clients for a flow (scan-based for Upstash compatibility)"""
        clients = []
        pattern = "sse:client:*"

        try:
            if self.client_type == "upstash":
                # Upstash doesn't support SCAN, need to track clients differently
                # This is a limitation - would need to maintain a separate set of client IDs
                logger.warning("SSE client listing not fully supported with Upstash")
                return []
            else:
                # Use SCAN for other Redis implementations
                cursor = "0"
                while cursor != 0:
                    cursor, keys = await self.client.scan(
                        cursor=cursor, match=pattern, count=100
                    )
                    for key in keys:
                        client_data = await self.get(
                            key.decode() if isinstance(key, bytes) else key
                        )
                        if client_data and client_data.get("flow_id") == flow_id:
                            client_id = key.split(":")[-1]
                            clients.append(client_id)
                    if cursor == "0":
                        break
                return clients
        except Exception as e:
            logger.error(f"Failed to get SSE clients: {e}")
            return []
