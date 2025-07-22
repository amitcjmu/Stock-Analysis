/**
 * Assessment Flow Types
 * 
 * Type definitions for the assessment flow hook and related interfaces.
 */

// User input interface for flow resumption
export interface UserInput {
  phase?: string;
  data?: Record<string, string | number | boolean>;
  action?: 'continue' | 'skip' | 'retry';
  timestamp?: string;
}

// Types for Assessment Flow
export type AssessmentFlowStatus = 
  | 'initialized' 
  | 'processing' 
  | 'paused_for_user_input' 
  | 'completed' 
  | 'error';

export type AssessmentPhase = 
  | 'initialization'
  | 'architecture_minimums'
  | 'tech_debt_analysis' 
  | 'component_sixr_strategies'
  | 'app_on_page_generation'
  | 'finalization';

export interface ArchitectureStandard {
  id?: string;
  requirement_type: string;
  description: string;
  mandatory: boolean;
  supported_versions?: Record<string, string>;
  requirement_details?: Record<string, string | number | boolean>;
  verification_status?: string;
  modified_by?: string;
}

export interface ApplicationComponent {
  component_name: string;
  component_type: string;
  technology_stack?: Record<string, string>;
  dependencies?: string[];
}

export interface TechDebtItem {
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  remediation_effort_hours?: number;
  impact_on_migration?: string;
  tech_debt_score?: number;
}

export interface ComponentTreatment {
  component_name: string;
  component_type: string;
  recommended_strategy: string;
  rationale: string;
  compatibility_validated: boolean;
  compatibility_issues?: string[];
}

export interface SixRDecision {
  application_id: string;
  application_name: string;
  component_treatments: ComponentTreatment[];
  overall_strategy: string;
  confidence_score: number;
  rationale: string;
  architecture_exceptions: string[];
  tech_debt_score?: number;
  risk_factors: string[];
  move_group_hints: string[];
  user_modifications?: Record<string, string | number | boolean>;
  app_on_page_data?: Record<string, string | number | boolean>;
}

export interface AssessmentFlowState {
  flowId: string | null;
  status: AssessmentFlowStatus;
  progress: number;
  currentPhase: AssessmentPhase;
  nextPhase: AssessmentPhase | null;
  pausePoints: string[];
  selectedApplicationIds: string[];
  
  // Phase-specific data
  engagementStandards: ArchitectureStandard[];
  applicationOverrides: Record<string, ArchitectureStandard>;
  applicationComponents: Record<string, ApplicationComponent[]>;
  techDebtAnalysis: Record<string, TechDebtItem[]>;
  sixrDecisions: Record<string, SixRDecision>;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  lastUserInteraction: Date | null;
  appsReadyForPlanning: string[];
  
  // Real-time updates
  agentUpdates: Array<{
    timestamp: Date;
    phase: string;
    message: string;
    progress?: number;
  }>;
}

export interface UseAssessmentFlowReturn {
  // State
  state: AssessmentFlowState;
  
  // Flow control
  initializeFlow: (selectedAppIds: string[]) => Promise<void>;
  resumeFlow: (userInput: UserInput) => Promise<void>;
  navigateToPhase: (phase: AssessmentPhase) => Promise<void>;
  finalizeAssessment: () => Promise<void>;
  
  // Data operations
  updateArchitectureStandards: (
    standards: ArchitectureStandard[], 
    overrides: Record<string, ArchitectureStandard>
  ) => Promise<void>;
  updateApplicationComponents: (
    appId: string, 
    components: ApplicationComponent[]
  ) => Promise<void>;
  updateTechDebtAnalysis: (
    appId: string, 
    techDebt: TechDebtItem[]
  ) => Promise<void>;
  updateSixRDecision: (
    appId: string, 
    decision: Partial<SixRDecision>
  ) => Promise<void>;
  
  // Real-time updates
  subscribeToUpdates: () => void;
  unsubscribeFromUpdates: () => void;
  
  // Utilities
  getPhaseProgress: (phase: AssessmentPhase) => number;
  canNavigateToPhase: (phase: AssessmentPhase) => boolean;
  getApplicationsNeedingReview: () => string[];
  isPhaseComplete: (phase: AssessmentPhase) => boolean;
}