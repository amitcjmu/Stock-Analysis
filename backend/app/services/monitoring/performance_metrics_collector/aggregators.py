"""
Metrics aggregation classes for performance metrics collection.

This module contains the core metric aggregation classes including Counter,
Gauge, and Histogram implementations. These classes handle the actual metric
data collection, storage, and retrieval with thread-safe operations.
"""

import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional

from .base import HistogramBucket, MetricSample


class Counter:
    """Counter metric - monotonically increasing value"""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment counter by amount"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += amount

    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values.get(label_key, 0.0)

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key from labels"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def get_samples(self) -> List[MetricSample]:
        """Get all samples for Prometheus export"""
        samples = []
        with self._lock:
            for label_key, value in self._values.items():
                labels = {}
                if label_key:
                    for pair in label_key.split(","):
                        k, v = pair.split("=", 1)
                        labels[k] = v
                samples.append(
                    MetricSample(value=value, timestamp=time.time(), labels=labels)
                )
        return samples


class Gauge:
    """Gauge metric - value that can go up and down"""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set gauge to specific value"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment gauge by amount"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += amount

    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Decrement gauge by amount"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] -= amount

    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values.get(label_key, 0.0)

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key from labels"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def get_samples(self) -> List[MetricSample]:
        """Get all samples for Prometheus export"""
        samples = []
        with self._lock:
            for label_key, value in self._values.items():
                labels = {}
                if label_key:
                    for pair in label_key.split(","):
                        k, v = pair.split("=", 1)
                        labels[k] = v
                samples.append(
                    MetricSample(value=value, timestamp=time.time(), labels=labels)
                )
        return samples


class Histogram:
    """Histogram metric for response time distribution tracking"""

    # Default buckets optimized for auth performance (in seconds)
    DEFAULT_BUCKETS = [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")]

    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = buckets or self.DEFAULT_BUCKETS

        # Initialize buckets for each label combination
        self._buckets: Dict[str, List[HistogramBucket]] = defaultdict(
            lambda: [HistogramBucket(b) for b in self.buckets]
        )
        self._counts: Dict[str, int] = defaultdict(int)
        self._sums: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record an observation in the histogram"""
        label_key = self._make_label_key(labels)

        with self._lock:
            # Update count and sum
            self._counts[label_key] += 1
            self._sums[label_key] += value

            # Update buckets
            for bucket in self._buckets[label_key]:
                if value <= bucket.upper_bound:
                    bucket.increment()

    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get total number of observations"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._counts.get(label_key, 0)

    def get_sum(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get sum of all observed values"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._sums.get(label_key, 0.0)

    def get_average(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get average of all observed values"""
        count = self.get_count(labels)
        if count == 0:
            return 0.0
        return self.get_sum(labels) / count

    def get_percentile(
        self, percentile: float, labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Estimate percentile from histogram buckets"""
        label_key = self._make_label_key(labels)
        total_count = self.get_count(labels)

        if total_count == 0:
            return 0.0

        target_count = total_count * (percentile / 100.0)
        cumulative_count = 0

        with self._lock:
            buckets = self._buckets.get(label_key, [])
            for i, bucket in enumerate(buckets):
                cumulative_count += bucket.count
                if cumulative_count >= target_count:
                    if i == 0:
                        return bucket.upper_bound
                    # Linear interpolation between buckets
                    prev_bucket = buckets[i - 1]
                    prev_count = cumulative_count - bucket.count
                    ratio = (
                        (target_count - prev_count) / bucket.count
                        if bucket.count > 0
                        else 0
                    )
                    return prev_bucket.upper_bound + ratio * (
                        bucket.upper_bound - prev_bucket.upper_bound
                    )

        return self.buckets[-1] if self.buckets else 0.0

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key from labels"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def get_samples(self) -> List[MetricSample]:
        """Get all samples for Prometheus export"""
        samples = []
        with self._lock:
            for label_key in self._counts.keys():
                labels = {}
                if label_key:
                    for pair in label_key.split(","):
                        k, v = pair.split("=", 1)
                        labels[k] = v

                # Add count and sum samples
                samples.append(
                    MetricSample(
                        value=self._counts[label_key],
                        timestamp=time.time(),
                        labels={**labels, "__name__": f"{self.name}_count"},
                    )
                )
                samples.append(
                    MetricSample(
                        value=self._sums[label_key],
                        timestamp=time.time(),
                        labels={**labels, "__name__": f"{self.name}_sum"},
                    )
                )

                # Add bucket samples
                for bucket in self._buckets[label_key]:
                    bucket_labels = {**labels, "le": str(bucket.upper_bound)}
                    samples.append(
                        MetricSample(
                            value=bucket.count,
                            timestamp=time.time(),
                            labels={**bucket_labels, "__name__": f"{self.name}_bucket"},
                        )
                    )

        return samples
