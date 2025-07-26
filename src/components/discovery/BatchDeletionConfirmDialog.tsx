import React from 'react';
import { FileText, Server } from 'lucide-react'
import { AlertTriangle, Database, Clock, Users, TrendingDown } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { IncompleteFlow } from '@/hooks/discovery/useIncompleteFlowDetection';

interface BatchDeletionConfirmDialogProps {
  flowCount: number;
  flows: IncompleteFlow[];
  onConfirm: () => void;
  onCancel: () => void;
}

export const BatchDeletionConfirmDialog: React.FC<BatchDeletionConfirmDialogProps> = ({
  flowCount,
  flows,
  onConfirm,
  onCancel
}) => {
  const getPhaseDisplayName = (phase: string): any => {
    const names = {
      'field_mapping': 'Field Mapping',
      'data_cleansing': 'Data Cleansing',
      'asset_inventory': 'Asset Inventory',
      'dependency_analysis': 'Dependency Analysis',
      'tech_debt_analysis': 'Tech Debt Analysis'
    };
    return names[phase as keyof typeof names] || phase.replace('_', ' ').toUpperCase();
  };

  const getAggregatedImpact = (): JSX.Element => {
    const aggregated: Record<string, number> = {};
    let totalInsights = 0;
    let estimatedTotalTime = 0;

    flows.forEach(flow => {
      // Aggregate data deletion counts with safety checks
      if (flow.deletion_impact?.data_to_delete) {
        Object.entries(flow.deletion_impact.data_to_delete).forEach(([key, count]) => {
          if (typeof count === 'number') {
            aggregated[key] = (aggregated[key] || 0) + count;
          }
        });
      }

      // Count total insights with safety check
      totalInsights += flow.agent_insights?.length || 0;

      // Estimate total cleanup time (rough approximation in seconds) with safety checks
      const timeStr = flow.deletion_impact?.estimated_cleanup_time || '30s';
      if (timeStr.includes('s')) {
        estimatedTotalTime += parseInt(timeStr.replace('s', '')) || 0;
      } else if (timeStr.includes('m')) {
        estimatedTotalTime += (parseInt(timeStr.replace('m', '')) || 0) * 60;
      }
    });

    return {
      aggregatedData: aggregated,
      totalInsights,
      estimatedTotalTime: estimatedTotalTime > 60
        ? `${Math.ceil(estimatedTotalTime / 60)}m`
        : `${estimatedTotalTime}s`
    };
  };

  const { aggregatedData, totalInsights, estimatedTotalTime } = getAggregatedImpact();
  const totalDataRecords = Object.values(aggregatedData).reduce((sum, count) => sum + count, 0);

  const getPhaseDistribution = (): JSX.Element => {
    const distribution: Record<string, number> = {};
    flows.forEach(flow => {
      distribution[flow.current_phase] = (distribution[flow.current_phase] || 0) + 1;
    });
    return distribution;
  };

  const getStatusDistribution = (): JSX.Element => {
    const distribution: Record<string, number> = {};
    flows.forEach(flow => {
      distribution[flow.status] = (distribution[flow.status] || 0) + 1;
    });
    return distribution;
  };

  const phaseDistribution = getPhaseDistribution();
  const statusDistribution = getStatusDistribution();

  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <span>Batch Delete Discovery Flows</span>
          </DialogTitle>
          <DialogDescription>
            This action will permanently delete {flowCount} discovery flows and all their associated data.
            This cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh]">
          <div className="space-y-4 pr-4">
            {/* Overview Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-red-50 border border-red-200 p-3 rounded-lg text-center">
                <TrendingDown className="h-6 w-6 text-red-600 mx-auto mb-1" />
                <p className="text-2xl font-bold text-red-800">{flowCount}</p>
                <p className="text-xs text-red-600">Flows to Delete</p>
              </div>
              <div className="bg-orange-50 border border-orange-200 p-3 rounded-lg text-center">
                <Database className="h-6 w-6 text-orange-600 mx-auto mb-1" />
                <p className="text-2xl font-bold text-orange-800">{totalDataRecords}</p>
                <p className="text-xs text-orange-600">Data Records</p>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg text-center">
                <Users className="h-6 w-6 text-yellow-600 mx-auto mb-1" />
                <p className="text-2xl font-bold text-yellow-800">{totalInsights}</p>
                <p className="text-xs text-yellow-600">Agent Insights</p>
              </div>
              <div className="bg-purple-50 border border-purple-200 p-3 rounded-lg text-center">
                <Clock className="h-6 w-6 text-purple-600 mx-auto mb-1" />
                <p className="text-2xl font-bold text-purple-800">{estimatedTotalTime}</p>
                <p className="text-xs text-purple-600">Cleanup Time</p>
              </div>
            </div>

            {/* Phase and Status Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-3">Flows by Phase</h3>
                <div className="space-y-2">
                  {Object.entries(phaseDistribution).map(([phase, count]) => (
                    <div key={phase} className="flex items-center justify-between">
                      <span className="text-sm capitalize">{getPhaseDisplayName(phase)}</span>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-3">Flows by Status</h3>
                <div className="space-y-2">
                  {Object.entries(statusDistribution).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <span className="text-sm capitalize">{status}</span>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Aggregated Deletion Impact */}
            <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
              <h3 className="font-semibold text-red-800 mb-3 flex items-center">
                <Database className="h-4 w-4 mr-2" />
                Aggregated Deletion Impact
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(aggregatedData).map(([key, count]) => {
                  if (count === 0) return null;

                  const icons = {
                    workflow_state: FileText,
                    import_sessions: Server,
                    field_mappings: FileText,
                    assets: Database,
                    dependencies: Users,
                    shared_memory_refs: Server
                  };

                  const Icon = icons[key as keyof typeof icons] || Database;

                  return (
                    <div key={key} className="flex items-center space-x-2">
                      <Icon className="h-4 w-4 text-red-600" />
                      <div>
                        <p className="text-xs text-red-600 capitalize">
                          {key.replace('_', ' ')}
                        </p>
                        <p className="font-semibold text-red-800">{count}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Flow List Preview */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold mb-3">Flows to be Deleted</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {flows.map((flow, idx) => (
                  <div key={flow.flow_id || `batch-flow-${idx}`} className="flex items-center justify-between text-sm bg-white p-2 rounded border">
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-500">#{idx + 1}</span>
                      <span className="font-mono text-xs">{flow.flow_id?.substring(0, 8) || 'unknown'}...</span>
                      <span className="capitalize">{getPhaseDisplayName(flow.current_phase)}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="text-xs">
                        {flow.status}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {Math.round(flow.progress_percentage)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Agent Insights Summary */}
            {totalInsights > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                <h3 className="font-semibold text-yellow-800 mb-2 flex items-center">
                  <Users className="h-4 w-4 mr-2" />
                  Agent Insights Will Be Lost
                </h3>
                <p className="text-sm text-yellow-700">
                  A total of <strong>{totalInsights} agent insights</strong> across all flows will be permanently deleted.
                  These insights contain valuable AI-generated analysis and recommendations that cannot be recovered.
                </p>
              </div>
            )}

            {/* Critical Warning */}
            <Alert className="border-red-200 bg-red-50">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                <strong>Critical Warning:</strong> This batch deletion is permanent and cannot be undone.
                All {flowCount} flows, their progress, agent insights, and {totalDataRecords} associated data records will be lost forever.
                Consider resuming flows individually if you want to continue any discovery processes.
              </AlertDescription>
            </Alert>
          </div>
        </ScrollArea>

        <Separator />

        <DialogFooter className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            <strong>{flowCount}</strong> flows • <strong>{totalDataRecords}</strong> records •
            <strong>{totalInsights}</strong> insights will be permanently deleted
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={onConfirm}>
              <AlertTriangle className="h-4 w-4 mr-2" />
              Delete All {flowCount} Flows
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
