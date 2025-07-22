"""
GCP Adapter Data Models

Contains dataclasses and type definitions for GCP adapter operations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class GCPCredentials:
    """GCP credentials configuration"""
    project_id: str
    service_account_key: Dict[str, Any]  # Service account JSON key
    
    
@dataclass
class GCPResourceMetrics:
    """GCP resource performance metrics"""
    resource_id: str
    resource_type: str
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    network_sent_bytes: Optional[float] = None
    network_received_bytes: Optional[float] = None
    disk_read_bytes: Optional[float] = None
    disk_write_bytes: Optional[float] = None
    timestamp: Optional[datetime] = None