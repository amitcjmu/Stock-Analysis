"""
Architecture Pattern Standards for Assessment Flow
Containerization, API design, and microservices patterns.
"""

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
