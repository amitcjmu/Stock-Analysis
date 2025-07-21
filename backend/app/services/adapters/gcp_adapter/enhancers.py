"""
GCP Resource Enhancers

Provides detailed enhancement for different GCP resource types.
"""

from typing import Dict, Any, List
import logging

from .dependencies import (
    compute_v1,
    sql_v1,
    container_v1,
    functions_v1
)
from .auth import GCPAuthManager


class GCPResourceEnhancer:
    """Enhances basic asset data with detailed information from specific APIs"""
    
    def __init__(self, auth_manager: GCPAuthManager):
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        
    async def enhance_asset_data(self, asset_type: str, assets: List[Dict], config: Dict[str, Any]) -> List[Dict]:
        """Enhance basic asset data with detailed information from specific APIs"""
        try:
            enhanced_assets = []
            
            for asset in assets:
                enhanced_asset = asset.copy()
                
                # Add detailed information based on asset type
                if asset_type == "compute.googleapis.com/Instance":
                    enhanced_asset.update(await self.enhance_compute_instance_data(asset))
                elif asset_type == "sqladmin.googleapis.com/Instance":
                    enhanced_asset.update(await self.enhance_sql_instance_data(asset))
                elif asset_type == "storage.googleapis.com/Bucket":
                    enhanced_asset.update(await self.enhance_storage_bucket_data(asset))
                elif asset_type == "container.googleapis.com/Cluster":
                    enhanced_asset.update(await self.enhance_gke_cluster_data(asset))
                elif asset_type == "cloudfunctions.googleapis.com/CloudFunction":
                    enhanced_asset.update(await self.enhance_cloud_function_data(asset))
                    
                enhanced_assets.append(enhanced_asset)
                
            return enhanced_assets
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance {asset_type} data: {str(e)}")
            return assets  # Return basic data if enhancement fails
            
    async def enhance_compute_instance_data(self, instance_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Compute Engine instance data"""
        try:
            # Extract instance details from asset name
            # Format: //compute.googleapis.com/projects/{project}/zones/{zone}/instances/{instance}
            asset_name = instance_asset.get("name", "")
            if "/instances/" not in asset_name:
                return {}
                
            parts = asset_name.split("/")
            if len(parts) >= 6:
                zone = parts[-3]
                instance_name = parts[-1]
                
                # Get detailed instance information
                request = compute_v1.GetInstanceRequest(
                    project=self.auth_manager.project_id,
                    zone=zone,
                    instance=instance_name
                )
                
                instance = self.auth_manager.compute_client.get(request=request)
                
                return {
                    "zone": zone,
                    "machine_type": instance.machine_type.split("/")[-1] if instance.machine_type else None,
                    "status": instance.status,
                    "creation_timestamp": instance.creation_timestamp,
                    "description": instance.description,
                    "hostname": instance.hostname,
                    "can_ip_forward": instance.can_ip_forward,
                    "cpu_platform": instance.cpu_platform,
                    "deletion_protection": instance.deletion_protection,
                    "fingerprint": instance.fingerprint,
                    "start_restricted": instance.start_restricted,
                    "disks": [
                        {
                            "device_name": disk.device_name,
                            "boot": disk.boot,
                            "auto_delete": disk.auto_delete,
                            "mode": disk.mode,
                            "type": disk.type_,
                            "disk_size_gb": disk.disk_size_gb,
                        } for disk in instance.disks
                    ] if instance.disks else [],
                    "network_interfaces": [
                        {
                            "name": nic.name,
                            "network": nic.network.split("/")[-1] if nic.network else None,
                            "subnetwork": nic.subnetwork.split("/")[-1] if nic.subnetwork else None,
                            "network_ip": nic.network_i_p,
                            "access_configs": [
                                {
                                    "type": ac.type_,
                                    "name": ac.name,
                                    "nat_ip": ac.nat_i_p,
                                } for ac in nic.access_configs
                            ] if nic.access_configs else [],
                        } for nic in instance.network_interfaces
                    ] if instance.network_interfaces else [],
                    "scheduling": {
                        "automatic_restart": instance.scheduling.automatic_restart if instance.scheduling else None,
                        "on_host_maintenance": instance.scheduling.on_host_maintenance if instance.scheduling else None,
                        "preemptible": instance.scheduling.preemptible if instance.scheduling else None,
                    } if instance.scheduling else {},
                    "service_accounts": [
                        {
                            "email": sa.email,
                            "scopes": list(sa.scopes),
                        } for sa in instance.service_accounts
                    ] if instance.service_accounts else [],
                    "tags": {
                        "items": list(instance.tags.items) if instance.tags and instance.tags.items else [],
                        "fingerprint": instance.tags.fingerprint if instance.tags else None,
                    } if instance.tags else {},
                    "metadata": {
                        "items": [
                            {
                                "key": item.key,
                                "value": item.value,
                            } for item in instance.metadata.items
                        ] if instance.metadata and instance.metadata.items else [],
                        "fingerprint": instance.metadata.fingerprint if instance.metadata else None,
                    } if instance.metadata else {},
                    "labels": dict(instance.labels) if instance.labels else {},
                }
                
        except Exception as e:
            self.logger.warning(f"Failed to enhance Compute instance data: {str(e)}")
            
        return {}
        
    async def enhance_sql_instance_data(self, sql_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Cloud SQL instance data"""
        try:
            # Extract instance name from asset name
            # Format: //sqladmin.googleapis.com/projects/{project}/instances/{instance}
            asset_name = sql_asset.get("name", "")
            if "/instances/" not in asset_name:
                return {}
                
            instance_name = asset_name.split("/")[-1]
            
            # Get detailed SQL instance information
            request = sql_v1.SqlInstancesGetRequest(
                project=self.auth_manager.project_id,
                instance=instance_name
            )
            
            instance = self.auth_manager.sql_client.get(request=request)
            
            return {
                "backend_type": instance.backend_type,
                "connection_name": instance.connection_name,
                "database_version": instance.database_version,
                "gce_zone": instance.gce_zone,
                "instance_type": instance.instance_type,
                "master_instance_name": instance.master_instance_name,
                "max_disk_size": instance.max_disk_size,
                "region": instance.region,
                "state": instance.state,
                "settings": {
                    "activation_policy": instance.settings.activation_policy if instance.settings else None,
                    "authorized_gae_applications": list(instance.settings.authorized_gae_applications) if instance.settings and instance.settings.authorized_gae_applications else [],
                    "availability_type": instance.settings.availability_type if instance.settings else None,
                    "backup_configuration": {
                        "enabled": instance.settings.backup_configuration.enabled if instance.settings and instance.settings.backup_configuration else None,
                        "start_time": instance.settings.backup_configuration.start_time if instance.settings and instance.settings.backup_configuration else None,
                    } if instance.settings and instance.settings.backup_configuration else {},
                    "crash_safe_replication_enabled": instance.settings.crash_safe_replication_enabled if instance.settings else None,
                    "data_disk_size_gb": instance.settings.data_disk_size_gb if instance.settings else None,
                    "data_disk_type": instance.settings.data_disk_type if instance.settings else None,
                    "database_flags": [
                        {
                            "name": flag.name,
                            "value": flag.value,
                        } for flag in instance.settings.database_flags
                    ] if instance.settings and instance.settings.database_flags else [],
                    "ip_configuration": {
                        "ipv4_enabled": instance.settings.ip_configuration.ipv4_enabled if instance.settings and instance.settings.ip_configuration else None,
                        "require_ssl": instance.settings.ip_configuration.require_ssl if instance.settings and instance.settings.ip_configuration else None,
                        "authorized_networks": [
                            {
                                "name": net.name,
                                "value": net.value,
                            } for net in instance.settings.ip_configuration.authorized_networks
                        ] if instance.settings and instance.settings.ip_configuration and instance.settings.ip_configuration.authorized_networks else [],
                    } if instance.settings and instance.settings.ip_configuration else {},
                    "maintenance_window": {
                        "day": instance.settings.maintenance_window.day if instance.settings and instance.settings.maintenance_window else None,
                        "hour": instance.settings.maintenance_window.hour if instance.settings and instance.settings.maintenance_window else None,
                        "update_track": instance.settings.maintenance_window.update_track if instance.settings and instance.settings.maintenance_window else None,
                    } if instance.settings and instance.settings.maintenance_window else {},
                    "pricing_plan": instance.settings.pricing_plan if instance.settings else None,
                    "replication_type": instance.settings.replication_type if instance.settings else None,
                    "storage_auto_resize": instance.settings.storage_auto_resize if instance.settings else None,
                    "storage_auto_resize_limit": instance.settings.storage_auto_resize_limit if instance.settings else None,
                    "tier": instance.settings.tier if instance.settings else None,
                    "user_labels": dict(instance.settings.user_labels) if instance.settings and instance.settings.user_labels else {},
                } if instance.settings else {},
                "current_disk_size": instance.current_disk_size,
                "etag": instance.etag,
                "failover_replica": {
                    "available": instance.failover_replica.available if instance.failover_replica else None,
                    "name": instance.failover_replica.name if instance.failover_replica else None,
                } if instance.failover_replica else {},
                "ip_addresses": [
                    {
                        "ip_address": ip.ip_address,
                        "type": ip.type_,
                        "time_to_retire": ip.time_to_retire,
                    } for ip in instance.ip_addresses
                ] if instance.ip_addresses else [],
                "server_ca_cert": {
                    "cert": instance.server_ca_cert.cert if instance.server_ca_cert else None,
                    "common_name": instance.server_ca_cert.common_name if instance.server_ca_cert else None,
                    "create_time": instance.server_ca_cert.create_time if instance.server_ca_cert else None,
                    "expiration_time": instance.server_ca_cert.expiration_time if instance.server_ca_cert else None,
                    "instance": instance.server_ca_cert.instance if instance.server_ca_cert else None,
                    "sha1_fingerprint": instance.server_ca_cert.sha1_fingerprint if instance.server_ca_cert else None,
                } if instance.server_ca_cert else {},
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance SQL instance data: {str(e)}")
            
        return {}
        
    async def enhance_storage_bucket_data(self, bucket_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Cloud Storage bucket data"""
        try:
            # Extract bucket name from asset name
            # Format: //storage.googleapis.com/projects/_/buckets/{bucket}
            asset_name = bucket_asset.get("name", "")
            if "/buckets/" not in asset_name:
                return {}
                
            bucket_name = asset_name.split("/")[-1]
            
            # Get detailed bucket information
            bucket = self.auth_manager.storage_client.bucket(bucket_name)
            bucket.reload()
            
            return {
                "location": bucket.location,
                "location_type": bucket.location_type,
                "storage_class": bucket.storage_class,
                "time_created": bucket.time_created.isoformat() if bucket.time_created else None,
                "updated": bucket.updated.isoformat() if bucket.updated else None,
                "versioning_enabled": bucket.versioning_enabled,
                "requester_pays": bucket.requester_pays,
                "self_link": bucket.self_link,
                "public_access_prevention": bucket.public_access_prevention,
                "uniform_bucket_level_access": bucket.uniform_bucket_level_access.enabled if bucket.uniform_bucket_level_access else None,
                "encryption": {
                    "default_kms_key_name": bucket.encryption.default_kms_key_name if bucket.encryption else None,
                } if bucket.encryption else {},
                "lifecycle_rules": [
                    {
                        "action": rule.get("action", {}),
                        "condition": rule.get("condition", {}),
                    } for rule in bucket.lifecycle_rules
                ] if bucket.lifecycle_rules else [],
                "cors": [
                    {
                        "origin": cors_rule.get("origin", []),
                        "method": cors_rule.get("method", []),
                        "response_header": cors_rule.get("responseHeader", []),
                        "max_age_seconds": cors_rule.get("maxAgeSeconds"),
                    } for cors_rule in bucket.cors
                ] if bucket.cors else [],
                "default_event_based_hold": bucket.default_event_based_hold,
                "retention_policy": {
                    "retention_period": bucket.retention_policy.retention_period if bucket.retention_policy else None,
                    "effective_time": bucket.retention_policy.effective_time.isoformat() if bucket.retention_policy and bucket.retention_policy.effective_time else None,
                    "is_locked": bucket.retention_policy.is_locked if bucket.retention_policy else None,
                } if bucket.retention_policy else {},
                "labels": dict(bucket.labels) if bucket.labels else {},
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance Storage bucket data: {str(e)}")
            
        return {}
        
    async def enhance_gke_cluster_data(self, cluster_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance GKE cluster data"""
        try:
            # Extract cluster details from asset name
            # Format: //container.googleapis.com/projects/{project}/locations/{location}/clusters/{cluster}
            asset_name = cluster_asset.get("name", "")
            if "/clusters/" not in asset_name:
                return {}
                
            parts = asset_name.split("/")
            if len(parts) >= 6:
                location = parts[-3]
                cluster_name = parts[-1]
                
                # Get detailed cluster information
                request = container_v1.GetClusterRequest(
                    name=f"projects/{self.auth_manager.project_id}/locations/{location}/clusters/{cluster_name}"
                )
                
                cluster = self.auth_manager.container_client.get_cluster(request=request)
                
                return {
                    "location": cluster.location,
                    "status": cluster.status,
                    "description": cluster.description,
                    "initial_node_count": cluster.initial_node_count,
                    "current_master_version": cluster.current_master_version,
                    "current_node_version": cluster.current_node_version,
                    "create_time": cluster.create_time,
                    "status_message": cluster.status_message,
                    "node_ipv4_cidr_size": cluster.node_ipv4_cidr_size,
                    "services_ipv4_cidr": cluster.services_ipv4_cidr,
                    "cluster_ipv4_cidr": cluster.cluster_ipv4_cidr,
                    "endpoint": cluster.endpoint,
                    "initial_cluster_version": cluster.initial_cluster_version,
                    "current_node_count": cluster.current_node_count,
                    "expire_time": cluster.expire_time,
                    "enable_kubernetes_alpha": cluster.enable_kubernetes_alpha,
                    "enable_k8s_beta_apis": {
                        "enabled_apis": list(cluster.enable_k8s_beta_apis.enabled_apis) if cluster.enable_k8s_beta_apis else [],
                    } if cluster.enable_k8s_beta_apis else {},
                    "resource_labels": dict(cluster.resource_labels) if cluster.resource_labels else {},
                    "label_fingerprint": cluster.label_fingerprint,
                    "network": cluster.network,
                    "subnetwork": cluster.subnetwork,
                    "node_pools": [
                        {
                            "name": np.name,
                            "status": np.status,
                            "initial_node_count": np.initial_node_count,
                            "version": np.version,
                            "instance_group_urls": list(np.instance_group_urls),
                        } for np in cluster.node_pools
                    ] if cluster.node_pools else [],
                    "legacy_abac": {
                        "enabled": cluster.legacy_abac.enabled if cluster.legacy_abac else None,
                    } if cluster.legacy_abac else {},
                    "network_policy": {
                        "provider": cluster.network_policy.provider if cluster.network_policy else None,
                        "enabled": cluster.network_policy.enabled if cluster.network_policy else None,
                    } if cluster.network_policy else {},
                    "ip_allocation_policy": {
                        "use_ip_aliases": cluster.ip_allocation_policy.use_ip_aliases if cluster.ip_allocation_policy else None,
                        "cluster_secondary_range_name": cluster.ip_allocation_policy.cluster_secondary_range_name if cluster.ip_allocation_policy else None,
                        "services_secondary_range_name": cluster.ip_allocation_policy.services_secondary_range_name if cluster.ip_allocation_policy else None,
                        "cluster_ipv4_cidr_block": cluster.ip_allocation_policy.cluster_ipv4_cidr_block if cluster.ip_allocation_policy else None,
                        "services_ipv4_cidr_block": cluster.ip_allocation_policy.services_ipv4_cidr_block if cluster.ip_allocation_policy else None,
                    } if cluster.ip_allocation_policy else {},
                    "master_auth": {
                        "username": cluster.master_auth.username if cluster.master_auth else None,
                        "client_certificate_config": {
                            "issue_client_certificate": cluster.master_auth.client_certificate_config.issue_client_certificate if cluster.master_auth and cluster.master_auth.client_certificate_config else None,
                        } if cluster.master_auth and cluster.master_auth.client_certificate_config else {},
                    } if cluster.master_auth else {},
                    "logging_service": cluster.logging_service,
                    "monitoring_service": cluster.monitoring_service,
                    "network_config": {
                        "network": cluster.network_config.network if cluster.network_config else None,
                        "subnetwork": cluster.network_config.subnetwork if cluster.network_config else None,
                        "enable_intra_node_visibility": cluster.network_config.enable_intra_node_visibility if cluster.network_config else None,
                    } if cluster.network_config else {},
                }
                
        except Exception as e:
            self.logger.warning(f"Failed to enhance GKE cluster data: {str(e)}")
            
        return {}
        
    async def enhance_cloud_function_data(self, function_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Cloud Function data"""
        try:
            # Extract function name from asset name
            # Format: //cloudfunctions.googleapis.com/projects/{project}/locations/{location}/functions/{function}
            asset_name = function_asset.get("name", "")
            if "/functions/" not in asset_name:
                return {}
                
            # Get detailed function information
            request = functions_v1.GetFunctionRequest(name=asset_name)
            function = self.auth_manager.functions_client.get_function(request=request)
            
            return {
                "status": function.status,
                "entry_point": function.entry_point,
                "runtime": function.runtime,
                "timeout": function.timeout.seconds if function.timeout else None,
                "available_memory_mb": function.available_memory_mb,
                "service_account_email": function.service_account_email,
                "update_time": function.update_time.isoformat() if function.update_time else None,
                "version_id": function.version_id,
                "labels": dict(function.labels) if function.labels else {},
                "source_archive_url": function.source_archive_url,
                "source_repository": {
                    "url": function.source_repository.url if function.source_repository else None,
                    "deployed_url": function.source_repository.deployed_url if function.source_repository else None,
                } if function.source_repository else {},
                "https_trigger": {
                    "url": function.https_trigger.url if function.https_trigger else None,
                    "security_level": function.https_trigger.security_level if function.https_trigger else None,
                } if function.https_trigger else {},
                "event_trigger": {
                    "event_type": function.event_trigger.event_type if function.event_trigger else None,
                    "resource": function.event_trigger.resource if function.event_trigger else None,
                    "service": function.event_trigger.service if function.event_trigger else None,
                } if function.event_trigger else {},
                "environment_variables": dict(function.environment_variables) if function.environment_variables else {},
                "network": function.network,
                "max_instances": function.max_instances,
                "vpc_connector": function.vpc_connector,
                "vpc_connector_egress_settings": function.vpc_connector_egress_settings,
                "ingress_settings": function.ingress_settings,
                "kms_key_name": function.kms_key_name,
                "build_environment_variables": dict(function.build_environment_variables) if function.build_environment_variables else {},
                "docker_registry": function.docker_registry,
                "docker_repository": function.docker_repository,
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance Cloud Function data: {str(e)}")
            
        return {}