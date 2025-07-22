"""
AWS Container Services Collection (ECS, EKS)
"""

import logging
from typing import Any, Dict

try:
    import boto3
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)


class ContainerServicesCollector:
    """Collector for AWS container services (ECS, EKS)"""
    
    def __init__(self, region: str):
        self._region = region
        
    async def collect_ecs_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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
            
    async def collect_eks_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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