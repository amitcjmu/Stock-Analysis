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
                  state.status === 'completed' ? 'default' :
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