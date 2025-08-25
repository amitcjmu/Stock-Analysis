"""
Cloud-Native Standards for Assessment Flow
Observability, scalability, and disaster recovery capabilities.
"""

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
