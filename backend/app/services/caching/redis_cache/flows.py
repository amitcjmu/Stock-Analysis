"""
Flow-related caching operations for Redis.

Handles flow state caching, metadata storage, and atomic flow operations.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

from .serializers import datetime_json_serializer
from .utils import redis_fallback

logger = get_logger(__name__)


class RedisFlowMixin:
    """Mixin for Redis flow-related operations"""

    @redis_fallback
    async def cache_flow_state(
        self, flow_id: str, state: Dict[str, Any], ttl: int = 3600
    ) -> bool:
        """Cache flow state with encryption for sensitive data"""
        key = f"flow:state:{flow_id}"
        # Flow state contains sensitive data like client_account_id, user_id, etc.
        return await self.set_secure(key, state, ttl, force_encrypt=True)

    @redis_fallback
    async def invalidate_flow_cache(self, flow_id: str) -> bool:
        """Invalidate all cached data related to a flow"""
        try:
            keys_to_delete = [
                f"flow:state:{flow_id}",
                f"flow:exists:{flow_id}",
                f"flow:metadata:{flow_id}",
                f"flow:phase:*:{flow_id}",  # Phase results
                f"flow:agent:*:{flow_id}",  # Agent results
                f"lock:flow:{flow_id}",  # Flow locks
                f"lock:flow:status:{flow_id}",  # Status locks
            ]

            if self.client_type == "upstash":
                # Upstash doesn't support pattern deletion, delete known keys
                for key in keys_to_delete:
                    if "*" not in key:
                        self.client.delete(key)
            else:
                # For Redis with SCAN support, find and delete pattern keys
                pipeline = self.client.pipeline()

                for key_pattern in keys_to_delete:
                    if "*" in key_pattern:
                        # Use SCAN to find matching keys
                        cursor = "0"
                        while True:
                            cursor, keys = await self.client.scan(
                                cursor=cursor, match=key_pattern, count=100
                            )
                            for key in keys:
                                pipeline.delete(key)
                            if cursor == "0":
                                break
                    else:
                        pipeline.delete(key_pattern)

                await pipeline.execute()

            logger.info(f"Invalidated all cache entries for flow {flow_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate flow cache: {str(e)}")
            return False

    @redis_fallback
    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get flow state from cache with decryption"""
        key = f"flow:state:{flow_id}"
        return await self.get_secure(key)

    @redis_fallback
    async def register_flow_atomic(
        self,
        flow_id: str,
        flow_type: str,
        flow_data: Dict[str, Any],
        ttl: int = 86400,  # 24 hours
    ) -> bool:
        """
        Atomically register a new flow with all necessary keys.
        This prevents race conditions during flow creation.
        """
        try:
            # Use pipeline for atomic operations where supported
            if self.client_type == "upstash":
                # Upstash doesn't support pipelines, use individual operations
                # But still maintain order and check for conflicts

                # Check if flow already exists (prevent duplicate registration)
                exists_key = f"flow:exists:{flow_id}"
                if self.client.get(exists_key):
                    logger.warning(f"Flow {flow_id} already registered")
                    return False

                # Set all flow-related keys
                success = True

                # 1. Mark flow as existing
                self.client.setex(exists_key, ttl, "1")

                # 2. Store flow metadata
                metadata_key = f"flow:metadata:{flow_id}"
                self.client.setex(
                    metadata_key,
                    ttl,
                    json.dumps(
                        {
                            "flow_type": flow_type,
                            "created_at": datetime.utcnow().isoformat(),
                            "client_id": flow_data.get("client_id"),
                            "engagement_id": flow_data.get("engagement_id"),
                            "user_id": flow_data.get("user_id"),
                        },
                        default=datetime_json_serializer,
                        ensure_ascii=False,
                    ),
                )

                # 3. Initialize flow state
                state_key = f"flow:state:{flow_id}"
                self.client.setex(
                    state_key,
                    ttl,
                    json.dumps(
                        flow_data, default=datetime_json_serializer, ensure_ascii=False
                    ),
                )

                # 4. Add to active flows set
                active_key = f"flows:active:{flow_type}"
                # Upstash doesn't have SADD with TTL, use regular key
                active_flows = self.client.get(active_key)
                if active_flows:
                    active_list = json.loads(active_flows)
                    if flow_id not in active_list:
                        active_list.append(flow_id)
                else:
                    active_list = [flow_id]
                self.client.setex(active_key, ttl, json.dumps(active_list))

                return success

            else:
                # Use pipeline for Redis implementations that support it
                pipeline = self.client.pipeline()

                # Check if flow already exists
                exists_key = f"flow:exists:{flow_id}"
                exists = await self.client.get(exists_key)
                if exists:
                    logger.warning(f"Flow {flow_id} already registered")
                    return False

                # Set all flow-related keys atomically
                pipeline.setex(exists_key, ttl, "1")

                metadata_key = f"flow:metadata:{flow_id}"
                pipeline.setex(
                    metadata_key,
                    ttl,
                    json.dumps(
                        {
                            "flow_type": flow_type,
                            "created_at": datetime.utcnow().isoformat(),
                            "client_id": flow_data.get("client_id"),
                            "engagement_id": flow_data.get("engagement_id"),
                            "user_id": flow_data.get("user_id"),
                        },
                        default=datetime_json_serializer,
                        ensure_ascii=False,
                    ),
                )

                state_key = f"flow:state:{flow_id}"
                pipeline.setex(
                    state_key,
                    ttl,
                    json.dumps(
                        flow_data, default=datetime_json_serializer, ensure_ascii=False
                    ),
                )

                # Add to active flows set
                active_key = f"flows:active:{flow_type}"
                pipeline.sadd(active_key, flow_id)
                pipeline.expire(active_key, ttl)

                # Execute pipeline atomically
                results = await pipeline.execute()
                return all(results)

        except Exception as e:
            logger.error(f"Failed to register flow atomically: {str(e)}")
            return False

    @redis_fallback
    async def unregister_flow_atomic(self, flow_id: str, flow_type: str) -> bool:
        """
        Atomically unregister a flow and clean up all related keys.
        """
        try:
            if self.client_type == "upstash":
                # Manual cleanup for Upstash
                self.client.delete(f"flow:exists:{flow_id}")
                self.client.delete(f"flow:metadata:{flow_id}")
                self.client.delete(f"flow:state:{flow_id}")
                self.client.delete(f"lock:flow:{flow_id}")

                # Remove from active flows
                active_key = f"flows:active:{flow_type}"
                active_flows = self.client.get(active_key)
                if active_flows:
                    active_list = json.loads(active_flows)
                    if flow_id in active_list:
                        active_list.remove(flow_id)
                        self.client.set(active_key, json.dumps(active_list))

                return True

            else:
                # Use pipeline for atomic cleanup
                pipeline = self.client.pipeline()

                pipeline.delete(f"flow:exists:{flow_id}")
                pipeline.delete(f"flow:metadata:{flow_id}")
                pipeline.delete(f"flow:state:{flow_id}")
                pipeline.delete(f"lock:flow:{flow_id}")

                # Remove from active flows set
                active_key = f"flows:active:{flow_type}"
                pipeline.srem(active_key, flow_id)

                results = await pipeline.execute()
                return any(results)  # At least one key was deleted

        except Exception as e:
            logger.error(f"Failed to unregister flow atomically: {str(e)}")
            return False

    @redis_fallback
    async def get_active_flows(self, flow_type: str) -> List[str]:
        """Get list of active flows for a given type"""
        try:
            active_key = f"flows:active:{flow_type}"

            if self.client_type == "upstash":
                # Upstash uses JSON list
                active_flows = self.client.get(active_key)
                return json.loads(active_flows) if active_flows else []
            else:
                # Redis uses SET
                members = await self.client.smembers(active_key)
                return list(members) if members else []

        except Exception as e:
            logger.error(f"Failed to get active flows: {str(e)}")
            return []
