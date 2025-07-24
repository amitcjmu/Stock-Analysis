"""
Assessment Flow Architecture Standards Seed Data
Industry-standard templates for common technology stacks and engagement initialization.
"""

import logging
from typing import Any, Dict, List

from app.models.assessment_flow import EngagementArchitectureStandard
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# === TECHNOLOGY VERSION STANDARDS ===

TECH_VERSION_STANDARDS = [
    {
        "requirement_type": "java_versions",
        "description": "Minimum supported Java versions for cloud migration",
        "mandatory": True,
        "supported_versions": {
            "java": "11+",
            "spring_boot": "2.5+",
            "spring_framework": "5.3+",
            "maven": "3.6+",
            "gradle": "6.0+",
        },
        "requirement_details": {
            "rationale": "Java 8 end-of-life considerations and cloud platform requirements",
            "migration_path": "Upgrade to Java 11 LTS or Java 17 LTS for long-term support",
            "compatibility_notes": "Review deprecated APIs and third-party library compatibility",
            "cloud_support": {
                "aws": "Supports Java 11+ in Lambda, ECS, EKS",
                "azure": "Supports Java 11+ in App Service, AKS",
                "gcp": "Supports Java 11+ in App Engine, GKE",
            },
            "security_benefits": [
                "Enhanced TLS support",
                "Improved cryptographic algorithms",
                "Regular security updates",
            ],
        },
    },
    {
        "requirement_type": "dotnet_versions",
        "description": "Minimum supported .NET versions for modern cloud deployment",
        "mandatory": True,
        "supported_versions": {
            "dotnet_core": "3.1+",
            "dotnet_framework": "4.8+",
            "asp_net_core": "3.1+",
            "entity_framework": "6.0+",
            "nuget": "5.0+",
        },
        "requirement_details": {
            "rationale": ".NET Core provides better cloud compatibility and performance",
            "migration_path": "Migrate from .NET Framework to .NET Core/.NET 5+",
            "compatibility_notes": "Review Windows-specific dependencies",
            "cloud_support": {
                "azure": "Native support in App Service, AKS, Service Fabric",
                "aws": "Supports .NET Core in Lambda, ECS, EKS",
                "gcp": "Supports .NET Core in App Engine, GKE",
            },
            "performance_benefits": [
                "Cross-platform deployment",
                "Improved startup times",
                "Lower memory footprint",
            ],
        },
    },
    {
        "requirement_type": "python_versions",
        "description": "Minimum supported Python versions with security updates",
        "mandatory": True,
        "supported_versions": {
            "python": "3.8+",
            "django": "3.2+",
            "flask": "2.0+",
            "fastapi": "0.65+",
            "pip": "21.0+",
        },
        "requirement_details": {
            "rationale": "Python 3.7 and below are end-of-life and lack security updates",
            "migration_path": "Upgrade to Python 3.8+ for continued security support",
            "compatibility_notes": "Review deprecated features and library compatibility",
            "cloud_support": {
                "aws": "Supports Python 3.8+ in Lambda, ECS, EC2",
                "azure": "Supports Python 3.8+ in Functions, App Service",
                "gcp": "Supports Python 3.8+ in Cloud Functions, App Engine",
            },
            "language_features": [
                "Assignment expressions (walrus operator)",
                "Positional-only parameters",
                "Improved type hints",
            ],
        },
    },
    {
        "requirement_type": "nodejs_versions",
        "description": "Minimum supported Node.js versions with LTS support",
        "mandatory": True,
        "supported_versions": {
            "nodejs": "14+",
            "npm": "6.0+",
            "express": "4.17+",
            "react": "17.0+",
            "angular": "12.0+",
        },
        "requirement_details": {
            "rationale": "Node.js 14+ provides LTS support and enhanced security",
            "migration_path": "Upgrade to Node.js 14 LTS or 16 LTS",
            "compatibility_notes": "Review npm package dependencies and security vulnerabilities",
            "cloud_support": {
                "aws": "Supports Node.js 14+ in Lambda, ECS, Elastic Beanstalk",
                "azure": "Supports Node.js 14+ in Functions, App Service",
                "gcp": "Supports Node.js 14+ in Cloud Functions, App Engine",
            },
            "performance_improvements": [
                "V8 engine updates",
                "Enhanced ES modules support",
                "Improved diagnostic reporting",
            ],
        },
    },
]

# === SECURITY AND COMPLIANCE STANDARDS ===

SECURITY_STANDARDS = [
    {
        "requirement_type": "authentication",
        "description": "Modern authentication and authorization patterns",
        "mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "required_patterns": ["OAuth2", "OIDC", "SAML"],
            "deprecated_patterns": [
                "Basic Auth",
                "Custom Sessions",
                "Plain text passwords",
            ],
            "required_features": [
                "Multi-Factor Authentication (MFA)",
                "Single Sign-On (SSO) Integration",
                "Role-Based Access Control (RBAC)",
                "Session management with timeout",
            ],
            "implementation_guidelines": {
                "token_storage": "Secure, httpOnly cookies or secure token storage",
                "token_expiration": "Access tokens: 15-60 minutes, Refresh tokens: 7-30 days",
                "password_policy": "Minimum 12 characters, complexity requirements",
            },
            "compliance_frameworks": ["SOC2", "ISO27001", "GDPR", "HIPAA"],
        },
    },
    {
        "requirement_type": "data_encryption",
        "description": "Data encryption at rest and in transit requirements",
        "mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "encryption_in_transit": {
                "minimum_tls": "TLS 1.2+",
                "preferred_tls": "TLS 1.3",
                "certificate_management": "Automated certificate rotation",
                "cipher_suites": "Modern, secure cipher suites only",
            },
            "encryption_at_rest": {
                "algorithm": "AES-256",
                "key_management": "Cloud provider KMS or dedicated HSM",
                "database_encryption": "Transparent Data Encryption (TDE)",
                "file_system_encryption": "Full disk encryption",
            },
            "key_management": {
                "rotation_policy": "Automatic key rotation every 90 days",
                "access_control": "Principle of least privilege",
                "audit_logging": "All key access logged and monitored",
            },
            "compliance_requirements": ["PCI-DSS", "SOC2", "GDPR", "HIPAA"],
        },
    },
    {
        "requirement_type": "api_security",
        "description": "API security standards and best practices",
        "mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "authentication": "OAuth2 Bearer tokens or API keys",
            "authorization": "Fine-grained permissions and scoping",
            "rate_limiting": "Per-client rate limiting and throttling",
            "input_validation": "Comprehensive input sanitization and validation",
            "security_headers": [
                "Content-Security-Policy",
                "X-Frame-Options",
                "X-Content-Type-Options",
                "Strict-Transport-Security",
            ],
            "monitoring": {
                "logging": "All API calls logged with request/response details",
                "alerting": "Anomaly detection and security event alerting",
                "metrics": "Response times, error rates, security events",
            },
            "vulnerability_management": "Regular security scanning and penetration testing",
        },
    },
]

# === ARCHITECTURE PATTERN STANDARDS ===

ARCHITECTURE_STANDARDS = [
    {
        "requirement_type": "containerization",
        "description": "Container readiness for cloud deployment",
        "mandatory": False,
        "supported_versions": {
            "docker": "20.10+",
            "kubernetes": "1.20+",
            "helm": "3.0+",
            "istio": "1.10+",
        },
        "requirement_details": {
            "container_requirements": {
                "base_images": "Official, minimal, and regularly updated base images",
                "security_scanning": "Container image vulnerability scanning",
                "multi_stage_builds": "Use multi-stage builds to minimize image size",
                "non_root_user": "Run containers as non-root user",
            },
            "orchestration": {
                "preferred": "Kubernetes",
                "alternatives": [
                    "Docker Swarm",
                    "AWS ECS",
                    "Azure Container Instances",
                ],
                "service_mesh": "Consider Istio for complex microservices",
            },
            "best_practices": [
                "Health checks and readiness probes",
                "Resource limits and requests",
                "Horizontal pod autoscaling",
                "Rolling updates and rollback capability",
            ],
            "monitoring": "Container metrics, logs aggregation, distributed tracing",
        },
    },
    {
        "requirement_type": "api_design",
        "description": "RESTful API design standards and documentation",
        "mandatory": True,
        "supported_versions": {
            "openapi": "3.0+",
            "swagger": "3.0+",
            "postman": "9.0+",
            "rest_maturity": "Level 2+",
        },
        "requirement_details": {
            "design_principles": {
                "rest_compliance": "Follow REST architectural constraints",
                "resource_naming": "Consistent, hierarchical resource naming",
                "http_methods": "Proper use of GET, POST, PUT, DELETE, PATCH",
                "status_codes": "Appropriate HTTP status codes",
            },
            "documentation": {
                "openapi_spec": "Complete OpenAPI 3.0+ specification",
                "interactive_docs": "Swagger UI or similar documentation interface",
                "examples": "Comprehensive request/response examples",
                "sdk_generation": "Auto-generated client SDKs",
            },
            "versioning": {
                "strategy": "URL path versioning (/api/v1/) or header versioning",
                "backward_compatibility": "Maintain compatibility for at least 2 versions",
                "deprecation_policy": "6-month deprecation notice for breaking changes",
            },
            "error_handling": "Consistent error response format with proper codes",
        },
    },
    {
        "requirement_type": "microservices_architecture",
        "description": "Microservices design patterns and practices",
        "mandatory": False,
        "supported_versions": None,
        "requirement_details": {
            "service_boundaries": {
                "domain_driven_design": "Services aligned with business domains",
                "single_responsibility": "Each service has a single, well-defined purpose",
                "data_ownership": "Each service owns its data and database",
            },
            "communication": {
                "synchronous": "REST APIs or gRPC for real-time communication",
                "asynchronous": "Message queues or event streams for loose coupling",
                "service_discovery": "Dynamic service discovery and load balancing",
            },
            "resilience_patterns": [
                "Circuit breakers for fault tolerance",
                "Retry mechanisms with exponential backoff",
                "Bulkhead pattern for resource isolation",
                "Timeout configurations",
            ],
            "observability": {
                "distributed_tracing": "End-to-end request tracing across services",
                "centralized_logging": "Structured logging with correlation IDs",
                "metrics_collection": "Service-level and business metrics",
            },
        },
    },
]

# === CLOUD-NATIVE STANDARDS ===

CLOUD_NATIVE_STANDARDS = [
    {
        "requirement_type": "observability",
        "description": "Comprehensive monitoring, logging, and tracing capabilities",
        "mandatory": True,
        "supported_versions": {
            "prometheus": "2.30+",
            "grafana": "8.0+",
            "jaeger": "1.25+",
            "elk_stack": "7.10+",
        },
        "requirement_details": {
            "monitoring": {
                "metrics_collection": "Application and infrastructure metrics",
                "alerting": "Proactive alerting based on SLA thresholds",
                "dashboards": "Real-time dashboards for system health",
                "tools": [
                    "Prometheus",
                    "CloudWatch",
                    "Application Insights",
                    "Datadog",
                ],
            },
            "logging": {
                "structured_logging": "JSON-formatted logs with consistent schema",
                "centralized_collection": "Centralized log aggregation and search",
                "retention_policy": "Log retention based on compliance requirements",
                "tools": ["ELK Stack", "Splunk", "CloudWatch Logs", "Azure Monitor"],
            },
            "tracing": {
                "distributed_tracing": "End-to-end request tracing across services",
                "performance_analysis": "Identify bottlenecks and latency issues",
                "error_tracking": "Detailed error context and stack traces",
                "tools": [
                    "Jaeger",
                    "Zipkin",
                    "AWS X-Ray",
                    "Azure Application Insights",
                ],
            },
            "sla_requirements": {
                "uptime": "99.9% availability",
                "response_time": "95th percentile under 500ms",
                "error_rate": "Less than 1% error rate",
            },
        },
    },
    {
        "requirement_type": "scalability",
        "description": "Horizontal and vertical scaling capabilities",
        "mandatory": False,
        "supported_versions": None,
        "requirement_details": {
            "horizontal_scaling": {
                "auto_scaling": "Automatic scaling based on metrics",
                "load_balancing": "Distributed load across instances",
                "stateless_design": "Stateless application design for easy scaling",
                "session_management": "Externalized session storage",
            },
            "vertical_scaling": {
                "resource_optimization": "Efficient CPU and memory usage",
                "performance_tuning": "Application and database performance optimization",
                "capacity_planning": "Proactive capacity planning based on growth",
            },
            "data_scaling": {
                "database_scaling": "Read replicas, sharding, or distributed databases",
                "caching_strategies": "Multi-level caching (application, database, CDN)",
                "cdn_integration": "Content delivery network for static assets",
            },
            "scaling_triggers": {
                "cpu_utilization": "Scale when CPU > 70% for 5 minutes",
                "memory_utilization": "Scale when memory > 80% for 5 minutes",
                "request_rate": "Scale when request rate > threshold",
                "custom_metrics": "Business-specific scaling triggers",
            },
        },
    },
    {
        "requirement_type": "disaster_recovery",
        "description": "Business continuity and disaster recovery planning",
        "mandatory": True,
        "supported_versions": None,
        "requirement_details": {
            "backup_strategy": {
                "frequency": "Daily automated backups with point-in-time recovery",
                "retention": "30 days for daily, 12 months for monthly backups",
                "testing": "Monthly backup restoration testing",
                "encryption": "Encrypted backups with separate key management",
            },
            "high_availability": {
                "multi_az_deployment": "Deploy across multiple availability zones",
                "failover_automation": "Automatic failover with minimal downtime",
                "health_checks": "Continuous health monitoring and remediation",
                "rto_rpo": "RTO < 4 hours, RPO < 1 hour",
            },
            "geographic_distribution": {
                "multi_region": "Consider multi-region deployment for critical systems",
                "data_replication": "Cross-region data replication for DR",
                "traffic_routing": "DNS-based traffic routing for failover",
            },
            "testing_procedures": {
                "dr_drills": "Quarterly disaster recovery drills",
                "chaos_engineering": "Regular chaos engineering exercises",
                "documentation": "Detailed runbooks and escalation procedures",
            },
        },
    },
]

# === MAIN INITIALIZATION FUNCTIONS ===


async def initialize_assessment_standards(db: AsyncSession, engagement_id: str) -> None:
    """
    Initialize engagement with default architecture standards.

    Args:
        db: Async database session
        engagement_id: UUID of the engagement
    """
    logger.info(f"Initializing assessment standards for engagement {engagement_id}")

    # Check if standards already exist
    existing_standards = await db.execute(
        select(EngagementArchitectureStandard).where(
            EngagementArchitectureStandard.engagement_id == engagement_id
        )
    )

    if existing_standards.first():
        logger.info(
            f"Standards already exist for engagement {engagement_id}, skipping initialization"
        )
        return

    # Combine all standard categories
    all_standards = (
        TECH_VERSION_STANDARDS
        + SECURITY_STANDARDS
        + ARCHITECTURE_STANDARDS
        + CLOUD_NATIVE_STANDARDS
    )

    # Create standard records
    standards_created = 0
    for standard in all_standards:
        try:
            standard_record = EngagementArchitectureStandard(
                engagement_id=engagement_id,
                requirement_type=standard["requirement_type"],
                description=standard["description"],
                mandatory=standard["mandatory"],
                supported_versions=standard.get("supported_versions"),
                requirement_details=standard["requirement_details"],
                created_by="system_init",
            )
            db.add(standard_record)
            standards_created += 1

        except Exception as e:
            logger.error(
                f"Failed to create standard {standard['requirement_type']}: {str(e)}"
            )
            continue

    try:
        await db.commit()
        logger.info(
            f"Successfully created {standards_created} architecture standards for engagement {engagement_id}"
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to commit architecture standards: {str(e)}")
        raise


def get_default_standards() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all default architecture standards organized by category.

    Returns:
        Dictionary with standard categories as keys and lists of standards as values
    """
    return {
        "technology_versions": TECH_VERSION_STANDARDS,
        "security_compliance": SECURITY_STANDARDS,
        "architecture_patterns": ARCHITECTURE_STANDARDS,
        "cloud_native": CLOUD_NATIVE_STANDARDS,
    }


def get_standards_by_type(requirement_type: str) -> Dict[str, Any]:
    """
    Get a specific standard by requirement type.

    Args:
        requirement_type: The type of requirement to retrieve

    Returns:
        Standard definition or None if not found
    """
    all_standards = (
        TECH_VERSION_STANDARDS
        + SECURITY_STANDARDS
        + ARCHITECTURE_STANDARDS
        + CLOUD_NATIVE_STANDARDS
    )

    for standard in all_standards:
        if standard["requirement_type"] == requirement_type:
            return standard

    return None


def validate_technology_compliance(
    technology_stack: Dict[str, str], engagement_standards: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate a technology stack against engagement standards.

    Args:
        technology_stack: Dictionary of technology and version pairs
        engagement_standards: List of engagement architecture standards

    Returns:
        Validation result with compliance status and recommendations
    """
    validation_result = {
        "compliant": True,
        "issues": [],
        "recommendations": [],
        "exceptions_needed": [],
    }

    # Check each technology in the stack
    for tech, version in technology_stack.items():
        # Find matching standard
        matching_standard = None
        for standard in engagement_standards:
            if (
                standard.get("supported_versions")
                and tech in standard["supported_versions"]
            ):
                matching_standard = standard
                break

        if not matching_standard:
            validation_result["recommendations"].append(
                f"No standard defined for {tech}"
            )
            continue

        # Check version compliance
        required_version = matching_standard["supported_versions"][tech]
        if not _is_version_compliant(version, required_version):
            issue = {
                "technology": tech,
                "current_version": version,
                "required_version": required_version,
                "mandatory": matching_standard["mandatory"],
            }

            if matching_standard["mandatory"]:
                validation_result["compliant"] = False
                validation_result["issues"].append(issue)
            else:
                validation_result["recommendations"].append(
                    f"Consider upgrading {tech} from {version} to {required_version}"
                )

    return validation_result


def _is_version_compliant(current_version: str, required_version: str) -> bool:
    """
    Check if current version meets the requirement.

    Args:
        current_version: Current version string
        required_version: Required version string (may include + for minimum)

    Returns:
        True if compliant, False otherwise
    """
    # Simple version comparison - can be enhanced with proper semver parsing
    if required_version.endswith("+"):
        min_version = required_version[:-1]
        # Basic string comparison - in production, use proper version parsing
        return current_version >= min_version
    else:
        return current_version == required_version
