"""
Auto Enrichment Phase Configuration

Configuration for the auto enrichment phase of the Collection flow.
Runs enrichment BEFORE gap analysis to reduce questionnaire burden.

**CRITICAL TIMING**: Per BULK_UPLOAD_ENRICHMENT_ARCHITECTURE_ANALYSIS.md Part 6.1:
- This phase MUST run BEFORE gap_analysis
- Populates 7 enrichment tables (compliance, licenses, vulnerabilities, etc.)
- Updates business_context with enriched data
- Enables gap analysis to see enriched fields and reduce questions by 50-80%

**ADR COMPLIANCE**:
- ADR-015: Uses TenantScopedAgentPool for persistent agents
- ADR-024: Uses TenantMemoryManager for agent learning (CrewAI memory=False)
- ADR-028: All LLM calls use multi_model_service.generate_response()
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_auto_enrichment_phase() -> PhaseConfig:
    """
    Get the Auto Enrichment phase configuration

    This phase runs BEFORE gap_analysis to:
    1. Populate 7 enrichment tables from uploaded CSV data
    2. Enrich assets using AI agents (compliance, licenses, vulnerabilities, etc.)
    3. Update business_context with enriched data
    4. Enable gap analysis to see enriched fields and reduce questions

    **Performance Target**: 100 assets < 5 minutes (Phase 2.3 optimization)

    **Enrichment Tables** (7 total):
    1. asset_compliance_flags - Compliance requirements, data classification
    2. asset_licenses - Software licensing information
    3. asset_vulnerabilities - Security vulnerabilities (CVE tracking)
    4. asset_resilience - HA/DR configuration
    5. asset_dependencies - Asset relationship mapping
    6. asset_product_links - Vendor product catalog matching
    7. asset_field_conflicts - Multi-source conflict resolution

    **Expected Result**: Gap analysis generates 50-80% fewer questions
    """

    # Define retry configuration
    enrichment_retry = RetryConfig(
        max_attempts=2,  # Enrichment is optional - don't over-retry
        initial_delay_seconds=30.0,  # Give agents time to complete
        backoff_multiplier=1.5,
        max_delay_seconds=60.0,
    )

    return PhaseConfig(
        name="auto_enrichment",
        display_name="Auto Enrichment",
        description="Enrich assets with AI-powered analysis before gap analysis",
        required_inputs=["asset_ids"],  # From asset_selection phase
        optional_inputs=[
            "enrichment_config",
            "skip_enrichment_types",
            "enrichment_timeout",
        ],
        validators=["enrichment_validation"],
        pre_handlers=["enrichment_preparation"],
        post_handlers=["enrichment_summary"],
        requires_user_input=False,  # Automatic - no user interaction needed
        crew_config={
            "crew_type": "auto_enrichment_crew",
            "crew_factory": "create_auto_enrichment_crew",
            "input_mapping": {
                "asset_ids": "state.selected_asset_ids",
                "enrichment_config": "enrichment_config",
                "skip_enrichment_types": "skip_enrichment_types",
                "context": {
                    "client_account_id": "client_account_id",
                    "engagement_id": "engagement_id",
                    "automation_tier": "state.automation_tier",
                },
            },
            "output_mapping": {
                "enrichment_results": "crew_results.enrichment_results",
                "enriched_asset_count": "crew_results.enriched_asset_count",
                "enrichment_types_completed": "crew_results.enrichment_types_completed",
                "elapsed_time_seconds": "crew_results.elapsed_time_seconds",
                "batches_processed": "crew_results.batches_processed",
                "assets_per_minute": "crew_results.assets_per_minute",
                "readiness_recalculated": "crew_results.readiness_recalculated",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 600,  # 10 minutes for 100 assets
                "temperature": 0.1,  # Very conservative for enrichment
                "max_iterations": 1,
                "allow_delegation": True,  # Enable agent collaboration
                "enable_memory": False,  # Per ADR-024: Use TenantMemoryManager
                "enable_caching": True,  # Performance optimization
                "enable_parallel": True,  # Parallel batch processing
                "conservative_mode": True,
            },
            "llm_config": {
                "temperature": 0.1,  # Conservative for factual enrichment
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
            "validation_mapping": {
                "required_fields": [
                    "enrichment_results",
                    "enriched_asset_count",
                    "elapsed_time_seconds",
                ],
                "success_criteria": {
                    "enriched_asset_count": {"min": 0},  # Some enrichment is optional
                    "elapsed_time_seconds": {"max": 600},  # 10 minute timeout
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_batch_processing": True,
                "batch_size": 10,  # Per Phase 2.3 optimization
                "concurrent_batches": 3,  # Backpressure control
                "rate_limit_batches_per_minute": 10,
            },
        },
        can_pause=True,
        can_skip=True,  # CRITICAL: Can skip if AUTO_ENRICHMENT_ENABLED=False
        retry_config=enrichment_retry,
        timeout_seconds=600,  # 10 minutes for 100 assets
        metadata={
            "enrichment_tables": [
                "asset_compliance_flags",
                "asset_licenses",
                "asset_vulnerabilities",
                "asset_resilience",
                "asset_dependencies",
                "asset_product_links",
                "asset_field_conflicts",
            ],
            "performance_target": "100_assets_in_5_minutes",
            "phase_2_3_optimization": True,
            "backpressure_controls": True,
            "ai_powered": True,
            "adr_015_compliant": True,  # TenantScopedAgentPool
            "adr_024_compliant": True,  # TenantMemoryManager
            "adr_028_compliant": True,  # multi_model_service tracking
            "reduces_questionnaire_burden": "50_to_80_percent",
            "feature_flag": "AUTO_ENRICHMENT_ENABLED",
        },
    )
