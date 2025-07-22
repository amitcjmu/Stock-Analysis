"""
AWS Storage Services Collection (S3)
"""

import logging
from typing import Any, Dict, List

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

logger = logging.getLogger(__name__)


class StorageServicesCollector:
    """Collector for AWS storage services (S3)"""
    
    def __init__(self, region: str):
        self._region = region
        
    async def collect_s3_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
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