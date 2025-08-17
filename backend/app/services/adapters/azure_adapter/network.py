"""
Azure network services operations (VNet, security groups, load balancers, etc.)
"""

import logging
from typing import Any, Dict

from .auth import AzureAuthManager
from .utils import parse_azure_resource_id

logger = logging.getLogger(__name__)


class AzureNetworkManager:
    """Manages Azure network resource operations"""

    def __init__(self, auth_manager: AzureAuthManager):
        self.auth_manager = auth_manager

    async def enhance_load_balancer_data(
        self, lb_resource: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance load balancer data with detailed information"""
        try:
            # Parse resource ID
            parsed = parse_azure_resource_id(lb_resource.get("id", ""))

            if not parsed.get("resource_group") or not parsed.get("resource_name"):
                logger.warning(
                    f"Could not parse load balancer resource ID: {lb_resource.get('id')}"
                )
                return {}

            resource_group = parsed["resource_group"]
            lb_name = parsed["resource_name"]

            # Get detailed load balancer information
            load_balancer = self.auth_manager.network_client.load_balancers.get(
                resource_group_name=resource_group, load_balancer_name=lb_name
            )

            return {
                "sku": {
                    "name": load_balancer.sku.name if load_balancer.sku else None,
                    "tier": load_balancer.sku.tier if load_balancer.sku else None,
                },
                "provisioning_state": load_balancer.provisioning_state,
                "frontend_ip_configurations": (
                    [
                        {
                            "name": fic.name,
                            "private_ip_address": fic.private_ip_address,
                            "private_ip_allocation_method": fic.private_ip_allocation_method,
                            "subnet_id": fic.subnet.id if fic.subnet else None,
                            "public_ip_address_id": (
                                fic.public_ip_address.id
                                if fic.public_ip_address
                                else None
                            ),
                        }
                        for fic in load_balancer.frontend_ip_configurations
                    ]
                    if load_balancer.frontend_ip_configurations
                    else []
                ),
                "backend_address_pools": (
                    [
                        {
                            "name": bap.name,
                            "backend_addresses_count": (
                                len(bap.backend_addresses)
                                if bap.backend_addresses
                                else 0
                            ),
                        }
                        for bap in load_balancer.backend_address_pools
                    ]
                    if load_balancer.backend_address_pools
                    else []
                ),
                "load_balancing_rules": (
                    [
                        {
                            "name": lbr.name,
                            "protocol": lbr.protocol,
                            "frontend_port": lbr.frontend_port,
                            "backend_port": lbr.backend_port,
                            "enable_floating_ip": lbr.enable_floating_ip,
                        }
                        for lbr in load_balancer.load_balancing_rules
                    ]
                    if load_balancer.load_balancing_rules
                    else []
                ),
                "inbound_nat_rules": (
                    [
                        {
                            "name": inr.name,
                            "protocol": inr.protocol,
                            "frontend_port": inr.frontend_port,
                            "backend_port": inr.backend_port,
                        }
                        for inr in load_balancer.inbound_nat_rules
                    ]
                    if load_balancer.inbound_nat_rules
                    else []
                ),
            }

        except Exception as e:
            logger.warning(
                f"Failed to enhance load balancer data for {lb_resource.get('name')}: {str(e)}"
            )

        return {}
