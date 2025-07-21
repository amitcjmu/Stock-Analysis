"""
AWS Compute Services Collection (EC2, Lambda)
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ComputeServicesCollector:
    """Collector for AWS compute services (EC2, Lambda)"""
    
    def __init__(self, ec2_client, lambda_client):
        self._ec2_client = ec2_client
        self._lambda_client = lambda_client
        
    async def collect_ec2_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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
            
    async def collect_lambda_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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
            
    def _get_lambda_tags(self, function_arn: str) -> Dict[str, str]:
        """Get tags for Lambda function"""
        try:
            response = self._lambda_client.list_tags(Resource=function_arn)
            return response.get('Tags', {})
        except Exception:
            return {}
            
    async def test_ec2_connectivity(self) -> bool:
        """Test EC2 service connectivity"""
        try:
            response = self._ec2_client.describe_regions(MaxResults=1)
            return len(response.get('Regions', [])) > 0
        except Exception:
            return False
            
    async def test_lambda_connectivity(self) -> bool:
        """Test Lambda service connectivity"""
        try:
            response = self._lambda_client.list_functions(MaxItems=1)
            return True
        except Exception:
            return False
            
    async def check_ec2_has_resources(self) -> bool:
        """Quick check if EC2 has any resources"""
        try:
            response = self._ec2_client.describe_instances(MaxResults=1)
            return len(response.get('Reservations', [])) > 0
        except Exception:
            return False
            
    async def check_lambda_has_resources(self) -> bool:
        """Quick check if Lambda has any resources"""
        try:
            response = self._lambda_client.list_functions(MaxItems=1)
            return len(response.get('Functions', [])) > 0
        except Exception:
            return False