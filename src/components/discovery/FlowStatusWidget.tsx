import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, AlertCircle, Clock, ArrowRight, RefreshCw, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { flowProcessingService } from '@/services/flowProcessingService';
import { useAuth } from '@/contexts/AuthContext';
import { useClient } from '@/contexts/ClientContext';

interface FlowStatusWidgetProps {
  flowId: string;
  flowType?: string;
  currentPhase?: string;
  className?: string;
}

interface FlowAnalysis {
  flow_id: string;
  flow_type: string;
  current_phase: string;
  progress_percentage: number;
  phase_completion_status: {
    [phase: string]: {
      completed: boolean;
      confidence: number;
      missing_requirements?: string[];
      completion_evidence?: string[];
    };
  };
  routing_decision: {
    recommended_page: string;
    reasoning: string;
    specific_task?: string;
    urgency_level: 'low' | 'medium' | 'high';
  };
  user_guidance: {
    summary: string;
    next_steps: string[];
    estimated_time_to_complete?: string;
    blockers?: string[];
  };
  success: boolean;
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

  const fetchFlowAnalysis = async () => {
    if (!flowId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      console.log('🔍 Fetching flow analysis for:', flowId);
      
      const result = await flowProcessingService.processContinuation(flowId, {
        client_account_id: client?.id,
        engagement_id: engagement?.id,
        user_id: user?.id
      });
      
      if (result.success) {
        setAnalysis(result as FlowAnalysis);
      } else {
        setError(result.error_message || 'Failed to analyze flow');
      }
    } catch (err) {
      console.error('Flow analysis error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlowAnalysis();
  }, [flowId]);

  const handleNavigateToRecommendedPage = () => {
    if (!analysis?.routing_decision?.recommended_page) return;
    
    // Show confirmation toast
    toast.success('🚀 Navigating to recommended next step', {
      description: analysis.routing_decision.reasoning
    });
    
    // Navigate with context
    navigate(analysis.routing_decision.recommended_page, {
      state: {
        flow_id: flowId,
        phase: analysis.current_phase,
        agent_guidance: analysis.user_guidance,
        from_flow_status_widget: true
      }
    });
  };

  const getPhaseStatusIcon = (completed: boolean, confidence: number) => {
    if (completed && confidence >= 0.8) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (completed && confidence >= 0.6) {
      return <CheckCircle className="h-4 w-4 text-yellow-500" />;
    } else {
      return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
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
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <Button 
            onClick={fetchFlowAnalysis} 
            variant="outline" 
            size="sm"
            className="w-full"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Analysis
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!analysis) {
    return null;
  }

  const completedPhases = Object.values(analysis.phase_completion_status || {})
    .filter(phase => phase.completed).length;
  const totalPhases = Object.keys(analysis.phase_completion_status || {}).length;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              🤖 Flow Intelligence
              <Badge variant="outline" className="ml-2">
                {analysis.flow_type}
              </Badge>
            </CardTitle>
            <CardDescription>
              AI-powered flow analysis and recommendations
            </CardDescription>
          </div>
          <Button
            onClick={fetchFlowAnalysis}
            variant="ghost"
            size="sm"
          >
            <RefreshCw className="h-4 w-4" />
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
          <Progress value={analysis.progress_percentage} className="h-2" />
          <p className="text-xs text-gray-500 mt-1">
            Current Phase: <span className="font-medium">{analysis.current_phase}</span>
          </p>
        </div>

        {/* Phase Status Breakdown */}
        {analysis.phase_completion_status && (
          <div>
            <h4 className="text-sm font-medium mb-3">Phase Status</h4>
            <div className="space-y-2">
              {Object.entries(analysis.phase_completion_status).map(([phase, status]) => (
                <div key={phase} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex items-center gap-2">
                    {getPhaseStatusIcon(status.completed, status.confidence)}
                    <span className="text-sm capitalize">
                      {phase.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge 
                      variant={status.completed ? "default" : "secondary"}
                      className="text-xs"
                    >
                      {Math.round(status.confidence * 100)}%
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
          <p className="text-sm text-gray-700 mb-3">
            {analysis.user_guidance.summary}
          </p>
          
          {analysis.user_guidance.next_steps && analysis.user_guidance.next_steps.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">Recommended Next Steps:</p>
              <ul className="space-y-1">
                {analysis.user_guidance.next_steps.slice(0, 3).map((step, index) => (
                  <li key={index} className="text-xs text-gray-600 flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Blockers */}
        {analysis.user_guidance.blockers && analysis.user_guidance.blockers.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-2 text-orange-600">⚠️ Blockers</h4>
            <ul className="space-y-1">
              {analysis.user_guidance.blockers.map((blocker, index) => (
                <li key={index} className="text-xs text-orange-700 flex items-start gap-2">
                  <span className="text-orange-500 mt-1">•</span>
                  {blocker}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommended Action */}
        {analysis.routing_decision && (
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium">Recommended Action</h4>
              <Badge variant={getUrgencyColor(analysis.routing_decision.urgency_level)}>
                {analysis.routing_decision.urgency_level} priority
              </Badge>
            </div>
            
            <p className="text-sm text-gray-700 mb-3">
              {analysis.routing_decision.reasoning}
            </p>
            
            {analysis.routing_decision.specific_task && (
              <p className="text-xs text-blue-600 mb-3">
                <strong>Specific Task:</strong> {analysis.routing_decision.specific_task}
              </p>
            )}

            <Button 
              onClick={handleNavigateToRecommendedPage}
              className="w-full"
              variant="default"
            >
              <ArrowRight className="h-4 w-4 mr-2" />
              Go to Recommended Page
              <ExternalLink className="h-3 w-3 ml-2" />
            </Button>
          </div>
        )}

        {/* Time Estimate */}
        {analysis.user_guidance.estimated_time_to_complete && (
          <div className="text-xs text-gray-500 text-center border-t pt-2">
            Estimated time to complete: {analysis.user_guidance.estimated_time_to_complete}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FlowStatusWidget; 