"""
Additional Flow Configurations
MFO-049 through MFO-054: Planning, Execution, Modernize, FinOps, Observability, Decommission flows

Contains configurations for all remaining flow types.
"""

from app.services.flow_type_registry import (FlowCapabilities, FlowTypeConfig,
                                             PhaseConfig, RetryConfig)


def get_planning_flow_config() -> FlowTypeConfig:
    """
    MFO-049: Planning Flow Configuration

    Wave planning, resource planning, and timeline optimization
    """
    default_retry = RetryConfig(max_attempts=3, initial_delay_seconds=2.0)

    phases = [
        PhaseConfig(
            name="wave_planning",
            display_name="Wave Planning",
            description="Plan migration waves based on dependencies and constraints",
            required_inputs=["assessment_results", "business_constraints"],
            optional_inputs=[
                "dependency_graph",
                "blackout_windows",
                "priority_overrides",
            ],
            validators=["wave_validation", "dependency_validation"],
            pre_handlers=["wave_analysis"],
            post_handlers=["wave_optimization"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=3600,  # 60 minutes
            metadata={
                "optimization_algorithm": "constraint_satisfaction",
                "max_waves": 10,
                "parallel_execution": True,
            },
        ),
        PhaseConfig(
            name="resource_planning",
            display_name="Resource Planning",
            description="Plan resource allocation and capacity requirements",
            required_inputs=["wave_plan", "resource_constraints"],
            optional_inputs=[
                "skill_matrix",
                "vendor_availability",
                "budget_allocation",
            ],
            validators=["resource_validation", "capacity_validation"],
            pre_handlers=["resource_analysis"],
            post_handlers=["resource_optimization"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "resource_types": ["human", "infrastructure", "licensing", "tools"],
                "optimization_goals": ["cost", "duration", "risk"],
            },
        ),
        PhaseConfig(
            name="timeline_optimization",
            display_name="Timeline Optimization",
            description="Optimize migration timeline for efficiency",
            required_inputs=["wave_plan", "resource_plan"],
            optional_inputs=[
                "critical_path",
                "buffer_requirements",
                "acceleration_options",
            ],
            validators=["timeline_validation", "feasibility_check"],
            pre_handlers=["critical_path_analysis"],
            post_handlers=["timeline_finalization"],
            completion_handler="planning_completion",
            can_pause=True,
            can_skip=True,
            retry_config=default_retry,
            timeout_seconds=1800,  # 30 minutes
            metadata={
                "optimization_method": "critical_path_method",
                "buffer_calculation": "monte_carlo",
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_iterations=True,
        max_iterations=5,
        supports_scheduling=True,
        supports_checkpointing=True,
        required_permissions=["planning.read", "planning.write", "planning.execute"],
    )

    return FlowTypeConfig(
        name="planning",
        display_name="Planning Flow",
        description="Migration wave and resource planning with timeline optimization",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "optimization_enabled": True,
            "dependency_tracking": True,
            "resource_constraints": True,
            "scenario_planning": True,
            "monte_carlo_simulations": 1000,
        },
        initialization_handler="planning_initialization",
        finalization_handler="planning_finalization",
        error_handler="planning_error_handler",
        metadata={
            "category": "orchestration",
            "complexity": "high",
            "prerequisite_flows": ["assessment"],
        },
        tags=["planning", "optimization", "resource_management", "scheduling"],
    )


def get_execution_flow_config() -> FlowTypeConfig:
    """
    MFO-050: Execution Flow Configuration

    Pre-migration validation, migration execution, post-migration validation
    """
    default_retry = RetryConfig(
        max_attempts=5, initial_delay_seconds=5.0, max_delay_seconds=300.0
    )

    phases = [
        PhaseConfig(
            name="pre_migration_validation",
            display_name="Pre-Migration Validation",
            description="Validate readiness before migration execution",
            required_inputs=["migration_plan", "target_environment"],
            optional_inputs=[
                "validation_checklist",
                "rollback_plan",
                "communication_plan",
            ],
            validators=["pre_migration_validation", "environment_validation"],
            pre_handlers=["environment_preparation"],
            post_handlers=["validation_report"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=1800,  # 30 minutes
            metadata={
                "validation_types": [
                    "connectivity",
                    "permissions",
                    "capacity",
                    "compatibility",
                ],
                "go_no_go_decision": True,
            },
        ),
        PhaseConfig(
            name="migration_execution",
            display_name="Migration Execution",
            description="Execute the actual migration process",
            required_inputs=["validated_plan", "execution_config"],
            optional_inputs=[
                "parallel_streams",
                "throttling_config",
                "monitoring_config",
            ],
            validators=["execution_validation", "progress_validation"],
            pre_handlers=["execution_preparation"],
            post_handlers=["execution_verification"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=10800,  # 180 minutes
            metadata={
                "execution_modes": ["big_bang", "phased", "parallel", "blue_green"],
                "rollback_enabled": True,
                "real_time_monitoring": True,
            },
        ),
        PhaseConfig(
            name="post_migration_validation",
            display_name="Post-Migration Validation",
            description="Validate migration success and functionality",
            required_inputs=["migration_results", "validation_criteria"],
            optional_inputs=[
                "performance_benchmarks",
                "user_acceptance_tests",
                "integration_tests",
            ],
            validators=["post_migration_validation", "success_criteria_validation"],
            pre_handlers=["validation_preparation"],
            post_handlers=["validation_summary"],
            completion_handler="migration_completion",
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "validation_levels": [
                    "infrastructure",
                    "application",
                    "data",
                    "integration",
                ],
                "automated_testing": True,
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_branching=True,
        supports_iterations=False,
        supports_scheduling=True,
        supports_parallel_phases=True,
        supports_checkpointing=True,
        required_permissions=[
            "execution.read",
            "execution.write",
            "execution.execute",
            "execution.rollback",
        ],
    )

    return FlowTypeConfig(
        name="execution",
        display_name="Execution Flow",
        description="Migration execution with validation and rollback capabilities",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "rollback_enabled": True,
            "real_time_monitoring": True,
            "automated_validation": True,
            "parallel_execution": True,
            "failure_threshold": 0.05,
        },
        initialization_handler="execution_initialization",
        finalization_handler="execution_finalization",
        error_handler="execution_error_handler",
        metadata={
            "category": "operational",
            "complexity": "critical",
            "prerequisite_flows": ["planning"],
            "requires_approval": True,
        },
        tags=["execution", "migration", "validation", "rollback", "critical"],
    )


def get_modernize_flow_config() -> FlowTypeConfig:
    """
    MFO-051: Modernize Flow Configuration

    Assessment, architecture redesign, implementation planning
    """
    default_retry = RetryConfig(max_attempts=3, initial_delay_seconds=2.0)

    phases = [
        PhaseConfig(
            name="modernization_assessment",
            display_name="Modernization Assessment",
            description="Assess modernization opportunities and readiness",
            required_inputs=["current_architecture", "modernization_goals"],
            optional_inputs=[
                "technology_trends",
                "skill_assessment",
                "budget_constraints",
            ],
            validators=["modernization_validation", "goal_alignment_validation"],
            pre_handlers=["modernization_analysis"],
            post_handlers=["opportunity_identification"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=3600,  # 60 minutes
            metadata={
                "assessment_areas": [
                    "containerization",
                    "microservices",
                    "serverless",
                    "cloud_native",
                ],
                "maturity_model": "cloud_native_maturity_model_v2",
            },
        ),
        PhaseConfig(
            name="architecture_redesign",
            display_name="Architecture Redesign",
            description="Redesign architecture for cloud-native patterns",
            required_inputs=["modernization_opportunities", "design_principles"],
            optional_inputs=[
                "reference_architectures",
                "pattern_library",
                "constraints",
            ],
            validators=["architecture_validation", "pattern_validation"],
            pre_handlers=["design_preparation"],
            post_handlers=["design_review"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=5400,  # 90 minutes
            metadata={
                "design_patterns": [
                    "microservices",
                    "event_driven",
                    "api_first",
                    "twelve_factor",
                ],
                "architecture_tools": ["diagrams", "models", "prototypes"],
            },
        ),
        PhaseConfig(
            name="implementation_planning",
            display_name="Implementation Planning",
            description="Plan modernization implementation approach",
            required_inputs=["new_architecture", "implementation_constraints"],
            optional_inputs=["pilot_selection", "training_plan", "transition_approach"],
            validators=["implementation_validation", "feasibility_validation"],
            pre_handlers=["implementation_analysis"],
            post_handlers=["roadmap_creation"],
            completion_handler="modernization_completion",
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "implementation_approaches": [
                    "rehost",
                    "replatform",
                    "refactor",
                    "rebuild",
                ],
                "pilot_program": True,
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=False,
        supports_iterations=True,
        max_iterations=3,
        supports_scheduling=True,
        supports_checkpointing=True,
        required_permissions=["modernize.read", "modernize.write", "modernize.design"],
    )

    return FlowTypeConfig(
        name="modernize",
        display_name="Modernize Flow",
        description="Application modernization and cloud-native transformation",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "cloud_native_patterns": True,
            "microservices_assessment": True,
            "containerization_analysis": True,
            "ai_recommendations": True,
        },
        initialization_handler="modernize_initialization",
        finalization_handler="modernize_finalization",
        error_handler="modernize_error_handler",
        metadata={
            "category": "transformation",
            "complexity": "high",
            "prerequisite_flows": ["assessment"],
        },
        tags=["modernization", "cloud_native", "transformation", "architecture"],
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


def get_decommission_flow_config() -> FlowTypeConfig:
    """
    MFO-054: Decommission Flow Configuration

    Planning, data migration, system shutdown
    """
    default_retry = RetryConfig(
        max_attempts=5, initial_delay_seconds=10.0, max_delay_seconds=600.0
    )

    phases = [
        PhaseConfig(
            name="decommission_planning",
            display_name="Decommission Planning",
            description="Plan safe system decommissioning approach",
            required_inputs=["decommission_targets", "business_requirements"],
            optional_inputs=[
                "dependency_analysis",
                "risk_assessment",
                "compliance_requirements",
            ],
            validators=["decommission_validation", "dependency_validation"],
            pre_handlers=["impact_analysis"],
            post_handlers=["plan_approval"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "planning_aspects": [
                    "data",
                    "dependencies",
                    "compliance",
                    "communication",
                ],
                "approval_required": True,
                "rollback_planning": True,
            },
        ),
        PhaseConfig(
            name="data_migration",
            display_name="Data Migration",
            description="Migrate and archive critical data before decommission",
            required_inputs=["decommission_plan", "data_requirements"],
            optional_inputs=[
                "archive_policies",
                "retention_requirements",
                "encryption_keys",
            ],
            validators=["data_migration_validation", "integrity_validation"],
            pre_handlers=["data_inventory"],
            post_handlers=["migration_verification"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=7200,  # 120 minutes
            metadata={
                "migration_methods": ["backup", "archive", "transfer", "export"],
                "data_validation": True,
                "encryption_required": True,
            },
        ),
        PhaseConfig(
            name="system_shutdown",
            display_name="System Shutdown",
            description="Safely shutdown and decommission systems",
            required_inputs=["migrated_data", "shutdown_procedures"],
            optional_inputs=[
                "verification_checklist",
                "stakeholder_signoff",
                "audit_requirements",
            ],
            validators=["shutdown_validation", "completion_validation"],
            pre_handlers=["final_backup"],
            post_handlers=["decommission_verification"],
            completion_handler="decommission_completion",
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=3600,  # 60 minutes
            metadata={
                "shutdown_sequence": [
                    "connections",
                    "applications",
                    "databases",
                    "infrastructure",
                ],
                "verification_required": True,
                "audit_trail": True,
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_branching=False,
        supports_iterations=False,
        supports_scheduling=True,
        supports_checkpointing=True,
        required_permissions=[
            "decommission.read",
            "decommission.write",
            "decommission.execute",
            "decommission.approve",
        ],
    )

    return FlowTypeConfig(
        name="decommission",
        display_name="Decommission Flow",
        description="Safe system decommissioning with data preservation",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "data_backup_required": True,
            "approval_workflow": True,
            "audit_trail": True,
            "compliance_checks": True,
            "point_of_no_return_warning": True,
        },
        initialization_handler="decommission_initialization",
        finalization_handler="decommission_finalization",
        error_handler="decommission_error_handler",
        metadata={
            "category": "lifecycle",
            "complexity": "high",
            "irreversible": True,
            "requires_approval": True,
            "compliance_critical": True,
        },
        tags=["decommission", "lifecycle", "data_migration", "compliance", "critical"],
    )
