"""
Data models for On-Premises Platform Adapter
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class OnPremisesCredentials:
    """On-premises discovery credentials"""
    # Network scanning
    network_ranges: List[str]  # CIDR ranges to scan
    
    # SSH credentials
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_private_key: Optional[str] = None
    ssh_port: int = 22
    
    # SNMP credentials
    snmp_community: str = "public"
    snmp_version: str = "2c"  # 1, 2c, 3
    snmp_username: Optional[str] = None
    snmp_auth_protocol: Optional[str] = None
    snmp_auth_key: Optional[str] = None
    snmp_priv_protocol: Optional[str] = None
    snmp_priv_key: Optional[str] = None
    
    # WMI credentials (Windows)
    wmi_username: Optional[str] = None
    wmi_password: Optional[str] = None
    wmi_domain: Optional[str] = None
    
    # General settings
    timeout: int = 10
    max_concurrent_scans: int = 50


@dataclass
class DiscoveredHost:
    """Discovered host information"""
    ip_address: str
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    operating_system: Optional[str] = None
    open_ports: List[int] = None
    services: List[Dict[str, Any]] = None
    snmp_info: Optional[Dict[str, Any]] = None
    ssh_info: Optional[Dict[str, Any]] = None
    wmi_info: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    discovery_timestamp: Optional[datetime] = None