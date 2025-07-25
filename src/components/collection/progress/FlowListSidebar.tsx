/**
 * Flow List Sidebar Component
 *
 * Displays a list of collection flows in a sidebar layout with selection capability.
 * Extracted from Progress.tsx to create a focused, reusable component.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

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

export interface FlowListSidebarProps {
  flows: CollectionFlow[];
  selectedFlow: string | null;
  onFlowSelect: (flowId: string) => void;
  className?: string;
}

/**
 * Get status badge for flow status
 */
const getStatusBadge = (status: CollectionFlow['status']) => {
  switch (status) {
    case 'running':
      return <Badge variant="default">Running</Badge>;
    case 'paused':
      return <Badge variant="secondary">Paused</Badge>;
    case 'completed':
      return <Badge variant="outline">Completed</Badge>;
    case 'failed':
      return <Badge variant="destructive">Failed</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
};

export const FlowListSidebar: React.FC<FlowListSidebarProps> = ({
  flows,
  selectedFlow,
  onFlowSelect,
  className = ''
}) => {
  return (
    <div className={`lg:col-span-1 ${className}`}>
      <Card>
        <CardHeader>
          <CardTitle>Active Flows</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {flows.map((flow) => (
            <div
              key={flow.id}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedFlow === flow.id
                  ? 'border-primary bg-primary/5'
                  : 'hover:bg-muted/50'
              }`}
              onClick={() => onFlowSelect(flow.id)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm line-clamp-2">{flow.name}</span>
                {getStatusBadge(flow.status)}
              </div>

              <Progress value={flow.progress} className="h-2 mb-2" />

              <div className="text-xs text-muted-foreground">
                {flow.completedApplications}/{flow.applicationCount} apps ({Math.round(flow.progress)}%)
              </div>

              <div className="text-xs text-muted-foreground mt-1 capitalize">
                Type: {flow.type}
              </div>
            </div>
          ))}

          {flows.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <p className="text-sm">No active collection flows</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default FlowListSidebar;
