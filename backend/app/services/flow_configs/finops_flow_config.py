"""
FinOps Flow Configuration
MFO-052: Cost analysis, optimization identification, budget planning
"""

from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
    PhaseConfig,
    RetryConfig,
)


def get_finops_flow_config() -> FlowTypeConfig:
    """
    MFO-052: FinOps Flow Configuration

    Cost analysis, optimization identification, budget planning
    """
    default_retry = RetryConfig(max_attempts=3, initial_delay_seconds=2.0)

    phases = [
        PhaseConfig(
            name="cost_analysis",
            display_name="Cost Analysis",
            description="Analyze current and projected cloud costs",
            required_inputs=["current_costs", "usage_patterns"],
            optional_inputs=[
                "historical_trends",
                "forecasting_models",
                "seasonality_data",
            ],
            validators=["cost_validation", "data_completeness_validation"],
            pre_handlers=["cost_data_collection"],
            post_handlers=["cost_categorization"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "analysis_dimensions": ["service", "environment", "team", "project"],
                "cost_allocation": True,
                "anomaly_detection": True,
            },
        ),
        PhaseConfig(
            name="optimization_identification",
            display_name="Optimization Identification",
            description="Identify cost optimization opportunities",
            required_inputs=["cost_analysis", "optimization_rules"],
            optional_inputs=["best_practices", "benchmark_data", "risk_tolerance"],
            validators=["optimization_validation", "savings_validation"],
            pre_handlers=["optimization_scanning"],
            post_handlers=["opportunity_ranking"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=3600,  # 60 minutes
            metadata={
                "optimization_areas": [
                    "rightsizing",
                    "reserved_instances",
                    "spot_instances",
                    "waste_elimination",
                ],
                "ai_recommendations": True,
                "impact_analysis": True,
            },
        ),
        PhaseConfig(
            name="budget_planning",
            display_name="Budget Planning",
            description="Plan budgets and implement cost controls",
            required_inputs=["optimization_opportunities", "business_goals"],
            optional_inputs=[
                "growth_projections",
                "budget_constraints",
                "approval_workflows",
            ],
            validators=["budget_validation", "control_validation"],
            pre_handlers=["budget_modeling"],
            post_handlers=["control_implementation"],
            completion_handler="finops_completion",
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=1800,  # 30 minutes
            metadata={
                "budget_types": ["annual", "quarterly", "project", "team"],
                "alerting_enabled": True,
                "automated_controls": True,
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=False,
        supports_iterations=True,
        max_iterations=10,
        supports_scheduling=True,
        supports_checkpointing=True,
        required_permissions=["finops.read", "finops.write", "finops.budget"],
    )

    return FlowTypeConfig(
        name="finops",
        display_name="FinOps Flow",
        description="Financial operations and cloud cost optimization",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "real_time_cost_tracking": True,
            "automated_optimization": True,
            "budget_alerts": True,
            "multi_cloud_support": True,
            "showback_enabled": True,
        },
        initialization_handler="finops_initialization",
        finalization_handler="finops_finalization",
        error_handler="finops_error_handler",
        metadata={
            "category": "financial",
            "complexity": "medium",
            "recurring": True,
            "frequency": "monthly",
        },
        tags=["finops", "cost_optimization", "budgeting", "financial"],
    )
