# ADR-014: On-Premises Deployment Model for Regulated Environments

## Status
Proposed

## Context

The Adaptive Data Collection System (ADCS) design includes support for air-gapped and highly regulated environments (Tier 3) through an on-premises deployment model. This represents a significant deviation from our established "Docker-First Development Mandate" (ADR-010) and cloud-centric architecture patterns.

### Current Architecture Constraints
- **ADR-010**: Docker-First Development Mandate enforces container-based development and deployment
- **Cloud-Centric Design**: Existing platform targets cloud environments (Railway, Vercel, cloud databases)
- **Multi-Tenant SaaS Model**: Current architecture optimized for centralized SaaS delivery
- **Continuous Deployment**: Existing CI/CD pipelines assume cloud deployment targets

### Business Drivers for On-Premises Support
- **Regulated Industries**: Finance, healthcare, government require air-gapped environments
- **Data Sovereignty**: Compliance requirements prevent cloud data storage
- **Security Policies**: Enterprise security policies restrict external API access
- **Market Expansion**: Significant revenue opportunity in regulated markets

### Technical Challenges
1. **Infrastructure Management**: Customer infrastructure vs. managed cloud services
2. **Update Mechanisms**: Software updates in air-gapped environments
3. **Support Model**: Remote support without direct system access
4. **Security Model**: Self-managed vs. managed security infrastructure
5. **Scalability**: Single-tenant vs. multi-tenant optimization

## Decision

We will implement a **Hybrid Deployment Architecture** that supports both SaaS and on-premises deployment models through a modular, containerized approach that maintains consistency with our Docker-First mandate while enabling regulated environment support.

### Architectural Approach

#### 1. Modular Container Architecture
```yaml
# On-Premises Docker Compose Stack
services:
  collection-orchestrator:
    image: migrate-ui/collection-service:latest
    environment:
      - DEPLOYMENT_MODE=on_premises
      - TELEMETRY_ENABLED=false
  
  discovery-processor:
    image: migrate-ui/discovery-service:latest
    environment:
      - DEPLOYMENT_MODE=on_premises
  
  assessment-engine:
    image: migrate-ui/assessment-service:latest
    environment:
      - DEPLOYMENT_MODE=on_premises
  
  local-database:
    image: postgres:15
    volumes:
      - ./data:/var/lib/postgresql/data
```

#### 2. Deployment Mode Configuration
```typescript
interface DeploymentConfig {
  mode: 'saas' | 'on_premises';
  telemetry: {
    enabled: boolean;
    endpoint?: string;
  };
  database: {
    type: 'managed' | 'local';
    connection: DatabaseConfig;
  };
  security: {
    credential_storage: 'cloud_kms' | 'local_vault';
    encryption_keys: 'managed' | 'customer_managed';
  };
}
```

#### 3. Feature Parity Matrix
| Feature | SaaS | On-Premises | Notes |
|---------|------|-------------|-------|
| Collection Flow | ✅ | ✅ | Full feature parity |
| Discovery Flow | ✅ | ✅ | Full feature parity |
| Assessment Flow | ✅ | ✅ | Full feature parity |
| Multi-Tenancy | ✅ | ❌ | Single tenant per deployment |
| Cloud Telemetry | ✅ | ⚠️ | Optional, configurable |
| Auto-Updates | ✅ | ❌ | Manual update process |
| Managed Security | ✅ | ❌ | Customer-managed security |

### Implementation Strategy

#### Phase 1: Container Modularization (Within Existing Roadmap)
- Modularize existing services into deployment-agnostic containers
- Implement deployment mode configuration system
- Create local database and secrets management options

#### Phase 2: On-Premises Packaging (Future Release)
- Create on-premises installation packages
- Develop customer deployment automation
- Implement local update mechanisms

#### Phase 3: Regulated Environment Features (Future Release)
- Enhanced audit logging for compliance
- Local credential management system
- Air-gapped update mechanisms

### Technical Implementation

#### Container Strategy
```dockerfile
# Collection Service Dockerfile
FROM node:18-alpine
COPY . /app
WORKDIR /app

# Support both deployment modes
ENV DEPLOYMENT_MODE=saas
ENV DATABASE_TYPE=managed

# Conditional service initialization based on deployment mode
CMD ["npm", "run", "start:${DEPLOYMENT_MODE}"]
```

#### Configuration Management
```yaml
# config/on-premises.yml
deployment:
  mode: on_premises
  single_tenant: true
  
database:
  type: local
  host: local-postgres
  
security:
  credential_storage: local_vault
  encryption: customer_managed
  
telemetry:
  enabled: false
  
features:
  multi_tenant: false
  cloud_integrations: optional
```

#### Service Discovery
```typescript
class ServiceRegistry {
  constructor(deploymentMode: DeploymentMode) {
    if (deploymentMode === 'on_premises') {
      this.initializeLocalServices();
    } else {
      this.initializeCloudServices();
    }
  }
  
  private initializeLocalServices() {
    // Local service discovery and configuration
  }
  
  private initializeCloudServices() {
    // Cloud service discovery and configuration
  }
}
```

## Consequences

### Positive

1. **Market Expansion**: Enables entry into regulated industries with significant revenue potential
2. **Docker Consistency**: Maintains Docker-First principles through containerized on-premises deployment
3. **Code Reuse**: Single codebase supports both deployment models through configuration
4. **Customer Choice**: Flexible deployment options based on security and compliance requirements
5. **Competitive Advantage**: Differentiation through flexible deployment models

### Negative

1. **Increased Complexity**: Supporting two deployment models increases development and testing overhead
2. **Support Burden**: On-premises deployments require different support models and procedures
3. **Update Complexity**: Manual update processes for air-gapped environments
4. **Testing Overhead**: Must validate functionality across both deployment models
5. **Documentation Burden**: Separate documentation and procedures for each deployment model

### Risks

1. **Feature Divergence**: Risk of on-premises deployments falling behind SaaS features
   - **Mitigation**: Automated testing across both deployment modes in CI/CD pipeline
2. **Support Complexity**: Difficult remote troubleshooting for on-premises deployments
   - **Mitigation**: Comprehensive logging, diagnostic tools, and local support procedures
3. **Security Management**: Customer-managed security may be less secure than managed services
   - **Mitigation**: Security best practices documentation, automated security configuration
4. **Update Lag**: On-premises deployments may not receive timely security updates
   - **Mitigation**: Automated update packaging, security-focused update procedures

## Implementation

### Immediate Actions (Current Roadmap)
1. **Modularize Services**: Ensure all ADCS services are containerized and deployment-agnostic
2. **Configuration System**: Implement deployment mode configuration throughout codebase
3. **Local Database Support**: Ensure PostgreSQL can run locally with full feature support
4. **Security Abstraction**: Abstract credential management to support both cloud and local storage

### Future Roadmap Items
1. **On-Premises Installer**: Customer-friendly installation and configuration system
2. **Update Mechanism**: Secure, automated update system for on-premises deployments
3. **Local Monitoring**: On-premises monitoring and alerting capabilities
4. **Support Tools**: Remote diagnostic and troubleshooting capabilities

### Technical Validation Required
1. **Master Flow Orchestrator**: Validate single-tenant operation mode
2. **Database Isolation**: Ensure complete tenant isolation in single-tenant mode
3. **Service Communication**: Validate inter-service communication in local deployment
4. **Security Model**: Validate local credential management and encryption

## Alternatives Considered

### Alternative 1: SaaS-Only Approach
**Rejected**: Eliminates significant market opportunity in regulated industries

### Alternative 2: Separate On-Premises Product
**Rejected**: Increases development overhead and creates feature divergence risks

### Alternative 3: Cloud-Only with VPN Access
**Rejected**: Doesn't meet air-gapped environment requirements

### Alternative 4: Hybrid Cloud Deployment
**Rejected**: Still requires internet connectivity, doesn't address air-gapped requirements

## References

- **ADR-010**: Docker-First Development Mandate
- **ADR-013**: Adaptive Data Collection System Integration
- **Business Requirements**: Tier 3 and Tier 4 automation requirements
- **Security Requirements**: Regulated industry compliance needs

## Success Metrics

### Technical Metrics
- On-premises deployment completes successfully in <30 minutes
- Feature parity maintained >95% between SaaS and on-premises
- Update deployment completes successfully in <15 minutes
- Local credential management passes security audit

### Business Metrics
- Enables pursuit of regulated industry opportunities
- Customer satisfaction with deployment flexibility
- Support burden remains within acceptable limits
- Revenue growth from regulated market segments

---

*Date: 2025-07-19*  
*Authors: Architecture Team*  
*Status: Proposed - Requires stakeholder review and approval*