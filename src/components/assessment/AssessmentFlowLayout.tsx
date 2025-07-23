import React from 'react';
import type { useParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { ChevronRight } from 'lucide-react'
import { CheckCircle2, Circle, Clock, AlertCircle, Loader2 } from 'lucide-react'
import type { AssessmentPhase } from '@/hooks/useAssessmentFlow'
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow'
import { cn } from '@/lib/utils';

import MainSidebar from '../Sidebar';
import ContextBreadcrumbs from '../context/ContextBreadcrumbs';
import AgentClarificationPanel from '../discovery/AgentClarificationPanel';
import AgentInsightsSection from '../discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../discovery/AgentPlanningDashboard';

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
    description: 'Identify and analyze technical debt across applications',
    route: 'tech-debt',
    icon: ({ className }) => <AlertCircle className={className} />,
    estimatedTime: '20-40 min'
  },
  {
    id: 'component_sixr_strategies',
    title: '6R Strategy Review',
    description: 'Review and approve component-level migration strategies',
    route: 'sixr-review',
    icon: ({ className }) => <CheckCircle2 className={className} />,
    estimatedTime: '30-60 min'
  },
  {
    id: 'app_on_page_generation',
    title: 'Application Summary',
    description: 'Generate comprehensive application summaries',
    route: 'app-on-page',
    icon: ({ className }) => <Circle className={className} />,
    estimatedTime: '10-20 min'
  },
  {
    id: 'finalization',
    title: 'Summary & Export',
    description: 'Review assessment and export to planning',
    route: 'summary',
    icon: ({ className }) => <CheckCircle2 className={className} />,
    estimatedTime: '5-10 min'
  }
];

export const AssessmentFlowLayout: React.FC<AssessmentFlowLayoutProps> = ({ 
  children, 
  flowId 
}) => {
  const navigate = useNavigate();
  const { state, navigateToPhase } = useAssessmentFlow(flowId);
  
  const getPhaseStatus = (phaseId: AssessmentPhase) => {
    if (state.error) return 'error';
    if (state.currentPhase === phaseId) {
      return state.status === 'processing' ? 'processing' : 'active';
    }
    // Simple phase completion logic - can be enhanced
    const phaseOrder = ['architecture_minimums', 'tech_debt_analysis', 'component_sixr_strategies', 'app_on_page_generation', 'finalization'];
    const currentIndex = phaseOrder.indexOf(state.currentPhase);
    const phaseIndex = phaseOrder.indexOf(phaseId);
    
    if (phaseIndex < currentIndex) return 'completed';
    if (phaseIndex === currentIndex) return 'active';
    return 'disabled';
  };

  const isPhaseComplete = (phaseId: AssessmentPhase) => {
    return getPhaseStatus(phaseId) === 'completed';
  };

  const canNavigateToPhase = (phaseId: AssessmentPhase) => {
    const status = getPhaseStatus(phaseId);
    return status === 'completed' || status === 'active' || status === 'processing';
  };

  const getPhaseIcon = (phaseId: AssessmentPhase, status: string) => {
    if (status === 'completed') return <CheckCircle2 className="h-4 w-4" />;
    if (status === 'processing') return <Loader2 className="h-4 w-4 animate-spin" />;
    if (status === 'error') return <AlertCircle className="h-4 w-4" />;
    
    const phase = PHASE_CONFIG.find(p => p.id === phaseId);
    const IconComponent = phase?.icon || Circle;
    return <IconComponent className="h-4 w-4" />;
  };

  const handlePhaseNavigation = async (phase: AssessmentPhase, route: string) => {
    if (!canNavigateToPhase(phase)) return;
    
    try {
      await navigateToPhase(phase);
      await navigate(`/assessment/${flowId}/${route}`);
    } catch (error) {
      console.error('Navigation failed:', error);
    }
  };
  
  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <MainSidebar />
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Assessment Flow Progress Header */}
          <div className="mb-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    Assessment Flow Progress
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {state.selectedApplicationIds?.length || 0} applications • {state.currentPhase?.replace('_', ' ') || 'Unknown phase'}
                  </p>
                </div>
                
                <Badge 
                  variant={
                    state.status === 'completed' ? 'default' :
                    state.status === 'error' ? 'destructive' :
                    state.status === 'processing' ? 'default' : 'secondary'
                  }
                >
                  {state.status?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
                </Badge>
              </div>
              
              {/* Overall Progress */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">
                    Overall Progress
                  </span>
                  <span className="text-sm text-gray-600">
                    {state.progress || 0}%
                  </span>
                </div>
                <Progress value={state.progress || 0} className="h-2" />
              </div>
              
              {/* Phase Navigation */}
              <div className="mt-4 flex flex-wrap gap-2">
                {PHASE_CONFIG.map((phase) => {
                  const status = getPhaseStatus(phase.id);
                  const isCurrentPhase = state.currentPhase === phase.id;
                  const canNavigate = canNavigateToPhase(phase.id);
                  
                  return (
                    <Button
                      key={phase.id}
                      variant={isCurrentPhase ? "default" : "outline"}
                      size="sm"
                      onClick={() => handlePhaseNavigation(phase.id, phase.route)}
                      disabled={!canNavigate}
                      className={cn(
                        "flex items-center space-x-2",
                        status === 'completed' && "border-green-300 text-green-700"
                      )}
                    >
                      {getPhaseIcon(phase.id, status)}
                      <span>{phase.title}</span>
                    </Button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 space-y-6">
              {/* Status Alerts */}
              {state.error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="h-5 w-5 text-red-600" />
                    <p className="text-sm text-red-600">{state.error}</p>
                  </div>
                </div>
              )}
              
              {state.status === 'paused_for_user_input' && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-5 w-5 text-blue-600" />
                    <p className="text-sm text-blue-600">
                      Waiting for your input to continue...
                    </p>
                  </div>
                </div>
              )}

              {/* Main Content */}
              {children}
            </div>

            <div className="xl:col-span-1 space-y-6">
              {/* Agent Communication Panel */}
              <AgentClarificationPanel 
                pageContext={`assessment-${state.currentPhase || 'unknown'}`}
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Assessment question answered:', questionId, response);
                }}
              />

              {/* Agent Insights */}
              <AgentInsightsSection 
                pageContext={`assessment-${state.currentPhase || 'unknown'}`}
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Assessment insight action:', insightId, action);
                }}
              />

              {/* Agent Planning Dashboard */}
              <AgentPlanningDashboard pageContext={`assessment-${state.currentPhase || 'unknown'}`} />
              
              {/* Real-time Agent Updates */}
              {state.agentUpdates?.length > 0 && state.status === 'processing' && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                    <span className="text-sm font-medium text-gray-900">
                      AI Agents Working...
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    {state.agentUpdates.slice(-3).map((update, index) => (
                      <p key={index} className="text-xs text-gray-600 p-2 bg-gray-50 rounded">
                        {update.message}
                      </p>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Continue to Planning */}
              {state.status === 'completed' && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <Button 
                    className="w-full" 
                    onClick={() => navigate(`/planning`)}
                  >
                    Continue to Planning
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentFlowLayout;