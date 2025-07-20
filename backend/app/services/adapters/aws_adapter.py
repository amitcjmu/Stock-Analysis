"""
AWS Platform Adapter for ADCS Implementation

This adapter provides comprehensive AWS resource discovery and data collection
using CloudWatch for metrics and AWS Config for configuration data.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
    AWS_SDK_AVAILABLE = True
except ImportError:
    AWS_SDK_AVAILABLE = False
    # Create dummy classes for type hints
    boto3 = None
    ClientError = NoCredentialsError = PartialCredentialsError = Exception
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
class AWSCredentials:
    """AWS credentials configuration"""
    access_key_id: str
    secret_access_key: str
    session_token: Optional[str] = None
    region: str = "us-east-1"
    
    
@dataclass
class AWSResourceMetrics:
    """AWS resource performance metrics"""
    resource_id: str
    resource_type: str
    cpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    network_in: Optional[float] = None
    network_out: Optional[float] = None
    disk_read_ops: Optional[float] = None
    disk_write_ops: Optional[float] = None
    timestamp: Optional[datetime] = None


class AWSAdapter(BaseAdapter):
    """
    AWS Platform Adapter implementing BaseAdapter interface
    
    Provides comprehensive AWS resource discovery using:
    - EC2 for compute instances
    - RDS for databases  
    - Lambda for serverless functions
    - CloudWatch for performance metrics
    - AWS Config for configuration data
    - IAM for permission validation
    """
    
    def __init__(self, db: AsyncSession, metadata: AdapterMetadata):
        """Initialize AWS adapter with metadata and session"""
        super().__init__(db, metadata)
        if not AWS_SDK_AVAILABLE:
            logger.warning("AWS SDK (boto3) is not installed. AWS adapter functionality will be limited.")
        self._ec2_client = None
        self._rds_client = None
        self._lambda_client = None
        self._cloudwatch_client = None
        self._config_client = None
        self._iam_client = None
        self._region = "us-east-1"
        self._supported_services = {
            "EC2", "RDS", "Lambda", "ELB", "ELBv2", "ECS", "EKS", 
            "ElastiCache", "Redshift", "DynamoDB", "S3"
        }
        
    def _get_aws_session(self, credentials: AWSCredentials) -> boto3.Session:
        """Create AWS session with provided credentials"""
        return boto3.Session(
            aws_access_key_id=credentials.access_key_id,
            aws_secret_access_key=credentials.secret_access_key,
            aws_session_token=credentials.session_token,
            region_name=credentials.region
        )
        
    def _init_clients(self, session: boto3.Session, region: str):
        """Initialize AWS service clients"""
        self._region = region
        self._ec2_client = session.client('ec2', region_name=region)
        self._rds_client = session.client('rds', region_name=region)
        self._lambda_client = session.client('lambda', region_name=region)
        self._cloudwatch_client = session.client('cloudwatch', region_name=region)
        self._config_client = session.client('config', region_name=region)
        self._iam_client = session.client('iam', region_name=region)
        
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate AWS credentials by attempting to call STS GetCallerIdentity
        
        Args:
            credentials: AWS credentials dictionary
            
        Returns:
            True if credentials are valid, False otherwise
        """
        if not AWS_SDK_AVAILABLE:
            logger.error("AWS SDK (boto3) is not installed. Cannot validate credentials.")
            return False
            
        try:
            # Parse credentials
            aws_creds = AWSCredentials(
                access_key_id=credentials.get("access_key_id", ""),
                secret_access_key=credentials.get("secret_access_key", ""),
                session_token=credentials.get("session_token"),
                region=credentials.get("region", "us-east-1")
            )
            
            # Create session and test credentials
            session = self._get_aws_session(aws_creds)
            sts_client = session.client('sts')
            
            # Test credentials with STS GetCallerIdentity
            response = sts_client.get_caller_identity()
            
            self.logger.info(f"AWS credentials validated for account: {response.get('Account')}")
            return True
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            self.logger.error(f"AWS credentials validation failed: {str(e)}")
            return False
        except ClientError as e:
            self.logger.error(f"AWS API error during credential validation: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error validating AWS credentials: {str(e)}")
            return False
            
    async def test_connectivity(self, configuration: Dict[str, Any]) -> bool:
        """
        Test connectivity to AWS APIs and verify required permissions
        
        Args:
            configuration: AWS configuration including credentials and region
            
        Returns:
            True if connectivity successful, False otherwise
        """
        try:
            # Extract credentials and configuration
            credentials = configuration.get("credentials", {})
            region = configuration.get("region", "us-east-1")
            
            aws_creds = AWSCredentials(
                access_key_id=credentials.get("access_key_id", ""),
                secret_access_key=credentials.get("secret_access_key", ""),
                session_token=credentials.get("session_token"),
                region=region
            )
            
            # Create session and initialize clients
            session = self._get_aws_session(aws_creds)
            self._init_clients(session, region)
            
            # Test connectivity to core services
            connectivity_tests = {
                "EC2": self._test_ec2_connectivity,
                "RDS": self._test_rds_connectivity,
                "Lambda": self._test_lambda_connectivity,
                "CloudWatch": self._test_cloudwatch_connectivity,
                "Config": self._test_config_connectivity
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
            
            self.logger.info(f"AWS connectivity tests: {successful_tests}/{total_tests} successful")
            
            # Consider connectivity successful if at least core services work
            core_services = ["EC2", "CloudWatch"]
            core_success = all(results.get(service, False) for service in core_services)
            
            return core_success
            
        except Exception as e:
            self.logger.error(f"AWS connectivity test failed: {str(e)}")
            return False
            
    async def _test_ec2_connectivity(self) -> bool:
        """Test EC2 service connectivity"""
        try:
            response = self._ec2_client.describe_regions(MaxResults=1)
            return len(response.get('Regions', [])) > 0
        except Exception:
            return False
            
    async def _test_rds_connectivity(self) -> bool:
        """Test RDS service connectivity"""
        try:
            response = self._rds_client.describe_db_instances(MaxRecords=1)
            # Service is available even if no instances exist
            return True
        except Exception:
            return False
            
    async def _test_lambda_connectivity(self) -> bool:
        """Test Lambda service connectivity"""
        try:
            response = self._lambda_client.list_functions(MaxItems=1)
            return True
        except Exception:
            return False
            
    async def _test_cloudwatch_connectivity(self) -> bool:
        """Test CloudWatch service connectivity"""
        try:
            response = self._cloudwatch_client.list_metrics(MaxRecords=1)
            return True
        except Exception:
            return False
            
    async def _test_config_connectivity(self) -> bool:
        """Test AWS Config service connectivity"""
        try:
            response = self._config_client.describe_configuration_recorders()
            return True
        except Exception:
            return False
            
    async def collect_data(self, request: CollectionRequest) -> CollectionResponse:
        """
        Collect data from AWS platform
        
        Args:
            request: Collection request with parameters
            
        Returns:
            Collection response with collected data or error information
        """
        if not AWS_SDK_AVAILABLE:
            return CollectionResponse(
                adapter_id=self.metadata.adapter_id,
                success=False,
                error_message="AWS SDK (boto3) is not installed. Please install boto3 package.",
                collection_metadata={
                    "error": "AWS SDK not available",
                    "suggestion": "Install required package: pip install boto3"
                }
            )
            
        start_time = time.time()
        
        try:
            # Initialize AWS clients
            credentials = request.credentials
            region = request.configuration.get("region", "us-east-1")
            
            aws_creds = AWSCredentials(
                access_key_id=credentials.get("access_key_id", ""),
                secret_access_key=credentials.get("secret_access_key", ""),
                session_token=credentials.get("session_token"),
                region=region
            )
            
            session = self._get_aws_session(aws_creds)
            self._init_clients(session, region)
            
            # Collect data based on target resources
            collected_data = {}
            total_resources = 0
            
            if not request.target_resources or "all" in request.target_resources:
                # Collect all supported resources
                target_services = self._supported_services
            else:
                # Collect specific resources
                target_services = set(request.target_resources) & self._supported_services
                
            # Collect resources from each service
            for service in target_services:
                try:
                    service_data = await self._collect_service_data(service, request.configuration)
                    if service_data:
                        collected_data[service] = service_data
                        total_resources += len(service_data.get("resources", []))
                        
                except Exception as e:
                    self.logger.error(f"Failed to collect data from {service}: {str(e)}")
                    collected_data[service] = {"error": str(e), "resources": []}
                    
            # Collect performance metrics if requested
            if request.configuration.get("include_metrics", True):
                try:
                    metrics_data = await self._collect_performance_metrics(collected_data)
                    collected_data["metrics"] = metrics_data
                except Exception as e:
                    self.logger.error(f"Failed to collect performance metrics: {str(e)}")
                    collected_data["metrics"] = {"error": str(e)}
                    
            # Collect configuration data if AWS Config is available
            if request.configuration.get("include_config", True):
                try:
                    config_data = await self._collect_configuration_data(collected_data)
                    collected_data["configuration"] = config_data
                except Exception as e:
                    self.logger.error(f"Failed to collect configuration data: {str(e)}")
                    collected_data["configuration"] = {"error": str(e)}
                    
            duration = time.time() - start_time
            
            self.logger.info(f"AWS data collection completed: {total_resources} resources in {duration:.2f}s")
            
            return CollectionResponse(
                success=True,
                data=collected_data,
                resource_count=total_resources,
                collection_method=request.collection_method,
                duration_seconds=duration,
                metadata={
                    "region": region,
                    "services_collected": list(target_services),
                    "adapter_version": self.metadata.version
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"AWS data collection failed: {str(e)}"
            self.logger.error(error_msg)
            
            return CollectionResponse(
                success=False,
                error_message=error_msg,
                error_details={"exception_type": type(e).__name__},
                duration_seconds=duration,
                metadata={"region": region if 'region' in locals() else "unknown"}
            )
            
    async def _collect_service_data(self, service: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data from specific AWS service"""
        service_collectors = {
            "EC2": self._collect_ec2_data,
            "RDS": self._collect_rds_data,
            "Lambda": self._collect_lambda_data,
            "ELB": self._collect_elb_data,
            "ELBv2": self._collect_elbv2_data,
            "ECS": self._collect_ecs_data,
            "EKS": self._collect_eks_data,
            "ElastiCache": self._collect_elasticache_data,
            "Redshift": self._collect_redshift_data,
            "DynamoDB": self._collect_dynamodb_data,
            "S3": self._collect_s3_data,
        }
        
        collector = service_collectors.get(service)
        if collector:
            return await collector(config)
        else:
            return {"error": f"No collector implemented for service: {service}", "resources": []}
            
    async def _collect_ec2_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect EC2 instances data"""
        try:
            paginator = self._ec2_client.get_paginator('describe_instances')
            instances = []
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_data = {
                            "instance_id": instance['InstanceId'],
                            "instance_type": instance['InstanceType'],
                            "state": instance['State']['Name'],
                            "launch_time": instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None,
                            "availability_zone": instance.get('Placement', {}).get('AvailabilityZone'),
                            "vpc_id": instance.get('VpcId'),
                            "subnet_id": instance.get('SubnetId'),
                            "private_ip": instance.get('PrivateIpAddress'),
                            "public_ip": instance.get('PublicIpAddress'),
                            "security_groups": [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                            "tags": {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
                            "platform": instance.get('Platform', 'linux'),
                            "architecture": instance.get('Architecture'),
                            "virtualization_type": instance.get('VirtualizationType'),
                            "monitoring": instance.get('Monitoring', {}).get('State'),
                        }
                        instances.append(instance_data)
                        
            return {"resources": instances, "service": "EC2", "count": len(instances)}
            
        except Exception as e:
            raise Exception(f"EC2 data collection failed: {str(e)}")
            
    async def _collect_rds_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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
            
    async def _collect_lambda_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect Lambda functions data"""
        try:
            paginator = self._lambda_client.get_paginator('list_functions')
            functions = []
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    function_data = {
                        "function_name": function['FunctionName'],
                        "function_arn": function['FunctionArn'],
                        "runtime": function.get('Runtime'),
                        "role": function.get('Role'),
                        "handler": function.get('Handler'),
                        "code_size": function.get('CodeSize'),
                        "description": function.get('Description'),
                        "timeout": function.get('Timeout'),
                        "memory_size": function.get('MemorySize'),
                        "last_modified": function.get('LastModified'),
                        "code_sha256": function.get('CodeSha256'),
                        "version": function.get('Version'),
                        "vpc_config": function.get('VpcConfig'),
                        "environment": function.get('Environment'),
                        "dead_letter_config": function.get('DeadLetterConfig'),
                        "kms_key_arn": function.get('KMSKeyArn'),
                        "tracing_config": function.get('TracingConfig'),
                        "layers": function.get('Layers', []),
                        "state": function.get('State'),
                        "state_reason": function.get('StateReason'),
                        "tags": self._get_lambda_tags(function['FunctionArn']),
                    }
                    functions.append(function_data)
                    
            return {"resources": functions, "service": "Lambda", "count": len(functions)}
            
        except Exception as e:
            raise Exception(f"Lambda data collection failed: {str(e)}")
            
    async def _collect_elb_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect Classic Load Balancer data"""
        try:
            elb_client = self._ec2_client.meta.client._client_config.region_name
            elb_client = boto3.client('elb', region_name=self._region)
            
            paginator = elb_client.get_paginator('describe_load_balancers')
            load_balancers = []
            
            for page in paginator.paginate():
                for lb in page['LoadBalancerDescriptions']:
                    lb_data = {
                        "load_balancer_name": lb['LoadBalancerName'],
                        "dns_name": lb['DNSName'],
                        "canonical_hosted_zone_name": lb.get('CanonicalHostedZoneName'),
                        "canonical_hosted_zone_name_id": lb.get('CanonicalHostedZoneNameID'),
                        "listeners": lb.get('ListenerDescriptions', []),
                        "policies": lb.get('Policies', {}),
                        "backend_server_descriptions": lb.get('BackendServerDescriptions', []),
                        "availability_zones": lb.get('AvailabilityZones', []),
                        "subnets": lb.get('Subnets', []),
                        "vpc_id": lb.get('VPCId'),
                        "instances": [inst['InstanceId'] for inst in lb.get('Instances', [])],
                        "health_check": lb.get('HealthCheck', {}),
                        "source_security_group": lb.get('SourceSecurityGroup', {}),
                        "security_groups": lb.get('SecurityGroups', []),
                        "created_time": lb.get('CreatedTime').isoformat() if lb.get('CreatedTime') else None,
                        "scheme": lb.get('Scheme'),
                        "tags": self._get_elb_tags(lb['LoadBalancerName']),
                    }
                    load_balancers.append(lb_data)
                    
            return {"resources": load_balancers, "service": "ELB", "count": len(load_balancers)}
            
        except Exception as e:
            raise Exception(f"ELB data collection failed: {str(e)}")
            
    async def _collect_elbv2_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect Application/Network Load Balancer data"""
        try:
            elbv2_client = boto3.client('elbv2', region_name=self._region)
            
            paginator = elbv2_client.get_paginator('describe_load_balancers')
            load_balancers = []
            
            for page in paginator.paginate():
                for lb in page['LoadBalancers']:
                    lb_data = {
                        "load_balancer_arn": lb['LoadBalancerArn'],
                        "load_balancer_name": lb['LoadBalancerName'],
                        "dns_name": lb['DNSName'],
                        "canonical_hosted_zone_id": lb.get('CanonicalHostedZoneId'),
                        "created_time": lb.get('CreatedTime').isoformat() if lb.get('CreatedTime') else None,
                        "load_balancer_type": lb.get('Type'),
                        "scheme": lb.get('Scheme'),
                        "vpc_id": lb.get('VpcId'),
                        "state": lb.get('State', {}),
                        "ip_address_type": lb.get('IpAddressType'),
                        "security_groups": lb.get('SecurityGroups', []),
                        "availability_zones": lb.get('AvailabilityZones', []),
                        "tags": self._get_elbv2_tags(lb['LoadBalancerArn']),
                    }
                    load_balancers.append(lb_data)
                    
            return {"resources": load_balancers, "service": "ELBv2", "count": len(load_balancers)}
            
        except Exception as e:
            raise Exception(f"ELBv2 data collection failed: {str(e)}")
            
    async def _collect_ecs_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect ECS clusters and services data"""
        try:
            ecs_client = boto3.client('ecs', region_name=self._region)
            clusters_data = []
            
            # Get clusters
            paginator = ecs_client.get_paginator('list_clusters')
            cluster_arns = []
            
            for page in paginator.paginate():
                cluster_arns.extend(page['clusterArns'])
                
            if cluster_arns:
                # Describe clusters in batches
                for i in range(0, len(cluster_arns), 100):
                    batch = cluster_arns[i:i+100]
                    response = ecs_client.describe_clusters(clusters=batch, include=['CONFIGURATIONS', 'STATISTICS'])
                    
                    for cluster in response['clusters']:
                        cluster_data = {
                            "cluster_arn": cluster['clusterArn'],
                            "cluster_name": cluster['clusterName'],
                            "status": cluster['status'],
                            "running_tasks_count": cluster.get('runningTasksCount', 0),
                            "pending_tasks_count": cluster.get('pendingTasksCount', 0),
                            "active_services_count": cluster.get('activeServicesCount', 0),
                            "statistics": cluster.get('statistics', []),
                            "configurations": cluster.get('configurations', []),
                            "capacity_providers": cluster.get('capacityProviders', []),
                            "default_capacity_provider_strategy": cluster.get('defaultCapacityProviderStrategy', []),
                            "tags": cluster.get('tags', []),
                        }
                        clusters_data.append(cluster_data)
                        
            return {"resources": clusters_data, "service": "ECS", "count": len(clusters_data)}
            
        except Exception as e:
            raise Exception(f"ECS data collection failed: {str(e)}")
            
    async def _collect_eks_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect EKS clusters data"""
        try:
            eks_client = boto3.client('eks', region_name=self._region)
            clusters_data = []
            
            # List clusters
            paginator = eks_client.get_paginator('list_clusters')
            cluster_names = []
            
            for page in paginator.paginate():
                cluster_names.extend(page['clusters'])
                
            # Describe each cluster
            for cluster_name in cluster_names:
                cluster_response = eks_client.describe_cluster(name=cluster_name)
                cluster = cluster_response['cluster']
                
                cluster_data = {
                    "cluster_name": cluster['name'],
                    "cluster_arn": cluster['arn'],
                    "created_at": cluster.get('createdAt').isoformat() if cluster.get('createdAt') else None,
                    "version": cluster.get('version'),
                    "endpoint": cluster.get('endpoint'),
                    "role_arn": cluster.get('roleArn'),
                    "resources_vpc_config": cluster.get('resourcesVpcConfig', {}),
                    "kubernetes_network_config": cluster.get('kubernetesNetworkConfig', {}),
                    "logging": cluster.get('logging', {}),
                    "identity": cluster.get('identity', {}),
                    "status": cluster.get('status'),
                    "certificate_authority": cluster.get('certificateAuthority', {}),
                    "platform_version": cluster.get('platformVersion'),
                    "tags": cluster.get('tags', {}),
                    "encryption_config": cluster.get('encryptionConfig', []),
                }
                clusters_data.append(cluster_data)
                
            return {"resources": clusters_data, "service": "EKS", "count": len(clusters_data)}
            
        except Exception as e:
            raise Exception(f"EKS data collection failed: {str(e)}")
            
    async def _collect_elasticache_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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
            
    async def _collect_redshift_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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
            
    async def _collect_dynamodb_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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
            
    async def _collect_s3_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect S3 buckets data"""
        try:
            s3_client = boto3.client('s3', region_name=self._region)
            buckets_data = []
            
            # List buckets
            response = s3_client.list_buckets()
            
            for bucket in response['Buckets']:
                bucket_name = bucket['Name']
                
                try:
                    # Get bucket location
                    location_response = s3_client.get_bucket_location(Bucket=bucket_name)
                    bucket_region = location_response.get('LocationConstraint') or 'us-east-1'
                    
                    # Only collect buckets in the current region or if no region filter
                    if bucket_region == self._region or config.get('collect_all_regions', False):
                        bucket_data = {
                            "bucket_name": bucket_name,
                            "creation_date": bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None,
                            "region": bucket_region,
                            "tags": self._get_s3_bucket_tags(bucket_name),
                        }
                        
                        # Get additional bucket properties
                        try:
                            # Versioning
                            versioning_response = s3_client.get_bucket_versioning(Bucket=bucket_name)
                            bucket_data["versioning"] = versioning_response.get('Status', 'Disabled')
                            
                            # Encryption
                            try:
                                encryption_response = s3_client.get_bucket_encryption(Bucket=bucket_name)
                                bucket_data["encryption"] = encryption_response.get('ServerSideEncryptionConfiguration', {})
                            except ClientError as e:
                                if e.response['Error']['Code'] != 'ServerSideEncryptionConfigurationNotFoundError':
                                    raise
                                bucket_data["encryption"] = {}
                                
                            # Public access block
                            try:
                                public_access_response = s3_client.get_public_access_block(Bucket=bucket_name)
                                bucket_data["public_access_block"] = public_access_response.get('PublicAccessBlockConfiguration', {})
                            except ClientError as e:
                                if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
                                    raise
                                bucket_data["public_access_block"] = {}
                                
                        except ClientError as e:
                            # Handle permission errors gracefully
                            if e.response['Error']['Code'] in ['AccessDenied', 'AllAccessDisabled']:
                                bucket_data["access_error"] = str(e)
                            else:
                                raise
                                
                        buckets_data.append(bucket_data)
                        
                except ClientError as e:
                    # Handle permission errors for bucket location
                    if e.response['Error']['Code'] in ['AccessDenied', 'AllAccessDisabled']:
                        bucket_data = {
                            "bucket_name": bucket_name,
                            "creation_date": bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None,
                            "region": "unknown",
                            "access_error": str(e),
                        }
                        buckets_data.append(bucket_data)
                    else:
                        raise
                        
            return {"resources": buckets_data, "service": "S3", "count": len(buckets_data)}
            
        except Exception as e:
            raise Exception(f"S3 data collection failed: {str(e)}")
            
    async def _collect_performance_metrics(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect CloudWatch performance metrics for discovered resources"""
        try:
            metrics_data = {}
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)  # Last 24 hours
            
            # Collect metrics for EC2 instances
            if "EC2" in collected_data:
                ec2_metrics = await self._collect_ec2_metrics(
                    collected_data["EC2"]["resources"], start_time, end_time
                )
                metrics_data["EC2"] = ec2_metrics
                
            # Collect metrics for RDS instances
            if "RDS" in collected_data:
                rds_metrics = await self._collect_rds_metrics(
                    collected_data["RDS"]["resources"], start_time, end_time
                )
                metrics_data["RDS"] = rds_metrics
                
            # Collect metrics for Lambda functions
            if "Lambda" in collected_data:
                lambda_metrics = await self._collect_lambda_metrics(
                    collected_data["Lambda"]["resources"], start_time, end_time
                )
                metrics_data["Lambda"] = lambda_metrics
                
            return metrics_data
            
        except Exception as e:
            raise Exception(f"Performance metrics collection failed: {str(e)}")
            
    async def _collect_ec2_metrics(self, instances: List[Dict], start_time: datetime, end_time: datetime) -> List[AWSResourceMetrics]:
        """Collect CloudWatch metrics for EC2 instances"""
        metrics = []
        
        for instance in instances:
            instance_id = instance["instance_id"]
            
            try:
                # Get CPU utilization
                cpu_response = self._cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour
                    Statistics=['Average']
                )
                
                # Get network metrics
                network_in_response = self._cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkIn',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                network_out_response = self._cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkOut',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                # Calculate averages
                cpu_avg = None
                if cpu_response['Datapoints']:
                    cpu_avg = sum(dp['Average'] for dp in cpu_response['Datapoints']) / len(cpu_response['Datapoints'])
                    
                network_in_avg = None
                if network_in_response['Datapoints']:
                    network_in_avg = sum(dp['Sum'] for dp in network_in_response['Datapoints']) / len(network_in_response['Datapoints'])
                    
                network_out_avg = None
                if network_out_response['Datapoints']:
                    network_out_avg = sum(dp['Sum'] for dp in network_out_response['Datapoints']) / len(network_out_response['Datapoints'])
                    
                instance_metrics = AWSResourceMetrics(
                    resource_id=instance_id,
                    resource_type="EC2Instance",
                    cpu_utilization=cpu_avg,
                    network_in=network_in_avg,
                    network_out=network_out_avg,
                    timestamp=datetime.utcnow()
                )
                
                metrics.append(instance_metrics.__dict__)
                
            except Exception as e:
                self.logger.warning(f"Failed to collect metrics for EC2 instance {instance_id}: {str(e)}")
                
        return metrics
        
    async def _collect_rds_metrics(self, databases: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
        """Collect CloudWatch metrics for RDS instances"""
        metrics = []
        
        for db in databases:
            db_id = db["db_instance_identifier"]
            
            try:
                # Get CPU utilization
                cpu_response = self._cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                # Get database connections
                connections_response = self._cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='DatabaseConnections',
                    Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                # Calculate averages
                cpu_avg = None
                if cpu_response['Datapoints']:
                    cpu_avg = sum(dp['Average'] for dp in cpu_response['Datapoints']) / len(cpu_response['Datapoints'])
                    
                connections_avg = None
                if connections_response['Datapoints']:
                    connections_avg = sum(dp['Average'] for dp in connections_response['Datapoints']) / len(connections_response['Datapoints'])
                    
                db_metrics = AWSResourceMetrics(
                    resource_id=db_id,
                    resource_type="RDSInstance",
                    cpu_utilization=cpu_avg,
                    timestamp=datetime.utcnow()
                )
                
                # Add custom field for database connections
                db_metrics_dict = db_metrics.__dict__
                db_metrics_dict["database_connections"] = connections_avg
                
                metrics.append(db_metrics_dict)
                
            except Exception as e:
                self.logger.warning(f"Failed to collect metrics for RDS instance {db_id}: {str(e)}")
                
        return metrics
        
    async def _collect_lambda_metrics(self, functions: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
        """Collect CloudWatch metrics for Lambda functions"""
        metrics = []
        
        for func in functions:
            func_name = func["function_name"]
            
            try:
                # Get invocation count
                invocations_response = self._cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                # Get duration
                duration_response = self._cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Duration',
                    Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                # Get errors
                errors_response = self._cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Errors',
                    Dimensions=[{'Name': 'FunctionName', 'Value': func_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                # Calculate metrics
                invocations_total = sum(dp['Sum'] for dp in invocations_response['Datapoints']) if invocations_response['Datapoints'] else 0
                duration_avg = None
                if duration_response['Datapoints']:
                    duration_avg = sum(dp['Average'] for dp in duration_response['Datapoints']) / len(duration_response['Datapoints'])
                    
                errors_total = sum(dp['Sum'] for dp in errors_response['Datapoints']) if errors_response['Datapoints'] else 0
                
                func_metrics = {
                    "resource_id": func_name,
                    "resource_type": "LambdaFunction",
                    "invocations": invocations_total,
                    "average_duration_ms": duration_avg,
                    "errors": errors_total,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                metrics.append(func_metrics)
                
            except Exception as e:
                self.logger.warning(f"Failed to collect metrics for Lambda function {func_name}: {str(e)}")
                
        return metrics
        
    async def _collect_configuration_data(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect AWS Config configuration data for discovered resources"""
        try:
            config_data = {}
            
            # Check if AWS Config is enabled
            try:
                recorders = self._config_client.describe_configuration_recorders()
                if not recorders.get('ConfigurationRecorders'):
                    return {"error": "AWS Config is not enabled in this region"}
                    
                # Get configuration items for discovered resources
                for service, service_data in collected_data.items():
                    if service in ["EC2", "RDS", "Lambda"] and "resources" in service_data:
                        service_config = await self._get_service_configuration(service, service_data["resources"])
                        if service_config:
                            config_data[service] = service_config
                            
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchConfigurationRecorderException':
                    return {"error": "AWS Config service is not configured"}
                else:
                    raise
                    
            return config_data
            
        except Exception as e:
            raise Exception(f"Configuration data collection failed: {str(e)}")
            
    async def _get_service_configuration(self, service: str, resources: List[Dict]) -> List[Dict]:
        """Get AWS Config configuration data for specific service resources"""
        config_items = []
        
        # Map service to Config resource types
        resource_type_map = {
            "EC2": "AWS::EC2::Instance",
            "RDS": "AWS::RDS::DBInstance",
            "Lambda": "AWS::Lambda::Function"
        }
        
        resource_type = resource_type_map.get(service)
        if not resource_type:
            return config_items
            
        # Get configuration for each resource
        for resource in resources[:10]:  # Limit to first 10 for performance
            resource_id = None
            if service == "EC2":
                resource_id = resource.get("instance_id")
            elif service == "RDS":
                resource_id = resource.get("db_instance_identifier")
            elif service == "Lambda":
                resource_id = resource.get("function_name")
                
            if resource_id:
                try:
                    response = self._config_client.get_resource_config_history(
                        resourceType=resource_type,
                        resourceId=resource_id,
                        limit=1
                    )
                    
                    if response.get('configurationItems'):
                        config_item = response['configurationItems'][0]
                        config_items.append({
                            "resource_id": resource_id,
                            "resource_type": resource_type,
                            "configuration_state": config_item.get('configurationItemStatus'),
                            "configuration": config_item.get('configuration', {}),
                            "configuration_item_capture_time": config_item.get('configurationItemCaptureTime').isoformat() if config_item.get('configurationItemCaptureTime') else None,
                            "availability_zone": config_item.get('availabilityZone'),
                            "aws_region": config_item.get('awsRegion'),
                            "tags": config_item.get('tags', {}),
                            "relationships": config_item.get('relationships', [])
                        })
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get Config data for {service} resource {resource_id}: {str(e)}")
                    
        return config_items
        
    async def get_available_resources(self, configuration: Dict[str, Any]) -> List[str]:
        """
        Get list of available AWS resources for collection
        
        Args:
            configuration: AWS configuration including credentials and region
            
        Returns:
            List of available resource identifiers
        """
        try:
            # Test connectivity first
            if not await self.test_connectivity(configuration):
                return []
                
            available_resources = []
            
            # Check which services have resources
            for service in self._supported_services:
                try:
                    # Quick check if service has resources
                    has_resources = await self._check_service_has_resources(service)
                    if has_resources:
                        available_resources.append(service)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to check resources for {service}: {str(e)}")
                    
            return available_resources
            
        except Exception as e:
            self.logger.error(f"Failed to get available AWS resources: {str(e)}")
            return []
            
    async def _check_service_has_resources(self, service: str) -> bool:
        """Quick check if a service has any resources"""
        try:
            if service == "EC2":
                response = self._ec2_client.describe_instances(MaxResults=1)
                return len(response.get('Reservations', [])) > 0
            elif service == "RDS":
                response = self._rds_client.describe_db_instances(MaxRecords=1)
                return len(response.get('DBInstances', [])) > 0
            elif service == "Lambda":
                response = self._lambda_client.list_functions(MaxItems=1)
                return len(response.get('Functions', [])) > 0
            else:
                # For other services, assume they might have resources
                return True
                
        except Exception:
            return False
            
    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw AWS data to normalized format for Discovery Flow
        
        Args:
            raw_data: Raw AWS data from collection
            
        Returns:
            Normalized data structure compatible with Discovery Flow
        """
        try:
            normalized_data = {
                "platform": "AWS",
                "platform_version": "1.0",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {},
                "metadata": raw_data.get("metadata", {})
            }
            
            # Transform each service's resources to normalized assets
            for service, service_data in raw_data.items():
                if service == "metadata" or "error" in service_data:
                    continue
                    
                if "resources" in service_data:
                    for resource in service_data["resources"]:
                        normalized_asset = self._transform_resource_to_asset(service, resource)
                        if normalized_asset:
                            normalized_data["assets"].append(normalized_asset)
                            
            # Transform performance metrics
            if "metrics" in raw_data:
                normalized_data["performance_metrics"] = self._transform_metrics(raw_data["metrics"])
                
            # Transform configuration data
            if "configuration" in raw_data:
                normalized_data["configuration"] = raw_data["configuration"]
                
            self.logger.info(f"Transformed {len(normalized_data['assets'])} AWS assets to normalized format")
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Failed to transform AWS data: {str(e)}")
            return {
                "platform": "AWS",
                "error": f"Data transformation failed: {str(e)}",
                "assets": [],
                "dependencies": [],
                "performance_metrics": {},
                "configuration": {}
            }
            
    def _transform_resource_to_asset(self, service: str, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform AWS resource to normalized asset format"""
        try:
            # Common asset structure
            asset = {
                "platform": "AWS",
                "platform_service": service,
                "asset_type": self._get_asset_type(service, resource),
                "unique_id": self._get_resource_unique_id(service, resource),
                "name": self._get_resource_name(service, resource),
                "environment": "cloud",
                "region": self._region,
                "tags": resource.get("tags", {}),
                "discovery_method": "automated",
                "discovery_timestamp": datetime.utcnow().isoformat(),
                "raw_data": resource
            }
            
            # Service-specific transformations
            if service == "EC2":
                asset.update({
                    "compute_type": "virtual_machine",
                    "instance_type": resource.get("instance_type"),
                    "state": resource.get("state"),
                    "ip_addresses": {
                        "private": resource.get("private_ip"),
                        "public": resource.get("public_ip")
                    },
                    "network": {
                        "vpc_id": resource.get("vpc_id"),
                        "subnet_id": resource.get("subnet_id"),
                        "security_groups": resource.get("security_groups", [])
                    },
                    "operating_system": resource.get("platform", "linux"),
                    "architecture": resource.get("architecture")
                })
                
            elif service == "RDS":
                asset.update({
                    "database_type": resource.get("engine"),
                    "database_version": resource.get("engine_version"),
                    "instance_class": resource.get("db_instance_class"),
                    "storage": {
                        "allocated": resource.get("allocated_storage"),
                        "type": resource.get("storage_type")
                    },
                    "multi_az": resource.get("multi_az"),
                    "endpoint": resource.get("endpoint", {})
                })
                
            elif service == "Lambda":
                asset.update({
                    "compute_type": "serverless_function",
                    "runtime": resource.get("runtime"),
                    "memory_size": resource.get("memory_size"),
                    "timeout": resource.get("timeout"),
                    "code_size": resource.get("code_size")
                })
                
            return asset
            
        except Exception as e:
            self.logger.warning(f"Failed to transform {service} resource to asset: {str(e)}")
            return None
            
    def _get_asset_type(self, service: str, resource: Dict[str, Any]) -> str:
        """Get normalized asset type for AWS resource"""
        type_map = {
            "EC2": "server",
            "RDS": "database",
            "Lambda": "application",
            "ELB": "load_balancer",
            "ELBv2": "load_balancer",
            "ECS": "container_service",
            "EKS": "kubernetes_cluster",
            "ElastiCache": "cache",
            "Redshift": "data_warehouse",
            "DynamoDB": "nosql_database",
            "S3": "storage"
        }
        return type_map.get(service, "infrastructure")
        
    def _get_resource_unique_id(self, service: str, resource: Dict[str, Any]) -> str:
        """Get unique identifier for AWS resource"""
        id_fields = {
            "EC2": "instance_id",
            "RDS": "db_instance_identifier",
            "Lambda": "function_arn",
            "ELB": "load_balancer_name",
            "ELBv2": "load_balancer_arn",
            "ECS": "cluster_arn",
            "EKS": "cluster_arn",
            "ElastiCache": "cache_cluster_id",
            "Redshift": "cluster_identifier",
            "DynamoDB": "table_arn",
            "S3": "bucket_name"
        }
        
        field = id_fields.get(service, "id")
        return resource.get(field, f"unknown-{service}-{id(resource)}")
        
    def _get_resource_name(self, service: str, resource: Dict[str, Any]) -> str:
        """Get display name for AWS resource"""
        name_fields = {
            "EC2": ["instance_id", "tags.Name"],
            "RDS": ["db_instance_identifier"],
            "Lambda": ["function_name"],
            "ELB": ["load_balancer_name"],
            "ELBv2": ["load_balancer_name"],
            "ECS": ["cluster_name"],
            "EKS": ["cluster_name"],
            "ElastiCache": ["cache_cluster_id"],
            "Redshift": ["cluster_identifier"],
            "DynamoDB": ["table_name"],
            "S3": ["bucket_name"]
        }
        
        fields = name_fields.get(service, ["id"])
        for field in fields:
            if "." in field:
                # Handle nested fields like tags.Name
                parts = field.split(".")
                value = resource
                for part in parts:
                    value = value.get(part, {}) if isinstance(value, dict) else {}
                if value:
                    return str(value)
            else:
                value = resource.get(field)
                if value:
                    return str(value)
                    
        return f"Unknown {service} Resource"
        
    def _transform_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AWS CloudWatch metrics to normalized format"""
        normalized_metrics = {}
        
        for service, service_metrics in metrics_data.items():
            if isinstance(service_metrics, list):
                normalized_metrics[service] = []
                for metric in service_metrics:
                    normalized_metric = {
                        "resource_id": metric.get("resource_id"),
                        "resource_type": metric.get("resource_type"),
                        "timestamp": metric.get("timestamp"),
                        "metrics": {}
                    }
                    
                    # Normalize metric names
                    for key, value in metric.items():
                        if key not in ["resource_id", "resource_type", "timestamp"] and value is not None:
                            normalized_metric["metrics"][key] = value
                            
                    normalized_metrics[service].append(normalized_metric)
                    
        return normalized_metrics
        
    # Helper methods for collecting tags
    def _get_rds_tags(self, resource_arn: str) -> Dict[str, str]:
        """Get tags for RDS resource"""
        try:
            response = self._rds_client.list_tags_for_resource(ResourceName=resource_arn)
            return {tag['Key']: tag['Value'] for tag in response.get('TagList', [])}
        except Exception:
            return {}
            
    def _get_lambda_tags(self, function_arn: str) -> Dict[str, str]:
        """Get tags for Lambda function"""
        try:
            response = self._lambda_client.list_tags(Resource=function_arn)
            return response.get('Tags', {})
        except Exception:
            return {}
            
    def _get_elb_tags(self, load_balancer_name: str) -> Dict[str, str]:
        """Get tags for Classic Load Balancer"""
        try:
            elb_client = boto3.client('elb', region_name=self._region)
            response = elb_client.describe_tags(LoadBalancerNames=[load_balancer_name])
            if response.get('TagDescriptions'):
                return {tag['Key']: tag['Value'] for tag in response['TagDescriptions'][0].get('Tags', [])}
            return {}
        except Exception:
            return {}
            
    def _get_elbv2_tags(self, load_balancer_arn: str) -> Dict[str, str]:
        """Get tags for Application/Network Load Balancer"""
        try:
            elbv2_client = boto3.client('elbv2', region_name=self._region)
            response = elbv2_client.describe_tags(ResourceArns=[load_balancer_arn])
            if response.get('TagDescriptions'):
                return {tag['Key']: tag['Value'] for tag in response['TagDescriptions'][0].get('Tags', [])}
            return {}
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
            
    def _get_s3_bucket_tags(self, bucket_name: str) -> Dict[str, str]:
        """Get tags for S3 bucket"""
        try:
            s3_client = boto3.client('s3', region_name=self._region)
            response = s3_client.get_bucket_tagging(Bucket=bucket_name)
            return {tag['Key']: tag['Value'] for tag in response.get('TagSet', [])}
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                return {}
            raise
        except Exception:
            return {}


# AWS Adapter metadata for registration
AWS_ADAPTER_METADATA = AdapterMetadata(
    name="aws_adapter",
    version="1.0.0",
    adapter_type="cloud_platform",
    automation_tier=AutomationTier.TIER_1,
    supported_platforms=["AWS"],
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
        "access_key_id",
        "secret_access_key"
    ],
    configuration_schema={
        "type": "object",
        "required": ["credentials", "region"],
        "properties": {
            "credentials": {
                "type": "object",
                "required": ["access_key_id", "secret_access_key"],
                "properties": {
                    "access_key_id": {"type": "string"},
                    "secret_access_key": {"type": "string"},
                    "session_token": {"type": "string"},
                    "region": {"type": "string", "default": "us-east-1"}
                }
            },
            "region": {"type": "string", "default": "us-east-1"},
            "include_metrics": {"type": "boolean", "default": True},
            "include_config": {"type": "boolean", "default": True},
            "collect_all_regions": {"type": "boolean", "default": False}
        }
    },
    description="Comprehensive AWS platform adapter with CloudWatch and Config integration",
    author="ADCS Team B1",
    documentation_url="https://docs.aws.amazon.com/sdk-for-python/"
)