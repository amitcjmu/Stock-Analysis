"""
AWS Config Configuration Data Collection
"""

from typing import Dict, Any, List
import logging

try:
    from botocore.exceptions import ClientError
except ImportError:
    ClientError = Exception

logger = logging.getLogger(__name__)


class ConfigurationCollector:
    """Collector for AWS Config configuration data"""
    
    def __init__(self, config_client):
        self._config_client = config_client
        
    async def collect_configuration_data(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
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
                    logger.warning(f"Failed to get Config data for {service} resource {resource_id}: {str(e)}")
                    
        return config_items
        
    async def test_config_connectivity(self) -> bool:
        """Test AWS Config service connectivity"""
        try:
            response = self._config_client.describe_configuration_recorders()
            return True
        except Exception:
            return False