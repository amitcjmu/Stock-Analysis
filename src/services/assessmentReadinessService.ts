import { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import api from './api';
import { useAuth } from '@/contexts/AuthContext';

// Types
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
      workflow_acceleration_recommendations: string[];
    };
  };
  application_readiness: Array<{
    application_id: string;
    application_name: string;
    readiness_score: number;
    readiness_level: string;
    readiness_factors: {
      technical_readiness: number;
      business_readiness: number;
      operational_readiness: number;
      metadata?: Record<string, unknown>;
    };
    blocking_issues: string[];
    assessment_priority: number;
  }>;
  prioritized_applications: Array<{
    application_id: string;
    application_name: string;
    readiness_score: number;
    assessment_priority_score: number;
    priority_justification: string;
    recommended_assessment_order: number;
    assessment_complexity: string;
    stakeholder_attention_required: string;
  }>;
  assessment_preparation: string[];
  outstanding_questions: Array<{
    question: string;
    assessment_impact_score: number;
    phase: string;
  }>;
  handoff_metadata: {
    assessment_readiness_score: number;
    applications_ready_for_assessment: number;
    critical_gaps: string[];
    recommended_timeline: string;
    assessment_timestamp: string;
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

// API Calls
const fetchReadinessAssessment = async (clientAccountId: string, engagementId: string): Promise<ReadinessAssessment> => {
  const response = await api.get(`/api/v1/assess/readiness/${clientAccountId}/${engagementId}`);
  return response.data;
};

const generateSignoffPackage = async (clientAccountId: string, engagementId: string): Promise<SignoffPackage> => {
  const response = await api.post(`/api/v1/assess/generate-signoff/${clientAccountId}/${engagementId}`);
  return response.data;
};

/**
 * Stakeholder signoff data for external approval systems
 */
export interface StakeholderSignoffData {
  approval_type: 'assessment_readiness' | 'stakeholder_review' | 'final_signoff';
  approver_role: string;
  comments?: string;
  approval_status: 'approved' | 'rejected' | 'pending';
  metadata?: Record<string, unknown>;
}

const submitForApproval = async (clientAccountId: string, engagementId: string, signoffData: StakeholderSignoffData) => {
  const response = await api.post(`/api/v1/assess/submit-approval/${clientAccountId}/${engagementId}`, signoffData);
  return response.data;
};

// React Query Hooks
export const useReadinessAssessment = (clientAccountId: string, engagementId: string): ReturnType<typeof useQuery> => {
  return useQuery({
    queryKey: ['readinessAssessment', clientAccountId, engagementId],
    queryFn: () => fetchReadinessAssessment(clientAccountId, engagementId),
    enabled: !!clientAccountId && !!engagementId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useGenerateSignoffPackage = (): ReturnType<typeof useMutation> => {
  const { clientAccountId, engagementId } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => generateSignoffPackage(clientAccountId, engagementId),
    onSuccess: (data) => {
      queryClient.setQueryData(['signoffPackage', clientAccountId, engagementId], data);
    },
  });
};

export const useSubmitForApproval = (): ReturnType<typeof useMutation> => {
  const { clientAccountId, engagementId } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (signoffData: StakeholderSignoffData) => submitForApproval(clientAccountId, engagementId, signoffData),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['readinessAssessment', clientAccountId, engagementId] });
    },
  });
};
