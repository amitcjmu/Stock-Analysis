/**
 * Progress Monitor Container Component
 *
 * Redesigned container with enhanced UI for better flow monitoring.
 * Features searchable flow list, tabbed details, and phase timeline visualization.
 */

import React from 'react';
import { RefreshCw, Download, ChevronUp, ChevronDown } from 'lucide-react';

// Import redesigned progress components
import FlowMetricsGrid from './FlowMetricsGrid';
import type { FlowMetrics } from './FlowMetricsGrid';
import EnhancedFlowList from './EnhancedFlowList';
import type { CollectionFlow } from './EnhancedFlowList';
import TabbedFlowDetails from './TabbedFlowDetails';
import type { PhaseInfo } from './PhaseTimeline';

// Import types
import type { ProgressMilestone } from '@/components/collection/types';

// UI Components
import { Button } from '@/components/ui/button';

export interface ProgressMonitorContainerProps {
  flows: CollectionFlow[];
  metrics: FlowMetrics | null;
  selectedFlow: string | null;
  autoRefresh: boolean;
  readiness?: {
    apps_ready_for_assessment: number;
    phase_scores: { collection: number; discovery: number };
    quality: { collection_quality_score: number; confidence_score: number };
  } | null;
  onFlowSelect: (flowId: string) => void;
  onFlowAction: (flowId: string, action: 'pause' | 'resume' | 'stop') => Promise<void>;
  onToggleAutoRefresh: () => void;
  onExportReport: () => void;
  getFlowMilestones: (flow: CollectionFlow) => ProgressMilestone[];
  onContinue?: () => Promise<void>;
  onDelete?: () => Promise<void>;
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
  readiness,
  onContinue,
  onDelete,
  className = ''
}) => {
  const [showMetrics, setShowMetrics] = React.useState(true);
  const selectedFlowData = flows.find(f => f.id === selectedFlow);

  // Convert flow phases to PhaseInfo format
  const flowPhases: PhaseInfo[] = selectedFlowData?.current_phase
    ? [
        {
          id: selectedFlowData.current_phase,
          name: selectedFlowData.current_phase,
          display_name: selectedFlowData.current_phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          description: '',
          status: 'current' as const
        }
      ]
    : [];

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header Actions */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Collection Progress Monitor</h1>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onToggleAutoRefresh}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-Refresh On' : 'Auto-Refresh Off'}
          </Button>
          <Button variant="outline" size="sm" onClick={onExportReport}>
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Collapsible Metrics Overview */}
      {metrics && (
        <div className="space-y-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowMetrics(!showMetrics)}
            className="w-full justify-between hover:bg-muted/50"
          >
            <span className="text-sm font-medium">Overview Metrics</span>
            {showMetrics ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
          {showMetrics && <FlowMetricsGrid metrics={metrics} />}
        </div>
      )}

      {/* Main Content Grid - Enhanced Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Enhanced Flow List (Left Panel) */}
        <div className="lg:col-span-1">
          <EnhancedFlowList
            flows={flows}
            selectedFlow={selectedFlow}
            onFlowSelect={onFlowSelect}
          />
        </div>

        {/* Tabbed Flow Details (Main Panel) */}
        <div className="lg:col-span-2">
          {selectedFlowData ? (
            <TabbedFlowDetails
              flow={selectedFlowData}
              phases={flowPhases}
              milestones={getFlowMilestones(selectedFlowData)}
              readiness={readiness}
              onFlowAction={onFlowAction}
              onContinue={onContinue}
              onDelete={onDelete}
            />
          ) : (
            <div className="flex items-center justify-center min-h-[600px] border-2 border-dashed border-muted-foreground/25 rounded-lg bg-muted/20">
              <div className="text-center p-8">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-lg font-medium mb-2">No Flow Selected</h3>
                <p className="text-muted-foreground max-w-sm">
                  Select a collection flow from the left panel to view detailed progress information, timeline, and actions.
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
