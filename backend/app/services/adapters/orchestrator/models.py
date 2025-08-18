"""Data models for adapter orchestration results"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.collection_flow.adapters import CollectionResponse

from .base import AdapterStatus, OrchestrationStatus


@dataclass
class AdapterExecutionResult:
    """Result of adapter execution"""

    adapter_name: str
    adapter_version: str
    platform: str
    status: AdapterStatus
    response: Optional[CollectionResponse] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    resource_count: int = 0

    @property
    def success(self) -> bool:
        return (
            self.status == AdapterStatus.COMPLETED
            and self.response
            and self.response.success
        )


@dataclass
class OrchestrationResult:
    """Result of orchestrated collection"""

    orchestration_id: str
    status: OrchestrationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Adapter results
    adapter_results: List[AdapterExecutionResult] = field(default_factory=list)
    successful_adapters: int = 0
    failed_adapters: int = 0
    total_adapters: int = 0

    # Aggregated data
    aggregated_data: Optional[Dict[str, Any]] = None
    total_resources: int = 0
    unique_resources: int = 0
    duplicate_resources: int = 0

    # Performance metrics
    peak_memory_usage_mb: Optional[float] = None
    peak_cpu_usage_percent: Optional[float] = None
    disk_usage_mb: Optional[float] = None

    # Summary
    platforms_collected: List[str] = field(default_factory=list)
    collection_methods_used: List[str] = field(default_factory=list)
    error_summary: Optional[Dict[str, Any]] = None
