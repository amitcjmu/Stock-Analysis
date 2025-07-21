# AWS Adapter Modularization

This document describes the modularization of the AWS adapter from a single 1,576 line file into a well-organized module structure.

## Module Structure

The AWS adapter has been split into the following modules:

```
aws_adapter/
├── __init__.py          # Package initialization and exports
├── base.py              # Base classes (AWSCredentials, AWSResourceMetrics) and metadata
├── main.py              # Main AWSAdapter class implementation
├── compute_services.py  # EC2 and Lambda collection
├── database_services.py # RDS, DynamoDB, Redshift, ElastiCache collection
├── networking_services.py # ELB and ELBv2 collection
├── container_services.py # ECS and EKS collection
├── storage_services.py  # S3 collection
├── metrics.py           # CloudWatch metrics collection
├── configuration.py     # AWS Config data collection
└── transformation.py    # Data transformation to normalized format
```

## Module Responsibilities

### base.py (76 lines)
- `AWSCredentials` dataclass for credential management
- `AWSResourceMetrics` dataclass for performance metrics
- `AWS_ADAPTER_METADATA` constant with adapter registration metadata

### main.py (265 lines)
- Main `AWSAdapter` class that coordinates all collectors
- Credential validation and connectivity testing
- Service discovery and resource availability checking
- Main data collection orchestration

### compute_services.py (116 lines)
- `ComputeServicesCollector` class
- EC2 instance discovery and data collection
- Lambda function discovery and data collection
- Connectivity testing for compute services

### database_services.py (335 lines)
- `DatabaseServicesCollector` class
- RDS database instance collection
- DynamoDB table collection
- Redshift cluster collection
- ElastiCache cluster collection
- Database-specific tag collection methods

### networking_services.py (96 lines)
- `NetworkingServicesCollector` class
- Classic Load Balancer (ELB) collection
- Application/Network Load Balancer (ELBv2) collection
- Load balancer tag collection

### container_services.py (94 lines)
- `ContainerServicesCollector` class
- ECS cluster and service collection
- EKS cluster collection

### storage_services.py (108 lines)
- `StorageServicesCollector` class
- S3 bucket discovery and property collection
- Bucket versioning, encryption, and access configuration

### metrics.py (216 lines)
- `MetricsCollector` class
- CloudWatch metrics collection for EC2, RDS, and Lambda
- Performance data aggregation and averaging
- Support for CPU, network, database connections, and Lambda invocations

### configuration.py (103 lines)
- `ConfigurationCollector` class
- AWS Config integration for configuration history
- Resource configuration state tracking

### transformation.py (198 lines)
- `DataTransformer` class
- Transform AWS-specific data to normalized ADCS format
- Asset type mapping and resource naming
- Metrics normalization

## Backward Compatibility

The original `aws_adapter.py` file has been preserved as a compatibility layer that re-exports all public interfaces:

```python
from .aws_adapter.base import AWSCredentials, AWSResourceMetrics, AWS_ADAPTER_METADATA
from .aws_adapter.main import AWSAdapter

__all__ = [
    "AWSAdapter",
    "AWSCredentials",
    "AWSResourceMetrics",
    "AWS_ADAPTER_METADATA"
]
```

This ensures that existing code importing from `app.services.adapters.aws_adapter` continues to work without modification.

## Benefits of Modularization

1. **Improved Maintainability**: Each module has a focused responsibility, making it easier to understand and modify
2. **Better Testing**: Individual collectors can be tested in isolation
3. **Reduced Complexity**: The main adapter file went from 1,576 lines to 265 lines
4. **Easier Extension**: New AWS services can be added by creating new collector modules
5. **Code Reusability**: Collectors can be reused in other contexts if needed
6. **Clear Dependencies**: Each module clearly imports only what it needs

## Migration Notes

- No changes are required for existing code that imports the AWS adapter
- The modular structure is transparent to consumers of the adapter
- All functionality remains identical to the original implementation
- The only external dependency remains the optional boto3 package