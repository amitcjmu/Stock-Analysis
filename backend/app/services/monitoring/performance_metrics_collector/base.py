"""
Base classes, enums, and data structures for performance metrics collection.

This module contains the foundational types and structures used throughout
the performance metrics collection system. All core data types, enums, and
base classes are defined here to ensure consistency and reusability.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Union


class MetricType(str, Enum):
    """Metric type enumeration following Prometheus conventions"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricUnit(str, Enum):
    """Standard metric units"""

    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    BYTES = "bytes"
    PERCENT = "percent"
    COUNT = "count"
    RATE = "rate"


@dataclass
class MetricSample:
    """Individual metric sample with timestamp and labels"""

    value: Union[float, int]
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class HistogramBucket:
    """Histogram bucket for response time distribution tracking"""

    upper_bound: float
    count: int = 0

    def increment(self):
        self.count += 1
