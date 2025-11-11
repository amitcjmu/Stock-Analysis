"""
Observability Flow Configuration
MFO-053: Monitoring setup, logging configuration, alerting setup
"""

from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
    PhaseConfig,
    RetryConfig,
)


def get_observability_flow_config() -> FlowTypeConfig:
    """
    MFO-053: Observability Flow Configuration

    Monitoring setup, logging configuration, alerting setup
    """
    default_retry = RetryConfig(max_attempts=3, initial_delay_seconds=2.0)

    phases = [
        PhaseConfig(
            name="monitoring_setup",
            display_name="Monitoring Setup",
            description="Set up comprehensive monitoring infrastructure",
            required_inputs=["target_environment", "monitoring_requirements"],
            optional_inputs=[
                "sla_requirements",
                "custom_metrics",
                "integration_points",
            ],
            validators=["monitoring_validation", "coverage_validation"],
            pre_handlers=["monitoring_design"],
            post_handlers=["monitoring_verification"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=3600,  # 60 minutes
            metadata={
                "monitoring_layers": [
                    "infrastructure",
                    "application",
                    "business",
                    "security",
                ],
                "metrics_types": ["system", "application", "custom", "synthetic"],
                "collection_methods": ["agent", "agentless", "api", "logs"],
            },
        ),
        PhaseConfig(
            name="logging_configuration",
            display_name="Logging Configuration",
            description="Configure centralized logging and log aggregation",
            required_inputs=["monitoring_infrastructure", "logging_requirements"],
            optional_inputs=[
                "retention_policies",
                "compliance_requirements",
                "search_patterns",
            ],
            validators=["logging_validation", "retention_validation"],
            pre_handlers=["logging_architecture"],
            post_handlers=["logging_testing"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "log_types": ["application", "system", "security", "audit"],
                "aggregation_tools": ["elk", "splunk", "cloudwatch", "datadog"],
                "real_time_streaming": True,
            },
        ),
        PhaseConfig(
            name="alerting_setup",
            display_name="Alerting Setup",
            description="Configure alerting rules and notification channels",
            required_inputs=["monitoring_infrastructure", "alerting_rules"],
            optional_inputs=[
                "escalation_policies",
                "maintenance_windows",
                "correlation_rules",
            ],
            validators=["alerting_validation", "notification_validation"],
            pre_handlers=["alerting_design"],
            post_handlers=["alerting_testing"],
            completion_handler="observability_completion",
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=1800,  # 30 minutes
            metadata={
                "alert_types": ["threshold", "anomaly", "predictive", "composite"],
                "notification_channels": ["email", "sms", "slack", "pagerduty"],
                "intelligent_routing": True,
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_iterations=True,
        supports_scheduling=True,
        supports_checkpointing=True,
        required_permissions=[
            "observability.read",
            "observability.write",
            "observability.configure",
        ],
    )

    return FlowTypeConfig(
        name="observability",
        display_name="Observability Flow",
        description="Comprehensive monitoring, logging, and alerting setup",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "real_time_monitoring": True,
            "distributed_tracing": True,
            "automated_alerting": True,
            "aiops_enabled": True,
            "chaos_engineering": False,
        },
        initialization_handler="observability_initialization",
        finalization_handler="observability_finalization",
        error_handler="observability_error_handler",
        metadata={
            "category": "operational",
            "complexity": "medium",
            "ongoing_maintenance": True,
        },
        tags=["observability", "monitoring", "logging", "alerting", "operations"],
    )
