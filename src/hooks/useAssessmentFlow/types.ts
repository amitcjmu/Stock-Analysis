/**
 * Assessment Flow Types
 *
 * Type definitions for the assessment flow hook and related interfaces.
 */

// User input interface for flow resumption
export interface UserInput {
  phase?: string;
  data?: Record<string, string | number | boolean>;
  action?: "continue" | "skip" | "retry";
  timestamp?: string;
}

// Types for Assessment Flow
export type AssessmentFlowStatus =
  | "initialized"
  | "processing"
  | "paused_for_user_input"
  | "completed"
  | "error";

// Assessment phases aligned with backend FlowTypeConfig (assessment_flow_config.py)
// Order: readiness_assessment → architecture_minimums → complexity_analysis →
//        dependency_analysis → tech_debt_assessment → risk_assessment → recommendation_generation
export type AssessmentPhase =
  | "initialization"
  | "readiness_assessment"
  | "architecture_minimums"
  | "complexity_analysis"
  | "dependency_analysis"
  | "tech_debt_assessment"
  | "risk_assessment"
  | "recommendation_generation"
  | "finalization";

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
  severity: "critical" | "high" | "medium" | "low";
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
  is_accepted?: boolean; // Issue #719 - User accepted recommendation, ready for planning
}

export interface AssessmentApplication {
  application_id: string;
  application_name: string;
  application_type: string;
  environment: string;
  business_criticality: string;
  technology_stack: string[];
  complexity_score: number;
  readiness_score: number;
  discovery_completed_at: string;
}

export interface AssessmentFlowState {
  flowId: string | null;
  status: AssessmentFlowStatus;
  progress: number;
  currentPhase: AssessmentPhase;
  nextPhase: AssessmentPhase | null;
  pausePoints: string[];
  selectedApplicationIds: string[];
  selectedApplications: AssessmentApplication[]; // Full application details
  applicationCount: number; // Count of applications

  // Phase-specific data
  engagementStandards: ArchitectureStandard[];
  applicationOverrides: Record<string, ArchitectureStandard>;
  selectedTemplate: string | null; // Template ID (enterprise-standard, cloud-native, security-first, performance-optimized, custom, or null)
  applicationComponents: Record<string, ApplicationComponent[]>;
  techDebtAnalysis: Record<string, TechDebtItem[]>;
  sixrDecisions: Record<string, SixRDecision>;

  // UI state
  isLoading: boolean;
  dataFetched: boolean; // Bug #730 fix - track if initial data has been loaded
  error: string | null;
  lastUserInteraction: Date | null;
  appsReadyForPlanning: string[];
  autoPollingEnabled: boolean; // User-controlled auto-polling toggle

  // Phase failure tracking (Fix for issue #818)
  hasFailedPhases?: boolean;
  failedPhases?: string[];

  // Real-time updates
  agentUpdates: Array<{
    timestamp: Date;
    phase: string;
    message: string;
    progress?: number;
  }>;
}

// Response from resume flow API (ADR-027)
export interface AssessmentFlowStatusResponse {
  flow_id: string;
  status: string;
  current_phase: string;
  progress: number;
}

export interface UseAssessmentFlowReturn {
  // State
  state: AssessmentFlowState;

  // Flow control
  initializeFlow: (selectedAppIds: string[]) => Promise<void>;
  resumeFlow: (userInput: UserInput) => Promise<AssessmentFlowStatusResponse>;
  navigateToPhase: (phase: AssessmentPhase) => Promise<void>;
  finalizeAssessment: () => Promise<void>;

  // Data operations
  updateArchitectureStandards: (
    standards: ArchitectureStandard[],
    overrides: Record<string, ArchitectureStandard>,
  ) => Promise<void>;
  updateApplicationComponents: (
    appId: string,
    components: ApplicationComponent[],
  ) => Promise<void>;
  updateTechDebtAnalysis: (
    appId: string,
    techDebt: TechDebtItem[],
  ) => Promise<void>;
  updateSixRDecision: (
    appId: string,
    decision: Partial<SixRDecision>,
  ) => Promise<void>;

  // Real-time updates
  subscribeToUpdates: () => void;
  unsubscribeFromUpdates: () => void;

  // Utilities
  getPhaseProgress: (phase: AssessmentPhase) => number;
  canNavigateToPhase: (phase: AssessmentPhase) => boolean;
  getApplicationsNeedingReview: () => string[];
  isPhaseComplete: (phase: AssessmentPhase) => boolean;
  refreshApplicationData: () => Promise<void>;
  toggleAutoPolling: () => void; // Toggle auto-polling on/off
}
