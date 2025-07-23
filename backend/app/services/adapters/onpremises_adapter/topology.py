"""
Network topology discovery for On-Premises Platform Adapter
"""

from ipaddress import AddressValueError, IPv4Address, IPv4Network
from typing import Any, Dict, List

from .models import DiscoveredHost


class TopologyDiscovery:
    """Handles network topology discovery and mapping"""

    def __init__(self, logger):
        self.logger = logger

    async def perform_topology_discovery(
        self,
        network_ranges: List[IPv4Network],
        discovered_hosts: List[DiscoveredHost],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Perform network topology discovery"""
        try:
            topology_info = {
                "network_segments": [],
                "discovered_networks": [],
                "routing_info": {},
                "status": "basic_topology_only",
            }

            # Basic topology based on network ranges
            for network in network_ranges:
                segment_info = {
                    "network": str(network),
                    "network_address": str(network.network_address),
                    "broadcast_address": str(network.broadcast_address),
                    "netmask": str(network.netmask),
                    "num_addresses": network.num_addresses,
                    "active_hosts": [],
                }

                # Add active hosts in this segment
                for host in discovered_hosts:
                    try:
                        host_ip = IPv4Address(host.ip_address)
                        if host_ip in network:
                            segment_info["active_hosts"].append(
                                {
                                    "ip": host.ip_address,
                                    "hostname": host.hostname,
                                    "mac": host.mac_address,
                                    "os": host.operating_system,
                                }
                            )
                    except AddressValueError:
                        continue

                topology_info["network_segments"].append(segment_info)
                topology_info["discovered_networks"].append(str(network))

            # Add summary information
            topology_info["summary"] = {
                "total_networks": len(network_ranges),
                "total_hosts_discovered": len(discovered_hosts),
                "hosts_per_network": {
                    str(network): len(
                        [
                            h
                            for h in discovered_hosts
                            if IPv4Address(h.ip_address) in network
                        ]
                    )
                    for network in network_ranges
                },
            }

            return topology_info

        except Exception as e:
            raise Exception(f"Topology discovery failed: {str(e)}")
