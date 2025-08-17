"""
Cache entry data structures and management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata"""

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: int = 3600  # Default TTL of 1 hour
    tags: list = field(default_factory=list)
    priority: int = 1  # Higher number = higher priority

    def __post_init__(self):
        """Post-initialization processing"""
        if isinstance(self.value, (str, bytes)):
            self.size_bytes = len(self.value)
        elif hasattr(self.value, "__sizeof__"):
            self.size_bytes = self.value.__sizeof__()

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        if self.ttl_seconds <= 0:
            return False
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Get the age of the cache entry in seconds"""
        return (datetime.utcnow() - self.created_at).total_seconds()

    @property
    def idle_seconds(self) -> float:
        """Get seconds since last access"""
        return (datetime.utcnow() - self.last_accessed).total_seconds()

    def touch(self):
        """Update last accessed time and increment access count"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
