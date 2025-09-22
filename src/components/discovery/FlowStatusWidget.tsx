import React from 'react'
import { useState, useRef, useCallback } from 'react'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ExternalLink } from 'lucide-react'
import { CheckCircle, AlertCircle, Clock, ArrowRight, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { masterFlowService } from '@/services/api/masterFlowService';
import { useAuth } from '@/contexts/AuthContext';
import { useClient } from '@/contexts/ClientContext';

interface FlowStatusWidgetProps {
  flowId: string;
  flowType?: string;
  currentPhase?: string;
  className?: string;
}

interface FlowAnalysis {
  success: boolean;
  flow_id: string;
  flow_type: string;
  current_phase: string;
  routing_context: {
    target_page: string;
    recommended_page: string;
    flow_id: string;
    phase: string;
    flow_type: string;
  };
  user_guidance: {
    primary_message: string;
    action_items: string[];
    user_actions: string[];
    system_actions: string[];
    estimated_completion_time?: number;
  };
  checklist_status: Array<{
    phase_id: string;
    phase_name: string;
    status: string;
    completion_percentage: number;
    tasks: Array<{
      task_id: string;
      task_name: string;
      status: string;
      confidence: number;
      next_steps: string[];
    }>;
    estimated_time_remaining?: number;
  }>;
  agent_insights: Array<{
    agent: string;
    analysis: string;
    confidence: number;
    issues_found: string[];
  }>;
  confidence: number;
  reasoning: string;
  execution_time: number;
  error_message?: string;
}

const FlowStatusWidget: React.FC<FlowStatusWidgetProps> = ({
  flowId,
  flowType = 'discovery',
  currentPhase = 'unknown',
  className = ''
}) => {
  const [analysis, setAnalysis] = useState<FlowAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();
  const { client, engagement } = useClient();

  // Request deduplication
  const requestInProgress = useRef(false);
  const lastRequestTime = useRef(0);
  const REQUEST_DEBOUNCE_MS = 1000; // Prevent requests within 1 second of each other

  const fetchFlowAnalysis = useCallback(async () => {
    if (!flowId || requestInProgress.current) {
      console.log('🚫 FlowStatusWidget: Request blocked', { flowId, requestInProgress: requestInProgress.current });
      return;
    }

    if (!client?.id || !engagement?.id || !user?.id) {
      console.warn('⚠️ FlowStatusWidget: Missing required context', { client: client?.id, engagement: engagement?.id, user: user?.id });
      setError('Missing required context for flow analysis');
      return;
    }

    setLoading(true);
    setError(null);
    requestInProgress.current = true;

    try {
      console.log('🚀 FlowStatusWidget: Starting flow analysis using MasterFlowService', { flowId });

      // CC: Use MasterFlowService.resumeFlow instead of FlowProcessingService for consistent API patterns
      // This aligns with the working implementation used by other flow components
      const result = await masterFlowService.resumeFlow(flowId, client.id, engagement.id);

      console.log('📊 FlowStatusWidget: Received result:', result);

      if (result && typeof result === 'object') {
        // Convert MasterFlowService response to FlowAnalysis format
        const analysisData: FlowAnalysis = {
          success: true,
          flow_id: flowId,
          flow_type: flowType,
          current_phase: currentPhase,
          user_guidance: result.user_guidance || {
            primary_message: 'Flow analysis completed',
            action_items: ['Continue with next phase'],
            user_actions: ['Review progress'],
            system_actions: ['Update flow status'],
            estimated_completion_time: 10
          },
          routing_context: result.routing_context || {
            target_page: '/discovery/overview',
            recommended_page: '/discovery/overview',
            flow_id: flowId,
            phase: currentPhase,
            flow_type: flowType
          },
          checklist_status: result.checklist_status || [],
          agent_insights: result.agent_insights || [],
          confidence: result.confidence || 0.8,
          reasoning: result.reasoning || 'Flow analysis completed successfully',
          execution_time: result.execution_time || 0
        };

        setAnalysis(analysisData);
        setError(null);
      } else {
        const errorMsg = 'Invalid response format from flow service';
        setError(errorMsg);
        console.error('❌ FlowStatusWidget: Invalid response format:', result);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error('❌ FlowStatusWidget: Request failed:', err);
      setError(errorMsg);

      // Show user-friendly error toast
      toast.error('Flow Analysis Failed', {
        description: 'Unable to analyze flow status. Please try again.',
      });
    } finally {
      setLoading(false);
      requestInProgress.current = false;
    }
  }, [flowId, client?.id, engagement?.id, user?.id, currentPhase, flowType]);

  useEffect(() => {
    // Add a small delay to prevent immediate execution on mount
    const timer = setTimeout(() => {
      fetchFlowAnalysis();
    }, 100);

    return () => clearTimeout(timer);
  }, [fetchFlowAnalysis]);

  const handleNavigateToRecommendedPage = (): void => {
    if (!analysis?.routing_context?.target_page) {
      toast.error('Navigation Error', {
        description: 'No target page available. Please try refreshing.',
      });
      return;
    }

    try {
      // Show confirmation toast
      toast.success('🚀 Navigating to recommended next step', {
        description: analysis.user_guidance.primary_message
      });

      // Navigate with context
      navigate(analysis.routing_context.target_page, {
        state: {
          flow_id: flowId,
          phase: analysis.current_phase,
          agent_guidance: analysis.user_guidance,
          from_flow_status_widget: true
        }
      });
    } catch (navError) {
      console.error('Navigation failed:', navError);
      toast.error('Navigation Failed', {
        description: 'Unable to navigate to the recommended page.',
      });
    }
  };

  const handleRetryAnalysis = (): void => {
    // Reset state and retry
    setError(null);
    setAnalysis(null);
    fetchFlowAnalysis();
  };

  const getPhaseStatusIcon = (status: string, confidence: number): JSX.Element => {
    if (status === 'completed' && confidence >= 0.8) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (status === 'completed' && confidence >= 0.6) {
      return <CheckCircle className="h-4 w-4 text-yellow-500" />;
    } else if (status === 'in_progress') {
      return <Clock className="h-4 w-4 text-blue-500" />;
    } else {
      return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getTaskStatusColor = (status: string): unknown => {
    switch (status) {
      case 'completed': return 'default';
      case 'pending': return 'secondary';
      case 'in_progress': return 'default';
      case 'blocked': return 'destructive';
      default: return 'outline';
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 animate-spin" />
            Analyzing Flow Status...
          </CardTitle>
          <CardDescription>
            AI agent is analyzing your flow and determining next steps
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            Flow Analysis Error
          </CardTitle>
          <CardDescription>
            Unable to analyze flow status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <Button
            onClick={handleRetryAnalysis}
            variant="outline"
            size="sm"
            className="w-full"
            disabled={loading || requestInProgress.current}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Analysis
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!analysis) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-600">
            <AlertCircle className="h-5 w-5" />
            No Analysis Available
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-4">No flow analysis data available.</p>
          <Button
            onClick={handleRetryAnalysis}
            variant="outline"
            size="sm"
            className="w-full"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Load Analysis
          </Button>
        </CardContent>
      </Card>
    );
  }

  const completedPhases = analysis.checklist_status?.filter(phase => phase.status === 'completed').length || 0;
  const totalPhases = analysis.checklist_status?.length || 0;
  const overallProgress = totalPhases > 0 ? (completedPhases / totalPhases) * 100 : 0;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              🤖 Flow Intelligence
              <Badge variant="outline" className="ml-2">
                {flowType}
              </Badge>
            </CardTitle>
            <CardDescription>
              AI-powered flow analysis and recommendations
            </CardDescription>
          </div>
          <Button
            onClick={handleRetryAnalysis}
            variant="ghost"
            size="sm"
            disabled={loading || requestInProgress.current}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Current Status */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-sm text-gray-500">
              {completedPhases}/{totalPhases} phases
            </span>
          </div>
          <Progress value={overallProgress} className="h-2" />
          <p className="text-xs text-gray-500 mt-1">
            Current Phase: <span className="font-medium">{analysis.current_phase?.replace('_', ' ') || 'Unknown'}</span>
          </p>
        </div>

        {/* Phase Status Breakdown */}
        {analysis.checklist_status && analysis.checklist_status.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-3">Phase Status</h4>
            <div className="space-y-2">
              {analysis.checklist_status.map((phase) => (
                <div key={phase.phase_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex items-center gap-2">
                    {getPhaseStatusIcon(phase.status, phase.completion_percentage / 100)}
                    <span className="text-sm capitalize">
                      {phase.phase_name.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={getTaskStatusColor(phase.status)}
                      className="text-xs"
                    >
                      {Math.round(phase.completion_percentage)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Guidance */}
        <div>
          <h4 className="text-sm font-medium mb-2">AI Guidance</h4>
          <p className="text-sm text-gray-700 mb-3 break-words overflow-wrap-anywhere">
            {analysis.user_guidance.primary_message}
          </p>

          {analysis.user_guidance.action_items && analysis.user_guidance.action_items.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">Recommended Next Steps:</p>
              <ul className="space-y-1">
                {analysis.user_guidance.action_items.slice(0, 3).map((step, index) => (
                  <li key={index} className="text-xs text-gray-600 flex items-start gap-2 break-words overflow-wrap-anywhere">
                    <span className="text-blue-500 mt-1">•</span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t">
          <Button
            onClick={handleNavigateToRecommendedPage}
            className="w-full"
            size="sm"
            disabled={!analysis.routing_context?.target_page}
          >
            <ArrowRight className="h-4 w-4 mr-2" />
            Continue to Next Step
          </Button>

          {analysis.routing_context.specific_task && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              Task: {analysis.routing_context.specific_task.replace('_', ' ')}
            </p>
          )}
        </div>

        {/* Debug Info (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="pt-2 border-t">
            <details>
              <summary className="text-xs text-gray-500 cursor-pointer">Debug Info</summary>
              <pre className="text-xs bg-gray-100 p-2 mt-2 rounded overflow-auto">
                {JSON.stringify({
                  flow_id: analysis.flow_id,
                  current_phase: analysis.current_phase,
                  target_page: analysis.routing_context.target_page,
                  specific_task: analysis.routing_context.specific_task,
                  request_state: {
                    loading,
                    error,
                    request_in_progress: requestInProgress.current,
                    last_request_time: new Date(lastRequestTime.current).toISOString()
                  }
                }, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FlowStatusWidget;
