"""
Azure compute services operations (VMs, scaling, etc.)
"""

import logging
from typing import Any, Dict

from .auth import AzureAuthManager
from .exceptions import AZURE_SDK_AVAILABLE
from .utils import get_vm_power_state, parse_azure_resource_id

logger = logging.getLogger(__name__)


class AzureComputeManager:
    """Manages Azure compute resource operations"""

    def __init__(self, auth_manager: AzureAuthManager):
        self.auth_manager = auth_manager

    async def test_compute_connectivity(self) -> bool:
        """Test Compute API connectivity"""
        if not AZURE_SDK_AVAILABLE:
            return False

        try:
            # List VM sizes in a region (basic compute access)
            list(self.auth_manager.compute_client.virtual_machine_sizes.list("eastus"))
            return True
        except Exception:
            return False

    async def enhance_vm_data(self, vm_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance VM data with detailed compute information"""
        try:
            # Parse resource ID to get resource group and VM name
            parsed = parse_azure_resource_id(vm_resource.get("id", ""))

            if not parsed.get("resource_group") or not parsed.get("resource_name"):
                logger.warning(
                    f"Could not parse VM resource ID: {vm_resource.get('id')}"
                )
                return {}

            resource_group = parsed["resource_group"]
            vm_name = parsed["resource_name"]

            # Get detailed VM information
            vm = self.auth_manager.compute_client.virtual_machines.get(
                resource_group_name=resource_group,
                vm_name=vm_name,
                expand="instanceView",
            )

            return {
                "vm_size": (
                    vm.hardware_profile.vm_size if vm.hardware_profile else None
                ),
                "os_type": (
                    vm.storage_profile.os_disk.os_type
                    if vm.storage_profile and vm.storage_profile.os_disk
                    else None
                ),
                "os_disk_size": (
                    vm.storage_profile.os_disk.disk_size_gb
                    if vm.storage_profile and vm.storage_profile.os_disk
                    else None
                ),
                "data_disks_count": (
                    len(vm.storage_profile.data_disks)
                    if vm.storage_profile and vm.storage_profile.data_disks
                    else 0
                ),
                "network_interfaces": (
                    [nic.id for nic in vm.network_profile.network_interfaces]
                    if vm.network_profile and vm.network_profile.network_interfaces
                    else []
                ),
                "provisioning_state": vm.provisioning_state,
                "power_state": (
                    get_vm_power_state(vm.instance_view) if vm.instance_view else None
                ),
                "computer_name": (
                    vm.os_profile.computer_name if vm.os_profile else None
                ),
                "admin_username": (
                    vm.os_profile.admin_username if vm.os_profile else None
                ),
                "zones": vm.zones,
                "availability_set": (
                    vm.availability_set.id if vm.availability_set else None
                ),
            }

        except Exception as e:
            logger.warning(
                f"Failed to enhance VM data for {vm_resource.get('name')}: {str(e)}"
            )

        return {}

    async def enhance_web_app_data(
        self, app_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance web app data with detailed information"""
        try:
            # Parse resource ID
            parsed = parse_azure_resource_id(app_resource.get("id", ""))

            if not parsed.get("resource_group") or not parsed.get("resource_name"):
                logger.warning(
                    f"Could not parse web app resource ID: {app_resource.get('id')}"
                )
                return {}

            resource_group = parsed["resource_group"]
            app_name = parsed["resource_name"]

            # Get detailed web app information
            web_app = self.auth_manager.web_client.web_apps.get(
                resource_group_name=resource_group, name=app_name
            )

            return {
                "kind": web_app.kind,
                "state": web_app.state,
                "host_names": web_app.host_names,
                "enabled": web_app.enabled,
                "availability_state": web_app.availability_state,
                "server_farm_id": web_app.server_farm_id,
                "default_host_name": web_app.default_host_name,
                "https_only": web_app.https_only,
                "site_config": (
                    {
                        "app_settings": (
                            getattr(web_app.site_config, "app_settings", None)
                            if web_app.site_config
                            else None
                        ),
                        "connection_strings": (
                            getattr(web_app.site_config, "connection_strings", None)
                            if web_app.site_config
                            else None
                        ),
                        "default_documents": (
                            getattr(web_app.site_config, "default_documents", None)
                            if web_app.site_config
                            else None
                        ),
                        "net_framework_version": (
                            getattr(web_app.site_config, "net_framework_version", None)
                            if web_app.site_config
                            else None
                        ),
                        "php_version": (
                            getattr(web_app.site_config, "php_version", None)
                            if web_app.site_config
                            else None
                        ),
                        "python_version": (
                            getattr(web_app.site_config, "python_version", None)
                            if web_app.site_config
                            else None
                        ),
                        "node_version": (
                            getattr(web_app.site_config, "node_version", None)
                            if web_app.site_config
                            else None
                        ),
                        "java_version": (
                            getattr(web_app.site_config, "java_version", None)
                            if web_app.site_config
                            else None
                        ),
                    }
                    if web_app.site_config
                    else {}
                ),
            }

        except Exception as e:
            logger.warning(
                f"Failed to enhance web app data for {app_resource.get('name')}: {str(e)}"
            )

        return {}

    async def enhance_sql_database_data(
        self, db_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance SQL database data with detailed information"""
        try:
            # Parse resource ID to get server and database info
            parsed = parse_azure_resource_id(db_resource.get("id", ""))

            if (
                not parsed.get("resource_group")
                or not parsed.get("parent_resource")
                or not parsed.get("resource_name")
            ):
                logger.warning(
                    f"Could not parse SQL database resource ID: {db_resource.get('id')}"
                )
                return {}

            resource_group = parsed["resource_group"]
            server_name = parsed["parent_resource"]
            database_name = parsed["resource_name"]

            # Get detailed database information
            database = self.auth_manager.sql_client.databases.get(
                resource_group_name=resource_group,
                server_name=server_name,
                database_name=database_name,
            )

            return {
                "sku": {
                    "name": database.sku.name if database.sku else None,
                    "tier": database.sku.tier if database.sku else None,
                    "capacity": database.sku.capacity if database.sku else None,
                },
                "status": database.status,
                "creation_date": (
                    database.creation_date.isoformat()
                    if database.creation_date
                    else None
                ),
                "collation": database.collation,
                "max_size_bytes": database.max_size_bytes,
                "current_backup_storage_redundancy": database.current_backup_storage_redundancy,
                "zone_redundant": database.zone_redundant,
                "read_scale": database.read_scale,
                "elastic_pool_id": database.elastic_pool_id,
            }

        except Exception as e:
            logger.warning(
                f"Failed to enhance SQL database data for {db_resource.get('name')}: {str(e)}"
            )

        return {}
