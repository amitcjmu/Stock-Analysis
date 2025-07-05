import React from 'react';
import { AlertTriangle, Database, Clock, FileText, Users, Server } from 'lucide-react';
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
// Simple flow interface that matches the actual API response
interface SimpleFlow {
  flow_id: string;
  status: string;
  current_phase?: string;
  progress_percentage?: number;
  created_at: string;
  updated_at: string;
  flow_name?: string;
  agent_insights?: any[];
  deletion_impact?: {
    data_to_delete: Record<string, number>;
    estimated_cleanup_time: string;
  };
  session_id?: string;
}

interface FlowDeletionConfirmDialogProps {
  flow: SimpleFlow;
  onConfirm: () => void;
  onCancel: () => void;
}

export const FlowDeletionConfirmDialog: React.FC<FlowDeletionConfirmDialogProps> = ({
  flow,
  onConfirm,
  onCancel
}) => {
  const getPhaseDisplayName = (phase: string) => {
    const names = {
      'field_mapping': 'Field Mapping',
      'data_cleansing': 'Data Cleansing', 
      'asset_inventory': 'Asset Inventory',
      'dependency_analysis': 'Dependency Analysis',
      'tech_debt_analysis': 'Tech Debt Analysis'
    };
    return names[phase as keyof typeof names] || phase.replace('_', ' ').toUpperCase();
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const getTotalDataRecords = () => {
    if (!flow.deletion_impact?.data_to_delete) return 0;
    const data = flow.deletion_impact.data_to_delete;
    return Object.values(data).reduce((sum, count) => sum + (typeof count === 'number' ? count : 0), 0);
  };

  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <span>Delete Discovery Flow</span>
          </DialogTitle>
          <DialogDescription>
            This action will permanently delete the discovery flow and all associated data. 
            This cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Flow Information */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Flow Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Flow ID:</span>
                <p className="font-mono">{flow.flow_id}</p>
              </div>
              <div>
                <span className="text-gray-500">Current Phase:</span>
                <p>{getPhaseDisplayName(flow.current_phase || 'unknown')}</p>
              </div>
              <div>
                <span className="text-gray-500">Status:</span>
                <Badge variant="outline" className="ml-1">
                  {flow.status.toUpperCase()}
                </Badge>
              </div>
              <div>
                <span className="text-gray-500">Progress:</span>
                <p>{Math.round(flow.progress_percentage || 0)}% Complete</p>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <p>{formatTimeAgo(flow.created_at)}</p>
              </div>
              <div>
                <span className="text-gray-500">Last Activity:</span>
                <p>{formatTimeAgo(flow.updated_at)}</p>
              </div>
            </div>
          </div>

          {/* Deletion Impact Analysis */}
          <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
            <h3 className="font-semibold text-red-800 mb-3 flex items-center">
              <Database className="h-4 w-4 mr-2" />
              Deletion Impact
            </h3>
            
            {flow.deletion_impact?.data_to_delete ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  {Object.entries(flow.deletion_impact.data_to_delete).map(([key, count]) => {
                    if (typeof count !== 'number' || count === 0) return null;
                    
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

                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-red-600" />
                    <span className="text-red-700">
                      Estimated cleanup time: {flow.deletion_impact.estimated_cleanup_time}
                    </span>
                  </div>
                  <div className="font-semibold text-red-800">
                    Total records: {getTotalDataRecords()}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-sm text-red-700">
                <p>This flow will be permanently deleted along with any associated data and progress.</p>
              </div>
            )}
          </div>

          {/* Agent Insights Impact */}
          {flow.agent_insights && flow.agent_insights.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
              <h3 className="font-semibold text-yellow-800 mb-2 flex items-center">
                <Users className="h-4 w-4 mr-2" />
                Agent Insights Will Be Lost
              </h3>
              <p className="text-sm text-yellow-700 mb-2">
                This flow contains {flow.agent_insights.length} agent insights that will be permanently deleted:
              </p>
              <div className="space-y-1">
                {flow.agent_insights.slice(0, 3).map((insight, idx) => (
                  <div key={idx} className="text-xs bg-yellow-100 p-2 rounded">
                    <span className="font-medium capitalize">
                      {getPhaseDisplayName(insight.phase || 'unknown')}:
                    </span>
                    <span className="ml-1">{(insight.insight || insight.description || 'Insight data').substring(0, 100)}...</span>
                  </div>
                ))}
                {flow.agent_insights.length > 3 && (
                  <p className="text-xs text-yellow-600">
                    And {flow.agent_insights.length - 3} more insights...
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Warning Alert */}
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              <strong>Warning:</strong> This deletion is permanent and cannot be undone. 
              All progress, agent insights, and associated data will be lost. 
              Consider resuming the flow instead if you want to continue the discovery process.
            </AlertDescription>
          </Alert>
        </div>

        <Separator />

        <DialogFooter className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Data recovery will not be possible after deletion
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={onConfirm}>
              <AlertTriangle className="h-4 w-4 mr-2" />
              Delete Permanently
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}; 