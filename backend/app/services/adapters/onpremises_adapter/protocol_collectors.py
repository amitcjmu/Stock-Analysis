"""
Protocol-specific collectors for On-Premises Platform Adapter
"""

from typing import Optional, Dict, Any, List
from .models import OnPremisesCredentials, DiscoveredHost


class ProtocolCollectors:
    """Handles protocol-specific information gathering (SNMP, SSH, WMI)"""
    
    def __init__(self, logger):
        self.logger = logger
        
    async def perform_detailed_info_gathering(self, discovered_hosts: List[DiscoveredHost],
                                            creds: OnPremisesCredentials, 
                                            config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed information gathering using SNMP, SSH, WMI"""
        try:
            detailed_info = []
            
            for host in discovered_hosts:
                host_info = {
                    "ip_address": host.ip_address,
                    "hostname": host.hostname,
                    "detailed_data": {}
                }
                
                # Try SNMP information gathering
                if creds.snmp_community or creds.snmp_username:
                    try:
                        snmp_info = await self.gather_snmp_info(host.ip_address, creds)
                        if snmp_info:
                            host_info["detailed_data"]["snmp"] = snmp_info
                            host.snmp_info = snmp_info
                    except Exception as e:
                        self.logger.debug(f"SNMP gathering failed for {host.ip_address}: {str(e)}")
                        
                # Try SSH information gathering
                if creds.ssh_username and (creds.ssh_password or creds.ssh_private_key):
                    if 22 in (host.open_ports or []):
                        try:
                            ssh_info = await self.gather_ssh_info(host.ip_address, creds)
                            if ssh_info:
                                host_info["detailed_data"]["ssh"] = ssh_info
                                host.ssh_info = ssh_info
                        except Exception as e:
                            self.logger.debug(f"SSH gathering failed for {host.ip_address}: {str(e)}")
                            
                # Try WMI information gathering (Windows)
                if creds.wmi_username and creds.wmi_password:
                    if 135 in (host.open_ports or []) or 445 in (host.open_ports or []):
                        try:
                            wmi_info = await self.gather_wmi_info(host.ip_address, creds)
                            if wmi_info:
                                host_info["detailed_data"]["wmi"] = wmi_info
                                host.wmi_info = wmi_info
                        except Exception as e:
                            self.logger.debug(f"WMI gathering failed for {host.ip_address}: {str(e)}")
                            
                if host_info["detailed_data"]:
                    detailed_info.append(host_info)
                    
            return {
                "detailed_hosts": detailed_info,
                "total_hosts": len(detailed_info),
                "info_sources": ["snmp", "ssh", "wmi", "os_detection"]
            }
            
        except Exception as e:
            raise Exception(f"Detailed info gathering failed: {str(e)}")
            
    async def gather_snmp_info(self, ip: str, creds: OnPremisesCredentials) -> Optional[Dict[str, Any]]:
        """Gather information using SNMP (simplified implementation)"""
        try:
            # This is a simplified implementation
            # In a real implementation, you would use pysnmp library
            
            snmp_info = {
                "community": creds.snmp_community,
                "version": creds.snmp_version,
                "status": "not_implemented",
                "note": "SNMP gathering requires pysnmp library"
            }
            
            # Placeholder for SNMP OIDs that would typically be queried:
            # 1.3.6.1.2.1.1.1.0 - sysDescr (System Description)
            # 1.3.6.1.2.1.1.3.0 - sysUpTime (System Uptime)
            # 1.3.6.1.2.1.1.4.0 - sysContact (System Contact)
            # 1.3.6.1.2.1.1.5.0 - sysName (System Name)
            # 1.3.6.1.2.1.1.6.0 - sysLocation (System Location)
            
            return snmp_info
            
        except Exception as e:
            self.logger.debug(f"SNMP info gathering failed for {ip}: {str(e)}")
            return None
            
    async def gather_ssh_info(self, ip: str, creds: OnPremisesCredentials) -> Optional[Dict[str, Any]]:
        """Gather information using SSH (simplified implementation)"""
        try:
            # This is a simplified implementation
            # In a real implementation, you would use paramiko or asyncssh library
            
            ssh_info = {
                "username": creds.ssh_username,
                "port": creds.ssh_port,
                "status": "not_implemented",
                "note": "SSH gathering requires paramiko or asyncssh library"
            }
            
            # Commands that would typically be executed:
            # uname -a (system information)
            # cat /proc/cpuinfo (CPU information)
            # cat /proc/meminfo (memory information)
            # df -h (disk usage)
            # ps aux (running processes)
            # netstat -tuln (network connections)
            
            return ssh_info
            
        except Exception as e:
            self.logger.debug(f"SSH info gathering failed for {ip}: {str(e)}")
            return None
            
    async def gather_wmi_info(self, ip: str, creds: OnPremisesCredentials) -> Optional[Dict[str, Any]]:
        """Gather information using WMI (simplified implementation)"""
        try:
            # This is a simplified implementation
            # In a real implementation, you would use wmi-client-wrapper or impacket
            
            wmi_info = {
                "username": creds.wmi_username,
                "domain": creds.wmi_domain,
                "status": "not_implemented",
                "note": "WMI gathering requires wmi-client-wrapper or impacket library"
            }
            
            # WMI classes that would typically be queried:
            # Win32_ComputerSystem (system information)
            # Win32_OperatingSystem (OS information)
            # Win32_Processor (CPU information)
            # Win32_PhysicalMemory (memory information)
            # Win32_LogicalDisk (disk information)
            # Win32_Service (services)
            # Win32_Process (processes)
            
            return wmi_info
            
        except Exception as e:
            self.logger.debug(f"WMI info gathering failed for {ip}: {str(e)}")
            return None
            
    async def test_snmp_connectivity(self, creds: OnPremisesCredentials) -> bool:
        """Test SNMP connectivity"""
        try:
            # This would require pysnmp library - for now, return True if credentials provided
            if creds.snmp_community or creds.snmp_username:
                return True
            return False
        except Exception:
            return False
            
    async def test_ssh_connectivity(self, creds: OnPremisesCredentials) -> bool:
        """Test SSH connectivity"""
        try:
            # Return True if SSH credentials are provided
            if creds.ssh_username and (creds.ssh_password or creds.ssh_private_key):
                return True
            return False
        except Exception:
            return False