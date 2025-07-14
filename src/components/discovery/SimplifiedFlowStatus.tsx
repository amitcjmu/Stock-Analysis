import React from 'react';
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
import { useDiscoveryFlowStatusVisual } from '@/hooks/discovery/useDiscoveryFlowStatus';

interface SimplifiedFlowStatusProps {
  flow_id: string;
  onNavigateToMapping?: () => void;
}

export const SimplifiedFlowStatus: React.FC<SimplifiedFlowStatusProps> = ({
  flow_id,
  onNavigateToMapping
}) => {
  // Use the consolidated hook for visual updates (5 second polling)
  const { data: flowStatus, isLoading: loading, error } = useDiscoveryFlowStatusVisual(flow_id);

  const getStatusDisplay = () => {
    if (!flowStatus) return null;

    const { status, currentPhase, progress, awaitingUserApproval } = flowStatus;
    const current_phase = currentPhase || flowStatus.current_phase || flowStatus.phase;
    const progress_percentage = progress ?? flowStatus.progress_percentage ?? flowStatus.progress ?? 0;
    const awaiting_user_approval = awaitingUserApproval || flowStatus.awaiting_user_approval;

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
          {error?.message || 'Unable to load flow status'}
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
            {Math.round(progress_percentage || 0)}% Complete
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
            <span className="text-sm">{current_phase?.replace(/_/g, ' ') || 'Unknown'}</span>
          </div>
          <p className="text-sm text-gray-600 mt-2">{description}</p>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Overall Progress</span>
            <span>{Math.round(progress_percentage || 0)}%</span>
          </div>
          <Progress value={progress_percentage || 0} className="w-full" />
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
          Last updated: {flowStatus.lastUpdated ? new Date(flowStatus.lastUpdated).toLocaleTimeString() : 'N/A'}
        </div>
      </CardContent>
    </Card>
  );
};