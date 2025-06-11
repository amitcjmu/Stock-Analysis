export interface ReadinessAssessment {
  overall_readiness: {
    readiness_score: number;
    readiness_state: string;
    readiness_color: string;
    recommended_action: string;
    critical_gaps: string[];
    recommended_timeline: string;
    confidence_level: number;
  };
  readiness_breakdown: {
    data_discovery: {
      discovery_readiness_score: number;
      asset_inventory_completeness: number;
      application_identification_completeness: number;
      dependency_mapping_completeness: number;
      data_quality_score: number;
      discovery_gaps: string[];
      discovery_recommendations: string[];
    };
    business_context: {
      business_context_score: number;
      stakeholder_input_completeness: number;
      business_criticality_mapping: number;
      risk_tolerance_clarity: number;
      migration_timeline_clarity: number;
      business_gaps: string[];
      stakeholder_engagement_recommendations: string[];
    };
    technical_analysis: {
      technical_analysis_score: number;
      tech_debt_assessment_completeness: number;
      application_complexity_completeness: number;
      infrastructure_analysis_completeness: number;
      security_assessment_completeness: number;
      technical_gaps: string[];
      technical_analysis_recommendations: string[];
    };
    workflow_progression: {
      workflow_progression_score: number;
      discovery_phase_completion: number;
      mapping_phase_completion: number;
      cleanup_phase_completion: number;
      validation_phase_completion: number;
      workflow_gaps: string[];
      workflow_recommendations: string[];
    };
  };
  handoff_metadata: {
    applications_ready_for_assessment: number;
    total_applications: number;
    ready_application_ids: string[];
    pending_application_ids: string[];
    readiness_by_application_type: Record<string, number>;
  };
  outstanding_questions: Array<{
    id: string;
    question: string;
    category: string;
    impact: 'high' | 'medium' | 'low';
    required_for: string;
  }>;
  risk_assessment: {
    overall_risk_level: string;
    risk_factors: Array<{
      factor: string;
      impact: 'high' | 'medium' | 'low';
      mitigation_strategy: string;
    }>;
  };
  recommendations: Array<{
    id: string;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    estimated_effort: string;
    impact: string;
    category: string;
  }>;
  signoff_status: {
    current_status: 'not_started' | 'in_progress' | 'pending_approval' | 'approved' | 'rejected';
    approvers: Array<{
      id: string;
      name: string;
      role: string;
      status: 'pending' | 'approved' | 'rejected';
      timestamp?: string;
      comments?: string;
    }>;
    approval_threshold: number;
    current_approval_percentage: number;
    next_steps: string[];
  };
  metadata: {
    assessment_id: string;
    assessment_timestamp: string;
    assessment_version: string;
    generated_by: string;
    last_updated: string;
  };
}

export interface SignoffPackage {
  executive_summary: {
    assessment_readiness_status: string;
    applications_ready_for_assessment: number;
    total_applications: number;
    key_achievements: string[];
    remaining_gaps: string[];
    business_confidence: number;
  };
  validation_checkpoints: Array<{
    checkpoint: string;
    status: string;
    confidence: number;
  }>;
  assessment_risk_evaluation: {
    risk_level: string;
    risk_factors: string[];
  };
  recommended_actions: string[];
  stakeholder_decisions_required: string[];
  success_criteria: string[];
  signoff_metadata: {
    package_generated: string;
    assessment_confidence: number;
    stakeholder_input_level: number;
    recommended_signoff_date: string;
  };
}
