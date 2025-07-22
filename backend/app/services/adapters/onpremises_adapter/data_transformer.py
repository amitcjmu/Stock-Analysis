"""
Data transformation for On-Premises Platform Adapter
"""

from datetime import datetime
from typing import Any, Dict, List, Optional



class DataTransformer:
    """Handles data transformation to normalized format"""
    
    def __init__(self, logger):
        self.logger = logger
        
    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw on-premises data to normalized format for Discovery Flow
        
        Args:
            raw_data: Raw on-premises data from collection
            
        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        try:
            normalized_data = {
                "platform": "OnPremises",
                "platform_version": "1.0",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
                "metadata": raw_data.get("metadata", {})
            }
            
            # Transform discovered hosts to normalized assets
            if "host_discovery" in raw_data and "discovered_hosts" in raw_data["host_discovery"]:
                for host_data in raw_data["host_discovery"]["discovered_hosts"]:
                    normalized_asset = self._transform_host_to_asset(host_data)
                    if normalized_asset:
                        normalized_data["assets"].append(normalized_asset)
                        
            # Add network topology as infrastructure assets
            if "topology" in raw_data and "network_segments" in raw_data["topology"]:
                for segment in raw_data["topology"]["network_segments"]:
                    network_asset = self._transform_network_to_asset(segment)
                    if network_asset:
                        normalized_data["assets"].append(network_asset)
                        
            # Transform service discovery to dependencies
            if "service_discovery" in raw_data and "service_results" in raw_data["service_discovery"]:
                dependencies = self._transform_services_to_dependencies(raw_data["service_discovery"]["service_results"])
                normalized_data["dependencies"].extend(dependencies)
                
            self.logger.info(f"Transformed {len(normalized_data['assets'])} on-premises assets to normalized format")
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Failed to transform on-premises data: {str(e)}")
            return {
                "platform": "OnPremises",
                "error": f"Data transformation failed: {str(e)}",
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {}
            }
            
    def _transform_host_to_asset(self, host_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform discovered host to normalized asset format"""
        try:
            asset = {
                "platform": "OnPremises",
                "platform_service": "infrastructure",
                "asset_type": "server",
                "unique_id": host_data.get("ip_address"),
                "name": host_data.get("hostname") or host_data.get("ip_address"),
                "environment": "on_premises",
                "ip_addresses": {
                    "primary": host_data.get("ip_address")
                },
                "discovery_method": "network_scanning",
                "discovery_timestamp": host_data.get("discovery_timestamp") or datetime.utcnow().isoformat(),
                "raw_data": host_data
            }
            
            # Add network information
            if host_data.get("mac_address"):
                asset["mac_address"] = host_data["mac_address"]
                
            # Add operating system information
            if host_data.get("operating_system"):
                asset["operating_system"] = host_data["operating_system"]
                
            # Add service information
            if host_data.get("open_ports"):
                asset["network_services"] = {
                    "open_ports": host_data["open_ports"],
                    "total_ports": len(host_data["open_ports"])
                }
                
            if host_data.get("services"):
                asset["services"] = host_data["services"]
                
            # Add performance metrics
            if host_data.get("response_time"):
                asset["performance_metrics"] = {
                    "network_latency_ms": host_data["response_time"] * 1000
                }
                
            # Add detailed information if available
            if host_data.get("snmp_info"):
                asset["snmp_info"] = host_data["snmp_info"]
                
            if host_data.get("ssh_info"):
                asset["ssh_info"] = host_data["ssh_info"]
                
            if host_data.get("wmi_info"):
                asset["wmi_info"] = host_data["wmi_info"]
                
            return asset
            
        except Exception as e:
            self.logger.warning(f"Failed to transform host to asset: {str(e)}")
            return None
            
    def _transform_network_to_asset(self, segment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform network segment to normalized asset format"""
        try:
            asset = {
                "platform": "OnPremises",
                "platform_service": "networking",
                "asset_type": "network",
                "unique_id": segment_data.get("network"),
                "name": f"Network {segment_data.get('network')}",
                "environment": "on_premises",
                "discovery_method": "network_scanning",
                "discovery_timestamp": datetime.utcnow().isoformat(),
                "network_info": {
                    "network_address": segment_data.get("network_address"),
                    "broadcast_address": segment_data.get("broadcast_address"),
                    "netmask": segment_data.get("netmask"),
                    "num_addresses": segment_data.get("num_addresses"),
                    "active_hosts_count": len(segment_data.get("active_hosts", []))
                },
                "raw_data": segment_data
            }
            
            return asset
            
        except Exception as e:
            self.logger.warning(f"Failed to transform network segment to asset: {str(e)}")
            return None
            
    def _transform_services_to_dependencies(self, service_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform service discovery results to dependencies"""
        dependencies = []
        
        try:
            for service_result in service_results:
                ip_address = service_result.get("ip_address")
                services = service_result.get("services", [])
                
                for service in services:
                    dependency = {
                        "source_asset_id": ip_address,
                        "dependency_type": "network_service",
                        "service_name": service.get("service"),
                        "port": service.get("port"),
                        "protocol": service.get("protocol", "tcp"),
                        "service_version": service.get("version"),
                        "service_banner": service.get("banner"),
                        "discovery_method": "port_scanning",
                        "discovery_timestamp": datetime.utcnow().isoformat()
                    }
                    dependencies.append(dependency)
                    
        except Exception as e:
            self.logger.warning(f"Failed to transform services to dependencies: {str(e)}")
            
        return dependencies