"""
Backoff algorithms for retry handling.

This module contains various backoff calculation strategies used to determine
delays between retry attempts.
"""

import random

from .base import RetryStrategy


class BackoffCalculator:
    """Calculates delay based on retry strategy and configuration"""

    @staticmethod
    def calculate_delay(
        retry_count: int,
        strategy: RetryStrategy,
        base_delay: float,
        max_delay: float,
        jitter: bool = False,
        jitter_range: float = 0.1,
    ) -> float:
        """
        Calculate delay based on retry strategy

        Args:
            retry_count: Current retry attempt number
            strategy: Retry strategy to use
            base_delay: Base delay in seconds
            max_delay: Maximum delay allowed
            jitter: Whether to apply jitter
            jitter_range: Range of jitter to apply (0.0-1.0)

        Returns:
            Calculated delay in seconds
        """
        if strategy == RetryStrategy.FIXED_DELAY:
            delay = base_delay
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = base_delay * (2**retry_count)
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * (retry_count + 1)
        elif strategy == RetryStrategy.RANDOM_JITTER:
            delay = base_delay + random.uniform(0, base_delay)
        else:
            delay = base_delay

        # Apply max delay limit
        delay = min(delay, max_delay)

        # Apply jitter
        if jitter:
            jitter_amount = delay * jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(delay, 0.1)  # Minimum delay of 0.1 seconds
