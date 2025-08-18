"""
GCP Authentication and Credentials Management

Handles GCP authentication, credential validation, and client initialization.
"""

import logging
from typing import Any, Dict, Optional

from .dependencies import (
    GCP_AVAILABLE,
    DefaultCredentialsError,
    HttpError,
    asset_v1,
    compute_v1,
    container_v1,
    discovery,
    functions_v1,
    monitoring_v3,
    service_account,
    sql_v1,
    storage,
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

    def get_gcp_credentials(self, credentials: GCPCredentials) -> Optional[Any]:
        """Create GCP credentials from service account key"""
        if not GCP_AVAILABLE:
            raise ImportError("Google Cloud SDK not installed")
        return service_account.Credentials.from_service_account_info(
            credentials.service_account_key
        )

    def init_clients(self, credentials: Any, project_id: str):
        """Initialize GCP service clients"""
        if not GCP_AVAILABLE:
            self.logger.warning("GCP SDK not available - clients not initialized")
            return

        self._credentials = credentials
        self._project_id = project_id

        if asset_v1:
            self._asset_client = asset_v1.AssetServiceClient(credentials=credentials)
        if monitoring_v3:
            self._monitoring_client = monitoring_v3.MetricServiceClient(
                credentials=credentials
            )
        if compute_v1:
            self._compute_client = compute_v1.InstancesClient(credentials=credentials)
        if sql_v1:
            self._sql_client = sql_v1.SqlInstancesServiceClient(credentials=credentials)
        if storage:
            self._storage_client = storage.Client(
                credentials=credentials, project=project_id
            )
        if container_v1:
            self._container_client = container_v1.ClusterManagerClient(
                credentials=credentials
            )
        if functions_v1:
            self._functions_client = functions_v1.CloudFunctionsServiceClient(
                credentials=credentials
            )

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate GCP credentials by attempting to list projects

        Args:
            credentials: GCP credentials dictionary

        Returns:
            True if credentials are valid, False otherwise
        """
        if not GCP_AVAILABLE:
            self.logger.error(
                "Google Cloud SDK not installed. Cannot validate GCP credentials."
            )
            return False

        try:
            # Parse credentials
            gcp_creds = GCPCredentials(
                project_id=credentials.get("project_id", ""),
                service_account_key=credentials.get("service_account_key", {}),
            )

            # Create credentials and test with Resource Manager
            creds = self.get_gcp_credentials(gcp_creds)

            # Build Resource Manager service
            service = discovery.build("cloudresourcemanager", "v1", credentials=creds)

            # Test credentials by getting project info
            project = service.projects().get(projectId=gcp_creds.project_id).execute()

            self.logger.info(
                f"GCP credentials validated for project: {project.get('name', gcp_creds.project_id)}"
            )
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
    def asset_client(self) -> Optional[Any]:
        """Get the Asset Service client"""
        return self._asset_client

    @property
    def monitoring_client(self) -> Optional[Any]:
        """Get the Monitoring client"""
        return self._monitoring_client

    @property
    def compute_client(self) -> Optional[Any]:
        """Get the Compute Engine client"""
        return self._compute_client

    @property
    def sql_client(self) -> Optional[Any]:
        """Get the Cloud SQL client"""
        return self._sql_client

    @property
    def storage_client(self) -> Optional[Any]:
        """Get the Cloud Storage client"""
        return self._storage_client

    @property
    def container_client(self) -> Optional[Any]:
        """Get the Container (GKE) client"""
        return self._container_client

    @property
    def functions_client(self) -> Optional[Any]:
        """Get the Cloud Functions client"""
        return self._functions_client
