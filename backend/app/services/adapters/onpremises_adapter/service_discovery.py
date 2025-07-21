"""
Service discovery and identification for On-Premises Platform Adapter
"""

import asyncio
from typing import List, Dict, Any, Optional

from .models import DiscoveredHost, OnPremisesCredentials
from .network_scanner import NetworkScanner


class ServiceDiscovery:
    """Handles service detection and identification"""
    
    def __init__(self, logger, network_scanner: NetworkScanner):
        self.logger = logger
        self.network_scanner = network_scanner
        self.service_map = {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            111: "RPC",
            135: "RPC/WMI",
            139: "NetBIOS",
            143: "IMAP",
            443: "HTTPS",
            445: "SMB",
            993: "IMAPS",
            995: "POP3S",
            1433: "SQL Server",
            1521: "Oracle",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt"
        }
        
    async def perform_service_discovery(self, discovered_hosts: List[DiscoveredHost], 
                                      creds: OnPremisesCredentials, 
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform service discovery using port scanning"""
        try:
            if not discovered_hosts:
                return {"error": "No hosts discovered for service scanning"}
                
            # Define ports to scan
            common_ports = [
                21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
                1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443
            ]
            
            custom_ports = config.get("custom_ports", [])
            all_ports = list(set(common_ports + custom_ports))
            
            service_results = []
            
            # Scan ports for each discovered host
            for host in discovered_hosts:
                try:
                    open_ports = await self.network_scanner.scan_ports(
                        host.ip_address, all_ports, creds.timeout
                    )
                    if open_ports:
                        host.open_ports = open_ports
                        
                        # Try to identify services
                        services = await self.identify_services(
                            host.ip_address, open_ports, creds.timeout
                        )
                        host.services = services
                        
                        service_results.append({
                            "ip_address": host.ip_address,
                            "hostname": host.hostname,
                            "open_ports": open_ports,
                            "services": services
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Service discovery failed for {host.ip_address}: {str(e)}")
                    
            return {
                "service_results": service_results,
                "ports_scanned": all_ports,
                "hosts_scanned": len(discovered_hosts),
                "hosts_with_services": len(service_results)
            }
            
        except Exception as e:
            raise Exception(f"Service discovery failed: {str(e)}")
            
    async def identify_services(self, ip: str, ports: List[int], timeout: int) -> List[Dict[str, Any]]:
        """Identify services running on open ports"""
        services = []
        
        for port in ports:
            service_name = self.service_map.get(port, "Unknown")
            
            service_info = {
                "port": port,
                "service": service_name,
                "protocol": "tcp"
            }
            
            # Try to get service banner/version
            try:
                banner = await self._get_service_banner(ip, port, timeout)
                if banner:
                    service_info["banner"] = banner
                    service_info["version"] = self._parse_service_version(banner)
            except Exception:
                pass
                
            services.append(service_info)
            
        return services
        
    async def _get_service_banner(self, ip: str, port: int, timeout: int) -> Optional[str]:
        """Get service banner from a port"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            
            # Try to read banner
            try:
                banner_data = await asyncio.wait_for(
                    reader.read(1024),
                    timeout=3
                )
                banner = banner_data.decode('utf-8', errors='ignore').strip()
                
                # For HTTP services, try to get server header
                if port in [80, 8080, 443, 8443]:
                    writer.write(b"HEAD / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
                    await writer.drain()
                    
                    response_data = await asyncio.wait_for(
                        reader.read(2048),
                        timeout=3
                    )
                    response = response_data.decode('utf-8', errors='ignore')
                    
                    # Extract Server header
                    for line in response.split('\n'):
                        if line.lower().startswith('server:'):
                            banner = line.strip()
                            break
                            
            finally:
                writer.close()
                await writer.wait_closed()
                
            return banner if banner else None
            
        except Exception:
            return None
            
    def _parse_service_version(self, banner: str) -> Optional[str]:
        """Parse service version from banner"""
        try:
            # Simple version extraction patterns
            import re
            
            patterns = [
                r'(\d+\.?\d*\.?\d*)',  # Version numbers
                r'Server:\s*(.+)',     # Server header
                r'OpenSSH[_\s]([^\s]+)',  # SSH version
                r'Microsoft[_\s]([^\s]+)',  # Microsoft products
            ]
            
            for pattern in patterns:
                match = re.search(pattern, banner, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
                    
        except Exception:
            pass
            
        return None
        
    async def detect_operating_system(self, host: DiscoveredHost) -> Optional[Dict[str, Any]]:
        """Detect operating system based on available information"""
        try:
            os_info = {
                "detection_method": "port_fingerprinting",
                "confidence": "low"
            }
            
            # Simple OS detection based on open ports and services
            if host.open_ports:
                if 3389 in host.open_ports:  # RDP
                    os_info["os_family"] = "Windows"
                    os_info["confidence"] = "medium"
                elif 22 in host.open_ports and 80 in host.open_ports:  # SSH + HTTP
                    os_info["os_family"] = "Linux/Unix"
                    os_info["confidence"] = "low"
                elif 135 in host.open_ports or 445 in host.open_ports:  # WMI/SMB
                    os_info["os_family"] = "Windows"
                    os_info["confidence"] = "medium"
                elif 161 in host.open_ports:  # SNMP
                    os_info["os_family"] = "Network Device"
                    os_info["confidence"] = "low"
                    
            # Check service banners for more specific detection
            if host.services:
                for service in host.services:
                    banner = service.get("banner", "").lower()
                    if "windows" in banner or "microsoft" in banner:
                        os_info["os_family"] = "Windows"
                        os_info["confidence"] = "high"
                        break
                    elif "linux" in banner or "ubuntu" in banner or "centos" in banner:
                        os_info["os_family"] = "Linux"
                        os_info["confidence"] = "high"
                        break
                    elif "openssh" in banner:
                        os_info["os_family"] = "Linux/Unix"
                        os_info["confidence"] = "medium"
                        break
                        
            return os_info
            
        except Exception as e:
            self.logger.debug(f"OS detection failed for {host.ip_address}: {str(e)}")
            return None