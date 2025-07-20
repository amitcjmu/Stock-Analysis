# ADCS Troubleshooting Guide and FAQ

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [Platform-Specific Troubleshooting](#platform-specific-troubleshooting)
4. [Performance Issues](#performance-issues)
5. [Data Quality Problems](#data-quality-problems)
6. [Integration Issues](#integration-issues)
7. [Frequently Asked Questions](#frequently-asked-questions)
8. [Advanced Troubleshooting](#advanced-troubleshooting)
9. [Support and Escalation](#support-and-escalation)

## Quick Diagnostic Checklist

When encountering issues with the Adaptive Data Collection System, follow this quick diagnostic checklist:

### ✅ Initial System Check
- [ ] Verify user authentication and permissions
- [ ] Check system status dashboard for known issues
- [ ] Confirm internet connectivity and firewall settings
- [ ] Validate platform credentials and access permissions
- [ ] Review recent system logs for error patterns

### ✅ Collection Flow Status
- [ ] Check Collection Flow status in the dashboard
- [ ] Verify automation tier assignment matches environment
- [ ] Confirm platform adapter connectivity
- [ ] Review current phase and progress indicators
- [ ] Check for any paused or failed operations

### ✅ Data Validation
- [ ] Review data quality scores and completeness metrics
- [ ] Check for identified gaps and validation errors
- [ ] Verify data transformation and normalization status
- [ ] Confirm stakeholder approvals and sign-offs

## Common Issues and Solutions

### 1. Collection Flow Fails to Start

#### Symptoms
- Flow remains in "pending" status after initialization
- Error messages about configuration validation
- Platform adapter connection failures

#### Causes and Solutions

**Invalid Credentials**
```
Error: "Authentication failed for platform adapter"
```
**Solution:**
1. Verify credentials in platform configuration
2. Check credential expiration dates
3. Validate IAM permissions for service accounts
4. Test connectivity using adapter test endpoint

**Insufficient Permissions**
```
Error: "Access denied for required operations"
```
**Solution:**
1. Review required permissions for your automation tier
2. Contact platform administrator for permission grants
3. Consider downgrading to lower automation tier
4. Use manual collection workflow as alternative

**Network Connectivity Issues**
```
Error: "Connection timeout to platform services"
```
**Solution:**
1. Check firewall rules and proxy configurations
2. Verify DNS resolution for platform endpoints
3. Test connectivity from deployment environment
4. Configure appropriate network routes

### 2. Slow or Stalled Collection

#### Symptoms
- Collection progress stops or moves very slowly
- Timeout errors during resource discovery
- High resource utilization on collection services

#### Diagnostic Steps

1. **Check Resource Scope**
   ```
   Review Collection Scope:
   ✓ Number of resources in scope
   ✓ Geographic distribution of resources
   ✓ Complexity of dependency relationships
   ✓ Network latency to target platforms
   ```

2. **Monitor Performance Metrics**
   ```
   Key Metrics to Review:
   ✓ Operations per minute
   ✓ Success rate percentage
   ✓ Average response time
   ✓ Concurrent operation count
   ```

**Solutions:**

**Reduce Parallelism**
```json
{
  "execution_options": {
    "max_concurrent_operations": 5,
    "timeout_settings": {
      "per_operation": 600,
      "total_execution": 14400
    }
  }
}
```

**Optimize Collection Scope**
```json
{
  "scope": {
    "regions": ["us-east-1"],
    "resource_tags": ["Environment:Production"],
    "scan_depth": "standard"
  }
}
```

**Schedule During Off-Peak Hours**
- Avoid peak usage times for target platforms
- Coordinate with infrastructure teams
- Consider weekend or evening collection windows

### 3. Authentication and Authorization Failures

#### AWS Authentication Issues

**Expired or Invalid Credentials**
```
Error: "The AWS Access Key Id you provided does not exist in our records"
```
**Solution:**
1. Generate new access keys in AWS IAM
2. Update credentials in Collection Flow configuration
3. Verify credential format and special characters

**Insufficient IAM Permissions**
```
Error: "User is not authorized to perform: ec2:DescribeInstances"
```
**Required AWS Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "rds:Describe*",
        "lambda:List*",
        "s3:List*",
        "iam:Get*",
        "iam:List*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Azure Authentication Issues

**Service Principal Authentication**
```
Error: "AADSTS70011: The provided value for the input parameter 'scope' is not valid"
```
**Solution:**
1. Verify Azure tenant ID and subscription ID
2. Check service principal permissions
3. Confirm API permissions are granted and consented

**Required Azure Permissions:**
```
Subscription Reader
Virtual Machine Contributor (read-only)
Network Contributor (read-only)
SQL DB Contributor (read-only)
```

#### GCP Authentication Issues

**Service Account Key Issues**
```
Error: "invalid_grant: Invalid JWT Signature"
```
**Solution:**
1. Download new service account key file
2. Verify JSON key file format and encoding
3. Check service account permissions

**Required GCP Permissions:**
```
roles/compute.viewer
roles/cloudsql.viewer
roles/storage.objectViewer
roles/iam.serviceAccountUser
```

### 4. Data Quality and Completeness Issues

#### Low Quality Scores

**Symptoms:**
- Overall quality score below 0.8
- High number of identified data gaps
- Low confidence levels in collected data

**Root Cause Analysis:**

1. **Check Data Sources**
   ```
   Automated Sources:
   ✓ Platform API availability
   ✓ Resource tagging completeness
   ✓ Configuration management data
   
   Manual Sources:
   ✓ Stakeholder response rates
   ✓ Documentation completeness
   ✓ Subject matter expert availability
   ```

2. **Review Collection Methods**
   ```
   Collection Issues:
   ✓ Network discovery limitations
   ✓ Legacy system compatibility
   ✓ Security restrictions
   ✓ Resource accessibility
   ```

**Improvement Strategies:**

**Enhance Automated Discovery**
```json
{
  "collection_options": {
    "include_dependencies": true,
    "include_configuration": true,
    "include_performance_data": true,
    "cross_platform_correlation": true
  }
}
```

**Supplement with Manual Collection**
- Use guided questionnaires for missing data
- Conduct stakeholder interviews
- Review existing documentation
- Perform technical deep-dives

**Implement Data Validation Rules**
- Cross-reference multiple data sources
- Validate against business rules
- Implement consistency checks
- Use historical data for validation

#### Missing Critical Dependencies

**Symptoms:**
- Low dependency mapping scores
- Incomplete application relationships
- Missing integration points

**Solutions:**

1. **Network Traffic Analysis**
   - Enable network monitoring tools
   - Analyze application communication patterns
   - Review firewall logs and rules

2. **Configuration Analysis**
   - Review application configuration files
   - Analyze connection strings and endpoints
   - Check service discovery configurations

3. **Manual Documentation Review**
   - Interview application architects
   - Review system documentation
   - Conduct dependency mapping workshops

### 5. Platform Adapter Issues

#### AWS Adapter Problems

**EC2 Instance Discovery Issues**
```
Common Issues:
✓ Stopped instances not discovered
✓ Missing instance metadata
✓ Incomplete security group information
✓ Missing EBS volume details
```

**Solution:**
```json
{
  "aws_adapter_config": {
    "include_stopped_instances": true,
    "gather_extended_metadata": true,
    "include_security_groups": true,
    "include_storage_details": true
  }
}
```

**RDS Discovery Problems**
```
Common Issues:
✓ Read replica relationships unclear
✓ Missing parameter group information
✓ Incomplete subnet group details
✓ Missing backup configuration
```

#### Azure Adapter Problems

**Virtual Machine Discovery Issues**
```
Common Issues:
✓ Deallocated VMs not included
✓ Missing network interface details
✓ Incomplete disk information
✓ Missing availability set membership
```

**Solution:**
```json
{
  "azure_adapter_config": {
    "include_deallocated_vms": true,
    "gather_network_details": true,
    "include_disk_details": true,
    "include_availability_groups": true
  }
}
```

#### GCP Adapter Problems

**Compute Engine Discovery Issues**
```
Common Issues:
✓ Preemptible instances not tracked
✓ Missing custom metadata
✓ Incomplete network tag information
✓ Missing managed instance groups
```

### 6. Performance Optimization

#### Collection Duration Optimization

**Baseline Performance Expectations:**
```
Tier 1 (Modern Cloud): 2-4 hours per 100 applications
Tier 2 (Mixed Environment): 4-8 hours per 100 applications  
Tier 3 (Restricted Access): 1-2 days per 100 applications
Tier 4 (Air-Gapped): 3-5 days per 100 applications
```

**Optimization Strategies:**

1. **Parallel Processing Tuning**
   ```json
   {
     "performance_config": {
       "max_concurrent_adapters": 5,
       "operations_per_adapter": 10,
       "adaptive_throttling": true,
       "resource_utilization_limit": 0.8
     }
   }
   ```

2. **Scope Optimization**
   ```json
   {
     "scope_optimization": {
       "prioritize_critical_systems": true,
       "exclude_development_environments": true,
       "focus_on_production_data": true,
       "limit_historical_data": "30_days"
     }
   }
   ```

3. **Caching and Reuse**
   ```json
   {
     "caching_config": {
       "enable_result_caching": true,
       "cache_duration": "24_hours",
       "reuse_similar_discoveries": true,
       "intelligent_refresh": true
     }
   }
   ```

#### Memory and Resource Issues

**High Memory Usage**
```
Symptoms:
✓ Collection services consuming excessive memory
✓ Out of memory errors in logs
✓ System performance degradation

Solutions:
✓ Increase memory allocation for collection services
✓ Implement data streaming for large datasets
✓ Enable garbage collection optimization
✓ Process data in smaller batches
```

**Database Performance Issues**
```
Symptoms:
✓ Slow query response times
✓ Database connection timeouts
✓ Lock contention in collection tables

Solutions:
✓ Optimize database indexes
✓ Implement connection pooling
✓ Use read replicas for reporting queries
✓ Archive historical collection data
```

## Frequently Asked Questions

### General Usage Questions

**Q: How do I determine which workflow type to use?**

A: The system automatically recommends workflow types based on environment assessment:
- **Smart Workflow**: For modern cloud environments with API access
- **Traditional Workflow**: For air-gapped or legacy environments
- **Hybrid Workflow**: For mixed environments requiring both automated and manual collection

**Q: Can I switch between workflow types during collection?**

A: Yes, you can transition from Smart to Traditional workflow if automation fails, or supplement Smart workflow results with manual validation. The system maintains data lineage across workflow types.

**Q: How long does a typical collection take?**

A: Collection duration depends on automation tier and scope:
- Tier 1 (90% automation): 2-4 hours per 100 applications
- Tier 2 (70% automation): 4-8 hours per 100 applications
- Tier 3 (40% automation): 1-2 days per 100 applications
- Tier 4 (10% automation): 3-5 days per 100 applications

### Technical Implementation Questions

**Q: What happens if my platform credentials expire during collection?**

A: The system detects credential expiration and:
1. Pauses the collection flow automatically
2. Sends notification to administrators
3. Preserves collected data and current state
4. Allows credential refresh and collection resumption

**Q: How does the system handle rate limiting from cloud platforms?**

A: The system implements adaptive rate limiting:
- Monitors platform response times and rate limit headers
- Automatically adjusts request frequency
- Implements exponential backoff for rate limit violations
- Prioritizes critical operations during throttled periods

**Q: Can I run multiple collection flows simultaneously?**

A: Yes, with considerations:
- Each flow runs independently with separate resource allocation
- Platform rate limits are shared across all flows
- System monitors total resource utilization
- Automatic load balancing prevents resource contention

### Data Quality and Completeness Questions

**Q: What is considered an acceptable data quality score?**

A: Quality score thresholds:
- **Excellent (0.9-1.0)**: Ready for immediate 6R analysis
- **Good (0.8-0.89)**: Acceptable with minor gap resolution
- **Fair (0.7-0.79)**: Requires gap resolution before analysis
- **Poor (<0.7)**: Significant data collection improvements needed

**Q: How do I resolve identified data gaps?**

A: Gap resolution strategies:
1. **Automated Resolution**: System attempts additional discovery methods
2. **Guided Manual Collection**: Targeted questionnaires for specific gaps
3. **Stakeholder Interviews**: Expert consultation for complex gaps
4. **Document Review**: Analysis of existing documentation
5. **Gap Acceptance**: Document and accept gaps with business justification

**Q: Can I override or correct automatically collected data?**

A: Yes, through multiple mechanisms:
- Manual override of specific data points with approval workflow
- Bulk correction through data upload templates
- Stakeholder validation and correction processes
- Expert review and modification procedures

### Security and Compliance Questions

**Q: How are platform credentials stored and protected?**

A: Security measures include:
- AES-256 encryption for credentials at rest
- TLS 1.3 for credentials in transit
- Role-based access control for credential management
- Automatic credential rotation support
- Audit logging for all credential access

**Q: What compliance certifications does the system support?**

A: The system supports:
- SOC 2 Type II compliance
- ISO 27001 security standards
- GDPR data protection requirements
- HIPAA healthcare data protection (when configured)
- PCI DSS for payment card environments

**Q: Can the system operate in air-gapped environments?**

A: Yes, through multiple deployment options:
- Standalone on-premises deployment
- Disconnected data collection with offline export
- Manual data transfer between environments
- Template-based data collection workflows

### Integration and Workflow Questions

**Q: How does Collection Flow integrate with existing Discovery Flows?**

A: Integration is seamless:
- Collection Flow data automatically transfers to Discovery Flow
- Shared data schemas ensure compatibility
- Quality metadata preserves data lineage
- Gap information informs Discovery Flow planning

**Q: Can I export collected data to external systems?**

A: Yes, through multiple formats:
- JSON for programmatic integration
- CSV/Excel for spreadsheet analysis
- API endpoints for real-time integration
- Webhook notifications for event-driven integration

**Q: How do I monitor collection progress across multiple flows?**

A: Monitoring capabilities include:
- Real-time dashboard with progress indicators
- Automated notifications for status changes
- Executive summary reports
- Detailed technical progress reports

## Advanced Troubleshooting

### Debug Mode and Logging

#### Enabling Debug Mode

1. **API Request Debug Mode**
   ```json
   {
     "debug_options": {
       "enable_verbose_logging": true,
       "log_api_requests": true,
       "include_performance_metrics": true,
       "capture_error_details": true
     }
   }
   ```

2. **Platform Adapter Debug Mode**
   ```json
   {
     "adapter_debug": {
       "log_platform_requests": true,
       "capture_response_headers": true,
       "include_retry_attempts": true,
       "log_rate_limit_info": true
     }
   }
   ```

#### Log Analysis

**Common Error Patterns:**
```
Authentication Errors:
[ERROR] 2025-07-19 10:30:15 - AWS adapter authentication failed: InvalidUserID.NotFound

Permission Errors:
[ERROR] 2025-07-19 10:31:22 - Azure adapter permission denied: Insufficient privileges for subscription

Network Errors:
[ERROR] 2025-07-19 10:32:45 - GCP adapter timeout: Connection timeout after 30 seconds

Data Processing Errors:
[ERROR] 2025-07-19 10:33:12 - Data transformation failed: Invalid JSON structure in source data
```

### Performance Profiling

#### Collection Performance Analysis

1. **Resource Discovery Profiling**
   ```bash
   # Monitor resource discovery performance
   curl -H "Authorization: Bearer $TOKEN" \
        "https://api.migration-orchestrator.com/api/v1/collection/flows/$FLOW_ID/performance"
   ```

2. **Database Query Performance**
   ```sql
   -- Analyze slow queries during collection
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   WHERE query LIKE '%collection_flow%'
   ORDER BY total_time DESC;
   ```

3. **Memory Usage Analysis**
   ```bash
   # Monitor memory usage during collection
   docker stats migration-orchestrator-backend
   ```

### Custom Diagnostic Scripts

#### Environment Validation Script

```python
#!/usr/bin/env python3
"""
ADCS Environment Validation Script
Validates environment setup and connectivity for Collection Flows
"""

import requests
import json
import boto3
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient

def validate_aws_connectivity(credentials):
    """Validate AWS connectivity and permissions"""
    try:
        session = boto3.Session(
            aws_access_key_id=credentials['access_key'],
            aws_secret_access_key=credentials['secret_key'],
            region_name=credentials['region']
        )
        
        ec2 = session.client('ec2')
        response = ec2.describe_instances(MaxResults=5)
        
        return {
            "status": "success",
            "instances_found": len(response['Reservations']),
            "permissions": "valid"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "solution": "Check AWS credentials and permissions"
        }

def validate_azure_connectivity(credentials):
    """Validate Azure connectivity and permissions"""
    try:
        credential = ClientSecretCredential(
            tenant_id=credentials['tenant_id'],
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret']
        )
        
        client = ResourceManagementClient(
            credential, 
            credentials['subscription_id']
        )
        
        resources = list(client.resources.list())
        
        return {
            "status": "success",
            "resources_found": len(resources),
            "permissions": "valid"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "solution": "Check Azure service principal permissions"
        }

def run_validation():
    """Run complete environment validation"""
    config = {
        "aws": {
            "access_key": "YOUR_AWS_ACCESS_KEY",
            "secret_key": "YOUR_AWS_SECRET_KEY",
            "region": "us-east-1"
        },
        "azure": {
            "tenant_id": "YOUR_TENANT_ID",
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "subscription_id": "YOUR_SUBSCRIPTION_ID"
        }
    }
    
    results = {
        "aws": validate_aws_connectivity(config['aws']),
        "azure": validate_azure_connectivity(config['azure'])
    }
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_validation()
```

## Support and Escalation

### Self-Service Resources

1. **System Status Page**: Check real-time system status and known issues
2. **Documentation Portal**: Access complete technical documentation
3. **Community Forums**: Connect with other users and share solutions
4. **Knowledge Base**: Search solutions for common problems

### Support Channels

#### Tier 1 - Basic Support
- **Email**: support@migration-orchestrator.com
- **Response Time**: 24 hours during business days
- **Coverage**: Basic usage questions, configuration assistance

#### Tier 2 - Technical Support
- **Email**: technical-support@migration-orchestrator.com
- **Response Time**: 8 hours during business days
- **Coverage**: Technical issues, integration problems, performance optimization

#### Tier 3 - Expert Support
- **Phone**: +1-800-MIGRATE (24/7 for critical issues)
- **Email**: expert-support@migration-orchestrator.com
- **Response Time**: 2 hours for critical issues, 4 hours for high priority
- **Coverage**: Complex technical issues, custom integrations, architecture guidance

### Escalation Criteria

#### Critical Issues (Immediate Escalation)
- System-wide outages affecting multiple users
- Data loss or corruption incidents
- Security breaches or suspected attacks
- Critical business process failures

#### High Priority Issues (4-hour SLA)
- Collection Flow failures affecting business timelines
- Platform adapter connectivity issues
- Performance degradation affecting multiple users
- Integration failures with external systems

#### Medium Priority Issues (24-hour SLA)
- Data quality issues requiring expert analysis
- Configuration optimization requests
- Feature enhancement requests
- Training and documentation requests

### Information to Provide When Contacting Support

1. **Environment Information**
   - Deployment type (cloud/on-premises)
   - System version and build information
   - Platform configurations (AWS/Azure/GCP)

2. **Issue Details**
   - Collection Flow ID and timestamps
   - Error messages and log entries
   - Steps to reproduce the issue
   - Impact on business operations

3. **Diagnostic Information**
   - System performance metrics
   - Network connectivity test results
   - Platform adapter test results
   - Recent configuration changes

This comprehensive troubleshooting guide provides systematic approaches to resolving common issues while ensuring users can maintain high-quality data collection workflows across diverse environments.