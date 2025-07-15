# AWS EC2 Development Server - Network Architecture

**Current Development Environment**  
**Document Date:** January 15, 2025  
**Deployment Type:** Single EC2 Instance with Docker Containers  
**Environment:** Development Server

## Overview

This document describes the current network architecture of the AI Force Migration Platform running on a single AWS EC2 instance. The platform uses Docker containers orchestrated by docker-compose to provide a complete development environment.

## Current Network Architecture

### Single Instance Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                AWS EC2 Instance                                    │
│                            (Single Development Server)                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                            INTERNET GATEWAY                                 │  │
│  │                         (AWS Security Group)                               │  │
│  │                                                                             │  │
│  │  • Port 22 (SSH) - Admin Access                                            │  │
│  │  • Port 8000 (HTTP) - Backend API                                          │  │
│  │  • Port 8081 (HTTP) - Frontend Application                                 │  │
│  │  • Port 5433 (TCP) - PostgreSQL Database (External)                       │  │
│  │  • Port 6379 (TCP) - Redis Cache (External)                               │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                        DOCKER BRIDGE NETWORK                               │  │
│  │                          (172.17.0.0/16)                                   │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │  │
│  │  │   Frontend      │  │    Backend      │  │   PostgreSQL    │             │  │
│  │  │   Container     │  │   Container     │  │   Container     │             │  │
│  │  │                 │  │                 │  │                 │             │  │
│  │  │ migration_      │  │ migration_      │  │ migration_      │             │  │
│  │  │ frontend        │  │ backend         │  │ postgres        │             │  │
│  │  │                 │  │                 │  │                 │             │  │
│  │  │ Port: 8081      │  │ Port: 8000      │  │ Port: 5432      │             │  │
│  │  │ (mapped to      │  │ (mapped to      │  │ (mapped to      │             │  │
│  │  │  host:8081)     │  │  host:8000)     │  │  host:5433)     │             │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘             │  │
│  │                                                                             │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                                  │  │
│  │  │     Redis       │  │  Assessment     │                                  │  │
│  │  │   Container     │  │    Worker       │                                  │  │
│  │  │                 │  │  (Optional)     │                                  │  │
│  │  │ migration_      │  │ migration_      │                                  │  │
│  │  │ redis           │  │ assessment_     │                                  │  │
│  │  │                 │  │ worker          │                                  │  │
│  │  │ Port: 6379      │  │ Internal Only   │                                  │  │
│  │  │ (mapped to      │  │                 │                                  │  │
│  │  │  host:6379)     │  │                 │                                  │  │
│  │  └─────────────────┘  └─────────────────┘                                  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Container Network Configuration

### Docker Compose Network Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          Docker Compose Network (Default)                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Container Name: migration_frontend                                                 │
│  ├─ Internal IP: 172.17.0.x                                                        │
│  ├─ Internal Port: 8081                                                            │
│  ├─ External Port: 8081 (Host mapping)                                             │
│  ├─ Network Access: Can reach backend via "backend:8000"                          │
│  └─ Purpose: Next.js frontend serving UI                                           │
│                                                                                     │
│  Container Name: migration_backend                                                  │
│  ├─ Internal IP: 172.17.0.x                                                        │
│  ├─ Internal Port: 8000                                                            │
│  ├─ External Port: 8000 (Host mapping)                                             │
│  ├─ Network Access: Can reach postgres via "postgres:5432"                        │
│  │                   Can reach redis via "redis:6379"                             │
│  └─ Purpose: FastAPI backend with CrewAI flows                                     │
│                                                                                     │
│  Container Name: migration_postgres                                                 │
│  ├─ Internal IP: 172.17.0.x                                                        │
│  ├─ Internal Port: 5432                                                            │
│  ├─ External Port: 5433 (Host mapping)                                             │
│  ├─ Network Access: Internal only (backend connections)                           │
│  └─ Purpose: PostgreSQL database with migration data                               │
│                                                                                     │
│  Container Name: migration_redis                                                    │
│  ├─ Internal IP: 172.17.0.x                                                        │
│  ├─ Internal Port: 6379                                                            │
│  ├─ External Port: 6379 (Host mapping)                                             │
│  ├─ Network Access: Internal + External (for debugging)                           │
│  └─ Purpose: Redis cache for session management                                    │
│                                                                                     │
│  Container Name: migration_assessment_worker (Optional)                             │
│  ├─ Internal IP: 172.17.0.x                                                        │
│  ├─ No External Port                                                               │
│  ├─ Network Access: Can reach postgres, redis, backend                            │
│  └─ Purpose: Background worker for assessment flows                                │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Security Groups Configuration

### Current AWS Security Group Rules

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         EC2 Security Group Rules                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  INBOUND RULES:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ Rule 1: SSH Access                                                          │  │
│  │ ├─ Port: 22                                                                 │  │
│  │ ├─ Protocol: TCP                                                            │  │
│  │ ├─ Source: Admin IP Range (e.g., 0.0.0.0/0 or specific IPs)               │  │
│  │ └─ Purpose: Server administration and deployment                            │  │
│  │                                                                             │  │
│  │ Rule 2: Frontend Application                                                │  │
│  │ ├─ Port: 8081                                                               │  │
│  │ ├─ Protocol: TCP                                                            │  │
│  │ ├─ Source: 0.0.0.0/0 (User access)                                         │  │
│  │ └─ Purpose: Next.js frontend user interface                                │  │
│  │                                                                             │  │
│  │ Rule 3: Backend API                                                         │  │
│  │ ├─ Port: 8000                                                               │  │
│  │ ├─ Protocol: TCP                                                            │  │
│  │ ├─ Source: 0.0.0.0/0 (API access)                                          │  │
│  │ └─ Purpose: FastAPI backend for API calls                                  │  │
│  │                                                                             │  │
│  │ Rule 4: PostgreSQL Database (Development)                                   │  │
│  │ ├─ Port: 5433                                                               │  │
│  │ ├─ Protocol: TCP                                                            │  │
│  │ ├─ Source: Admin IP Range (restricted)                                     │  │
│  │ └─ Purpose: Database administration and debugging                           │  │
│  │                                                                             │  │
│  │ Rule 5: Redis Cache (Development)                                           │  │
│  │ ├─ Port: 6379                                                               │  │
│  │ ├─ Protocol: TCP                                                            │  │
│  │ ├─ Source: Admin IP Range (restricted)                                     │  │
│  │ └─ Purpose: Redis monitoring and debugging                                 │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│  OUTBOUND RULES:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ Rule 1: All Traffic                                                         │  │
│  │ ├─ Port: All                                                                │  │
│  │ ├─ Protocol: All                                                            │  │
│  │ ├─ Destination: 0.0.0.0/0                                                  │  │
│  │ └─ Purpose: Internet access for updates and external API calls             │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Container Communication Flow

### Internal Network Communication

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        Container Communication Patterns                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Frontend Container (migration_frontend)                                           │
│  ├─ Connects to: backend:8000 (Internal Docker DNS)                               │
│  ├─ API Calls: HTTP requests to FastAPI backend                                   │
│  ├─ WebSocket: ws://backend:8000/ws (Real-time updates)                           │
│  └─ External Access: Host IP:8081 for user browsers                               │
│                                                                                     │
│  Backend Container (migration_backend)                                             │
│  ├─ Connects to: postgres:5432 (Database operations)                              │
│  ├─ Connects to: redis:6379 (Cache and session management)                        │
│  ├─ Database: PostgreSQL via SQLAlchemy async sessions                            │
│  ├─ Cache: Redis for background task queuing                                      │
│  └─ External Access: Host IP:8000 for API calls                                   │
│                                                                                     │
│  PostgreSQL Container (migration_postgres)                                         │
│  ├─ Accepts from: backend:5432 (Internal connections)                             │
│  ├─ Data Storage: /var/lib/postgresql/data (Docker volume)                        │
│  ├─ Health Check: pg_isready monitoring                                           │
│  └─ External Access: Host IP:5433 for admin connections                           │
│                                                                                     │
│  Redis Container (migration_redis)                                                 │
│  ├─ Accepts from: backend:6379 (Internal connections)                             │
│  ├─ Accepts from: assessment-worker:6379 (Background tasks)                       │
│  ├─ Data Storage: /data (Docker volume with persistence)                          │
│  └─ External Access: Host IP:6379 for debugging                                   │
│                                                                                     │
│  Assessment Worker Container (migration_assessment_worker)                          │
│  ├─ Connects to: postgres:5432 (Database operations)                              │
│  ├─ Connects to: redis:6379 (Task queue processing)                               │
│  ├─ Purpose: Background processing for assessment flows                           │
│  └─ Profile: worker (Optional container)                                          │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow and Network Paths

### User Request Flow

```
User Browser → Internet → AWS Security Group → EC2 Instance → Docker Container

1. User accesses frontend: Browser → EC2:8081 → migration_frontend container
2. Frontend API calls: migration_frontend → backend:8000 → migration_backend container
3. Database operations: migration_backend → postgres:5432 → migration_postgres container
4. Cache operations: migration_backend → redis:6379 → migration_redis container
5. Background processing: migration_backend → redis:6379 → migration_assessment_worker
```

## Network Security Considerations

### Current Security Measures

1. **AWS Security Groups**: Firewall rules controlling inbound/outbound traffic
2. **Docker Network Isolation**: Containers communicate via internal Docker network
3. **Port Mapping**: Only specific ports exposed to host system
4. **Internal DNS**: Container-to-container communication using Docker DNS resolution

### Security Recommendations for Development

1. **Restrict Database Access**: Limit PostgreSQL (5433) and Redis (6379) to admin IPs only
2. **Enable HTTPS**: Add SSL certificates for production-like testing
3. **Environment Variables**: Secure API keys and database credentials
4. **Network Monitoring**: Log network traffic for security analysis
5. **Regular Updates**: Keep Docker images and EC2 instance updated

## Deployment Commands

### Starting the Development Environment

```bash
# Start all core services
docker-compose up -d

# Start with assessment worker
docker-compose --profile worker up -d

# View running containers
docker-compose ps

# Monitor logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Network Troubleshooting

```bash
# Check container network
docker network ls
docker network inspect migrate-ui-orchestrator_default

# Test container connectivity
docker exec migration_backend ping migration_postgres
docker exec migration_frontend curl http://backend:8000/health

# Port verification
netstat -tlnp | grep -E ":(8000|8081|5433|6379)"
```

## Current Limitations

1. **Single Point of Failure**: All services on one EC2 instance
2. **No Load Balancing**: Direct container access without load balancer
3. **Limited Scalability**: Cannot scale individual services independently
4. **Development Configuration**: Not optimized for production workloads
5. **Basic Security**: Minimal security hardening for development use

---

**Document Status**: Current Development Configuration  
**Next Review**: When moving to production architecture  
**Maintained By**: Development Team