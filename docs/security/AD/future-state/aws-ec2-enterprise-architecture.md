# AWS EC2 Network Architecture - AI Force Migration Platform

**Enterprise Solution Architecture for Secure AWS Deployment**  
**Document Date:** January 15, 2025  
**Deployment Type:** AWS EC2 Multi-Tier Architecture with Docker Containers  
**Classification:** Internal Use - Security Review  

## Executive Summary

This document provides the comprehensive solution architecture for deploying the AI Force Migration Platform on AWS EC2 instances within a secure, locked-down environment. The platform is designed as a self-contained, enterprise-grade solution that operates entirely within the AWS infrastructure boundary with no external dependencies on third-party cloud services.

## Overview

The AI Force Migration Platform is deployed as a containerized application stack across multiple AWS EC2 instances with managed PostgreSQL database, providing a secure, scalable, and highly available cloud migration orchestration system. All components are contained within the customer's AWS environment with strict network isolation and comprehensive security controls.

## Enterprise Solution Architecture

### High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                AWS CLOUD REGION                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                            INTERNET GATEWAY                                 │  │
│  │                         (TLS 1.3 Encrypted)                                │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                            AWS WAF + SHIELD                                 │  │
│  │              (DDoS Protection, SQL Injection, XSS Prevention)              │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                      APPLICATION LOAD BALANCER                             │  │
│  │                    (SSL Termination, Multi-AZ)                             │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                           VPC (10.0.0.0/16)                                │  │
│  │                                                                             │  │
│  │  ┌────────────────────┐    ┌────────────────────┐    ┌────────────────────┐│  │
│  │  │   PUBLIC SUBNET    │    │   PRIVATE SUBNET   │    │   PRIVATE SUBNET   ││  │
│  │  │   (10.0.1.0/24)    │    │   (10.0.2.0/24)    │    │   (10.0.3.0/24)    ││  │
│  │  │                    │    │                    │    │                    ││  │
│  │  │  ┌──────────────┐  │    │  ┌──────────────┐  │    │  ┌──────────────┐  ││  │
│  │  │  │   NAT GW     │  │    │  │   WEB TIER   │  │    │  │   API TIER   │  ││  │
│  │  │  │   (HA)       │  │    │  │   (Frontend) │  │    │  │   (Backend)  │  ││  │
│  │  │  │              │  │    │  │              │  │    │  │              │  ││  │
│  │  │  │  • Auto      │  │    │  │  • Auto      │  │    │  │  • Auto      │  ││  │
│  │  │  │    Scaling   │  │    │  │    Scaling   │  │    │  │    Scaling   │  ││  │
│  │  │  │  • Multi-AZ  │  │    │  │  • Multi-AZ  │  │    │  │  • Multi-AZ  │  ││  │
│  │  │  │  • Redundant │  │    │  │  • ELB       │  │    │  │  • ELB       │  ││  │
│  │  │  └──────────────┘  │    │  └──────────────┘  │    │  └──────────────┘  ││  │
│  │  └────────────────────┘    └────────────────────┘    └────────────────────┘│  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐│  │
│  │  │                    DATABASE SUBNET (10.0.4.0/24)                       ││  │
│  │  │                                                                          ││  │
│  │  │  ┌──────────────┐                              ┌──────────────┐          ││  │
│  │  │  │ RDS PRIMARY  │                              │ RDS REPLICA  │          ││  │
│  │  │  │ PostgreSQL   │◄────────────────────────────►│ PostgreSQL   │          ││  │
│  │  │  │ (Multi-AZ)   │                              │ (Multi-AZ)   │          ││  │
│  │  │  │              │                              │              │          ││  │
│  │  │  │  • Encrypted │                              │  • Encrypted │          ││  │
│  │  │  │  • Backup    │                              │  • Backup    │          ││  │
│  │  │  │  • Audit     │                              │  • Audit     │          ││  │
│  │  │  └──────────────┘                              └──────────────┘          ││  │
│  │  └─────────────────────────────────────────────────────────────────────────┘│  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Application Stack Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            WEB TIER (Private Subnet)                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   EC2 Instance  │    │   EC2 Instance  │    │   EC2 Instance  │                │
│  │   (Frontend 1)  │    │   (Frontend 2)  │    │   (Frontend 3)  │                │
│  │                 │    │                 │    │                 │                │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │                │
│  │ │   Docker    │ │    │ │   Docker    │ │    │ │   Docker    │ │                │
│  │ │   Engine    │ │    │ │   Engine    │ │    │ │   Engine    │ │                │
│  │ │             │ │    │ │             │ │    │ │             │ │                │
│  │ │ ┌─────────┐ │ │    │ │ ┌─────────┐ │ │    │ │ ┌─────────┐ │ │                │
│  │ │ │Next.js  │ │ │    │ │ │Next.js  │ │ │    │ │ │Next.js  │ │ │                │
│  │ │ │Frontend │ │ │    │ │ │Frontend │ │ │    │ │ │Frontend │ │ │                │
│  │ │ │Container│ │ │    │ │ │Container│ │ │    │ │ │Container│ │ │                │
│  │ │ │         │ │ │    │ │ │         │ │ │    │ │ │         │ │ │                │
│  │ │ │Port 3000│ │ │    │ │ │Port 3000│ │ │    │ │ │Port 3000│ │ │                │
│  │ │ └─────────┘ │ │    │ │ └─────────┘ │ │    │ │ └─────────┘ │ │                │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           └───────────────────────┼───────────────────────┘                        │
│                                   │                                                │
└───────────────────────────────────┼────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────────────────┐
│                            API TIER (Private Subnet)                               │
├───────────────────────────────────┼────────────────────────────────────────────────┤
│                                   │                                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   EC2 Instance  │    │   EC2 Instance  │    │   EC2 Instance  │                │
│  │   (Backend 1)   │    │   (Backend 2)   │    │   (Backend 3)   │                │
│  │                 │    │                 │    │                 │                │
│  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │                │
│  │ │   Docker    │ │    │ │   Docker    │ │    │ │   Docker    │ │                │
│  │ │   Engine    │ │    │ │   Engine    │ │    │ │   Engine    │ │                │
│  │ │             │ │    │ │             │ │    │ │             │ │                │
│  │ │ ┌─────────┐ │ │    │ │ ┌─────────┐ │ │    │ │ ┌─────────┐ │ │                │
│  │ │ │FastAPI  │ │ │    │ │ │FastAPI  │ │ │    │ │ │FastAPI  │ │ │                │
│  │ │ │Backend  │ │ │    │ │ │Backend  │ │ │    │ │ │Backend  │ │ │                │
│  │ │ │Container│ │ │    │ │ │Container│ │ │    │ │ │Container│ │ │                │
│  │ │ │         │ │ │    │ │ │         │ │ │    │ │ │         │ │ │                │
│  │ │ │Port 8000│ │ │    │ │ │Port 8000│ │ │    │ │ │Port 8000│ │ │                │
│  │ │ └─────────┘ │ │    │ │ └─────────┘ │ │    │ │ └─────────┘ │ │                │
│  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           └───────────────────────┼───────────────────────┘                        │
│                                   │                                                │
└───────────────────────────────────┼────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────────────────┐
│                        DATABASE TIER (Private Subnet)                             │
├───────────────────────────────────┼────────────────────────────────────────────────┤
│                                   │                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         RDS POSTGRESQL CLUSTER                             │  │
│  │                                                                             │  │
│  │  ┌──────────────┐                              ┌──────────────┐             │  │
│  │  │    PRIMARY   │                              │  READ REPLICA│             │  │
│  │  │   DATABASE   │◄────────────────────────────►│   DATABASE   │             │  │
│  │  │              │                              │              │             │  │
│  │  │ • Multi-AZ   │                              │ • Multi-AZ   │             │  │
│  │  │ • Encrypted  │                              │ • Encrypted  │             │  │
│  │  │ • Auto Backup│                              │ • Auto Backup│             │  │
│  │  │ • Monitoring │                              │ • Monitoring │             │  │
│  │  │ • Audit Log  │                              │ • Audit Log  │             │  │
│  │  └──────────────┘                              └──────────────┘             │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              SECURITY LAYERS                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                       EXTERNAL SECURITY LAYER                              │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │  │
│  │  │   AWS SHIELD    │    │    AWS WAF      │    │   ROUTE 53      │        │  │
│  │  │   (DDoS Protect)│    │  (Web Firewall) │    │   (DNS Security)│        │  │
│  │  │                 │    │                 │    │                 │        │  │
│  │  │ • Layer 3/4     │    │ • SQL Injection │    │ • DNS Filtering │        │  │
│  │  │ • Volumetric    │    │ • XSS Prevention│    │ • Health Check  │        │  │
│  │  │ • Protocol      │    │ • Rate Limiting │    │ • Failover      │        │  │
│  │  │ • Application   │    │ • IP Filtering  │    │ • Geo Routing   │        │  │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘        │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                       NETWORK SECURITY LAYER                               │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      SECURITY GROUPS                                │  │  │
│  │  │                                                                      │  │  │
│  │  │  ALB-SG:           Web-SG:            API-SG:            DB-SG:     │  │  │
│  │  │  • 80/443 → Web    • 80/443 → API    • 8000 → DB        • 5432     │  │  │
│  │  │  • Health Check    • Health Check    • Health Check     • Internal  │  │  │
│  │  │                                                                      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      NETWORK ACLS                                   │  │  │
│  │  │                                                                      │  │  │
│  │  │  Public Subnet:    Private Subnet:    Database Subnet:              │  │  │
│  │  │  • Allow 80/443    • Allow Internal   • Allow 5432                  │  │  │
│  │  │  • Deny All Other  • Deny External    • Deny All Other              │  │  │
│  │  │                                                                      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                      APPLICATION SECURITY LAYER                            │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      CONTAINER SECURITY                             │  │  │
│  │  │                                                                      │  │  │
│  │  │  • Non-root user execution                                           │  │  │
│  │  │  • Read-only root filesystem                                         │  │  │
│  │  │  • Resource limits (CPU/Memory)                                      │  │  │
│  │  │  • Security scanning                                                 │  │  │
│  │  │  • Secrets management                                                │  │  │
│  │  │  • Network isolation                                                 │  │  │
│  │  │                                                                      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      DATA SECURITY                                  │  │  │
│  │  │                                                                      │  │  │
│  │  │  • Encryption at rest (EBS/RDS)                                     │  │  │
│  │  │  • Encryption in transit (TLS 1.3)                                  │  │  │
│  │  │  • Database encryption                                               │  │  │
│  │  │  • Backup encryption                                                 │  │  │
│  │  │  • Secrets encryption                                                │  │  │
│  │  │  • Multi-tenant isolation                                            │  │  │
│  │  │                                                                      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Technical Specifications

### Infrastructure Components

#### 1. Compute Resources

**Web Tier (Frontend) - EC2 Instances:**
- **Instance Type**: m5.large (2 vCPU, 8 GB RAM) - Minimum
- **Instance Type**: m5.xlarge (4 vCPU, 16 GB RAM) - Recommended
- **Auto Scaling Group**: 2-8 instances
- **Operating System**: Amazon Linux 2023
- **Storage**: 100 GB gp3 EBS (encrypted)
- **Availability Zones**: Multi-AZ deployment

**API Tier (Backend) - EC2 Instances:**
- **Instance Type**: m5.xlarge (4 vCPU, 16 GB RAM) - Minimum
- **Instance Type**: m5.2xlarge (8 vCPU, 32 GB RAM) - Recommended
- **Auto Scaling Group**: 2-6 instances
- **Operating System**: Amazon Linux 2023
- **Storage**: 200 GB gp3 EBS (encrypted)
- **Availability Zones**: Multi-AZ deployment

**Database Tier - RDS PostgreSQL:**
- **Instance Class**: db.r5.xlarge (4 vCPU, 32 GB RAM) - Minimum
- **Instance Class**: db.r5.2xlarge (8 vCPU, 64 GB RAM) - Recommended
- **Engine**: PostgreSQL 15 with pgvector extension
- **Storage**: 1000 GB gp3 (encrypted)
- **Multi-AZ**: Enabled for high availability
- **Read Replicas**: 2 replicas for read scaling

#### 2. Network Architecture

**VPC Configuration:**
- **CIDR Block**: 10.0.0.0/16
- **Public Subnet**: 10.0.1.0/24 (NAT Gateway, ALB)
- **Private Subnet (Web)**: 10.0.2.0/24 (Frontend containers)
- **Private Subnet (API)**: 10.0.3.0/24 (Backend containers)
- **Database Subnet**: 10.0.4.0/24 (RDS PostgreSQL)
- **Internet Gateway**: Public internet access
- **NAT Gateway**: Outbound internet for private subnets

**Load Balancer Configuration:**
- **Type**: Application Load Balancer (ALB)
- **Scheme**: Internet-facing
- **Listeners**: HTTP (80) → HTTPS (443)
- **SSL/TLS**: AWS Certificate Manager
- **Health Checks**: /health endpoint
- **Target Groups**: Web and API tiers

#### 3. Security Configuration

**Security Groups:**
```
ALB Security Group (alb-sg):
  Inbound:
    - Port 80: 0.0.0.0/0 (HTTP → HTTPS redirect)
    - Port 443: 0.0.0.0/0 (HTTPS)
  Outbound:
    - Port 3000: Web-SG (Frontend)
    - Port 8000: API-SG (Backend)

Web Tier Security Group (web-sg):
  Inbound:
    - Port 3000: ALB-SG (Frontend traffic)
    - Port 22: Admin-SG (SSH)
  Outbound:
    - Port 8000: API-SG (Backend API)
    - Port 443: 0.0.0.0/0 (HTTPS)

API Tier Security Group (api-sg):
  Inbound:
    - Port 8000: Web-SG (Backend API)
    - Port 22: Admin-SG (SSH)
  Outbound:
    - Port 5432: DB-SG (Database)
    - Port 443: 0.0.0.0/0 (HTTPS)

Database Security Group (db-sg):
  Inbound:
    - Port 5432: API-SG (PostgreSQL)
  Outbound:
    - None (database isolation)
```

**Network ACLs:**
```
Public Subnet ACL:
  Inbound:
    - Port 80: 0.0.0.0/0
    - Port 443: 0.0.0.0/0
    - Ephemeral ports: 32768-65535
  Outbound:
    - All traffic: 0.0.0.0/0

Private Subnet ACL:
  Inbound:
    - Port 3000: 10.0.0.0/16
    - Port 8000: 10.0.0.0/16
    - Port 22: 10.0.0.0/16
  Outbound:
    - All traffic: 10.0.0.0/16
    - Port 443: 0.0.0.0/0

Database Subnet ACL:
  Inbound:
    - Port 5432: 10.0.0.0/16
  Outbound:
    - None
```

### Application Architecture

#### 1. Docker Container Configuration

**Frontend Container (Next.js):**
```dockerfile
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM base AS runtime
COPY . .
RUN npm run build
EXPOSE 3000
USER node
CMD ["npm", "start"]
```

**Backend Container (FastAPI):**
```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
COPY . .
EXPOSE 8000
USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Container Orchestration

**Docker Compose Configuration:**
```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NODE_ENV=production
    volumes:
      - app_logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - database
    environment:
      - DATABASE_URL=postgresql://user:${DB_PASSWORD}@db:5432/migration_db
      - CREWAI_ENABLED=true
      - ENVIRONMENT=production
    volumes:
      - app_logs:/app/logs
      - app_data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  database:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=migration_db
      - POSTGRES_USER=migration_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - postgres_backup:/backup
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U migration_user -d migration_db"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  postgres_backup:
  app_logs:
  app_data:
```

### Security Implementation

#### 1. Data Protection

**Encryption at Rest:**
- **EBS Volumes**: AWS KMS encryption (customer-managed keys)
- **RDS Database**: Encryption enabled with AWS KMS
- **S3 Buckets**: SSE-S3 encryption for backups
- **Application Secrets**: AWS Secrets Manager

**Encryption in Transit:**
- **External Communication**: TLS 1.3 minimum
- **Internal Communication**: TLS 1.2 minimum
- **Database Connections**: SSL/TLS enforced
- **Container Communication**: Docker overlay network encryption

#### 2. Identity and Access Management

**IAM Roles and Policies:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "rds:DescribeDBInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-west-2"]
        }
      }
    }
  ]
}
```

**Container Security:**
- **Non-root execution**: All containers run as non-root users
- **Resource limits**: CPU and memory constraints
- **Security scanning**: Continuous vulnerability scanning
- **Secrets management**: Environment variables via AWS Secrets Manager
- **Network isolation**: Container-level network policies

#### 3. Monitoring and Logging

**CloudWatch Integration:**
```yaml
Monitoring Configuration:
  Metrics:
    - CPU utilization
    - Memory usage
    - Network I/O
    - Application metrics
    - Database performance
  
  Logs:
    - Application logs
    - Access logs
    - Error logs
    - Security events
    - Audit trails
  
  Alarms:
    - High CPU (>80%)
    - Memory exhaustion (>90%)
    - Failed health checks
    - Database connection issues
    - Security violations
```

**Security Monitoring:**
- **AWS GuardDuty**: Threat detection
- **AWS Security Hub**: Security posture management
- **AWS Config**: Configuration compliance
- **VPC Flow Logs**: Network traffic analysis
- **CloudTrail**: API call auditing

### Deployment Process

#### 1. Infrastructure as Code

**CloudFormation Template Structure:**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'AI Force Migration Platform - Enterprise Deployment'

Parameters:
  Environment:
    Type: String
    Default: 'production'
    AllowedValues: [development, staging, production]
  
  VPCCidr:
    Type: String
    Default: '10.0.0.0/16'
  
  DBPassword:
    Type: String
    NoEcho: true
    MinLength: 12

Resources:
  # VPC and Networking
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VPCCidr
      EnableDnsHostnames: true
      EnableDnsSupport: true
  
  # Security Groups
  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: ALB Security Group
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
  
  # Auto Scaling Groups
  WebTierASG:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      MinSize: 2
      MaxSize: 8
      DesiredCapacity: 2
      LaunchTemplate:
        LaunchTemplateId: !Ref WebTierLaunchTemplate
        Version: !GetAtt WebTierLaunchTemplate.LatestVersionNumber
  
  # RDS Database
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS
      SubnetIds:
        - !Ref DatabaseSubnet1
        - !Ref DatabaseSubnet2
  
  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.r5.xlarge
      Engine: postgres
      EngineVersion: '15.4'
      MasterUsername: migration_user
      MasterUserPassword: !Ref DBPassword
      AllocatedStorage: 1000
      StorageType: gp3
      StorageEncrypted: true
      MultiAZ: true
      DBSubnetGroupName: !Ref DBSubnetGroup
      VPCSecurityGroups:
        - !Ref DatabaseSecurityGroup
```

#### 2. CI/CD Pipeline

**Deployment Pipeline:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run security scan
        run: |
          # Container security scanning
          # Static code analysis
          # Dependency vulnerability check
  
  build:
    needs: security-scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push images
        run: |
          # Build Docker images
          # Security scan images
          # Push to ECR
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy infrastructure
        run: |
          # Deploy CloudFormation stack
          # Update Auto Scaling Groups
          # Run health checks
```

### Scaling and Performance

#### 1. Auto Scaling Configuration

**Web Tier Auto Scaling:**
```yaml
Auto Scaling Policy:
  MinSize: 2
  MaxSize: 8
  DesiredCapacity: 2
  TargetCapacity: 70% CPU
  ScaleOutCooldown: 300s
  ScaleInCooldown: 300s
  HealthCheckGracePeriod: 300s
  HealthCheckType: ELB
```

**API Tier Auto Scaling:**
```yaml
Auto Scaling Policy:
  MinSize: 2
  MaxSize: 6
  DesiredCapacity: 2
  TargetCapacity: 70% CPU
  ScaleOutCooldown: 300s
  ScaleInCooldown: 300s
  HealthCheckGracePeriod: 300s
  HealthCheckType: ELB
```

#### 2. Database Scaling

**RDS Configuration:**
```yaml
Primary Database:
  InstanceClass: db.r5.xlarge
  MultiAZ: true
  BackupRetentionPeriod: 30
  PreferredBackupWindow: "03:00-04:00"
  PreferredMaintenanceWindow: "sun:04:00-sun:05:00"

Read Replicas:
  Count: 2
  InstanceClass: db.r5.large
  AutoMinorVersionUpgrade: true
  ReadReplicaIdentifier: migration-db-replica
```

### Backup and Disaster Recovery

#### 1. Backup Strategy

**Database Backups:**
```yaml
RDS Backup Configuration:
  AutomatedBackups:
    RetentionPeriod: 30 days
    BackupWindow: "03:00-04:00 UTC"
    DeleteAutomatedBackups: false
  
  Manual Snapshots:
    Frequency: Weekly
    RetentionPeriod: 1 year
    CrossRegionCopy: true
    DestinationRegion: us-west-2
```

**Application Backups:**
```yaml
EBS Snapshot Configuration:
  Frequency: Daily
  RetentionPeriod: 30 days
  CrossRegionCopy: true
  DestinationRegion: us-west-2
  
Configuration Backups:
  S3Bucket: migration-platform-config-backup
  Frequency: On every deployment
  RetentionPeriod: 2 years
  Encryption: AES-256
```

#### 2. Disaster Recovery

**Recovery Objectives:**
- **RTO (Recovery Time Objective)**: 2 hours
- **RPO (Recovery Point Objective)**: 15 minutes

**Recovery Procedures:**
1. **Database Recovery**: Restore from point-in-time backup
2. **Application Recovery**: Deploy from latest AMI/container images
3. **Infrastructure Recovery**: CloudFormation stack recreation
4. **Data Recovery**: Restore from S3 backups
5. **Network Recovery**: VPC and security group recreation
6. **Verification**: Complete system functionality testing

### Cost Optimization

#### 1. Resource Optimization

**Reserved Instances:**
```yaml
Reserved Instance Strategy:
  WebTier:
    InstanceType: m5.large
    Term: 3 years
    PaymentOption: Partial upfront
    Coverage: 70% of baseline capacity
  
  APITier:
    InstanceType: m5.xlarge
    Term: 3 years
    PaymentOption: Partial upfront
    Coverage: 70% of baseline capacity
  
  Database:
    InstanceType: db.r5.xlarge
    Term: 3 years
    PaymentOption: Partial upfront
    Coverage: 100% of primary database
```

**Spot Instances:**
```yaml
Spot Instance Configuration:
  AutoScalingGroup: WebTierASG
  MixedInstancesPolicy:
    OnDemandBaseCapacity: 2
    OnDemandPercentageAboveBaseCapacity: 50
    SpotAllocationStrategy: diversified
    SpotInstancePools: 3
```

#### 2. Estimated Monthly Costs

**Infrastructure Costs (Production):**
```yaml
Compute Resources:
  WebTier: $780 (6 x m5.large)
  APITier: $960 (4 x m5.xlarge)
  Database: $1,200 (db.r5.xlarge + 2 replicas)
  
Network Resources:
  ALB: $25
  NAT Gateway: $45
  Data Transfer: $150
  
Storage:
  EBS: $300
  RDS Storage: $200
  S3 Backup: $100
  
Monitoring:
  CloudWatch: $75
  GuardDuty: $50
  Config: $25
  
Total Monthly: ~$3,910
```

**Annual Cost Optimization:**
```yaml
Reserved Instance Savings: -$1,200/month
Spot Instance Savings: -$200/month
Storage Optimization: -$100/month

Optimized Monthly Cost: ~$2,410
Annual Savings: ~$18,000 (46% reduction)
```

## Active Directory Integration

### Authentication Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           AD INTEGRATION ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                        CORPORATE NETWORK                                    │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │  │
│  │  │  DOMAIN USERS   │    │  ACTIVE         │    │  DOMAIN         │        │  │
│  │  │  (Employees)    │    │  DIRECTORY      │    │  CONTROLLERS    │        │  │
│  │  │                 │    │  (Primary)      │    │  (Secondary)    │        │  │
│  │  │ • Authentication│    │                 │    │                 │        │  │
│  │  │ • Authorization │    │ • User Store    │    │ • Replication   │        │  │
│  │  │ • Group Member  │    │ • Group Policy  │    │ • Failover      │        │  │
│  │  │ • RBAC          │    │ • Security      │    │ • Load Balance  │        │  │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘        │  │
│  │           │                       │                       │                │  │
│  │           │                       │                       │                │  │
│  │           │ LDAPS/636             │ LDAPS/636             │ LDAPS/636      │  │
│  │           │ (Encrypted)           │ (Encrypted)           │ (Encrypted)    │  │
│  │           │                       │                       │                │  │
│  └───────────┼───────────────────────┼───────────────────────┼────────────────┘  │
│              │                       │                       │                   │
│              │                       │                       │                   │
│              │ VPN/ExpressRoute      │ VPN/ExpressRoute      │ VPN/ExpressRoute  │
│              │ (Secure Channel)      │ (Secure Channel)      │ (Secure Channel)  │
│              │                       │                       │                   │
│  ┌───────────▼───────────────────────▼───────────────────────▼───────────────┐  │
│  │                            AWS ENVIRONMENT                                 │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                        API TIER                                     │  │  │
│  │  │                                                                      │  │  │
│  │  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │  │  │
│  │  │  │  BACKEND API    │    │  BACKEND API    │    │  BACKEND API    │ │  │  │
│  │  │  │  (Instance 1)   │    │  (Instance 2)   │    │  (Instance 3)   │ │  │  │
│  │  │  │                 │    │                 │    │                 │ │  │  │
│  │  │  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │ │  │  │
│  │  │  │ │AD Connector │ │    │ │AD Connector │ │    │ │AD Connector │ │ │  │  │
│  │  │  │ │  Service    │ │    │ │  Service    │ │    │ │  Service    │ │ │  │  │
│  │  │  │ │             │ │    │ │             │ │    │ │             │ │ │  │  │
│  │  │  │ │ • LDAP Auth │ │    │ │ • LDAP Auth │ │    │ │ • LDAP Auth │ │ │  │  │
│  │  │  │ │ • Group Sync│ │    │ │ • Group Sync│ │    │ │ • Group Sync│ │ │  │  │
│  │  │  │ │ • RBAC Map  │ │    │ │ • RBAC Map  │ │    │ │ • RBAC Map  │ │ │  │  │
│  │  │  │ │ • JWT Issue │ │    │ │ │ • JWT Issue │ │    │ │ • JWT Issue │ │ │  │  │
│  │  │  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │ │  │  │
│  │  │  └─────────────────┘    └─────────────────┘    └─────────────────┘ │  │  │
│  │  │                                   │                                 │  │  │
│  │  │                                   │                                 │  │  │
│  │  │                                   ▼                                 │  │  │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │                      USER STORE                                 │ │  │  │
│  │  │  │                   (PostgreSQL)                                  │ │  │  │
│  │  │  │                                                                 │ │  │  │
│  │  │  │ • User Profiles                                                 │ │  │  │
│  │  │  │ • Group Mappings                                                │ │  │  │
│  │  │  │ • Role Assignments                                              │ │  │  │
│  │  │  │ • Session Management                                            │ │  │  │
│  │  │  │ • Audit Logging                                                 │ │  │  │
│  │  │  │ • Multi-tenant Context                                          │ │  │  │
│  │  │  └─────────────────────────────────────────────────────────────────┘ │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### AD Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            AUTHENTICATION FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │     USER        │    │   FRONTEND      │    │   BACKEND       │                │
│  │   (Browser)     │    │   (Next.js)     │    │   (FastAPI)     │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           │                       │                       │                        │
│           │ 1. Login Request      │                       │                        │
│           │ (Username/Password)   │                       │                        │
│           ├──────────────────────►│                       │                        │
│           │                       │                       │                        │
│           │                       │ 2. Authentication     │                        │
│           │                       │ Request               │                        │
│           │                       ├──────────────────────►│                        │
│           │                       │                       │                        │
│           │                       │                       │ ┌─────────────────┐    │
│           │                       │                       │ │  ACTIVE         │    │
│           │                       │                       │ │  DIRECTORY      │    │
│           │                       │                       │ │  (LDAPS/636)    │    │
│           │                       │                       │ └─────────────────┘    │
│           │                       │                       │          │             │
│           │                       │                       │          │             │
│           │                       │                       │ 3. LDAP Bind Request   │
│           │                       │                       │ (Username/Password)    │
│           │                       │                       │ ├──────────────────────►│
│           │                       │                       │          │             │
│           │                       │                       │          │ 4. Auth     │
│           │                       │                       │          │ Response    │
│           │                       │                       │ ◄────────┼─────────────│
│           │                       │                       │          │             │
│           │                       │                       │ 5. User Attributes     │
│           │                       │                       │ Query (Groups/Roles)   │
│           │                       │                       │ ├──────────────────────►│
│           │                       │                       │          │             │
│           │                       │                       │          │ 6. Attributes│
│           │                       │                       │          │ Response    │
│           │                       │                       │ ◄────────┼─────────────│
│           │                       │                       │          │             │
│           │                       │                       │ ┌─────────────────┐    │
│           │                       │                       │ │   DATABASE      │    │
│           │                       │                       │ │  (PostgreSQL)   │    │
│           │                       │                       │ └─────────────────┘    │
│           │                       │                       │          │             │
│           │                       │                       │          │             │
│           │                       │                       │ 7. Create/Update User  │
│           │                       │                       │ Profile & Roles        │
│           │                       │                       │ ├──────────────────────►│
│           │                       │                       │          │             │
│           │                       │                       │          │ 8. User     │
│           │                       │                       │          │ Record      │
│           │                       │                       │ ◄────────┼─────────────│
│           │                       │                       │          │             │
│           │                       │                       │ 9. Generate JWT Token  │
│           │                       │                       │ (User Context)         │
│           │                       │                       │          │             │
│           │                       │ 10. JWT Token         │                        │
│           │                       │ (Authentication       │                        │
│           │                       │ Success)              │                        │
│           │                       │ ◄─────────────────────┤                        │
│           │                       │                       │                        │
│           │ 11. Set Session       │                       │                        │
│           │ Cookie & Redirect     │                       │                        │
│           │ ◄─────────────────────┤                       │                        │
│           │                       │                       │                        │
│           │                       │                       │                        │
│           │ 12. Authenticated     │                       │                        │
│           │ Application Access    │                       │                        │
│           │ ◄─────────────────────┤                       │                        │
│           │                       │                       │                        │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Security Controls

**AD Integration Security:**
- **Encrypted Communication**: LDAPS (LDAP over SSL/TLS) on port 636
- **Certificate Validation**: Full certificate chain validation
- **Multi-Factor Authentication**: Support for MFA integration
- **Conditional Access**: Context-based access policies
- **Group-Based Authorization**: AD group to application role mapping
- **Session Management**: Secure session handling with timeout
- **Audit Logging**: Complete authentication audit trail

**Network Security:**
- **VPN/ExpressRoute**: Secure connection to corporate network
- **Firewall Rules**: Restrictive firewall policies
- **Network Segmentation**: Isolated network segments
- **DDoS Protection**: AWS Shield and WAF protection
- **Intrusion Detection**: GuardDuty threat detection

**Data Security:**
- **Encryption at Rest**: All data encrypted at rest
- **Encryption in Transit**: TLS 1.3 for all communications
- **Key Management**: AWS KMS for encryption keys
- **Access Controls**: Role-based access control (RBAC)
- **Data Classification**: Sensitive data classification
- **Backup Encryption**: Encrypted backup storage

## Compliance and Audit

### Security Compliance Framework

**Compliance Standards:**
- **SOC 2 Type II**: System and Organization Controls
- **ISO 27001**: Information Security Management
- **NIST Cybersecurity Framework**: Comprehensive security controls
- **PCI DSS**: Payment Card Industry Data Security Standard
- **GDPR**: General Data Protection Regulation compliance
- **HIPAA**: Healthcare information protection (if applicable)

**Audit Requirements:**
- **Access Logging**: All user access logged and monitored
- **Change Management**: All system changes tracked
- **Incident Response**: Documented incident response procedures
- **Vulnerability Management**: Regular vulnerability assessments
- **Penetration Testing**: Annual penetration testing
- **Compliance Reporting**: Regular compliance assessments

### Monitoring and Alerting

**Security Event Monitoring:**
```yaml
CloudWatch Alarms:
  Authentication:
    - Failed login attempts > 5/minute
    - Successful logins outside business hours
    - Multiple failed logins from same IP
    - Privilege escalation attempts
  
  Network:
    - Unusual network traffic patterns
    - Outbound connections to unknown hosts
    - Port scanning attempts
    - DDoS attack indicators
  
  Application:
    - Application errors > 10/minute
    - Database connection failures
    - High CPU/memory usage
    - Disk space exhaustion
  
  Security:
    - Unauthorized access attempts
    - Configuration changes
    - Security group modifications
    - Root account usage
```

**Incident Response:**
```yaml
Response Procedures:
  Detection:
    - Automated monitoring alerts
    - Manual security reviews
    - User reports
    - Third-party notifications
  
  Response:
    - Incident classification
    - Stakeholder notification
    - Containment actions
    - Evidence preservation
  
  Recovery:
    - System restoration
    - Service recovery
    - Business continuity
    - Lessons learned
```

## Operations and Maintenance

### Operational Procedures

**Regular Maintenance:**
- **Security Patching**: Monthly security updates
- **System Updates**: Quarterly system updates
- **Certificate Renewal**: Annual certificate updates
- **Backup Testing**: Monthly backup verification
- **Disaster Recovery**: Quarterly DR testing
- **Performance Tuning**: Monthly performance review
- **Capacity Planning**: Quarterly capacity assessment
- **Security Assessment**: Annual security review

**Change Management:**
```yaml
Change Process:
  Planning:
    - Change request documentation
    - Risk assessment
    - Impact analysis
    - Approval workflow
  
  Implementation:
    - Pre-change backup
    - Staged deployment
    - Testing verification
    - Rollback procedures
  
  Validation:
    - Functionality testing
    - Performance verification
    - Security validation
    - User acceptance testing
```

### Support Structure

**24/7 Operations:**
- **Level 1**: Basic monitoring and incident response
- **Level 2**: Application troubleshooting and system administration
- **Level 3**: Advanced technical support and architecture changes
- **Level 4**: Vendor escalation and critical incident management

**Escalation Procedures:**
```yaml
Escalation Matrix:
  Critical (P1):
    - Immediate notification
    - All hands response
    - Executive notification
    - Vendor engagement
  
  High (P2):
    - 15-minute response
    - Senior engineer assignment
    - Management notification
    - Status updates every hour
  
  Medium (P3):
    - 1-hour response
    - Standard assignment
    - Regular status updates
    - Business hours resolution
  
  Low (P4):
    - 4-hour response
    - Planned resolution
    - Weekly status updates
    - Best effort resolution
```

## Conclusion

This enterprise solution architecture provides a comprehensive, secure, and scalable deployment model for the AI Force Migration Platform on AWS infrastructure. The design ensures:

### Key Benefits:
- **Security**: Multi-layered security architecture with defense-in-depth
- **Scalability**: Auto-scaling infrastructure for variable workloads
- **Reliability**: High availability with multi-AZ deployment
- **Compliance**: Comprehensive compliance framework
- **Performance**: Optimized architecture for high performance
- **Cost-Effectiveness**: Reserved instances and cost optimization strategies

### Security Posture:
- **Network Security**: VPC isolation, security groups, and NACLs
- **Application Security**: Container security and secure coding practices
- **Data Security**: Encryption at rest and in transit
- **Identity Security**: Active Directory integration with MFA
- **Operational Security**: Comprehensive monitoring and incident response

### Operational Excellence:
- **Automation**: Infrastructure as Code and CI/CD pipelines
- **Monitoring**: Comprehensive monitoring and alerting
- **Backup**: Automated backup and disaster recovery
- **Maintenance**: Proactive maintenance and change management
- **Support**: 24/7 operations and escalation procedures

This architecture is designed to meet enterprise security requirements while providing the flexibility and scalability needed for a production cloud migration platform. The integration with Active Directory ensures seamless authentication and authorization within the corporate environment, while the comprehensive security controls protect against modern threats and ensure regulatory compliance.

---

**Document Classification**: Internal Use - Security Review  
**Last Updated**: January 15, 2025  
**Architecture Version**: 2.0  
**Review Status**: Ready for Security Team Assessment
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USERS         │    │   AWS ALB       │    │   EC2 INSTANCE  │
│   (HTTPS/443)   │    │   (SSL Term)    │    │   (HTTP/8081)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ HTTPS/443             │                       │
         │ ✅ TLS 1.3           │                       │
         │ ✅ AWS Certificate    │                       │
         ├──────────────────────▶│                       │
         │                       │ ✅ WAF Filtering      │
         │                       │ ✅ DDoS Protection    │
         │                       │ ✅ Health Checks      │
         │                       │                       │
         │                       │ HTTP/8081             │
         │                       │ (Internal Network)    │
         │                       ├──────────────────────▶│
         │                       │                       │
         │                       │                       │ ┌─────────────────┐
         │                       │                       │ │   DOCKER NET    │
         │                       │                       │ │   (172.18.0.0)  │
         │                       │                       │ └─────────────────┘
         │                       │                       │          │
         │                       │                       │          │ HTTP/8000
         │                       │                       │          │ (Backend API)
         │                       │                       │          │
         │                       │                       │          ▼
         │                       │                       │ ┌─────────────────┐
         │                       │                       │ │   POSTGRESQL    │
         │                       │                       │ │   (5432)        │
         │                       │                       │ └─────────────────┘
```

## 🛡️ AWS Security Architecture

### Network Security
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                INTERNET                                             │
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   ATTACKERS     │    │   LEGITIMATE    │    │   AD USERS      │                │
│  │   (Blocked)     │    │   USERS         │    │   (Authenticated│                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           │ ❌ BLOCKED             │ ✅ ALLOWED            │ ✅ ALLOWED            │
│           │                       │                       │                        │
│           ▼                       ▼                       ▼                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                              AWS SHIELD                                     │  │
│  │                         (DDoS Protection)                                  │  │
│  │                                                                             │  │
│  │  ✅ Automatic DDoS Protection                                               │  │
│  │  ✅ Layer 3/4 Attack Mitigation                                             │  │
│  │  ✅ Real-time Attack Detection                                              │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Clean Traffic Only
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────────────┐
│                                AWS WAF                                              │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                        WAF RULES CONFIGURATION                              │  │
│  │                                                                              │  │
│  │  ✅ SQL Injection Protection                                                 │  │
│  │  ✅ XSS Attack Prevention                                                    │  │
│  │  ✅ IP Reputation Filtering                                                  │  │
│  │  ✅ Rate Limiting (Additional Layer)                                         │  │
│  │  ✅ Geo-blocking (Optional)                                                  │  │
│  │  ✅ Custom Security Rules                                                    │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Filtered Traffic
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────────────┐
│                           APPLICATION LOAD BALANCER                                 │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         SSL/TLS TERMINATION                                 │  │
│  │                                                                              │  │
│  │  ✅ TLS 1.3 Encryption                                                       │  │
│  │  ✅ AWS Certificate Manager                                                  │  │
│  │  ✅ Perfect Forward Secrecy                                                  │  │
│  │  ✅ Health Check Monitoring                                                  │  │
│  │  ✅ Multi-AZ Deployment                                                      │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Container Security
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EC2 UBUNTU INSTANCE                                    │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                           DOCKER SECURITY                                   │  │
│  │                                                                              │  │
│  │  ✅ Container Isolation                                                      │  │
│  │  ✅ Network Segmentation (Bridge Network)                                   │  │
│  │  ✅ Resource Limits (CPU/Memory)                                            │  │
│  │  ✅ Read-only Root Filesystem                                               │  │
│  │  ✅ Non-root User Execution                                                 │  │
│  │  ✅ Security Scanning (Vulnerability Detection)                             │  │
│  │                                                                              │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    CONTAINER NETWORK                                │  │  │
│  │  │                                                                     │  │  │
│  │  │  Frontend (172.18.0.10) ←→ Backend (172.18.0.20)                  │  │  │
│  │  │                    ↓                                                │  │  │
│  │  │              Database (172.18.0.30)                                │  │  │
│  │  │                                                                     │  │  │
│  │  │  Security Controls:                                                 │  │  │
│  │  │  • No external database access                                     │  │  │
│  │  │  • Internal communication only                                     │  │  │
│  │  │  • Database not exposed to host                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 🔍 Security Controls Implementation

### AWS Security Group Rules
```
ALB Security Group (alb-sg):
  Inbound Rules:
    - Port 80 (HTTP): 0.0.0.0/0 → Redirect to HTTPS
    - Port 443 (HTTPS): 0.0.0.0/0 → SSL Termination
  
  Outbound Rules:
    - Port 8081: → EC2 Security Group (Frontend)
    - Port 8000: → EC2 Security Group (Backend Health)

EC2 Security Group (ec2-sg):
  Inbound Rules:
    - Port 8081: ALB Security Group → Frontend Container
    - Port 8000: ALB Security Group → Backend Health Check
    - Port 22: Admin IP Ranges → SSH Access
  
  Outbound Rules:
    - Port 443: 0.0.0.0/0 → HTTPS Internet Access
    - Port 80: 0.0.0.0/0 → HTTP Internet Access (Package Updates)

Database Security:
  - No external access (container internal only)
  - PostgreSQL port 5432 internal to Docker network
  - Database credentials via environment variables
  - Encrypted storage volumes
```

### Authentication and Authorization
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               AD INTEGRATION                                        │
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   USERS         │    │   ACTIVE        │    │   APPLICATION   │                │
│  │   (AD Domain)   │    │   DIRECTORY     │    │   (EC2)         │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           │ LDAP/LDAPS            │                       │                        │
│           │ (Port 636)            │                       │                        │
│           ├──────────────────────▶│                       │                        │
│           │                       │                       │                        │
│           │                       │ SAML/OAuth Response   │                        │
│           │                       ├──────────────────────▶│                        │
│           │                       │                       │                        │
│           │                       │                       │ ┌─────────────────┐    │
│           │                       │                       │ │   BACKEND API   │    │
│           │                       │                       │ │   (Port 8000)   │    │
│           │                       │                       │ └─────────────────┘    │
│           │                       │                       │          │             │
│           │                       │                       │          │             │
│           │                       │                       │          ▼             │
│           │                       │                       │ ┌─────────────────┐    │
│           │                       │                       │ │   POSTGRESQL    │    │
│           │                       │                       │ │   (User Store)  │    │
│           │                       │                       │ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 📊 Security Monitoring and Logging

### CloudWatch Monitoring
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              MONITORING STACK                                       │
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   CLOUDWATCH    │    │   CLOUDTRAIL    │    │   AWS CONFIG    │                │
│  │   METRICS       │    │   AUDIT LOGS    │    │   COMPLIANCE    │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           │                       │                       │                        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   • CPU Usage   │    │   • API Calls   │    │   • Security    │                │
│  │   • Memory      │    │   • Login Events │    │   • Compliance  │                │
│  │   • Disk I/O    │    │   • Access Logs  │    │   • Config      │                │
│  │   • Network     │    │   • Error Events │    │   • Changes     │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                            ALERTING                                         │  │
│  │                                                                              │  │
│  │  • High CPU Usage (>80%)                                                    │  │
│  │  • Memory Exhaustion (>90%)                                                 │  │
│  │  • Failed Login Attempts (>5/min)                                           │  │
│  │  • Application Errors (>10/min)                                             │  │
│  │  • Disk Space (>85%)                                                        │  │
│  │  • Network Anomalies                                                        │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 🔐 Security Best Practices Implemented

### Infrastructure Security
- ✅ **Multi-AZ Deployment**: ALB across multiple availability zones
- ✅ **Security Groups**: Least privilege access control
- ✅ **Private Subnets**: Database isolated from internet
- ✅ **VPC Flow Logs**: Network traffic monitoring
- ✅ **AWS Shield**: DDoS protection
- ✅ **AWS WAF**: Application firewall protection

### Application Security
- ✅ **Container Isolation**: Docker container security
- ✅ **Non-root Execution**: Containers run as non-root user
- ✅ **Resource Limits**: CPU and memory constraints
- ✅ **Health Checks**: Application monitoring
- ✅ **Encrypted Storage**: EBS volume encryption
- ✅ **Backup Strategy**: Automated backups

### Network Security
- ✅ **TLS 1.3**: Modern encryption protocols
- ✅ **Certificate Management**: AWS Certificate Manager
- ✅ **Network ACLs**: Additional network layer security
- ✅ **VPC Endpoints**: Private AWS service access
- ✅ **NAT Gateway**: Secure outbound internet access

## 📋 Compliance and Audit

### Security Compliance
- ✅ **SOC 2 Type II**: AWS compliance framework
- ✅ **ISO 27001**: Information security management
- ✅ **GDPR**: Data protection regulation compliance
- ✅ **HIPAA**: Healthcare data protection (if applicable)
- ✅ **PCI DSS**: Payment card industry standards

### Audit Trail
- ✅ **CloudTrail**: All API calls logged
- ✅ **VPC Flow Logs**: Network traffic audit
- ✅ **Application Logs**: Centralized logging
- ✅ **Security Events**: Real-time monitoring
- ✅ **Access Logs**: User activity tracking

## 🎯 AD Integration Security Requirements

### Prerequisites Met
- ✅ **Secure Communication**: HTTPS/TLS encryption
- ✅ **Network Isolation**: VPC security boundaries
- ✅ **Access Control**: Security group restrictions
- ✅ **Monitoring**: Comprehensive logging and alerting
- ✅ **Compliance**: Industry standard security controls

### AD-Specific Security
- ✅ **LDAPS Support**: Secure LDAP communication
- ✅ **Certificate Validation**: PKI certificate chains
- ✅ **Multi-Factor Authentication**: MFA integration ready
- ✅ **Conditional Access**: Context-based access control
- ✅ **Audit Logging**: Authentication event tracking

## 📝 Deployment Specifications

### EC2 Instance Configuration
```yaml
Instance Type: t3.medium (2 vCPU, 4 GB RAM)
Operating System: Ubuntu 22.04 LTS
Storage: 50 GB GP3 SSD (Encrypted)
Network: VPC with public/private subnets
Security: Security groups, NACLs, WAF
Monitoring: CloudWatch, CloudTrail
```

### Docker Compose Configuration
```yaml
services:
  migration-frontend:
    image: migration-frontend:latest
    ports: ["8081:3000"]
    networks: ["app-network"]
    
  migration-backend:
    image: migration-backend:latest
    ports: ["8000:8000"]
    networks: ["app-network"]
    
  pgvector16:
    image: pgvector/pgvector:16
    ports: ["5432:5432"]
    networks: ["app-network"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]
```

This AWS EC2 Ubuntu Docker architecture provides enterprise-grade security controls suitable for Active Directory integration and meets industry compliance requirements.

---

**Architecture Review By:** Cloud Security Team  
**Review Date:** July 10, 2025  
**Deployment Type:** AWS EC2 Ubuntu + Docker  
**Status:** Ready for AD Integration Security Review