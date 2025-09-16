"""
Main Redis cache implementation combining all functional mixins.

Provides the complete RedisCache class with all operations.
"""

from .base import RedisBaseCache
from .failures import RedisFailureMixin
from .flows import RedisFlowMixin
from .imports import RedisImportMixin
from .locking import RedisLockingMixin
from .patterns import RedisPatternMixin
from .sse import RedisSSEMixin


class RedisCache(
    RedisBaseCache,
    RedisLockingMixin,
    RedisFlowMixin,
    RedisImportMixin,
    RedisFailureMixin,
    RedisPatternMixin,
    RedisSSEMixin,
):
    """Unified Redis cache service with multiple backend support"""

    pass  # All functionality is provided by mixins
