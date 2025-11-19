/**
 * Tabbed Flow Details Component
 *
 * Unified flow details view with tabs for Overview, Timeline, Progress, and Actions
 */

import React, { useState } from 'react';
import {
  LayoutGrid,
  GitCommitHorizontal,
  TrendingUp,
  Settings,
  Play,
  Pause,
  Square,
  Trash2,
  ArrowRight,
  Loader2
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

// Import existing components
import PhaseTimeline from './PhaseTimeline';
import type { PhaseInfo } from './PhaseTimeline';
// CC: ProgressTracker commented out - too complex and not updating properly with section-based generation
// import { ProgressTracker } from '@/components/collection/ProgressTracker';
import type { ProgressMilestone } from '@/components/collection/types';

export interface CollectionFlow {
  id: string;
  name: string;
  type: 'adaptive' | 'bulk' | 'integration';
  status: 'running' | 'paused' | 'completed' | 'failed';
  progress: number;
  started_at: string;
  completed_at?: string;
  estimated_completion?: string;
  application_count: number;
  completed_applications: number;
  current_phase?: string;
}

export interface TabbedFlowDetailsProps {
  flow: CollectionFlow;
  phases?: PhaseInfo[];
  milestones: ProgressMilestone[];
  readiness?: {
    apps_ready_for_assessment: number;
    phase_scores: { collection: number; discovery: number };
    quality: { collection_quality_score: number; confidence_score: number };
  } | null;
  onFlowAction: (flowId: string, action: 'pause' | 'resume' | 'stop') => Promise<void>;
  onContinue?: () => Promise<void>;
  onDelete?: () => Promise<void>;
  className?: string;
}

export const TabbedFlowDetails: React.FC<TabbedFlowDetailsProps> = ({
  flow,
  phases = [],
  milestones,
  readiness,
  onFlowAction,
  onContinue,
  onDelete,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAction = async (action: 'pause' | 'resume' | 'stop') => {
    setIsProcessing(true);
    try {
      await onFlowAction(flow.id, action);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleContinue = async () => {
    if (!onContinue) return;
    setIsProcessing(true);
    try {
      await onContinue();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async () => {
    if (!onDelete) return;
    setIsProcessing(true);
    try {
      await onDelete();
    } finally {
      setIsProcessing(false);
    }
  };

  const isFlowStuck = flow.status === 'running' && flow.progress === 0;
  const isCompleted = flow.status === 'completed' || flow.progress === 100;

  return (
    <Card className={className}>
      {/* Header with Actions */}
      <div className="border-b bg-muted/30 p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold line-clamp-2 mb-1">{flow.name}</h2>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <Badge variant="outline" className="capitalize">
                {flow.type}
              </Badge>
              <Badge
                className={
                  flow.status === 'running'
                    ? 'bg-blue-500'
                    : flow.status === 'completed'
                    ? 'bg-green-500'
                    : flow.status === 'failed'
                    ? 'bg-red-500'
                    : 'bg-yellow-500'
                }
              >
                Status: {flow.status}
              </Badge>
              {flow.current_phase && (
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-300">
                  Phase: {flow.current_phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Badge>
              )}
              <span className="text-muted-foreground">Started: {new Date(flow.started_at).toLocaleString()}</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {/* Continue/View Progress button - always show for running or completed flows */}
            {(flow.status === 'running' || isCompleted) && onContinue && (
              <Button
                variant="default"
                size="sm"
                onClick={handleContinue}
                disabled={isProcessing}
                title={isCompleted ? "Continue to Assessment" : "View Current Phase"}
              >
                {isProcessing ? (
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                ) : (
                  <ArrowRight className="h-4 w-4 mr-1" />
                )}
                {isCompleted ? "Continue" : "View Progress"}
              </Button>
            )}

            {/* Pause button - show for all running flows */}
            {flow.status === 'running' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('pause')}
                disabled={isProcessing}
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
                disabled={isProcessing}
              >
                <Play className="h-4 w-4" />
              </Button>
            )}

            {(flow.status === 'running' || flow.status === 'paused') && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('stop')}
                disabled={isProcessing}
              >
                <Square className="h-4 w-4" />
              </Button>
            )}

            {(flow.status === 'failed' || flow.status === 'completed' || flow.status === 'paused') && onDelete && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDelete}
                disabled={isProcessing}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">Overall Progress</span>
            <span className="font-medium">{Math.round(flow.progress)}%</span>
          </div>
          <Progress value={flow.progress} className="h-2" />
        </div>
      </div>

      {/* Tabbed Content */}
      <CardContent className="p-0">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full justify-start rounded-none border-b bg-transparent p-0">
            <TabsTrigger
              value="overview"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              <LayoutGrid className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger
              value="timeline"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              <GitCommitHorizontal className="h-4 w-4 mr-2" />
              Timeline
            </TabsTrigger>
            <TabsTrigger
              value="progress"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              Progress
            </TabsTrigger>
            <TabsTrigger
              value="details"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              <Settings className="h-4 w-4 mr-2" />
              Details
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="p-6 space-y-4">
            {/* Flow Status Summary */}
            <div className="p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50">
              <h3 className="font-semibold text-sm mb-3 text-gray-700">Flow Status</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Lifecycle Status</p>
                  <Badge
                    className={
                      flow.status === 'running'
                        ? 'bg-blue-500'
                        : flow.status === 'completed'
                        ? 'bg-green-500'
                        : flow.status === 'failed'
                        ? 'bg-red-500'
                        : 'bg-yellow-500'
                    }
                  >
                    {flow.status.toUpperCase()}
                  </Badge>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Current Phase</p>
                  {flow.current_phase ? (
                    <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-300">
                      {flow.current_phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Badge>
                  ) : (
                    <span className="text-xs text-muted-foreground">Not Started</span>
                  )}
                </div>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 border rounded-lg bg-muted/30">
                <p className="text-xs text-muted-foreground">Applications</p>
                <p className="text-2xl font-bold">
                  {flow.completed_applications}/{flow.application_count}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {Math.round((flow.completed_applications / flow.application_count) * 100)}% complete
                </p>
              </div>

              <div className="p-3 border rounded-lg bg-muted/30">
                <p className="text-xs text-muted-foreground">Progress</p>
                <p className="text-2xl font-bold">{Math.round(flow.progress)}%</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {100 - Math.round(flow.progress)}% remaining
                </p>
              </div>

              {readiness && (
                <>
                  <div className="p-3 border rounded-lg bg-muted/30">
                    <p className="text-xs text-muted-foreground">Quality Score</p>
                    <p className="text-2xl font-bold">
                      {readiness.quality.collection_quality_score || 0}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Data quality
                    </p>
                  </div>

                  <div className="p-3 border rounded-lg bg-muted/30">
                    <p className="text-xs text-muted-foreground">Confidence</p>
                    <p className="text-2xl font-bold">
                      {readiness.quality.confidence_score || 0}%
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Analysis confidence
                    </p>
                  </div>
                </>
              )}
            </div>

            {/* Readiness Info */}
            {readiness && (
              <div className="p-4 border rounded-lg bg-blue-50/50">
                <h3 className="font-medium text-sm mb-3">Collection Readiness</h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Apps Ready:</span>
                    <span className="ml-2 font-medium">
                      {readiness.apps_ready_for_assessment}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Collection Score:</span>
                    <span className="ml-2 font-medium">
                      {Math.round(readiness.phase_scores.collection * 100)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Discovery Score:</span>
                    <span className="ml-2 font-medium">
                      {Math.round(readiness.phase_scores.discovery * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Status Messages */}
            {isFlowStuck && (
              <div className="p-4 border border-amber-200 bg-amber-50 rounded-lg">
                <p className="text-sm font-medium text-amber-900">Flow Appears Stuck</p>
                <p className="text-sm text-amber-700 mt-1">
                  The flow is not making progress. Click "Continue" to proceed.
                </p>
              </div>
            )}

            {isCompleted && (
              <div className="p-4 border border-green-200 bg-green-50 rounded-lg">
                <p className="text-sm font-medium text-green-900">Collection Complete</p>
                <p className="text-sm text-green-700 mt-1">
                  {readiness &&
                  readiness.apps_ready_for_assessment > 0 &&
                  readiness.quality.collection_quality_score >= 60
                    ? 'Ready to proceed to assessment phase.'
                    : 'Review collected data before proceeding.'}
                </p>
              </div>
            )}
          </TabsContent>

          {/* Timeline Tab */}
          <TabsContent value="timeline" className="p-6">
            <PhaseTimeline phases={phases} currentPhase={flow.current_phase} />
          </TabsContent>

          {/* Progress Tab - COMMENTED OUT (ProgressTracker too complex) */}
          <TabsContent value="progress" className="p-6 flex justify-center">
            {/* CC: ProgressTracker commented out - too complex and not updating properly */}
            {/* <ProgressTracker
              formId={flow.id}
              totalSections={milestones.length}
              completedSections={milestones.filter(m => m.achieved).length}
              overallCompletion={flow.progress}
              confidenceScore={(readiness?.quality?.confidence_score || 0) / 100}
              milestones={milestones}
              timeSpent={flow.started_at ? Date.now() - new Date(flow.started_at).getTime() : 0}
              estimatedTimeRemaining={
                flow.estimated_completion
                  ? Math.max(0, new Date(flow.estimated_completion).getTime() - Date.now())
                  : 0
              }
            /> */}
            <div className="text-center text-muted-foreground">
              <p>Progress tracking temporarily disabled</p>
              <p className="text-sm mt-2">Use the Overview tab to monitor flow progress</p>
            </div>
          </TabsContent>

          {/* Details Tab */}
          <TabsContent value="details" className="p-6 space-y-4">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Flow ID:</span>
                  <p className="font-mono text-xs mt-1 break-all">{flow.id}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Type:</span>
                  <p className="mt-1 capitalize">{flow.type}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <p className="mt-1 capitalize">{flow.status}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Current Phase:</span>
                  <p className="mt-1 capitalize">
                    {flow.current_phase?.replace(/_/g, ' ') || 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Started:</span>
                  <p className="mt-1 text-xs">{new Date(flow.started_at).toLocaleString()}</p>
                </div>
                {flow.completed_at && (
                  <div>
                    <span className="text-muted-foreground">Completed:</span>
                    <p className="mt-1 text-xs">
                      {new Date(flow.completed_at).toLocaleString()}
                    </p>
                  </div>
                )}
                {flow.estimated_completion && (
                  <div>
                    <span className="text-muted-foreground">Estimated Completion:</span>
                    <p className="mt-1 text-xs">
                      {new Date(flow.estimated_completion).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default TabbedFlowDetails;
