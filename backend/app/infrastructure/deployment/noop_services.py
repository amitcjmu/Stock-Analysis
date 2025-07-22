"""
No-operation service implementations for local/disconnected deployments.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class NoOpExternalAPIService:
    """
    No-operation external API service for disconnected deployments.
    """
    
    def __init__(self):
        """Initialize no-op external API service."""
        self._mock_data: Dict[str, Any] = {}
        logger.info("Initialized NoOpExternalAPIService")
    
    async def call_api(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Simulate API call with mock response.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request data
            headers: Request headers
            
        Returns:
            Mock response data
        """
        logger.debug(f"[NoOp] API call: {method} {endpoint}")
        
        # Return mock responses based on endpoint
        if "auth" in endpoint:
            return {
                "status": "success",
                "token": "noop_token_12345",
                "expires_in": 3600
            }
        elif "user" in endpoint:
            return {
                "id": "noop_user_1",
                "name": "NoOp User",
                "email": "noop@example.com"
            }
        elif "data" in endpoint:
            return {
                "data": [],
                "total": 0,
                "page": 1
            }
        else:
            return {
                "status": "ok",
                "message": "NoOp response",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def stream_api(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Simulate streaming API response.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Yields:
            Mock streamed data
        """
        logger.debug(f"[NoOp] Stream API: {endpoint}")
        
        # Simulate streaming response
        for i in range(3):
            await asyncio.sleep(0.1)
            yield {
                "chunk": i,
                "data": f"Mock stream data {i}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> bool:
        """Always healthy for no-op."""
        return True


class NoOpNotificationService:
    """
    No-operation notification service for local deployments.
    """
    
    def __init__(self):
        """Initialize no-op notification service."""
        self._notifications: List[Dict[str, Any]] = []
        logger.info("Initialized NoOpNotificationService")
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> bool:
        """
        Log email instead of sending.
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            html: Optional HTML body
            
        Returns:
            Always True
        """
        notification = {
            "type": "email",
            "to": to,
            "subject": subject,
            "body": body,
            "html": html,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._notifications.append(notification)
        logger.info(f"[NoOp] Email logged: to={to}, subject={subject}")
        
        return True
    
    async def send_sms(
        self,
        to: str,
        message: str
    ) -> bool:
        """
        Log SMS instead of sending.
        
        Args:
            to: Phone number
            message: SMS message
            
        Returns:
            Always True
        """
        notification = {
            "type": "sms",
            "to": to,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._notifications.append(notification)
        logger.info(f"[NoOp] SMS logged: to={to}")
        
        return True
    
    async def send_push(
        self,
        user_id: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log push notification instead of sending.
        
        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
            data: Additional data
            
        Returns:
            Always True
        """
        notification = {
            "type": "push",
            "user_id": user_id,
            "title": title,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._notifications.append(notification)
        logger.info(f"[NoOp] Push notification logged: user_id={user_id}, title={title}")
        
        return True
    
    def get_notifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logged notifications for debugging."""
        return self._notifications[-limit:]
    
    async def health_check(self) -> bool:
        """Always healthy for no-op."""
        return True


class NoOpQueueService:
    """
    No-operation queue service for local deployments.
    """
    
    def __init__(self):
        """Initialize no-op queue service."""
        self._queues: Dict[str, List[Dict[str, Any]]] = {}
        self._handlers: Dict[str, Callable] = {}
        logger.info("Initialized NoOpQueueService")
    
    async def enqueue(
        self,
        queue_name: str,
        message: Dict[str, Any],
        delay_seconds: Optional[int] = None
    ) -> str:
        """
        Add message to in-memory queue.
        
        Args:
            queue_name: Name of the queue
            message: Message data
            delay_seconds: Optional delay (ignored)
            
        Returns:
            Message ID
        """
        if queue_name not in self._queues:
            self._queues[queue_name] = []
        
        message_id = f"msg_{len(self._queues[queue_name])}"
        self._queues[queue_name].append({
            "id": message_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "delay_seconds": delay_seconds
        })
        
        logger.debug(f"[NoOp] Enqueued message to {queue_name}: {message_id}")
        
        # Process immediately if handler exists
        if queue_name in self._handlers:
            await self._process_message(queue_name, message)
        
        return message_id
    
    async def dequeue(
        self,
        queue_name: str,
        max_messages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get messages from queue.
        
        Args:
            queue_name: Name of the queue
            max_messages: Maximum messages to retrieve
            
        Returns:
            List of messages
        """
        if queue_name not in self._queues:
            return []
        
        messages = self._queues[queue_name][:max_messages]
        self._queues[queue_name] = self._queues[queue_name][max_messages:]
        
        logger.debug(f"[NoOp] Dequeued {len(messages)} messages from {queue_name}")
        return messages
    
    def register_handler(
        self,
        queue_name: str,
        handler: Callable
    ) -> None:
        """
        Register a message handler.
        
        Args:
            queue_name: Name of the queue
            handler: Async function to handle messages
        """
        self._handlers[queue_name] = handler
        logger.info(f"[NoOp] Registered handler for queue: {queue_name}")
    
    async def _process_message(
        self,
        queue_name: str,
        message: Dict[str, Any]
    ) -> None:
        """Process message with registered handler."""
        handler = self._handlers.get(queue_name)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"[NoOp] Error processing message: {e}")
    
    def get_queue_size(self, queue_name: str) -> int:
        """Get number of messages in queue."""
        return len(self._queues.get(queue_name, []))
    
    async def health_check(self) -> bool:
        """Always healthy for no-op."""
        return True


class NoOpCacheService:
    """
    No-operation cache service for local deployments.
    """
    
    def __init__(self):
        """Initialize no-op cache service."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized NoOpCacheService")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        item = self._cache.get(key)
        if item:
            # Check expiration
            if item.get("expires_at"):
                if datetime.fromisoformat(item["expires_at"]) < datetime.utcnow():
                    del self._cache[key]
                    return None
            
            logger.debug(f"[NoOp] Cache hit: {key}")
            return item["value"]
        
        logger.debug(f"[NoOp] Cache miss: {key}")
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        item = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if ttl_seconds:
            expires_at = datetime.utcnow().timestamp() + ttl_seconds
            item["expires_at"] = datetime.fromtimestamp(expires_at).isoformat()
        
        self._cache[key] = item
        logger.debug(f"[NoOp] Cached: {key}")
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"[NoOp] Cache deleted: {key}")
            return True
        
        return False
    
    async def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("[NoOp] Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "keys": list(self._cache.keys())
        }
    
    async def health_check(self) -> bool:
        """Always healthy for no-op."""
        return True


class NoOpSearchService:
    """
    No-operation search service for local deployments.
    """
    
    def __init__(self):
        """Initialize no-op search service."""
        self._documents: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("Initialized NoOpSearchService")
    
    async def index_document(
        self,
        index_name: str,
        document_id: str,
        document: Dict[str, Any]
    ) -> None:
        """
        Index a document.
        
        Args:
            index_name: Name of the index
            document_id: Document ID
            document: Document data
        """
        if index_name not in self._documents:
            self._documents[index_name] = []
        
        # Remove existing document with same ID
        self._documents[index_name] = [
            doc for doc in self._documents[index_name]
            if doc.get("_id") != document_id
        ]
        
        # Add new document
        doc_with_id = {"_id": document_id, **document}
        self._documents[index_name].append(doc_with_id)
        
        logger.debug(f"[NoOp] Indexed document: {index_name}/{document_id}")
    
    async def search(
        self,
        index_name: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents (simple substring match).
        
        Args:
            index_name: Name of the index
            query: Search query
            filters: Optional filters
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        if index_name not in self._documents:
            return []
        
        results = []
        query_lower = query.lower()
        
        for doc in self._documents[index_name]:
            # Simple substring search
            doc_str = json.dumps(doc).lower()
            if query_lower in doc_str:
                # Apply filters
                if filters:
                    match = True
                    for key, value in filters.items():
                        if doc.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                results.append(doc)
                
                if len(results) >= limit:
                    break
        
        logger.debug(f"[NoOp] Search found {len(results)} results for: {query}")
        return results
    
    async def delete_document(
        self,
        index_name: str,
        document_id: str
    ) -> bool:
        """
        Delete a document.
        
        Args:
            index_name: Name of the index
            document_id: Document ID
            
        Returns:
            True if deleted
        """
        if index_name not in self._documents:
            return False
        
        original_count = len(self._documents[index_name])
        self._documents[index_name] = [
            doc for doc in self._documents[index_name]
            if doc.get("_id") != document_id
        ]
        
        deleted = len(self._documents[index_name]) < original_count
        if deleted:
            logger.debug(f"[NoOp] Deleted document: {index_name}/{document_id}")
        
        return deleted
    
    async def health_check(self) -> bool:
        """Always healthy for no-op."""
        return True