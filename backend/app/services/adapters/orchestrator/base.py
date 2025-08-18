"""Base classes and enums for adapter orchestration"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OrchestrationStatus(str, Enum):
    """Orchestration execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"


class AdapterStatus(str, Enum):
    """Individual adapter execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class OrchestrationConfig:
    """Configuration for adapter orchestration"""

    max_parallel_adapters: int = 5
    adapter_timeout_seconds: int = 1800  # 30 minutes
    enable_result_deduplication: bool = True
    enable_cross_platform_correlation: bool = True
    resource_limit_per_adapter: Optional[int] = None
    retry_failed_adapters: bool = False
    retry_attempts: int = 1
    retry_delay_seconds: int = 30

    # Performance settings
    memory_limit_mb: int = 2048
    cpu_limit_percent: float = 80.0
    disk_space_threshold_mb: int = 1024

    # Result aggregation settings
    merge_duplicate_assets: bool = True
    confidence_threshold: float = 0.7
    asset_similarity_threshold: float = 0.8
