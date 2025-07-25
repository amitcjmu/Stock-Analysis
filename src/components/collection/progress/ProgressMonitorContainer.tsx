/**
 * Progress Monitor Container Component
 *
 * Container component that orchestrates all progress monitoring components.
 * Extracted from Progress.tsx to create a more organized, modular structure.
 */

import React from 'react';
import { RefreshCw, Download } from 'lucide-react';

// Import modular progress components
import FlowMetricsGrid from './FlowMetricsGrid'
import type { FlowMetrics } from './FlowMetricsGrid'
import FlowListSidebar from './FlowListSidebar'
import type { CollectionFlow } from './FlowListSidebar'
import FlowDetailsCard from './FlowDetailsCard';
import { ProgressTracker } from '@/components/collection/ProgressTracker';

// Import types
import type { ProgressMilestone } from '@/components/collection/types';

// UI Components
import { Button } from '@/components/ui/button';

export interface ProgressMonitorContainerProps {
  flows: CollectionFlow[];
  metrics: FlowMetrics | null;
  selectedFlow: string | null;
  autoRefresh: boolean;
  onFlowSelect: (flowId: string) => void;
  onFlowAction: (flowId: string, action: 'pause' | 'resume' | 'stop') => Promise<void>;
  onToggleAutoRefresh: () => void;
  onExportReport: () => void;
  getFlowMilestones: (flow: CollectionFlow) => ProgressMilestone[];
  className?: string;
}

export const ProgressMonitorContainer: React.FC<ProgressMonitorContainerProps> = ({
  flows,
  metrics,
  selectedFlow,
  autoRefresh,
  onFlowSelect,
  onFlowAction,
  onToggleAutoRefresh,
  onExportReport,
  getFlowMilestones,
  className = ''
}) => {
  const selectedFlowData = flows.find(f => f.id === selectedFlow);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Actions */}
      <div className="flex justify-end items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleAutoRefresh}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
          {autoRefresh ? 'Auto-Refresh On' : 'Auto-Refresh Off'}
        </Button>
        <Button
          variant="outline"
          onClick={onExportReport}
        >
          <Download className="h-4 w-4 mr-2" />
          Export Report
        </Button>
      </div>

      {/* Metrics Overview */}
      {metrics && (
        <FlowMetricsGrid metrics={metrics} />
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Flow List Sidebar */}
        <FlowListSidebar
          flows={flows}
          selectedFlow={selectedFlow}
          onFlowSelect={onFlowSelect}
        />

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {selectedFlowData ? (
            <>
              {/* Flow Details */}
              <FlowDetailsCard
                flow={selectedFlowData}
                onFlowAction={onFlowAction}
              />

              {/* Progress Tracker */}
              <ProgressTracker
                formId={selectedFlowData.id}
                totalSections={getFlowMilestones(selectedFlowData).length}
                completedSections={getFlowMilestones(selectedFlowData).filter(m => m.achieved).length}
                overallCompletion={selectedFlowData.progress}
                confidenceScore={85}
                milestones={getFlowMilestones(selectedFlowData)}
                timeSpent={Date.now() - new Date(selectedFlowData.startedAt).getTime()}
                estimatedTimeRemaining={
                  selectedFlowData.estimatedCompletion
                    ? new Date(selectedFlowData.estimatedCompletion).getTime() - Date.now()
                    : 0
                }
              />
            </>
          ) : (
            <div className="flex items-center justify-center min-h-64 border-2 border-dashed border-muted-foreground/25 rounded-lg">
              <div className="text-center">
                <p className="text-muted-foreground">Select a flow to view details</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Choose a collection flow from the sidebar to monitor its progress
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProgressMonitorContainer;
