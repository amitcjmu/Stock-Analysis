// Flow identifier interface
export interface FlowIdentifier {
  flowId: string;
}

// Agent insight interface
export interface AgentInsight {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: string;
  agent: string;
  phase: string;
  metadata?: Record<string, unknown>;
}

export interface FlowState {
  flow_id: string; // Primary identifier
  current_phase: string;
  next_phase: string;
  previous_phase: string;
  phase_completion: Record<string, boolean>;
  phase_data: Record<string, unknown>;
  crew_completion_status: Record<string, boolean>;
  agent_insights: Record<string, unknown>;
  agent_learning: Record<string, unknown>;
  agent_feedback: Record<string, unknown>;
  agent_clarifications: Record<string, unknown>;
  agent_recommendations: Record<string, unknown>;
  agent_warnings: Record<string, unknown>;
  agent_errors: Record<string, unknown>;
  agent_progress: Record<string, unknown>;
  agent_status: Record<string, unknown>;
  agent_memory: Record<string, unknown>;
  agent_context: Record<string, unknown>;
  agent_configuration: Record<string, unknown>;
  agent_orchestration: Record<string, unknown>;
  agent_monitoring: Record<string, unknown>;
  agent_metrics: Record<string, unknown>;
  agent_logs: Record<string, unknown>;
  agent_events: Record<string, unknown>;
  agent_tasks: Record<string, unknown>;
  agent_results: Record<string, unknown>;
  agent_artifacts: Record<string, unknown>;
  agent_dependencies: Record<string, unknown>;
  agent_relationships: Record<string, unknown>;
  agent_patterns: Record<string, unknown>;
  agent_decisions: Record<string, unknown>;
  agent_validations: Record<string, unknown>;
  agent_transformations: Record<string, unknown>;
  agent_optimizations: Record<string, unknown>;
  agent_suggestions: Record<string, unknown>;
  agent_improvements: Record<string, unknown>;
  agent_enhancements: Record<string, unknown>;
  agent_refinements: Record<string, unknown>;
  agent_adjustments: Record<string, unknown>;
  agent_modifications: Record<string, unknown>;
  agent_updates: Record<string, unknown>;
  agent_changes: Record<string, unknown>;
  agent_revisions: Record<string, unknown>;
  agent_versions: Record<string, unknown>;
  agent_history: Record<string, unknown>;
  agent_timeline: Record<string, unknown>;
  agent_schedule: Record<string, unknown>;
  agent_planning: Record<string, unknown>;
  agent_execution: Record<string, unknown>;
  agent_monitoring_data: Record<string, unknown>;
  agent_analysis: Record<string, unknown>;
  agent_evaluation: Record<string, unknown>;
  agent_assessment: Record<string, unknown>;
  agent_reporting: Record<string, unknown>;
  agent_documentation: Record<string, unknown>;
  agent_communication: Record<string, unknown>;
  agent_collaboration: Record<string, unknown>;
  agent_coordination: Record<string, unknown>;
  agent_integration: Record<string, unknown>;
  agent_automation: Record<string, unknown>;
  agent_intelligence: Record<string, unknown>;
  agent_learning_data: Record<string, unknown>;
  agent_knowledge: Record<string, unknown>;
  agent_expertise: Record<string, unknown>;
  agent_capabilities: Record<string, unknown>;
  agent_skills: Record<string, unknown>;
  agent_competencies: Record<string, unknown>;
  agent_proficiencies: Record<string, unknown>;
  agent_qualifications: Record<string, unknown>;
  agent_certifications: Record<string, unknown>;
  agent_credentials: Record<string, unknown>;
  agent_permissions: Record<string, unknown>;
  agent_roles: Record<string, unknown>;
  agent_responsibilities: Record<string, unknown>;
  agent_assignments: Record<string, unknown>;
  agent_workload: Record<string, unknown>;
  agent_performance: Record<string, unknown>;
  agent_efficiency: Record<string, unknown>;
  agent_productivity: Record<string, unknown>;
  agent_quality: Record<string, unknown>;
  agent_reliability: Record<string, unknown>;
  agent_availability: Record<string, unknown>;
  agent_scalability: Record<string, unknown>;
  agent_maintainability: Record<string, unknown>;
  agent_sustainability: Record<string, unknown>;
  agent_security: Record<string, unknown>;
  agent_compliance: Record<string, unknown>;
  agent_governance: Record<string, unknown>;
  agent_policies: Record<string, unknown>;
  agent_standards: Record<string, unknown>;
  agent_guidelines: Record<string, unknown>;
  agent_procedures: Record<string, unknown>;
  agent_processes: Record<string, unknown>;
  agent_workflows: Record<string, unknown>;
  agent_pipelines: Record<string, unknown>;
  agent_infrastructure: Record<string, unknown>;
  agent_resources: Record<string, unknown>;
  agent_assets: Record<string, unknown>;
  agent_inventory: Record<string, unknown>;
  agent_catalog: Record<string, unknown>;
  agent_repository: Record<string, unknown>;
  agent_storage: Record<string, unknown>;
  agent_backup: Record<string, unknown>;
  agent_recovery: Record<string, unknown>;
  agent_restoration: Record<string, unknown>;
  agent_maintenance: Record<string, unknown>;
  agent_support: Record<string, unknown>;
  agent_assistance: Record<string, unknown>;
  agent_help: Record<string, unknown>;
  agent_guidance: Record<string, unknown>;
  agent_direction: Record<string, unknown>;
  agent_instruction: Record<string, unknown>;
  agent_training: Record<string, unknown>;
  agent_education: Record<string, unknown>;
  agent_development: Record<string, unknown>;
  agent_growth: Record<string, unknown>;
  agent_improvement: Record<string, unknown>;
  agent_enhancement: Record<string, unknown>;
  agent_optimization: Record<string, unknown>;
  agent_refinement: Record<string, unknown>;
  agent_adjustment: Record<string, unknown>;
  agent_modification: Record<string, unknown>;
  agent_update: Record<string, unknown>;
  agent_change: Record<string, unknown>;
  agent_revision: Record<string, unknown>;
  agent_version: Record<string, unknown>;
  agent_history_data: Record<string, unknown>;
  agent_timeline_data: Record<string, unknown>;
  agent_schedule_data: Record<string, unknown>;
  agent_planning_data: Record<string, unknown>;
  agent_execution_data: Record<string, unknown>;
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
  agent_insights?: AgentInsight[];
  errors?: string[];
  warnings?: string[];
}

export interface FlowData {
  flowId: string;
  flowData: Record<string, unknown>;
} 