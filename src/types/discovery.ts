// Flow identifier interface
export interface FlowIdentifier {
  flowId: string;
}

export interface FlowState {
  flow_id: string; // Primary identifier
  current_phase: string;
  next_phase: string;
  previous_phase: string;
  phase_completion: Record<string, boolean>;
  phase_data: Record<string, any>;
  crew_completion_status: Record<string, boolean>;
  agent_insights: Record<string, any>;
  agent_learning: Record<string, any>;
  agent_feedback: Record<string, any>;
  agent_clarifications: Record<string, any>;
  agent_recommendations: Record<string, any>;
  agent_warnings: Record<string, any>;
  agent_errors: Record<string, any>;
  agent_progress: Record<string, any>;
  agent_status: Record<string, any>;
  agent_memory: Record<string, any>;
  agent_context: Record<string, any>;
  agent_configuration: Record<string, any>;
  agent_orchestration: Record<string, any>;
  agent_monitoring: Record<string, any>;
  agent_metrics: Record<string, any>;
  agent_logs: Record<string, any>;
  agent_events: Record<string, any>;
  agent_tasks: Record<string, any>;
  agent_results: Record<string, any>;
  agent_artifacts: Record<string, any>;
  agent_dependencies: Record<string, any>;
  agent_relationships: Record<string, any>;
  agent_patterns: Record<string, any>;
  agent_decisions: Record<string, any>;
  agent_validations: Record<string, any>;
  agent_transformations: Record<string, any>;
  agent_optimizations: Record<string, any>;
  agent_suggestions: Record<string, any>;
  agent_improvements: Record<string, any>;
  agent_enhancements: Record<string, any>;
  agent_refinements: Record<string, any>;
  agent_adjustments: Record<string, any>;
  agent_modifications: Record<string, any>;
  agent_updates: Record<string, any>;
  agent_changes: Record<string, any>;
  agent_revisions: Record<string, any>;
  agent_versions: Record<string, any>;
  agent_history: Record<string, any>;
  agent_timeline: Record<string, any>;
  agent_schedule: Record<string, any>;
  agent_planning: Record<string, any>;
  agent_execution: Record<string, any>;
  agent_monitoring_data: Record<string, any>;
  agent_analysis: Record<string, any>;
  agent_evaluation: Record<string, any>;
  agent_assessment: Record<string, any>;
  agent_reporting: Record<string, any>;
  agent_documentation: Record<string, any>;
  agent_communication: Record<string, any>;
  agent_collaboration: Record<string, any>;
  agent_coordination: Record<string, any>;
  agent_integration: Record<string, any>;
  agent_automation: Record<string, any>;
  agent_intelligence: Record<string, any>;
  agent_learning_data: Record<string, any>;
  agent_knowledge: Record<string, any>;
  agent_expertise: Record<string, any>;
  agent_capabilities: Record<string, any>;
  agent_skills: Record<string, any>;
  agent_competencies: Record<string, any>;
  agent_proficiencies: Record<string, any>;
  agent_qualifications: Record<string, any>;
  agent_certifications: Record<string, any>;
  agent_credentials: Record<string, any>;
  agent_permissions: Record<string, any>;
  agent_roles: Record<string, any>;
  agent_responsibilities: Record<string, any>;
  agent_assignments: Record<string, any>;
  agent_workload: Record<string, any>;
  agent_performance: Record<string, any>;
  agent_efficiency: Record<string, any>;
  agent_productivity: Record<string, any>;
  agent_quality: Record<string, any>;
  agent_reliability: Record<string, any>;
  agent_availability: Record<string, any>;
  agent_scalability: Record<string, any>;
  agent_maintainability: Record<string, any>;
  agent_sustainability: Record<string, any>;
  agent_security: Record<string, any>;
  agent_compliance: Record<string, any>;
  agent_governance: Record<string, any>;
  agent_policies: Record<string, any>;
  agent_standards: Record<string, any>;
  agent_guidelines: Record<string, any>;
  agent_procedures: Record<string, any>;
  agent_processes: Record<string, any>;
  agent_workflows: Record<string, any>;
  agent_pipelines: Record<string, any>;
  agent_infrastructure: Record<string, any>;
  agent_resources: Record<string, any>;
  agent_assets: Record<string, any>;
  agent_inventory: Record<string, any>;
  agent_catalog: Record<string, any>;
  agent_repository: Record<string, any>;
  agent_storage: Record<string, any>;
  agent_backup: Record<string, any>;
  agent_recovery: Record<string, any>;
  agent_restoration: Record<string, any>;
  agent_maintenance: Record<string, any>;
  agent_support: Record<string, any>;
  agent_assistance: Record<string, any>;
  agent_help: Record<string, any>;
  agent_guidance: Record<string, any>;
  agent_direction: Record<string, any>;
  agent_instruction: Record<string, any>;
  agent_training: Record<string, any>;
  agent_education: Record<string, any>;
  agent_development: Record<string, any>;
  agent_growth: Record<string, any>;
  agent_improvement: Record<string, any>;
  agent_enhancement: Record<string, any>;
  agent_optimization: Record<string, any>;
  agent_refinement: Record<string, any>;
  agent_adjustment: Record<string, any>;
  agent_modification: Record<string, any>;
  agent_update: Record<string, any>;
  agent_change: Record<string, any>;
  agent_revision: Record<string, any>;
  agent_version: Record<string, any>;
  agent_history_data: Record<string, any>;
  agent_timeline_data: Record<string, any>;
  agent_schedule_data: Record<string, any>;
  agent_planning_data: Record<string, any>;
  agent_execution_data: Record<string, any>;
}

// Discovery Flow Types for Phase 1 Migration
export interface DiscoveryFlowData {
  id: string;
  flow_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  flow_name: string;
  flow_description?: string;
  status: 'active' | 'completed' | 'failed' | 'paused' | 'waiting_for_user' | 'migrated';
  progress_percentage: number;
  phases: {
    data_import_completed: boolean;
    attribute_mapping_completed: boolean;
    data_cleansing_completed: boolean;
    inventory_completed: boolean;
    dependencies_completed: boolean;
    tech_debt_completed: boolean;
  };
  current_phase: string;
  next_phase?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// API Response Types
export interface FlowStatusResponse {
  flow_id: string;
  status: string;
  progress_percentage: number;
  current_phase: string;
  phase_completion: Record<string, boolean>;
  records_processed?: number;
  records_total?: number;
  records_valid?: number;
  agent_insights?: any[];
  errors?: string[];
  warnings?: string[];
}

export interface FlowData {
  flowId: string;
  flowData: any;
} 