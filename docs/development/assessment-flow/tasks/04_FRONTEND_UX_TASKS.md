# Assessment Flow - Frontend & UX Tasks

## Overview
This document tracks all frontend implementation, user interface, and user experience tasks for the Assessment Flow implementation.

## Key Implementation Context
- **Node-based navigation** with left sidebar mapping to flow phases
- **Pause/resume state management** with automatic progress persistence
- **Mixed API usage** (v1 primarily) during platform transition period
- **Multi-browser session support** with robust state synchronization
- **Real-time agent updates** via HTTP/2 Server-Sent Events
- **App-on-page comprehensive view** for detailed application assessment

---

## ⚛️ Frontend Core Tasks

### FE-001: Create Assessment Flow Hook and State Management
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 16 hours  
**Dependencies**: API Core (API-001)  
**Sprint**: Frontend Week 7-8  

**Description**: Implement central React hook for assessment flow state management with pause/resume capabilities and API integration

**Location**: `src/hooks/useAssessmentFlow.ts`

**Technical Requirements**:
- React hook with TypeScript for type safety
- Integration with v1 API endpoints (aligning with platform reality)
- State persistence across browser sessions and navigation
- Real-time updates via Server-Sent Events
- Error handling and recovery mechanisms
- Multi-tenant context management

**Hook Implementation**:
```typescript
import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/router';
import { useClientAccount } from '@/hooks/useClientAccount';
import { assessmentFlowAPI } from '@/utils/api/assessmentFlow';
import { eventSourceService } from '@/utils/events/eventSource';

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

export const useAssessmentFlow = (
  initialFlowId?: string
): UseAssessmentFlowReturn => {
  const router = useRouter();
  const { clientAccountId, engagementId } = useClientAccount();
  const eventSourceRef = useRef<EventSource | null>(null);
  
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
      const response = await assessmentFlowAPI.initialize({
        selected_application_ids: selectedAppIds
      }, {
        'X-Client-Account-ID': clientAccountId.toString(),
        'X-Engagement-ID': engagementId.toString()
      });
      
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
      await router.push(`/assessment/${response.flow_id}/architecture`);
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to initialize assessment',
        isLoading: false 
      }));
      throw error;
    }
  }, [clientAccountId, engagementId, router]);
  
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
      
      await router.push(`/assessment/${state.flowId}/${phaseRoutes[phase]}`);
      
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Navigation failed'
      }));
      throw error;
    }
  }, [state.flowId, router]);
  
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
    updateTechDebtAnalysis: async (appId: string, techDebt: TechDebtItem[]) => {
      // Implementation for tech debt updates
    },
    updateSixRDecision,
    subscribeToUpdates,
    unsubscribeFromUpdates,
    getPhaseProgress,
    canNavigateToPhase,
    getApplicationsNeedingReview,
    isPhaseComplete
  };
};
```

**Acceptance Criteria**:
- [ ] Complete TypeScript hook with proper type safety
- [ ] Integration with v1 API endpoints
- [ ] State persistence across browser sessions
- [ ] Real-time updates via Server-Sent Events
- [ ] Multi-tenant context management
- [ ] Comprehensive error handling and recovery
- [ ] Phase navigation and progress tracking
- [ ] User input capture and flow resumption

---

### FE-002: Create Assessment Flow Navigation Layout
**Status**: 🔴 Not Started  
**Priority**: P0 - Critical  
**Effort**: 12 hours  
**Dependencies**: FE-001  
**Sprint**: Frontend Week 7-8  

**Description**: Implement the main layout component with left sidebar navigation mapping to assessment flow phases

**Location**: `src/components/assessment/AssessmentFlowLayout.tsx`

**Technical Requirements**:
- Left sidebar navigation with phase indicators
- Progress visualization and phase completion status
- Responsive design for different screen sizes
- Integration with flow navigation and state management
- Real-time progress updates and visual feedback

**Layout Implementation**:
```typescript
import React from 'react';
import { useRouter } from 'next/router';
import { 
  Sidebar, 
  SidebarContent, 
  SidebarHeader, 
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton 
} from '@/components/ui/sidebar';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle,
  ChevronRight,
  Loader2 
} from 'lucide-react';
import { useAssessmentFlow, AssessmentPhase } from '@/hooks/useAssessmentFlow';
import { cn } from '@/lib/utils';

interface AssessmentFlowLayoutProps {
  children: React.ReactNode;
  flowId: string;
}

interface PhaseConfig {
  id: AssessmentPhase;
  title: string;
  description: string;
  route: string;
  icon: React.ComponentType<{ className?: string }>;
  estimatedTime: string;
}

const PHASE_CONFIG: PhaseConfig[] = [
  {
    id: 'architecture_minimums',
    title: 'Architecture Standards',
    description: 'Define engagement-level minimums and application exceptions',
    route: 'architecture',
    icon: ({ className }) => <Circle className={className} />,
    estimatedTime: '15-30 min'
  },
  {
    id: 'tech_debt_analysis', 
    title: 'Technical Debt Analysis',
    description: 'Analyze components and identify modernization opportunities',
    route: 'tech-debt',
    icon: ({ className }) => <Circle className={className} />,
    estimatedTime: '20-45 min'
  },
  {
    id: 'component_sixr_strategies',
    title: '6R Strategy Review',
    description: 'Review and modify component-level modernization strategies',
    route: 'sixr-review', 
    icon: ({ className }) => <Circle className={className} />,
    estimatedTime: '30-60 min'
  },
  {
    id: 'app_on_page_generation',
    title: 'Application Review',
    description: 'Comprehensive review of all application assessments',
    route: 'app-on-page',
    icon: ({ className }) => <Circle className={className} />,
    estimatedTime: '15-30 min'
  },
  {
    id: 'finalization',
    title: 'Assessment Summary',
    description: 'Finalize assessment and prepare for planning',
    route: 'summary',
    icon: ({ className }) => <Circle className={className} />,
    estimatedTime: '10-15 min'
  }
];

export const AssessmentFlowLayout: React.FC<AssessmentFlowLayoutProps> = ({
  children,
  flowId
}) => {
  const router = useRouter();
  const {
    state,
    navigateToPhase,
    canNavigateToPhase,
    isPhaseComplete,
    getPhaseProgress
  } = useAssessmentFlow(flowId);
  
  const getPhaseStatus = (phase: AssessmentPhase) => {
    if (state.currentPhase === phase) {
      if (state.status === 'processing') return 'processing';
      if (state.status === 'paused_for_user_input') return 'active';
      if (state.status === 'error') return 'error';
    }
    
    if (isPhaseComplete(phase)) return 'completed';
    if (canNavigateToPhase(phase)) return 'available';
    return 'disabled';
  };
  
  const getPhaseIcon = (phase: AssessmentPhase, status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'active':
        return <Clock className="h-5 w-5 text-blue-600" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };
  
  const handlePhaseNavigation = async (phase: AssessmentPhase, route: string) => {
    if (!canNavigateToPhase(phase)) return;
    
    try {
      await navigateToPhase(phase);
      await router.push(`/assessment/${flowId}/${route}`);
    } catch (error) {
      console.error('Navigation failed:', error);
    }
  };
  
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <Sidebar className="w-80 border-r border-gray-200 bg-white">
        <SidebarHeader className="p-6 border-b border-gray-200">
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Assessment Flow
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {state.selectedApplicationIds.length} applications selected
              </p>
            </div>
            
            {/* Overall Progress */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">
                  Overall Progress
                </span>
                <span className="text-sm text-gray-600">
                  {state.progress}%
                </span>
              </div>
              <Progress value={state.progress} className="h-2" />
            </div>
            
            {/* Status Badge */}
            <div className="flex items-center space-x-2">
              <Badge 
                variant={
                  state.status === 'completed' ? 'success' :
                  state.status === 'error' ? 'destructive' :
                  state.status === 'processing' ? 'default' : 'secondary'
                }
              >
                {state.status.replace('_', ' ').toUpperCase()}
              </Badge>
              
              {state.appsReadyForPlanning.length > 0 && (
                <Badge variant="outline">
                  {state.appsReadyForPlanning.length} ready for planning
                </Badge>
              )}
            </div>
          </div>
        </SidebarHeader>
        
        <SidebarContent className="p-4">
          <SidebarMenu>
            {PHASE_CONFIG.map((phase, index) => {
              const status = getPhaseStatus(phase.id);
              const isCurrentPhase = state.currentPhase === phase.id;
              const canNavigate = canNavigateToPhase(phase.id);
              
              return (
                <SidebarMenuItem key={phase.id}>
                  <SidebarMenuButton
                    onClick={() => canNavigate && handlePhaseNavigation(phase.id, phase.route)}
                    className={cn(
                      "w-full p-4 rounded-lg transition-all duration-200",
                      isCurrentPhase && "bg-blue-50 border-2 border-blue-200",
                      canNavigate && !isCurrentPhase && "hover:bg-gray-50",
                      !canNavigate && "opacity-50 cursor-not-allowed"
                    )}
                    disabled={!canNavigate}
                  >
                    <div className="flex items-start space-x-3 w-full">
                      {/* Phase Number & Icon */}
                      <div className="flex-shrink-0 flex flex-col items-center">
                        <div className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium",
                          status === 'completed' && "bg-green-100 text-green-700",
                          status === 'active' && "bg-blue-100 text-blue-700", 
                          status === 'processing' && "bg-blue-100 text-blue-700",
                          status === 'error' && "bg-red-100 text-red-700",
                          status === 'available' && "bg-gray-100 text-gray-600",
                          status === 'disabled' && "bg-gray-50 text-gray-400"
                        )}>
                          {getPhaseIcon(phase.id, status)}
                        </div>
                        
                        {/* Connector Line */}
                        {index < PHASE_CONFIG.length - 1 && (
                          <div className={cn(
                            "w-0.5 h-8 mt-2",
                            isPhaseComplete(phase.id) ? "bg-green-300" : "bg-gray-200"
                          )} />
                        )}
                      </div>
                      
                      {/* Phase Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h3 className={cn(
                            "font-medium truncate",
                            isCurrentPhase ? "text-blue-900" : "text-gray-900"
                          )}>
                            {phase.title}
                          </h3>
                          
                          {canNavigate && (
                            <ChevronRight className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                        
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {phase.description}
                        </p>
                        
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-500">
                            {phase.estimatedTime}
                          </span>
                          
                          {status === 'completed' && (
                            <span className="text-xs text-green-600 font-medium">
                              Complete
                            </span>
                          )}
                          
                          {status === 'processing' && (
                            <span className="text-xs text-blue-600 font-medium">
                              Processing...
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </SidebarContent>
        
        {/* Footer Actions */}
        <div className="p-4 border-t border-gray-200 space-y-3">
          {state.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{state.error}</p>
            </div>
          )}
          
          {state.status === 'paused_for_user_input' && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-600">
                Waiting for your input to continue...
              </p>
            </div>
          )}
          
          {state.status === 'completed' && (
            <Button 
              className="w-full" 
              onClick={() => router.push(`/planning`)}
            >
              Continue to Planning
            </Button>
          )}
        </div>
      </Sidebar>
      
      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="h-full">
          {children}
        </div>
      </main>
      
      {/* Real-time Updates Overlay */}
      {state.agentUpdates.length > 0 && state.status === 'processing' && (
        <div className="fixed bottom-4 right-4 max-w-sm">
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
              <span className="text-sm font-medium text-gray-900">
                AI Agents Working...
              </span>
            </div>
            
            <div className="space-y-1">
              {state.agentUpdates.slice(-3).map((update, index) => (
                <p key={index} className="text-xs text-gray-600">
                  {update.message}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

**Acceptance Criteria**:
- [ ] Left sidebar with phase navigation
- [ ] Progress visualization and completion status
- [ ] Real-time status updates and visual feedback
- [ ] Responsive design for different screen sizes
- [ ] Integration with flow state management
- [ ] Error states and user guidance
- [ ] Phase accessibility and navigation controls

---

### FE-003: Create Architecture Standards Capture Page
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 14 hours  
**Dependencies**: FE-001, FE-002  
**Sprint**: Frontend Week 7-8  

**Description**: Implement the architecture standards capture interface with RBAC controls and template support

**Location**: `src/pages/assessment/[flowId]/architecture.tsx`

**Technical Requirements**:
- Form-based interface for architecture standards capture
- Template selection and customization capabilities
- Application-specific override management
- RBAC-based field access control
- Real-time validation and preview
- Integration with assessment flow state

**Page Implementation Summary**:
```typescript
import React, { useState, useEffect } from 'react';
import { GetServerSideProps } from 'next';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ArchitectureStandardsForm } from '@/components/assessment/ArchitectureStandardsForm';
import { TemplateSelector } from '@/components/assessment/TemplateSelector';
import { ApplicationOverrides } from '@/components/assessment/ApplicationOverrides';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';

interface ArchitecturePageProps {
  flowId: string;
}

const ArchitecturePage: React.FC<ArchitecturePageProps> = ({ flowId }) => {
  const {
    state,
    updateArchitectureStandards,
    resumeFlow
  } = useAssessmentFlow(flowId);
  
  const [standards, setStandards] = useState(state.engagementStandards);
  const [overrides, setOverrides] = useState(state.applicationOverrides);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await updateArchitectureStandards(standards, overrides);
      await resumeFlow({ standards, overrides });
    } catch (error) {
      console.error('Failed to submit architecture standards:', error);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <AssessmentFlowLayout flowId={flowId}>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            Architecture Standards
          </h1>
          <p className="text-gray-600">
            Define engagement-level architecture minimums and application-specific exceptions
          </p>
        </div>
        
        <TemplateSelector 
          onTemplateSelect={(template) => setStandards(template.standards)}
        />
        
        <ArchitectureStandardsForm
          standards={standards}
          onChange={setStandards}
        />
        
        <ApplicationOverrides
          applications={state.selectedApplicationIds}
          overrides={overrides}
          onChange={setOverrides}
        />
        
        <div className="flex justify-end space-x-4">
          <Button 
            variant="outline" 
            onClick={() => {/* Save draft */}}
          >
            Save Draft
          </Button>
          <Button 
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Processing...' : 'Continue to Tech Debt Analysis'}
          </Button>
        </div>
      </div>
    </AssessmentFlowLayout>
  );
};

export const getServerSideProps: GetServerSideProps = async (context) => {
  return {
    props: {
      flowId: context.params?.flowId as string
    }
  };
};

export default ArchitecturePage;
```

**Acceptance Criteria**:
- [ ] Architecture standards capture form with validation
- [ ] Template selection and customization
- [ ] Application-specific override management
- [ ] RBAC-based access controls
- [ ] Real-time validation and save functionality
- [ ] Integration with flow resumption

---

### FE-004: Create Tech Debt Analysis Review Page
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 16 hours  
**Dependencies**: FE-001, FE-002  
**Sprint**: Frontend Week 8  

**Description**: Implement tech debt analysis review interface with component identification and user modification capabilities

**Location**: `src/pages/assessment/[flowId]/tech-debt.tsx`

**Technical Requirements**:
- Component identification display and editing
- Tech debt analysis visualization and modification
- Severity-based filtering and prioritization
- Application-level and component-level views
- Real-time agent progress updates
- User override and feedback mechanisms

**Page Implementation Summary**:
```typescript
// Implementation includes:
// - ComponentIdentificationPanel
// - TechDebtAnalysisGrid  
// - SeverityFilter
// - ApplicationTabs
// - RealTimeProgressIndicator
// - UserModificationForm
```

**Acceptance Criteria**:
- [ ] Component identification display and editing
- [ ] Tech debt visualization with severity indicators
- [ ] Application and component-level navigation
- [ ] Real-time agent progress tracking
- [ ] User modification and override capabilities

---

### FE-005: Create 6R Strategy Review Page
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 18 hours  
**Dependencies**: FE-001, FE-002  
**Sprint**: Frontend Week 8  

**Description**: Implement 6R strategy review interface with component-level treatments and compatibility validation

**Location**: `src/pages/assessment/[flowId]/sixr-review.tsx`

**Technical Requirements**:
- Component-level 6R strategy display and modification
- Compatibility validation between component treatments
- Confidence scoring and rationale presentation
- Application rollup visualization (highest modernization)
- Bulk editing and pattern application
- Move group hint display and validation

**Page Implementation Summary**:
```typescript
// Implementation includes:
// - SixRStrategyMatrix
// - ComponentTreatmentEditor
// - CompatibilityValidator
// - ConfidenceScoreIndicator
// - ApplicationRollupView
// - MoveGroupHintsPanel
// - BulkEditingControls
```

**Acceptance Criteria**:
- [ ] Component-level 6R strategy management
- [ ] Compatibility validation and issue highlighting
- [ ] Application rollup with strategy hierarchy
- [ ] Move group hints and planning integration
- [ ] Bulk editing and pattern application capabilities

---

### FE-006: Create App-on-Page Comprehensive View
**Status**: 🔴 Not Started  
**Priority**: P1 - High  
**Effort**: 20 hours  
**Dependencies**: FE-001, FE-002, FE-005  
**Sprint**: Frontend Week 8  

**Description**: Implement comprehensive app-on-page view for final assessment review and approval

**Location**: `src/pages/assessment/[flowId]/app-on-page.tsx`

**Technical Requirements**:
- Single-page comprehensive application view
- All assessment data consolidation and presentation
- Interactive editing and approval workflow
- Export and sharing capabilities
- Print-friendly layout design
- Integration with final assessment approval

**Page Implementation Summary**:
```typescript
// Implementation includes:
// - ApplicationSummaryCard
// - ComponentBreakdownView
// - TechDebtSummaryChart
// - SixRDecisionRationale
// - ArchitectureExceptionsPanel
// - DependencyVisualization
// - BusinessImpactAssessment
// - ExportAndSharingControls
```

**Acceptance Criteria**:
- [ ] Comprehensive single-page application view
- [ ] All assessment data consolidation
- [ ] Interactive editing and approval workflow
- [ ] Export and print-friendly capabilities
- [ ] Final assessment validation and approval

---

## 🎨 UI Component Tasks

### UI-001: Create Assessment-Specific UI Components
**Status**: 🔴 Not Started  
**Priority**: P2 - Medium  
**Effort**: 12 hours  
**Dependencies**: FE-001  
**Sprint**: Frontend Week 8  

**Description**: Build reusable UI components specific to assessment flow functionality

**Location**: `src/components/assessment/`

**Components Required**:
- TechDebtScoreIndicator
- SixRStrategyBadge
- ComponentArchitectureCard
- CompatibilityStatusIndicator
- ArchitectureStandardsSelector
- ApplicationOverrideForm
- MoveGroupHintsList
- AssessmentProgressBar

**Implementation Summary for Key Components**:
```typescript
// TechDebtScoreIndicator.tsx
export const TechDebtScoreIndicator: React.FC<{
  score: number;
  breakdown?: Record<string, number>;
  size?: 'sm' | 'md' | 'lg';
}> = ({ score, breakdown, size = 'md' }) => {
  // Visual score indicator with color coding and breakdown tooltip
};

// SixRStrategyBadge.tsx  
export const SixRStrategyBadge: React.FC<{
  strategy: string;
  confidence?: number;
  interactive?: boolean;
  onChange?: (strategy: string) => void;
}> = ({ strategy, confidence, interactive, onChange }) => {
  // Color-coded strategy badge with confidence indicator
};

// ComponentArchitectureCard.tsx
export const ComponentArchitectureCard: React.FC<{
  component: ApplicationComponent;
  techDebt?: TechDebtItem[];
  treatment?: ComponentTreatment;
  onEdit?: (component: ApplicationComponent) => void;
}> = ({ component, techDebt, treatment, onEdit }) => {
  // Comprehensive component display with tech debt and treatment
};
```

**Acceptance Criteria**:
- [ ] Complete set of assessment-specific UI components
- [ ] Consistent design language and styling
- [ ] Interactive capabilities where appropriate
- [ ] Accessibility and responsive design
- [ ] Integration with main assessment pages

---

## Next Steps

After completing these frontend tasks, proceed to:
1. **Testing & DevOps Tasks** (Document 05)

## Dependencies Map

- **FE-001** (Assessment Flow Hook) is foundational for all other frontend tasks
- **FE-002** (Navigation Layout) depends on **FE-001**
- **FE-003** through **FE-006** (Page Components) depend on **FE-001** and **FE-002**
- **UI-001** (UI Components) depends on **FE-001** and supports **FE-003** through **FE-006**

All frontend tasks depend on completing the API tasks (Document 03) first.