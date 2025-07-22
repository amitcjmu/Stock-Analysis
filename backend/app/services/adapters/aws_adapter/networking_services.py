"""
AWS Networking Services Collection (ELB, ELBv2)
"""

import logging
from typing import Any, Dict, List

try:
    import boto3
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)


class NetworkingServicesCollector:
    """Collector for AWS networking services (Load Balancers)"""
    
    def __init__(self, ec2_client, region: str):
        self._ec2_client = ec2_client
        self._region = region
        
    async def collect_elb_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect Classic Load Balancer data"""
        try:
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
            
    async def collect_elbv2_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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