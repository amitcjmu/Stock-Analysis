"""
GCP Authentication and Credentials Management

Handles GCP authentication, credential validation, and client initialization.
"""

from typing import Dict, Any, Optional
import logging

from .dependencies import (
    GCP_AVAILABLE,
    service_account,
    DefaultCredentialsError,
    discovery,
    HttpError,
    asset_v1,
    monitoring_v3,
    compute_v1,
    sql_v1,
    storage,
    container_v1,
    functions_v1
)
from .models import GCPCredentials


class GCPAuthManager:
    """Manages GCP authentication and service client initialization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._credentials = None
        self._project_id = None
        
        # Service clients
        self._asset_client = None
        self._monitoring_client = None
        self._compute_client = None
        self._sql_client = None
        self._storage_client = None
        self._container_client = None
        self._functions_client = None
        
    def get_gcp_credentials(self, credentials: GCPCredentials) -> service_account.Credentials:
        """Create GCP credentials from service account key"""
        if not GCP_AVAILABLE:
            raise ImportError("Google Cloud SDK not installed")
        return service_account.Credentials.from_service_account_info(
            credentials.service_account_key
        )
        
    def init_clients(self, credentials: service_account.Credentials, project_id: str):
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
        if not GCP_AVAILABLE:
            self.logger.error("Google Cloud SDK not installed. Cannot validate GCP credentials.")
            return False
            
        try:
            # Parse credentials
            gcp_creds = GCPCredentials(
                project_id=credentials.get("project_id", ""),
                service_account_key=credentials.get("service_account_key", {})
            )
            
            # Create credentials and test with Resource Manager
            creds = self.get_gcp_credentials(gcp_creds)
            
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
            
    @property
    def project_id(self) -> Optional[str]:
        """Get the current project ID"""
        return self._project_id
        
    @property
    def asset_client(self) -> Optional[asset_v1.AssetServiceClient]:
        """Get the Asset Service client"""
        return self._asset_client
        
    @property
    def monitoring_client(self) -> Optional[monitoring_v3.MetricServiceClient]:
        """Get the Monitoring client"""
        return self._monitoring_client
        
    @property
    def compute_client(self) -> Optional[compute_v1.InstancesClient]:
        """Get the Compute Engine client"""
        return self._compute_client
        
    @property
    def sql_client(self) -> Optional[sql_v1.SqlInstancesServiceClient]:
        """Get the Cloud SQL client"""
        return self._sql_client
        
    @property
    def storage_client(self) -> Optional[storage.Client]:
        """Get the Cloud Storage client"""
        return self._storage_client
        
    @property
    def container_client(self) -> Optional[container_v1.ClusterManagerClient]:
        """Get the Container (GKE) client"""
        return self._container_client
        
    @property
    def functions_client(self) -> Optional[functions_v1.CloudFunctionsServiceClient]:
        """Get the Cloud Functions client"""
        return self._functions_client