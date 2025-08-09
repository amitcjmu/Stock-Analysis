/**
 * Flow Details Card Component
 *
 * Displays detailed information and controls for a selected collection flow.
 * Extracted from Progress.tsx to create a focused, reusable component.
 */

import React from 'react';
import { Play, Pause, Square, ArrowRight, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useNavigate } from 'react-router-dom';

export interface CollectionFlow {
  id: string;
  name: string;
  type: 'adaptive' | 'bulk' | 'integration';
  status: 'running' | 'paused' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  completedAt?: string;
  estimatedCompletion?: string;
  applicationCount: number;
  completedApplications: number;
}

export interface FlowDetailsCardProps {
  flow: CollectionFlow;
  onFlowAction: (flowId: string, action: 'pause' | 'resume' | 'stop') => Promise<void>;
  className?: string;
  readiness?: {
    apps_ready_for_assessment: number;
    phase_scores: { collection: number; discovery: number };
    quality: { collection_quality_score: number; confidence_score: number };
  } | null;
}

export const FlowDetailsCard: React.FC<FlowDetailsCardProps> = ({
  flow,
  onFlowAction,
  className = '',
  readiness
}) => {
  const navigate = useNavigate();

  const handleAction = async (action: 'pause' | 'resume' | 'stop'): void => {
    await onFlowAction(flow.id, action);
  };

  const handleContinue = (): void => {
    // Navigate to adaptive forms page with the flow ID
    navigate(`/collection/adaptive-forms?flowId=${flow.id}`);
  };

  // Check if flow is stuck (running but with 0% progress)
  const isFlowStuck = flow.status === 'running' && flow.progress === 0;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="line-clamp-2">{flow.name}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Started: {new Date(flow.startedAt).toLocaleString()}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {/* Continue button for stuck flows */}
            {isFlowStuck && (
              <Button
                variant="default"
                size="sm"
                onClick={handleContinue}
                title="Continue Flow"
              >
                <ArrowRight className="h-4 w-4 mr-1" />
                Continue
              </Button>
            )}

            {flow.status === 'running' && !isFlowStuck && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('pause')}
                title="Pause Flow"
              >
                <Pause className="h-4 w-4" />
              </Button>
            )}

            {flow.status === 'paused' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('resume')}
                title="Resume Flow"
              >
                <Play className="h-4 w-4" />
              </Button>
            )}

            {(flow.status === 'running' || flow.status === 'paused') && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('stop')}
                title="Stop Flow"
              >
                <Square className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">Progress</span>
              <span className="text-muted-foreground">{Math.round(flow.progress)}%</span>
            </div>
            <Progress value={flow.progress} className="h-3" />
          </div>

          {/* Flow Details Grid */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div>
                <span className="text-muted-foreground">Applications:</span>
                <div className="font-medium">
                  {flow.completedApplications} / {flow.applicationCount}
                  <span className="text-xs text-muted-foreground ml-1">
                    ({Math.round((flow.completedApplications / flow.applicationCount) * 100)}%)
                  </span>
                </div>
              </div>

              <div>
                <span className="text-muted-foreground">Type:</span>
                <div className="font-medium capitalize">{flow.type}</div>
              </div>
            </div>

            <div className="space-y-2">
              <div>
                <span className="text-muted-foreground">Status:</span>
                <div className={`font-medium capitalize ${
                  flow.status === 'running' ? 'text-blue-600' :
                  flow.status === 'completed' ? 'text-green-600' :
                  flow.status === 'failed' ? 'text-red-600' :
                  'text-yellow-600'
                }`}>
                  {flow.status}
                </div>
              </div>

              {flow.estimatedCompletion && flow.status === 'running' && (
                <div>
                  <span className="text-muted-foreground">ETA:</span>
                  <div className="font-medium text-xs">
                    {new Date(flow.estimatedCompletion).toLocaleString()}
                  </div>
                </div>
              )}

              {flow.completedAt && (
                <div>
                  <span className="text-muted-foreground">Completed:</span>
                  <div className="font-medium text-xs">
                    {new Date(flow.completedAt).toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Additional Status Information */}
          {readiness && (
            <div className="mt-2 p-3 bg-muted/30 border rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="text-muted-foreground">Apps Ready</span>
                  <div className="font-medium">{readiness.apps_ready_for_assessment}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Collection Score</span>
                  <div className="font-medium">{Math.round(readiness.phase_scores.collection * 100)}%</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Discovery Score</span>
                  <div className="font-medium">{Math.round(readiness.phase_scores.discovery * 100)}%</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Quality / Confidence</span>
                  <div className="font-medium">{readiness.quality.collection_quality_score || 0} / {readiness.quality.confidence_score || 0}</div>
                </div>
              </div>
            </div>
          )}
          {isFlowStuck && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start space-x-2">
                <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-amber-800 font-medium">
                    Flow appears to be stuck
                  </p>
                  <p className="text-sm text-amber-700 mt-1">
                    The flow is not making progress. Click "Continue" to proceed with the data collection process.
                  </p>
                </div>
              </div>
            </div>
          )}

          {flow.status === 'failed' && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                Flow execution failed. Check logs for detailed error information.
              </p>
            </div>
          )}

          {flow.status === 'paused' && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                Flow is currently paused. Resume to continue processing.
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default FlowDetailsCard;
