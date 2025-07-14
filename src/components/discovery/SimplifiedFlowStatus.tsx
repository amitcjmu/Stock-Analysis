import React, { useEffect, useState } from 'react';
import { 
  Activity, 
  CheckCircle, 
  Clock, 
  Loader2,
  XCircle,
  AlertCircle,
  ArrowRight,
  Pause
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { masterFlowService } from '@/services/api/masterFlowService';
import { useAuth } from '@/contexts/AuthContext';

interface SimplifiedFlowStatusProps {
  flow_id: string;
  onNavigateToMapping?: () => void;
}

interface FlowStatus {
  flow_id: string;
  status: string;
  current_phase: string;
  progress_percentage: number;
  awaiting_user_approval: boolean;
  phase_completion: Record<string, boolean>;
  agent_insights: any[];
  last_updated: string;
}

export const SimplifiedFlowStatus: React.FC<SimplifiedFlowStatusProps> = ({
  flow_id,
  onNavigateToMapping
}) => {
  const { client, engagement } = useAuth();
  const [flowStatus, setFlowStatus] = useState<FlowStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      // Use proper UUIDs from auth context with demo fallbacks
      const clientAccountId = client?.id || "11111111-1111-1111-1111-111111111111";
      const engagementId = engagement?.id || "22222222-2222-2222-2222-222222222222";
      
      const response = await masterFlowService.getFlowStatus(flow_id, clientAccountId, engagementId);
      setFlowStatus(response as any);
      setError(null);
    } catch (err) {
      setError('Failed to fetch flow status');
      console.error('Error fetching flow status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (flow_id) {
      fetchStatus();
    }
  }, [flow_id]);

  // Separate effect for polling to avoid recreation on status changes
  useEffect(() => {
    if (!flow_id || !flowStatus) return;
    
    // Only poll if actually processing - not if waiting for approval, completed, or paused
    const shouldPoll = 
      (flowStatus.status === 'running' || flowStatus.status === 'processing' || flowStatus.status === 'active') &&
      !flowStatus.awaiting_user_approval &&
      flowStatus.status !== 'waiting_for_approval' &&
      flowStatus.status !== 'completed' &&
      flowStatus.status !== 'failed' &&
      flowStatus.status !== 'paused' &&
      // Stop polling if in field_mapping phase (usually means waiting for approval)
      !(flowStatus.current_phase === 'field_mapping' && flowStatus.progress_percentage > 10);
    
    if (shouldPoll) {
      const interval = setInterval(() => {
        fetchStatus();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [flow_id]); // Only depend on flow_id, not on flowStatus

  const getStatusDisplay = () => {
    if (!flowStatus) return null;

    const { status, current_phase, progress_percentage, awaiting_user_approval } = flowStatus;

    // Determine display properties
    let icon = Activity;
    let iconColor = 'text-blue-600';
    let bgColor = 'bg-blue-50 border-blue-200';
    let statusText = 'Processing';
    let description = '';
    let showAction = false;

    if (status === 'completed') {
      icon = CheckCircle;
      iconColor = 'text-green-600';
      bgColor = 'bg-green-50 border-green-200';
      statusText = 'Completed';
      description = 'Discovery flow completed successfully';
    } else if (status === 'failed' || status === 'error') {
      icon = XCircle;
      iconColor = 'text-red-600';
      bgColor = 'bg-red-50 border-red-200';
      statusText = 'Failed';
      description = 'An error occurred during processing';
    } else if (status === 'paused') {
      icon = Pause;
      iconColor = 'text-yellow-600';
      bgColor = 'bg-yellow-50 border-yellow-200';
      statusText = 'Paused';
      description = 'Flow is paused. Resume to continue processing.';
    } else if (status === 'waiting_for_approval' || awaiting_user_approval || 
               (current_phase === 'field_mapping' && progress_percentage > 10)) {
      icon = Pause;
      iconColor = 'text-orange-600';
      bgColor = 'bg-orange-50 border-orange-200';
      statusText = 'Waiting for Approval';
      description = 'Field mapping suggestions ready. Please review and approve to continue.';
      showAction = true;
    } else if (status === 'running' || status === 'processing' || status === 'active') {
      icon = Loader2;
      iconColor = 'text-blue-600 animate-spin';
      bgColor = 'bg-blue-50 border-blue-200';
      statusText = 'Processing';
      description = `Currently in ${current_phase?.replace(/_/g, ' ') || 'processing'} phase`;
    } else {
      icon = Clock;
      iconColor = 'text-gray-600';
      bgColor = 'bg-gray-50 border-gray-200';
      statusText = 'Initializing';
      description = 'Flow is being initialized';
    }

    const Icon = icon;

    return {
      Icon,
      iconColor,
      bgColor,
      statusText,
      description,
      showAction
    };
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2">Loading flow status...</span>
        </CardContent>
      </Card>
    );
  }

  if (error || !flowStatus) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800">
          {error || 'Unable to load flow status'}
        </AlertDescription>
      </Alert>
    );
  }

  const display = getStatusDisplay();
  if (!display) return null;

  const { Icon, iconColor, bgColor, statusText, description, showAction } = display;

  return (
    <Card className={`${bgColor}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${iconColor}`} />
            Discovery Flow Status
          </div>
          <Badge variant="outline">
            {Math.round(flowStatus.progress_percentage || 0)}% Complete
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Summary */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Status:</span>
            <span className="text-sm">{statusText}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Current Phase:</span>
            <span className="text-sm">{flowStatus.current_phase?.replace(/_/g, ' ') || 'Unknown'}</span>
          </div>
          <p className="text-sm text-gray-600 mt-2">{description}</p>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Overall Progress</span>
            <span>{Math.round(flowStatus.progress_percentage || 0)}%</span>
          </div>
          <Progress value={flowStatus.progress_percentage || 0} className="w-full" />
        </div>

        {/* Phase Completion */}
        <div className="space-y-2">
          <span className="text-sm font-medium">Phases Completed:</span>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {Object.entries(flowStatus.phase_completion || {}).map(([phase, completed]) => (
              <div key={phase} className="flex items-center gap-2">
                {completed ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <Clock className="h-4 w-4 text-gray-400" />
                )}
                <span className={completed ? 'text-green-700' : 'text-gray-500'}>
                  {phase.replace(/_/g, ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Action Button */}
        {showAction && onNavigateToMapping && (
          <div className="pt-4 border-t">
            <Button 
              className="w-full"
              onClick={onNavigateToMapping}
            >
              <ArrowRight className="h-4 w-4 mr-2" />
              Review Field Mappings
            </Button>
          </div>
        )}

        {/* Last Updated */}
        <div className="text-xs text-gray-500 text-right">
          Last updated: {new Date(flowStatus.last_updated).toLocaleTimeString()}
        </div>
      </CardContent>
    </Card>
  );
};