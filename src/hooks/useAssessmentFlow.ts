import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

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
  requirement_details?: Record<string, any>;
  verification_status?: string;
  modified_by?: string;
}

export interface ApplicationComponent {
  component_name: string;
  component_type: string;
  technology_stack?: Record<string, any>;
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
  user_modifications?: Record<string, any>;
  app_on_page_data?: Record<string, any>;
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
  applicationOverrides: Record<string, any>;
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

interface UseAssessmentFlowReturn {
  // State
  state: AssessmentFlowState;
  
  // Flow control
  initializeFlow: (selectedAppIds: string[]) => Promise<void>;
  resumeFlow: (userInput: any) => Promise<void>;
  navigateToPhase: (phase: AssessmentPhase) => Promise<void>;
  finalizeAssessment: () => Promise<void>;
  
  // Data operations
  updateArchitectureStandards: (
    standards: ArchitectureStandard[], 
    overrides: Record<string, any>
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

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Assessment Flow API client
const assessmentFlowAPI = {
  async initialize(data: { selected_application_ids: string[] }, headers: Record<string, string>) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/initialize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to initialize assessment flow: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getStatus(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/status`);
    
    if (!response.ok) {
      throw new Error(`Failed to get flow status: ${response.statusText}`);
    }
    
    return response.json();
  },

  async resume(flowId: string, data: { user_input: any; save_progress: boolean }) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to resume flow: ${response.statusText}`);
    }
    
    return response.json();
  },

  async navigateToPhase(flowId: string, phase: AssessmentPhase) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/navigate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ phase }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to navigate to phase: ${response.statusText}`);
    }
    
    return response.json();
  },

  async updateArchitectureStandards(flowId: string, data: { 
    engagement_standards: ArchitectureStandard[]; 
    application_overrides: Record<string, any> 
  }) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/architecture-standards`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update architecture standards: ${response.statusText}`);
    }
    
    return response.json();
  },

  async updateApplicationComponents(flowId: string, appId: string, components: ApplicationComponent[]) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/applications/${appId}/components`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ components }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update application components: ${response.statusText}`);
    }
    
    return response.json();
  },

  async updateSixRDecision(flowId: string, appId: string, decision: Partial<SixRDecision>) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/applications/${appId}/sixr-decision`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(decision),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update 6R decision: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getArchitectureStandards(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/architecture-standards`);
    
    if (!response.ok) {
      throw new Error(`Failed to get architecture standards: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getTechDebtAnalysis(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/tech-debt-analysis`);
    
    if (!response.ok) {
      throw new Error(`Failed to get tech debt analysis: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getApplicationComponents(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/application-components`);
    
    if (!response.ok) {
      throw new Error(`Failed to get application components: ${response.statusText}`);
    }
    
    return response.json();
  },

  async getSixRDecisions(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/sixr-decisions`);
    
    if (!response.ok) {
      throw new Error(`Failed to get 6R decisions: ${response.statusText}`);
    }
    
    return response.json();
  },

  async finalize(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/finalize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to finalize assessment: ${response.statusText}`);
    }
    
    return response.json();
  },
};

// Event source service for real-time updates
const eventSourceService = {
  subscribe(url: string, options: {
    onMessage: (event: MessageEvent) => void;
    onError: (error: Event) => void;
  }): EventSource {
    const eventSource = new EventSource(`${API_BASE}${url}`);
    
    eventSource.onmessage = options.onMessage;
    eventSource.onerror = options.onError;
    
    return eventSource;
  }
};

export const useAssessmentFlow = (
  initialFlowId?: string
): UseAssessmentFlowReturn => {
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();
  const eventSourceRef = useRef<EventSource | null>(null);
  
  // Get client account and engagement from auth context
  const clientAccountId = user?.client_account_id;
  const engagementId = user?.engagement_id;
  
  // Initial state
  const [state, setState] = useState<AssessmentFlowState>({
    flowId: initialFlowId || null,
    status: 'initialized',
    progress: 0,
    currentPhase: 'architecture_minimums',
    nextPhase: null,
    pausePoints: [],
    selectedApplicationIds: [],
    engagementStandards: [],
    applicationOverrides: {},
    applicationComponents: {},
    techDebtAnalysis: {},
    sixrDecisions: {},
    isLoading: false,
    error: null,
    lastUserInteraction: null,
    appsReadyForPlanning: [],
    agentUpdates: []
  });
  
  // Initialize assessment flow
  const initializeFlow = useCallback(async (selectedAppIds: string[]) => {
    if (!clientAccountId || !engagementId) {
      throw new Error('Client account and engagement context required');
    }
    
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const headers = getAuthHeaders?.() || {};
      const response = await assessmentFlowAPI.initialize({
        selected_application_ids: selectedAppIds
      }, headers);
      
      setState(prev => ({
        ...prev,
        flowId: response.flow_id,
        status: response.status as AssessmentFlowStatus,
        currentPhase: response.current_phase as AssessmentPhase,
        nextPhase: response.next_phase as AssessmentPhase,
        selectedApplicationIds: selectedAppIds,
        progress: 10,
        isLoading: false
      }));
      
      // Start real-time updates
      subscribeToUpdates();
      
      // Navigate to first phase
      if (navigate) {
        navigate(`/assessment/${response.flow_id}/architecture`);
      }
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to initialize assessment',
        isLoading: false 
      }));
      throw error;
    }
  }, [clientAccountId, engagementId, navigate, getAuthHeaders]);
  
  // Resume flow from current phase
  const resumeFlow = useCallback(async (userInput: any) => {
    if (!state.flowId) {
      throw new Error('No active flow to resume');
    }
    
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      await assessmentFlowAPI.resume(state.flowId, {
        user_input: userInput,
        save_progress: true
      });
      
      setState(prev => ({
        ...prev,
        status: 'processing',
        lastUserInteraction: new Date(),
        isLoading: false
      }));
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to resume flow',
        isLoading: false 
      }));
      throw error;
    }
  }, [state.flowId]);
  
  // Navigate to specific phase
  const navigateToPhase = useCallback(async (phase: AssessmentPhase) => {
    if (!state.flowId) {
      throw new Error('No active flow for navigation');
    }
    
    if (!canNavigateToPhase(phase)) {
      throw new Error(`Cannot navigate to phase: ${phase}`);
    }
    
    try {
      await assessmentFlowAPI.navigateToPhase(state.flowId, phase);
      
      setState(prev => ({
        ...prev,
        currentPhase: phase,
        nextPhase: getNextPhaseForNavigation(phase)
      }));
      
      // Update URL
      const phaseRoutes: Record<AssessmentPhase, string> = {
        'initialization': 'initialize',
        'architecture_minimums': 'architecture',
        'tech_debt_analysis': 'tech-debt',
        'component_sixr_strategies': 'sixr-review',
        'app_on_page_generation': 'app-on-page',
        'finalization': 'summary'
      };
      
      if (navigate) {
        navigate(`/assessment/${state.flowId}/${phaseRoutes[phase]}`);
      }
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Navigation failed'
      }));
      throw error;
    }
  }, [state.flowId, navigate]);
  
  // Update architecture standards
  const updateArchitectureStandards = useCallback(async (
    standards: ArchitectureStandard[], 
    overrides: Record<string, any>
  ) => {
    if (!state.flowId) {
      throw new Error('No active flow');
    }
    
    try {
      await assessmentFlowAPI.updateArchitectureStandards(state.flowId, {
        engagement_standards: standards,
        application_overrides: overrides
      });
      
      setState(prev => ({
        ...prev,
        engagementStandards: standards,
        applicationOverrides: overrides,
        lastUserInteraction: new Date()
      }));
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to update standards'
      }));
      throw error;
    }
  }, [state.flowId]);
  
  // Update application components
  const updateApplicationComponents = useCallback(async (
    appId: string, 
    components: ApplicationComponent[]
  ) => {
    if (!state.flowId) {
      throw new Error('No active flow');
    }
    
    try {
      await assessmentFlowAPI.updateApplicationComponents(state.flowId, appId, components);
      
      setState(prev => ({
        ...prev,
        applicationComponents: {
          ...prev.applicationComponents,
          [appId]: components
        },
        lastUserInteraction: new Date()
      }));
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to update components'
      }));
      throw error;
    }
  }, [state.flowId]);
  
  // Update tech debt analysis
  const updateTechDebtAnalysis = useCallback(async (
    appId: string, 
    techDebt: TechDebtItem[]
  ) => {
    if (!state.flowId) {
      throw new Error('No active flow');
    }
    
    try {
      // Note: API endpoint would need to be implemented for tech debt updates
      setState(prev => ({
        ...prev,
        techDebtAnalysis: {
          ...prev.techDebtAnalysis,
          [appId]: techDebt
        },
        lastUserInteraction: new Date()
      }));
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to update tech debt analysis'
      }));
      throw error;
    }
  }, [state.flowId]);
  
  // Update 6R decision
  const updateSixRDecision = useCallback(async (
    appId: string, 
    decision: Partial<SixRDecision>
  ) => {
    if (!state.flowId) {
      throw new Error('No active flow');
    }
    
    try {
      await assessmentFlowAPI.updateSixRDecision(state.flowId, appId, decision);
      
      setState(prev => ({
        ...prev,
        sixrDecisions: {
          ...prev.sixrDecisions,
          [appId]: { ...prev.sixrDecisions[appId], ...decision } as SixRDecision
        },
        lastUserInteraction: new Date()
      }));
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to update decision'
      }));
      throw error;
    }
  }, [state.flowId]);
  
  // Subscribe to real-time updates
  const subscribeToUpdates = useCallback(() => {
    if (!state.flowId || eventSourceRef.current) {
      return;
    }
    
    try {
      const eventSource = eventSourceService.subscribe(
        `/api/v1/assessment-flow/${state.flowId}/events`,
        {
          onMessage: (event) => {
            const data = JSON.parse(event.data);
            
            setState(prev => ({
              ...prev,
              status: data.status || prev.status,
              progress: data.progress || prev.progress,
              currentPhase: data.current_phase || prev.currentPhase,
              nextPhase: data.next_phase || prev.nextPhase,
              agentUpdates: [
                ...prev.agentUpdates,
                {
                  timestamp: new Date(),
                  phase: data.phase || prev.currentPhase,
                  message: data.message || 'Processing...',
                  progress: data.progress
                }
              ].slice(-20) // Keep last 20 updates
            }));
          },
          onError: (error) => {
            console.error('Assessment flow SSE error:', error);
            setState(prev => ({ 
              ...prev, 
              error: 'Real-time updates disconnected' 
            }));
          }
        }
      );
      
      eventSourceRef.current = eventSource;
      
    } catch (error) {
      console.error('Failed to subscribe to updates:', error);
    }
  }, [state.flowId]);
  
  // Unsubscribe from updates
  const unsubscribeFromUpdates = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);
  
  // Utility functions
  const getPhaseProgress = useCallback((phase: AssessmentPhase): number => {
    const progressMap: Record<AssessmentPhase, number> = {
      'initialization': 10,
      'architecture_minimums': 20,
      'tech_debt_analysis': 50,
      'component_sixr_strategies': 75,
      'app_on_page_generation': 90,
      'finalization': 100
    };
    return progressMap[phase] || 0;
  }, []);
  
  const canNavigateToPhase = useCallback((phase: AssessmentPhase): boolean => {
    const phaseOrder: AssessmentPhase[] = [
      'architecture_minimums',
      'tech_debt_analysis', 
      'component_sixr_strategies',
      'app_on_page_generation',
      'finalization'
    ];
    
    const currentIndex = phaseOrder.indexOf(state.currentPhase);
    const targetIndex = phaseOrder.indexOf(phase);
    
    // Can navigate to current phase or any previous completed phase
    return targetIndex <= currentIndex || state.pausePoints.includes(phase);
  }, [state.currentPhase, state.pausePoints]);
  
  const getApplicationsNeedingReview = useCallback((): string[] => {
    return Object.entries(state.sixrDecisions)
      .filter(([_, decision]) => decision.confidence_score < 0.8)
      .map(([appId, _]) => appId);
  }, [state.sixrDecisions]);
  
  const isPhaseComplete = useCallback((phase: AssessmentPhase): boolean => {
    return state.pausePoints.includes(phase);
  }, [state.pausePoints]);
  
  // Load flow state on mount or flowId change
  useEffect(() => {
    if (state.flowId && clientAccountId) {
      loadFlowState();
      subscribeToUpdates();
    }
    
    return () => {
      unsubscribeFromUpdates();
    };
  }, [state.flowId, clientAccountId]);
  
  // Load current flow state
  const loadFlowState = async () => {
    if (!state.flowId) return;
    
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      
      const flowStatus = await assessmentFlowAPI.getStatus(state.flowId);
      
      setState(prev => ({
        ...prev,
        status: flowStatus.status as AssessmentFlowStatus,
        progress: flowStatus.progress,
        currentPhase: flowStatus.current_phase as AssessmentPhase,
        nextPhase: flowStatus.next_phase as AssessmentPhase,
        pausePoints: flowStatus.pause_points,
        appsReadyForPlanning: flowStatus.apps_ready_for_planning,
        lastUserInteraction: flowStatus.last_user_interaction ? 
          new Date(flowStatus.last_user_interaction) : null,
        isLoading: false
      }));
      
      // Load phase-specific data
      await loadPhaseData(flowStatus.current_phase);
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to load flow state',
        isLoading: false 
      }));
    }
  };
  
  // Load phase-specific data
  const loadPhaseData = async (phase: AssessmentPhase) => {
    if (!state.flowId) return;
    
    try {
      switch (phase) {
        case 'architecture_minimums':
          const archData = await assessmentFlowAPI.getArchitectureStandards(state.flowId);
          setState(prev => ({
            ...prev,
            engagementStandards: archData.engagement_standards,
            applicationOverrides: archData.application_overrides
          }));
          break;
          
        case 'tech_debt_analysis':
          const techDebtData = await assessmentFlowAPI.getTechDebtAnalysis(state.flowId);
          const componentsData = await assessmentFlowAPI.getApplicationComponents(state.flowId);
          setState(prev => ({
            ...prev,
            techDebtAnalysis: techDebtData.applications,
            applicationComponents: componentsData.applications
          }));
          break;
          
        case 'component_sixr_strategies':
        case 'app_on_page_generation':
          const decisionsData = await assessmentFlowAPI.getSixRDecisions(state.flowId);
          setState(prev => ({
            ...prev,
            sixrDecisions: decisionsData.decisions.reduce((acc: Record<string, SixRDecision>, decision: SixRDecision) => {
              acc[decision.application_id] = decision;
              return acc;
            }, {})
          }));
          break;
      }
    } catch (error) {
      console.error(`Failed to load ${phase} data:`, error);
    }
  };
  
  // Helper function for navigation
  const getNextPhaseForNavigation = (currentPhase: AssessmentPhase): AssessmentPhase | null => {
    const phaseOrder: AssessmentPhase[] = [
      'architecture_minimums',
      'tech_debt_analysis',
      'component_sixr_strategies', 
      'app_on_page_generation',
      'finalization'
    ];
    
    const currentIndex = phaseOrder.indexOf(currentPhase);
    return currentIndex < phaseOrder.length - 1 ? phaseOrder[currentIndex + 1] : null;
  };
  
  return {
    state,
    initializeFlow,
    resumeFlow,
    navigateToPhase,
    finalizeAssessment: async () => {
      if (!state.flowId) return;
      await assessmentFlowAPI.finalize(state.flowId);
    },
    updateArchitectureStandards,
    updateApplicationComponents,
    updateTechDebtAnalysis,
    updateSixRDecision,
    subscribeToUpdates,
    unsubscribeFromUpdates,
    getPhaseProgress,
    canNavigateToPhase,
    getApplicationsNeedingReview,
    isPhaseComplete
  };
};