"""
Main AWS Adapter implementation
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
    AWS_SDK_AVAILABLE = True
except ImportError:
    AWS_SDK_AVAILABLE = False
    # Create dummy classes for type hints
    class DummyBoto3:
        class Session:
            pass
    boto3 = DummyBoto3()
    ClientError = NoCredentialsError = PartialCredentialsError = Exception

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.collection_flow.adapters import BaseAdapter, CollectionRequest, CollectionResponse

from .base import AWS_ADAPTER_METADATA, AWSCredentials
from .compute_services import ComputeServicesCollector
from .configuration import ConfigurationCollector
from .container_services import ContainerServicesCollector
from .database_services import DatabaseServicesCollector
from .metrics import MetricsCollector
from .networking_services import NetworkingServicesCollector
from .storage_services import StorageServicesCollector
from .transformation import DataTransformer

logger = logging.getLogger(__name__)


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
    
    def __init__(self, db: AsyncSession, metadata=AWS_ADAPTER_METADATA):
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
        
        # Initialize collectors
        self._compute_collector = None
        self._database_collector = None
        self._networking_collector = None
        self._container_collector = None
        self._storage_collector = None
        self._metrics_collector = None
        self._config_collector = None
        self._transformer = None
        
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
        
        # Initialize collectors
        self._compute_collector = ComputeServicesCollector(self._ec2_client, self._lambda_client)
        self._database_collector = DatabaseServicesCollector(self._rds_client, region)
        self._networking_collector = NetworkingServicesCollector(self._ec2_client, region)
        self._container_collector = ContainerServicesCollector(region)
        self._storage_collector = StorageServicesCollector(region)
        self._metrics_collector = MetricsCollector(self._cloudwatch_client)
        self._config_collector = ConfigurationCollector(self._config_client)
        self._transformer = DataTransformer(region)
        
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
                "EC2": self._compute_collector.test_ec2_connectivity,
                "RDS": self._database_collector.test_rds_connectivity,
                "Lambda": self._compute_collector.test_lambda_connectivity,
                "CloudWatch": self._metrics_collector.test_cloudwatch_connectivity,
                "Config": self._config_collector.test_config_connectivity
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
                    metrics_data = await self._metrics_collector.collect_performance_metrics(collected_data)
                    collected_data["metrics"] = metrics_data
                except Exception as e:
                    self.logger.error(f"Failed to collect performance metrics: {str(e)}")
                    collected_data["metrics"] = {"error": str(e)}
                    
            # Collect configuration data if AWS Config is available
            if request.configuration.get("include_config", True):
                try:
                    config_data = await self._config_collector.collect_configuration_data(collected_data)
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
            "EC2": self._compute_collector.collect_ec2_data,
            "RDS": self._database_collector.collect_rds_data,
            "Lambda": self._compute_collector.collect_lambda_data,
            "ELB": self._networking_collector.collect_elb_data,
            "ELBv2": self._networking_collector.collect_elbv2_data,
            "ECS": self._container_collector.collect_ecs_data,
            "EKS": self._container_collector.collect_eks_data,
            "ElastiCache": self._database_collector.collect_elasticache_data,
            "Redshift": self._database_collector.collect_redshift_data,
            "DynamoDB": self._database_collector.collect_dynamodb_data,
            "S3": self._storage_collector.collect_s3_data,
        }
        
        collector = service_collectors.get(service)
        if collector:
            return await collector(config)
        else:
            return {"error": f"No collector implemented for service: {service}", "resources": []}
            
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
                return await self._compute_collector.check_ec2_has_resources()
            elif service == "RDS":
                return await self._database_collector.check_rds_has_resources()
            elif service == "Lambda":
                return await self._compute_collector.check_lambda_has_resources()
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
        return self._transformer.transform_data(raw_data)