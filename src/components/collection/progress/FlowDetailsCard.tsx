/**
 * Flow Details Card Component
 * 
 * Displays detailed information and controls for a selected collection flow.
 * Extracted from Progress.tsx to create a focused, reusable component.
 */

import React from 'react';
import { Play, Pause, Square } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

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
}

export const FlowDetailsCard: React.FC<FlowDetailsCardProps> = ({
  flow,
  onFlowAction,
  className = ''
}) => {
  const handleAction = async (action: 'pause' | 'resume' | 'stop') => {
    await onFlowAction(flow.id, action);
  };

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
            {flow.status === 'running' && (
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