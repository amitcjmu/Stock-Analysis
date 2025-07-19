"""
GCP Platform Adapter for ADCS Implementation

This adapter provides comprehensive GCP resource discovery and data collection
using Cloud Asset Inventory for resource discovery and Cloud Monitoring for metrics.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

from google.cloud import asset_v1
from google.cloud import monitoring_v3
from google.cloud import compute_v1
from google.cloud import sql_v1
from google.cloud import storage
from google.cloud import container_v1
from google.cloud import functions_v1
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.collection_flow.adapters import (
    BaseAdapter, 
    AdapterMetadata, 
    AdapterCapability, 
    CollectionMethod,
    CollectionRequest,
    CollectionResponse
)
from app.models.collection_flow import AutomationTier


@dataclass
class GCPCredentials:
    """GCP credentials configuration"""
    project_id: str
    service_account_key: Dict[str, Any]  # Service account JSON key
    
    
@dataclass
class GCPResourceMetrics:
    """GCP resource performance metrics"""
    resource_id: str
    resource_type: str
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    network_sent_bytes: Optional[float] = None
    network_received_bytes: Optional[float] = None
    disk_read_bytes: Optional[float] = None
    disk_write_bytes: Optional[float] = None
    timestamp: Optional[datetime] = None


class GCPAdapter(BaseAdapter):
    """
    GCP Platform Adapter implementing BaseAdapter interface
    
    Provides comprehensive GCP resource discovery using:
    - Cloud Asset Inventory for efficient resource queries
    - Cloud Monitoring for performance metrics
    - Compute Engine API for VM details
    - Cloud SQL API for database details
    - Cloud Storage API for bucket details
    - Container API for GKE cluster details
    - Cloud Functions API for function details
    """
    
    def __init__(self, db: AsyncSession, metadata: AdapterMetadata):
        """Initialize GCP adapter with metadata and session"""
        super().__init__(db, metadata)
        self._credentials = None
        self._project_id = None
        self._asset_client = None
        self._monitoring_client = None
        self._compute_client = None
        self._sql_client = None
        self._storage_client = None
        self._container_client = None
        self._functions_client = None
        self._supported_asset_types = {
            "compute.googleapis.com/Instance",
            "sqladmin.googleapis.com/Instance",
            "storage.googleapis.com/Bucket",
            "container.googleapis.com/Cluster",
            "cloudfunctions.googleapis.com/CloudFunction",
            "compute.googleapis.com/ForwardingRule",
            "compute.googleapis.com/UrlMap",
            "compute.googleapis.com/TargetHttpProxy",
            "compute.googleapis.com/TargetHttpsProxy",
            "compute.googleapis.com/BackendService",
            "compute.googleapis.com/Network",
            "compute.googleapis.com/Subnetwork",
            "compute.googleapis.com/Firewall",
            "bigquery.googleapis.com/Dataset",
            "bigquery.googleapis.com/Table"
        }
        
    def _get_gcp_credentials(self, credentials: GCPCredentials) -> service_account.Credentials:
        """Create GCP credentials from service account key"""
        return service_account.Credentials.from_service_account_info(
            credentials.service_account_key
        )
        
    def _init_clients(self, credentials: service_account.Credentials, project_id: str):
        """Initialize GCP service clients"""
        self._credentials = credentials
        self._project_id = project_id
        self._asset_client = asset_v1.AssetServiceClient(credentials=credentials)
        self._monitoring_client = monitoring_v3.MetricServiceClient(credentials=credentials)
        self._compute_client = compute_v1.InstancesClient(credentials=credentials)
        self._sql_client = sql_v1.SqlInstancesServiceClient(credentials=credentials)
        self._storage_client = storage.Client(credentials=credentials, project=project_id)
        self._container_client = container_v1.ClusterManagerClient(credentials=credentials)
        self._functions_client = functions_v1.CloudFunctionsServiceClient(credentials=credentials)
        
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate GCP credentials by attempting to list projects
        
        Args:
            credentials: GCP credentials dictionary
            
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Parse credentials
            gcp_creds = GCPCredentials(
                project_id=credentials.get("project_id", ""),
                service_account_key=credentials.get("service_account_key", {})
            )
            
            # Create credentials and test with Resource Manager
            creds = self._get_gcp_credentials(gcp_creds)
            
            # Build Resource Manager service
            service = discovery.build('cloudresourcemanager', 'v1', credentials=creds)
            
            # Test credentials by getting project info
            project = service.projects().get(projectId=gcp_creds.project_id).execute()
            
            self.logger.info(f"GCP credentials validated for project: {project.get('name', gcp_creds.project_id)}")
            return True
            
        except DefaultCredentialsError as e:
            self.logger.error(f"GCP credentials validation failed: {str(e)}")
            return False
        except HttpError as e:
            self.logger.error(f"GCP API error during credential validation: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error validating GCP credentials: {str(e)}")
            return False
            
    async def test_connectivity(self, configuration: Dict[str, Any]) -> bool:
        """
        Test connectivity to GCP APIs and verify required permissions
        
        Args:
            configuration: GCP configuration including credentials
            
        Returns:
            True if connectivity successful, False otherwise
        """
        try:
            # Extract credentials
            credentials = configuration.get("credentials", {})
            
            gcp_creds = GCPCredentials(
                project_id=credentials.get("project_id", ""),
                service_account_key=credentials.get("service_account_key", {})
            )
            
            # Create credentials and initialize clients
            creds = self._get_gcp_credentials(gcp_creds)
            self._init_clients(creds, gcp_creds.project_id)
            
            # Test connectivity to core services
            connectivity_tests = {
                "AssetInventory": self._test_asset_inventory_connectivity,
                "Monitoring": self._test_monitoring_connectivity,
                "Compute": self._test_compute_connectivity,
                "Storage": self._test_storage_connectivity
            }
            
            results = {}
            for service, test_func in connectivity_tests.items():
                try:
                    results[service] = await test_func()
                except Exception as e:
                    self.logger.warning(f"Connectivity test failed for {service}: {str(e)}")
                    results[service] = False
                    
            # Log results
            successful_tests = sum(1 for result in results.values() if result)
            total_tests = len(results)
            
            self.logger.info(f"GCP connectivity tests: {successful_tests}/{total_tests} successful")
            
            # Consider connectivity successful if core services work
            core_services = ["AssetInventory", "Compute"]
            core_success = all(results.get(service, False) for service in core_services)
            
            return core_success
            
        except Exception as e:
            self.logger.error(f"GCP connectivity test failed: {str(e)}")
            return False
            
    async def _test_asset_inventory_connectivity(self) -> bool:
        """Test Cloud Asset Inventory API connectivity"""
        try:
            # Try to list assets with limit 1
            parent = f"projects/{self._project_id}"
            request = asset_v1.ListAssetsRequest(
                parent=parent,
                page_size=1
            )
            response = self._asset_client.list_assets(request=request)
            return True
        except Exception:
            return False
            
    async def _test_monitoring_connectivity(self) -> bool:
        """Test Cloud Monitoring API connectivity"""
        try:
            # Try to list metric descriptors
            project_name = f"projects/{self._project_id}"
            request = monitoring_v3.ListMetricDescriptorsRequest(
                name=project_name,
                page_size=1
            )
            response = self._monitoring_client.list_metric_descriptors(request=request)
            return True
        except Exception:
            return False
            
    async def _test_compute_connectivity(self) -> bool:
        """Test Compute Engine API connectivity"""
        try:
            # Try to list instances in all zones
            request = compute_v1.AggregatedListInstancesRequest(
                project=self._project_id,
                max_results=1
            )
            response = self._compute_client.aggregated_list(request=request)
            return True
        except Exception:
            return False
            
    async def _test_storage_connectivity(self) -> bool:
        """Test Cloud Storage API connectivity"""
        try:
            # Try to list buckets
            buckets = list(self._storage_client.list_buckets(max_results=1))
            return True
        except Exception:
            return False
            
    async def collect_data(self, request: CollectionRequest) -> CollectionResponse:
        """
        Collect data from GCP platform
        
        Args:
            request: Collection request with parameters
            
        Returns:
            Collection response with collected data or error information
        """
        start_time = time.time()
        
        try:
            # Initialize GCP clients
            credentials = request.credentials
            
            gcp_creds = GCPCredentials(
                project_id=credentials.get("project_id", ""),
                service_account_key=credentials.get("service_account_key", {})
            )
            
            creds = self._get_gcp_credentials(gcp_creds)
            self._init_clients(creds, gcp_creds.project_id)
            
            # Collect data using Cloud Asset Inventory for efficiency
            collected_data = {}
            total_resources = 0
            
            if not request.target_resources or "all" in request.target_resources:
                # Collect all supported resources
                target_types = self._supported_asset_types
            else:
                # Map request targets to GCP asset types
                target_types = self._map_targets_to_asset_types(request.target_resources)
                
            # Use Cloud Asset Inventory for efficient bulk collection
            asset_data = await self._collect_assets_with_inventory(target_types, request.configuration)
            
            if asset_data:
                # Process and enhance asset data
                for asset_type, assets in asset_data.items():
                    try:
                        enhanced_assets = await self._enhance_asset_data(asset_type, assets, request.configuration)
                        if enhanced_assets:
                            collected_data[asset_type] = {
                                "resources": enhanced_assets,
                                "service": asset_type,
                                "count": len(enhanced_assets)
                            }
                            total_resources += len(enhanced_assets)
                            
                    except Exception as e:
                        self.logger.error(f"Failed to enhance data for {asset_type}: {str(e)}")
                        collected_data[asset_type] = {"error": str(e), "resources": []}
                        
            # Collect performance metrics if requested
            if request.configuration.get("include_metrics", True):
                try:
                    metrics_data = await self._collect_performance_metrics(collected_data)
                    collected_data["metrics"] = metrics_data
                except Exception as e:
                    self.logger.error(f"Failed to collect performance metrics: {str(e)}")
                    collected_data["metrics"] = {"error": str(e)}
                    
            duration = time.time() - start_time
            
            self.logger.info(f"GCP data collection completed: {total_resources} resources in {duration:.2f}s")
            
            return CollectionResponse(
                success=True,
                data=collected_data,
                resource_count=total_resources,
                collection_method=request.collection_method,
                duration_seconds=duration,
                metadata={
                    "project_id": gcp_creds.project_id,
                    "asset_types_collected": list(target_types),
                    "adapter_version": self.metadata.version
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"GCP data collection failed: {str(e)}"
            self.logger.error(error_msg)
            
            return CollectionResponse(
                success=False,
                error_message=error_msg,
                error_details={"exception_type": type(e).__name__},
                duration_seconds=duration,
                metadata={"project_id": gcp_creds.project_id if 'gcp_creds' in locals() else "unknown"}
            )
            
    def _map_targets_to_asset_types(self, targets: List[str]) -> Set[str]:
        """Map request targets to GCP asset types"""
        target_mapping = {
            "Instances": "compute.googleapis.com/Instance",
            "VM": "compute.googleapis.com/Instance",
            "Compute": "compute.googleapis.com/Instance",
            "SQL": "sqladmin.googleapis.com/Instance",
            "Databases": "sqladmin.googleapis.com/Instance",
            "Storage": "storage.googleapis.com/Bucket",
            "Buckets": "storage.googleapis.com/Bucket",
            "GKE": "container.googleapis.com/Cluster",
            "Kubernetes": "container.googleapis.com/Cluster",
            "Functions": "cloudfunctions.googleapis.com/CloudFunction",
            "LoadBalancers": "compute.googleapis.com/ForwardingRule",
            "Networks": "compute.googleapis.com/Network",
            "BigQuery": "bigquery.googleapis.com/Dataset"
        }
        
        mapped_types = set()
        for target in targets:
            if target in target_mapping:
                mapped_types.add(target_mapping[target])
            elif target in self._supported_asset_types:
                mapped_types.add(target)
                
        return mapped_types or self._supported_asset_types
        
    async def _collect_assets_with_inventory(self, asset_types: Set[str], config: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Use Cloud Asset Inventory to efficiently collect asset data"""
        try:
            asset_data = {}
            parent = f"projects/{self._project_id}"
            
            # Build asset type filters
            asset_type_filters = list(asset_types)
            
            # Request assets with content type RESOURCE
            request = asset_v1.ListAssetsRequest(
                parent=parent,
                asset_types=asset_type_filters,
                content_type=asset_v1.ContentType.RESOURCE,
                page_size=1000
            )
            
            # Execute request and process results
            page_result = self._asset_client.list_assets(request=request)
            
            for asset in page_result:
                asset_type = asset.asset_type
                if asset_type not in asset_data:
                    asset_data[asset_type] = []
                    
                # Convert Asset Inventory result to standard format
                asset_dict = {
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "resource": self._proto_to_dict(asset.resource) if asset.resource else {},
                    "ancestors": list(asset.ancestors),
                    "update_time": asset.update_time.isoformat() if asset.update_time else None,
                }
                
                # Extract resource data if available
                if asset.resource and asset.resource.data:
                    resource_data = self._proto_to_dict(asset.resource.data)
                    asset_dict["resource_data"] = resource_data
                    
                asset_data[asset_type].append(asset_dict)
                
            self.logger.info(f"Asset Inventory collected resources across {len(asset_data)} types")
            
            return asset_data
            
        except Exception as e:
            self.logger.error(f"Asset Inventory collection failed: {str(e)}")
            return {}
            
    def _proto_to_dict(self, proto_message) -> Dict[str, Any]:
        """Convert protobuf message to dictionary"""
        try:
            from google.protobuf.json_format import MessageToDict
            return MessageToDict(proto_message, preserving_proto_field_name=True)
        except Exception:
            return {}
            
    async def _enhance_asset_data(self, asset_type: str, assets: List[Dict], config: Dict[str, Any]) -> List[Dict]:
        """Enhance basic asset data with detailed information from specific APIs"""
        try:
            enhanced_assets = []
            
            for asset in assets:
                enhanced_asset = asset.copy()
                
                # Add detailed information based on asset type
                if asset_type == "compute.googleapis.com/Instance":
                    enhanced_asset.update(await self._enhance_compute_instance_data(asset))
                elif asset_type == "sqladmin.googleapis.com/Instance":
                    enhanced_asset.update(await self._enhance_sql_instance_data(asset))
                elif asset_type == "storage.googleapis.com/Bucket":
                    enhanced_asset.update(await self._enhance_storage_bucket_data(asset))
                elif asset_type == "container.googleapis.com/Cluster":
                    enhanced_asset.update(await self._enhance_gke_cluster_data(asset))
                elif asset_type == "cloudfunctions.googleapis.com/CloudFunction":
                    enhanced_asset.update(await self._enhance_cloud_function_data(asset))
                    
                enhanced_assets.append(enhanced_asset)
                
            return enhanced_assets
            
        except Exception as e:
            self.logger.warning(f"Failed to enhance {asset_type} data: {str(e)}")
            return assets  # Return basic data if enhancement fails
            
    async def _enhance_compute_instance_data(self, instance_asset: Dict[str, Any]) -> Dict[str, Any]:
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
                    project=self._project_id,
                    zone=zone,
                    instance=instance_name
                )
                
                instance = self._compute_client.get(request=request)
                
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
        
    async def _enhance_sql_instance_data(self, sql_asset: Dict[str, Any]) -> Dict[str, Any]:
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
                project=self._project_id,
                instance=instance_name
            )
            
            instance = self._sql_client.get(request=request)
            
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
        
    async def _enhance_storage_bucket_data(self, bucket_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Cloud Storage bucket data"""
        try:
            # Extract bucket name from asset name
            # Format: //storage.googleapis.com/projects/_/buckets/{bucket}
            asset_name = bucket_asset.get("name", "")
            if "/buckets/" not in asset_name:
                return {}
                
            bucket_name = asset_name.split("/")[-1]
            
            # Get detailed bucket information
            bucket = self._storage_client.bucket(bucket_name)
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
        
    async def _enhance_gke_cluster_data(self, cluster_asset: Dict[str, Any]) -> Dict[str, Any]:
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
                    name=f"projects/{self._project_id}/locations/{location}/clusters/{cluster_name}"
                )
                
                cluster = self._container_client.get_cluster(request=request)
                
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
        
    async def _enhance_cloud_function_data(self, function_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Cloud Function data"""
        try:
            # Extract function name from asset name
            # Format: //cloudfunctions.googleapis.com/projects/{project}/locations/{location}/functions/{function}
            asset_name = function_asset.get("name", "")
            if "/functions/" not in asset_name:
                return {}
                
            # Get detailed function information
            request = functions_v1.GetFunctionRequest(name=asset_name)
            function = self._functions_client.get_function(request=request)
            
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
        
    async def _collect_performance_metrics(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect Cloud Monitoring performance metrics for discovered resources"""
        try:
            metrics_data = {}
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)  # Last 24 hours
            
            # Collect metrics for Compute Instances
            if "compute.googleapis.com/Instance" in collected_data:
                compute_metrics = await self._collect_compute_metrics(
                    collected_data["compute.googleapis.com/Instance"]["resources"], 
                    start_time, 
                    end_time
                )
                metrics_data["ComputeInstances"] = compute_metrics
                
            # Collect metrics for Cloud SQL Instances
            if "sqladmin.googleapis.com/Instance" in collected_data:
                sql_metrics = await self._collect_sql_metrics(
                    collected_data["sqladmin.googleapis.com/Instance"]["resources"], 
                    start_time, 
                    end_time
                )
                metrics_data["SqlInstances"] = sql_metrics
                
            # Collect metrics for Cloud Functions
            if "cloudfunctions.googleapis.com/CloudFunction" in collected_data:
                function_metrics = await self._collect_function_metrics(
                    collected_data["cloudfunctions.googleapis.com/CloudFunction"]["resources"], 
                    start_time, 
                    end_time
                )
                metrics_data["CloudFunctions"] = function_metrics
                
            return metrics_data
            
        except Exception as e:
            raise Exception(f"Performance metrics collection failed: {str(e)}")
            
    async def _collect_compute_metrics(self, instances: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
        """Collect Cloud Monitoring metrics for Compute Engine instances"""
        metrics = []
        
        for instance in instances:
            asset_name = instance.get("name", "")
            if "/instances/" not in asset_name:
                continue
                
            # Extract instance details
            parts = asset_name.split("/")
            if len(parts) >= 6:
                project_id = parts[2]
                zone = parts[4]
                instance_name = parts[6]
                
                try:
                    # Define metrics to collect
                    metric_filters = [
                        "compute.googleapis.com/instance/cpu/utilization",
                        "compute.googleapis.com/instance/network/received_bytes_count",
                        "compute.googleapis.com/instance/network/sent_bytes_count",
                        "compute.googleapis.com/instance/disk/read_bytes_count",
                        "compute.googleapis.com/instance/disk/write_bytes_count"
                    ]
                    
                    instance_metrics = {
                        "resource_id": asset_name,
                        "resource_type": "ComputeInstance",
                        "resource_name": instance_name,
                        "zone": zone,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Collect each metric
                    for metric_type in metric_filters:
                        try:
                            # Build time series request
                            interval = monitoring_v3.TimeInterval(
                                {
                                    "end_time": {"seconds": int(end_time.timestamp())},
                                    "start_time": {"seconds": int(start_time.timestamp())},
                                }
                            )
                            
                            request = monitoring_v3.ListTimeSeriesRequest(
                                name=f"projects/{self._project_id}",
                                filter=f'metric.type="{metric_type}" AND resource.labels.instance_id="{instance_name}" AND resource.labels.zone="{zone}"',
                                interval=interval,
                                view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                            )
                            
                            results = self._monitoring_client.list_time_series(request=request)
                            
                            # Process results
                            values = []
                            for result in results:
                                for point in result.points:
                                    if point.value.double_value is not None:
                                        values.append(point.value.double_value)
                                    elif point.value.int64_value is not None:
                                        values.append(float(point.value.int64_value))
                                        
                            if values:
                                avg_value = sum(values) / len(values)
                                
                                # Map metric types to standard fields
                                if "cpu/utilization" in metric_type:
                                    instance_metrics["cpu_utilization"] = avg_value * 100  # Convert to percentage
                                elif "network/received_bytes_count" in metric_type:
                                    instance_metrics["network_received_bytes"] = avg_value
                                elif "network/sent_bytes_count" in metric_type:
                                    instance_metrics["network_sent_bytes"] = avg_value
                                elif "disk/read_bytes_count" in metric_type:
                                    instance_metrics["disk_read_bytes"] = avg_value
                                elif "disk/write_bytes_count" in metric_type:
                                    instance_metrics["disk_write_bytes"] = avg_value
                                    
                        except Exception as e:
                            self.logger.warning(f"Failed to collect {metric_type} for instance {instance_name}: {str(e)}")
                            
                    metrics.append(instance_metrics)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to collect metrics for instance {instance_name}: {str(e)}")
                    
        return metrics
        
    async def _collect_sql_metrics(self, instances: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
        """Collect Cloud Monitoring metrics for Cloud SQL instances"""
        metrics = []
        
        for instance in instances:
            asset_name = instance.get("name", "")
            if "/instances/" not in asset_name:
                continue
                
            instance_name = asset_name.split("/")[-1]
            
            try:
                # Define metrics to collect for SQL instances
                metric_filters = [
                    "cloudsql.googleapis.com/database/cpu/utilization",
                    "cloudsql.googleapis.com/database/memory/utilization",
                    "cloudsql.googleapis.com/database/disk/utilization",
                    "cloudsql.googleapis.com/database/network/received_bytes_count",
                    "cloudsql.googleapis.com/database/network/sent_bytes_count"
                ]
                
                sql_metrics = {
                    "resource_id": asset_name,
                    "resource_type": "SqlInstance",
                    "resource_name": instance_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Collect each metric
                for metric_type in metric_filters:
                    try:
                        # Build time series request
                        interval = monitoring_v3.TimeInterval(
                            {
                                "end_time": {"seconds": int(end_time.timestamp())},
                                "start_time": {"seconds": int(start_time.timestamp())},
                            }
                        )
                        
                        request = monitoring_v3.ListTimeSeriesRequest(
                            name=f"projects/{self._project_id}",
                            filter=f'metric.type="{metric_type}" AND resource.labels.database_id="{self._project_id}:{instance_name}"',
                            interval=interval,
                            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        )
                        
                        results = self._monitoring_client.list_time_series(request=request)
                        
                        # Process results
                        values = []
                        for result in results:
                            for point in result.points:
                                if point.value.double_value is not None:
                                    values.append(point.value.double_value)
                                elif point.value.int64_value is not None:
                                    values.append(float(point.value.int64_value))
                                    
                        if values:
                            avg_value = sum(values) / len(values)
                            
                            # Map metric types to standard fields
                            if "cpu/utilization" in metric_type:
                                sql_metrics["cpu_utilization"] = avg_value * 100
                            elif "memory/utilization" in metric_type:
                                sql_metrics["memory_utilization"] = avg_value * 100
                            elif "disk/utilization" in metric_type:
                                sql_metrics["disk_utilization"] = avg_value * 100
                            elif "network/received_bytes_count" in metric_type:
                                sql_metrics["network_received_bytes"] = avg_value
                            elif "network/sent_bytes_count" in metric_type:
                                sql_metrics["network_sent_bytes"] = avg_value
                                
                    except Exception as e:
                        self.logger.warning(f"Failed to collect {metric_type} for SQL instance {instance_name}: {str(e)}")
                        
                metrics.append(sql_metrics)
                
            except Exception as e:
                self.logger.warning(f"Failed to collect metrics for SQL instance {instance_name}: {str(e)}")
                
        return metrics
        
    async def _collect_function_metrics(self, functions: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
        """Collect Cloud Monitoring metrics for Cloud Functions"""
        metrics = []
        
        for function in functions:
            asset_name = function.get("name", "")
            if "/functions/" not in asset_name:
                continue
                
            function_name = asset_name.split("/")[-1]
            
            try:
                # Define metrics to collect for functions
                metric_filters = [
                    "cloudfunctions.googleapis.com/function/executions",
                    "cloudfunctions.googleapis.com/function/execution_times",
                    "cloudfunctions.googleapis.com/function/user_memory_bytes",
                    "cloudfunctions.googleapis.com/function/network_egress"
                ]
                
                function_metrics = {
                    "resource_id": asset_name,
                    "resource_type": "CloudFunction",
                    "resource_name": function_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Collect each metric
                for metric_type in metric_filters:
                    try:
                        # Build time series request
                        interval = monitoring_v3.TimeInterval(
                            {
                                "end_time": {"seconds": int(end_time.timestamp())},
                                "start_time": {"seconds": int(start_time.timestamp())},
                            }
                        )
                        
                        request = monitoring_v3.ListTimeSeriesRequest(
                            name=f"projects/{self._project_id}",
                            filter=f'metric.type="{metric_type}" AND resource.labels.function_name="{function_name}"',
                            interval=interval,
                            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        )
                        
                        results = self._monitoring_client.list_time_series(request=request)
                        
                        # Process results
                        values = []
                        for result in results:
                            for point in result.points:
                                if point.value.double_value is not None:
                                    values.append(point.value.double_value)
                                elif point.value.int64_value is not None:
                                    values.append(float(point.value.int64_value))
                                    
                        if values:
                            if "executions" in metric_type:
                                function_metrics["executions"] = sum(values)
                            else:
                                avg_value = sum(values) / len(values)
                                
                                if "execution_times" in metric_type:
                                    function_metrics["average_execution_time_ms"] = avg_value / 1000000  # Convert from nanoseconds to milliseconds
                                elif "user_memory_bytes" in metric_type:
                                    function_metrics["memory_usage_bytes"] = avg_value
                                elif "network_egress" in metric_type:
                                    function_metrics["network_egress_bytes"] = avg_value
                                    
                    except Exception as e:
                        self.logger.warning(f"Failed to collect {metric_type} for function {function_name}: {str(e)}")
                        
                metrics.append(function_metrics)
                
            except Exception as e:
                self.logger.warning(f"Failed to collect metrics for function {function_name}: {str(e)}")
                
        return metrics
        
    async def get_available_resources(self, configuration: Dict[str, Any]) -> List[str]:
        """
        Get list of available GCP resources for collection
        
        Args:
            configuration: GCP configuration including credentials
            
        Returns:
            List of available asset type identifiers
        """
        try:
            # Test connectivity first
            if not await self.test_connectivity(configuration):
                return []
                
            # Use Asset Inventory to quickly check for asset types
            available_types = []
            
            for asset_type in self._supported_asset_types:
                try:
                    has_resources = await self._check_asset_type_has_resources(asset_type)
                    if has_resources:
                        available_types.append(asset_type)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to check resources for {asset_type}: {str(e)}")
                    
            return available_types
            
        except Exception as e:
            self.logger.error(f"Failed to get available GCP resources: {str(e)}")
            return []
            
    async def _check_asset_type_has_resources(self, asset_type: str) -> bool:
        """Quick check if an asset type has any resources using Asset Inventory"""
        try:
            parent = f"projects/{self._project_id}"
            
            request = asset_v1.ListAssetsRequest(
                parent=parent,
                asset_types=[asset_type],
                page_size=1
            )
            
            page_result = self._asset_client.list_assets(request=request)
            
            # Check if any assets were returned
            for asset in page_result:
                return True
                
            return False
            
        except Exception:
            return False
            
    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw GCP data to normalized format for Discovery Flow
        
        Args:
            raw_data: Raw GCP data from collection
            
        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        try:
            normalized_data = {
                "platform": "GCP",
                "platform_version": "1.0",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
                "metadata": raw_data.get("metadata", {})
            }
            
            # Transform each asset type's resources to normalized assets
            for asset_type, type_data in raw_data.items():
                if asset_type == "metadata" or "error" in type_data:
                    continue
                    
                if "resources" in type_data:
                    for resource in type_data["resources"]:
                        normalized_asset = self._transform_resource_to_asset(asset_type, resource)
                        if normalized_asset:
                            normalized_data["assets"].append(normalized_asset)
                            
            # Transform performance metrics
            if "metrics" in raw_data:
                normalized_data["performance_metrics"] = self._transform_metrics(raw_data["metrics"])
                
            self.logger.info(f"Transformed {len(normalized_data['assets'])} GCP assets to normalized format")
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Failed to transform GCP data: {str(e)}")
            return {
                "platform": "GCP",
                "error": f"Data transformation failed: {str(e)}",
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {}
            }
            
    def _transform_resource_to_asset(self, asset_type: str, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform GCP resource to normalized asset format"""
        try:
            # Common asset structure
            asset = {
                "platform": "GCP",
                "platform_service": asset_type,
                "asset_type": self._get_asset_type(asset_type),
                "unique_id": resource.get("name"),
                "name": self._extract_resource_name(resource.get("name", "")),
                "environment": "cloud",
                "project_id": self._project_id,
                "discovery_method": "automated",
                "discovery_timestamp": datetime.utcnow().isoformat(),
                "raw_data": resource
            }
            
            # Asset-type-specific transformations
            if asset_type == "compute.googleapis.com/Instance":
                asset.update({
                    "compute_type": "virtual_machine",
                    "instance_type": resource.get("machine_type"),
                    "zone": resource.get("zone"),
                    "state": resource.get("status"),
                    "cpu_platform": resource.get("cpu_platform"),
                    "deletion_protection": resource.get("deletion_protection"),
                    "network_interfaces": resource.get("network_interfaces", []),
                    "disks": resource.get("disks", []),
                    "labels": resource.get("labels", {}),
                    "tags": resource.get("tags", {})
                })
                
            elif asset_type == "sqladmin.googleapis.com/Instance":
                asset.update({
                    "database_type": "cloud_sql",
                    "database_version": resource.get("database_version"),
                    "backend_type": resource.get("backend_type"),
                    "instance_type": resource.get("instance_type"),
                    "region": resource.get("region"),
                    "gce_zone": resource.get("gce_zone"),
                    "state": resource.get("state"),
                    "connection_name": resource.get("connection_name"),
                    "settings": resource.get("settings", {})
                })
                
            elif asset_type == "storage.googleapis.com/Bucket":
                asset.update({
                    "storage_type": "object_storage",
                    "location": resource.get("location"),
                    "location_type": resource.get("location_type"),
                    "storage_class": resource.get("storage_class"),
                    "versioning_enabled": resource.get("versioning_enabled"),
                    "uniform_bucket_level_access": resource.get("uniform_bucket_level_access"),
                    "labels": resource.get("labels", {})
                })
                
            elif asset_type == "container.googleapis.com/Cluster":
                asset.update({
                    "compute_type": "kubernetes_cluster",
                    "location": resource.get("location"),
                    "cluster_status": resource.get("status"),
                    "current_master_version": resource.get("current_master_version"),
                    "current_node_version": resource.get("current_node_version"),
                    "current_node_count": resource.get("current_node_count"),
                    "node_pools": resource.get("node_pools", []),
                    "network": resource.get("network"),
                    "subnetwork": resource.get("subnetwork")
                })
                
            elif asset_type == "cloudfunctions.googleapis.com/CloudFunction":
                asset.update({
                    "compute_type": "serverless_function",
                    "runtime": resource.get("runtime"),
                    "entry_point": resource.get("entry_point"),
                    "available_memory_mb": resource.get("available_memory_mb"),
                    "timeout": resource.get("timeout"),
                    "function_status": resource.get("status"),
                    "labels": resource.get("labels", {})
                })
                
            return asset
            
        except Exception as e:
            self.logger.warning(f"Failed to transform {asset_type} resource to asset: {str(e)}")
            return None
            
    def _get_asset_type(self, asset_type: str) -> str:
        """Get normalized asset type for GCP resource"""
        type_map = {
            "compute.googleapis.com/Instance": "server",
            "sqladmin.googleapis.com/Instance": "database",
            "storage.googleapis.com/Bucket": "storage",
            "container.googleapis.com/Cluster": "kubernetes_cluster",
            "cloudfunctions.googleapis.com/CloudFunction": "application",
            "compute.googleapis.com/ForwardingRule": "load_balancer",
            "compute.googleapis.com/UrlMap": "load_balancer",
            "compute.googleapis.com/TargetHttpProxy": "load_balancer",
            "compute.googleapis.com/TargetHttpsProxy": "load_balancer",
            "compute.googleapis.com/BackendService": "load_balancer",
            "compute.googleapis.com/Network": "network",
            "compute.googleapis.com/Subnetwork": "network",
            "compute.googleapis.com/Firewall": "security_group",
            "bigquery.googleapis.com/Dataset": "data_warehouse",
            "bigquery.googleapis.com/Table": "data_warehouse"
        }
        return type_map.get(asset_type, "infrastructure")
        
    def _extract_resource_name(self, resource_name: str) -> str:
        """Extract display name from GCP resource name"""
        if "/" in resource_name:
            return resource_name.split("/")[-1]
        return resource_name
        
    def _transform_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform GCP Cloud Monitoring metrics to normalized format"""
        normalized_metrics = {}
        
        for service, service_metrics in metrics_data.items():
            if isinstance(service_metrics, list):
                normalized_metrics[service] = []
                for metric in service_metrics:
                    normalized_metric = {
                        "resource_id": metric.get("resource_id"),
                        "resource_type": metric.get("resource_type"),
                        "resource_name": metric.get("resource_name"),
                        "timestamp": metric.get("timestamp"),
                        "metrics": {}
                    }
                    
                    # Normalize metric names
                    for key, value in metric.items():
                        if key not in ["resource_id", "resource_type", "resource_name", "timestamp"] and value is not None:
                            normalized_metric["metrics"][key] = value
                            
                    normalized_metrics[service].append(normalized_metric)
                    
        return normalized_metrics


# GCP Adapter metadata for registration
GCP_ADAPTER_METADATA = AdapterMetadata(
    name="gcp_adapter",
    version="1.0.0",
    adapter_type="cloud_platform",
    automation_tier=AutomationTier.TIER_1,
    supported_platforms=["GCP"],
    capabilities=[
        AdapterCapability.SERVER_DISCOVERY,
        AdapterCapability.APPLICATION_DISCOVERY,
        AdapterCapability.DATABASE_DISCOVERY,
        AdapterCapability.NETWORK_DISCOVERY,
        AdapterCapability.DEPENDENCY_MAPPING,
        AdapterCapability.PERFORMANCE_METRICS,
        AdapterCapability.CONFIGURATION_EXPORT,
        AdapterCapability.CREDENTIAL_VALIDATION
    ],
    required_credentials=[
        "project_id",
        "service_account_key"
    ],
    configuration_schema={
        "type": "object",
        "required": ["credentials"],
        "properties": {
            "credentials": {
                "type": "object",
                "required": ["project_id", "service_account_key"],
                "properties": {
                    "project_id": {"type": "string"},
                    "service_account_key": {"type": "object"}
                }
            },
            "include_metrics": {"type": "boolean", "default": True},
            "regions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific regions to collect from (optional)"
            }
        }
    },
    description="Comprehensive GCP platform adapter with Asset Inventory and Monitoring integration",
    author="ADCS Team B1",
    documentation_url="https://cloud.google.com/python/docs/reference"
)