export interface ReadinessAssessment {
  id: string;
  overall_readiness: {
    readiness_score: number;
    status: string;
    last_updated: string;
    recommended_action: string;
    critical_gaps: string[];
  };
  handoff_metadata: {
    applications_ready_for_assessment: number;
    total_applications: number;
    assessment_completion_percentage: number;
  };
  recommendations: Array<{
    id: string;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    status: 'pending' | 'in-progress' | 'completed';
    category?: string;
    estimated_effort?: string;
    impact?: string;
  }>;
  outstanding_questions: Array<{
    id: string;
    question: string;
    category: string;
    status: 'pending' | 'answered';
  }>;
  readiness_breakdown: {
    [key: string]: {
      score: number;
      status: string;
      gaps?: string[];
    };
  };
  risk_assessment?: {
    overall_risk: string;
    risk_factors: Array<{
      id: string;
      title: string;
      description: string;
      impact: string;
      likelihood: string;
      risk_level: string;
      recommended_action: string;
    }>;
  };
  signoffPackage?: SignoffPackage;
  workflow_progression?: {
    workflow_recommendations: string[];
  };
}

export interface SignoffPackage {
  id: string;
  generated_at: string;
  status: 'draft' | 'pending' | 'approved' | 'rejected';
  download_url?: string;
  executive_summary?: {
    overview: string;
    key_findings: string[];
    recommendations: string[];
  };
  signoff_metadata?: {
    generated_by: string;
    generated_on: string;
    version: string;
    client_name: string;
    engagement_name: string;
  };
  approvers: Array<{
    id: string;
    name: string;
    email: string;
    status: 'pending' | 'approved' | 'rejected';
    approved_at?: string;
    comments?: string;
  }>;
}

export interface ReadinessScoreCardProps {
  assessment: ReadinessAssessment;
  onRefresh: () => void;
  isLoading: boolean;
}

export interface ReadinessTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  assessment: ReadinessAssessment;
  signoffPackage: SignoffPackage | null;
  isReadyForSignoff: boolean;
  isGeneratingSignoff: boolean;
  isSubmittingApproval: boolean;
  onGenerateSignoff: () => void;
  onSubmitForApproval: () => void;
  children?: React.ReactNode;
}

export interface UseReadinessAssessmentOptions {
  clientAccountId: string;
  engagementId: string;
}

export interface GenerateSignoffPackageParams {
  assessmentId: string;
  clientAccountId: string;
  engagementId: string;
}

export interface SubmitForApprovalParams {
  assessmentId: string;
  signoffPackage: SignoffPackage;
  clientAccountId: string;
  engagementId: string;
}
