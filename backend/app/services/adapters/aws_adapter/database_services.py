"""
AWS Database Services Collection (RDS, DynamoDB, Redshift, ElastiCache)
"""

import logging
from typing import Any, Dict

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

logger = logging.getLogger(__name__)


class DatabaseServicesCollector:
    """Collector for AWS database services"""
    
    def __init__(self, rds_client, region: str):
        self._rds_client = rds_client
        self._region = region
        
    async def collect_rds_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect RDS databases data"""
        try:
            paginator = self._rds_client.get_paginator('describe_db_instances')
            databases = []
            
            for page in paginator.paginate():
                for db_instance in page['DBInstances']:
                    db_data = {
                        "db_instance_identifier": db_instance['DBInstanceIdentifier'],
                        "db_instance_class": db_instance['DBInstanceClass'],
                        "engine": db_instance['Engine'],
                        "engine_version": db_instance['EngineVersion'],
                        "db_instance_status": db_instance['DBInstanceStatus'],
                        "allocated_storage": db_instance.get('AllocatedStorage'),
                        "storage_type": db_instance.get('StorageType'),
                        "multi_az": db_instance.get('MultiAZ'),
                        "availability_zone": db_instance.get('AvailabilityZone'),
                        "vpc_security_groups": [sg['VpcSecurityGroupId'] for sg in db_instance.get('VpcSecurityGroups', [])],
                        "db_subnet_group": db_instance.get('DBSubnetGroup', {}).get('DBSubnetGroupName'),
                        "endpoint": {
                            "address": db_instance.get('Endpoint', {}).get('Address'),
                            "port": db_instance.get('Endpoint', {}).get('Port')
                        },
                        "backup_retention_period": db_instance.get('BackupRetentionPeriod'),
                        "preferred_backup_window": db_instance.get('PreferredBackupWindow'),
                        "preferred_maintenance_window": db_instance.get('PreferredMaintenanceWindow'),
                        "instance_create_time": db_instance.get('InstanceCreateTime').isoformat() if db_instance.get('InstanceCreateTime') else None,
                        "tags": self._get_rds_tags(db_instance['DBInstanceArn']),
                    }
                    databases.append(db_data)
                    
            return {"resources": databases, "service": "RDS", "count": len(databases)}
            
        except Exception as e:
            raise Exception(f"RDS data collection failed: {str(e)}")
            
    async def collect_dynamodb_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect DynamoDB tables data"""
        try:
            dynamodb_client = boto3.client('dynamodb', region_name=self._region)
            tables_data = []
            
            paginator = dynamodb_client.get_paginator('list_tables')
            table_names = []
            
            for page in paginator.paginate():
                table_names.extend(page['TableNames'])
                
            # Describe each table
            for table_name in table_names:
                table_response = dynamodb_client.describe_table(TableName=table_name)
                table = table_response['Table']
                
                table_data = {
                    "table_name": table['TableName'],
                    "table_status": table.get('TableStatus'),
                    "creation_date_time": table.get('CreationDateTime').isoformat() if table.get('CreationDateTime') else None,
                    "provisioned_throughput": table.get('ProvisionedThroughput', {}),
                    "table_size_bytes": table.get('TableSizeBytes'),
                    "item_count": table.get('ItemCount'),
                    "table_arn": table.get('TableArn'),
                    "table_id": table.get('TableId'),
                    "billing_mode_summary": table.get('BillingModeSummary', {}),
                    "local_secondary_indexes": table.get('LocalSecondaryIndexes', []),
                    "global_secondary_indexes": table.get('GlobalSecondaryIndexes', []),
                    "stream_specification": table.get('StreamSpecification', {}),
                    "latest_stream_label": table.get('LatestStreamLabel'),
                    "latest_stream_arn": table.get('LatestStreamArn'),
                    "global_table_version": table.get('GlobalTableVersion'),
                    "replicas": table.get('Replicas', []),
                    "restore_summary": table.get('RestoreSummary', {}),
                    "sse_description": table.get('SSEDescription', {}),
                    "archival_summary": table.get('ArchivalSummary', {}),
                    "table_class_summary": table.get('TableClassSummary', {}),
                    "deletion_protection_enabled": table.get('DeletionProtectionEnabled'),
                    "tags": self._get_dynamodb_tags(table['TableArn']),
                }
                tables_data.append(table_data)
                
            return {"resources": tables_data, "service": "DynamoDB", "count": len(tables_data)}
            
        except Exception as e:
            raise Exception(f"DynamoDB data collection failed: {str(e)}")
            
    async def collect_redshift_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect Redshift clusters data"""
        try:
            redshift_client = boto3.client('redshift', region_name=self._region)
            clusters_data = []
            
            paginator = redshift_client.get_paginator('describe_clusters')
            for page in paginator.paginate():
                for cluster in page['Clusters']:
                    cluster_data = {
                        "cluster_identifier": cluster['ClusterIdentifier'],
                        "node_type": cluster.get('NodeType'),
                        "cluster_status": cluster.get('ClusterStatus'),
                        "cluster_availability_status": cluster.get('ClusterAvailabilityStatus'),
                        "modify_status": cluster.get('ModifyStatus'),
                        "master_username": cluster.get('MasterUsername'),
                        "db_name": cluster.get('DBName'),
                        "endpoint": cluster.get('Endpoint'),
                        "cluster_create_time": cluster.get('ClusterCreateTime').isoformat() if cluster.get('ClusterCreateTime') else None,
                        "automated_snapshot_retention_period": cluster.get('AutomatedSnapshotRetentionPeriod'),
                        "manual_snapshot_retention_period": cluster.get('ManualSnapshotRetentionPeriod'),
                        "cluster_security_groups": cluster.get('ClusterSecurityGroups', []),
                        "vpc_security_groups": cluster.get('VpcSecurityGroups', []),
                        "cluster_parameter_groups": cluster.get('ClusterParameterGroups', []),
                        "cluster_subnet_group_name": cluster.get('ClusterSubnetGroupName'),
                        "vpc_id": cluster.get('VpcId'),
                        "availability_zone": cluster.get('AvailabilityZone'),
                        "preferred_maintenance_window": cluster.get('PreferredMaintenanceWindow'),
                        "pending_modified_values": cluster.get('PendingModifiedValues', {}),
                        "cluster_version": cluster.get('ClusterVersion'),
                        "allow_version_upgrade": cluster.get('AllowVersionUpgrade'),
                        "number_of_nodes": cluster.get('NumberOfNodes'),
                        "publicly_accessible": cluster.get('PubliclyAccessible'),
                        "encrypted": cluster.get('Encrypted'),
                        "restore_status": cluster.get('RestoreStatus'),
                        "data_transfer_progress": cluster.get('DataTransferProgress'),
                        "hsm_status": cluster.get('HsmStatus'),
                        "cluster_snapshot_copy_status": cluster.get('ClusterSnapshotCopyStatus'),
                        "cluster_public_key": cluster.get('ClusterPublicKey'),
                        "cluster_nodes": cluster.get('ClusterNodes', []),
                        "elastic_ip_status": cluster.get('ElasticIpStatus'),
                        "cluster_revision_number": cluster.get('ClusterRevisionNumber'),
                        "tags": cluster.get('Tags', []),
                        "kms_key_id": cluster.get('KmsKeyId'),
                        "enhanced_vpc_routing": cluster.get('EnhancedVpcRouting'),
                        "iam_roles": cluster.get('IamRoles', []),
                        "pending_actions": cluster.get('PendingActions', []),
                        "maintenance_track_name": cluster.get('MaintenanceTrackName'),
                        "elastic_resize_number_of_node_options": cluster.get('ElasticResizeNumberOfNodeOptions'),
                        "deferred_maintenance_windows": cluster.get('DeferredMaintenanceWindows', []),
                        "snapshot_schedule_identifier": cluster.get('SnapshotScheduleIdentifier'),
                        "snapshot_schedule_state": cluster.get('SnapshotScheduleState'),
                        "expected_next_snapshot_schedule_time": cluster.get('ExpectedNextSnapshotScheduleTime').isoformat() if cluster.get('ExpectedNextSnapshotScheduleTime') else None,
                        "expected_next_snapshot_schedule_time_status": cluster.get('ExpectedNextSnapshotScheduleTimeStatus'),
                        "next_maintenance_window_start_time": cluster.get('NextMaintenanceWindowStartTime').isoformat() if cluster.get('NextMaintenanceWindowStartTime') else None,
                        "resize_info": cluster.get('ResizeInfo'),
                        "availability_zone_relocation_status": cluster.get('AvailabilityZoneRelocationStatus'),
                        "cluster_namespace_arn": cluster.get('ClusterNamespaceArn'),
                        "total_storage_capacity_in_mega_bytes": cluster.get('TotalStorageCapacityInMegaBytes'),
                        "aqua_configuration": cluster.get('AquaConfiguration'),
                        "default_iam_role_arn": cluster.get('DefaultIamRoleArn'),
                        "reserved_node_exchange_status": cluster.get('ReservedNodeExchangeStatus'),
                        "custom_domain_name": cluster.get('CustomDomainName'),
                        "custom_domain_certificate_arn": cluster.get('CustomDomainCertificateArn'),
                        "custom_domain_certificate_expiry_date": cluster.get('CustomDomainCertificateExpiryDate').isoformat() if cluster.get('CustomDomainCertificateExpiryDate') else None,
                        "master_password_secret_arn": cluster.get('MasterPasswordSecretArn'),
                        "master_password_secret_kms_key_id": cluster.get('MasterPasswordSecretKmsKeyId'),
                        "ip_address_type": cluster.get('IpAddressType'),
                        "multi_az": cluster.get('MultiAZ'),
                        "multi_az_secondary": cluster.get('MultiAZSecondary'),
                    }
                    clusters_data.append(cluster_data)
                    
            return {"resources": clusters_data, "service": "Redshift", "count": len(clusters_data)}
            
        except Exception as e:
            raise Exception(f"Redshift data collection failed: {str(e)}")
            
    async def collect_elasticache_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect ElastiCache clusters data"""
        try:
            elasticache_client = boto3.client('elasticache', region_name=self._region)
            clusters_data = []
            
            # Get cache clusters
            paginator = elasticache_client.get_paginator('describe_cache_clusters')
            for page in paginator.paginate(ShowCacheNodeInfo=True):
                for cluster in page['CacheClusters']:
                    cluster_data = {
                        "cache_cluster_id": cluster['CacheClusterId'],
                        "configuration_endpoint": cluster.get('ConfigurationEndpoint'),
                        "client_download_landing_page": cluster.get('ClientDownloadLandingPage'),
                        "cache_node_type": cluster.get('CacheNodeType'),
                        "engine": cluster.get('Engine'),
                        "engine_version": cluster.get('EngineVersion'),
                        "cache_cluster_status": cluster.get('CacheClusterStatus'),
                        "num_cache_nodes": cluster.get('NumCacheNodes'),
                        "preferred_availability_zone": cluster.get('PreferredAvailabilityZone'),
                        "preferred_outpost_arn": cluster.get('PreferredOutpostArn'),
                        "cache_cluster_create_time": cluster.get('CacheClusterCreateTime').isoformat() if cluster.get('CacheClusterCreateTime') else None,
                        "preferred_maintenance_window": cluster.get('PreferredMaintenanceWindow'),
                        "pending_modified_values": cluster.get('PendingModifiedValues', {}),
                        "notification_configuration": cluster.get('NotificationConfiguration', {}),
                        "cache_security_groups": cluster.get('CacheSecurityGroups', []),
                        "cache_parameter_group": cluster.get('CacheParameterGroup', {}),
                        "cache_subnet_group_name": cluster.get('CacheSubnetGroupName'),
                        "cache_nodes": cluster.get('CacheNodes', []),
                        "auto_minor_version_upgrade": cluster.get('AutoMinorVersionUpgrade'),
                        "security_groups": cluster.get('SecurityGroups', []),
                        "replication_group_id": cluster.get('ReplicationGroupId'),
                        "snapshot_retention_limit": cluster.get('SnapshotRetentionLimit'),
                        "snapshot_window": cluster.get('SnapshotWindow'),
                        "auth_token_enabled": cluster.get('AuthTokenEnabled'),
                        "auth_token_last_modified_date": cluster.get('AuthTokenLastModifiedDate').isoformat() if cluster.get('AuthTokenLastModifiedDate') else None,
                        "transit_encryption_enabled": cluster.get('TransitEncryptionEnabled'),
                        "at_rest_encryption_enabled": cluster.get('AtRestEncryptionEnabled'),
                        "arn": cluster.get('ARN'),
                        "replication_group_log_delivery_enabled": cluster.get('ReplicationGroupLogDeliveryEnabled'),
                        "log_delivery_configurations": cluster.get('LogDeliveryConfigurations', []),
                        "network_type": cluster.get('NetworkType'),
                        "ip_discovery": cluster.get('IpDiscovery'),
                        "transit_encryption_mode": cluster.get('TransitEncryptionMode'),
                    }
                    clusters_data.append(cluster_data)
                    
            return {"resources": clusters_data, "service": "ElastiCache", "count": len(clusters_data)}
            
        except Exception as e:
            raise Exception(f"ElastiCache data collection failed: {str(e)}")
            
    def _get_rds_tags(self, resource_arn: str) -> Dict[str, str]:
        """Get tags for RDS resource"""
        try:
            response = self._rds_client.list_tags_for_resource(ResourceName=resource_arn)
            return {tag['Key']: tag['Value'] for tag in response.get('TagList', [])}
        except Exception:
            return {}
            
    def _get_dynamodb_tags(self, table_arn: str) -> Dict[str, str]:
        """Get tags for DynamoDB table"""
        try:
            dynamodb_client = boto3.client('dynamodb', region_name=self._region)
            response = dynamodb_client.list_tags_of_resource(ResourceArn=table_arn)
            return {tag['Key']: tag['Value'] for tag in response.get('Tags', [])}
        except Exception:
            return {}
            
    async def test_rds_connectivity(self) -> bool:
        """Test RDS service connectivity"""
        try:
            self._rds_client.describe_db_instances(MaxRecords=1)
            # Service is available even if no instances exist
            return True
        except Exception:
            return False
            
    async def check_rds_has_resources(self) -> bool:
        """Quick check if RDS has any resources"""
        try:
            response = self._rds_client.describe_db_instances(MaxRecords=1)
            return len(response.get('DBInstances', [])) > 0
        except Exception:
            return False