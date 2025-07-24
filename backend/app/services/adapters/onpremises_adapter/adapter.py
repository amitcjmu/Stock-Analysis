"""
Main On-Premises Platform Adapter implementing BaseAdapter interface
"""

import time
from ipaddress import AddressValueError, IPv4Network
from typing import Any, Dict, List

from app.services.collection_flow.adapters import (
    AdapterMetadata,
    BaseAdapter,
    CollectionRequest,
    CollectionResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .data_transformer import DataTransformer
from .models import DiscoveredHost, OnPremisesCredentials
from .network_scanner import NetworkScanner
from .protocol_collectors import ProtocolCollectors
from .service_discovery import ServiceDiscovery
from .topology import TopologyDiscovery


class OnPremisesAdapter(BaseAdapter):
    """
    On-Premises Platform Adapter implementing BaseAdapter interface

    Provides comprehensive on-premises infrastructure discovery using:
    - Network scanning (ping, port scanning)
    - SNMP for network devices and server information
    - SSH for Linux/Unix server information
    - WMI for Windows server information
    - Service detection and OS fingerprinting
    - Network topology discovery
    """

    def __init__(self, db: AsyncSession, metadata: AdapterMetadata):
        """Initialize on-premises adapter with metadata and session"""
        super().__init__(db, metadata)
        self._discovered_hosts: List[DiscoveredHost] = []
        self._network_ranges: List[IPv4Network] = []
        self._supported_protocols = {
            "ICMP": {"name": "ping", "description": "Basic host discovery"},
            "SSH": {"name": "ssh", "ports": [22], "description": "Secure Shell access"},
            "SNMP": {
                "name": "snmp",
                "ports": [161],
                "description": "Simple Network Management Protocol",
            },
            "WMI": {
                "name": "wmi",
                "ports": [135, 445],
                "description": "Windows Management Instrumentation",
            },
            "HTTP": {
                "name": "http",
                "ports": [80, 8080],
                "description": "Web services",
            },
            "HTTPS": {
                "name": "https",
                "ports": [443, 8443],
                "description": "Secure web services",
            },
            "Database": {
                "name": "database",
                "ports": [1433, 1521, 3306, 5432],
                "description": "Database services",
            },
            "RDP": {
                "name": "rdp",
                "ports": [3389],
                "description": "Remote Desktop Protocol",
            },
            "VNC": {
                "name": "vnc",
                "ports": [5900, 5901, 5902],
                "description": "Virtual Network Computing",
            },
        }

        # Initialize component modules
        self.network_scanner = NetworkScanner(self.logger)
        self.service_discovery = ServiceDiscovery(self.logger, self.network_scanner)
        self.protocol_collectors = ProtocolCollectors(self.logger)
        self.topology_discovery = TopologyDiscovery(self.logger)
        self.data_transformer = DataTransformer(self.logger)

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate on-premises credentials and configuration

        Args:
            credentials: On-premises credentials dictionary

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Parse credentials
            creds = self._parse_credentials(credentials)

            # Validate network ranges
            if not creds.network_ranges:
                self.logger.error("No network ranges specified for scanning")
                return False

            for network_range in creds.network_ranges:
                try:
                    network = IPv4Network(network_range, strict=False)
                    # Check if network range is reasonable (not too large)
                    if network.num_addresses > 65536:  # /16 network max
                        self.logger.warning(
                            f"Network range {network_range} is very large ({network.num_addresses} addresses)"
                        )
                except AddressValueError as e:
                    self.logger.error(
                        f"Invalid network range {network_range}: {str(e)}"
                    )
                    return False

            # Test basic network connectivity
            test_result = await self._test_basic_connectivity(creds)

            if test_result:
                self.logger.info(
                    "On-premises adapter credentials validated successfully"
                )
                return True
            else:
                self.logger.error("Failed to validate on-premises adapter connectivity")
                return False

        except Exception as e:
            self.logger.error(f"Error validating on-premises credentials: {str(e)}")
            return False

    def _parse_credentials(self, credentials: Dict[str, Any]) -> OnPremisesCredentials:
        """Parse credentials dictionary into OnPremisesCredentials object"""
        return OnPremisesCredentials(
            network_ranges=credentials.get("network_ranges", []),
            ssh_username=credentials.get("ssh_username"),
            ssh_password=credentials.get("ssh_password"),
            ssh_private_key=credentials.get("ssh_private_key"),
            ssh_port=credentials.get("ssh_port", 22),
            snmp_community=credentials.get("snmp_community", "public"),
            snmp_version=credentials.get("snmp_version", "2c"),
            snmp_username=credentials.get("snmp_username"),
            snmp_auth_protocol=credentials.get("snmp_auth_protocol"),
            snmp_auth_key=credentials.get("snmp_auth_key"),
            snmp_priv_protocol=credentials.get("snmp_priv_protocol"),
            snmp_priv_key=credentials.get("snmp_priv_key"),
            wmi_username=credentials.get("wmi_username"),
            wmi_password=credentials.get("wmi_password"),
            wmi_domain=credentials.get("wmi_domain"),
            timeout=credentials.get("timeout", 10),
            max_concurrent_scans=credentials.get("max_concurrent_scans", 50),
        )

    async def _test_basic_connectivity(self, creds: OnPremisesCredentials) -> bool:
        """Test basic network connectivity to validate configuration"""
        try:
            # Test with first network range
            if not creds.network_ranges:
                return False

            network = IPv4Network(creds.network_ranges[0], strict=False)

            # Try to ping first few hosts in the range
            test_hosts = list(network.hosts())[: min(5, len(list(network.hosts())))]

            for host in test_hosts:
                if await self.network_scanner.ping_host(str(host), creds.timeout):
                    self.logger.info(f"Successfully pinged test host {host}")
                    return True

            # If no hosts respond to ping, still consider valid (could be firewalled)
            self.logger.info(
                "No test hosts responded to ping, but configuration appears valid"
            )
            return True

        except Exception as e:
            self.logger.error(f"Basic connectivity test failed: {str(e)}")
            return False

    async def test_connectivity(self, configuration: Dict[str, Any]) -> bool:
        """
        Test connectivity to on-premises infrastructure

        Args:
            configuration: On-premises configuration including credentials

        Returns:
            True if connectivity successful, False otherwise
        """
        try:
            # Parse configuration
            credentials = configuration.get("credentials", {})
            creds = self._parse_credentials(credentials)

            # Test different connectivity methods
            connectivity_tests = {
                "Network_Scanning": self._test_network_scanning,
                "SNMP": self.protocol_collectors.test_snmp_connectivity,
                "SSH": self.protocol_collectors.test_ssh_connectivity,
            }

            results = {}
            for test_name, test_func in connectivity_tests.items():
                try:
                    results[test_name] = await test_func(creds)
                except Exception as e:
                    self.logger.warning(
                        f"Connectivity test {test_name} failed: {str(e)}"
                    )
                    results[test_name] = False

            # Log results
            successful_tests = sum(1 for result in results.values() if result)
            total_tests = len(results)

            self.logger.info(
                f"On-premises connectivity tests: {successful_tests}/{total_tests} successful"
            )

            # Consider connectivity successful if at least network scanning works
            return results.get("Network_Scanning", False)

        except Exception as e:
            self.logger.error(f"On-premises connectivity test failed: {str(e)}")
            return False

    async def _test_network_scanning(self, creds: OnPremisesCredentials) -> bool:
        """Test basic network scanning capability"""
        try:
            if not creds.network_ranges:
                return False

            # Quick scan of first few hosts
            network = IPv4Network(creds.network_ranges[0], strict=False)
            test_hosts = list(network.hosts())[:3]

            for host_ip in test_hosts:
                # Try to ping the host
                if await self.network_scanner.ping_host(str(host_ip), creds.timeout):
                    return True

            return True  # Consider successful even if no hosts respond

        except Exception:
            return False

    async def collect_data(self, request: CollectionRequest) -> CollectionResponse:
        """
        Collect data from on-premises infrastructure

        Args:
            request: Collection request with parameters

        Returns:
            Collection response with collected data or error information
        """
        start_time = time.time()

        try:
            # Parse credentials and configuration
            creds = self._parse_credentials(request.credentials)

            # Initialize scanning parameters
            self._discovered_hosts = []
            self._network_ranges = []

            # Parse network ranges
            for network_range in creds.network_ranges:
                try:
                    network = IPv4Network(network_range, strict=False)
                    self._network_ranges.append(network)
                except AddressValueError as e:
                    self.logger.warning(
                        f"Skipping invalid network range {network_range}: {str(e)}"
                    )

            if not self._network_ranges:
                raise Exception("No valid network ranges provided for scanning")

            # Perform discovery phases
            collected_data = {}
            total_resources = 0

            # Phase 1: Network Discovery (Host Detection)
            self.logger.info("Starting network discovery phase...")
            host_discovery_data = await self.network_scanner.perform_host_discovery(
                creds, self._network_ranges, request.configuration
            )
            collected_data["host_discovery"] = host_discovery_data

            # Update discovered hosts from the scanner results
            self._discovered_hosts = []
            for host_dict in host_discovery_data.get("discovered_hosts", []):
                host = DiscoveredHost(**host_dict)
                self._discovered_hosts.append(host)

            total_resources += len(self._discovered_hosts)

            # Phase 2: Service Discovery (Port Scanning)
            if request.configuration.get("include_port_scanning", True):
                self.logger.info("Starting service discovery phase...")
                service_discovery_data = (
                    await self.service_discovery.perform_service_discovery(
                        self._discovered_hosts, creds, request.configuration
                    )
                )
                collected_data["service_discovery"] = service_discovery_data

            # Phase 3: Detailed Information Gathering
            if request.configuration.get("include_detailed_info", True):
                self.logger.info("Starting detailed information gathering...")
                detailed_info_data = (
                    await self.protocol_collectors.perform_detailed_info_gathering(
                        self._discovered_hosts, creds, request.configuration
                    )
                )
                collected_data["detailed_info"] = detailed_info_data

                # Add OS detection
                for host in self._discovered_hosts:
                    try:
                        os_info = await self.service_discovery.detect_operating_system(
                            host
                        )
                        if os_info:
                            host.operating_system = os_info.get("os_family")
                    except Exception as e:
                        self.logger.debug(
                            f"OS detection failed for {host.ip_address}: {str(e)}"
                        )

            # Phase 4: Network Topology Discovery
            if request.configuration.get("include_topology", False):
                self.logger.info("Starting network topology discovery...")
                topology_data = (
                    await self.topology_discovery.perform_topology_discovery(
                        self._network_ranges,
                        self._discovered_hosts,
                        request.configuration,
                    )
                )
                collected_data["topology"] = topology_data

            duration = time.time() - start_time

            self.logger.info(
                f"On-premises data collection completed: {total_resources} hosts discovered in {duration:.2f}s"
            )

            return CollectionResponse(
                success=True,
                data=collected_data,
                resource_count=total_resources,
                collection_method=request.collection_method,
                duration_seconds=duration,
                metadata={
                    "network_ranges": creds.network_ranges,
                    "discovery_phases": list(collected_data.keys()),
                    "adapter_version": self.metadata.version,
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"On-premises data collection failed: {str(e)}"
            self.logger.error(error_msg)

            return CollectionResponse(
                success=False,
                error_message=error_msg,
                error_details={"exception_type": type(e).__name__},
                duration_seconds=duration,
                metadata={
                    "network_ranges": (
                        creds.network_ranges if "creds" in locals() else []
                    )
                },
            )

    async def get_available_resources(self, configuration: Dict[str, Any]) -> List[str]:
        """
        Get list of available on-premises resources for collection

        Args:
            configuration: On-premises configuration including credentials

        Returns:
            List of available resource identifiers (network ranges)
        """
        try:
            # Test connectivity first
            if not await self.test_connectivity(configuration):
                return []

            # Return the configured network ranges as available resources
            credentials = configuration.get("credentials", {})
            network_ranges = credentials.get("network_ranges", [])

            # Validate network ranges
            valid_ranges = []
            for network_range in network_ranges:
                try:
                    IPv4Network(network_range, strict=False)
                    valid_ranges.append(network_range)
                except AddressValueError:
                    continue

            return valid_ranges

        except Exception as e:
            self.logger.error(
                f"Failed to get available on-premises resources: {str(e)}"
            )
            return []

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw on-premises data to normalized format for Discovery Flow

        Args:
            raw_data: Raw on-premises data from collection

        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        return self.data_transformer.transform_data(raw_data)
