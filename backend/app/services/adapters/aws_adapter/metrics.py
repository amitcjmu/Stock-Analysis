"""
AWS CloudWatch Metrics Collection
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from .base import AWSResourceMetrics

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collector for AWS CloudWatch metrics"""
    
    def __init__(self, cloudwatch_client):
        self._cloudwatch_client = cloudwatch_client
        
    async def collect_performance_metrics(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect CloudWatch performance metrics for discovered resources"""
        try:
            metrics_data = {}
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)  # Last 24 hours
            
            # Collect metrics for EC2 instances
            if "EC2" in collected_data:
                ec2_metrics = await self.collect_ec2_metrics(
                    collected_data["EC2"]["resources"], start_time, end_time
                )
                metrics_data["EC2"] = ec2_metrics
                
            # Collect metrics for RDS instances
            if "RDS" in collected_data:
                rds_metrics = await self.collect_rds_metrics(
                    collected_data["RDS"]["resources"], start_time, end_time
                )
                metrics_data["RDS"] = rds_metrics
                
            # Collect metrics for Lambda functions
            if "Lambda" in collected_data:
                lambda_metrics = await self.collect_lambda_metrics(
                    collected_data["Lambda"]["resources"], start_time, end_time
                )
                metrics_data["Lambda"] = lambda_metrics
                
            return metrics_data
            
        except Exception as e:
            raise Exception(f"Performance metrics collection failed: {str(e)}")
            
    async def collect_ec2_metrics(self, instances: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
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
                logger.warning(f"Failed to collect metrics for EC2 instance {instance_id}: {str(e)}")
                
        return metrics
        
    async def collect_rds_metrics(self, databases: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
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
                logger.warning(f"Failed to collect metrics for RDS instance {db_id}: {str(e)}")
                
        return metrics
        
    async def collect_lambda_metrics(self, functions: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
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
                logger.warning(f"Failed to collect metrics for Lambda function {func_name}: {str(e)}")
                
        return metrics
        
    async def test_cloudwatch_connectivity(self) -> bool:
        """Test CloudWatch service connectivity"""
        try:
            response = self._cloudwatch_client.list_metrics(MaxRecords=1)
            return True
        except Exception:
            return False