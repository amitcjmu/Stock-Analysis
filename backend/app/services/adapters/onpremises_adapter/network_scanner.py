"""
Network scanning functionality for On-Premises Platform Adapter
"""

import asyncio
import socket
import time
import re
import platform
from typing import Optional, List, Dict, Any
from datetime import datetime
from ipaddress import IPv4Network, IPv4Address, AddressValueError

from .models import DiscoveredHost, OnPremisesCredentials


class NetworkScanner:
    """Handles network scanning operations including ping, port scanning, and host discovery"""
    
    def __init__(self, logger):
        self.logger = logger
        self._scanning_semaphore = None
        
    async def perform_host_discovery(self, creds: OnPremisesCredentials, 
                                   network_ranges: List[IPv4Network], 
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform network host discovery using ping and ARP"""
        try:
            self._scanning_semaphore = asyncio.Semaphore(creds.max_concurrent_scans)
            discovered_hosts = []
            
            # Collect all IP addresses to scan
            all_ips = []
            for network in network_ranges:
                # Limit scan size for performance
                hosts = list(network.hosts())
                max_hosts = config.get("max_hosts_per_network", 1000)
                if len(hosts) > max_hosts:
                    self.logger.warning(f"Network {network} has {len(hosts)} hosts, limiting to {max_hosts}")
                    hosts = hosts[:max_hosts]
                all_ips.extend([str(ip) for ip in hosts])
                
            self.logger.info(f"Scanning {len(all_ips)} IP addresses for host discovery")
            
            # Perform concurrent ping scanning
            ping_tasks = [self._ping_and_gather_info(ip, creds) for ip in all_ips]
            
            # Process results as they complete
            for task in asyncio.as_completed(ping_tasks):
                try:
                    host_info = await task
                    if host_info:
                        discovered_hosts.append(host_info)
                except Exception as e:
                    self.logger.debug(f"Host discovery task failed: {str(e)}")
                    
            return {
                "discovered_hosts": [host.__dict__ for host in discovered_hosts],
                "total_scanned": len(all_ips),
                "total_discovered": len(discovered_hosts),
                "discovery_method": "ping_sweep"
            }
            
        except Exception as e:
            raise Exception(f"Host discovery failed: {str(e)}")
            
    async def _ping_and_gather_info(self, ip: str, creds: OnPremisesCredentials) -> Optional[DiscoveredHost]:
        """Ping a host and gather basic information"""
        async with self._scanning_semaphore:
            try:
                # Ping the host
                ping_result = await self.ping_host(ip, creds.timeout)
                if not ping_result:
                    return None
                    
                # Create host object
                host = DiscoveredHost(
                    ip_address=ip,
                    discovery_timestamp=datetime.utcnow(),
                    response_time=ping_result
                )
                
                # Try to resolve hostname
                try:
                    hostname = await self._resolve_hostname(ip, creds.timeout)
                    if hostname and hostname != ip:
                        host.hostname = hostname
                except Exception:
                    pass
                    
                # Try to get MAC address (for local network)
                try:
                    mac_address = await self._get_mac_address(ip)
                    if mac_address:
                        host.mac_address = mac_address
                except Exception:
                    pass
                    
                return host
                
            except Exception as e:
                self.logger.debug(f"Error gathering info for {ip}: {str(e)}")
                return None
                
    async def ping_host(self, ip: str, timeout: int) -> Optional[float]:
        """Ping a host and return response time if successful"""
        try:
            # Determine ping command based on OS
            system = platform.system().lower()
            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
                
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout + 5
                )
                end_time = time.time()
                
                if process.returncode == 0:
                    return end_time - start_time
                    
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                
        except Exception as e:
            self.logger.debug(f"Ping failed for {ip}: {str(e)}")
            
        return None
        
    async def _resolve_hostname(self, ip: str, timeout: int) -> Optional[str]:
        """Resolve hostname for IP address"""
        try:
            # Use asyncio-compatible hostname resolution
            loop = asyncio.get_event_loop()
            hostname, _, _ = await asyncio.wait_for(
                loop.run_in_executor(None, socket.gethostbyaddr, ip),
                timeout=timeout
            )
            return hostname
        except Exception:
            return None
            
    async def _get_mac_address(self, ip: str) -> Optional[str]:
        """Get MAC address for IP (works only for local network)"""
        try:
            system = platform.system().lower()
            if system == "windows":
                cmd = ["arp", "-a", ip]
            else:
                cmd = ["arp", "-n", ip]
                
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                # Parse MAC address from ARP output
                mac_pattern = r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}'
                match = re.search(mac_pattern, output)
                if match:
                    return match.group(0)
                    
        except Exception:
            pass
            
        return None
        
    async def scan_ports(self, ip: str, ports: List[int], timeout: int) -> List[int]:
        """Scan ports on a host and return list of open ports"""
        open_ports = []
        
        # Limit concurrent port scans per host
        semaphore = asyncio.Semaphore(20)
        
        async def scan_port(port):
            async with semaphore:
                try:
                    # Create connection with timeout
                    future = asyncio.open_connection(ip, port)
                    reader, writer = await asyncio.wait_for(future, timeout=timeout)
                    writer.close()
                    await writer.wait_closed()
                    return port
                except Exception:
                    return None
                    
        # Scan all ports concurrently
        port_tasks = [scan_port(port) for port in ports]
        results = await asyncio.gather(*port_tasks, return_exceptions=True)
        
        # Collect open ports
        for result in results:
            if isinstance(result, int):
                open_ports.append(result)
                
        return sorted(open_ports)